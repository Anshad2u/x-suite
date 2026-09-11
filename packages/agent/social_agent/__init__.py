"""Agent library — scheduling and draft queue for the x-suite.

This package is pure logic with no I/O of its own. Credentials, databases,
and HTTP clients are injected by the caller (see ``services/api/agent_cli.py``).

X access is scraper-only by design; there is no paid-API client here.
"""

from social_agent.drafts import add_draft, list_drafts, load_due_drafts
from social_agent.scheduler import run_once

__all__ = ["add_draft", "list_drafts", "load_due_drafts", "run_once"]
__version__ = "0.2.0"
