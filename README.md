# x-suite

One monorepo for the X (Twitter) toolset — follower analysis, growth tooling, and autonomous account maintenance.

Previously three separate projects:

| Was | Now | Role |
| :--- | :--- | :--- |
| `follower-dashboard` | `services/api` | Flask API + scraper engine + Postgres |
| `x-growth-hub` | `apps/web` | Next.js 16 UI |
| `social-agent` | `packages/agent` | Post queue, drafts, scheduling (pure logic) |

## Design decisions

- **X access is scraper-only.** Scweet plus browser cookies (`X_AUTH_TOKEN` / `CT0`). The paid X API is deliberately not used and no official-API client exists in this repo. There are no `X_API_KEY` / `X_ACCESS_TOKEN` variables anywhere — do not add them.
- **One database.** Postgres for everything. The agent's former SQLite store is gone.
- **One UI.** The Next.js app in `apps/web`. The old Vue `index.html` and the Vite `dashboard/` were removed in Phase 5.
- **One env file.** `.env` at the repo root. Both the Python services and the Next.js app read it (see `apps/web/next.config.ts`).
- **The agent library is pure.** `packages/agent` has no runtime dependencies; databases, HTTP clients and credentials are injected by the caller (`services/api/agent_cli.py` does the wiring).

## Layout

```
x-suite/
├─ apps/web/            Next.js UI (analyze, compare, tools, followers, groups, scrape, activity)
├─ services/api/        Flask API on :5000 — scraper, groups, posting, Reddit
├─ packages/agent/      Python agent — post queue, drafts, scheduling (pure logic)
├─ scripts/             Ops entry points for Task Scheduler / manual runs
├─ docs/MERGE_PLAN.md   Full migration plan and phase status
└─ start.bat            Dev entry point: starts API + UI
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
pip install -e packages/agent  # optional: the ops scripts put packages/agent on PYTHONPATH anyway
```

**Web**:

```bash
cd apps/web && npm install
```

## Running

```bash
start.bat                             # starts API + UI in two windows
```

or individually:

```bash
python services/api/app.py            # API on http://localhost:5000
cd apps/web && npm run dev            # UI on http://localhost:3000
python services/api/agent_cli.py status
```

`agent_cli.py` also exposes:

```bash
python services/api/agent_cli.py schedule once     [--dry-run]
python services/api/agent_cli.py schedule daemon   [--interval 300]
python services/api/agent_cli.py drafts list
python services/api/agent_cli.py drafts add --platform x --text "hello"
```

## Scheduled jobs

These run from `scripts/`, so the Task Scheduler entries never need to change again:

| Script | Task Scheduler name | Schedule | Does |
| :--- | :--- | :--- | :--- |
| `scripts/run_autopost.bat` | `FollowerDashboard-AutoPost` | every 4 h | learn engagement → drain post queue → autonomous fallback |
| `scripts/run_observe.bat` | `FollowerDashboard-Observe` | daily 09:00 | one observation cycle (Reddit + optional X) |
| `scripts/run_digest.bat` | `FollowerDashboard-Digest` | daily 18:00 | build the digest, send to Telegram |
| `scripts/run_mentions.bat` | — | manual | check X mentions, queue replies for approval |

All of them share `scripts/_env.bat`, which resolves the repo root, picks the interpreter, and puts `packages/agent` on `PYTHONPATH`.

`DRY_RUN=true` in `.env` means nothing is actually posted. Set it to `false` to go live.

## Notable modules

**`services/api`** — `app.py` (Flask routes), `config.py` (the single env loader), `db.py` (Postgres), `scraper.py` (Scweet wrapper), `poster.py` + `poster_browser.py` (posting), `autopost.py` + `autopost_runner.py` (autonomous loop), `learn.py` (engagement feedback), `data_models.py` (schema + queue), `agent_cli.py` (wiring + CLI), `mention_watcher.py`, `reddit_*.py`, `telegram_approval.py`, `memory.py`.

**`packages/agent`** — `scheduler.py` (due-post runner, DI via Protocols), `drafts.py` (markdown draft queue).

## Deployment

- `apps/web/vercel.json` — deploy `apps/web` as its own Vercel project.
- `services/api/vercel.json` — deploy `services/api` (entry `api/index.py`) as a second Vercel project.
- `.github/workflows/autopost.yml` — hits the deployed `/api/auto-post` every 2 h. Needs the `AUTO_POST_URL` and `AUTO_POST_SECRET` repository secrets.

## Migration status

All phases complete — see `docs/MERGE_PLAN.md` for the per-phase detail and the bugs found along the way.
