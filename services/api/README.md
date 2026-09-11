# Follower Dashboard

A dashboard to categorize your Twitter/X followers, group them, and scrape data from each group.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get your X auth token:**
   - Log into x.com
   - Press F12 to open DevTools
   - Go to Application > Cookies > x.com
   - Copy the `auth_token` value

3. **Set the auth token:**
   ```bash
   set X_AUTH_TOKEN=your_auth_token_here
   ```
   
   Or edit `config.py` directly (not recommended for security).

4. **Optional - Add proxy** (recommended for high volume):
   ```bash
   set X_PROXY=http://user:pass@host:port
   ```

## Running

```bash
python app.py
```

Then open http://localhost:5000 in your browser.

## How to Use

### 1. Fetch Your Following/Followers
Go to the **Scrape** tab and click:
- "Fetch Following" - gets people you follow
- "Fetch Followers" - gets your followers

### 2. Create Groups
Go to the **Groups** tab and click "+ New Group". Give it a name (e.g., "Tech", "Crypto") and color.

### 3. Assign Followers to Groups
Go to **All Followers** and use the dropdown to assign each follower to a group.

### 4. Configure Scrape per Group
Click on a group and set:
- Keywords to search for (comma-separated)
- Date range (since)
- Number of tweets per user

Then click "Start Scraping" to scrape tweets from that group's followers.

## Tweet Analyzer

Analyze any X/Twitter user's tweets and score them by engagement.

### Usage

```bash
python tweet_analyzer.py <username> [max_tweets]
```

**Example:**
```bash
python tweet_analyzer.py wilczyn 500
```

### Formula

```
Score = (Replies * 20) + (Reposts * 2) + (Likes * 0.5) + (Bookmarks * 80)
```

Also calculates:
- **View-Weighted Score**: engagement per 1,000 views
- **Engagement Rate**: score as % of views

### API Endpoint

```
GET /api/analyze-tweets/<username>
```

Returns JSON with scored tweets sorted by engagement.

### Limitations

- X's free tier HTML only shows the latest ~5 tweets per profile
- For full tweet history, add both `X_AUTH_TOKEN` and `CT0` to your `.env`
- To get `CT0`: Log into x.com > F12 > Application > Cookies > x.com > `ct0`

## Files

- `app.py` - Flask backend API
- `data_models.py` - PostgreSQL database functions
- `scraper.py` - Scweet wrapper for scraping
- `config.py` - Configuration
- `tweet_analyzer.py` - Tweet analysis and scoring
- `index.html` - Dashboard frontend (Vue.js)

## Social Maintenance

Passive account upkeep: scheduled auto-post recap + mention alerts via Telegram, for X and Reddit (official APIs only - no engagement bots).

### Features

- **X mention watcher** - scans for tweets mentioning `@TWITTER_USERNAME`, stores them, alerts via Telegram
- **Reddit mention watcher** - checks the Reddit inbox for mentions (PRAW official OAuth), stores them, alerts via Telegram
- **Reddit RSS watcher** - no API key needed - polls subreddit `.rss` feeds, stores candidates; per-post alerts only when keywords/digest configured
- **Reddit health check** - detects shadowban/suspension via `is_suspended`, alerts on problems
- **Reddit poster** - submits a post to a configured subreddit with retry+backoff, Telegram recap
- **Engagement learning** - `learn.py` fetches engagement on posted tweets, credits the source that produced each post
- **Autonomous loop** - every 2h: learn engagement, pick the highest-scoring unused candidate (X group or Reddit feed), post it, cap on posts/day; Telegram only on errors
- **Humanized posting** - random jitter delay before each tweet, retry+backoff on transient X errors
- **`/api/mentions`** / **`/api/reddit/mentions`** - recent mentions (JSON, `?limit=`)
- **`/api/health`** / **`/api/reddit/health`** - config/feature status (JSON)

### New `.env` keys

| Key | Default | Purpose |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | (empty) | Telegram alerts disabled when empty |
| `TELEGRAM_CHAT_ID` | (empty) | Alert destination chat |
| `MENTION_WATCH_LIMIT` | `50` | Max X mentions scanned per run |
| `POST_JITTER_MIN` / `POST_JITTER_MAX` | `2` / `8` | Random delay (s) before posting |
| `POST_MAX_RETRIES` | `3` | Retries on 429/5xx before raising |
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | (empty) | Reddit app credentials (script type) - module disabled when empty |
| `REDDIT_USERNAME` / `REDDIT_PASSWORD` | (empty) | Reddit account login |
| `REDDIT_USER_AGENT` | (empty) | Reddit API user-agent |
| `REDDIT_MENTION_LIMIT` | `50` | Max Reddit inbox mentions scanned per run |
| `REDDIT_POST_SUBREDDIT` | (empty) | Default subreddit for `reddit_poster.py` |
| `REDDIT_FEED_SUBREDDITS` | (empty) | Comma-separated feeds monitored via RSS: subreddits (`python`) or multireddits (`user/trickshame/m/saudi`) |
| `REDDIT_FEED_LIMIT` | `20` | Max feed entries scanned per subreddit per run |
| `REDDIT_FEED_KEYWORDS` | (empty) | Comma-separated keywords; only matching post titles alert (empty = alert all) |
| `REDDIT_FEED_DIGEST` | `0` | `1` = one summary per run (top 5), instead of per-post alerts |

### Run

```bash
python mention_watcher.py            # one X scan + alert
python mention_watcher.py daemon 120 # every 2 minutes
python reddit_watcher.py             # one Reddit inbox scan + alert
python reddit_watcher.py daemon 120  # every 2 minutes
python reddit_feed_watcher.py        # one RSS scan + alert
python reddit_feed_watcher.py daemon # every 5 minutes
python reddit_health.py              # account health check
python reddit_poster.py "Title" "Body" [subreddit]  # post to Reddit
python learn.py                      # one engagement-feedback run
python autopost_runner.py            # one autonomous pick+post (scheduled every 2h)
python autopost_runner.py --dry-run  # preview what would be posted (no live post)
```

## Autonomous mode (full autopilot)

The system runs your X account as a silent curator. Telegram contact happens only for errors and real inbound mentions.

```
multireddits + X group tweets
   -> candidates stored (reddit_feed_log / tweets)
   -> every 2h: learn_once() fetches engagement on posted tweets, credits their source
   -> autopost picks the highest-scoring unused candidate (daily cap)
   -> posts to X, records source_key in posted_log
   -> next run: sources with better engagement earn more picks
```

- Per-post Reddit alerts default OFF. Set `REDDIT_FEED_KEYWORDS` (comma-separated title keywords) and/or `REDDIT_FEED_DIGEST=1` to re-enable filtered or digest alerts.
- Sources learn from real engagement: `source_scores` (`source_key`, `posts`, `sum_engagement`); new sources start at 2.0.
- Dashboard APIs: `/api/source-scores`, `/api/engagements`, `/api/posted-log`, `/api/reddit/feeds`.

### Windows Task Scheduler (survives reboot)

| Task | Schedule | Command (Start in = project root) |
| :--- | :--- | :--- |
| `fd-rss` | At logon | `C:\Python313\python.exe reddit_feed_watcher.py daemon` |
| `fd-mentions` | At logon | `C:\Python313\python.exe mention_watcher.py daemon 120` |
| `fd-api` | At logon | `C:\Python313\python.exe app.py` |
| `fd-autopost` | Every 2h | `C:\Python313\python.exe autopost_runner.py` |

Stop a daemon any time with `Stop-Process -Id (Get-Content <name>.pid)`.