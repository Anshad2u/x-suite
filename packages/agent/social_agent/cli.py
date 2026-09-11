"""CLI entry point — argparse subcommands."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from social_agent import config
from social_agent.db import Database


def _get_db() -> Database:
    db_path = config.get("DB_PATH", str(Path(__file__).resolve().parent.parent / "social_agent.db"))
    return Database(db_path)


def _build_app() -> dict:
    """Build the app dict used by scheduler/watcher."""
    from social_agent.clients.reddit_client import RedditClient
    from social_agent.clients.x_client import XClient
    from social_agent.notifier import Notifier

    return {
        "db": _get_db(),
        "x_client": XClient(),
        "reddit_client": RedditClient(),
        "notifier": Notifier(),
    }


# -- subcommand handlers -----------------------------------------------------

def cmd_drafts_add(args: argparse.Namespace) -> None:
    from social_agent.drafts import add_draft

    path = add_draft(args.platform, args.text, args.scheduled_at)
    print(f"Draft created: {path}")


def cmd_drafts_list(args: argparse.Namespace) -> None:
    from social_agent.drafts import list_drafts

    drafts = list_drafts()
    if not drafts:
        print("No drafts found.")
        return
    for i, d in enumerate(drafts, 1):
        sched = d["scheduled_at"] or "(immediate)"
        print(f"  {i}. [{d['platform']}] {sched} — {d['content'][:60]}")


def cmd_schedule_once(args: argparse.Namespace) -> None:
    from social_agent.scheduler import run_once

    app = _build_app()
    summary = run_once(app)
    print(f"Scheduler: posted={summary['posted']} failed={summary['failed']} skipped_budget={summary['skipped_budget']}")


def cmd_schedule_daemon(args: argparse.Namespace) -> None:
    from social_agent.scheduler import daemon

    app = _build_app()
    print("Starting scheduler daemon (Ctrl+C to stop)...")
    daemon(app)


def cmd_watch_once(args: argparse.Namespace) -> None:
    from social_agent.watcher import run_once

    app = _build_app()
    summary = run_once(app)
    print(f"Watcher: new_mentions={summary['new_mentions']} alerted={summary['alerted']} replied={summary['replied']}")


def cmd_watch_daemon(args: argparse.Namespace) -> None:
    from social_agent.watcher import daemon

    app = _build_app()
    print("Starting watcher daemon (Ctrl+C to stop)...")
    daemon(app)


def cmd_status(args: argparse.Namespace) -> None:
    db = _get_db()
    now = datetime.now(timezone.utc).isoformat()

    pending = len(db.due_posts(now))
    # Count posted and failed
    with db._conn() as conn:
        posted = conn.execute("SELECT COUNT(*) as c FROM posts WHERE status='posted'").fetchone()["c"]
        failed = conn.execute("SELECT COUNT(*) as c FROM posts WHERE status='failed'").fetchone()["c"]

    x_monthly = db.monthly_post_count("x")
    reddit_monthly = db.monthly_post_count("reddit")

    print("=== Social Agent Status ===")
    print(f"  Pending posts:      {pending}")
    print(f"  Posted (total):     {posted}")
    print(f"  Failed (total):     {failed}")
    print(f"  X posts this month: {x_monthly}/500")
    print(f"  Reddit this month:  {reddit_monthly}")
    print(f"  DRY_RUN:            {config.is_dry_run()}")


# -- argument parser ---------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="social-agent",
        description="Social Maintenance Agent — schedule posts and watch mentions on X and Reddit.",
    )
    sub = parser.add_subparsers(dest="command")

    # drafts
    drafts = sub.add_parser("drafts", help="Manage draft posts")
    drafts_sub = drafts.add_subparsers(dest="drafts_cmd")

    add_p = drafts_sub.add_parser("add", help="Add a new draft")
    add_p.add_argument("--platform", required=True, choices=["x", "reddit"], help="Target platform")
    add_p.add_argument("--text", required=True, help="Post content")
    add_p.add_argument("--scheduled-at", dest="scheduled_at", help="ISO 8601 timestamp")

    drafts_sub.add_parser("list", help="List all drafts")

    # schedule
    schedule = sub.add_parser("schedule", help="Run the post scheduler")
    schedule_sub = schedule.add_subparsers(dest="schedule_cmd")
    schedule_sub.add_parser("once", help="Run one scheduler pass")
    schedule_sub.add_parser("daemon", help="Run scheduler in a loop")

    # watch
    watch = sub.add_parser("watch", help="Watch for mentions")
    watch_sub = watch.add_subparsers(dest="watch_cmd")
    watch_sub.add_parser("once", help="Run one watcher pass")
    watch_sub.add_parser("daemon", help="Run watcher in a loop")

    # status
    sub.add_parser("status", help="Show current status")

    return parser


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return

    dispatch = {
        ("drafts", "add"): cmd_drafts_add,
        ("drafts", "list"): cmd_drafts_list,
        ("schedule", "once"): cmd_schedule_once,
        ("schedule", "daemon"): cmd_schedule_daemon,
        ("watch", "once"): cmd_watch_once,
        ("watch", "daemon"): cmd_watch_daemon,
        ("status", None): cmd_status,
    }

    # Resolve sub-subcommand
    sub_cmd = getattr(args, "drafts_cmd", None) or getattr(args, "schedule_cmd", None) or getattr(args, "watch_cmd", None)
    key = (args.command, sub_cmd)

    handler = dispatch.get(key)
    if handler is None:
        parser.print_help()
        return

    handler(args)


if __name__ == "__main__":
    main()
