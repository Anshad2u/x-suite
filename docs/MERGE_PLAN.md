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
| 4 — Port follower/group UI | **done** — 4 pages added, all 18 endpoints wired |
| 5 — Retire old UI and prune | **done** — Vue UI and 26 template routes/files removed |
| 6 — Consolidate config and ops | **done** — one root `.env`, `scripts/` wrappers, Task Scheduler repointed |

### Phase 4 — what was ported

The Vue `index.html` had 8 sections; they map onto 4 Next.js pages plus the
existing analysis pages.

| Vue section | New page | Backend endpoints |
| :--- | :--- | :--- |
| Scrape Data | `/scrape` | `/api/stats`, `/api/scrape/following`, `/api/scrape/followers` |
| Groups + scrape config | `/groups` | `/api/groups` (GET/POST/DELETE), `/api/groups/{n}/scrape-config` (GET/PUT), `/api/scrape/group` |
| All Followers | `/followers` | `/api/followers`, `/api/groups/{n}/followers` (POST/DELETE) |
| Approvals, Watchlist, Insights, Memory | `/activity` | `/api/approvals/*`, `/api/observe/run`, `/api/watchlist`, `/api/memory/*`, `/api/posted-log`, `/api/source-scores` |

Supporting changes:
- `lib/api.ts` gained typed client functions (`apiGet` / `apiSend`) for all
  18 endpoints, with optional basic-auth support via
  `NEXT_PUBLIC_API_USER` / `NEXT_PUBLIC_API_PASSWORD`.
- The nav gained the 4 new entries. The next-forge `Dashboard` entry was
  dropped — it pointed at a template demo route that Phase 5 deletes.
- `/activity` loads its 6 panels with `Promise.allSettled`, so one failing
  endpoint (e.g. Reddit unconfigured) doesn't blank the page.

**Not yet done in this phase:** nothing is deleted. `index.html`, the Vite
`dashboard/`, and the template routes are still present — that is Phase 5.

### Phase 5 — what was removed

**Old UI (the point of the phase):**
- `services/api/index.html` — the Vue dashboard
- `services/api/dashboard/` — the Vite frontend
- `app.py`'s `/` route no longer serves a file; it returns a JSON pointer to
  the Next.js app, and the now-unused `send_file` import is gone.

**Next.js template surface:**
- `src/app/dashboard/**` — 23 template routes (overview, kanban, chat,
  billing, forms, products, users, workspaces, profile, elements, …)
- `src/app/api/**` — 4 mock API routes (`products`, `users`)
- `src/features/**` — all 12 feature modules

**Orphaned modules that followed:**
- components: `header`, `app-sidebar`, `info-sidebar`, `page-container`,
  `user-nav`, `cta-github`, `breadcrumbs`, `kbar/`, `forms/`, `modal/`,
  `nav-*`, `org-switcher`, `search-input`, `user-avatar-profile`,
  `file-uploader`, `form-card-skeleton`, `ui/table/` (dir), `ui/kanban.tsx`
- lib: `form`, `data-table`, `parsers`, `searchparams`, `compose-refs`,
  `format`, `api-client`, `form-context`
- hooks: `use-data-table`, `use-breadcrumbs`, `use-nav`, `use-stepper`,
  `use-media-query`, `use-controllable-state`, `use-debounce`,
  `use-debounced-callback`; types: `data-table`

**Kept deliberately:** `components/icons.tsx` (still imported by 7 UI
primitives), `components/ui/*` except the two above, `components/themes/*`,
`components/layout/providers.tsx` + `query-provider.tsx` (root layout),
`lib/api.ts`, `lib/analytics.ts`.

**Two traps worth remembering:**
1. Deleting a route leaves a **stale `.next/types/validator.ts`** that fails
   `tsc` with errors about files that no longer exist. Clear `.next/`.
2. With `"incremental": true`, a stale **`tsconfig.tsbuildinfo`** makes
   `next build` fail with "Root file specified for compilation" for a deleted
   file, even though `tsc --noEmit` passes. Clear it too.




### Two knock-on effects worth calling out

1. **The 480/500 monthly cap disappears.** That cap exists because the official X API free tier allows 500 posts/month. Scraping has no such quota — so `X_MONTHLY_HARD_STOP` is dropped and the existing daily cap (`AUTO_POST_MAX_PER_DAY`, default 8) plus posting jitter become the only throttle. Keep the `counters` table anyway; it is useful for daily accounting.
2. **The Next.js app is currently a subset.** x-growth-hub only has `analyze`, `compare`, and `tools/*`. The follower/groups/scrape screens live only in the Vue `index.html`. Those had to be ported *before* `index.html` was deleted — done in Phase 4.

### Phase 6 — what changed

