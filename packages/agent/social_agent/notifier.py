"""Telegram notifier — sends alerts via Bot API."""

from __future__ import annotations

import logging
from typing import Any

import requests

from social_agent import config

logger = logging.getLogger(__name__)

_API_TEMPLATE = "https://api.telegram.org/bot{token}/sendMessage"


class Notifier:
    """Send Telegram messages. Disabled gracefully when keys are missing."""

    def __init__(self, session: Any | None = None) -> None:
        self._session = session
        self._enabled: bool | None = None  # lazy check

    @property
    def enabled(self) -> bool:
        if self._enabled is None:
            self._enabled = bool(config.get("TELEGRAM_BOT_TOKEN") and config.get("TELEGRAM_CHAT_ID"))
        return self._enabled

    def send_message(self, text: str) -> bool | None:
        """Send *text* to the configured Telegram chat.

        Returns True on success, False on HTTP error, None if disabled.
        """
        if not self.enabled:
            logger.debug("Telegram notifier disabled — missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
            return None

        if config.is_dry_run():
            logger.info("[DRY RUN] Would send Telegram: %s", text[:80])
            return True

        token = config.get("TELEGRAM_BOT_TOKEN")
        chat_id = config.get("TELEGRAM_CHAT_ID")
        url = _API_TEMPLATE.format(token=token)

        session = self._session or requests
        try:
            resp = session.post(url, json={"chat_id": chat_id, "text": text})
            if resp.status_code == 200:
                logger.info("Telegram message sent")
                return True
            logger.warning("Telegram API returned %s: %s", resp.status_code, resp.text[:200])
            return False
        except Exception as exc:
            logger.error("Failed to send Telegram message: %s", exc)
            return False
