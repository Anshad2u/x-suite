import db
import config
import requests

TOKEN = config.TELEGRAM_BOT_TOKEN
CHAT_ID = config.TELEGRAM_CHAT_ID
BASE = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else ""


def send_daily_digest():
    summary = db.query_one("""SELECT
        (SELECT COUNT(*) FROM observed_posts) AS posts,
        (SELECT COUNT(*) FROM post_insights) AS analyzed,
        (SELECT COUNT(*) FROM accounts) AS accounts,
        (SELECT COUNT(*) FROM topics) AS topics,
        (SELECT COUNT(*) FROM engagement_profiles) AS profiles""")
    top_topics = db.query_all("SELECT name, relevant_count, observed_count FROM topics ORDER BY relevant_count DESC LIMIT 5")
    top_accounts = db.query_all("SELECT username, relevance_score, observed_posts, relevant_posts FROM accounts ORDER BY relevance_score DESC LIMIT 5")
    watchlist = db.query_all("SELECT username, platform, relevance_score FROM accounts WHERE watchlisted=TRUE ORDER BY relevance_score DESC LIMIT 10")
    recent_actions = db.query_all("SELECT post_id, decision, reason FROM decisions_log ORDER BY created_at DESC LIMIT 5")

    lines = [f"DAILY DIGEST", f"Posts {summary['posts']} | Analyzed {summary['analyzed']} | Accounts {summary['accounts']} | Profiles {summary['profiles']}", ""]
    lines.append("Top topics:")
    for t in top_topics:
        lines.append(f"  {t['name']} ({t['relevant_count']}/{t['observed_count']})")
    lines.append("")
    lines.append("Top accounts:")
    for a in top_accounts:
        lines.append(f"  @{a['username']} score {a['relevance_score']:.2f} ({a['relevant_posts']}/{a['observed_posts']})")
    if watchlist:
        lines.append("")
        lines.append("Watchlist:")
        for w in watchlist:
            lines.append(f"  @{w['username']} {w['platform']} {w['relevance_score']:.2f}")
    if recent_actions:
        lines.append("")
        lines.append("Recent actions:")
        for a in recent_actions:
            lines.append(f"  {a['decision']}: {(a.get('reason') or '')[:60]}")
    text = "\n".join(lines)
    if TOKEN and CHAT_ID:
        requests.post(f"{BASE}/sendMessage", json={"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True}, timeout=15)
    return text


if __name__ == "__main__":
    # Scheduled entry point. Prints the digest and sends it to Telegram when
    # TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID are set.
    print(send_daily_digest())
