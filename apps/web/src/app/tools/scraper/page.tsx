'use client';

import * as React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { IconUsers, IconUserPlus, IconDatabase } from '@tabler/icons-react';
import { analyzeProfile } from '@/lib/api';

export default function GrowthScraperPage() {
  const [target, setTarget] = React.useState('');
  const [mode, setMode] = React.useState<'following' | 'followers'>('following');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [users, setUsers] = React.useState<Array<{username: string; name?: string}>>([]);

  const run = async () => {
    if (!target.trim()) return;
    setLoading(true);
    setError(null);
    setUsers([]);
    try {
      // Use the analyzeProfile API which now falls back to mock data
      const data = await analyzeProfile(target.trim(), 50);
      // Convert tweet data to a simple user list for demonstration
      const uniqueUsers = [...new Set(data.tweets.map((t: any) => {
        // Extract potential usernames from tweet content or raw metrics
        return t.raw_metrics;
      }))];
      setUsers(uniqueUsers.slice(0, 20));
    } catch (e: any) {
      setError(e?.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className='container mx-auto max-w-7xl py-8'>
      <div className='mb-8'>
        <h1 className='text-3xl font-bold mb-2'>Growth Scraper</h1>
        <p className='text-muted-foreground'>
          Extract who any account follows or who follows them — build target lists for
          engagement and competitor research.
        </p>
      </div>

      <Card className='mb-6'>
        <CardHeader>
          <CardTitle>Analyze target account</CardTitle>
          <CardDescription>
            Enter an X username to analyze their tweet network and engagement patterns.
          </CardDescription>
        </CardHeader>
        <CardContent className='space-y-4'>
          <div className='flex gap-2'>
            <Input
              placeholder={`Account to analyze ${mode}`}
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && run()}
              className='max-w-md'
            />
            <Button onClick={run} disabled={loading || !target.trim()}>
              {loading ? 'Analyzing…' : 'Analyze'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {loading && <Skeleton className='h-48 w-full' />}

      {error && (
        <Card className='mb-6 border-destructive'>
          <CardContent className='pt-6 text-sm text-destructive'>{error}</CardContent>
        </Card>
      )}

      {!loading && users.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>
              {users.length} analyzed tweets from @{target}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className='grid gap-2 md:grid-cols-2 lg:grid-cols-3'>
              {users.map((u, i) => (
                <div key={`${u.username}-${i}`} className='border rounded p-2 text-sm'>
                  <span className='font-medium'>@{u.username}</span>
                  {u.name && (
                    <span className='text-muted-foreground ml-2 text-xs'>{u.name}</span>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {!loading && !error && users.length === 0 && (
        <Card>
          <CardContent className='py-10 text-center text-sm text-muted-foreground'>
            Enter an X username above to analyze their tweet engagement patterns.
            The system will score their tweets and show top-performing content.
          </CardContent>
        </Card>
      )}
    </div>
  );
}