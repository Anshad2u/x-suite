import json
import time
import requests

import config
import db
import memory
from draft import generate_draft
from poster import XPoster

TOKEN = config.TELEGRAM_BOT_TOKEN
CHAT_ID = config.TELEGRAM_CHAT_ID
BASE = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else ""


def _ensure_table():
    db.execute("""CREATE TABLE IF NOT EXISTS pending_drafts (
        id SERIAL PRIMARY KEY,
        post_id TEXT,
        draft TEXT,
        reason TEXT,
        topic TEXT,
        source_link TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMPTZ DEFAULT NOW()
    )""")


def send_draft_for_approval(source_post, insight):
    _ensure_table()
    gen = generate_draft(source_post, insight)
    draft = gen["draft"]
    if not draft:
        return None
    db.execute("INSERT INTO pending_drafts (post_id, draft, reason, topic, source_link) VALUES (%s,%s,%s,%s,%s)",
               (source_post["id"], draft, gen["reason"], gen["topic"], source_post.get("link","")))
    row = db.query_one("SELECT id FROM pending_drafts WHERE post_id=%s ORDER BY id DESC LIMIT 1", (source_post["id"],))
    did = row["id"]
    exact = draft
    text = f"APPROVAL NEEDED — EXACT POST ({len(exact)} chars, will post verbatim to X):\n\n\"{exact}\"\n\nWhy this draft: {gen['reason']}\nTopic: {gen['topic']}\nSource: {source_post.get('link','')}\n\nTap Approve to post THIS EXACT TEXT. Tap Reject to discard."
    kb = {"inline_keyboard": [[{"text": "✅ Approve — post this", "callback_data": f"approve_{did}"}, {"text": "❌ Reject", "callback_data": f"reject_{did}"}]]}
    if not TOKEN or not CHAT_ID:
        return {"id": did, "draft": draft, "no_telegram": True}
    requests.post(f"{BASE}/sendMessage", json={"chat_id": CHAT_ID, "text": text, "reply_markup": kb}, timeout=15)
    return {"id": did, "draft": draft}


def handle_callback(callback_data):
    _ensure_table()
    if callback_data.startswith("approve_reply_"):
        did = int(callback_data.split("_")[2])
        row = db.query_one("SELECT * FROM pending_replies WHERE id=%s", (did,))
        if not row or row["status"] != "pending":
            return "already handled"
        try:
            poster = XPoster()
            res = poster.post(row["reply"], reply_to=row["tweet_id"])
            db.execute("UPDATE pending_replies SET status='approved' WHERE id=%s", (did,))
            requests.post(f"{BASE}/sendMessage", json={"chat_id": CHAT_ID, "text": f"✅ Replied on X: https://x.com/i/web/status/{res}"}, timeout=15)
            return "replied"
        except Exception as exc:
            msg = str(exc)[:200]
            db.execute("UPDATE pending_replies SET status='failed' WHERE id=%s", (did,))
            requests.post(f"{BASE}/sendMessage", json={"chat_id": CHAT_ID, "text": f"❌ Reply failed: {msg}"}, timeout=15)
            return f"failed: {msg}"
    if callback_data.startswith("reject_reply_"):
        did = int(callback_data.split("_")[2])
        db.execute("UPDATE pending_replies SET status='rejected' WHERE id=%s", (did,))
        requests.post(f"{BASE}/sendMessage", json={"chat_id": CHAT_ID, "text": "Reply rejected."}, timeout=15)
        return "rejected"
    if callback_data.startswith("approve_"):
        did = int(callback_data.split("_")[1])
        row = db.query_one("SELECT * FROM pending_drafts WHERE id=%s", (did,))
        if not row or row["status"] != "pending":
            return "already handled"
        try:
            try:
                from poster_browser import post_via_browser
                res = post_via_browser(row["draft"])
            except Exception:
                from poster import XPoster
                res = XPoster().post(row["draft"])
            db.execute("UPDATE pending_drafts SET status='approved' WHERE id=%s", (did,))
            requests.post(f"{BASE}/sendMessage", json={"chat_id": CHAT_ID, "text": f"✅ Posted to X: https://x.com/i/web/status/{res}\nExact text:\n\"{row['draft']}\""}, timeout=15)
            return "posted"
        except Exception as exc:
            msg = str(exc)
            if "344" in msg:
                msg = "X daily limit (344). Try tomorrow."
            elif "226" in msg:
                msg = "X flagged as automated (226). Wait, vary wording."
            db.execute("UPDATE pending_drafts SET status='failed' WHERE id=%s", (did,))
            requests.post(f"{BASE}/sendMessage", json={"chat_id": CHAT_ID, "text": f"❌ Post failed: {msg}\nDraft was:\n\"{row['draft']}\""}, timeout=15)
            return f"failed: {msg}"
    if callback_data.startswith("reject_"):
        did = int(callback_data.split("_")[1])
        db.execute("UPDATE pending_drafts SET status='rejected' WHERE id=%s", (did,))
        requests.post(f"{BASE}/sendMessage", json={"chat_id": CHAT_ID, "text": "Rejected."}, timeout=15)
        return "rejected"
    if callback_data.startswith("reject_reply_"):
        did = int(callback_data.split("_")[2])
        db.execute("UPDATE pending_replies SET status='rejected' WHERE id=%s", (did,))
        requests.post(f"{BASE}/sendMessage", json={"chat_id": CHAT_ID, "text": "Reply rejected."}, timeout=15)
        return "rejected"
    if callback_data == "approve_summary":
        requests.post(f"{BASE}/sendMessage", json={"chat_id": CHAT_ID, "text": "Summary approved — learning."}, timeout=15)
        return "summary approved"
    if callback_data == "correct_summary":
        requests.post(f"{BASE}/sendMessage", json={"chat_id": CHAT_ID, "text": "Send correction: reply with correct topic/relevance for last summary."}, timeout=15)
        return "awaiting correction"
    if callback_data == "reject_summary":
        requests.post(f"{BASE}/sendMessage", json={"chat_id": CHAT_ID, "text": "Summary rejected — will adjust."}, timeout=15)
        return "summary rejected"
    return "unknown"


