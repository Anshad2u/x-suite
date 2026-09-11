import json
from datetime import datetime, timezone

import db


def init_dbs():
    db.execute('''CREATE TABLE IF NOT EXISTS followers (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        display_name TEXT,
        bio TEXT,
        followers_count INTEGER DEFAULT 0,
        following_count INTEGER DEFAULT 0,
        tweets_count INTEGER DEFAULT 0,
        verified BOOLEAN DEFAULT FALSE,
        created_at TEXT,
        fetched_at TIMESTAMPTZ DEFAULT NOW()
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS groups (
        name TEXT PRIMARY KEY,
        description TEXT DEFAULT '',
        color TEXT DEFAULT '#6366f1',
        created_at TIMESTAMPTZ DEFAULT NOW(),
        scrape_config JSONB DEFAULT '{}'::jsonb
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS follower_groups (
        follower_id INTEGER REFERENCES followers(id) ON DELETE CASCADE,
        group_name TEXT REFERENCES groups(name) ON DELETE CASCADE,
        added_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (follower_id, group_name)
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS tweets (
        tweet_id TEXT PRIMARY KEY,
        username TEXT,
        content TEXT,
        reply_count INTEGER DEFAULT 0,
        retweet_count INTEGER DEFAULT 0,
        like_count INTEGER DEFAULT 0,
        view_count BIGINT DEFAULT 0,
        posted_at TEXT,
        scraped_at TIMESTAMPTZ DEFAULT NOW()
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS posted_log (
        id SERIAL PRIMARY KEY,
        source_tweet_id TEXT UNIQUE,
        source_username TEXT,
        group_name TEXT,
        posted_tweet_ids TEXT,
        content TEXT,
        posted_at TIMESTAMPTZ DEFAULT NOW()
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS mentions (
        id SERIAL PRIMARY KEY,
        tweet_id TEXT UNIQUE,
        username TEXT,
        author TEXT,
        content TEXT,
        tweet_url TEXT,
        posted_at TEXT,
        alerted BOOLEAN DEFAULT FALSE,
        seen_at TIMESTAMPTZ DEFAULT NOW()
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS reddit_mentions (
        id TEXT PRIMARY KEY,
        author TEXT,
        content TEXT,
        permalink TEXT,
        posted_at TEXT,
        alerted BOOLEAN DEFAULT FALSE,
        seen_at TIMESTAMPTZ DEFAULT NOW()
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS reddit_posts_log (
        id SERIAL PRIMARY KEY,
        title TEXT,
        content TEXT,
        subreddit TEXT,
        permalink TEXT,
        posted_at TIMESTAMPTZ DEFAULT NOW()
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS reddit_feed_log (
        id SERIAL PRIMARY KEY,
        entry_id TEXT UNIQUE,
        subreddit TEXT,
        author TEXT,
        title TEXT,
        link TEXT,
        updated_at TEXT,
        alerted BOOLEAN DEFAULT FALSE,
        seen_at TIMESTAMPTZ DEFAULT NOW()
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS posted_engagement (
        id SERIAL PRIMARY KEY,
        tweet_id TEXT UNIQUE,
        likes INTEGER DEFAULT 0,
        reposts INTEGER DEFAULT 0,
        replies INTEGER DEFAULT 0,
        fetched_at TIMESTAMPTZ DEFAULT NOW()
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS source_scores (
        source_key TEXT PRIMARY KEY,
        posts INTEGER DEFAULT 0,
        sum_engagement INTEGER DEFAULT 0,
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )''')
    db.execute('ALTER TABLE posted_log ADD COLUMN IF NOT EXISTS source_key TEXT')
    db.execute('ALTER TABLE posted_log ADD COLUMN IF NOT EXISTS posted_tweet_id TEXT')

    # --- post queue (migrated from social-agent's SQLite `posts` table) ---
    # Distinct from posted_log: posted_log records what was published and
    # from which source (provenance + engagement learning); post_queue is
    # the pending-work list the scheduler drains.
    db.execute('''CREATE TABLE IF NOT EXISTS post_queue (
        id SERIAL PRIMARY KEY,
        platform TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending'
            CHECK (status IN ('pending','posted','failed')),
        scheduled_at TIMESTAMPTZ,
        posted_at TIMESTAMPTZ,
        content TEXT NOT NULL,
        permalink TEXT,
        error TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    )''')
    db.execute('''CREATE INDEX IF NOT EXISTS idx_post_queue_due
        ON post_queue (status, scheduled_at)''')

    # --- counters (migrated from social-agent's SQLite `counters` table) ---
    db.execute('''CREATE TABLE IF NOT EXISTS counters (
        key TEXT PRIMARY KEY,
        value INTEGER NOT NULL DEFAULT 0
    )''')

    # --- opt-in auto-reply support ---
    db.execute('ALTER TABLE mentions ADD COLUMN IF NOT EXISTS replied BOOLEAN DEFAULT FALSE')
    db.execute('ALTER TABLE reddit_mentions ADD COLUMN IF NOT EXISTS replied BOOLEAN DEFAULT FALSE')


