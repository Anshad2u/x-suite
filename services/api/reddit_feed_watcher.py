"""Reddit RSS feed watcher - no API key needed, alerts new posts in configured subreddits."""
import sys
import time
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen

import config
from data_models import (
    add_reddit_feed_item, get_unseen_reddit_feed_items, mark_reddit_feed_alerted,
)
from notifier import send_message

ATOM = "{http://www.w3.org/2005/Atom}"
HEADERS = {"User-Agent": "follower-dashboard/0.1 by /u/" + config.REDDIT_USERNAME}


def _subreddits():
    return [s.strip() for s in config.REDDIT_FEED_SUBREDDITS.split(",") if s.strip()]


def _feed_url(name):
    path = f"/r/{name}" if "/" not in name else f"/{name}"
    return f"https://www.reddit.com{path}/.rss?limit={config.REDDIT_FEED_LIMIT}"


def fetch_entries(feed_name):
    req = Request(_feed_url(feed_name), headers=HEADERS)
    with urlopen(req, timeout=20) as resp:
        root = ET.fromstring(resp.read())
    entries = []
    for entry in root.findall(f"{ATOM}entry"):
        link_el = entry.find(f"{ATOM}link")
        author_el = entry.find(f"{ATOM}author/{ATOM}name")
        entries.append({
            "entry_id": (entry.findtext(f"{ATOM}id") or "").strip(),
            "title": (entry.findtext(f"{ATOM}title") or "").strip(),
            "link": (link_el.get("href") if link_el is not None else ""),
            "author": (author_el.text or "").strip() if author_el is not None else "",
            "updated": (entry.findtext(f"{ATOM}updated") or "").strip(),
        })
    return entries


def watch_once(dry_run=False):
    subs = _subreddits()
    if not subs:
        return {"status": "no_subreddits"}

    new = 0
    for sub in subs:
        try:
            entries = fetch_entries(sub)
        except Exception as e:
            print(f"fetch {sub} failed: {e}")
            continue
        for e in entries:
            if not e["entry_id"]:
                continue
            add_reddit_feed_item({
                "entry_id": e["entry_id"],
                "subreddit": sub,
                "author": e["author"],
                "title": e["title"][:300],
                "link": e["link"],
                "updated_at": e["updated"],
            })
            new += 1
        time.sleep(2)

    keywords = [k.strip().lower() for k in config.REDDIT_FEED_KEYWORDS.split(",") if k.strip()]
    digest = config.REDDIT_FEED_DIGEST.strip().lower() in ("1", "true", "yes", "on")
    unseen = get_unseen_reddit_feed_items()

    def _passes(m):
        if not keywords:
            return True
        title = (m['title'] or '').lower()
        return any(k in title for k in keywords)

    sent_ids = []
    if not dry_run and (keywords or digest):
        if digest:
            picks = [m for m in unseen if _passes(m)][:5]
            if picks:
                lines = [f"[r/{m['subreddit'].split('/')[-1]}] {m['title']}\n{m['link']}" for m in picks]
                extra = len([m for m in unseen if _passes(m)]) - len(picks)
                text = "\n\n".join(lines) + (f"\n\n+{extra} more" if extra > 0 else "")
                if send_message(text):
                    sent_ids = [m['id'] for m in picks]
        else:
            for m in unseen:
                if not _passes(m):
                    continue
                text = f"[r/{m['subreddit'].split('/')[-1]}] {m['title']}\n{m['link']}"
                if send_message(text):
                    sent_ids.append(m['id'])
    if sent_ids:
        mark_reddit_feed_alerted(sent_ids)

    return {"status": "ok", "scanned": new, "unseen": len(unseen), "alerted": len(sent_ids)}


def daemon(interval_sec):
    while True:
        try:
            result = watch_once()
            print(f"[{time.strftime('%H:%M:%S')}] {result}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] rss watch error: {e}")
        time.sleep(interval_sec)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "once"
    dry_run = "dry-run" in sys.argv[2:]
    if mode == "daemon":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 300
        daemon(interval)
    else:
        result = watch_once(dry_run=dry_run)
        print(result)
        if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
            print("NOTE: TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID not set - alerts disabled")


if __name__ == '__main__':
    main()