"""Tests for social_agent.scheduler.

The scheduler is pure logic, so these tests inject fakes for the queue,
the posters, and the draft loader — no database and no network.
"""

from __future__ import annotations

from typing import Any

import pytest

from social_agent import scheduler
from social_agent.scheduler import run_once


class FakeQueue:
    """In-memory PostQueue implementation."""

    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self._next_id = 1
        self.posted_today = 0

    def add_post(self, platform: str, content: str,
                 scheduled_at: str | None = None,
                 source_ref: str | None = None) -> int | None:
        # Mirror the real queue's uniqueness on source_ref.
        if source_ref is not None and any(r.get("source_ref") == source_ref
                                          for r in self.rows):
            return None
        pid = self._next_id
        self._next_id += 1
        self.rows.append({
            "id": pid,
            "platform": platform,
            "content": content,
            "scheduled_at": scheduled_at,
            "source_ref": source_ref,
            "status": "pending",
        })
        return pid

    def due_posts(self, now_iso: str) -> list[dict[str, Any]]:
        return [r for r in self.rows if r["status"] == "pending"]

    def mark_posted(self, post_id: int, permalink: str) -> None:
        for r in self.rows:
            if r["id"] == post_id:
                r["status"] = "posted"
                r["permalink"] = permalink
        self.posted_today += 1

    def mark_failed(self, post_id: int, error: str) -> None:
        for r in self.rows:
            if r["id"] == post_id:
                r["status"] = "failed"
                r["error"] = error

    def posts_today(self) -> int:
        return self.posted_today


class FakePoster:
    def __init__(self, permalink: str = "https://x.com/u/status/1",
                 error: Exception | None = None) -> None:
        self.permalink = permalink
        self.error = error
        self.calls: list[str] = []

    def post(self, content: str) -> str:
        self.calls.append(content)
        if self.error:
            raise self.error
        return self.permalink


@pytest.fixture(autouse=True)
def no_draft_files(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the real drafts/ directory out of these tests."""
    monkeypatch.setattr(scheduler, "load_due_drafts", lambda now: [])


def make_app(**overrides: Any) -> dict[str, Any]:
    app: dict[str, Any] = {
        "queue": FakeQueue(),
        "posters": {"x": FakePoster()},
        "max_per_day": 8,
        "dry_run": False,
    }
    app.update(overrides)
    return app


class TestRunOnce:
    def test_posts_due_items(self) -> None:
        app = make_app()
        app["queue"].add_post("x", "Hello X", "2020-01-01T00:00:00")

        summary = run_once(app)
        assert summary["posted"] == 1
        assert summary["failed"] == 0
        assert summary["skipped_budget"] == 0

    def test_failure_recorded(self) -> None:
        app = make_app(posters={"x": FakePoster(error=Exception("network error"))})
        app["queue"].add_post("x", "will fail", "2020-01-01T00:00:00")

        summary = run_once(app)
        assert summary["posted"] == 0
        assert summary["failed"] == 1
        assert app["queue"].rows[0]["status"] == "failed"

    def test_daily_cap_defers(self) -> None:
        app = make_app(max_per_day=1)
        app["queue"].add_post("x", "first", "2020-01-01T00:00:00")
        app["queue"].add_post("x", "second", "2020-01-01T00:00:00")

        summary = run_once(app)
        assert summary["posted"] == 1
        assert summary["skipped_budget"] == 1

    def test_dry_run_changes_nothing(self) -> None:
        app = make_app(dry_run=True)
        app["queue"].add_post("x", "not really posted", "2020-01-01T00:00:00")

        summary = run_once(app)
        assert summary["posted"] == 0
        assert summary["failed"] == 0
        assert summary["dry_run"] is True
        assert app["queue"].rows[0]["status"] == "pending"
        assert app["posters"]["x"].calls == []

    def test_unknown_platform_fails(self) -> None:
        app = make_app()
        app["queue"].add_post("mastodon", "wrong platform", "2020-01-01T00:00:00")

        summary = run_once(app)
        assert summary["failed"] == 1

    def test_dry_run_does_not_mutate_on_missing_poster(self) -> None:
        app = make_app(dry_run=True)
        app["queue"].add_post("mastodon", "no poster here", "2020-01-01T00:00:00")

        summary = run_once(app)
        assert summary["failed"] == 1
        assert app["queue"].rows[0]["status"] == "pending"

    def test_empty_pass(self) -> None:
        summary = run_once(make_app())
        assert summary["posted"] == 0
        assert summary["failed"] == 0
        assert summary["skipped_budget"] == 0

    def test_reddit_and_x_both_post(self) -> None:
        app = make_app(posters={"x": FakePoster(), "reddit": FakePoster("/r/x/1")})
        app["queue"].add_post("x", "to X", "2020-01-01T00:00:00")
        app["queue"].add_post("reddit", "to Reddit", "2020-01-01T00:00:00")

        summary = run_once(app)
        assert summary["posted"] == 2

    def test_draft_promotion_is_idempotent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        draft = {"platform": "x", "content": "hello", "scheduled_at": None,
                 "path": "/drafts/a.md"}
        monkeypatch.setattr(scheduler, "load_due_drafts", lambda now: [draft])

        app = make_app()
        run_once(app)
        run_once(app)
        run_once(app)
        assert len(app["queue"].rows) == 1

    def test_dry_run_does_not_promote_drafts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        draft = {"platform": "x", "content": "hello", "scheduled_at": None,
                 "path": "/drafts/a.md"}
        monkeypatch.setattr(scheduler, "load_due_drafts", lambda now: [draft])

        app = make_app(dry_run=True)
        run_once(app)
        assert app["queue"].rows == []
