import psycopg2
import psycopg2.extras

# Importing config performs the env loading (monorepo-root .env first) and
# owns the single POSTGRES_URL definition. Do not load dotenv here as well:
# two loaders in two files was how the merged tree lost its database URL.
import config

POSTGRES_URL = config.POSTGRES_URL


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
