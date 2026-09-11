# social-agent (library)

Pure scheduling and draft-queue logic for the x-suite. No I/O, no
credentials, no HTTP clients — the caller injects everything.

> **X access is scraper-only.** This package contains no official X API
> client and no OAuth credentials. Posting is performed by the caller
> through the scraper-based poster in `services/api`.

## What's here

| Module | Responsibility |
| :--- | :--- |
| `social_agent.drafts` | Markdown draft queue — `add_draft`, `list_drafts`, `load_due_drafts` |
| `social_agent.scheduler` | `run_once(app)` — promotes due drafts into the queue, drains due posts, enforces a daily cap |

## The injection contract

`scheduler.run_once` takes one `app` dict:

| Key | Type | Purpose |
| :--- | :--- | :--- |
| `queue` | object | `add_post`, `due_posts`, `mark_posted`, `mark_failed`, `posts_today` |
| `posters` | `dict[str, object]` | platform name → object with `.post(content) -> permalink` |
| `notifier` | object, optional | `.send_message(text)` — used for failures only |
| `max_per_day` | int, optional | Daily cap, default `8` |
| `dry_run` | bool, optional | **Defaults to `True`** — an unconfigured scheduler never posts |

Returns `{posted, failed, skipped_budget, dry_run}`.

## Budget model

The old `480/500` monthly cap existed because the official X API free tier
allows 500 posts/month. This package does not use that API, so the cap is
gone. The daily cap (`max_per_day`) plus posting jitter in the API service
are now the only throttle.

## Wiring it up

`services/api/agent_cli.py` provides the real implementations (Postgres
queue, scraper poster, Telegram notifier) and the CLI entry point.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

All tests run offline against in-memory fakes.
