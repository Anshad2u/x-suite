import json
import logging
import threading

import config
from openai import OpenAI

logger = logging.getLogger(__name__)

_client_by_key = {}
_lock = threading.Lock()
_round_robin = 0


def _client(key):
    global _client_by_key
    if key not in _client_by_key:
        _client_by_key[key] = OpenAI(base_url=config.GROQ_BASE_URL, api_key=key)
    return _client_by_key[key]


def _next_client():
    global _round_robin
    keys = config.GROQ_API_KEYS
    if not keys:
        raise RuntimeError("No GROQ_API_KEYS configured")
    with _lock:
        _round_robin += 1
        key = keys[_round_robin % len(keys)]
    return _client(key)


def complete(prompt, *, system=None, max_tokens=1024, temperature=0.2, json_mode=True):
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    kwargs = {
        "model": config.GROQ_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    last_err = None
    for _ in range(len(config.GROQ_API_KEYS)):
        client = _next_client()
        try:
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content
        except Exception as exc:
            last_err = exc
            logger.warning("groq call failed (key rotated): %s", str(exc)[:120])
    raise last_err


def extract_json(prompt, *, system=None, max_tokens=1024, temperature=0.2):
    raw = complete(prompt, system=system, max_tokens=max_tokens, temperature=temperature, json_mode=True)
    if not raw:
        raise ValueError("empty LLM response")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            return json.loads(raw[start:end + 1])
        raise ValueError(f"LLM returned non-JSON: {raw[:200]}")