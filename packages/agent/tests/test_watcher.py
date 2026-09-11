"""Tests for social_agent.watcher."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from social_agent.db import Database
from social_agent.watcher import run_once


@pytest.fixture()
def app(tmp_path: Path) -> dict:
    db = Database(tmp_path / "test.db")
    x_client = MagicMock()
    x_client.fetch_mentions.return_value = []
    reddit_client = MagicMock()
    reddit_client.read_inbox.return_value = []
    notifier = MagicMock()
    notifier.send_message.return_value = True
    return {
        "db": db,
        "x_client": x_client,
        "reddit_client": reddit_client,
        "notifier": notifier,
    }


class TestRunOnce:
    def test_stores_new_mentions(self, app: dict) -> None:
        app["x_client"].fetch_mentions.return_value = [
            {"id": "m1", "author": "alice", "body": "hi", "created_at": "2025-01-01"}
        ]
        summary = run_once(app)
        assert summary["new_mentions"] == 1
        assert summary["alerted"] == 1
        assert app["db"].unread_mentions()

    def test_dedupe(self, app: dict) -> None:
        mentions = [{"id": "m1", "author": "alice", "body": "hi", "created_at": "2025-01-01"}]
        app["x_client"].fetch_mentions.return_value = mentions

        run_once(app)
        summary = run_once(app)  # second pass — should not duplicate
        assert summary["new_mentions"] == 0

    def test_reddit_mentions(self, app: dict) -> None:
        mock_raw = MagicMock()
        app["reddit_client"].read_inbox.return_value = [
            {"id": "r1", "author": "bob", "body": "hey", "created_utc": "1700000000", "raw": mock_raw}
        ]
        summary = run_once(app)
        assert summary["new_mentions"] == 1

    def test_auto_reply_off_by_default(self, app: dict, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("X_AUTO_REPLY", raising=False)
        monkeypatch.delenv("REDDIT_AUTO_REPLY", raising=False)
        mock_raw = MagicMock()
        app["reddit_client"].read_inbox.return_value = [
            {"id": "r1", "author": "bob", "body": "hey", "created_utc": "1700000000", "raw": mock_raw}
        ]
        summary = run_once(app)
        assert summary["replied"] == 0
        app["reddit_client"].reply.assert_not_called()

    def test_auto_reply_on(self, app: dict, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("REDDIT_AUTO_REPLY", "true")
        monkeypatch.delenv("X_AUTO_REPLY", raising=False)
        mock_raw = MagicMock()
        app["reddit_client"].read_inbox.return_value = [
            {"id": "r1", "author": "bob", "body": "hey", "created_utc": "1700000000", "raw": mock_raw}
        ]
        summary = run_once(app)
        assert summary["replied"] == 1
        app["reddit_client"].reply.assert_called_once()

    def test_empty_pass(self, app: dict) -> None:
        summary = run_once(app)
        assert summary == {"new_mentions": 0, "alerted": 0, "replied": 0}
