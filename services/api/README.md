# services/api

The Flask API and automation engine behind x-suite. Runs on **:5000**.

Setup, env vars and the repo layout live in the [root README](../../README.md).
Product and domain background is in [context.md](context.md). The UI is the
Next.js app in `apps/web` — this service no longer serves any HTML.

## Modules

| File | Role |
| :--- | :--- |
| `app.py` | Flask routes |
| `config.py` | the **single** env loader; everything else imports from here |
| `db.py` | Postgres connection + query helpers |
| `data_models.py` | schema (`init_dbs`) and all table access, incl. the post queue |
| `scraper.py` | Scweet wrapper |
| `poster.py` / `poster_browser.py` | publishing via the cookie path |
| `autopost.py` / `autopost_runner.py` | autonomous selection loop |
| `agent_cli.py` | wires the pure `social_agent` library to Postgres; also the CLI |
| `learn.py` | engagement feedback → `source_scores` |
| `feed_observer.py` / `understand.py` / `tweet_analyzer.py` | observe + analyse |
| `mention_watcher.py` | X mention scanning |
| `reddit_*.py` | Reddit mentions, RSS feeds, health, posting |
| `telegram_approval.py` / `notifier.py` | Telegram alerts and approvals |
| `memory.py` | topics / accounts / decision history |
| `backfill.py` | one-time: scrape your following list, auto-categorise into groups |

## Endpoints

Read: `/api/stats`, `/api/followers`, `/api/followers/<username>`,
`/api/groups`, `/api/groups/<name>/followers`, `/api/groups/<name>/scrape-config`,
`/api/approvals/pending`, `/api/memory/summary`, `/api/memory/topics`,
`/api/memory/recent_actions`, `/api/watchlist`, `/api/posted-log`,
`/api/engagements`, `/api/source-scores`, `/api/mentions`,
`/api/reddit/mentions`, `/api/reddit/feeds`, `/api/health`,
`/api/reddit/health`, `/api/config/status`, `/api/analyze-tweets/<username>`.

Write: `/api/groups` (POST/DELETE), `/api/groups/<name>/followers`,
`/api/scrape/following`, `/api/scrape/followers`, `/api/scrape/group`,
`/api/approvals/<id>/approve|reject`, `/api/auto-post`, `/api/auto-post/dry-run`,
`/api/observe/run`.

Machine callers must send `X-Auto-Post-Secret` matching `AUTO_POST_SECRET`.
Human callers use basic auth against `APP_PASSWORD` (disabled when empty).

## Running the automation

```bash
python mention_watcher.py             # one X mention scan + alert
python mention_watcher.py daemon 120  # every 2 minutes
python reddit_watcher.py              # one Reddit inbox scan + alert
python reddit_feed_watcher.py         # one RSS scan
python reddit_feed_watcher.py daemon  # every 5 minutes
python reddit_health.py               # account health check
python reddit_poster.py "Title" "Body" [subreddit]
python learn.py                       # one engagement-feedback run
python runner.py                      # one full observation cycle
python daily_digest.py                # build + send the digest
python autopost_runner.py             # one autonomous pass
python autopost_runner.py --dry-run   # preview, no live post
python backfill.py [username] [--limit N]
```

`agent_cli.py` drives the Postgres-backed post queue:

```bash
python agent_cli.py status
python agent_cli.py schedule once [--dry-run]
python agent_cli.py schedule daemon [--interval 300]
python agent_cli.py drafts list
python agent_cli.py drafts add --platform x --text "hello"
```

For scheduled use, prefer the wrappers in `../scripts/` — they set the repo
root, the interpreter and `PYTHONPATH` for you.

## Autonomous mode

The account runs as a silent curator. Telegram is contacted only for errors and
real inbound mentions.

```
multireddits + X group tweets
   -> candidates stored (reddit_feed_log / tweets)
   -> every pass: learn_once() fetches engagement on posted tweets, credits their source
   -> autopost picks the highest-scoring unused candidate (daily cap)
   -> posts to X, records source_key in posted_log
   -> next run: sources with better engagement earn more picks
```

- A source with no history gets a prior of **2.0**. After that, its score is
  `sum_engagement / posts`.
- `posted_log` is the single source of truth for the daily budget
  (`AUTO_POST_MAX_PER_DAY`), shared by the queue drain and the autopost
  fallback so they cannot each spend the full allowance.
- Per-post Reddit alerts default OFF. Set `REDDIT_FEED_KEYWORDS` and/or
  `REDDIT_FEED_DIGEST=1` to re-enable filtered or digest alerts.
- `DRY_RUN=true` (the default) records everything but posts nothing.

## Scheduled tasks

Registered in Windows Task Scheduler against the wrappers in `../scripts/`:

| Task | Schedule | Wrapper |
| :--- | :--- | :--- |
| `FollowerDashboard-AutoPost` | every 4 h | `run_autopost.bat` |
| `FollowerDashboard-Observe` | daily 09:00 | `run_observe.bat` |
| `FollowerDashboard-Digest` | daily 18:00 | `run_digest.bat` |

Stop a daemon with `Stop-Process -Id (Get-Content <name>.pid)`.
