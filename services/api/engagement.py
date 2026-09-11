import db
import llm

def init_engagement():
    db.execute("""CREATE TABLE IF NOT EXISTS engagement_profiles (
        username TEXT PRIMARY KEY,
        taste TEXT,
        style TEXT,
        topics TEXT,
        avg_reply_length INTEGER,
        updated_at TIMESTAMPTZ DEFAULT NOW()
    )""")

def learn_account_style(username, tweets):
    texts = [t.get("content","")[:300] for t in tweets[:5] if t.get("content")]
    if not texts:
        return None
    prompt = f"""Analyze this X account @{username} based on 5 recent tweets. Define their engagement taste.

Tweets:
{chr(10).join(f'- {t}' for t in texts)}

Return JSON: {{"taste": "one line taste, e.g. 'technical deep dives, concise, hates hype'", "style": "reply style, e.g. 'short, witty, code snippets'", "topics": "comma list of 3 topics they care about"}}"""
    try:
        data = llm.extract_json(prompt, system="You analyze X creators' voice for engagement.", max_tokens=400, temperature=0.3)
        db.execute("""INSERT INTO engagement_profiles (username, taste, style, topics)
            VALUES (%s,%s,%s,%s) ON CONFLICT (username) DO UPDATE SET taste=EXCLUDED.taste, style=EXCLUDED.style, topics=EXCLUDED.topics, updated_at=NOW()""",
            (username, data.get("taste",""), data.get("style",""), data.get("topics","")))
        return data
    except Exception:
        return None

def get_profile(username):
    return db.query_one("SELECT * FROM engagement_profiles WHERE username=%s", (username,))

def all_profiles(limit=100):
    return db.query_all("SELECT * FROM engagement_profiles ORDER BY updated_at DESC LIMIT %s", (limit,))