def poll_loop(interval=2):
    offset = 0
    import logging
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("tg_poll")
    while True:
        try:
            r = requests.get(f"{BASE}/getUpdates", params={"offset": offset, "timeout": 20}, timeout=35)
            data = r.json()
            if not data.get("ok"):
                log.warning("getUpdates not ok: %s", data)
                time.sleep(5)
                continue
            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                cb = upd.get("callback_query")
                if cb:
                    log.info("callback %s from %s", cb.get("data"), cb.get("from",{}).get("username"))
                    ans = handle_callback(cb["data"])
                    requests.post(f"{BASE}/answerCallbackQuery", json={"callback_query_id": cb["id"], "text": ans[:200]}, timeout=10)
                elif upd.get("message"):
                    log.info("message update %s", upd["message"].get("text","")[:40])
        except Exception as exc:
            log.warning("poll error: %s", str(exc)[:120])
            time.sleep(5)
        time.sleep(interval)


def send_reply_for_approval(source_tweet, reply_data):
    _ensure_table()
    db.execute("""CREATE TABLE IF NOT EXISTS pending_replies (
        id SERIAL PRIMARY KEY, tweet_id TEXT, reply TEXT, reason TEXT, status TEXT DEFAULT 'pending', created_at TIMESTAMPTZ DEFAULT NOW()
    )""")
    reply = reply_data.get("reply","")
    if not reply:
        return None
    db.execute("INSERT INTO pending_replies (tweet_id, reply, reason) VALUES (%s,%s,%s)", (source_tweet.get("tweet_id"), reply, reply_data.get("reason","")))
    row = db.query_one("SELECT id FROM pending_replies ORDER BY id DESC LIMIT 1")
    did = row["id"]
    text = f"REPLY APPROVAL — EXACT REPLY ({len(reply)} chars, will reply to @{source_tweet.get('username')}):\n\n\"{reply}\"\n\nWhy: {reply_data.get('reason','')}\nTo: https://x.com/{source_tweet.get('username')}/status/{source_tweet.get('tweet_id')}\n\nTap Approve to post reply."
    kb = {"inline_keyboard": [[{"text": "✅ Approve reply", "callback_data": f"approve_reply_{did}"}, {"text": "❌ Reject", "callback_data": f"reject_reply_{did}"}]]}
    if TOKEN and CHAT_ID:
        requests.post(f"{BASE}/sendMessage", json={"chat_id": CHAT_ID, "text": text, "reply_markup": kb}, timeout=15)
    return {"id": did, "reply": reply}


def send_understand_summary(limit=3):
    _ensure_table()
    rows = db.query_all("""SELECT p.title, p.link, i.topic, i.insight, i.relevance, i.decision, p.id
        FROM observed_posts p JOIN post_insights i ON i.id=p.id
        ORDER BY i.analyzed_at DESC LIMIT %s""", (limit,))
    if not rows:
        return None
    lines = []
    for r in rows:
        lines.append(f"• {r['topic']} | rel {r['relevance']:.2f} | {r['decision']}\n  {r['title'][:80]}\n  Insight: {r['insight'][:100]}\n  {r['link']}")
    text = "UNDERSTAND SUMMARY — last 3 insights:\n\n" + "\n\n".join(lines) + "\n\nTap Approve if correct, Correct to fix."
    kb = {"inline_keyboard": [[{"text": "✅ Approve all", "callback_data": "approve_summary"}, {"text": "✏️ Correct", "callback_data": "correct_summary"}, {"text": "❌ Reject", "callback_data": "reject_summary"}]]}
    if TOKEN and CHAT_ID:
        requests.post(f"{BASE}/sendMessage", json={"chat_id": CHAT_ID, "text": text, "reply_markup": kb}, timeout=15)
    return {"sent": len(rows)}


def pick_and_propose(limit=20):
    _ensure_table()
    cands = db.query_all("""SELECT p.*, i.topic, i.insight, i.relevance FROM observed_posts p
        JOIN post_insights i ON i.id=p.id
        WHERE i.decision IN ('save_watch','draft_post','draft_reply') AND i.relevance>=0.5
        AND NOT EXISTS (SELECT 1 FROM pending_drafts d WHERE d.post_id=p.id)
        ORDER BY i.relevance DESC LIMIT %s""", (limit,))
    if not cands:
        cands = db.query_all("""SELECT p.*, i.topic, i.insight, i.relevance FROM observed_posts p
            JOIN post_insights i ON i.id=p.id
            WHERE i.relevance>=0.6 AND NOT EXISTS (SELECT 1 FROM pending_drafts d WHERE d.post_id=p.id)
            ORDER BY i.relevance DESC LIMIT %s""", (limit,))
    if not cands:
        return None
    top = cands[0]
    insight = {"topic": top["topic"], "insight": top["insight"]}
    return send_draft_for_approval(top, insight)
