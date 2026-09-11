'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { IconLoader, IconTarget, IconCircleCheck, IconCircleX } from '@tabler/icons-react';
import { analyzeProfile, AnalysisResult } from '@/lib/api';

export default function MyAccountPage() {
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const handleAnalyze = async () => {
    const cleanUsername = username.replace('@', '').trim();
    if (!cleanUsername) return;
    setLoading(true);
    try {
      const data = await analyzeProfile(cleanUsername, 200);
      setResult(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Content insights
  const getTweetType = (content: string): string => {
    const text = content.toLowerCase().trim();
    if (/^(what|which|why|how|is|are|do|does|should|would|can|could|will|should|would)\b/i.test(text)) {
      return 'Question';
    }
    if (text.includes('?') && text.split('\n').length <= 2) {
      return 'Question';
    }
    if (/^(build|ship|launch|just|i recently|today|i published)/i.test(text)) {
      return 'Announcement';
    }
    if (text.includes('\n') && text.split('\n').length > 3) {
      return 'Thread';
    }
    return 'Other';
  };

  const tweet_types: Record<string, { count: number; totalScore: number; avgScore: number; bestScore: number }> = {};
  let total_views = 0;
  let total_engagement = 0;
  let best_engaging: { text: string; score: number; type: string } | null = null;
  let worst_engaging: { text: string; score: number; type: string } | null = null;

  if (result) {
    for (const tweet of result.tweets) {
      const score = tweet.score.engagement_score;
      total_views += tweet.raw_metrics.views;
      total_engagement += score;

      const type = getTweetType(tweet.full_content);
      if (!tweet_types[type]) tweet_types[type] = { count: 0, totalScore: 0, avgScore: 0, bestScore: 0 };
      tweet_types[type].count += 1;
      tweet_types[type].totalScore += score;
      tweet_types[type].bestScore = Math.max(tweet_types[type].bestScore, score);

      if (!best_engaging || score > best_engaging.score) {
        best_engaging = { text: tweet.full_content, score, type };
      }
      if (!worst_engaging || score < worst_engaging.score) {
        worst_engaging = { text: tweet.full_content, score, type };
      }
    }

    // Calculate averages
    for (const type of Object.keys(tweet_types)) {
      tweet_types[type].avgScore = Math.round(tweet_types[type].totalScore / tweet_types[type].count);
    }
  }

  return (
    <div className="container mx-auto py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">My Account Audit</h1>
        <p className="text-muted-foreground">
          Analyze your own X account to find growth opportunities and content patterns.
        </p>
      </div>

      <div className="flex gap-2 mb-6">
        <Input
          placeholder="Enter your X username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
          className="max-w-md"
        />
        <Button onClick={handleAnalyze} disabled={loading || !username.trim()}>
          {loading ? <IconLoader className="w-4 h-4 animate-spin" /> : <IconTarget className="w-4 h-4 mr-2" />}
          {loading ? 'Analyzing...' : 'Audit'}
        </Button>
      </div>

      {result && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card>
              <CardHeader>
                <CardTitle className="text-3xl">{result.total_tweets}</CardTitle>
                <p className="text-sm text-muted-foreground">Tweets analyzed</p>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-3xl font-bold text-primary">
                  {total_views.toLocaleString()}
                </CardTitle>
                <p className="text-sm text-muted-foreground">Total views</p>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-3xl font-bold text-green-500">
                  {Math.round(total_engagement / result.tweets.length)}
                </CardTitle>
                <p className="text-sm text-muted-foreground">Avg score</p>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-3xl font-bold text-purple-500">
                  {(total_engagement / total_views * 100).toFixed(1)}%
                </CardTitle>
                <p className="text-sm text-muted-foreground">Engagement rate</p>
              </CardHeader>
            </Card>
          </div>

          {/* Tweet type performance */}
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Content Type Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(tweet_types).map(([type, stats]) => (
                  <div key={type} className="space-y-2">
                    <div className="flex justify-between">
                      <span className="font-medium">{type}</span>
                      <span className="text-sm text-muted-foreground">
                        {stats.count} tweets · avg score: {stats.avgScore} · best: {stats.bestScore}
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary"
                        style={{
                          width: `${Math.min(100, (stats.avgScore / Math.max(...Object.values(tweet_types).map(s => s.avgScore))) * 100)}%`
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Best and worst tweets */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <IconCircleCheck className="w-5 h-5 text-green-500" />
                  Best Performing Tweet
                </CardTitle>
              </CardHeader>
              <CardContent>
                {best_engaging && (
                  <div className="space-y-3">
                    <p className="text-sm">{best_engaging.text}</p>
                    <Badge>{best_engaging.type}</Badge>
                    <p className="text-2xl font-bold text-green-500">{best_engaging.score.toFixed(1)}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <IconCircleX className="w-5 h-5 text-red-500" />
                  Worst Performing Tweet
                </CardTitle>
              </CardHeader>
              <CardContent>
                {worst_engaging && (
                  <div className="space-y-3">
                    <p className="text-sm">{worst_engaging.text}</p>
                    <Badge>{worst_engaging.type}</Badge>
                    <p className="text-2xl font-bold text-red-500">{worst_engaging.score.toFixed(1)}</p>
                    <p className="text-sm text-muted-foreground">
                      Suggestion: Try asking a question or making it more actionable.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle>Growth Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                <li className="flex items-start gap-2">
                  <IconCircleCheck className="w-4 h-4 mt-0.5 text-green-500" />
                  <span>
                    Your <strong>{best_engaging?.type}</strong> tweets perform best — create more content in this style.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <IconTarget className="w-4 h-4 mt-0.5 text-blue-500" />
                  <span>
                    Your worst performing tweets get {best_engaging ? Math.round(best_engaging.score / 3) : 0}+ fewer engagement points.
                    Consider asking questions or adding a call-to-action.
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <IconTarget className="w-4 h-4 mt-0.5 text-purple-500" />
                  <span>
                    Your average engagement rate is {(total_engagement / total_views * 100).toFixed(1)}%.
                    Aim for 1%+ for strong performance.
                  </span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
