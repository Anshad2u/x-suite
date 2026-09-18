import { query, queryOne } from './db';

// ---------------------------------------------------------------------------
// Dashboard overview
// ---------------------------------------------------------------------------

export interface DashboardStats {
  followers: number;
  groups: number;
  accounts: number;
  observedPosts: number;
  posted: number;
  pendingDrafts: number;
  topics: number;
  watchlist: number;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const [followers, groups, accounts, observedPosts, posted, pendingDrafts, topics, watchlist] =
    await Promise.all([
      queryOne<{ n: number }>('SELECT COUNT(*)::int AS n FROM followers'),
      queryOne<{ n: number }>('SELECT COUNT(*)::int AS n FROM groups'),
      queryOne<{ n: number }>('SELECT COUNT(*)::int AS n FROM accounts'),
      queryOne<{ n: number }>('SELECT COUNT(*)::int AS n FROM observed_posts'),
      queryOne<{ n: number }>('SELECT COUNT(*)::int AS n FROM posted_log'),
      queryOne<{ n: number }>("SELECT COUNT(*)::int AS n FROM pending_drafts WHERE status = 'pending'"),
      queryOne<{ n: number }>('SELECT COUNT(*)::int AS n FROM topics'),
      queryOne<{ n: number }>('SELECT COUNT(*)::int AS n FROM accounts WHERE watchlisted')
    ]);
  return {
    followers: followers?.n ?? 0,
    groups: groups?.n ?? 0,
    accounts: accounts?.n ?? 0,
    observedPosts: observedPosts?.n ?? 0,
    posted: posted?.n ?? 0,
    pendingDrafts: pendingDrafts?.n ?? 0,
    topics: topics?.n ?? 0,
    watchlist: watchlist?.n ?? 0
  };
}

export interface GroupStat {
  name: string;
  description: string;
  color: string;
  member_count: number;
}

export async function getGroupStats(): Promise<GroupStat[]> {
  return query<GroupStat>(`SELECT g.name, g.description, g.color,
      COUNT(fg.follower_id)::int AS member_count
    FROM groups g
    LEFT JOIN follower_groups fg ON g.name = fg.group_name
    GROUP BY g.name, g.description, g.color
    ORDER BY g.name`);
}

export interface PostedRow {
  id: number;
  source_username: string | null;
  group_name: string | null;
  content: string;
  posted_at: Date | null;
  source_key: string | null;
  posted_tweet_id: string | null;
}

export async function getRecentPosted(limit = 5): Promise<PostedRow[]> {
  return query<PostedRow>(
    `SELECT id, source_username, group_name, content, posted_at, source_key, posted_tweet_id
     FROM posted_log ORDER BY posted_at DESC NULLS LAST LIMIT $1`,
    [limit]
  );
}

export interface TopicRow {
  name: string;
  observed_count: number;
  relevant_count: number;
  last_seen: Date | null;
}

export async function getTopTopics(limit = 5): Promise<TopicRow[]> {
  return query<TopicRow>(
    `SELECT name, observed_count, relevant_count, last_seen
     FROM topics ORDER BY relevant_count DESC, observed_count DESC LIMIT $1`,
    [limit]
  );
}

export interface PendingDraftRow {
  id: number;
  post_id: string | null;
  draft: string;
  reason: string | null;
  topic: string | null;
  source_link: string | null;
  status: string;
  created_at: Date | null;
}

export async function getPendingDrafts(limit = 5): Promise<PendingDraftRow[]> {
  return query<PendingDraftRow>(
    `SELECT id, post_id, draft, reason, topic, source_link, status, created_at
     FROM pending_drafts WHERE status = 'pending' ORDER BY created_at DESC LIMIT $1`,
    [limit]
  );
}

export interface WatchlistRow {
  username: string;
  display_name: string | null;
  platform: string;
  relevance_score: number;
  topics: unknown;
  last_seen: Date | null;
  watchlisted: boolean;
}

export async function getWatchlist(limit = 5): Promise<WatchlistRow[]> {
  return query<WatchlistRow>(
    `SELECT username, display_name, platform, relevance_score, topics, last_seen, watchlisted
     FROM accounts WHERE watchlisted OR relevance_score >= 0.4
     ORDER BY relevance_score DESC LIMIT $1`,
    [limit]
  );
}

// ---------------------------------------------------------------------------
// Groups
// ---------------------------------------------------------------------------

export interface GroupRow {
  name: string;
  description: string;
  color: string;
  member_count: number;
}

export async function listGroups(): Promise<GroupRow[]> {
  return query<GroupRow>(`SELECT g.name, g.description, g.color,
      COUNT(fg.follower_id)::int AS member_count
    FROM groups g
    LEFT JOIN follower_groups fg ON g.name = fg.group_name
    GROUP BY g.name, g.description, g.color
    ORDER BY g.name`);
}

export async function createGroup(name: string, description = '', color = '#6366f1'): Promise<void> {
  await query(
    `INSERT INTO groups (name, description, color)
     VALUES ($1, $2, $3)
     ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description, color = EXCLUDED.color`,
    [name, description, color]
  );
}

