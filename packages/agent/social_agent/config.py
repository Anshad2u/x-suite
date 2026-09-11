"""Configuration loader — reads .env via python-dotenv."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


class ConfigError(Exception):
    """Raised when required configuration keys are missing."""


# Load .env from project root on import
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def get(key: str, default: Any = None) -> str | None:
    """Return the value of an environment variable, or *default*."""
    return os.environ.get(key, default)


def require(keys: list[str]) -> dict[str, str]:
    """Return a dict of key→value for every *key* in *keys*.

    Raises :class:`ConfigError` listing **all** missing keys at once.
    """
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        raise ConfigError(
            f"Missing required config keys: {', '.join(missing)}. "
            "Set them in .env or as environment variables."
        )
    return {k: os.environ[k] for k in keys}


def is_dry_run() -> bool:
    """Return True when DRY_RUN is truthy (default True)."""
    return get("DRY_RUN", "true").lower() in ("true", "1", "yes")
