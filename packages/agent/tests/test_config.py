"""Tests for social_agent.config."""

from __future__ import annotations

import os

import pytest

from social_agent.config import ConfigError, get, is_dry_run, require


class TestGet:
    def test_returns_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_KEY_XYZ", "hello")
        assert get("TEST_KEY_XYZ") == "hello"

    def test_returns_default_when_missing(self) -> None:
        assert get("NO_SUCH_KEY_12345", "fallback") == "fallback"

    def test_returns_none_when_missing_no_default(self) -> None:
        assert get("NO_SUCH_KEY_12345") is None


class TestRequire:
    def test_returns_dict_of_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("RK_A", "alpha")
        monkeypatch.setenv("RK_B", "beta")
        result = require(["RK_A", "RK_B"])
        assert result == {"RK_A": "alpha", "RK_B": "beta"}

    def test_raises_config_error_for_missing(self) -> None:
        with pytest.raises(ConfigError) as exc_info:
            require(["MISSING_A", "MISSING_B"])
        msg = str(exc_info.value)
        assert "MISSING_A" in msg
        assert "MISSING_B" in msg

    def test_raises_for_single_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("RK_OK", "ok")
        with pytest.raises(ConfigError):
            require(["RK_OK", "RK_NOPE"])


class TestIsDryRun:
    def test_default_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("DRY_RUN", raising=False)
        assert is_dry_run() is True

    def test_false_when_set_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "false")
        assert is_dry_run() is False

    def test_true_when_set_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "true")
        assert is_dry_run() is True

    def test_true_when_set_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DRY_RUN", "1")
        assert is_dry_run() is True
