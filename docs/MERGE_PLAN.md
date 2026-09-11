# Merge Plan — three X projects into one

Merging `follower-dashboard`, `x-growth-hub`, and `social-agent` into a single monorepo.

## Locked decisions

| Decision | Choice | Consequence |
| :--- | :--- | :--- |
| X access | **Scraper only (Scweet)** | Drop social-agent's OAuth1 client. All posting/reading goes through the existing Scweet + browser-cookie path. |
| Frontend | **Next.js only** | Retire Vue `index.html` and the Vite `dashboard/`. Follower/group management screens must be ported to Next.js. |
| Layout | **Monorepo** | `apps/web`, `services/api`, `packages/agent`. |
| Database | **Postgres only** | social-agent's SQLite is retired; its 3 tables are mapped onto the existing Postgres schema. |

> **The paid X API is permanently out of scope.** No official-API client
> exists in this repo and none should be added. The former `XBackend` seam
> (which existed only to keep the API option open) is therefore dropped.

## Status

| Phase | State |
| :--- | :--- |
| 0 — Scaffold monorepo | **done** — history grafted from both repos, uncommitted work preserved |
| 1 — Merge Python (api + agent) | **done** — agent reduced to a pure DI library, 21 tests pass |
| 2 — Unify data layer on Postgres | **done** — `post_queue` + `counters` live, verified against real DB |
| 3 — Collapse the agent loop | **done** — one queue, one daily budget |
| 4 — Port follower/group UI | **not started** |
| 5 — Retire old UI and prune | **not started** |
| 6 — Consolidate config and ops | **not started** |


### Two knock-on effects worth calling out

1. **The 480/500 monthly cap disappears.** That cap exists because the official X API free tier allows 500 posts/month. Scraping has no such quota — so `X_MONTHLY_HARD_STOP` is dropped and the existing daily cap (`AUTO_POST_MAX_PER_DAY`, default 8) plus posting jitter become the only throttle. Keep the `counters` table anyway; it is useful for daily accounting.
2. **The Next.js app is currently a subset.** x-growth-hub only has `analyze`, `compare`, and `tools/*`. The follower/groups/scrape screens live only in the Vue `index.html`. Those must be ported *before* `index.html` is deleted, or functionality is lost.

---

## Target structure

```
x-suite/
├─ apps/
│  └─ web/                  ← x-growth-hub (Next.js 16 + shadcn/ui)
├─ services/
│  └─ api/                  ← follower-dashboard (Flask, port 5000)
├─ packages/
│  └─ agent/                ← social-agent (Python, installable: pip install -e)
├─ docs/
│  └─ MERGE_PLAN.md
├─ .env.example             ← single source of truth
├─ start.bat / start.sh     ← launches api + web + agent loop
└─ README.md
```

`packages/agent` stays a real Python package so `services/api` can `import agent` directly instead of shelling out to a CLI.

---

## Module-by-module mapping

### From `social-agent`

| Module | Action | Notes |
| :--- | :--- | :--- |
| `social_agent/scheduler.py` | **Keep, rewire** | Drop `X_MONTHLY_LIMIT` / `X_MONTHLY_HARD_STOP`. Post via the scraper poster, not `x_client`. |
| `social_agent/drafts.py` | **Keep as-is** | Genuinely new capability — markdown + frontmatter draft queue. Nothing in follower-dashboard does this. |
| `social_agent/cli.py` | **Keep, extend** | Becomes the agent's CLI surface; add commands that call into the API's existing functions. |
| `social_agent/db.py` | **Replace** | SQLite `Database` class → thin wrapper over the Postgres `db.py` helpers. |
| `social_agent/notifier.py` | **Merge** | Fold into the existing `notifier.py`; keep `enabled`/DRY_RUN semantics. |
| `social_agent/config.py` | **Merge** | Collapse into the base `config.py`; keep `get()` / `require()` / `is_dry_run()` helpers, they are cleaner than raw `os.environ`. |
| `social_agent/clients/x_client.py` | **Delete** | OAuth1 path dropped by decision. |
| `social_agent/clients/reddit_client.py` | **Delete** | Duplicate of existing `reddit_client.py` + `reddit_poster.py`. |
| `social_agent/watcher.py` | **Delete** | `mention_watcher.py` + `reddit_watcher.py` already cover this. Salvage only the dedupe-key logic if useful. |

### From `follower-dashboard` (the base)

Stays put, gains an `agent/` sibling package and a few new tables. Its daemons (`mention_watcher.py`, `reddit_feed_watcher.py`, `autopost_runner.py`) keep their current entry points so the Windows Task Scheduler entries survive the move with only a path change.

### From `x-growth-hub`

Becomes `apps/web` largely unchanged. Two jobs:
- **Port** the missing screens from the Vue `index.html`: Scrape, Groups, All Followers, group scrape-config.
- **Prune** the next-forge template cruft that has nothing to do with this product: `dashboard/elements`, `dashboard/forms`, `dashboard/kanban`, `dashboard/chat`, `dashboard/ai-chat`, `dashboard/users`, `dashboard/products`, `dashboard/workspaces`, `dashboard/billing`, `dashboard/react-query`, `features/react-query-demo`.

---

## Data migration (SQLite → Postgres)

Three SQLite tables in social-agent. Mapping:

