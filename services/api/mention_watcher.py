"""Mention watcher - search tweets mentioning your account, store, alert via Telegram."""
import sys
import time

import config
from data_models import (
    add_mention, get_unseen_mentions, mark_mentions_alerted,
)
from notifier import send_message
from scraper import _get_scweet


def watch_once():
    s = _get_scweet()
    if not s:
        return {"status": "no_auth"}

    query = f"to:{config.TWITTER_USERNAME} OR @{config.TWITTER_USERNAME}"
    tweets = s.search(query, since="", limit=config.MENTION_WATCH_LIMIT)

    new = 0
    for t in tweets or []:
        user_info = t.get('user') or {}
        author = user_info.get('screen_name', '')
        tweet_id = str(t.get('tweet_id', ''))
        content = t.get('text', '') or t.get('embedded_text', '') or ''
        if not tweet_id or not content:
            continue
        add_mention({
            'tweet_id': tweet_id,
            'username': config.TWITTER_USERNAME,
            'author': author,
            'content': content,
            'tweet_url': f"https://x.com/{author}/status/{tweet_id}",
            'posted_at': t.get('timestamp'),
        })
        new += 1

    unseen = get_unseen_mentions()
    sent_ids = []
    for m in unseen:
        if send_message(f"@{m['author']}: {m['content'][:200]}\n{m['tweet_url']}"):
            sent_ids.append(m['id'])
    if sent_ids:
        mark_mentions_alerted(sent_ids)

    return {"status": "ok", "new": new, "unseen": len(unseen), "alerted": len(sent_ids)}


def daemon(interval_sec):
    while True:
        try:
            result = watch_once()
            print(f"[{time.strftime('%H:%M:%S')}] {result}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] watch error: {e}")
        time.sleep(interval_sec)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "once"
    if mode == "daemon":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 120
        daemon(interval)
    else:
        result = watch_once()
        print(result)
        if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
            print("NOTE: TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set - alerts disabled")


if __name__ == '__main__':
    main()