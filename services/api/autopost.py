"""Auto-post pipeline: pick the best candidate (X group tweet or Reddit feed
item), score it by source engagement history, post, and record the source so
the learning loop can credit it."""
import random
import re

import db
from data_models import (
    get_reddit_candidates, mark_reddit_feed_alerted, get_source_scores,
)

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


def _cap280(text):
    if len(text) <= 280:
        return text
    cut = text.rfind(" ", 0, 277)
    if cut < 100:
        cut = 277
    return text[:cut].rstrip() + "…"


def reddit_candidates(limit=15):
    out = []
    for r in get_reddit_candidates(limit):
        out.append({
            'tweet_id': 'r:' + r['entry_id'],
            'content': _cap280(f"{r['title']}\n{r['link']}"),
            'username': r['author'] or '',
            'src_username': r['subreddit'],
            '_group': r['subreddit'],
            '_source_key': 'reddit:' + r['subreddit'],
            '_reddit_id': r['id'],
            'like_count': 0,
            'retweet_count': 0,
            'reply_count': 0,
        })
    return out


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
        (source_tweet_id, source_username, group_name, posted_tweet_ids, content,
         posted_at, source_key, posted_tweet_id)
        VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s)
        ON CONFLICT (source_tweet_id) DO NOTHING''',
        (str(source_tweet.get('tweet_id')),
         source_tweet.get('src_username') or source_tweet.get('username'),
         source_tweet.get('_group', ''),
         ",".join(posted_ids),
         " || ".join(final_text),
         source_tweet.get('_source_key', ''),
         posted_ids[0] if posted_ids else None))


def init_log_table():
    db.execute('''CREATE TABLE IF NOT EXISTS posted_log (
        id SERIAL PRIMARY KEY,
        source_tweet_id TEXT UNIQUE,
        source_username TEXT,
        group_name TEXT,
        posted_tweet_ids TEXT,
        content TEXT,
        posted_at TIMESTAMPTZ DEFAULT NOW(),
        source_key TEXT,
        posted_tweet_id TEXT
    )''')
    db.execute('ALTER TABLE posted_log ADD COLUMN IF NOT EXISTS source_key TEXT')
    db.execute('ALTER TABLE posted_log ADD COLUMN IF NOT EXISTS posted_tweet_id TEXT')


def run_once(poster, group_name, dry_run=False, include_reddit=True, limit=1):
    score_rows = {s['source_key']: s for s in get_source_scores()}

    def prior(key):
        s = score_rows.get(key)
        if s and s['posts']:
            return s['sum_engagement'] / s['posts']
        return 2.0

    candidates = []
    src = select_top(group_name)
    if src:
        src['_group'] = group_name
        src['_source_key'] = 'x:' + group_name
        src['_score'] = (src.get('like_count', 0) * 0.0005
                         + src.get('retweet_count', 0) * 0.002
                         + src.get('reply_count', 0) * 0.02)
        candidates.append(src)

    if include_reddit:
        for rc in reddit_candidates(15):
            rc['_score'] = prior(rc['_source_key'])
            candidates.append(rc)

    if not candidates:
        return {"status": "no_candidates", "reason": "no unused group tweets or reddit items"}

    candidates.sort(key=lambda c: c.get('_score', 0), reverse=True)
    picks = candidates[:limit] if limit else candidates
    posted = []

    for pick in picks:
        if pick['_source_key'].startswith('reddit:'):
            text = pick['content']
            if dry_run:
                posted.append({'source_key': pick['_source_key'],
                               'score': round(pick['_score'], 2), 'text': text})
                continue
            ids = [poster.post(text)]
            log_post(pick, ids, [text])
            mark_reddit_feed_alerted([pick['_reddit_id']])
            posted.append({'source_key': pick['_source_key'],
                           'score': round(pick['_score'], 2), 'posted_ids': ids})
        else:
            thread = prepare(pick)
            if dry_run:
                posted.append({'source_key': pick['_source_key'],
                               'score': round(pick['_score'], 2), 'thread': thread})
                continue
            ids = poster.post_thread(thread)
            log_post(pick, ids, thread)
            posted.append({'source_key': pick['_source_key'],
                           'score': round(pick['_score'], 2), 'posted_ids': ids})

    return {"status": "posted" if posted else "pending",
            "dry_run": dry_run,
            "posted": posted}