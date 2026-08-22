from functools import wraps

from flask import Flask, jsonify, request, send_file, Response
from flask_cors import CORS

import config
import db
from data_models import (
    init_dbs, add_follower, get_all_followers, get_followers_by_group,
    get_followers_with_groups, create_group, get_groups, assign_follower_to_group,
    remove_follower_from_group, get_follower_groups, delete_group,
    update_group_scrape_config, get_group_scrape_config, get_group_stats,
    get_group_usernames,
)
from scraper import FollowerScraper
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)

init_dbs()

scraper = FollowerScraper()


def _require_auth():
    password = config.APP_PASSWORD
    if not password:
        return None
    auth = request.authorization
    if auth and auth.type == "basic" and auth.password == password:
        return None
    return Response(
        "Authentication required", 401,
        {"WWW-Authenticate": 'Basic realm="follower-dashboard"'},
    )


@app.before_request
def auth_gate():
    secret = config.AUTO_POST_SECRET
    if secret and request.headers.get("X-Auto-Post-Secret") == secret:
        return None
    resp = _require_auth()
    if resp is not None:
        return resp


def _autopost_secret_ok():
    return bool(config.AUTO_POST_SECRET) and \
        request.headers.get("X-Auto-Post-Secret") == config.AUTO_POST_SECRET


@app.route('/api/auto-post', methods=['POST'])
def auto_post():
    if not _autopost_secret_ok():
        return jsonify({'error': 'invalid secret'}), 403
    import autopost
    from poster import XPoster, PostError

    today_count = autopost.db.query_one(
        'SELECT COUNT(*) AS c FROM posted_log WHERE posted_at::date = NOW()::date')['c']
    if today_count >= config.AUTO_POST_MAX_PER_DAY:
        return jsonify({'status': 'daily_limit_reached', 'posted_today': today_count})

    try:
        result = autopost.run_once(XPoster(), config.AUTO_POST_GROUP)
        return jsonify(result)
    except PostError as e:
        return jsonify({'status': 'post_failed', 'error': str(e)}), 500
    except Exception as e:
        import traceback
        return jsonify({'status': 'error', 'error': str(e),
                        'trace': traceback.format_exc()[-1200:]}), 500


@app.route('/api/auto-post/dry-run', methods=['GET', 'POST'])
def auto_post_dry_run():
    if not _autopost_secret_ok():
        return jsonify({'error': 'invalid secret'}), 403
    import autopost
    return jsonify(autopost.run_once(None, config.AUTO_POST_GROUP, dry_run=True))


@app.route('/api/posted-log', methods=['GET'])
def posted_log():
    rows = db.query_all(
        'SELECT * FROM posted_log ORDER BY posted_at DESC LIMIT 50')
    for r in rows:
        r['posted_at'] = str(r['posted_at'])
    return jsonify(rows)


@app.route('/')
def index():
    return send_file(os.path.join(BASE_DIR, 'index.html'))


@app.route('/api/followers', methods=['GET'])
def get_followers():
    group = request.args.get('group')
    followers = get_followers_with_groups(group)
    return jsonify(followers)


@app.route('/api/followers/<username>', methods=['GET'])
def get_follower(username):
    rows = get_followers_with_groups()
    for r in rows:
        if r.get('username') == username:
            r['groups'] = [g.strip() for g in (r.get('groups') or '').split(',') if g.strip()]
            return jsonify(r)
    return jsonify({'error': 'Not found'}), 404


@app.route('/api/groups', methods=['GET'])
def api_get_groups():
    groups = get_groups()
    stats = get_group_stats()

    result = []
    for g in groups:
        result.append({
            'name': g['name'],
            'description': g['description'],
            'color': g['color'],
            'created_at': str(g['created_at']),
            'count': stats.get(g['name'], 0)
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
    config_data = get_group_scrape_config(name)
    return jsonify(config_data)


@app.route('/api/scrape/following', methods=['POST'])
def scrape_following():
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

    usernames = get_group_usernames(group_name)

    if not usernames:
        return jsonify({'error': 'No followers in group'})

    scrape_config = get_group_scrape_config(group_name)
    max_accounts = data.get('max_accounts')

    result = scraper.fetch_group_tweets(group_name, usernames, scrape_config, max_accounts)
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
        'configured': bool(config.X_AUTH_TOKEN),
        'has_proxy': bool(config.X_PROXY),
        'db': bool(os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")),
        'auth_enabled': bool(config.APP_PASSWORD)
    })


@app.route('/api/analyze-tweets/<username>', methods=['GET'])
def analyze_tweets_endpoint(username):
    """Analyze a user's tweets and return scored results.

    Requires the tweet_analyzer.py module to be importable.
    Uses browser automation (Playwright) if available.
    """
    import json as _json
    try:
        from tweet_analyzer import scrape_all_tweets
        tweets = scrape_all_tweets(username, max_tweets=100)

        analyzed = []
        from tweet_analyzer import calculate_score
        for t in tweets:
            m = t.get('metrics', {})
            score_data = calculate_score(
                m.get('reply_count', 0),
                m.get('retweet_count', 0),
                m.get('like_count', 0),
                m.get('bookmark_count', 0),
                m.get('view_count', 0),
            )
            content = t.get('content', '').replace('\\n', '\n').strip()
            analyzed.append({
                'tweet_id': t.get('tweet_id', ''),
                'url': t.get('url', ''),
                'date': t.get('created_at', ''),
                'content': content[:200],
                'full_content': content,
                'score': score_data,
                'raw_metrics': {
                    'replies': m.get('reply_count', 0),
                    'reposts': m.get('retweet_count', 0),
                    'likes': m.get('like_count', 0),
                    'bookmarks': m.get('bookmark_count', 0),
                    'views': m.get('view_count', 0),
                }
            })

        analyzed.sort(key=lambda x: x['score']['engagement_score'], reverse=True)
        return jsonify({
            'username': username,
            'total_tweets': len(analyzed),
            'formula': 'Score = (Replies * 20) + (Reposts * 2) + (Likes * 0.5) + (Bookmarks * 80)',
            'tweets': analyzed,
        })
    except ImportError:
        return jsonify({'error': 'tweet_analyzer module not available'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=False, port=5000, use_reloader=False)
