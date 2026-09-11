"""SQLite database layer — stdlib only, no ORM."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

_SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    platform    TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending','posted','failed')),
    scheduled_at TEXT,
    posted_at   TEXT,
    content     TEXT    NOT NULL,
    permalink   TEXT,
    error       TEXT
);

CREATE TABLE IF NOT EXISTS mentions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    platform    TEXT    NOT NULL,
    author      TEXT,
    body        TEXT,
    created_utc TEXT,
    replied     INTEGER DEFAULT 0,
    raw         TEXT
);

CREATE TABLE IF NOT EXISTS counters (
    key         TEXT PRIMARY KEY,
    value       INTEGER NOT NULL DEFAULT 0
);
"""


class Database:
    """Thin wrapper around a SQLite database file."""

    def __init__(self, db_path: str | Path) -> None:
        self._path = str(db_path)
        self._ensure_schema()

    # -- connection helper ---------------------------------------------------

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    # -- posts ---------------------------------------------------------------

    def add_post(
        self,
        platform: str,
        content: str,
        scheduled_at: str | None = None,
    ) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO posts (platform, content, scheduled_at) VALUES (?, ?, ?)",
                (platform, content, scheduled_at),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def due_posts(self, now_iso: str) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM posts WHERE status='pending' "
                "AND (scheduled_at IS NULL OR scheduled_at <= ?) "
                "ORDER BY scheduled_at ASC",
                (now_iso,),
            ).fetchall()
            return [dict(r) for r in rows]

    def mark_posted(self, post_id: int, permalink: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE posts SET status='posted', posted_at=?, permalink=? WHERE id=?",
                (datetime.now(timezone.utc).isoformat(), permalink, post_id),
            )

    def mark_failed(self, post_id: int, error: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE posts SET status='failed', error=? WHERE id=?",
                (error, post_id),
            )

    # -- mentions ------------------------------------------------------------

    def add_mention(
        self,
        platform: str,
        author: str,
        body: str,
        created_utc: str,
        raw: str = "",
    ) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO mentions (platform, author, body, created_utc, raw) "
                "VALUES (?, ?, ?, ?, ?)",
                (platform, author, body, created_utc, raw),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def unread_mentions(self) -> list[dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM mentions WHERE replied=0 ORDER BY created_utc ASC"
            ).fetchall()
            return [dict(r) for r in rows]

    def mark_replied(self, mention_id: int) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE mentions SET replied=1 WHERE id=?", (mention_id,)
            )

    # -- counters ------------------------------------------------------------

    def increment(self, key: str, n: int = 1) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO counters (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = value + ?",
                (key, n, n),
            )

    def get_counter(self, key: str) -> int:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT value FROM counters WHERE key=?", (key,)
            ).fetchone()
            return row["value"] if row else 0

    def monthly_post_count(self, platform: str) -> int:
        key = f"posts:{platform}:{datetime.now(timezone.utc):%Y-%m}"
        return self.get_counter(key)
