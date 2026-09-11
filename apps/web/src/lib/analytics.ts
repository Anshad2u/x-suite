import type { Tweet } from './api';

export interface HourSlot {
  hour: number;
  label: string;
  tweets: number;
  avgScore: number;
  totalScore: number;
}

export interface DaySlot {
  day: string;
  tweets: number;
  avgScore: number;
  totalScore: number;
}

export interface ContentTypeStat {
  type: string;
  count: number;
  avgScore: number;
  avgReplies: number;
  avgViews: number;
  share: number;
}

const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

function parseDate(dateStr: string): Date | null {
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? null : d;
}

export function getHourHistogram(tweets: Tweet[]): HourSlot[] {
  const slots: HourSlot[] = Array.from({ length: 24 }, (_, h) => ({
    hour: h,
    label: `${h.toString().padStart(2, '0')}:00`,
    tweets: 0,
    avgScore: 0,
    totalScore: 0
  }));
  for (const t of tweets) {
    const d = parseDate(t.date);
    if (!d) continue;
    const s = t.score?.engagement_score ?? 0;
    slots[d.getHours()].tweets += 1;
    slots[d.getHours()].totalScore += s;
  }
  for (const slot of slots) {
    slot.avgScore = slot.tweets > 0 ? slot.totalScore / slot.tweets : 0;
  }
  return slots;
}

export function getDayHistogram(tweets: Tweet[]): DaySlot[] {
  return DAYS.map((day) => {
    const dayTweets = tweets.filter((t) => {
      const d = parseDate(t.date);
      return d && DAYS[d.getDay()] === day;
    });
    const total = dayTweets.reduce((acc, t) => acc + (t.score?.engagement_score ?? 0), 0);
    return {
      day,
      tweets: dayTweets.length,
      totalScore: total,
      avgScore: dayTweets.length > 0 ? total / dayTweets.length : 0
    };
  });
}

export function classifyTweet(text: string): string {
  const lower = text.toLowerCase();
  if (/^https?:\/\/\S+$/.test(lower.trim())) return 'Link';
  if (text.includes('🧵') || /((1|2|3)\/|\bthread\b)/i.test(text)) return 'Thread';
  if (/\?\s*$/.test(text.trim()) || /^(what|how|why|who|when|where|which|do you|have you|would you|anyone)\b/i.test(text.trim())) return 'Question';
  if (/^(just|excited|proud|happy to|glad to|we'?re|I'?m)\b.*(launch|ship|releas|announc|introduc)/i.test(lower)) return 'Announcement';
  if (/(https?:\/\/)/.test(text)) return 'Link';
  if (text.length > 240) return 'Long-form';
  if (/(hot take|unpopular|actually|truth is|nobody talks)/i.test(lower)) return 'Hot Take';
  return 'Observation';
}

export function getContentTypeStats(tweets: Tweet[]): ContentTypeStat[] {
  const map = new Map<string, { count: number; score: number; replies: number; views: number }>();
  for (const t of tweets) {
    const type = classifyTweet(t.content || t.full_content || '');
    const cur = map.get(type) || { count: 0, score: 0, replies: 0, views: 0 };
    cur.count += 1;
    cur.score += t.score?.engagement_score ?? 0;
    cur.replies += t.raw_metrics?.replies ?? 0;
    cur.views += t.raw_metrics?.views ?? 0;
    map.set(type, cur);
  }
  const total = tweets.length || 1;
  return Array.from(map.entries())
    .map(([type, v]) => ({
      type,
      count: v.count,
      avgScore: v.score / v.count,
      avgReplies: v.replies / v.count,
      avgViews: v.views / v.count,
      share: (v.count / total) * 100
    }))
    .sort((a, b) => b.avgScore - a.avgScore);
}

export interface CalendarEntry {
  day: string;
  slot: string;
  contentType: string;
  example: string;
  expectedScore: number;
}

export function generateContentCalendar(tweets: Tweet[]): CalendarEntry[] {
  if (tweets.length === 0) return [];
  const dayStats = getDayHistogram(tweets);
  const hourStats = getHourHistogram(tweets);
  const typeStats = getContentTypeStats(tweets);

  // Best days (by avg score), best hours (by avg score, min 2 tweets), best types
  const bestDays = [...dayStats].sort((a, b) => b.avgScore - a.avgScore).slice(0, 7);
  const activeHours = hourStats.filter((h) => h.tweets >= 2);
  const bestHours = (activeHours.length > 0 ? activeHours : hourStats)
    .sort((a, b) => b.avgScore - a.avgScore)
    .slice(0, 3)
    .map((h) => h.hour);

  const calendar: CalendarEntry[] = [];
  bestDays.forEach((day, i) => {
    const hour = bestHours[i % bestHours.length];
    const type = typeStats[i % Math.max(typeStats.length, 1)];
    // find a real example tweet of that type
    const example =
      tweets.find((t) => classifyTweet(t.content || t.full_content || '') === type?.type)
        ?.content || '—';
    calendar.push({
      day: day.day,
      slot: `${hour.toString().padStart(2, '0')}:00`,
      contentType: type?.type || 'Observation',
      example: example.slice(0, 120),
      expectedScore: Math.round(type?.avgScore || 0)
    });
  });
  return calendar;
}

