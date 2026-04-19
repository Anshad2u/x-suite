from Scweet import Scweet
import time

_token = None
_proxy = None
_scweet = None

def _get_scweet():
    global _token, _proxy, _scweet
    import config
    if config.X_AUTH_TOKEN != _token:
        _token = config.X_AUTH_TOKEN
        _proxy = config.X_PROXY
        if _token:
            _scweet = Scweet(auth_token=_token, proxy=_proxy if _proxy else None)
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

    def fetch_group_tweets(self, group_name, usernames, scrape_config):
        s = _get_scweet()
        if not s:
            return {"error": "No auth token configured"}
        
        results = []
        
        keywords = scrape_config.get('keywords', [])
        since = scrape_config.get('since', '')
        limit = scrape_config.get('limit', 100)
        
        for username in usernames:
            try:
                if keywords:
                    for kw in keywords:
                        query = f"from:{username} {kw}"
                        tweets = s.search(query, since=since, limit=limit)
                        results.extend(tweets)
                else:
                    tweets = s.get_profile_tweets([username], limit=limit)
                    results.extend(tweets)
                
                time.sleep(1)
            except Exception as e:
                continue
        
        return {"success": True, "tweets": results}