"""Telegram alert sender - returns None when disabled, False on failure."""
import requests

import config


def send_message(text):
    token = config.TELEGRAM_BOT_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return None
    payload = {"chat_id": chat_id, "text": text}
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json=payload, timeout=15)
        return resp.ok
    except requests.RequestException:
        return False