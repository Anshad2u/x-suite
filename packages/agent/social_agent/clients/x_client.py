"""X (Twitter) API v2 client — OAuth 1.0a user context."""

from __future__ import annotations

import logging
from typing import Any

from social_agent import config

logger = logging.getLogger(__name__)

_PRIMARY_BASE = "https://api.x.com"
_FALLBACK_BASE = "https://api.twitter.com"


class RateLimitError(Exception):
    """Raised when X API returns HTTP 429."""


class XClient:
    """Thin wrapper around X API v2 with injectable HTTP session."""

    def __init__(self, session: Any | None = None) -> None:
        self._session = session
        self._dry_run_counter = 0

    # -- lazy session --------------------------------------------------------

    @property
    def session(self) -> Any:
        if self._session is None:
            from requests_oauthlib import OAuth1Session

            keys = config.require(
                ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"]
            )
            self._session = OAuth1Session(
                keys["X_API_KEY"],
                client_secret=keys["X_API_SECRET"],
                resource_owner_key=keys["X_ACCESS_TOKEN"],
                resource_owner_secret=keys["X_ACCESS_SECRET"],
            )
        return self._session

    # -- helpers -------------------------------------------------------------

    def _api_url(self, path: str) -> str:
        return f"{_PRIMARY_BASE}{path}"

    def _check_rate_limit(self, resp: Any) -> None:
        if resp.status_code == 429:
            raise RateLimitError(
                f"X API rate limit exceeded (429). "
                f"Reset: {resp.headers.get('x-rate-limit-reset', 'unknown')}"
            )

    # -- public API ----------------------------------------------------------

    def post_tweet(self, text: str) -> dict[str, str]:
        """Post a tweet. Returns {'id': ..., 'permalink': ...}.

        In DRY_RUN mode returns a fake id without hitting the API.
        """
        if config.is_dry_run():
            self._dry_run_counter += 1
            fake_id = f"dry-run-{self._dry_run_counter}"
            logger.info("[DRY RUN] Would post tweet: %s", text[:80])
            return {"id": fake_id, "permalink": f"https://x.com/dry-run/status/{fake_id}"}

        url = self._api_url("/2/tweets")
        resp = self.session.post(url, json={"text": text})
        self._check_rate_limit(resp)
        resp.raise_for_status()

        data = resp.json()
        tweet_id = data["data"]["id"]
        # Try to get username from the response or use 'user' placeholder
        permalink = f"https://x.com/user/status/{tweet_id}"
        logger.info("Posted tweet %s", tweet_id)
        return {"id": tweet_id, "permalink": permalink}

    def fetch_mentions(self) -> list[dict[str, Any]]:
        """Fetch mentions for the authenticated user.

        Returns [] with a logged warning if the free tier rejects the request.
        """
        if config.is_dry_run():
            logger.info("[DRY RUN] Would fetch mentions")
            return []

        try:
            # Step 1: get authenticated user id
            me_resp = self.session.get(
                self._api_url("/2/users/me"),
                headers={"User-Agent": "social-agent/0.1"},
            )
            self._check_rate_limit(me_resp)
            me_resp.raise_for_status()
            user_id = me_resp.json()["data"]["id"]

            # Step 2: fetch mentions
            mentions_resp = self.session.get(
                self._api_url(f"/2/users/{user_id}/mentions"),
                headers={"User-Agent": "social-agent/0.1"},
            )
            self._check_rate_limit(mentions_resp)
            mentions_resp.raise_for_status()

            results: list[dict[str, Any]] = []
            for item in mentions_resp.json().get("data", []):
                results.append(
                    {
                        "id": item["id"],
                        "author": item.get("author_id", "unknown"),
                        "body": item.get("text", ""),
                        "created_at": item.get("created_at", ""),
                    }
                )
            return results

        except RateLimitError:
            raise
        except Exception as exc:
            logger.warning("Failed to fetch X mentions (free tier may not support this): %s", exc)
            return []
