import llm
import engagement

def generate_reply(source_tweet, target_username):
    prof = engagement.get_profile(target_username) or {}
    taste = prof.get("taste","") if prof else ""
    style = prof.get("style","") if prof else ""
    text = (source_tweet.get("content") or "")[:800]
    prompt = f"""Create ONE reply to this X post from @{target_username}.

Post: "{text}"
Their taste: {taste}
Their style: {style}

Rules:
- Match their taste/style, be useful, concise (200 chars max)
- No spam, no generic praise
- Add insight, question, or experience
- Return JSON: {{"reply": "reply text", "reason": "why this reply fits their style"}}"""
    data = llm.extract_json(prompt, system="You write concise, valuable X replies that match the target's voice.", max_tokens=300, temperature=0.6)
    reply = (data.get("reply") or "").strip()
    if len(reply) > 280:
        reply = reply[:277] + "..."
    return {"reply": reply, "reason": data.get("reason","")}
