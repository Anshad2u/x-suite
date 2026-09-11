import config
import llm
import memory

SYSTEM_PROMPT = (
    "You are a personal-content curator for a tech/SaaS/AI-focused social-media agent. "
    "You read posts from the user's curated feeds (Reddit multireddits and X/Twitter AI/SaaS accounts) "
    "and decide what is worth learning or following. You are NOT a spam bot. "
    "Return strict JSON matching the requested schema."
)

TARGETS = ", ".join(config.TARGET_TOPICS)


def analyze_post(post):
    text = (post.get("title") or "") + "\n\n" + (post.get("body") or "")
    text = text.strip()[:3000]
    prompt = f"""Analyze this social post from the user's feed.

RELEVANT DOMAINS the user curates toward: {TARGETS}

POST:
Author: {post.get('author')}
Title: {post.get('title')}
Body: {post.get('body')}

Return JSON with these exact keys:
- "topic": short topic label (e.g. "AI agents", "SaaS pricing", "Dev tooling")
- "insight": one sentence on the genuinely useful idea/learning here, or "" if none
- "is_new": true if this is an original/new idea vs a repost of common knowledge
- "relevance": float 0.0-1.0 = how well it fits the relevant domains above
- "confidence": float 0.0-1.0 = how sure you are of this judgment
- "follow_worthy": true if the AUTHOR is worth following based on this post
- "decision": one of "ignore", "learn", "save_watch", "draft_reply", "draft_post"

Rules: default to "ignore" unless there is a real reason. Only "draft_reply"/"draft_post" if the post invites genuine, useful contribution. Never rate generic/low-effort content highly."""
    data = llm.extract_json(prompt, system=SYSTEM_PROMPT, max_tokens=600, temperature=0.2)
    data["decision"] = (data.get("decision") or "learn").lower()
    if data["decision"] not in ("ignore", "learn", "save_watch", "draft_reply", "draft_post"):
        data["decision"] = "learn"
    memory.upsert_insight(post["id"], data)
    memory.upsert_account(
        post.get("author"), post.get("platform"), "", topics=[data.get("topic")]
    )
    memory.bump_account_post(post.get("author"), relevant=(data.get("relevance", 0) >= 0.5))
    if data.get("topic"):
        memory.upsert_topic(data["topic"], relevant=(data.get("relevance", 0) >= 0.5))
    memory.log_decision(post["id"], data["decision"], data.get("insight", ""))
    return data