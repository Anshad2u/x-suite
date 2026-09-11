export interface TweetMetrics {
  replies: number;
  reposts: number;
  likes: number;
  bookmarks: number;
  views: number;
  quote_count: number;
}

export interface TweetScore {
  engagement_score: number;
  view_weighted_score: number;
  bookmark_score: number;
  engagement_rate: number;
  breakdown: {
    replies_x20: number;
    reposts_x2: number;
    likes_x0_5: number;
    bookmarks_x80: number;
  };
}

export interface Tweet {
  tweet_id: string;
  url: string;
  date: string;
  content: string;
  full_content: string;
  score: TweetScore;
  raw_metrics: TweetMetrics;
}

export interface AnalysisResult {
  username: string;
  total_tweets: number;
  formula: string;
  tweets: Tweet[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:5000';

const BYPASS_HEADERS = {
  'Content-Type': 'application/json',
  'bypass-tunnel-reminder': 'true'
};

/**
 * Fetches tweet analysis from the backend API.
 * Falls back to mock data if the backend is unavailable.
 */
async function fetchAnalyzeProfile(
  username: string,
  maxTweets: number = 100
): Promise<AnalysisResult> {
  const resp = await fetch(`${API_BASE}/api/analyze-tweets/${username}`, {
    method: 'GET',
    headers: BYPASS_HEADERS,
    next: { revalidate: 0 }
  });

  if (!resp.ok) {
    const errorText = await resp.text();
    throw new Error(`API error ${resp.status}: ${errorText}`);
  }

  const data = await resp.json();

  // Map the backend response to our frontend interface
  return {
    username: data.username || username,
    total_tweets: data.total_tweets || 0,
    formula:
      data.formula || 'Score = (Replies * 20) + (Reposts * 2) + (Likes * 0.5) + (Bookmarks * 80)',
    tweets: data.tweets || []
  };
}

/**
 * Gets mock data for the given username when backend is unavailable.
 * Uses sample tweets for demonstration purposes.
 */
function getMockAnalyzeProfile(username: string, maxTweets: number = 100): AnalysisResult {
  const tweets: Tweet[] = [];
  const tweetContents = [
    'Just launched my new product! Looking forward to your feedback everyone! 🚀',
    'What do you think about this design choice? Would love to hear your thoughts.',
    'Building in public day 3: the challenges nobody tells you about. #startup',
    '5 lessons from my year in SaaS: 1. Always listen to customers 2. Shipping beats perfection',
    'I tested posting at 9am for 30 days. The results surprised me 🧵',
    'Unpopular opinion: thread posts get less engagement than single tweets. Most people get this wrong.',
    'Excited to share: I just hit 10k followers! Thank you all for the support!',
    'What\'s your favorite productivity tool? Mine is Notion + Sunrise calendar.',
    'The truth is: most people overestimate how much others notice their work.',
    'Testing a new format today. Hope you enjoy this deep dive thread.',
  ];

  const tweetMetricsBase = {
    replies: 0,
    reposts: 0,
    likes: 0,
    bookmarks: 0,
    views: 0,
    quote_count: 0
  };

  const tweetScoreBase = {
    engagement_score: 0,
    view_weighted_score: 0,
    bookmark_score: 0,
    engagement_rate: 0,
    breakdown: {
      replies_x20: 0,
      reposts_x2: 0,
      likes_x0_5: 0,
      bookmarks_x80: 0
    }
  };

  for (let i = 0; i < maxTweets; i++) {
    const content = tweetContents[i % tweetContents.length];
    const metrics = { ...tweetMetricsBase };
    const score = { ...tweetScoreBase };

    // Weight the engagement score based on metrics
    score.engagement_score = (
      metrics.replies * 20 +
      metrics.reposts * 2 +
      metrics.likes * 0.5 +
      metrics.bookmarks * 80
    );

    score.breakdown = {
      replies_x20: metrics.replies * 20,
      reposts_x2: metrics.reposts * 2,
      likes_x0_5: metrics.likes * 0.5,
      bookmarks_x80: metrics.bookmarks * 80
    };

    // Set some metrics based on tweet index for variety
    metrics.replies = Math.floor(Math.random() * 50) + 1;
    metrics.likes = Math.floor(Math.random() * 500) + 1;
    metrics.bookmarks = Math.floor(Math.random() * 20) + 1;
    metrics.views = Math.floor(Math.random() * 10000) + 100;

    tweets.push({
      tweet_id: `tweet_${i}`,
      url: `https://x.com/${username}/status/${i}`,
      date: new Date(Date.now() - i * 86400000).toISOString(),
      content: content,
      full_content: content,
      score: score,
      raw_metrics: metrics
    });
  }

  const totalTweets = tweets.length;
  const formula = 'Score = (Replies * 20) + (Reposts * 2) + (Likes * 0.5) + (Bookmarks * 80)';

  return {
    username: username,
    total_tweets: totalTweets,
    formula: formula,
    tweets: tweets
  };
}

export async function analyzeProfile(
  username: string,
  maxTweets: number = 100
): Promise<AnalysisResult> {
  // Try the backend API first, then fall back to mock data
  try {
    return await fetchAnalyzeProfile(username, maxTweets);
  } catch (err) {
    // Backend unavailable — use mock data for beginner-friendly development
    console.warn('Backend API unavailable, using mock data:', err);
    return getMockAnalyzeProfile(username, maxTweets);
  }
}

// ---------------------------------------------------------------------------
// Account management API (followers, groups, scraping, autopilot)
// These map 1:1 onto the Flask routes in services/api/app.py.
// ---------------------------------------------------------------------------

/**
 * Optional basic auth. The Flask service enables it when APP_PASSWORD is set;
 * leave both unset locally and the header is omitted.
 *
 * Computed lazily: this module is also evaluated during SSR, and building the
 * header at module scope would run `btoa` outside the browser.
 */
function authHeaders(): Record<string, string> {
  const user = process.env.NEXT_PUBLIC_API_USER;
  const pass = process.env.NEXT_PUBLIC_API_PASSWORD;
  if (!user || !pass) return {};
  return { Authorization: 'Basic ' + btoa(`${user}:${pass}`) };
}

/** Fetch JSON from the backend, raising a useful error on failure. */
export async function apiGet<T>(path: string): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: { ...BYPASS_HEADERS, ...authHeaders() },
    cache: 'no-store'
  });
  if (!resp.ok) {
    throw new Error(`API ${resp.status}: ${(await resp.text()).slice(0, 200)}`);
  }
  return resp.json() as Promise<T>;
}

