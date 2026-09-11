"""Reddit account health check - suspended/email/karma via PRAW, alert on problems."""
from notifier import send_message
from reddit_client import get_reddit


def check():
    reddit = get_reddit()
    if not reddit:
        return {"status": "no_reddit", "configured": False}

    try:
        me = reddit.user.me()
        username = me.name
    except Exception:
        send_message("[Reddit] Account health check FAILED - OAuth invalid or account disabled.")
        return {"status": "auth_failed", "configured": True}

    suspended = False
    try:
        suspended = bool(reddit.redditor(username).is_suspended)
    except Exception:
        pass

    result = {
        "status": "suspended" if suspended else "ok",
        "username": username,
        "configured": True,
        "link_karma": getattr(me, "link_karma", 0),
        "comment_karma": getattr(me, "comment_karma", 0),
        "has_verified_email": bool(getattr(me, "has_verified_email", False)),
    }
    if suspended:
        send_message(f"[Reddit] WARNING: u/{username} appears shadowbanned/suspended.")
    return result


if __name__ == '__main__':
    print(check())