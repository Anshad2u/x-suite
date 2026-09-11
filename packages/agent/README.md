# Social Maintenance Agent

A lightweight Python agent that helps you **maintain** (not grow-hack) your X (Twitter) and Reddit accounts. It schedules posts, watches for mentions, and sends Telegram alerts — all through official APIs with strict rate-limit respect.

## What It Does

- **Schedule posts** — queue drafts as markdown files with optional timestamps; the scheduler posts them when due.
- **Watch mentions** — polls X mentions and Reddit inbox, stores new ones, and sends you a Telegram alert for each.
- **Auto-reply (opt-in)** — optionally reply to mentions with a configurable template (disabled by default).
- **Monthly budget** — tracks X posts per month and hard-stops at 480/500 to stay within free-tier limits.
- **DRY_RUN mode** — everything logs and records in the database without making real API calls. Test safely first.

## Quick Start

```powershell
# 1. Clone / copy the project
cd C:\Users\muzai\social-agent

# 2. Activate the virtual environment
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
copy .env.example .env
# Edit .env with your credentials (see below)

# 5. Test with DRY_RUN=true (default)
python -m social_agent.cli status
python -m social_agent.cli drafts list
python -m social_agent.cli schedule once
python -m social_agent.cli watch once
```

## Getting Credentials

### X (Twitter)
1. Go to the [X Developer Portal](https://developer.x.com/en/portal/dashboard).
2. Create a project and app.
3. Enable **OAuth 1.0a** with **Read and Write** permissions.
4. Generate API Key, API Secret, Access Token, and Access Secret.

### Reddit
1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps).
2. Create a **script** type app (redirect URI: `http://localhost:8080`).
3. Note the client ID (under the app name) and client secret.

### Telegram
1. Message [@BotFather](https://t.me/botfather) on Telegram.
2. Create a new bot, copy the token.
3. Send any message to your bot.
4. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your `chat_id`.

## CLI Usage

```
python -m social_agent.cli --help

python -m social_agent.cli drafts add --platform x --text "Hello world"
python -m social_agent.cli drafts add --platform reddit --text "Maintenance update" --scheduled-at 2025-09-01T12:00:00
python -m social_agent.cli drafts list

python -m social_agent.cli schedule once
python -m social_agent.cli schedule daemon

python -m social_agent.cli watch once
python -m social_agent.cli watch daemon

python -m social_agent.cli status
```

## Budget Notes

- **X free tier**: 500 posts/month. The agent hard-stops at 480 with a warning log.
- **Reddit**: No hard monthly limit, but respect subreddit rules and rate limits.
- **Telegram**: Bot API is free with generous limits.

## Platform ToS

This agent is designed for **single-account maintenance** only:

- Uses official APIs (X API v2, Reddit API via PRAW, Telegram Bot API).
- No stealth browsers, no multi-account creation, no engagement bots.
- No auto-liking, auto-following, or auto-upvoting.
- Respects rate limits and backs off on 429 responses.
- You are responsible for complying with each platform's Terms of Service.

## Running Tests

```powershell
venv\Scripts\python.exe -m pytest tests/ -v
```

All tests run offline with mocked API calls. No credentials needed.

## Project Structure

```
social-agent/
  social_agent/
    __init__.py          # Package init
    config.py            # .env loader, ConfigError
    db.py                # SQLite database layer
    drafts.py            # Markdown draft queue
    clients/
      __init__.py
      x_client.py        # X API v2 client
      reddit_client.py   # Reddit client via PRAW
    scheduler.py         # Post scheduler with budget
    watcher.py           # Mention watcher
    notifier.py          # Telegram alerts
    cli.py               # CLI entry point
  tests/                 # Pytest suite (all offline)
  drafts/                # Sample draft files
  requirements.txt
  .env.example
  README.md
```

## License

MIT
