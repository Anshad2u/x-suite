"""Scheduler — turns due drafts into posts, respecting a daily cap.

Pure logic: this module owns no database, no HTTP client, and no
credentials. Everything it touches is injected through the ``app`` dict,
so the same scheduler runs against Postgres in production and against
fakes in tests.

``app`` keys
------------
queue : PostQueue
    Pending-work store. See :class:`PostQueue`.
posters : dict[str, Poster]
    Platform name -> poster. Only platforms present here can be posted.
notifier : Notifier, optional
    Alert sink, used for failures only.
max_per_day : int, optional
    Daily post cap. Defaults to 8.
dry_run : bool, optional
    When true, log what would happen and change nothing. Defaults to True —
    an unconfigured scheduler must never post by accident.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Protocol

from social_agent.drafts import load_due_drafts

logger = logging.getLogger(__name__)

DEFAULT_MAX_PER_DAY = 8


class PostQueue(Protocol):
    """Storage contract the scheduler depends on."""

    def add_post(self, platform: str, content: str,
                 scheduled_at: str | None = None) -> int:
        """Insert a pending post, returning its id."""

    def due_posts(self, now_iso: str) -> list[dict[str, Any]]:
        """Return pending posts whose schedule has arrived."""

    def mark_posted(self, post_id: int, permalink: str) -> None:
        """Record a successful post."""

    def mark_failed(self, post_id: int, error: str) -> None:
        """Record a failed post."""

    def posts_today(self) -> int:
        """Return how many posts have succeeded today."""


class Poster(Protocol):
    """Posting contract. One implementation per platform."""

    def post(self, content: str) -> str:
        """Publish *content*, returning a permalink."""


class Notifier(Protocol):
    """Alert contract."""

    def send_message(self, text: str) -> Any:
        """Send an alert."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_once(app: dict[str, Any]) -> dict[str, int]:
    """Execute one scheduler pass.

    Returns ``{posted, failed, skipped_budget, dry_run}``.
    """
    queue: PostQueue = app["queue"]
    posters: dict[str, Poster] = app.get("posters", {})
    notifier: Notifier | None = app.get("notifier")
    max_per_day: int = app.get("max_per_day", DEFAULT_MAX_PER_DAY)
    dry_run: bool = app.get("dry_run", True)

    now = _now_iso()
    posted = 0
    failed = 0
    skipped_budget = 0

    # 1. Promote due draft files into the queue.
    for draft in load_due_drafts(now):
        queue.add_post(draft["platform"], draft["content"], draft["scheduled_at"])
        logger.info("Queued draft [%s]: %s", draft["platform"], draft["content"][:60])

    # 2. Drain due queue rows.
    for item in queue.due_posts(now):
        platform = item["platform"]
        post_id = item["id"]
        content = item["content"]

        poster = posters.get(platform)
        if poster is None:
            # A missing poster is a config error, not a post failure. Report it
            # either way, but only mutate the queue on a real run.
            if not dry_run:
                queue.mark_failed(post_id, f"No poster configured for platform: {platform}")
            failed += 1
            logger.warning("No poster for platform %s (post %s)", platform, post_id)
            continue

        if queue.posts_today() >= max_per_day:
            skipped_budget += 1
            logger.info("Daily cap reached (%d). Deferring post %s.", max_per_day, post_id)
            continue

        if dry_run:
            logger.info("[DRY RUN] Would post to %s: %s", platform, content[:80])
            continue

        try:
            permalink = poster.post(content)
            queue.mark_posted(post_id, permalink)
            posted += 1
            logger.info("Posted %s #%s -> %s", platform, post_id, permalink)
        except Exception as exc:
            queue.mark_failed(post_id, str(exc))
            failed += 1
            logger.error("Failed to post %s #%s: %s", platform, post_id, exc)
            if notifier is not None:
                try:
                    notifier.send_message(f"Post failed [{platform}] #{post_id}: {exc}")
                except Exception:
                    logger.exception("Notifier itself failed")

    summary = {
        "posted": posted,
        "failed": failed,
        "skipped_budget": skipped_budget,
        "dry_run": dry_run,
    }
    logger.info("Scheduler pass complete: %s", summary)
    return summary


def daemon(app: dict[str, Any], interval_sec: int = 300) -> None:
    """Run the scheduler in a loop.

    The queue is the source of truth, so this is safe to kill at any time.
    """
    import time

    logger.info("Scheduler daemon started (interval=%ds)", interval_sec)
    while True:
        try:
            run_once(app)
        except Exception as exc:
            logger.error("Scheduler pass failed: %s", exc)
        time.sleep(interval_sec)
