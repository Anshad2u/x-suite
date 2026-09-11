"""Tests for social_agent.scheduler."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from social_agent.clients.x_client import RateLimitError
from social_agent.db import Database
from social_agent.scheduler import X_MONTHLY_HARD_STOP, run_once


@pytest.fixture()
def app(tmp_path: Path) -> dict:
    """Build a test app dict with real DB and mock clients."""
    db = Database(tmp_path / "test.db")
    x_client = MagicMock()
    x_client.post_tweet.return_value = {"id": "tw1", "permalink": "https://x.com/u/status/tw1"}
    reddit_client = MagicMock()
    reddit_client.post_submission.return_value = "/r/test/comments/abc/"
    return {"db": db, "x_client": x_client, "reddit_client": reddit_client}


class TestRunOnce:
    def test_posts_due_items(self, app: dict) -> None:
        db: Database = app["db"]
        db.add_post("x", "Hello X", "2020-01-01T00:00:00")
        db.add_post("reddit", "Hello Reddit", "2020-01-01T00:00:00")

        summary = run_once(app)
        assert summary["posted"] == 2
        assert summary["failed"] == 0
        assert summary["skipped_budget"] == 0

    def test_failure_recorded(self, app: dict) -> None:
        db: Database = app["db"]
        db.add_post("x", "will fail", "2020-01-01T00:00:00")
        app["x_client"].post_tweet.side_effect = Exception("network error")

        summary = run_once(app)
        assert summary["posted"] == 0
        assert summary["failed"] == 1

    def test_budget_hard_stop(self, app: dict) -> None:
        db: Database = app["db"]
        # Simulate being at the hard-stop limit
        from datetime import datetime, timezone

        key = f"posts:x:{datetime.now(timezone.utc):%Y-%m}"
        db.increment(key, X_MONTHLY_HARD_STOP)

        db.add_post("x", "over budget", "2020-01-01T00:00:00")
        summary = run_once(app)
        assert summary["skipped_budget"] == 1
        assert summary["posted"] == 0

    def test_unknown_platform_fails(self, app: dict) -> None:
        db: Database = app["db"]
        db.add_post("mastodon", "wrong platform", "2020-01-01T00:00:00")
        summary = run_once(app)
        assert summary["failed"] == 1

    def test_rate_limit_records_failure(self, app: dict) -> None:
        db: Database = app["db"]
        db.add_post("x", "rate limited", "2020-01-01T00:00:00")
        app["x_client"].post_tweet.side_effect = RateLimitError("429")

        summary = run_once(app)
        assert summary["failed"] == 1

    def test_empty_pass(self, app: dict) -> None:
        summary = run_once(app)
        assert summary == {"posted": 0, "failed": 0, "skipped_budget": 0}
