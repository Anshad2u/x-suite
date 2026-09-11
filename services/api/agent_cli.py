"""Wiring layer — connects the pure `social_agent` library to this service.

`packages/agent` owns the scheduling logic but no I/O. This module supplies
the real implementations: the Postgres queue, the scraper-based posters, and
the Telegram notifier. It is also the CLI entry point.

X access is scraper-only. There is no paid-API client anywhere in this path.

Usage
-----
    python agent_cli.py status
    python agent_cli.py schedule once
    python agent_cli.py schedule daemon
    python agent_cli.py drafts list
    python agent_cli.py drafts add --platform x --text "Hello"
"""

from __future__ import annotations

import argparse
import logging
import sys

import config


# --- adapters ----------------------------------------------------------------

class PostgresQueue:
    """Implements the PostQueue contract from social_agent.scheduler."""

    def add_post(self, platform, content, scheduled_at=None):
        import data_models as dm
        return dm.queue_add_post(platform, content, scheduled_at)

    def due_posts(self, now_iso):
        import data_models as dm
        rows = dm.queue_due_posts(now_iso)
        # psycopg2 returns datetimes for TIMESTAMPTZ; the scheduler only
        # compares/passes them through, so leave them as-is.
        return rows

    def mark_posted(self, post_id, permalink):
        import data_models as dm
        dm.queue_mark_posted(post_id, permalink)

    def mark_failed(self, post_id, error):
        import data_models as dm
        dm.queue_mark_failed(post_id, error)

    def posts_today(self):
        import data_models as dm
        return dm.queue_posts_today()


class XPosterAdapter:
    """Adapts XPoster (returns a tweet id) to the Poster contract (permalink)."""

    def __init__(self):
        from poster import XPoster
        self._poster = XPoster()
        self._username = config.TWITTER_USERNAME or "i"

    def post(self, content):
        tweet_id = self._poster.post(content)
        return f"https://x.com/{self._username}/status/{tweet_id}"


class RedditPosterAdapter:
    """Adapts submit_post (returns a dict) to the Poster contract."""

    def post(self, content):
        from reddit_poster import submit_post
        title = (content.strip().splitlines() or ["Update"])[0][:300] or "Update"
        result = submit_post(title, content)
        if result.get("status") != "ok":
            raise RuntimeError(f"reddit post failed: {result}")
        return result["permalink"]


class TelegramNotifier:
    """Adapts the notifier module to the Notifier contract."""

    def send_message(self, text):
        from notifier import send_message
        return send_message(text)


# --- app assembly ------------------------------------------------------------

def build_app(dry_run: bool | None = None) -> dict:
    """Assemble the injection dict the scheduler expects."""
    if dry_run is None:
        dry_run = config.is_dry_run()

    posters = {}
    # Only wire a poster if its credentials are present, so a missing
    # platform surfaces as a clear "no poster" message instead of a
    # confusing auth error deep in a request.
    if config.X_AUTH_TOKEN and config.CT0:
        posters["x"] = XPosterAdapter()
    if config.REDDIT_CLIENT_ID and config.REDDIT_CLIENT_SECRET:
        posters["reddit"] = RedditPosterAdapter()

    return {
        "queue": PostgresQueue(),
        "posters": posters,
        "notifier": TelegramNotifier(),
        "max_per_day": config.AUTO_POST_MAX_PER_DAY,
        "dry_run": dry_run,
    }


# --- commands ----------------------------------------------------------------

def cmd_status(_args) -> None:
    import data_models as dm
    from social_agent.drafts import list_drafts

    rows = dm.queue_due_posts("9999-12-31T00:00:00+00:00")
    counts = dm.db.query_one('''SELECT
        COUNT(*) FILTER (WHERE status='pending') AS pending,
        COUNT(*) FILTER (WHERE status='posted')  AS posted,
        COUNT(*) FILTER (WHERE status='failed')  AS failed
        FROM post_queue''') or {}

    print("=== x-suite agent status ===")
    print(f"  Queue pending:      {counts.get('pending', 0)}")
    print(f"  Queue posted:       {counts.get('posted', 0)}")
    print(f"  Queue failed:       {counts.get('failed', 0)}")
    print(f"  Posted today:       {dm.queue_posts_today()}/{config.AUTO_POST_MAX_PER_DAY}")
    print(f"  Draft files:        {len(list_drafts())}")
    print(f"  Due now:            {len(rows)}")
    print(f"  DRY_RUN:            {config.is_dry_run()}")
    print(f"  X credentials:      {'yes' if config.X_AUTH_TOKEN and config.CT0 else 'MISSING'}")


def cmd_schedule_once(args) -> None:
    from social_agent.scheduler import run_once
    summary = run_once(build_app(dry_run=args.dry_run))
    print(f"Scheduler: {summary}")


def cmd_schedule_daemon(args) -> None:
    from social_agent.scheduler import daemon
    app = build_app(dry_run=args.dry_run)
    print("Scheduler daemon running (Ctrl+C to stop)...")
    daemon(app, interval_sec=args.interval)


def cmd_drafts_list(_args) -> None:
    from social_agent.drafts import list_drafts
    drafts = list_drafts()
    if not drafts:
        print("No drafts found.")
        return
    for i, d in enumerate(drafts, 1):
        sched = d["scheduled_at"] or "(immediate)"
        print(f"  {i}. [{d['platform']}] {sched} — {d['content'][:60]}")


def cmd_drafts_add(args) -> None:
    from social_agent.drafts import add_draft
    path = add_draft(args.platform, args.text, args.scheduled_at)
    print(f"Draft created: {path}")


# --- parser ------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agent_cli",
        description="x-suite agent — Postgres-backed post queue (scraper-only).",
    )
    p.add_argument("--dry-run", dest="dry_run", action="store_true", default=None,
                   help="Force dry-run: log intended actions, change nothing.")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("status", help="Show queue and budget status")

    sched = sub.add_parser("schedule", help="Run the post scheduler")
    sched_sub = sched.add_subparsers(dest="sub")
    once_p = sched_sub.add_parser("once", help="Run one pass")
    once_p.add_argument("--dry-run", dest="dry_run", action="store_true", default=None)
    daemon_p = sched_sub.add_parser("daemon", help="Run in a loop")
    daemon_p.add_argument("--interval", type=int, default=300, help="Seconds between passes")
    daemon_p.add_argument("--dry-run", dest="dry_run", action="store_true", default=None)

    drafts = sub.add_parser("drafts", help="Manage the markdown draft queue")
    drafts_sub = drafts.add_subparsers(dest="sub")
    drafts_sub.add_parser("list", help="List drafts")
    add_p = drafts_sub.add_parser("add", help="Add a draft")
    add_p.add_argument("--platform", required=True, choices=["x", "reddit"])
    add_p.add_argument("--text", required=True)
    add_p.add_argument("--scheduled-at", dest="scheduled_at", default=None)

    return p


def main(argv=None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )
    args = build_parser().parse_args(argv)

    dispatch = {
        ("status", None): cmd_status,
        ("schedule", "once"): cmd_schedule_once,
        ("schedule", "daemon"): cmd_schedule_daemon,
        ("drafts", "list"): cmd_drafts_list,
        ("drafts", "add"): cmd_drafts_add,
    }
    handler = dispatch.get((args.command, getattr(args, "sub", None)))
    if handler is None:
        build_parser().print_help()
        return
    handler(args)


if __name__ == "__main__":
    main()
