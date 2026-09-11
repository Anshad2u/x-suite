from Scweet import Scweet
import time
import os

_token = None
_proxy = None
_scweet = None

def _get_scweet():
    global _token, _proxy, _scweet
    import config
    if config.X_AUTH_TOKEN != _token or _scweet is None:
        _token = config.X_AUTH_TOKEN
        _proxy = config.X_PROXY
        _scweet = None
        if _token:
            # Scweet keeps its own SQLite state DB - must live in a writable
            # dir (config.DATA_DIR resolves to /tmp on Vercel).
            from Scweet.config import ScweetConfig
            cfg = ScweetConfig()
            cfg.daily_requests_limit = 500
            cfg.daily_tweets_limit = 50000
            db_path = os.path.join(config.DATA_DIR, "scweet_state.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            _scweet = Scweet(auth_token=_token, proxy=_proxy if _proxy else None,
                             config=cfg, db_path=db_path)
    return _scweet

class FollowerScraper:
    def fetch_following(self, username, limit=1000):
        s = _get_scweet()
        if not s:
            return {"error": "No auth token configured"}
        
        try:
            following = s.get_following([username], limit=limit)
            
            from data_models import add_follower
            for user in following:
                user_data = {
                    'username': user.get('username', ''),
                    'display_name': user.get('name', ''),
                    'bio': user.get('description', ''),
                    'followers_count': user.get('followers_count', 0),
                    'following_count': user.get('following_count', 0),
                    'tweets_count': user.get('statuses_count', 0),
                    'verified': user.get('verified', False),
                    'created_at': user.get('created_at', '')
                }
                add_follower(user_data)
            
            return {"success": True, "count": len(following)}
        except Exception as e:
            return {"error": str(e)}
    
    def fetch_followers(self, username, limit=1000):
        s = _get_scweet()
        if not s:
            return {"error": "No auth token configured"}
        
        try:
            followers = s.get_followers([username], limit=limit)
            
            from data_models import add_follower
            for user in followers:
                user_data = {
                    'username': user.get('username', ''),
                    'display_name': user.get('name', ''),
                    'bio': user.get('description', ''),
                    'followers_count': user.get('followers_count', 0),
                    'following_count': user.get('following_count', 0),
                    'tweets_count': user.get('statuses_count', 0),
                    'verified': user.get('verified', False),
                    'created_at': user.get('created_at', '')
                }
                add_follower(user_data)
            
            return {"success": True, "count": len(followers)}
        except Exception as e:
            return {"error": str(e)}

    def fetch_group_tweets(self, group_name, usernames, scrape_config, max_accounts=None):
        s = _get_scweet()
        if not s:
            return {"error": "No auth token configured"}

        if max_accounts:
            usernames = usernames[:max_accounts]

        results = []

        keywords = scrape_config.get('keywords', [])
        since = scrape_config.get('since', '')
        limit = scrape_config.get('limit', 100)

        from data_models import add_tweet

        for username in usernames:
            try:
                if keywords:
                    tweets = []
                    for kw in keywords:
                        query = f"from:{username} {kw}"
                        tweets.extend(s.search(query, since=since, limit=limit))
                else:
                    tweets = s.get_profile_tweets([username], limit=limit)

                _store_tweets(tweets, username)
                results.extend(tweets)
                time.sleep(1)
            except Exception as e:
                continue

        return {"success": True, "tweets": results, "accounts": len(usernames)}


def _store_tweets(tweets, fallback_username):
    from data_models import add_tweet
    for t in tweets or []:
        user_info = t.get('user') or {}
        try:
            add_tweet({
                'tweet_id': str(t.get('tweet_id', '')),
                'username': user_info.get('screen_name', fallback_username),
                'content': t.get('text', '') or t.get('embedded_text', '') or '',
                'reply_count': t.get('comments', 0) or 0,
                'retweet_count': t.get('retweets', 0) or 0,
                'like_count': t.get('likes', 0) or 0,
                'view_count': 0,
                'posted_at': t.get('timestamp'),
            })
        except Exception:
            continue