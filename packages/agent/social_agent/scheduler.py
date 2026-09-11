"""Scheduler — posts due drafts and due DB posts, respects monthly budget."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from social_agent import config
from social_agent.clients.reddit_client import RedditClient
from social_agent.clients.x_client import XClient, RateLimitError
from social_agent.db import Database
from social_agent.drafts import load_due_drafts

logger = logging.getLogger(__name__)

# X free-tier monthly budget
X_MONTHLY_LIMIT = 500
X_MONTHLY_HARD_STOP = 480


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_once(app: dict[str, Any]) -> dict[str, int]:
    """Execute one scheduler pass.

    *app* must contain keys: ``db`` (Database), ``x_client`` (XClient),
    ``reddit_client`` (RedditClient).

    Returns summary dict: {posted, failed, skipped_budget}.
    """
    db: Database = app["db"]
    x_client: XClient = app["x_client"]
    reddit_client: RedditClient = app["reddit_client"]

    now = _now_iso()
    posted = 0
    failed = 0
    skipped_budget = 0

    # 1. Load due drafts into DB
    for draft in load_due_drafts(now):
        db.add_post(draft["platform"], draft["content"], draft["scheduled_at"])
        logger.info("Loaded draft into DB: %s / %s", draft["platform"], draft["content"][:40])

    # 2. Process due posts from DB
    for post in db.due_posts(now):
        platform = post["platform"]
        content = post["content"]
        post_id = post["id"]

        # Budget check for X
        if platform == "x":
            monthly = db.monthly_post_count("x")
            if monthly >= X_MONTHLY_HARD_STOP:
                logger.warning(
                    "X monthly budget reached (%d/%d). Skipping post %d.",
                    monthly, X_MONTHLY_LIMIT, post_id,
                )
                skipped_budget += 1
                continue

        try:
            if platform == "x":
                result = x_client.post_tweet(content)
                permalink = result["permalink"]
            elif platform == "reddit":
                permalink = reddit_client.post_submission("test", content[:100], content)
            else:
                logger.warning("Unknown platform %s for post %d", platform, post_id)
                db.mark_failed(post_id, f"Unknown platform: {platform}")
                failed += 1
                continue

            db.mark_posted(post_id, permalink)
            # Increment monthly counter
            counter_key = f"posts:{platform}:{datetime.now(timezone.utc):%Y-%m}"
            db.increment(counter_key)
            posted += 1
            logger.info("Posted %s #%d -> %s", platform, post_id, permalink)

        except RateLimitError as exc:
            logger.error("Rate limit on post %d: %s", post_id, exc)
            db.mark_failed(post_id, str(exc))
            failed += 1
        except Exception as exc:
            logger.error("Failed to post %d: %s", post_id, exc)
            db.mark_failed(post_id, str(exc))
            failed += 1

    summary = {"posted": posted, "failed": failed, "skipped_budget": skipped_budget}
    logger.info("Scheduler pass complete: %s", summary)
    return summary


def daemon(app: dict[str, Any], interval_sec: int = 300) -> None:
    """Run scheduler in a loop. DB is source of truth — safe to kill at any time."""
    logger.info("Scheduler daemon started (interval=%ds)", interval_sec)
    while True:
        try:
            run_once(app)
        except Exception as exc:
            logger.error("Scheduler pass failed: %s", exc)
        time.sleep(interval_sec)