| SQLite table | Postgres destination | Reason |
| :--- | :--- | :--- |
| `posts` | **new `post_queue`** | Different shape from `posted_log`. `posted_log` records *what was posted and from which source* (provenance + engagement learning); `post_queue` is a *pending work queue*. Keep both, link them. |
| `mentions` | **fold into existing `mentions` + `reddit_mentions`** | Already exist with `alerted`. Add a `replied` column to support opt-in auto-reply. |
| `counters` | **new `counters`** | Generic key/value budget accounting. No existing equivalent. |

### New DDL

```sql
CREATE TABLE IF NOT EXISTS post_queue (
    id           SERIAL PRIMARY KEY,
    platform     TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending','posted','failed')),
    scheduled_at TIMESTAMPTZ,
    posted_at    TIMESTAMPTZ,
    content      TEXT NOT NULL,
    permalink    TEXT,
    error        TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS counters (
    key   TEXT PRIMARY KEY,
    value INTEGER NOT NULL DEFAULT 0
);

ALTER TABLE mentions         ADD COLUMN IF NOT EXISTS replied BOOLEAN DEFAULT FALSE;
ALTER TABLE reddit_mentions  ADD COLUMN IF NOT EXISTS replied BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_post_queue_due
    ON post_queue (status, scheduled_at);
```

### How the two post tables work together

```
post_queue (pending work)
   -> agent loop picks a due row
   -> posts via Scweet poster
   -> post_queue.status = 'posted'
   -> ALSO insert into posted_log (provenance + source_key)
   -> posted_log feeds the existing learn.py engagement loop
```

This preserves follower-dashboard's existing source-scoring loop while gaining social-agent's explicit scheduling.

---

## Phase plan

Each phase ends in a runnable state. Do not start the next until the check passes.

### Phase 0 — Scaffold
Create the monorepo skeleton, `git init`, add `.gitignore` and `.env.example`. Copy the three projects into place with `git mv` where possible to keep history.
**Check:** `git log --follow` still traces files back to their original repos.

### Phase 1 — Merge Python (api + agent)
Move `social_agent/` to `packages/agent/`, merge `config.py` and `notifier.py`, delete the three dead modules. Add `pyproject.toml` for the agent package; `pip install -e packages/agent` from the api service.
**Check:** `python -m agent.cli status` runs; `python app.py` still serves on :5000.

### Phase 2 — Unify the data layer
Run the new DDL. Port `db.py` to Postgres helpers. Rewire `scheduler.py` to write to `post_queue` + `posted_log`, and to post via the scraper poster.
**Check:** a dry run creates a `post_queue` row, posts nothing, and logs the intended post.

### Phase 3 — Collapse the agent loop
Rewrite `autopost_runner.py` to consume `post_queue` and `drafts/` together. Reduce the scheduler entries to: API + one agent loop.
**Check:** one full cycle: draft → queue → (dry-run) post → `posted_log` → engagement fetch.

### Phase 4 — Port the UI
Add Scrape / Groups / Followers / group-config screens to `apps/web`. Point `NEXT_PUBLIC_API_BASE` at the Flask service.
**Check:** every action the Vue `index.html` supported is reachable in Next.js.

### Phase 5 — Retire the old UI and prune
Delete `index.html`, `dashboard/` (Vite), and the next-forge template routes.
**Check:** `next build` passes with no dead imports; no route 404s.

### Phase 6 — Consolidate config and ops
Single `.env`. Rewrite the start scripts and Task Scheduler entries.
**Check:** fresh clone → `.env` → `start.bat` brings up web + api + agent loop.

---

## Risks

| Risk | Mitigation |
| :--- | :--- |
| **Scraper fragility.** Cookie-based scraping breaks when X rotates tokens or changes markup. This is now the *only* X path. | Keep the `XBackend` seam so an official-API implementation can be added later without touching callers. |
| **UI port is the largest chunk.** Follower/group CRUD is real work, not a copy-paste. | Do Phase 4 before Phase 5; never delete `index.html` first. |
| **Two post tables could drift.** | Write `post_queue` → `posted_log` in a single transaction. |
| **Vercel can't host the daemons.** | `apps/web` + `services/api` on Vercel; the agent loop runs on a worker host or local Task Scheduler. |
| **next-forge template cruft** inflates build time and confuses navigation. | Phase 5 prunes it explicitly. |

---

## Resolved / open items

**Dropped:** the `XBackend` seam. It only existed to keep the official API
option open; since the paid API is permanently out of scope, the seam would
be dead abstraction.

**Open (Phase 4):** the Next.js app is still a subset. Scrape, Groups, All
Followers, and group scrape-config exist only in the Vue `index.html` and
must be ported before Phase 5 deletes it.

## What changed vs. the original plan

Two correctness bugs surfaced while verifying Phase 3 and were fixed:

1. **Draft promotion was not idempotent.** Every scheduler pass re-queued
   every due draft, so a 2-hourly loop would have posted each draft
   repeatedly. Fixed with a unique `source_ref` (the draft file path) and
   `ON CONFLICT DO NOTHING`.
2. **The daily budget had two sources of truth.** The scheduler counted
   today's posts from `post_queue` while `autopost` counted from
   `posted_log`, so each loop could spend the full daily allowance. Both now
   read `posted_log`.

