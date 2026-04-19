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

## Files

- `app.py` - Flask backend API
- `data_models.py` - SQLite database functions
- `scraper.py` - Scweet wrapper for scraping
- `config.py` - Configuration
- `index.html` - Dashboard frontend (Vue.js)