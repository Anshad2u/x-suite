import json
import time
from datetime import datetime, timezone

import config
import memory
import requests

REDDIT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "Accept": "application/json",
}


def _reddit_cookies():
    return {
        "reddit_session": config.REDDIT_SESSION_COOKIE,
        "csrf_token": config.REDDIT_CSRF_TOKEN,
        "token_v2": config.REDDIT_TOKEN_V2,
    }


def fetch_multireddit(multireddit, limit=25):
    url = f"https://www.reddit.com/user/trickshame/m/{multireddit}/.json?limit={limit}"
    headers = dict(REDDIT_HEADERS)
    headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in _reddit_cookies().items())
    resp = requests.get(url, headers=headers, timeout=25)
    resp.raise_for_status()
    kids = resp.json().get("data", {}).get("children", [])
    posts = []
    for e in kids:
        d = e.get("data", {})
        author = d.get("author") or ""
        if author.startswith("["):
            continue
        body = d.get("selftext") or d.get("title") or ""
        posts.append({
            "id": f"reddit_{d.get('id')}",
            "platform": "reddit",
            "feed": f"m/{multireddit}",
            "author": author,
            "title": d.get("title") or "",
            "body": body[:4000],
            "link": "https://www.reddit.com" + (d.get("permalink") or ""),
            "posted_at": datetime.fromtimestamp(
                float(d.get("created_utc") or 0), tz=timezone.utc).isoformat(),
        })
    return posts


def fetch_subreddit(subreddit, limit=25):
    url = f"https://www.reddit.com/r/{subreddit}/.json?limit={limit}"
    headers = dict(REDDIT_HEADERS)
    headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in _reddit_cookies().items())
    resp = requests.get(url, headers=headers, timeout=25)
    resp.raise_for_status()
    kids = resp.json().get("data", {}).get("children", [])
    posts = []
    for e in kids:
        d = e.get("data", {})
        author = d.get("author") or ""
        if author.startswith("["):
            continue
        body = d.get("selftext") or d.get("title") or ""
        posts.append({
            "id": f"reddit_{d.get('id')}",
            "platform": "reddit",
            "feed": f"r/{subreddit}",
            "author": author,
            "title": d.get("title") or "",
            "body": body[:4000],
            "link": "https://www.reddit.com" + (d.get("permalink") or ""),
            "posted_at": datetime.fromtimestamp(
                float(d.get("created_utc") or 0), tz=timezone.utc).isoformat(),
        })
    return posts


def fetch_x_account(username, limit=20):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []
    posts = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context()
            cookies = []
            if config.X_AUTH_TOKEN:
                cookies.append({"name": "auth_token", "value": config.X_AUTH_TOKEN, "domain": ".x.com", "path": "/"})
                cookies.append({"name": "auth_token", "value": config.X_AUTH_TOKEN, "domain": ".twitter.com", "path": "/"})
            if config.CT0:
                cookies.append({"name": "ct0", "value": config.CT0, "domain": ".x.com", "path": "/"})
                cookies.append({"name": "ct0", "value": config.CT0, "domain": ".twitter.com", "path": "/"})
            if cookies:
                ctx.add_cookies(cookies)
            page = ctx.new_page()
            collected = []
            def on_response(resp):
                try:
                    url = resp.url
                    if "UserTweets" in url or "TweetDetail" in url:
                        data = resp.json()
                        entries = data.get("data", {}).get("user", {}).get("result", {}).get("timeline", {}).get("timeline", {}).get("instructions", [])
                        for instr in entries:
                            for entry in instr.get("entries", []):
                                c = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
                                leg = c.get("legacy", {})
                                if leg.get("full_text"):
                                    collected.append({
                                        "id": f"x_{leg.get('id_str') or c.get('rest_id')}",
                                        "platform": "x",
                                        "feed": f"@{username}",
                                        "author": username,
                                        "title": leg.get("full_text", "")[:120],
                                        "body": leg.get("full_text", "")[:4000],
                                        "link": f"https://x.com/{username}/status/{leg.get('id_str') or c.get('rest_id')}",
                                        "posted_at": leg.get("created_at", ""),
                                    })
                except Exception:
                    pass
            page.on("response", on_response)
            page.goto(f"https://x.com/{username}", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(8000)
            for _ in range(3):
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(3000)
                if len(collected) >= limit:
                    break
            browser.close()
            posts = collected[:limit]
    except Exception:
        pass
    return posts


def observe_reddit_once():
    results = []
    for m in ["ai_tools", "saudi"]:
        try:
            posts = fetch_multireddit(m, limit=config.REDDIT_FEED_LIMIT)
            for p in posts:
                memory.upsert_post(p)
            results.append({"feed": f"m/{m}", "posts": len(posts)})
        except Exception as exc:
            results.append({"feed": f"m/{m}", "error": str(exc)[:120]})
        time.sleep(2)
    for sub in getattr(config, "REDDIT_OBSERVE_SUBREDDITS", []):
        try:
            posts = fetch_subreddit(sub, limit=config.REDDIT_FEED_LIMIT)
            for p in posts:
                memory.upsert_post(p)
            results.append({"feed": f"r/{sub}", "posts": len(posts)})
        except Exception as exc:
            results.append({"feed": f"r/{sub}", "error": str(exc)[:120]})
        time.sleep(2)
    return results


def observe_x_once(limit_per_account=10):
    results = []
    for acct in getattr(config, "X_OBSERVE_ACCOUNTS", [])[:5]:
        try:
            posts = fetch_x_account(acct, limit=limit_per_account)
            for p in posts:
                memory.upsert_post(p)
            results.append({"feed": f"@{acct}", "posts": len(posts)})
        except Exception as exc:
            results.append({"feed": f"@{acct}", "error": str(exc)[:120]})
        time.sleep(2)
    return results


def get_unanalyzed(limit=20):
    return memory.unanalyzed_posts(limit)