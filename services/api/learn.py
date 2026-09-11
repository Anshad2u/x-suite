"""Engagement feedback loop: fetch own profile tweets, match them against
posted_log, store engagement, and credit the source that produced each post."""
import config
from scraper import _get_scweet
from data_models import get_unscored_posts, add_posted_engagement, upsert_source_score


def learn_once(limit_profile=20):
    rows = get_unscored_posts()
    if not rows:
        return {"status": "ok", "scored": 0}
    s = _get_scweet()
    if not s:
        return {"status": "no_auth", "scored": 0}
    tweets = s.get_profile_tweets([config.TWITTER_USERNAME], limit=limit_profile) or []
    by_id = {str(t.get('tweet_id')): t for t in tweets}
    scored = 0
    for r in rows:
        t = by_id.get(str(r['posted_tweet_id']))
        if not t:
            continue
        likes = t.get('likes', 0) or 0
        reps = t.get('retweets', 0) or 0
        repl = t.get('comments', 0) or 0
        add_posted_engagement({'tweet_id': str(r['posted_tweet_id']),
                               'likes': likes, 'reposts': reps, 'replies': repl})
        if r.get('source_key'):
            upsert_source_score(r['source_key'], likes + reps * 2 + repl * 20)
        scored += 1
    return {"status": "ok", "scored": scored}


if __name__ == '__main__':
    import json
    print(json.dumps(learn_once(), default=str))