"""Tests for social_agent.clients.x_client."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from social_agent.clients.x_client import RateLimitError, XClient


class FakeResponse:
    """Minimal response object for testing."""

    def __init__(self, status_code: int = 200, json_data: dict | None = None, headers: dict | None = None) -> None:
        self.status_code = status_code
        self._json = json_data or {}
        self.headers = headers or {}

    def json(self) -> dict:
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class TestPostTweet:
    def test_dry_run_returns_fake_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "true")
        client = XClient(session=MagicMock())
        result = client.post_tweet("Hello world")
        assert "dry-run" in result["id"]
        assert "permalink" in result

    def test_success_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "false")
        mock_session = MagicMock()
        mock_session.post.return_value = FakeResponse(
            200, {"data": {"id": "12345"}}
        )
        client = XClient(session=mock_session)
        result = client.post_tweet("Test tweet")
        assert result["id"] == "12345"
        assert "12345" in result["permalink"]
        mock_session.post.assert_called_once()

    def test_rate_limit_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "false")
        mock_session = MagicMock()
        mock_session.post.return_value = FakeResponse(
            429, headers={"x-rate-limit-reset": "99999"}
        )
        client = XClient(session=mock_session)
        with pytest.raises(RateLimitError):
            client.post_tweet("Rate limited")


class TestFetchMentions:
    def test_dry_run_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "true")
        client = XClient(session=MagicMock())
        assert client.fetch_mentions() == []

    def test_success_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "false")
        mock_session = MagicMock()
        mock_session.get.side_effect = [
            FakeResponse(200, {"data": {"id": "user123"}}),
            FakeResponse(200, {"data": [{"id": "m1", "author_id": "alice", "text": "hi", "created_at": "2025-01-01"}]}),
        ]
        client = XClient(session=mock_session)
        mentions = client.fetch_mentions()
        assert len(mentions) == 1
        assert mentions[0]["id"] == "m1"

    def test_free_tier_rejection_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "false")
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("403 Forbidden")
        client = XClient(session=mock_session)
        assert client.fetch_mentions() == []

    def test_rate_limit_on_mentions_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "false")
        mock_session = MagicMock()
        mock_session.get.return_value = FakeResponse(429)
        client = XClient(session=mock_session)
        with pytest.raises(RateLimitError):
            client.fetch_mentions()
