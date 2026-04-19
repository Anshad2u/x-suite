# Project Context: Follower-Dashboard & News Aggregator

## 1. Project Overview
A full-stack application designed to scrape, categorize, and analyze Twitter (X) "Following" lists. The primary goal is to segment followers into professional/official groups and generate tweet suggestions for a specific audience (Saudi Expats/Indians).

## 2. Technical Stack
- **Backend:** FastAPI (Python 3.13)
- **Frontend:** React (TypeScript) + Vite + Tailwind CSS v4
- **Scraper:** `Scweet` library (Customized for v5+ internal GraphQL API calls)
- **Data Storage:** Flat JSON files in `backend/data/` (for portability and speed)

## 3. Backend Endpoints (FastAPI)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/following` | Returns the list of all 729 scraped followers from `following.json`. |
| `GET` | `/groups` | Returns the current group mappings from `groups.json`. |
| `POST` | `/groups` | Creates a new custom group. |
| `POST` | `/groups/{name}/add` | Adds specific usernames to a named group. |
| `POST` | `/groups/{name}/remove` | Removes usernames from a group. |
| `GET` | `/tweets` | Returns the database of scraped tweets from `tweets.json`. |
| `POST` | `/refresh-following`| Triggers `scraper.py` to fetch the latest Following list from X. |
| `POST` | `/fetch-tweets` | Scrapes 1-3 recent tweets for a list of users (or all). |
| `POST` | `/categorize` | Runs the categorization engine (Bios + Tweets + Keywords). |
| `GET` | `/suggestions` | **Targeted Logic:** Scrapes "Saudi News" group, scores tweets via LLM-logic for expat relevance, and returns ranked repost ideas. |

## 4. Data Architecture (`backend/data/`)
- **`following.json`**: Primary profile data (username, name, bio, follower/tweet counts).
- **`tweets.json`**: A dictionary mapping `username` -> `list of strings` (latest tweets).
- **`groups.json`**: Mapping of `Category Name` -> `list of usernames`. 
    - *Note:* Current groups are high-accuracy LLM-categorized: Official Platforms, Saudi Govt, News, Islamic, Tech AI, etc.

## 5. Frontend Features
- **Dashboard View:**
    - Sidebar navigation with segment counts.
    - Global search and filtering by group.
    - **Advanced Filters:** Popularity (>10k followers) and Activity (>1k tweets).
    - Grid layout cards with bio and latest "updates" snippet.
- **Tweet Ideas View:**
    - Dedicated view for Saudi News analysis.
    - Categorizes news into "Labor Law", "Indian Community", "Travel", etc.
    - Provides LLM reasoning ("Why repost?") for each suggestion.

## 6. Known Technical Nuances (For Handover)
- **Scraping:** Requires `X_AUTH_TOKEN` in `.env`. The scraper uses `s.get_profile_tweets(username, limit=count)` for v5 compatibility.
- **Rate Limits:** Fetching all 729 followers' tweets should be done in batches (implemented in the CLI sessions).
- **Tailwind v4:** Uses the `@tailwindcss/vite` plugin. Configuration is handled within `vite.config.ts`, not `tailwind.config.js`.
- **JSX Safety:** Special characters like `>` and `<` in filters are escaped as `&gt;` and `&le;` to prevent OXC parse errors.

## 7. Current Progress Status
- ✅ **Phase 1:** Full Following list (729 users) fetched.
- ✅ **Phase 2:** Recent tweets for all users scraped.
- ✅ **Phase 3:** LLM-based segregation into 9 major professional/official categories complete.
- ✅ **Phase 4:** News suggestion engine for Saudi Expats implemented.
- 🚀 **Next Steps:** Continuous scraping automation or adding an "Auto-Post" feature if requested.
