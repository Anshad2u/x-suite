'use client';

import * as React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { IconSparkles, IconSearch } from '@tabler/icons-react';
import { analyzeProfile, type AnalysisResult, type Tweet } from '@/lib/api';
import { getContentTypeStats, getAccountSummary } from '@/lib/analytics';

export default function PatternsPage() {
  const [username, setUsername] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<AnalysisResult | null>(null);

  const run = async () => {
    if (!username.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await analyzeProfile(username.trim());
      setResult(data);
    } catch (e: any) {
      setError(e?.message || 'Failed to analyze profile');
    } finally {
      setLoading(false);
    }
  };

  const types = result ? getContentTypeStats(result.tweets) : [];
  const summary = result ? getAccountSummary(result.tweets) : null;
  const viral: Tweet[] = result
    ? [...result.tweets]
        .sort((a, b) => (b.score?.engagement_score ?? 0) - (a.score?.engagement_score ?? 0))
        .slice(0, 5)
    : [];

  return (
    <div className='container mx-auto max-w-7xl py-8'>
      <div className='mb-8'>
        <h1 className='text-3xl font-bold mb-2'>Pattern Recognition</h1>
        <p className='text-muted-foreground'>
          Which content formats drive the most engagement for any account — questions,
          threads, hot takes, links, and more.
        </p>
      </div>

      <div className='flex gap-2 mb-6'>
        <Input
          placeholder='Enter username'
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && run()}
          className='max-w-md'
        />
        <Button onClick={run} disabled={loading || !username.trim()}>
          <IconSearch className='w-4 h-4 mr-2' />
          {loading ? 'Analyzing…' : 'Find Patterns'}
        </Button>
      </div>

      {loading && <Skeleton className='h-64 w-full' />}

      {error && (
        <Card className='mb-6 border-destructive'>
          <CardContent className='pt-6 text-sm text-destructive'>{error}</CardContent>
        </Card>
      )}

      {!loading && types.length > 0 && summary && (
        <div className='space-y-6'>
          <Card>
            <CardHeader>
              <CardTitle className='flex items-center gap-2'>
                <IconSparkles className='w-5 h-5 text-primary' />
                Content type performance — @{result?.username}
              </CardTitle>
              <CardDescription>
                Ranked by average score across {summary.totalTweets} tweets
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className='space-y-3'>
                {types.map((t) => (
                  <div key={t.type} className='flex items-center gap-3'>
                    <Badge variant='outline' className='w-32 justify-center'>{t.type}</Badge>
                    <div className='flex-1 h-6 bg-muted rounded overflow-hidden'>
                      <div
                        className='h-full bg-primary rounded'
                        style={{
                          width: `${Math.max((t.avgScore / Math.max(types[0].avgScore, 1)) * 100, 2)}%`
                        }}
                      />
                    </div>
                    <span className='w-56 text-xs text-muted-foreground text-right'>
                      {t.count} tweets ({t.share.toFixed(0)}%) · avg{' '}
                      {Math.round(t.avgScore).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Top 5 viral tweets</CardTitle>
              <CardDescription>
                {summary.viralCount} tweets scored 10x+ above this account&apos;s average
              </CardDescription>
            </CardHeader>
            <CardContent className='space-y-4'>
              {viral.map((t) => (
                <div key={t.tweet_id} className='border rounded-lg p-4 space-y-2'>
                  <p className='text-sm'>{t.content || t.full_content}</p>
                  <div className='flex flex-wrap gap-2 text-xs text-muted-foreground'>
                    <Badge variant='secondary'>
                      Score {Math.round(t.score?.engagement_score ?? 0).toLocaleString()}
                    </Badge>
                    <span>{(t.raw_metrics?.replies ?? 0).toLocaleString()} replies</span>
                    <span>{(t.raw_metrics?.likes ?? 0).toLocaleString()} likes</span>
                    <span>{(t.raw_metrics?.views ?? 0).toLocaleString()} views</span>
                    {t.url && (
                      <a
                        href={t.url}
                        target='_blank'
                        rel='noreferrer'
                        className='text-primary underline'
                      >
                        Open on X
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}

      {!loading && !error && types.length === 0 && (
        <Card>
          <CardContent className='py-10 text-center text-sm text-muted-foreground'>
            Enter a username to discover which content patterns work for them.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
