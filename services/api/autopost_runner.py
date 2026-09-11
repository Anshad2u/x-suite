"""Scheduled autonomous runner - Task Scheduler every 2h.
Runs engagement feedback first, then picks and posts one candidate.
Telegram contact only on errors; silent on success."""
import sys

import config
import data_models as dm
from notifier import send_message


def main():
    dm.init_dbs()
    import db
    import learn
    import autopost
    from poster import XPoster, PostError

    dry_run = '--dry-run' in sys.argv
    out = {"learn": learn.learn_once()}

    today_count = db.query_one(
        'SELECT COUNT(*) AS c FROM posted_log WHERE posted_at::date = NOW()::date')['c']
    out['posted_today'] = today_count
    if today_count >= config.AUTO_POST_MAX_PER_DAY:
        out["status"] = "daily_limit_reached"
        return out

    try:
        result = autopost.run_once(XPoster(), config.AUTO_POST_GROUP, dry_run=dry_run)
        out.update(result)
    except PostError as e:
        out["status"] = "post_failed"
        out["error"] = str(e)
        send_message(f"autopost failed: {e}")
    except Exception as e:
        out["status"] = "error"
        out["error"] = str(e)
        send_message(f"autopost error: {e}")
    return out


if __name__ == '__main__':
    import json
    try:
        print(json.dumps(main(), indent=2, default=str))
    except Exception as e:
        print(f"runner error: {e}", file=sys.stderr)