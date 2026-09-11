import config
import llm


def generate_draft(source_post, insight):
    title = (source_post.get("title") or "")[:200]
    body = (source_post.get("body") or "")[:1500]
    topic = insight.get("topic", "") if isinstance(insight, dict) else ""
    idea = insight.get("insight", "") if isinstance(insight, dict) else ""
    prompt = f"""Create ONE original X post (280 chars max) inspired by this source.

Source title: {title}
Source insight: {idea}
Topic: {topic}
Domains: {', '.join(config.TARGET_TOPICS)}

Rules:
- Original angle, not reword. Add your own take, question, or experience hook.
- No hashtags spam. 1-2 max if natural.
- No false claims. If uncertain, frame as question.
- 280 chars hard limit.
- Return JSON: {{"draft": "post text", "reason": "why this draft is useful"}}
"""
    data = llm.extract_json(prompt, system="You write concise, original X posts for a tech/SaaS/AI builder audience. No fluff.", max_tokens=400, temperature=0.7)
    draft = (data.get("draft") or "").strip()
    if len(draft) > 280:
        draft = draft[:277] + "..."
    return {"draft": draft, "reason": data.get("reason", ""), "topic": topic}
