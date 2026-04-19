import sqlite3
import json
from datetime import datetime
from config import FOLLOWERS_DB, GROUPS_DB

def init_dbs():
    """Initialize both databases"""
    # Followers database
    conn = sqlite3.connect(FOLLOWERS_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS followers (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        display_name TEXT,
        bio TEXT,
        followers_count INTEGER,
        following_count INTEGER,
        tweets_count INTEGER,
        verified BOOLEAN,
        created_at TEXT,
        fetched_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS follower_groups (
        follower_id INTEGER,
        group_name TEXT,
        added_at TEXT,
        PRIMARY KEY (follower_id, group_name),
        FOREIGN KEY (follower_id) REFERENCES followers(id)
    )''')
    conn.commit()
    conn.close()
    
    # Groups database
    conn = sqlite3.connect(GROUPS_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS groups (
        name TEXT PRIMARY KEY,
        description TEXT,
        color TEXT,
        created_at TEXT,
        scrape_config TEXT
    )''')
    conn.commit()
    conn.close()

def add_follower(follower_data):
    """Add or update a follower"""
    conn = sqlite3.connect(FOLLOWERS_DB)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO followers 
        (username, display_name, bio, followers_count, following_count, tweets_count, verified, created_at, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
        (follower_data.get('username'),
         follower_data.get('display_name'),
         follower_data.get('bio'),
         follower_data.get('followers_count', 0),
         follower_data.get('following_count', 0),
         follower_data.get('tweets_count', 0),
         follower_data.get('verified', False),
         follower_data.get('created_at'),
         datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_all_followers():
    """Get all followers"""
    conn = sqlite3.connect(FOLLOWERS_DB)
    c = conn.cursor()
    c.execute('SELECT * FROM followers ORDER BY username')
    rows = c.fetchall()
    conn.close()
    return rows

def get_followers_by_group(group_name):
    """Get followers in a specific group"""
    conn = sqlite3.connect(FOLLOWERS_DB)
    c = conn.cursor()
    c.execute('''SELECT f.* FROM followers f 
        JOIN follower_groups fg ON f.id = fg.follower_id 
        WHERE fg.group_name = ? ORDER BY f.username''', (group_name,))
    rows = c.fetchall()
    conn.close()
    return rows

def create_group(name, description='', color='#6366f1'):
    """Create a new group"""
    conn = sqlite3.connect(GROUPS_DB)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO groups (name, description, color, created_at)
        VALUES (?, ?, ?, ?)''', (name, description, color, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_groups():
    """Get all groups"""
    conn = sqlite3.connect(GROUPS_DB)
    c = conn.cursor()
    c.execute('SELECT * FROM groups ORDER BY name')
    rows = c.fetchall()
    conn.close()
    return rows

def assign_follower_to_group(username, group_name):
    """Assign a follower to a group"""
    conn = sqlite3.connect(FOLLOWERS_DB)
    c = conn.cursor()
    c.execute('SELECT id FROM followers WHERE username = ?', (username,))
    row = c.fetchone()
    if row:
        c.execute('''INSERT OR IGNORE INTO follower_groups (follower_id, group_name, added_at)
            VALUES (?, ?, ?)''', (row[0], group_name, datetime.now().isoformat()))
        conn.commit()
    conn.close()

def remove_follower_from_group(username, group_name):
    """Remove a follower from a group"""
    conn = sqlite3.connect(FOLLOWERS_DB)
    c = conn.cursor()
    c.execute('SELECT id FROM followers WHERE username = ?', (username,))
    row = c.fetchone()
    if row:
        c.execute('DELETE FROM follower_groups WHERE follower_id = ? AND group_name = ?', 
                  (row[0], group_name))
        conn.commit()
    conn.close()

def get_follower_groups(username):
    """Get groups a follower belongs to"""
    conn = sqlite3.connect(FOLLOWERS_DB)
    c = conn.cursor()
    c.execute('SELECT id FROM followers WHERE username = ?', (username,))
    row = c.fetchone()
    if row:
        c.execute('SELECT group_name FROM follower_groups WHERE follower_id = ?', (row[0],))
        groups = [r[0] for r in c.fetchall()]
    else:
        groups = []
    conn.close()
    return groups

def delete_group(name):
    """Delete a group and its assignments"""
    conn = sqlite3.connect(FOLLOWERS_DB)
    c = conn.cursor()
    c.execute('DELETE FROM follower_groups WHERE group_name = ?', (name,))
    conn.commit()
    conn.close()
    
    conn = sqlite3.connect(GROUPS_DB)
    c = conn.cursor()
    c.execute('DELETE FROM groups WHERE name = ?', (name,))
    conn.commit()
    conn.close()

def update_group_scrape_config(group_name, config):
    """Update scrape config for a group"""
    conn = sqlite3.connect(GROUPS_DB)
    c = conn.cursor()
    c.execute('UPDATE groups SET scrape_config = ? WHERE name = ?', 
             (json.dumps(config), group_name))
    conn.commit()
    conn.close()

def get_group_scrape_config(group_name):
    """Get scrape config for a group"""
    conn = sqlite3.connect(GROUPS_DB)
    c = conn.cursor()
    c.execute('SELECT scrape_config FROM groups WHERE name = ?', (group_name,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        return json.loads(row[0])
    return {}

def get_group_stats():
    """Get statistics for all groups"""
    conn = sqlite3.connect(FOLLOWERS_DB)
    c = conn.cursor()
    c.execute('''SELECT fg.group_name, COUNT(fg.follower_id) as count 
        FROM follower_groups fg GROUP BY fg.group_name''')
    stats = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return stats