export async function deleteGroup(name: string): Promise<void> {
  await query('DELETE FROM follower_groups WHERE group_name = $1', [name]);
  await query('DELETE FROM groups WHERE name = $1', [name]);
}

// ---------------------------------------------------------------------------
// Followers
// ---------------------------------------------------------------------------

export interface FollowerRow {
  id: number;
  username: string;
  display_name: string | null;
  followers_count: number;
  verified: boolean;
  groups: string; // comma-joined
}

export async function listFollowers(opts: {
  group?: string;
  search?: string;
} = {}): Promise<FollowerRow[]> {
  const conditions: string[] = [];
  const params: unknown[] = [];
  if (opts.group && opts.group !== 'all') {
    params.push(opts.group);
    conditions.push(`f.id IN (SELECT follower_id FROM follower_groups WHERE group_name = $${params.length})`);
  }
  if (opts.search && opts.search.trim()) {
    params.push(`%${opts.search.trim()}%`);
    conditions.push(
      `(f.username ILIKE $${params.length} OR f.display_name ILIKE $${params.length})`
    );
  }
  const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
  return query<FollowerRow>(
    `SELECT f.id, f.username, f.display_name, f.followers_count, f.verified,
        COALESCE(STRING_AGG(g.name, ', ' ORDER BY g.name), '') AS groups
     FROM followers f
     LEFT JOIN follower_groups fg ON f.id = fg.follower_id
     LEFT JOIN groups g ON g.name = fg.group_name
     ${where}
     GROUP BY f.id
     ORDER BY f.username
     LIMIT 200`,
    params
  );
}

export async function listGroupNames(): Promise<string[]> {
  const rows = await query<{ name: string }>('SELECT name FROM groups ORDER BY name');
  return rows.map((r) => r.name);
}

export async function assignFollower(username: string, groupName: string): Promise<void> {
  await query(
    `INSERT INTO follower_groups (follower_id, group_name)
     SELECT f.id, $2 FROM followers f WHERE f.username = $1
     ON CONFLICT DO NOTHING`,
    [username, groupName]
  );
}

export async function removeFollower(username: string, groupName: string): Promise<void> {
  await query(
    `DELETE FROM follower_groups fg
     USING followers f
     WHERE fg.follower_id = f.id AND f.username = $1 AND fg.group_name = $2`,
    [username, groupName]
  );
}

// ---------------------------------------------------------------------------
// Activity
// ---------------------------------------------------------------------------

export async function getMemorySummary(): Promise<Record<string, number>> {
  const rows = await Promise.all([
    queryOne<{ n: number }>('SELECT COUNT(*)::int AS n FROM observed_posts'),
    queryOne<{ n: number }>('SELECT COUNT(*)::int AS n FROM post_insights'),
    queryOne<{ n: number }>('SELECT COUNT(*)::int AS n FROM accounts'),
    queryOne<{ n: number }>('SELECT COUNT(*)::int AS n FROM topics'),
    queryOne<{ n: number }>('SELECT COUNT(*)::int AS n FROM accounts WHERE watchlisted'),
    queryOne<{ n: number }>('SELECT COUNT(*)::int AS n FROM decisions_log')
  ]);
  return {
    observed_posts: rows[0]?.n ?? 0,
    analyzed: rows[1]?.n ?? 0,
    accounts: rows[2]?.n ?? 0,
    topics: rows[3]?.n ?? 0,
    watchlist: rows[4]?.n ?? 0,
    decisions: rows[5]?.n ?? 0
  };
}

export async function getPostedLog(limit = 30): Promise<PostedRow[]> {
  return query<PostedRow>(
    `SELECT id, source_username, group_name, content, posted_at, source_key, posted_tweet_id
     FROM posted_log ORDER BY posted_at DESC NULLS LAST LIMIT $1`,
    [limit]
  );
}

export async function getSourceScores(): Promise<
  { source_key: string; posts: number; sum_engagement: number }[]
> {
  return query(
    `SELECT source_key, posts, sum_engagement FROM source_scores ORDER BY sum_engagement DESC`
  );
}

export async function getFullPendingDrafts(): Promise<PendingDraftRow[]> {
  // 'pending' = needs your call; 'queued' = you approved it, the local
  // publisher will send it within the hour. Both are shown so an approval
  // never disappears into a black hole.
  return query<PendingDraftRow>(
    `SELECT id, post_id, draft, reason, topic, source_link, status, created_at
     FROM pending_drafts WHERE status IN ('pending', 'queued')
     ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END, created_at DESC`
  );
}

export async function approveDraft(id: number): Promise<void> {
  // 'queued' (not 'approved') — the legacy Telegram flow used 'approved' to mean
  // "already posted", so a distinct status keeps this safe from re-posting.
  await query("UPDATE pending_drafts SET status = 'queued' WHERE id = $1 AND status = 'pending'", [
    id
  ]);
}

export async function rejectDraft(id: number): Promise<void> {
  await query("UPDATE pending_drafts SET status = 'rejected' WHERE id = $1 AND status = 'pending'", [
    id
  ]);
}
