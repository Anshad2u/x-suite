"""Tests for social_agent.drafts."""

from __future__ import annotations

from pathlib import Path

import pytest

from social_agent.drafts import (
    _parse_frontmatter,
    add_draft,
    list_drafts,
    load_due_drafts,
)


class TestParseFrontmatter:
    def test_parses_meta_and_body(self) -> None:
        text = "---\nplatform: x\nscheduled_at: 2025-06-01T00:00:00\n---\nHello world"
        meta, body = _parse_frontmatter(text)
        assert meta["platform"] == "x"
        assert meta["scheduled_at"] == "2025-06-01T00:00:00"
        assert body == "Hello world"

    def test_no_frontmatter(self) -> None:
        meta, body = _parse_frontmatter("Just plain text")
        assert meta == {}
        assert body == "Just plain text"

    def test_empty_body(self) -> None:
        meta, body = _parse_frontmatter("---\nplatform: reddit\n---\n")
        assert meta["platform"] == "reddit"
        assert body == ""

    def test_multiline_body(self) -> None:
        text = "---\nplatform: x\n---\nLine one\nLine two\nLine three"
        _, body = _parse_frontmatter(text)
        assert "Line one" in body
        assert "Line three" in body


class TestListDrafts:
    def test_lists_md_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("---\nplatform: x\n---\nDraft A")
        (tmp_path / "b.md").write_text("---\nplatform: reddit\n---\nDraft B")
        (tmp_path / "c.txt").write_text("not a draft")
        drafts = list_drafts(tmp_path)
        assert len(drafts) == 2
        platforms = {d["platform"] for d in drafts}
        assert platforms == {"x", "reddit"}

    def test_empty_dir(self, tmp_path: Path) -> None:
        assert list_drafts(tmp_path) == []

    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        assert list_drafts(tmp_path / "nope") == []


class TestAddDraft:
    def test_creates_file(self, tmp_path: Path) -> None:
        path = add_draft("x", "My post content", drafts_dir=tmp_path)
        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "platform: x" in text
        assert "My post content" in text

    def test_with_scheduled_at(self, tmp_path: Path) -> None:
        path = add_draft("reddit", "Later", scheduled_at="2025-12-01T00:00:00", drafts_dir=tmp_path)
        text = path.read_text(encoding="utf-8")
        assert "scheduled_at: 2025-12-01T00:00:00" in text


class TestLoadDueDrafts:
    def test_returns_due(self, tmp_path: Path) -> None:
        add_draft("x", "Past draft", scheduled_at="2025-01-01T00:00:00", drafts_dir=tmp_path)
        add_draft("x", "Future draft", scheduled_at="2099-01-01T00:00:00", drafts_dir=tmp_path)
        due = load_due_drafts("2025-06-01T00:00:00", tmp_path)
        assert len(due) == 1
        assert due[0]["content"] == "Past draft"

    def test_no_schedule_is_due(self, tmp_path: Path) -> None:
        add_draft("x", "Immediate", drafts_dir=tmp_path)
        due = load_due_drafts("2025-01-01T00:00:00", tmp_path)
        assert len(due) == 1
