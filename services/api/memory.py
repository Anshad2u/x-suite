import json
from datetime import datetime, timezone

import db


def init_memory():
    db.execute('''CREATE TABLE IF NOT EXISTS observed_posts (
        id TEXT PRIMARY KEY,
        platform TEXT NOT NULL,
        feed TEXT,
        author TEXT,
        title TEXT,
        body TEXT,
        link TEXT,
        posted_at TEXT,
        first_seen TIMESTAMPTZ DEFAULT NOW(),
        last_seen TIMESTAMPTZ DEFAULT NOW(),
        seen_count INTEGER DEFAULT 1
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS post_insights (
        id TEXT PRIMARY KEY REFERENCES observed_posts(id) ON DELETE CASCADE,
        topic TEXT,
        insight TEXT,
        is_new BOOLEAN DEFAULT FALSE,
        relevance REAL DEFAULT 0,
        confidence REAL DEFAULT 0,
        follow_worthy BOOLEAN DEFAULT FALSE,
        decision TEXT DEFAULT 'learn',
        analyzed_at TIMESTAMPTZ DEFAULT NOW()
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS accounts (
        username TEXT PRIMARY KEY,
        platform TEXT NOT NULL,
        display_name TEXT,
        observed_posts INTEGER DEFAULT 0,
        relevant_posts INTEGER DEFAULT 0,
        relevance_score REAL DEFAULT 0,
        confidence REAL DEFAULT 0,
        topics JSONB DEFAULT '[]'::jsonb,
        first_seen TIMESTAMPTZ DEFAULT NOW(),
        last_seen TIMESTAMPTZ DEFAULT NOW(),
        watchlisted BOOLEAN DEFAULT FALSE
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS topics (
        name TEXT PRIMARY KEY,
        observed_count INTEGER DEFAULT 0,
        relevant_count INTEGER DEFAULT 0,
        last_seen TIMESTAMPTZ DEFAULT NOW()
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS account_topics (
        username TEXT REFERENCES accounts(username) ON DELETE CASCADE,
        topic TEXT,
        weight REAL DEFAULT 0,
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (username, topic)
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS decisions_log (
        id SERIAL PRIMARY KEY,
        post_id TEXT REFERENCES observed_posts(id) ON DELETE CASCADE,
        decision TEXT,
        reason TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )''')


def upsert_post(p):
    db.execute('''INSERT INTO observed_posts
        (id, platform, feed, author, title, body, link, posted_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            last_seen = NOW(), seen_count = observed_posts.seen_count + 1''',
        (p.get('id'), p.get('platform'), p.get('feed'), p.get('author'),
         p.get('title', ''), p.get('body', ''), p.get('link'), p.get('posted_at')))


def upsert_insight(post_id, data):
    db.execute('''INSERT INTO post_insights
        (id, topic, insight, is_new, relevance, confidence, follow_worthy, decision)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            topic = EXCLUDED.topic, insight = EXCLUDED.insight,
            is_new = EXCLUDED.is_new, relevance = EXCLUDED.relevance,
            confidence = EXCLUDED.confidence, follow_worthy = EXCLUDED.follow_worthy,
            decision = EXCLUDED.decision, analyzed_at = NOW()''',
        (post_id, data.get('topic'), data.get('insight'),
         bool(data.get('is_new')), float(data.get('relevance', 0)),
         float(data.get('confidence', 0)), bool(data.get('follow_worthy')),
         data.get('decision', 'learn')))


def upsert_account(username, platform, display_name='', topics=None):
    db.execute('''INSERT INTO accounts (username, platform, display_name, topics)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (username) DO UPDATE SET
            display_name = EXCLUDED.display_name,
            last_seen = NOW()''',
        (username, platform, display_name, json.dumps(topics or [])))


def bump_account_post(username, relevant=False):
    db.execute('''UPDATE accounts SET
        observed_posts = observed_posts + 1,
        relevant_posts = relevant_posts + %s,
        last_seen = NOW()
        WHERE username = %s''', (1 if relevant else 0, username))


def set_account_topics(username, topic_weights):
    db.execute('DELETE FROM account_topics WHERE username = %s', (username,))
    for topic, weight in topic_weights.items():
        db.execute('''INSERT INTO account_topics (username, topic, weight)
            VALUES (%s, %s, %s)
            ON CONFLICT (username, topic) DO UPDATE SET weight = EXCLUDED.weight, updated_at = NOW()''',
            (username, topic, weight))


def upsert_topic(name, relevant=False):
    db.execute('''INSERT INTO topics (name, observed_count, relevant_count)
        VALUES (%s, 1, %s)
        ON CONFLICT (name) DO UPDATE SET
            observed_count = topics.observed_count + 1,
            relevant_count = topics.relevant_count + %s,
            last_seen = NOW()''',
        (name, 1 if relevant else 0, 1 if relevant else 0))


def log_decision(post_id, decision, reason):
    db.execute('''INSERT INTO decisions_log (post_id, decision, reason)
        VALUES (%s, %s, %s)''', (post_id, decision, reason))


def unanalyzed_posts(limit=30):
    return db.query_all('''SELECT p.* FROM observed_posts p
        WHERE NOT EXISTS (SELECT 1 FROM post_insights i WHERE i.id = p.id)
        ORDER BY p.first_seen DESC LIMIT %s''', (limit,))


def get_post(post_id):
    return db.query_one('SELECT * FROM observed_posts WHERE id = %s', (post_id,))


def get_watchlist(limit=100, min_relevance=0.0):
    return db.query_all('''SELECT a.* FROM accounts a
        WHERE a.watchlisted = TRUE OR a.relevance_score >= %s
        ORDER BY a.relevance_score DESC LIMIT %s''', (min_relevance, limit))


def build_watchlist(relevance_threshold=0.4, min_observed=2, confidence_threshold=0.5, limit=100):
    db.execute('''UPDATE accounts SET watchlisted = FALSE
        WHERE observed_posts > 0 AND (relevance_score < %s OR confidence < %s OR observed_posts < %s)''',
        (relevance_threshold, confidence_threshold, min_observed))
    db.execute('''UPDATE accounts SET watchlisted = TRUE
        WHERE observed_posts >= %s AND relevance_score >= %s AND confidence >= %s''',
        (min_observed, relevance_threshold, confidence_threshold))
    return get_watchlist(limit=limit, min_relevance=relevance_threshold)


def get_account(username):
    return db.query_one('SELECT * FROM accounts WHERE username = %s', (username,))


def refresh_account_scores():
    db.execute('''UPDATE accounts a SET
        relevance_score = CASE WHEN a.observed_posts = 0 THEN 0
            ELSE a.relevant_posts::float / a.observed_posts END,
        confidence = LEAST(a.observed_posts::float / 10.0, 1.0)''')


def top_topics(limit=50):
    return db.query_all('SELECT * FROM topics ORDER BY relevant_count DESC, observed_count DESC LIMIT %s', (limit,))


def summary():
    return {
        'posts': db.query_one('SELECT COUNT(*) AS n FROM observed_posts')['n'],
        'analyzed': db.query_one('SELECT COUNT(*) AS n FROM post_insights')['n'],
        'accounts': db.query_one('SELECT COUNT(*) AS n FROM accounts')['n'],
        'topics': db.query_one('SELECT COUNT(*) AS n FROM topics')['n'],
        'watchlist': len(get_watchlist(limit=1000)),
    }