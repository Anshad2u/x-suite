"""Publish human-approved drafts to X.

This is the bridge that closes the loop the web console leaves open: the
Activity page only flips ``pending_drafts.status`` to ``'approved'``, so
something has to actually send the tweet. That something is this script.

Flow
----
1. select ``pending_drafts`` rows whose status is ``'queued'``
2. post each one (real browser first, cookie API as fallback)
3. mark it ``'posted'`` on success or ``'failed'`` on error
4. keep within the shared daily budget (``posted_log`` vs AUTO_POST_MAX_PER_DAY)

Status vocabulary (deliberately distinct to avoid a legacy collision):

    pending   -> generated, waiting for you
    queued    -> you approved it; awaiting this publisher   <-- our input
    posted    -> published by this script                    <-- our output
    failed    -> publish attempt errored
    rejected  -> you discarded it
    approved  -> LEGACY: the old Telegram callback set this *after* posting.
                 We never read or write it, so those rows are never re-posted.

Nothing is posted unless a human explicitly approved it — this never picks
candidates on its own. That is the whole point of "auto-draft, I approve".

Usage:
    python publish_approved.py
    python publish_approved.py --dry-run
"""
import json
import sys

import config
import db
import data_models as dm
from notifier import send_message


def _post(text):
    """Post via the browser path (real DOM, avoids 226), fall back to cookies."""
    try:
        from poster_browser import post_via_browser
        return post_via_browser(text)
    except Exception:
        from poster import XPoster
        return XPoster().post(text)


def _friendly(exc):
    msg = str(exc)
    if "344" in msg:
        return "X daily limit (344). Try again tomorrow."
    if "226" in msg:
        return "X flagged as automated (226). Vary the wording."
    return msg[:200]


def run(dry_run=False, limit=5):
    dm.init_dbs()

    rows = db.query_all(
        "SELECT id, draft FROM pending_drafts WHERE status='queued' ORDER BY id ASC LIMIT %s",
        (limit,),
    )
    if not rows:
        return {"status": "nothing_queued", "posted": 0}

    today = dm.queue_posts_today()
    remaining = max(0, config.AUTO_POST_MAX_PER_DAY - today)
    if remaining <= 0:
        return {"status": "daily_limit_reached", "posted_today": today}

    results = []
    for row in rows[:remaining]:
        did = row["id"]
        text = (row["draft"] or "").strip()
        if not text:
            db.execute("UPDATE pending_drafts SET status='failed' WHERE id=%s", (did,))
            results.append({"id": did, "status": "empty"})
            continue
        if dry_run:
            results.append({"id": did, "status": "dry_run", "text": text})
            continue
        try:
            tweet_id = _post(text)
            db.execute("UPDATE pending_drafts SET status='posted' WHERE id=%s", (did,))
            results.append({"id": did, "status": "posted", "tweet_id": tweet_id})
        except Exception as exc:
            friendly = _friendly(exc)
            db.execute("UPDATE pending_drafts SET status='failed' WHERE id=%s", (did,))
            send_message(f"Publish failed for draft #{did}: {friendly}")
            results.append({"id": did, "status": "failed", "error": friendly})

    return {
        "status": "done",
        "posted": sum(1 for r in results if r["status"] == "posted"),
        "results": results,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(run(dry_run="--dry-run" in sys.argv), indent=2, default=str))
    except Exception as exc:
        # Non-zero exit so Task Scheduler records the failure.
        print(f"publish error: {exc}", file=sys.stderr)
        sys.exit(1)
