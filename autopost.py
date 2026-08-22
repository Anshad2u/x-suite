"""Auto-post pipeline: pick top tweet from a group, modify, post (thread if long)."""
import random
import re
from datetime import datetime

import db

MAX_CHARS = 230

ENGAGEMENT_SQL = '''SELECT t.*, f.username AS src_username
    FROM tweets t
    JOIN followers f ON f.username = t.username
    JOIN follower_groups fg ON fg.follower_id = f.id AND fg.group_name = %s
    WHERE t.content IS NOT NULL AND LENGTH(t.content) > 40
      AND NOT EXISTS (SELECT 1 FROM posted_log p WHERE p.source_tweet_id = t.tweet_id)
    ORDER BY (t.like_count * 0.5 + t.retweet_count * 2 + t.reply_count * 20) DESC
    LIMIT 15'''


def select_top(group_name):
    rows = db.query_all(ENGAGEMENT_SQL, (group_name,))
    return random.choice(rows[:10]) if rows else None


def _clean(text):
    text = re.sub(r"https://t\.co/\w+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_thread(text, max_chars=MAX_CHARS):
    chunks = []
    remaining = text
    while len(remaining) > max_chars:
        cut = remaining.rfind(". ", 0, max_chars)
        if cut < max_chars // 2:
            cut = remaining.rfind(" ", 0, max_chars)
        if cut <= 0:
            cut = max_chars
        chunks.append(remaining[:cut + 1].strip())
        remaining = remaining[cut + 1:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def prepare(source_tweet):
    raw = source_tweet["content"]
    cleaned = _clean(raw)
    thread = split_thread(cleaned)
    if len(thread) == 1:
        thread = [cleaned]
    for i, c in enumerate(thread):
        thread[i] = f"{c} ({i + 1}/{len(thread)})" if len(thread) > 1 else c
    return thread


def log_post(source_tweet, posted_ids, final_text):
    db.execute('''INSERT INTO posted_log
        (source_tweet_id, source_username, group_name, posted_tweet_ids, content, posted_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
        ON CONFLICT (source_tweet_id) DO NOTHING''',
        (str(source_tweet.get('tweet_id')),
         source_tweet.get('src_username') or source_tweet.get('username'),
         source_tweet.get('_group', ''),
         ",".join(posted_ids),
         " || ".join(final_text)))


def init_log_table():
    db.execute('''CREATE TABLE IF NOT EXISTS posted_log (
        id SERIAL PRIMARY KEY,
        source_tweet_id TEXT UNIQUE,
        source_username TEXT,
        group_name TEXT,
        posted_tweet_ids TEXT,
        content TEXT,
        posted_at TIMESTAMPTZ DEFAULT NOW()
    )''')


def run_once(poster, group_name, dry_run=False):
    src = select_top(group_name)
    if not src:
        return {"status": "no_candidates", "reason": "all top tweets already used or table empty"}

    src['_group'] = group_name
    thread = prepare(src)

    if dry_run:
        return {"status": "dry_run", "source": {
            "tweet_id": str(src.get('tweet_id')), "username": src.get('src_username'),
            "likes": src.get('like_count'), "rts": src.get('retweet_count'),
        }, "thread": thread}

    ids = poster.post_thread(thread)
    log_post(src, ids, thread)
    return {"status": "posted", "posted_ids": ids, "thread": thread,
            "source": {"tweet_id": str(src.get('tweet_id')), "username": src.get('src_username')}}
