"""Tests for social_agent.notifier."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from social_agent.notifier import Notifier


class TestNotifier:
    def test_disabled_when_keys_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        n = Notifier()
        assert n.send_message("test") is None

    def test_dry_run_returns_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
        monkeypatch.setenv("DRY_RUN", "true")
        n = Notifier()
        assert n.send_message("hello") is True

    def test_success_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
        monkeypatch.setenv("DRY_RUN", "false")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_session = MagicMock()
        mock_session.post.return_value = mock_resp

        n = Notifier(session=mock_session)
        assert n.send_message("alert!") is True
        mock_session.post.assert_called_once()

    def test_http_error_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
        monkeypatch.setenv("DRY_RUN", "false")

        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "Bad Request"
        mock_session = MagicMock()
        mock_session.post.return_value = mock_resp

        n = Notifier(session=mock_session)
        assert n.send_message("fail") is False

    def test_network_error_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")
        monkeypatch.setenv("DRY_RUN", "false")

        mock_session = MagicMock()
        mock_session.post.side_effect = Exception("connection refused")

        n = Notifier(session=mock_session)
        assert n.send_message("boom") is False