export async function apiSend<T>(
  path: string,
  method: 'POST' | 'PUT' | 'DELETE',
  body?: unknown
): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    method,
    headers: { ...BYPASS_HEADERS, ...authHeaders() },
    body: body === undefined ? undefined : JSON.stringify(body)
  });
  if (!resp.ok) {
    throw new Error(`API ${resp.status}: ${(await resp.text()).slice(0, 200)}`);
  }
  return resp.json() as Promise<T>;
}

// -- types --

export interface Stats {
  total_followers: number;
  total_groups: number;
  group_counts: Record<string, number>;
}

export interface Follower {
  id: number;
  username: string;
  display_name: string | null;
  bio: string | null;
  followers_count: number;
  following_count: number;
  tweets_count: number;
  verified: boolean;
  groups: string;
}

export interface Group {
  name: string;
  description: string;
  color: string;
  created_at: string;
  count: number;
}

export interface ScrapeConfig {
  keywords?: string;
  since?: string;
  max_tweets?: number;
}

export interface ScrapeResult {
  status?: string;
  added?: number;
  total?: number;
  error?: string;
  [key: string]: unknown;
}

export interface PendingApproval {
  id: number;
  post_id: number;
  draft: string;
  reason: string;
  topic: string;
  source_link: string;
  status: string;
  created_at: string;
}

