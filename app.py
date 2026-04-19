from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import sqlite3
import os
from config import FOLLOWERS_DB, GROUPS_DB, X_AUTH_TOKEN, X_PROXY

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
from data_models import (
    init_dbs, add_follower, get_all_followers, get_followers_by_group,
    create_group, get_groups, assign_follower_to_group, remove_follower_from_group,
    get_follower_groups, delete_group, update_group_scrape_config, get_group_scrape_config,
    get_group_stats
)
from scraper import FollowerScraper
import json

app = Flask(__name__)
CORS(app)

init_dbs()

# Initialize scraper
scraper = FollowerScraper()

def row_to_dict(cursor, row):
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))

@app.route('/')
def index():
    return send_file(os.path.join(BASE_DIR, 'index.html'))

@app.route('/api/followers', methods=['GET'])
def get_followers():
    group = request.args.get('group')
    if group:
        rows = get_followers_by_group(group)
    else:
        rows = get_all_followers()
    
    conn = sqlite3.connect(FOLLOWERS_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if group:
        c.execute('''SELECT f.*, GROUP_CONCAT(fg.group_name, ', ') as groups 
            FROM followers f 
            JOIN follower_groups fg ON f.id = fg.follower_id 
            WHERE fg.group_name = ? 
            GROUP BY f.id ORDER BY f.username''', (group,))
    else:
        c.execute('SELECT * FROM followers ORDER BY username')
    
    followers = [row_to_dict(c, row) for row in c.fetchall()]
    conn.close()
    
    return jsonify(followers)

@app.route('/api/followers/<username>', methods=['GET'])
def get_follower(username):
    conn = sqlite3.connect(FOLLOWERS_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM followers WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    
    if row:
        follower = dict(row)
        follower['groups'] = get_follower_groups(username)
        return jsonify(follower)
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/groups', methods=['GET'])
def api_get_groups():
    groups = get_groups()
    stats = get_group_stats()
    
    result = []
    for g in groups:
        result.append({
            'name': g[0],
            'description': g[1],
            'color': g[2],
            'created_at': g[3],
            'count': stats.get(g[0], 0)
        })
    
    return jsonify(result)

@app.route('/api/groups', methods=['POST'])
def api_create_group():
    data = request.json
    create_group(data.get('name'), data.get('description', ''), data.get('color', '#6366f1'))
    return jsonify({'success': True})

@app.route('/api/groups/<name>', methods=['DELETE'])
def api_delete_group(name):
    delete_group(name)
    return jsonify({'success': True})

@app.route('/api/groups/<name>/followers', methods=['POST'])
def api_assign_follower(name):
    data = request.json
    username = data.get('username')
    if username:
        assign_follower_to_group(username, name)
    return jsonify({'success': True})

@app.route('/api/groups/<name>/followers', methods=['DELETE'])
def api_remove_follower(name):
    data = request.json
    username = data.get('username')
    if username:
        remove_follower_from_group(username, name)
    return jsonify({'success': True})

@app.route('/api/groups/<name>/scrape-config', methods=['PUT'])
def api_update_scrape_config(name):
    data = request.json
    update_group_scrape_config(name, data)
    return jsonify({'success': True})

@app.route('/api/groups/<name>/scrape-config', methods=['GET'])
def api_get_scrape_config(name):
    config = get_group_scrape_config(name)
    return jsonify(config)

@app.route('/api/scrape/following', methods=['POST'])
def scrape_following():
    import importlib, config
    importlib.reload(config)
    data = request.json
    username = data.get('username', 'me')
    limit = data.get('limit', 1000)
    
    result = scraper.fetch_following(username, limit)
    return jsonify(result)

@app.route('/api/scrape/followers', methods=['POST'])
def scrape_followers():
    data = request.json
    username = data.get('username', 'me')
    limit = data.get('limit', 1000)
    
    result = scraper.fetch_followers(username, limit)
    return jsonify(result)

@app.route('/api/scrape/group', methods=['POST'])
def scrape_group():
    data = request.json
    group_name = data.get('group')
    
    # Get followers in this group
    rows = get_followers_by_group(group_name)
    
    conn = sqlite3.connect(FOLLOWERS_DB)
    c = conn.cursor()
    c.execute('''SELECT f.username FROM followers f 
        JOIN follower_groups fg ON f.id = fg.follower_id 
        WHERE fg.group_name = ?''', (group_name,))
    usernames = [r[0] for r in c.fetchall()]
    conn.close()
    
    if not usernames:
        return jsonify({'error': 'No followers in group'})
    
    # Get scrape config
    config = get_group_scrape_config(group_name)
    
    # Scrape tweets
    result = scraper.fetch_group_tweets(group_name, usernames, config)
    return jsonify(result)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total = len(get_all_followers())
    groups = get_groups()
    group_stats = get_group_stats()
    
    return jsonify({
        'total_followers': total,
        'total_groups': len(groups),
        'group_counts': group_stats
    })

@app.route('/api/config/status', methods=['GET'])
def config_status():
    return jsonify({
        'configured': bool(X_AUTH_TOKEN),
        'has_proxy': bool(X_PROXY)
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)