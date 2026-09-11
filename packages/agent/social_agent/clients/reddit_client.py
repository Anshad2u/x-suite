"""Reddit client via PRAW — official API only."""

from __future__ import annotations

import logging
from typing import Any

from social_agent import config

logger = logging.getLogger(__name__)


def _build_reddit() -> Any:
    """Lazily construct a praw.Reddit instance from config."""
    import praw

    keys = config.require(
        ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"]
    )
    return praw.Reddit(
        client_id=keys["REDDIT_CLIENT_ID"],
        client_secret=keys["REDDIT_CLIENT_SECRET"],
        username=keys["REDDIT_USERNAME"],
        password=keys["REDDIT_PASSWORD"],
        user_agent="social-agent/0.1 (maintenance bot)",
    )


class RedditClient:
    """Reddit operations with injectable praw.Reddit instance."""

    def __init__(self, reddit: Any | None = None) -> None:
        self._reddit = reddit
        self._dry_run_counter = 0

    @property
    def reddit(self) -> Any:
        if self._reddit is None:
            self._reddit = _build_reddit()
        return self._reddit

    def post_submission(
        self, subreddit: str, title: str, text: str, flair: str | None = None
    ) -> str:
        """Submit a self-post. Returns permalink string."""
        if config.is_dry_run():
            self._dry_run_counter += 1
            fake = f"https://reddit.com/r/{subreddit}/dry-run-{self._dry_run_counter}"
            logger.info("[DRY RUN] Would submit to r/%s: %s", subreddit, title[:60])
            return fake

        sub = self.reddit.subreddit(subreddit)
        kwargs: dict[str, Any] = {"title": title, "selftext": text}
        if flair:
            kwargs["flair_id"] = flair
        submission = sub.submit(**kwargs)
        logger.info("Submitted to r/%s: %s", subreddit, submission.permalink)
        return submission.permalink

    def read_inbox(self) -> list[dict[str, Any]]:
        """Return unread inbox items (mentions/comments)."""
        if config.is_dry_run():
            logger.info("[DRY RUN] Would read Reddit inbox")
            return []

        items: list[dict[str, Any]] = []
        try:
            for item in self.reddit.inbox.unread(limit=50):
                items.append(
                    {
                        "id": item.id,
                        "author": str(item.author) if item.author else "[deleted]",
                        "body": getattr(item, "body", ""),
                        "created_utc": str(getattr(item, "created_utc", "")),
                        "raw": item,
                    }
                )
        except Exception as exc:
            logger.warning("Failed to read Reddit inbox: %s", exc)
        return items

    def reply(self, item: Any, text: str) -> None:
        """Reply to an inbox item."""
        if config.is_dry_run():
            logger.info("[DRY RUN] Would reply: %s", text[:60])
            return
        item.reply(text)
        logger.info("Replied to %s", getattr(item, "id", "unknown"))

    def mark_read(self, item: Any) -> None:
        """Mark an inbox item as read."""
        if config.is_dry_run():
            logger.info("[DRY RUN] Would mark read")
            return
        item.mark_read()
