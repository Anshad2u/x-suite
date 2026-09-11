"""Scheduled autonomous runner — Task Scheduler every 2h.

Order of operations:

1. **learn** — fetch engagement on previously posted tweets, credit sources
2. **queue** — drain `post_queue` (explicit and scheduled drafts)
3. **autopost** — only if the queue published nothing, autonomously pick the
   highest-scoring unused candidate

Steps 2 and 3 share one daily budget, read from `posted_log`.

Telegram contact only on errors; silent on success.

Usage:
    python autopost_runner.py
    python autopost_runner.py --dry-run
"""
import json
import sys

import config
import data_models as dm
from notifier import send_message


def main(dry_run=None):
    dm.init_dbs()

    import learn
    import autopost
    from poster import XPoster, PostError
    from agent_cli import build_app
    from social_agent.scheduler import run_once as run_queue

    if dry_run is None:
        dry_run = "--dry-run" in sys.argv

    out = {}

    # 1. Engagement feedback.
    out["learn"] = learn.learn_once()

    # 2. Drain the explicit/scheduled queue.
    try:
        out["queue"] = run_queue(build_app(dry_run=dry_run))
    except Exception as e:
        out["queue"] = {"status": "error", "error": str(e)}
        send_message(f"queue drain error: {e}")

    # 3. Shared daily budget check.
    today_count = dm.queue_posts_today()
    out["posted_today"] = today_count
    if today_count >= config.AUTO_POST_MAX_PER_DAY:
        out["status"] = "daily_limit_reached"
        return out

    # The queue already produced a post this pass — don't also curate one.
    if out["queue"].get("posted"):
        out["status"] = "queue_posted"
        return out

    # 4. Autonomous fallback: pick and post one curated candidate.
    try:
        result = autopost.run_once(XPoster(), config.AUTO_POST_GROUP, dry_run=dry_run)
        out.update(result)
    except PostError as e:
        out["status"] = "post_failed"
        out["error"] = str(e)
        send_message(f"autopost failed: {e}")
    except Exception as e:
        out["status"] = "error"
        out["error"] = str(e)
        send_message(f"autopost error: {e}")

    return out


if __name__ == "__main__":
    try:
        print(json.dumps(main(), indent=2, default=str))
    except Exception as e:
        print(f"runner error: {e}", file=sys.stderr)
