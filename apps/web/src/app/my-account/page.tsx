'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { IconLoader, IconTarget } from '@tabler/icons-react';
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
          {loading ? (
            <IconLoader className="w-4 h-4 animate-spin" />
          ) : (
            <IconTarget className="w-4 h-4 mr-2" />
          )}
          {loading ? 'Analyzing...' : 'Audit'}
        </Button>
      </div>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div>
                <CardTitle className="text-3xl">{result.total_tweets}</CardTitle>
                <p className="text-sm text-muted-foreground">Tweets analyzed</p>
              </div>
              <div>
                <CardTitle className="text-3xl font-bold text-primary">
                  {result.tweets.reduce((sum: number, t: any) => sum + t.raw_metrics.views, 0).toLocaleString()}
                </CardTitle>
                <p className="text-sm text-muted-foreground">Total views</p>
              </div>
              <div>
                <CardTitle className="text-3xl font-bold text-green-500">
                  {Math.round(result.tweets.reduce((sum: number, t: any) => sum + t.score.engagement_score, 0) / result.tweets.length)}
                </CardTitle>
                <p className="text-sm text-muted-foreground">Avg score</p>
              </div>
              <div>
                <CardTitle className="text-3xl font-bold text-purple-500">
                  {(result.tweets.reduce((sum: number, t: any) => sum + t.raw_metrics.views, 0) > 0
                    ? (result.tweets.reduce((sum: number, t: any) => sum + t.score.engagement_score, 0) /
                        result.tweets.reduce((sum: number, t: any) => sum + t.raw_metrics.views, 0) * 100)
                    : 0).toFixed(1)}%
                </CardTitle>
                <p className="text-sm text-muted-foreground">Engagement rate</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {!result && (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Enter a username above to discover growth opportunities and content patterns.
          </CardContent>
        </Card>
      )}
    </div>
  );
}