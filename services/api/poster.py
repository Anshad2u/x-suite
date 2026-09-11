"""Post tweets using X session cookies (auth_token + ct0) via internal GraphQL API."""
import random
import time

try:
    from curl_cffi import requests as cffi_requests
    HAS_CFFI = True
except ImportError:
    import requests as cffi_requests
    HAS_CFFI = False
import requests as _requests

import config

QUERY_ID = "7TKRKCPuAGsmYde0CudbVg"
BEARER = ("AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D"
          "1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA")
ENDPOINT = f"https://x.com/i/api/graphql/{QUERY_ID}/CreateTweet"

FEATURES = {
    'communities_web_enable_tweet_community_results_fetch': True,
    'c9s_tweet_anatomy_moderator_badge_enabled': True,
    'articles_preview_enabled': True,
    'tweetypie_unmention_optimization_enabled': True,
    'responsive_web_edit_tweet_api_enabled': True,
    'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
    'view_counts_everywhere_api_enabled': True,
    'longform_notetweets_consumption_enabled': True,
    'responsive_web_twitter_article_tweet_consumption_enabled': True,
    'tweet_awards_web_tipping_enabled': False,
    'creator_subscriptions_quote_tweet_preview_enabled': False,
    'longform_notetweets_rich_text_read_enabled': True,
    'longform_notetweets_inline_media_enabled': True,
    'rweb_video_timestamps_enabled': True,
    'rweb_tipjar_consumption_enabled': True,
    'responsive_web_graphql_exclude_directive_enabled': True,
    'verified_phone_label_enabled': False,
    'freedom_of_speech_not_reach_fetch_enabled': True,
    'standardized_nudges_misinfo': True,
    'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
    'interactive_text_enabled': True,
    'responsive_web_text_conversations_enabled': False,
}


class PostError(Exception):
    pass


class XPoster:
    def __init__(self):
        self.auth_token = config.X_AUTH_TOKEN
        self.ct0 = config.CT0
        if not self.auth_token or not self.ct0:
            raise PostError("X_AUTH_TOKEN and CT0 required for posting")

    def _headers(self):
        return {
            "authorization": f"Bearer {BEARER}",
            "content-type": "application/json",
            "cookie": f"auth_token={self.auth_token}; ct0={self.ct0}",
            "x-csrf-token": self.ct0,
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-active-user": "yes",
            "user-agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/131.0.0.0 Safari/537.36"),
            "referer": "https://x.com/compose/post",
            "origin": "https://x.com",
        }

    def post(self, text, reply_to=None):
        text = text.strip()
        if len(text) > 280 or len(text) < 1:
            raise PostError(f"tweet length invalid: {len(text)} chars")

        variables = {
            "tweet_text": text,
            "dark_request": False,
            "media": {"media_entities": [], "possibly_sensitive": False},
        }
        if reply_to:
            variables["reply"] = {
                "in_reply_to_tweet_id": str(reply_to),
                "exclude_reply_user_ids": [],
            }

        payload = {"variables": variables, "features": FEATURES, "queryId": QUERY_ID}
        time.sleep(random.uniform(config.POST_JITTER_MIN, config.POST_JITTER_MAX))
        try:
            if HAS_CFFI:
                _s = cffi_requests.Session(impersonate="chrome")
                _s.get("https://x.com/home", headers={"cookie": f"auth_token={self.auth_token}; ct0={self.ct0}"}, timeout=10)
                _s.close()
        except Exception:
            pass
        retryable = {429, 500, 502, 503, 504}
        resp = None
        for attempt in range(config.POST_MAX_RETRIES + 1):
            if HAS_CFFI:
                sess = cffi_requests.Session(impersonate="chrome")
                resp = sess.post(ENDPOINT, headers=self._headers(), json=payload, timeout=30)
                sess.close()
            else:
                resp = _requests.post(ENDPOINT, headers=self._headers(), json=payload, timeout=30)
            if resp.status_code not in retryable or attempt == config.POST_MAX_RETRIES:
                break
            time.sleep(min(2 ** attempt, 15))

        if resp.status_code != 200:
            raise PostError(f"HTTP {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        errors = data.get("errors")
        result = (data.get("data", {}).get("create_tweet", {})
                      .get("tweet_results", {}).get("result", {}))
        tweet_id = result.get("rest_id")
        if not tweet_id:
            err_msg = "; ".join(e.get("message", "") for e in errors or []) or str(data)[:300]
            raise PostError(f"no tweet created: {err_msg}")
        return tweet_id

    def post_thread(self, texts):
        ids = []
        parent = None
        for t in texts:
            tid = self.post(t, reply_to=parent)
            ids.append(tid)
            parent = tid
        return ids
