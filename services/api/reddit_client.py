"""Reddit client - PRAW singleton, returns None when credentials are missing."""
import config

_praw = None
_reddit = None


def _get_praw():
    global _praw
    if _praw is None:
        try:
            import praw
            _praw = praw
        except ImportError:
            _praw = False
    return _praw or None


def get_reddit():
    global _reddit
    if _reddit is not None:
        return _reddit
    if not (config.REDDIT_CLIENT_ID and config.REDDIT_CLIENT_SECRET
            and config.REDDIT_USERNAME and config.REDDIT_PASSWORD):
        return None
    praw = _get_praw()
    if not praw:
        return None
    _reddit = praw.Reddit(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        username=config.REDDIT_USERNAME,
        password=config.REDDIT_PASSWORD,
        user_agent=config.REDDIT_USER_AGENT or f"follower-dashboard:{config.REDDIT_USERNAME}:0.1",
    )
    return _reddit