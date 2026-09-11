# Project Context — x-suite

Product and domain background. For setup and architecture see the repo-root
`README.md`; for the migration history see `docs/MERGE_PLAN.md`.

> This file previously described a FastAPI + React/Vite + flat-JSON design that
> no longer exists. It has been rewritten to match the running system. The old
> text is recoverable from git history if you want it.

## 1. What this is

An X (Twitter) account-maintenance suite. It watches a set of AI/tech/SaaS
sources, decides what is worth posting, drafts it, queues it, posts it through
the scraper, and then measures the engagement of what it posted to learn which
sources are worth trusting.

It started as a *follower dashboard* — scrape your X following list, sort people
into professional groups, and suggest tweets to repost for a **Saudi-expats /
Indian-community** audience. That audience focus is why the group keywords in
`backfill.py` are bilingual (Arabic + English). The curation target has since
moved to **AI / developer-tools / SaaS** (`config.TARGET_TOPICS`), but the
original groups and their Arabic keyword rules are still live.

## 2. Running stack

| Layer | Technology |
| :--- | :--- |
| API | Flask on `:5000` (`services/api/app.py`) |
| UI | Next.js 16 App Router (`apps/web`) |
| Database | Postgres / Neon — 18 tables, one shared schema |
| X access | **Scraper only** — Scweet + browser cookies. No paid API client exists. |
| LLM | Groq via the `openai` client (`GROQ_BASE_URL`) |
| Alerts / approvals | Telegram bot |

## 3. The pipeline

```
observe  → understand → decide → queue → post → learn
```

- **observe** (`feed_observer.py`) — pull Reddit feeds/subreddits and optionally X
  accounts into `observed_posts`.
- **understand** (`understand.py`, `tweet_analyzer.py`) — LLM analysis into
  `post_insights`, updating `accounts` and `topics`.
- **decide** (`autopost.py`, `engagement.py`) — pick candidates, record the
  rationale in `decisions_log`.
- **queue** (`data_models.py` + `social_agent.scheduler`) — `post_queue` holds
  pending work; drafts come from markdown files in `drafts/`.
- **post** (`poster.py`, `poster_browser.py`) — publish; `posted_log` records
  provenance and the resulting tweet id, written in the same transaction as the
  queue update.
- **learn** (`learn.py`) — fetch engagement for posted tweets, write
  `posted_engagement`, and credit sources in `source_scores`.

`posted_log` is also the single source of truth for the daily budget — both the
scheduler and `autopost` read the same count so they cannot each spend the full
allowance.

## 4. Groups

Seven groups, seeded by `backfill.py` from bilingual bio keywords and stored in
`groups`:

`Saudi Govt` · `News & Media` · `Islamic & Dawah` · `Tech & AI` ·
`Business & Finance` · `Sports` · `Entertainment`

`AUTO_POST_GROUP` (default `Tech & AI`) selects which group the autonomous
fallback curates from.

## 5. Content targeting

- **`config.TARGET_TOPICS`** — AI, machine learning, LLM, AI agents, coding
  agents, developer tools, software engineering, tech, SaaS, online business,
  startups, indie hackers, automation.
- **`config.REDDIT_OBSERVE_FEEDS`** — the `ai_tools` and `saudi` multireddits.
- **`config.REDDIT_OBSERVE_SUBREDDITS`** — AI_Agents, LocalLLaMA, SaaS,
  indiehackers, startups, ArtificialIntelligence, MachineLearning, devtools,
  CodingAgents.
- **`config.X_OBSERVE_ACCOUNTS`** — seed accounts to learn from; the agent grows
  this list itself.

## 6. Scraper notes (still true)

- Auth is `X_AUTH_TOKEN` + `CT0` from browser cookies, both in the root `.env`.
- Profile reads use `s.get_profile_tweets(username, limit=N)` for Scweet v5.
- Fetching many accounts must be batched — see `backfill.py`.
- Posting goes through the same cookie path, not the official API.

## 7. Known state

Live row counts at the time of writing, useful as a sanity baseline:

| Table | Rows |
| :--- | ---: |
| `accounts` | 33 |
| `groups` | 7 |
| `observed_posts` | 251 |
| `post_insights` | 34 |
| `topics` | 29 |
| `posted_log` | 30 |

`DRY_RUN=true` in `.env` means nothing is actually posted. The daily cap is
`AUTO_POST_MAX_PER_DAY`.
