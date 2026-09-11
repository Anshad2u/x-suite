"""Reddit poster - submit a post to a subreddit via PRAW with retry + Telegram recap."""
import sys
import time

import config
from data_models import add_reddit_post_log
from notifier import send_message
from reddit_client import get_reddit


def submit_post(title, body, subreddit=None):
    reddit = get_reddit()
    if not reddit:
        return {"status": "no_reddit"}
    sub = subreddit or config.REDDIT_POST_SUBREDDIT
    if not sub:
        return {"status": "no_subreddit"}

    last_error = None
    for attempt in range(config.POST_MAX_RETRIES + 1):
        try:
            submission = reddit.subreddit(sub).submit(title=title, selftext=body)
            break
        except Exception as e:
            last_error = str(e)
            if attempt < config.POST_MAX_RETRIES:
                time.sleep(min(2 ** attempt, 15))

    if last_error:
        send_message(f"[Reddit] Post FAILED to r/{sub}: {last_error}")
        return {"status": "post_failed", "error": last_error}

    permalink = f"https://www.reddit.com{submission.permalink}"
    add_reddit_post_log({
        'title': title,
        'content': body,
        'subreddit': sub,
        'permalink': permalink,
    })
    send_message(f"[Reddit] Posted to r/{sub}: {title}\n{permalink}")
    return {"status": "ok", "permalink": permalink, "subreddit": sub}


def main():
    if len(sys.argv) < 3:
        print("Usage: python reddit_poster.py \"Title\" \"Body\" [subreddit]")
        return
    title = sys.argv[1]
    body = sys.argv[2]
    sub = sys.argv[3] if len(sys.argv) > 3 else None
    result = submit_post(title, body, sub)
    print(result)


if __name__ == '__main__':
    main()