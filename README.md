# x-suite

One monorepo for the X (Twitter) toolset — follower analysis, growth tooling, and autonomous account maintenance.

Previously three separate projects:

| Was | Now | Role |
| :--- | :--- | :--- |
| `follower-dashboard` | `services/api` | Flask API + scraper engine + Postgres |
| `x-growth-hub` | `apps/web` | Next.js 16 UI |
| `social-agent` | `packages/agent` | Scheduling + mention-watching agent |

## Design decisions

- **X access is scraper-only.** Scweet plus browser cookies (`X_AUTH_TOKEN` / `CT0`). The paid X API is deliberately not used and no official-API client exists in this repo.
- **One database.** Postgres for everything. The agent's former SQLite store is gone.
- **One UI.** The Next.js app in `apps/web`. The old Vue `index.html` and the Vite `dashboard/` are pending removal (see `docs/MERGE_PLAN.md`, Phase 5).

## Layout

```
x-suite/
├─ apps/web/            Next.js UI (analyze, compare, tools, follower management)
├─ services/api/        Flask API on :5000 — scraper, groups, posting, Reddit
├─ packages/agent/      Python agent — post queue, drafts, mention watching
└─ docs/MERGE_PLAN.md   Full migration plan and phase status
```

## Setup

```bash
cp .env.example .env          # then fill it in
```

**Python** (API + agent):

```bash
python -m venv .venv
.venv/Scripts/activate         # Windows
pip install -r services/api/requirements.txt
pip install -e packages/agent
```

**Web**:

```bash
cd apps/web && npm install
```

## Running

```bash
python services/api/app.py            # API on http://localhost:5000
cd apps/web && npm run dev            # UI on http://localhost:3000
python -m social_agent.cli status     # agent status
```

## Notable modules

**`services/api`** — `app.py` (Flask routes), `scraper.py` (Scweet wrapper), `poster_browser.py` (browser posting), `autopost.py` + `autopost_runner.py` (autonomous loop), `learn.py` (engagement feedback), `mention_watcher.py`, `reddit_*.py`, `telegram_approval.py`, `memory.py`.

**`packages/agent`** — `scheduler.py` (due-post runner), `drafts.py` (markdown draft queue), `cli.py` (entry point).

## Migration status

Phase 0 (scaffold) is complete. Phases 1–6 are tracked in `docs/MERGE_PLAN.md`.
