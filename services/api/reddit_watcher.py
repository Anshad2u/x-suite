"""Reddit mention watcher - check inbox mentions, store, alert via Telegram."""
import sys
import time
from datetime import datetime, timezone

import config
from data_models import (
    add_reddit_mention, get_unseen_reddit_mentions, mark_reddit_mentions_alerted,
)
from notifier import send_message
from reddit_client import get_reddit


def watch_once():
    reddit = get_reddit()
    if not reddit:
        return {"status": "no_reddit"}

    new = 0
    for item in reddit.inbox.mentions(limit=config.REDDIT_MENTION_LIMIT):
        author = getattr(item.author, "name", "") or ""
        fullname = item.fullname or ""
        body = (item.body or "").strip()
        if not fullname or not body:
            continue
        posted_at = datetime.fromtimestamp(
            float(item.created_utc), tz=timezone.utc).isoformat()
        add_reddit_mention({
            'id': fullname,
            'author': author,
            'content': body,
            'permalink': f"https://www.reddit.com{item.permalink}",
            'posted_at': posted_at,
        })
        new += 1

    unseen = get_unseen_reddit_mentions()
    sent_ids = []
    for m in unseen:
        text = f"[Reddit] u/{m['author']}: {m['content'][:200]}\n{m['permalink']}"
        if send_message(text):
            sent_ids.append(m['id'])
    if sent_ids:
        mark_reddit_mentions_alerted(sent_ids)

    return {"status": "ok", "new": new, "unseen": len(unseen), "alerted": len(sent_ids)}


def daemon(interval_sec):
    while True:
        try:
            result = watch_once()
            print(f"[{time.strftime('%H:%M:%S')}] {result}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] reddit watch error: {e}")
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