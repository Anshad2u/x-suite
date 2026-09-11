"""Watcher — polls mentions from X and Reddit, alerts via Telegram."""

from __future__ import annotations

import logging
import time
from typing import Any

from social_agent import config
from social_agent.clients.reddit_client import RedditClient
from social_agent.clients.x_client import XClient
from social_agent.db import Database
from social_agent.notifier import Notifier

logger = logging.getLogger(__name__)


def _dedupe_key(platform: str, item: dict[str, Any]) -> str:
    """Build a deduplication key from platform + item id/created_utc."""
    if platform == "x":
        return f"x:{item.get('id', '')}"
    return f"reddit:{item.get('id', item.get('created_utc', ''))}"


def run_once(app: dict[str, Any]) -> dict[str, int]:
    """Poll mentions once, store new ones, alert, optionally auto-reply.

    *app* must contain: db, x_client, reddit_client, notifier.
    Returns {new_mentions, alerted, replied}.
    """
    db: Database = app["db"]
    x_client: XClient = app["x_client"]
    reddit_client: RedditClient = app["reddit_client"]
    notifier: Notifier = app["notifier"]

    auto_reply_x = config.get("X_AUTO_REPLY", "false").lower() in ("true", "1", "yes")
    auto_reply_reddit = config.get("REDDIT_AUTO_REPLY", "false").lower() in ("true", "1", "yes")
    reply_template = config.get("AUTO_REPLY_TEMPLATE", "Thanks for reaching out! I'll look into this.")

    new_mentions = 0
    alerted = 0
    replied = 0

    # Build set of existing mention keys for dedup
    existing = set()
    for m in db.unread_mentions():
        existing.add(f"{m['platform']}:{m.get('id', m.get('created_utc', ''))}")
    # Also check replied mentions
    with db._conn() as conn:
        rows = conn.execute("SELECT platform, id, created_utc FROM mentions").fetchall()
        for r in rows:
            existing.add(f"{r['platform']}:{r['id']}")

    # X mentions
    try:
        for item in x_client.fetch_mentions():
            key = _dedupe_key("x", item)
            if key in existing:
                continue
            db.add_mention("x", item.get("author", ""), item.get("body", ""), item.get("created_at", ""), str(item))
            existing.add(key)
            new_mentions += 1
            msg = f"[X] @{item.get('author', '?')}: {item.get('body', '')[:120]}"
            result = notifier.send_message(msg)
            if result:
                alerted += 1
            if auto_reply_x:
                # X auto-reply not implemented (would need reply API) — log only
                logger.info("[X] Auto-reply would send: %s", reply_template[:60])
                replied += 1
    except Exception as exc:
        logger.warning("Error fetching X mentions: %s", exc)

    # Reddit mentions
    try:
        for item in reddit_client.read_inbox():
            key = _dedupe_key("reddit", item)
            if key in existing:
                continue
            db.add_mention("reddit", item.get("author", ""), item.get("body", ""), item.get("created_utc", ""), str(item))
            existing.add(key)
            new_mentions += 1
            msg = f"[Reddit] u/{item.get('author', '?')}: {item.get('body', '')[:120]}"
            result = notifier.send_message(msg)
            if result:
                alerted += 1
            if auto_reply_reddit:
                raw = item.get("raw")
                if raw:
                    reddit_client.reply(raw, reply_template)
                    replied += 1
    except Exception as exc:
        logger.warning("Error reading Reddit inbox: %s", exc)

    summary = {"new_mentions": new_mentions, "alerted": alerted, "replied": replied}
    logger.info("Watcher pass complete: %s", summary)
    return summary


def daemon(app: dict[str, Any], interval_sec: int = 120) -> None:
    """Run watcher in a loop."""
    logger.info("Watcher daemon started (interval=%ds)", interval_sec)
    while True:
        try:
            run_once(app)
        except Exception as exc:
            logger.error("Watcher pass failed: %s", exc)
        time.sleep(interval_sec)