def add_follower(follower_data):
    db.execute('''INSERT INTO followers
        (username, display_name, bio, followers_count, following_count, tweets_count, verified, created_at, fetched_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (username) DO UPDATE SET
            display_name = EXCLUDED.display_name,
            bio = EXCLUDED.bio,
            followers_count = EXCLUDED.followers_count,
            following_count = EXCLUDED.following_count,
            tweets_count = EXCLUDED.tweets_count,
            verified = EXCLUDED.verified,
            created_at = EXCLUDED.created_at,
            fetched_at = NOW()''',
        (follower_data.get('username'),
         follower_data.get('display_name', ''),
         follower_data.get('bio', ''),
         follower_data.get('followers_count', 0),
         follower_data.get('following_count', 0),
         follower_data.get('tweets_count', 0),
         bool(follower_data.get('verified', False)),
         follower_data.get('created_at')))


def get_all_followers():
    return db.query_all('SELECT * FROM followers ORDER BY username')


def get_followers_by_group(group_name):
    return db.query_all('''SELECT f.* FROM followers f
        JOIN follower_groups fg ON f.id = fg.follower_id
        WHERE fg.group_name = %s ORDER BY f.username''', (group_name,))


def get_followers_with_groups(group_name=None):
    if group_name:
        rows = db.query_all('''SELECT f.*, STRING_AGG(g.name, ', ' ORDER BY g.name) AS groups
            FROM followers f
            JOIN follower_groups fg ON f.id = fg.follower_id
            JOIN groups g ON g.name = fg.group_name
            WHERE fg.group_name = %s
            GROUP BY f.id ORDER BY f.username''', (group_name,))
    else:
        rows = db.query_all('''SELECT f.*, COALESCE(STRING_AGG(g.name, ', ' ORDER BY g.name), '') AS groups
            FROM followers f
            LEFT JOIN follower_groups fg ON f.id = fg.follower_id
            LEFT JOIN groups g ON g.name = fg.group_name
            GROUP BY f.id ORDER BY f.username''')
    for r in rows:
        r['verified'] = bool(r.get('verified'))
    return rows


def create_group(name, description='', color='#6366f1'):
    db.execute('''INSERT INTO groups (name, description, color)
        VALUES (%s, %s, %s)
        ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description, color = EXCLUDED.color''',
        (name, description, color))


def get_groups():
    return db.query_all('SELECT * FROM groups ORDER BY name')


def delete_group(name):
    db.execute('DELETE FROM follower_groups WHERE group_name = %s', (name,))
    db.execute('DELETE FROM groups WHERE name = %s', (name,))


def assign_follower_to_group(username, group_name):
    row = db.query_one('SELECT id FROM followers WHERE username = %s', (username,))
    if not row:
        return
    db.execute('''INSERT INTO follower_groups (follower_id, group_name)
        VALUES (%s, %s) ON CONFLICT DO NOTHING''', (row['id'], group_name))


def remove_follower_from_group(username, group_name):
    row = db.query_one('SELECT id FROM followers WHERE username = %s', (username,))
    if not row:
        return
    db.execute('DELETE FROM follower_groups WHERE follower_id = %s AND group_name = %s',
               (row['id'], group_name))


def get_follower_groups(username):
    row = db.query_one('''SELECT ARRAY(SELECT fg.group_name FROM follower_groups fg
        JOIN followers f ON f.id = fg.follower_id
        WHERE f.username = %s ORDER BY fg.group_name) AS groups''', (username,))
    return list(row['groups']) if row and row['groups'] else []


def update_group_scrape_config(group_name, config):
    db.execute('UPDATE groups SET scrape_config = %s::jsonb WHERE name = %s',
               (json.dumps(config), group_name))