**One env file.** `.env` at the repo root is now the only one. It was built by
merging `services/api/.env` (9 keys), `services/api/.env.local` (29 keys) and
`apps/web/.env.local` (2 `NEXT_PUBLIC_*` keys) — 36 keys, key parity verified
before the originals were removed. Precedence was flipped in `config.py` so the
root file loads **first** and therefore wins. `apps/web/next.config.ts` calls
`@next/env`'s `loadEnvConfig` on the repo root so the UI reads the same file.

**One loader, not two.** `db.py` used to run its own `load_dotenv` pointed at
`services/api/.env*`. Once those files were retired, `POSTGRES_URL` went empty
and every DB call raised `POSTGRES_URL not configured`. `db.py` now imports
`config` and reads `config.POSTGRES_URL`, so env loading happens in exactly one
place. This is the single most important fix of the phase — it was invisible
until the legacy files were actually deleted.

**Stable ops entry points.** `scripts/` holds `_env.bat` (resolves the repo
root, picks the interpreter, puts `packages/agent` on `PYTHONPATH`) plus four
wrappers. The Task Scheduler entries now point at the wrappers, so they never
need editing again.

**Fixed along the way:**

- `daily_digest.py` had **no `__main__` block** — the scheduled task had never
  actually sent anything. Added.
- `autopost_runner.py` caught its own exception and printed to stderr without
  `sys.exit(1)`, so Task Scheduler recorded a *successful* run on every
  failure. Now exits non-zero.
- The three Task Scheduler entries were all broken: `AutoPost` was disabled and
  pointed at the old repo; `Digest` ran `C:\temp\daily_digest.py`, where the
  flat `import db` cannot resolve; `Observe` ran `\runner.py`, which does not
  exist (`0x800700E0`, bad pathname).
- `.github/workflows/autopost.yml` was nested at `services/api/.github/`, where
  GitHub never reads it. Moved to the repo root and made to fail loudly when
  `AUTO_POST_URL` is unset.
- `apps/web/.github/FUNDING.yml` (next-forge template cruft) advertised the
  upstream author's PayPal. Removed.
- `packages/agent/.env.example` still documented the paid X API
  (`X_API_KEY`, `X_ACCESS_TOKEN`) and a SQLite `DB_PATH`. Removed — the package
  reads no env at all.

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
*Verified:* `run_digest.bat` returned real data from Postgres (exit 0) and
`run_autopost.bat --dry-run` completed a full learn → queue → curate pass
(exit 0, nothing posted). `run_observe.bat` was not executed — it performs a
live observation cycle with LLM calls — but its wrapper is identical and its
module imports were verified.

---

## Risks

| Risk | Mitigation |
| :--- | :--- |
| **Scraper fragility.** Cookie-based scraping breaks when X rotates tokens or changes markup. This is now the *only* X path. | Accept it — the paid API is permanently out of scope. Keep `scraper.py` as the single choke point so a future path can be swapped in without touching callers. |
| **UI port is the largest chunk.** Follower/group CRUD is real work, not a copy-paste. | Do Phase 4 before Phase 5; never delete `index.html` first. |
| **Two post tables could drift.** | Write `post_queue` → `posted_log` in a single transaction. |
| **Vercel can't host the daemons.** | `apps/web` + `services/api` on Vercel; the agent loop runs on a worker host or local Task Scheduler. |
| **next-forge template cruft** inflates build time and confuses navigation. | Phase 5 prunes it explicitly. |

---

## Resolved / open items

**Dropped:** the `XBackend` seam. It only existed to keep the official API
option open; since the paid API is permanently out of scope, the seam would
be dead abstraction.

**Resolved (Phase 4):** the Next.js app was a subset. Scrape, Groups, All
Followers, and group scrape-config have been ported, so the Vue `index.html`
could be deleted in Phase 5 without losing functionality.

## What changed vs. the original plan

Four correctness bugs surfaced during verification and were fixed:

1. **Draft promotion was not idempotent.** Every scheduler pass re-queued
   every due draft, so a 2-hourly loop would have posted each draft
   repeatedly. Fixed with a unique `source_ref` (the draft file path) and
   `ON CONFLICT DO NOTHING`.
2. **The daily budget had two sources of truth.** The scheduler counted
   today's posts from `post_queue` while `autopost` counted from
   `posted_log`, so each loop could spend the full daily allowance. Both now
   read `posted_log`.
3. **Two env loaders.** `config.py` and `db.py` each ran `load_dotenv`, the
   latter against paths that no longer existed after consolidation. Env
   loading now happens only in `config.py`, and `db.py` imports
   `config.POSTGRES_URL`.
4. **The digest never ran.** `daily_digest.py` defined `send_daily_digest()`
   but had no `__main__` block, so its scheduled task was a no-op that
   reported success. Same class of problem as `autopost_runner.py` swallowing
   its own exception without a non-zero exit — both fixed.

