import os

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_BASE_DIR, ".env"))
load_dotenv(os.path.join(_BASE_DIR, ".env.local"))

POSTGRES_URL = os.environ.get("POSTGRES_URL_NON_POOLING") or os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL_UNPOOLED") or os.environ.get("DATABASE_URL", "")


_conn_cache = None


def get_conn():
    global _conn_cache
    if _conn_cache is not None:
        try:
            with _conn_cache.cursor() as cur:
                cur.execute("SELECT 1")
            return _conn_cache
        except Exception:
            try:
                _conn_cache.close()
            except Exception:
                pass
            _conn_cache = None
    if not POSTGRES_URL:
        raise RuntimeError("POSTGRES_URL not configured - run 'vercel link' / check env")
    _conn_cache = psycopg2.connect(POSTGRES_URL, connect_timeout=15)
    return _conn_cache


def query_all(sql, params=()):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


def query_one(sql, params=()):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None


def execute(sql, params=()):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