def get_group_scrape_config(group_name):
    row = db.query_one('SELECT scrape_config FROM groups WHERE name = %s', (group_name,))
    if row and row['scrape_config']:
        cfg = row['scrape_config']
        return json.loads(cfg) if isinstance(cfg, str) else cfg
    return {}


def get_group_stats():
    rows = db.query_all(
        'SELECT group_name, COUNT(*) AS count FROM follower_groups GROUP BY group_name')
    return {r['group_name']: r['count'] for r in rows}


def get_group_usernames(group_name):
    rows = db.query_all('''SELECT f.username FROM followers f
        JOIN follower_groups fg ON f.id = fg.follower_id
        WHERE fg.group_name = %s''', (group_name,))
    return [r['username'] for r in rows]


def add_tweet(tweet_data):
    db.execute('''INSERT INTO tweets
        (tweet_id, username, content, reply_count, retweet_count, like_count, view_count, posted_at, scraped_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (tweet_id) DO UPDATE SET
            like_count = EXCLUDED.like_count,
            retweet_count = EXCLUDED.retweet_count,
            reply_count = EXCLUDED.reply_count,
            view_count = EXCLUDED.view_count''',
        (tweet_data.get('tweet_id'),
         tweet_data.get('username'),
         tweet_data.get('content', ''),
         tweet_data.get('reply_count', 0),
         tweet_data.get('retweet_count', 0),
         tweet_data.get('like_count', 0),
         tweet_data.get('view_count', 0),
         tweet_data.get('posted_at')))


def add_mention(mention_data):
    db.execute('''INSERT INTO mentions
        (tweet_id, username, author, content, tweet_url, posted_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (tweet_id) DO NOTHING''',
        (mention_data.get('tweet_id'),
         mention_data.get('username'),
         mention_data.get('author', ''),
         mention_data.get('content', ''),
         mention_data.get('tweet_url', ''),
         mention_data.get('posted_at')))


def get_mentions(limit=50):
    return db.query_all(
        'SELECT * FROM mentions ORDER BY seen_at DESC LIMIT %s', (limit,))


def get_unseen_mentions():
    return db.query_all(
        'SELECT * FROM mentions WHERE alerted = FALSE ORDER BY seen_at DESC')


def mark_mentions_alerted(ids):
    if not ids:
        return
    db.execute('UPDATE mentions SET alerted = TRUE WHERE id = ANY(%s)', (ids,))


def add_reddit_mention(mention_data):
    db.execute('''INSERT INTO reddit_mentions
        (id, author, content, permalink, posted_at)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING''',
        (mention_data.get('id'),
         mention_data.get('author', ''),
         mention_data.get('content', ''),
         mention_data.get('permalink', ''),
         mention_data.get('posted_at')))


def get_reddit_mentions(limit=50):
    return db.query_all(
        'SELECT * FROM reddit_mentions ORDER BY seen_at DESC LIMIT %s', (limit,))


def get_unseen_reddit_mentions():
    return db.query_all(
        'SELECT * FROM reddit_mentions WHERE alerted = FALSE ORDER BY seen_at DESC')


def mark_reddit_mentions_alerted(ids):
    if not ids:
        return
    db.execute('UPDATE reddit_mentions SET alerted = TRUE WHERE id = ANY(%s)', (ids,))


def add_reddit_post_log(post_data):
    db.execute('''INSERT INTO reddit_posts_log
        (title, content, subreddit, permalink)
        VALUES (%s, %s, %s, %s)''',
        (post_data.get('title', ''),
         post_data.get('content', ''),
         post_data.get('subreddit', ''),
         post_data.get('permalink', '')))


def get_reddit_post_log(limit=50):
    return db.query_all(
        'SELECT * FROM reddit_posts_log ORDER BY posted_at DESC LIMIT %s', (limit,))


def add_reddit_feed_item(feed_data):
    db.execute('''INSERT INTO reddit_feed_log
        (entry_id, subreddit, author, title, link, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (entry_id) DO NOTHING''',
        (feed_data.get('entry_id'),
         feed_data.get('subreddit', ''),
         feed_data.get('author', ''),
         feed_data.get('title', ''),
         feed_data.get('link', ''),
         feed_data.get('updated_at', '')))


def get_unseen_reddit_feed_items():
    return db.query_all(
        'SELECT * FROM reddit_feed_log WHERE alerted = FALSE ORDER BY seen_at DESC')


def mark_reddit_feed_alerted(ids):
    if not ids:
        return
    db.execute('UPDATE reddit_feed_log SET alerted = TRUE WHERE id = ANY(%s)', (ids,))


