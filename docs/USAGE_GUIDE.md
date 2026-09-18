# X Suite — Admin Console Usage Guide

A private, single-user control room for your X (Twitter) growth operation. It is **not** a public
website — only you can log in. Everything you see is read straight from your live database, so the
numbers are real.

The console is deliberately **lean**: the autopilot does the work, and the console is just a
monitor plus the one human step — approving drafts.

---

## 1. How to open it

- **URL:** https://x-suite-puce.vercel.app
- **Email / Password:** both live in the root `.env` (`ADMIN_EMAIL`, `ADMIN_PASSWORD`) and the
  matching Vercel environment variables — deliberately **not** written in this file, because this
  repository is public.

> Forgot them? Read `ADMIN_EMAIL` / `ADMIN_PASSWORD` from the root `.env`. To change either, edit
> that file **and** the Vercel env var, then redeploy.

After login you stay signed in for 7 days (browser cookie). Use **Log out** in the top bar when done.

---

## 2. What runs by itself (no intervention)

These are Windows Task Scheduler tasks on your PC. You never have to start them.

| Task | When | What it does |
|------|------|--------------|
| **FollowerDashboard-Observe** | daily 09:00 | Scans your feeds, scores topics, updates the watchlist, and writes **one fresh draft** into the console. |
| **FollowerDashboard-Digest** | daily 18:00 | Builds a Telegram summary. **Paused** — see note below. |
| **FollowerDashboard-PublishApproved** | hourly | Publishes any draft **you approved**. Nothing else. |

> **Telegram is paused (2026-09-18).** Every Telegram message — the daily digest, the draft-approval
> pings from the morning run, and failure alerts — is switched off by commenting out
> `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` in the root `.env`. The pipeline itself is unaffected:
> drafts are still created and approvals still publish. To resume, uncomment those two lines.

**Important:** these run on your machine, so they only fire while your PC is **on and you are logged
in**. If the PC is asleep at 09:00, that run is skipped. (Moving them to a cloud cron is possible if
you want true PC-off reliability — ask and it can be set up.)

**Your only job:** open the console, look at the draft, click Approve or Reject. Everything else is
automatic.

---

## 3. The console (just two screens)

- **Dashboard** — a live overview: followers, groups, observed accounts/posts, posts published,
  drafts waiting, topics learned, watchlist. Plus recently posted, top topics and the watchlist.
- **Activity** — your **review desk**. This is the only place you act.

### The approval loop, step by step

1. Every morning at 09:00 the autopilot writes a draft and it appears in **Activity → Drafts**.
2. You read it. Click **Approve** or **Reject**.
3. Approving flips it to **“Queued · publishing within the hour.”** It stays visible so you can see
   it is in flight — it does not vanish into a black hole.
4. The hourly publisher on your machine sends the queued draft to X and marks it **posted**.
5. It then shows up under **Activity → Recently posted**, with a link to the live tweet.

Nothing is ever published unless you approved it. The system never picks and posts on its own.

---

## 4. When to use it

1. **Once a day (1 min):** open **Activity**. If there's a draft, approve or reject it. Done.
2. **Whenever you're curious:** glance at the **Dashboard** for totals and the last posts.
3. **That's it.** No weekly chores required — the agent grows its own watchlist and topics.

---

## 5. Reference

| Need | Where |
|------|-------|
| Approve / reject a draft | Activity → Drafts |
| See what got published | Activity → Recently posted |
| Overall health | Dashboard |
| Change the password | root `.env` / Vercel `ADMIN_PASSWORD`, then redeploy |
| Check the crons | Windows Task Scheduler → tasks named `FollowerDashboard-*` |
| Log out | Top bar → Log out |

---

## 6. Notes for future you

- **Posting safety.** The publisher only ever sends drafts with status `queued` — i.e. ones you
  approved. A daily cap (`AUTO_POST_MAX_PER_DAY`) also applies.
- **Status vocabulary** in the database: `pending` (needs you) → `queued` (approved, awaiting
  publisher) → `posted` / `failed`; `rejected` is your discard. There is a legacy `approved` value
  from the old Telegram flow that means “already posted” — the system deliberately never touches it.
- **The old on-demand tools** (Analyze, Compare, Cloner, Scraper, etc.) still exist as routes but are
  hidden from the sidebar — they needed a local API that the hosted console can't reach. Re-add them
  to the nav if you ever want them back.