export interface MemorySummary {
  [key: string]: unknown;
}

export interface MemoryTopic {
  topic: string;
  count: number;
  last_seen: string | null;
}

export interface WatchlistEntry {
  id: number;
  handle: string;
  reason: string | null;
  topics: string[] | null;
  first_seen: string | null;
  last_seen: string | null;
}

export interface PostedLogEntry {
  id: number;
  content: string;
  posted_at: string;
  source_key: string | null;
  posted_tweet_id: string | null;
  permalink?: string | null;
}

export interface SourceScore {
  source_key: string;
  posts: number;
  sum_engagement: number;
  updated_at: string;
}

// -- calls --

export const getStats = () => apiGet<Stats>('/api/stats');

export const getFollowers = (group?: string) =>
  apiGet<Follower[]>(`/api/followers${group ? `?group=${encodeURIComponent(group)}` : ''}`);

export const getGroups = () => apiGet<Group[]>('/api/groups');

export const createGroup = (name: string, description = '', color = '#6366f1') =>
  apiSend<{ success: boolean }>('/api/groups', 'POST', { name, description, color });

export const deleteGroup = (name: string) =>
  apiSend<{ success: boolean }>(`/api/groups/${encodeURIComponent(name)}`, 'DELETE');

export const assignFollower = (group: string, username: string) =>
  apiSend<{ success: boolean }>(
    `/api/groups/${encodeURIComponent(group)}/followers`,
    'POST',
    { username }
  );

export const removeFollower = (group: string, username: string) =>
  apiSend<{ success: boolean }>(
    `/api/groups/${encodeURIComponent(group)}/followers`,
    'DELETE',
    { username }
  );

export const getScrapeConfig = (group: string) =>
  apiGet<ScrapeConfig>(`/api/groups/${encodeURIComponent(group)}/scrape-config`);

export const updateScrapeConfig = (group: string, config: ScrapeConfig) =>
  apiSend<{ success: boolean }>(
    `/api/groups/${encodeURIComponent(group)}/scrape-config`,
    'PUT',
    config
  );

export const scrapeFollowing = (username = 'me', limit = 1000) =>
  apiSend<ScrapeResult>('/api/scrape/following', 'POST', { username, limit });

export const scrapeFollowers = (username = 'me', limit = 1000) =>
  apiSend<ScrapeResult>('/api/scrape/followers', 'POST', { username, limit });

export const scrapeGroup = (group: string, maxAccounts?: number) =>
  apiSend<ScrapeResult>('/api/scrape/group', 'POST', { group, max_accounts: maxAccounts });

export const getPendingApprovals = (limit = 20) =>
  apiGet<PendingApproval[]>(`/api/approvals/pending?limit=${limit}`);

export const approveDraft = (id: number) =>
  apiSend<{ result: unknown }>(`/api/approvals/${id}/approve`, 'POST');

export const rejectDraft = (id: number) =>
  apiSend<{ result: unknown }>(`/api/approvals/${id}/reject`, 'POST');

export const runObserve = (maxNew = 20, includeX = false) =>
  apiSend<Record<string, unknown>>('/api/observe/run', 'POST', {
    max_new: maxNew,
    include_x: includeX
  });

export const getMemorySummary = () => apiGet<MemorySummary>('/api/memory/summary');

export const getMemoryTopics = (limit = 20) =>
  apiGet<MemoryTopic[]>(`/api/memory/topics?limit=${limit}`);

export const getWatchlist = (limit = 50) =>
  apiGet<WatchlistEntry[]>(`/api/watchlist?limit=${limit}`);

export const getPostedLog = (limit = 50) =>
  apiGet<PostedLogEntry[]>(`/api/posted-log?limit=${limit}`);

export const getSourceScores = () => apiGet<SourceScore[]>('/api/source-scores');

