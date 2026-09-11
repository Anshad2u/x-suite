"""Draft queue — markdown files with YAML-style frontmatter (hand-rolled)."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DRAFTS_DIR = _PROJECT_ROOT / "drafts"


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split *text* into (metadata_dict, body).

    Expects leading ``---`` line, key: value lines, closing ``---`` line.
    Everything after the second ``---`` is the body.
    Returns ({}, text) if no frontmatter is found.
    """
    if not text.startswith("---"):
        return {}, text.strip()

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text.strip()

    meta_block = parts[1].strip()
    body = parts[2].strip()

    meta: dict[str, str] = {}
    for line in meta_block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, body


def list_drafts(drafts_dir: Path | None = None) -> list[dict[str, Any]]:
    """Return all drafts as list of dicts with keys: platform, content, scheduled_at, path."""
    drafts_dir = drafts_dir or DRAFTS_DIR
    results: list[dict[str, Any]] = []
    if not drafts_dir.exists():
        return results
    for p in sorted(drafts_dir.glob("*.md")):
        text = p.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(text)
        results.append(
            {
                "platform": meta.get("platform", "x"),
                "content": body,
                "scheduled_at": meta.get("scheduled_at"),
                "path": str(p),
            }
        )
    return results


def add_draft(
    platform: str,
    content: str,
    scheduled_at: str | None = None,
    drafts_dir: Path | None = None,
) -> Path:
    """Create a new draft file and return its path."""
    drafts_dir = drafts_dir or DRAFTS_DIR
    drafts_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "-", content[:30].lower()).strip("-")
    filename = f"{ts}-{slug or 'draft'}.md"

    lines = ["---", f"platform: {platform}"]
    if scheduled_at:
        lines.append(f"scheduled_at: {scheduled_at}")
    lines.append("---")
    lines.append(content)

    path = drafts_dir / filename
    path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Created draft %s", path)
    return path


def load_due_drafts(now_iso: str, drafts_dir: Path | None = None) -> list[dict[str, Any]]:
    """Return drafts whose scheduled_at <= *now_iso* (or has no schedule)."""
    results: list[dict[str, Any]] = []
    for d in list_drafts(drafts_dir):
        sched = d["scheduled_at"]
        if sched is None or sched <= now_iso:
            results.append(d)
    return results
