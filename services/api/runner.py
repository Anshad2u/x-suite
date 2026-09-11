import logging
import time

import config
import feed_observer
import memory
import understand

logger = logging.getLogger(__name__)


def run_cycle(max_new=20, include_x=False):
    memory.init_memory()
    obs = feed_observer.observe_reddit_once()
    if include_x:
        obs_x = feed_observer.observe_x_once()
        obs = obs + obs_x
    logger.info("observed: %s", obs)
    unseen = feed_observer.get_unanalyzed(limit=max_new)
    analyzed = 0
    for post in unseen:
        try:
            res = understand.analyze_post(post)
            analyzed += 1
            logger.info("analyzed %s -> %s (rel=%.2f)", post["id"], res["decision"], res.get("relevance", 0))
        except Exception as exc:
            logger.warning("analyze failed %s: %s", post["id"], str(exc)[:120])
        time.sleep(1)
    memory.refresh_account_scores()
    watch = memory.build_watchlist()
    try:
        import telegram_approval
        prop = telegram_approval.pick_and_propose()
        if prop:
            logger.info("proposed draft %s", prop.get("id"))
        summ = telegram_approval.send_understand_summary(limit=3)
        if summ:
            logger.info("summary sent %s", summ)
    except Exception as exc:
        logger.warning("propose failed: %s", str(exc)[:120])
    return {
        "observed": obs,
        "analyzed": analyzed,
        "posts": memory.summary(),
        "watchlist_size": len(watch),
    }


def daemon(interval_sec=3600, max_new=20):
    while True:
        try:
            out = run_cycle(max_new=max_new)
            print(f"[{time.strftime('%H:%M:%S')}] cycle: {out}")
        except Exception as exc:
            print(f"[{time.strftime('%H:%M:%S')}] cycle error: {exc}")
        time.sleep(interval_sec)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(run_cycle())