export interface AccountSummary {
  totalTweets: number;
  totalViews: number;
  totalLikes: number;
  totalReplies: number;
  totalReposts: number;
  totalBookmarks: number;
  avgScore: number;
  medianScore: number;
  topScore: number;
  engagementRate: number; // (likes+replies+reposts) / views * 100
  viralCount: number; // tweets > 10x avg score
}

export function getAccountSummary(tweets: Tweet[]): AccountSummary {
  const scores = tweets.map((t) => t.score?.engagement_score ?? 0).sort((a, b) => a - b);
  const sum = (fn: (t: Tweet) => number) => tweets.reduce((acc, t) => acc + fn(t), 0);
  const totalViews = sum((t) => t.raw_metrics?.views ?? 0);
  const totalLikes = sum((t) => t.raw_metrics?.likes ?? 0);
  const totalReplies = sum((t) => t.raw_metrics?.replies ?? 0);
  const totalReposts = sum((t) => t.raw_metrics?.reposts ?? 0);
  const avg = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
  const median = scores.length ? scores[Math.floor(scores.length / 2)] : 0;
  return {
    totalTweets: tweets.length,
    totalViews,
    totalLikes,
    totalReplies,
    totalReposts,
    totalBookmarks: sum((t) => t.raw_metrics?.bookmarks ?? 0),
    avgScore: avg,
    medianScore: median,
    topScore: scores.length ? scores[scores.length - 1] : 0,
    engagementRate: totalViews > 0 ? ((totalLikes + totalReplies + totalReposts) / totalViews) * 100 : 0,
    viralCount: scores.filter((s) => s > avg * 10).length
  };
}

export interface Recommendation {
  title: string;
  detail: string;
  severity: 'good' | 'warn' | 'tip';
}

export function getRecommendations(tweets: Tweet[]): Recommendation[] {
  const recs: Recommendation[] = [];
  if (tweets.length === 0) return recs;
  const summary = getAccountSummary(tweets);
  const types = getContentTypeStats(tweets);
  const hours = getHourHistogram(tweets);
  const days = getDayHistogram(tweets);

  if (types.length > 0) {
    recs.push({
      title: `Double down on "${types[0].type}" tweets`,
      detail: `Your ${types[0].type.toLowerCase()} tweets average ${Math.round(types[0].avgScore)} score — ${Math.round(types[0].avgScore / Math.max(summary.avgScore, 1) * 100)}% of your baseline. Post more of these.`,
      severity: 'good'
    });
  }
  const bestHour = [...hours].sort((a, b) => b.avgScore - a.avgScore)[0];
  if (bestHour && bestHour.tweets >= 2) {
    recs.push({
      title: `Post around ${bestHour.label}`,
      detail: `Tweets posted at ${bestHour.label} average ${Math.round(bestHour.avgScore)} score, your best time slot.`,
      severity: 'tip'
    });
  }
  const bestDay = [...days].sort((a, b) => b.avgScore - a.avgScore)[0];
  if (bestDay && bestDay.tweets >= 2) {
    recs.push({
      title: `${bestDay.day} is your strongest day`,
      detail: `Average score of ${Math.round(bestDay.avgScore)} on ${bestDay.day}. Schedule important posts then.`,
      severity: 'tip'
    });
  }
  if (summary.engagementRate < 1) {
    recs.push({
      title: 'Engagement rate below 1%',
      detail: `Current rate: ${summary.engagementRate.toFixed(2)}%. Ask questions and reply to comments within the first hour to boost replies (worth 20x in the score).`,
      severity: 'warn'
    });
  } else {
    recs.push({
      title: `Healthy engagement rate: ${summary.engagementRate.toFixed(2)}%`,
      detail: 'Above 1% is solid for X. Keep the reply-driving formats coming.',
      severity: 'good'
    });
  }
  if (summary.viralCount > 0) {
    recs.push({
      title: `${summary.viralCount} viral tweet${summary.viralCount > 1 ? 's' : ''} detected`,
      detail: 'Tweets scoring 10x+ your average. Study their format and re-create variations.',
      severity: 'good'
    });
  }
  const questionShare = types.find((t) => t.type === 'Question')?.share ?? 0;
  if (questionShare < 10) {
    recs.push({
      title: 'Post more questions',
      detail: `Only ${questionShare.toFixed(0)}% of your tweets are questions. Questions drive replies — the highest-weighted metric (20x).`,
      severity: 'tip'
    });
  }
  return recs;
}
