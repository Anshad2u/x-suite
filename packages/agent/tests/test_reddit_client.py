"""Tests for social_agent.clients.reddit_client."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from social_agent.clients.reddit_client import RedditClient


class TestPostSubmission:
    def test_dry_run_returns_fake_permalink(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "true")
        client = RedditClient(reddit=MagicMock())
        result = client.post_submission("test", "Title", "Body")
        assert "reddit.com" in result
        assert "dry-run" in result

    def test_success_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "false")
        mock_submission = MagicMock()
        mock_submission.permalink = "/r/test/comments/abc123/title/"
        mock_subreddit = MagicMock()
        mock_subreddit.submit.return_value = mock_submission
        mock_reddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit

        client = RedditClient(reddit=mock_reddit)
        result = client.post_submission("test", "My Title", "My body")
        assert result == "/r/test/comments/abc123/title/"
        mock_subreddit.submit.assert_called_once_with(title="My Title", selftext="My body")


class TestReadInbox:
    def test_dry_run_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "true")
        client = RedditClient(reddit=MagicMock())
        assert client.read_inbox() == []

    def test_success_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "false")
        mock_item = MagicMock()
        mock_item.id = "msg1"
        mock_item.author = "alice"
        mock_item.body = "hello"
        mock_item.created_utc = "1700000000"

        mock_inbox = MagicMock()
        mock_inbox.unread.return_value = [mock_item]
        mock_reddit = MagicMock()
        mock_reddit.inbox = mock_inbox

        client = RedditClient(reddit=mock_reddit)
        items = client.read_inbox()
        assert len(items) == 1
        assert items[0]["author"] == "alice"


class TestReply:
    def test_dry_run_noop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "true")
        mock_item = MagicMock()
        client = RedditClient(reddit=MagicMock())
        client.reply(mock_item, "thanks")
        mock_item.reply.assert_not_called()

    def test_calls_reply(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "false")
        mock_item = MagicMock()
        client = RedditClient(reddit=MagicMock())
        client.reply(mock_item, "thanks!")
        mock_item.reply.assert_called_once_with("thanks!")


class TestMarkRead:
    def test_dry_run_noop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "true")
        mock_item = MagicMock()
        client = RedditClient(reddit=MagicMock())
        client.mark_read(mock_item)
        mock_item.mark_read.assert_not_called()

    def test_calls_mark_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "false")
        mock_item = MagicMock()
        client = RedditClient(reddit=MagicMock())
        client.mark_read(mock_item)
        mock_item.mark_read.assert_called_once()
