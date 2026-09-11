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

export async function analyzeProfile(
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
