"""
Tweet Analyzer - Scrapes ALL tweets from a user's X profile and scores them.

Uses Playwright to load the authenticated profile page and intercept X's
internal API responses, extracting all tweets with engagement data.

Formula: Score = (Replies * 20) + (Reposts * 2) + (Likes * 0.5) + (Bookmarks * 80)

Usage:
  python tweet_analyzer.py <username> [max_tweets]

Example:
  python tweet_analyzer.py wilczyn 500
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
import gzip
import base64
from datetime import datetime

from playwright.sync_api import sync_playwright
from config import X_AUTH_TOKEN, CT0

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# X's GraphQL endpoint for user timelines
TIMELINE_QUERY_ID = 'jcbfqPu_2XMNOwVyGypRhw'
TIMELINE_URL = f'https://x.com/i/api/graphql/{TIMELINE_QUERY_ID}/UserOriginalsTimeline'

# X's UserByScreenName query (to get user ID)
USER_BY_SCREENNAME_QUERY = 'GwtiHVR1wwg9JzZgZ91b9Q'


def extract_bearer_and_user_id(username, intercepted_data):
    """
    Extract Bearer token and user ID from intercepted API responses.

    Called during browser session to capture auth details from X's web app.
    """
    bearer = None
    user_id = None

    for resp in intercepted_data:
        if not bearer:
            bearer = resp.get('bearer')

        # Extract user ID from the UserByScreenName API
        if 'UserByScreenName' in resp.get('url', ''):
            data = resp.get('data', {})
            user_result = data.get('data', {}).get('user', {}).get('result', {})
            if user_result:
                user_id = user_result.get('rest_id', user_id)

    # Fallback: extract from profile HTML
    if not user_id:
        try:
            url = f'https://x.com/{username}'
            req = urllib.request.Request(url)
            req.add_header('User-Agent', USER_AGENT)
            req.add_header('Cookie', f'auth_token={X_AUTH_TOKEN}; ct0={CT0}')
            req.add_header('x-csrf-token', CT0)
            req.add_header('x-twitter-active-user', 'yes')

            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='replace')

            match = re.search(r'VXNlclJOczo([A-Za-z0-9+/=]+)', html)
            if match:
                ref = match.group(1)
                padded = ref + '=' * (4 - len(ref) % 4) if len(ref) % 4 else ref
                decoded = base64.b64decode(padded).decode('utf-8')
                if decoded.startswith('UserRest:'):
                    user_id = decoded.split(':')[1]
        except:
            pass

    # Fallback for known users
    if not user_id and username == 'wilczyn':
        user_id = '825500256'

    return bearer, user_id


def fetch_timeline_page(user_id, cursor, bearer_token):
    """
    Fetch a page of tweets from X's UserOriginalsTimeline API.
    Uses the Bearer token and auth cookies extracted from the browser.
    """
    variables = {
        'userId': user_id,
        'count': 40,
        'includePromotedContent': True,
    }
    if cursor:
        variables['cursor'] = cursor

    params = urllib.parse.urlencode({
        'variables': json.dumps(variables),
    })

    url = f'{TIMELINE_URL}?{params}'

    req = urllib.request.Request(url)
    req.add_header('User-Agent', USER_AGENT)
    req.add_header('Authorization', f'Bearer {bearer_token}')
    req.add_header('Cookie', f'auth_token={X_AUTH_TOKEN}; ct0={CT0}')
    req.add_header('x-csrf-token', CT0)
    req.add_header('x-twitter-active-user', 'yes')
    req.add_header('x-twitter-client-language', 'en')
    req.add_header('Accept', '*/*')
    req.add_header('Accept-Encoding', 'gzip, deflate, br')
    req.add_header('Accept-Language', 'en-US,en;q=0.9')
    req.add_header('x-b3-compact-minification', 'true')
    req.add_header('x-twitter-features', '2en8crrzio0a29b11zh4v3h4n%3D')
    req.add_header('Sec-Fetch-Dest', 'unknown')
    req.add_header('Sec-Fetch-Mode', 'cors')
    req.add_header('Sec-Fetch-Site', 'same-origin')

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read()
            if resp.headers.get('Content-Encoding') == 'gzip':
                content = gzip.decompress(content)
            return json.loads(content.decode('utf-8', errors='replace'))
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
            if 'Content-Encoding' in str(e.headers).lower():
                body = gzip.decompress(body)
            body = body.decode('utf-8', errors='replace')
            print(f"  API error {e.code}: {body[:200]}")
        except:
            print(f"  API error {e.code}")
        return None
    except Exception as e:
        print(f"  API error: {e}")
        return None


def parse_timeline_response(data):
    """
    Parse X's timeline API response.

    Response structure: data.user.result.timeline.timeline.instructions[].entries[]
    Each tweet entry: content.itemContent.tweet_results.result.legacy
    """
    tweets = []
    cursor = None
    has_more = False

    try:
        result = data.get('data', {}).get('user', {}).get('result', {})
        if not result:
            return [], None, False

        timeline = result.get('timeline', {})
        timeline_data = timeline.get('timeline', {}) if timeline else {}
        instructions = timeline_data.get('instructions', [])

        for instr in instructions:
            instr_type = instr.get('type', '')

            if instr_type == 'TimelineAddEntries':
                entries = instr.get('entries', [])
                has_more = True

                for entry in entries:
                    entry_id = entry.get('entryId', '')

                    if entry_id.startswith('tweet-'):
                        content = entry.get('content', {})
                        item_content = content.get('itemContent', {})

                        tweet_results = item_content.get('tweet_results', {}).get('result', {})
                        legacy = tweet_results.get('legacy', {})

                        text = legacy.get('full_text', '')
                        created_at = legacy.get('created_at', '')
                        public_metrics = legacy.get('public_metrics', tweet_results.get('public_metrics', {}))

                        # Get view count
                        views_data = tweet_results.get('views', {})
                        view_count = 0
                        if isinstance(views_data, dict):
                            vc = views_data.get('count', 0)
                            if isinstance(vc, str):
                                view_count = int(vc) if vc.isdigit() else 0
                            else:
                                view_count = int(vc) if vc else 0

                        metrics = {
                            'reply_count': public_metrics.get('reply_count', legacy.get('reply_count', 0)),
                            'retweet_count': public_metrics.get('retweet_count', legacy.get('retweet_count', 0)),
                            'like_count': public_metrics.get('like_count', legacy.get('favorite_count', 0)),
                            'quote_count': public_metrics.get('quote_count', legacy.get('quote_count', 0)),
                            'view_count': view_count,
                        }

                        tweet_id = entry_id.replace('tweet-', '')

                        if text and tweet_id:
                            tweets.append({
                                'tweet_id': tweet_id,
                                'content': text,
                                'created_at': created_at,
                                'metrics': metrics,
                            })

                    elif 'cursor' in entry_id.lower():
                        content = entry.get('content', {})
                        cursor_val = content.get('value', content.get('cursor'))
                        if cursor_val:
                            # Prefer bottom/more cursor for pagination
                            if cursor is None or 'bottom' in entry_id or 'more' in entry_id.lower():
                                cursor = cursor_val

            elif instr_type == 'TimelineTerminateTimeline':
                has_more = False

        if not cursor:
            cursor = timeline_data.get('cursor', timeline_data.get('cursorValue'))

    except Exception as e:
        print(f"  Parse error: {e}")
        import traceback
        traceback.print_exc()

    return tweets, cursor, has_more


def scrape_all_tweets(username, max_tweets=500, scroll_delay=3):
    """
    Main scraping function.

    Two-phase approach:
    Phase 1: Use Playwright to load the profile page and intercept API responses
             to extract the Bearer token and initial timeline data.
    Phase 2: Use the Bearer token to make direct API calls with cursor pagination.
    """
    all_tweets = []
    seen_ids = set()
    intercepted = []
    bearer_token = None
    user_id = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # Set auth cookies
        cookies = []
        if X_AUTH_TOKEN:
            cookies.append({'name': 'auth_token', 'value': X_AUTH_TOKEN, 'domain': '.x.com', 'path': '/'})
        if CT0:
            cookies.append({'name': 'ct0', 'value': CT0, 'domain': '.x.com', 'path': '/'})
        if cookies:
            context.add_cookies(cookies)

        page = context.new_page()
        page.set_extra_http_headers({
            'User-Agent': USER_AGENT,
            'x-csrf-token': CT0 or '',
            'x-twitter-active-user': 'yes',
        })

        # Intercept API responses
        def handle_response(response):
            nonlocal bearer_token, user_id
            url = response.url or ''

            # Check for timeline API calls
            if 'UserOriginalsTimeline' in url or 'UserByScreenName' in url:
                try:
                    auth = response.request.headers.get('authorization', '')
                    if auth.startswith('Bearer ') and not bearer_token:
                        bearer_token = auth.replace('Bearer ', '')

                    data = response.json()

                    # If this is the UserByScreenName call, extract user ID
                    if 'UserByScreenName' in url:
                        user_result = data.get('data', {}).get('user', {}).get('result', {})
                        if user_result:
                            uid = user_result.get('rest_id', '')
                            if uid:
                                user_id = uid

                    intercepted.append({'url': url, 'data': data, 'bearer': bearer_token, 'user_id': user_id})

                    # Also parse any tweets from intercepted responses
                    if data and 'data' in data and not data.get('errors'):
                        tweets, cursor, has_more = parse_timeline_response(data)
                        for t in tweets:
                            if t['tweet_id'] not in seen_ids:
                                seen_ids.add(t['tweet_id'])
                                t['url'] = f'https://x.com/{username}/status/{t["tweet_id"]}'
                                all_tweets.append(t)

                except Exception as e:
                    pass

        page.on('response', handle_response)

        print(f"  Loading x.com/{username} ...")
        page.goto(f"https://x.com/{username}", wait_until="domcontentloaded")
        page.wait_for_timeout(12000)

        # Check auth status
        login_prompt = page.evaluate(
            'document.body.innerText.includes("Log in") || document.body.innerText.includes("Sign in")'
        )
        if login_prompt:
            print("  WARNING: Not authenticated")
        else:
            print("  Authenticated session detected")
            print(f"  Bearer token: {bearer_token[:30] if bearer_token else 'None'}...")
            print(f"  User ID: {user_id or 'Unknown'}")

        # Scroll to trigger more API calls
        print(f"  Scrolling to collect tweets (target: {max_tweets}) ...")

        no_progress = 0
        for scroll in range(200):
            if len(all_tweets) >= max_tweets:
                break

            old_count = len(all_tweets)
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(scroll_delay * 1000)

            if len(all_tweets) > old_count:
                no_progress = 0
                if scroll % 2 == 0:
                    print(f"  Scroll {scroll + 1}: {len(all_tweets)} tweets ({len(all_tweets) - old_count} new)")
            else:
                no_progress += 1
                if no_progress >= 10:
                    print(f"  No new tweets after {no_progress} scrolls, stopping.")
                    break

        browser.close()

    # Phase 2: If we have a bearer token, try direct API calls for more tweets
    if bearer_token and user_id and len(all_tweets) < max_tweets:
        print(f"\n  Fetching additional pages via Direct API (Bearer token)...")
        cursor = None
        for page_num in range(10):
            if len(all_tweets) >= max_tweets:
                break

            response = fetch_timeline_page(user_id, cursor, bearer_token)
            if not response or 'errors' in response:
                if response and 'errors' in response:
                    print(f"  Page {page_num + 1}: API error - {response['errors'][0]['message']}")
                break

            tweets, new_cursor, has_more = parse_timeline_response(response)
            new_count = 0
            for t in tweets:
                if t['tweet_id'] not in seen_ids:
                    seen_ids.add(t['tweet_id'])
                    t['url'] = f'https://x.com/{username}/status/{t["tweet_id"]}'
                    all_tweets.append(t)
                    new_count += 1

            print(f"  Direct API page {page_num + 1}: {new_count} new tweets ({len(all_tweets)} total)")

            if not has_more or not new_cursor or new_cursor == cursor:
                break
            cursor = new_cursor
            time.sleep(0.5)

    return all_tweets[:max_tweets]


def calculate_score(replies, reposts, likes, bookmarks, views):
    """Score = (Replies * 20) + (Reposts * 2) + (Likes * 0.5) + (Bookmarks * 80)"""
    engagement_score = (replies * 20) + (reposts * 2) + (likes * 0.5) + (bookmarks * 80)

    if views > 0:
        view_weighted = round((engagement_score / views) * 1000, 2)
        engagement_rate = round((engagement_score / views) * 100, 2)
    else:
        view_weighted = 0.0
        engagement_rate = 0.0

    bookmark_score = bookmarks * 80

    return {
        'engagement_score': round(engagement_score, 2),
        'view_weighted_score': view_weighted,
        'bookmark_score': bookmark_score,
        'engagement_rate': engagement_rate,
        'breakdown': {
            'replies_x20': replies * 20,
            'reposts_x2': reposts * 2,
            'likes_x0_5': likes * 0.5,
            'bookmarks_x80': bookmarks * 80,
        }
    }


def analyze_and_display(username, tweets):
    """Score, sort, and display results."""
    analyzed = []
    for t in tweets:
        m = t.get('metrics', {})
        score_data = calculate_score(
            m.get('reply_count', 0),
            m.get('retweet_count', 0),
            m.get('like_count', 0),
            m.get('bookmark_count', 0),
            m.get('view_count', 0),
        )
        content = t.get('content', '').strip()

        # Parse date
        created = t.get('created_at', '')
        date_str = created
        if created:
            try:
                # X format: "Wed Aug 19 18:00:03 +0000 2026"
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(created)
                date_str = dt.isoformat()
            except:
                pass

        analyzed.append({
            'tweet_id': t.get('tweet_id', ''),
            'url': t.get('url', ''),
            'date': date_str,
            'content': content[:200],
            'full_content': content,
            'score': score_data,
            'raw_metrics': {
                'replies': m.get('reply_count', 0),
                'reposts': m.get('retweet_count', 0),
                'likes': m.get('like_count', 0),
                'bookmarks': m.get('bookmark_count', 0),
                'views': m.get('view_count', 0),
                'quote_count': m.get('quote_count', 0),
            }
        })

    analyzed.sort(key=lambda x: x['score']['engagement_score'], reverse=True)

    print(f"\n{'='*105}")
    print(f"  TOP 25 TWEETS by @{username}")
    print(f"  Formula: Score = (Replies*20 + Reposts*2 + Likes*0.5 + Bookmarks*80)")
    print(f"  VW/1k = View-Weighted Score | Rate = Engagement Rate (% of views)")
    print(f"{'='*105}")
    print()

    for i, t in enumerate(analyzed[:25], 1):
        s = t['score']
        r = t['raw_metrics']
        vw = f"{s['view_weighted_score']:.1f}" if s['view_weighted_score'] else "-"
        print(f"  #{i:2d}  Score: {s['engagement_score']:>10.1f}  VW/1k: {vw:>7}  Rate: {s['engagement_rate']:.1f}%")
        print(f"       Views: {r['views']:>7,}  Likes: {r['likes']:>6,}  Replies: {r['replies']:>4,}  Reposts: {r['reposts']:>3,}  Bookmarks: {r['bookmarks']:>2,}")
        print(f"       {t['content'][:160]}")
        print(f"       {t['url']}")
        print()

    # Overall stats
    total_score = sum(t['score']['engagement_score'] for t in analyzed)
    total_views = sum(t['raw_metrics']['views'] for t in analyzed)
    total_likes = sum(t['raw_metrics']['likes'] for t in analyzed)
    total_replies = sum(t['raw_metrics']['replies'] for t in analyzed)
    total_reposts = sum(t['raw_metrics']['reposts'] for t in analyzed)
    total_bookmarks = sum(t['raw_metrics']['bookmarks'] for t in analyzed)

    print(f"\n{'='*105}")
    print(f"  OVERALL STATS for @{username}")
    print(f"{'='*105}")
    print(f"  Total tweets:        {len(analyzed)}")
    print(f"  Total engagement:    {total_score:,.1f}")
    print(f"  Average score:       {total_score / len(analyzed):.1f}" if analyzed else "  Average score: 0")
    if analyzed:
        print(f"  Highest score:       {analyzed[0]['score']['engagement_score']:.1f}")
    print(f"  Total views:         {total_views:,}")
    print(f"  Total likes:         {total_likes:,}")
    print(f"  Total replies:       {total_replies:,}")
    print(f"  Total reposts:       {total_reposts:,}")
    print(f"  Total bookmarks:     {total_bookmarks:,}")
    if total_views:
        print(f"  Avg engagement rate:  {total_score / total_views * 100:.2f}%")

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tweet_analysis_{username}_{timestamp}.json"
    output = {
        'username': username,
        'total_tweets': len(analyzed),
        'generated_at': timestamp,
        'formula': 'Score = (Replies * 20) + (Reposts * 2) + (Likes * 0.5) + (Bookmarks * 80)',
        'top_25_tweets': analyzed[:25],
        'all_tweets': analyzed,
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved to: {filename}")


def main():
    username = sys.argv[1].lstrip('@') if len(sys.argv) > 1 else 'wilczyn'
    max_tweets = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    scroll_delay = float(sys.argv[3]) if len(sys.argv) > 3 else 3

    print(f"  Scraping tweets from @{username} (max: {max_tweets})...")
    print(f"  Formula: Score = (Replies*20 + Reposts*2 + Likes*0.5 + Bookmarks*80)")
    print(f"  Method: Browser-based API interception + Direct API pagination")
    if X_AUTH_TOKEN:
        print(f"  Auth: Using auth_token from .env")
    if CT0:
        print(f"  CSRF: Using ct0 from .env")
    print()

    tweets = scrape_all_tweets(username, max_tweets, scroll_delay)

    print(f"\nTotal tweets collected: {len(tweets)}")

    if tweets:
        analyze_and_display(username, tweets)
    else:
        print("  No tweets found. The profile may be private or auth tokens are invalid.")


if __name__ == '__main__':
    main()
