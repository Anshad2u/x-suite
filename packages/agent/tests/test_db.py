"""Tests for social_agent.db."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from social_agent.db import Database


@pytest.fixture()
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "test.db")


# -- posts -------------------------------------------------------------------

class TestPosts:
    def test_add_and_due_posts(self, db: Database) -> None:
        pid = db.add_post("x", "hello world", "2025-01-01T00:00:00")
        assert isinstance(pid, int)
        due = db.due_posts("2025-06-01T00:00:00")
        assert len(due) == 1
        assert due[0]["content"] == "hello world"
        assert due[0]["status"] == "pending"

    def test_due_posts_ordering(self, db: Database) -> None:
        db.add_post("x", "later", "2025-06-02T00:00:00")
        db.add_post("x", "sooner", "2025-06-01T00:00:00")
        due = db.due_posts("2025-06-03T00:00:00")
        assert due[0]["content"] == "sooner"
        assert due[1]["content"] == "later"

    def test_due_posts_excludes_future(self, db: Database) -> None:
        db.add_post("x", "not yet", "2099-01-01T00:00:00")
        assert db.due_posts("2025-01-01T00:00:00") == []

    def test_due_posts_includes_null_schedule(self, db: Database) -> None:
        db.add_post("x", "asap")
        due = db.due_posts("2025-01-01T00:00:00")
        assert len(due) == 1

    def test_mark_posted(self, db: Database) -> None:
        pid = db.add_post("x", "content")
        db.mark_posted(pid, "https://x.com/u/status/1")
        due = db.due_posts("2099-01-01T00:00:00")
        assert due == []

    def test_mark_failed(self, db: Database) -> None:
        pid = db.add_post("x", "content")
        db.mark_failed(pid, "rate limited")
        due = db.due_posts("2099-01-01T00:00:00")
        assert due == []


# -- mentions ----------------------------------------------------------------

class TestMentions:
    def test_add_and_unread(self, db: Database) -> None:
        mid = db.add_mention("x", "alice", "hi", "2025-01-01T00:00:00")
        assert isinstance(mid, int)
        unread = db.unread_mentions()
        assert len(unread) == 1
        assert unread[0]["author"] == "alice"

    def test_mark_replied(self, db: Database) -> None:
        mid = db.add_mention("reddit", "bob", "hey", "2025-01-01T00:00:00")
        db.mark_replied(mid)
        assert db.unread_mentions() == []


# -- counters ----------------------------------------------------------------

class TestCounters:
    def test_increment_and_get(self, db: Database) -> None:
        db.increment("test_key", 5)
        assert db.get_counter("test_key") == 5
        db.increment("test_key", 3)
        assert db.get_counter("test_key") == 8

    def test_get_counter_default_zero(self, db: Database) -> None:
        assert db.get_counter("nonexistent") == 0

    def test_monthly_post_count_starts_at_zero(self, db: Database) -> None:
        assert db.monthly_post_count("x") == 0

    def test_monthly_post_count_after_increment(self, db: Database) -> None:
        from datetime import datetime, timezone

        key = f"posts:x:{datetime.now(timezone.utc):%Y-%m}"
        db.increment(key, 15)
        assert db.monthly_post_count("x") == 15
