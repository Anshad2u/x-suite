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
