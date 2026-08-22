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
- `data_models.py` - SQLite database functions
- `scraper.py` - Scweet wrapper for scraping
- `config.py` - Configuration
- `tweet_analyzer.py` - Tweet analysis and scoring
- `index.html` - Dashboard frontend (Vue.js)