def get_reddit_feed_log(limit=50):
    return db.query_all(
        'SELECT * FROM reddit_feed_log ORDER BY seen_at DESC LIMIT %s', (limit,))


def get_reddit_candidates(limit=20):
    return db.query_all('''SELECT f.* FROM reddit_feed_log f
        WHERE f.alerted = FALSE
          AND NOT EXISTS (SELECT 1 FROM posted_log p
                          WHERE p.source_tweet_id = 'r:' || f.entry_id)
        ORDER BY f.seen_at DESC LIMIT %s''', (limit,))


def add_posted_engagement(data):
    db.execute('''INSERT INTO posted_engagement (tweet_id, likes, reposts, replies)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (tweet_id) DO UPDATE SET
            likes = EXCLUDED.likes,
            reposts = EXCLUDED.reposts,
            replies = EXCLUDED.replies,
            fetched_at = NOW()''',
        (data.get('tweet_id'),
         data.get('likes', 0),
         data.get('reposts', 0),
         data.get('replies', 0)))


def get_unscored_posts(limit=20):
    return db.query_all('''SELECT p.* FROM posted_log p
        WHERE p.posted_tweet_id IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM posted_engagement e
                          WHERE e.tweet_id = p.posted_tweet_id)
        ORDER BY p.posted_at DESC LIMIT %s''', (limit,))


def upsert_source_score(source_key, engagement):
    db.execute('''INSERT INTO source_scores (source_key, posts, sum_engagement)
        VALUES (%s, 1, %s)
        ON CONFLICT (source_key) DO UPDATE SET
            posts = source_scores.posts + 1,
            sum_engagement = source_scores.sum_engagement + EXCLUDED.sum_engagement,
            updated_at = NOW()''',
        (source_key, engagement))


def get_source_scores():
    return db.query_all('SELECT * FROM source_scores ORDER BY sum_engagement DESC')


# --- post queue --------------------------------------------------------------
# Implements the PostQueue contract expected by social_agent.scheduler.
# See packages/agent/README.md for the injection contract.

def queue_add_post(platform, content, scheduled_at=None):
    row = db.query_one('''INSERT INTO post_queue (platform, content, scheduled_at)
        VALUES (%s, %s, %s) RETURNING id''', (platform, content, scheduled_at))
    return row['id']


def queue_due_posts(now_iso):
    return db.query_all('''SELECT * FROM post_queue
        WHERE status = 'pending'
          AND (scheduled_at IS NULL OR scheduled_at <= %s)
        ORDER BY scheduled_at ASC NULLS FIRST''', (now_iso,))


def queue_mark_posted(post_id, permalink):
    """Mark a queue row posted and append it to posted_log, atomically.

    posted_log is what feeds the engagement-learning loop, so it must not
    drift from the queue. Both writes happen on one connection/transaction.
    """
    # Permalinks end in the platform's post id (e.g. .../status/123 -> 123).
    posted_id = (permalink or '').rstrip('/').rsplit('/', 1)[-1] or None

    conn = db.get_conn()
    with conn.cursor() as cur:
        cur.execute('''UPDATE post_queue
            SET status = 'posted', posted_at = NOW(), permalink = %s
            WHERE id = %s''', (permalink, post_id))
        cur.execute('SELECT platform, content FROM post_queue WHERE id = %s', (post_id,))
        row = cur.fetchone()
        if row:
            platform, content = row[0], row[1]
            cur.execute('''INSERT INTO posted_log
                (content, posted_at, source_key, posted_tweet_id)
                VALUES (%s, NOW(), %s, %s)''',
                (content, f'queue:{platform}', posted_id))
    conn.commit()


def queue_mark_failed(post_id, error):
    db.execute('''UPDATE post_queue SET status = 'failed', error = %s
        WHERE id = %s''', (error, post_id))


def queue_posts_today():
    row = db.query_one('''SELECT COUNT(*) AS c FROM post_queue
        WHERE status = 'posted' AND posted_at::date = NOW()::date''')
    return row['c'] if row else 0


# --- counters ----------------------------------------------------------------

def counter_increment(key, n=1):
    db.execute('''INSERT INTO counters (key, value) VALUES (%s, %s)
        ON CONFLICT (key) DO UPDATE SET value = counters.value + %s''', (key, n, n))


def counter_get(key):
    row = db.query_one('SELECT value FROM counters WHERE key = %s', (key,))
    return row['value'] if row else 0
