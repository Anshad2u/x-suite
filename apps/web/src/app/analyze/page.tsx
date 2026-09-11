'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { IconLoader, IconSearch, IconTrendingUp, IconChartBar } from '@tabler/icons-react';
import { analyzeProfile, AnalysisResult } from '@/lib/api';
import Link from 'next/link';

export default function AnalyzePage() {
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!username.trim()) return;
    const cleanUsername = username.replace('@', '').trim();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await analyzeProfile(cleanUsername, 100);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Analyze X Profile</h1>
        <p className="text-muted-foreground">
          Enter any X/Twitter username to analyze their tweets, engagement patterns, and growth strategies.
        </p>
      </div>

      {/* Search bar */}
      <div className="flex gap-2 mb-6">
        <Input
          placeholder="Enter username (e.g., wilczyn)"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
          className="max-w-md"
        />
        <Button onClick={handleAnalyze} disabled={loading || !username.trim()}>
          {loading ? (
            <>
              <IconLoader className="w-4 h-4 mr-2 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <IconSearch className="w-4 h-4 mr-2" />
              Analyze
            </>
          )}
        </Button>
      </div>

      {error && (
        <Card className="mb-6 border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {!result && !loading && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>How it works</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              <li>1. Enter an X/Twitter username to analyze</li>
              <li>2. Our system uses authenticated API access to fetch all tweets</li>
              <li>3. Each tweet is scored: <code>Score = (Replies×20) + (Reposts×2) + (Likes×0.5) + (Bookmarks×80)</code></li>
              <li>4. View the top-performing tweets and engagement patterns</li>
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {result && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card>
              <CardHeader>
                <CardTitle className="text-3xl">@{result.username}</CardTitle>
                <p className="text-sm text-muted-foreground">Profile analyzed</p>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-3xl">{result.total_tweets}</CardTitle>
                <p className="text-sm text-muted-foreground">Total tweets</p>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-3xl font-bold text-primary">
                  {Math.round(result.tweets.reduce((sum, t) => sum + t.score.engagement_score, 0))}
                </CardTitle>
                <p className="text-sm text-muted-foreground">Total engagement score</p>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-3xl font-bold text-green-500">
                  {result.tweets.length > 0
                    ? Math.round(result.tweets[0].score.engagement_score)
                    : 0}
                </CardTitle>
                <p className="text-sm text-muted-foreground">Top tweet score</p>
              </CardHeader>
            </Card>
          </div>

          {/* Tweet table */}
          <Card>
            <CardHeader>
              <CardTitle>Top 25 Tweets by Engagement Score</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>#</TableHead>
                    <TableHead>Tweet</TableHead>
                    <TableHead className="text-right">Views</TableHead>
                    <TableHead className="text-right">Likes</TableHead>
                    <TableHead className="text-right">Replies</TableHead>
                    <TableHead className="text-right">Reposts</TableHead>
                    <TableHead className="text-right">Score</TableHead>
                    <TableHead>Rate</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {result.tweets.slice(0, 25).map((tweet, i) => (
                    <TableRow key={tweet.tweet_id}>
                      <TableCell className="font-mono">{i + 1}</TableCell>
                      <TableCell className="max-w-md">
                        <div className="space-y-1">
                          <p className="text-sm line-clamp-3">{tweet.full_content}</p>
                          <a
                            href={tweet.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-500 hover:underline"
                          >
                            View on X →
                          </a>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">{tweet.raw_metrics.views.toLocaleString()}</TableCell>
                      <TableCell className="text-right">{tweet.raw_metrics.likes}</TableCell>
                      <TableCell className="text-right">{tweet.raw_metrics.replies}</TableCell>
                      <TableCell className="text-right">{tweet.raw_metrics.reposts}</TableCell>
                      <TableCell className="text-right font-bold">{tweet.score.engagement_score.toFixed(1)}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{tweet.score.engagement_rate.toFixed(1)}%</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
