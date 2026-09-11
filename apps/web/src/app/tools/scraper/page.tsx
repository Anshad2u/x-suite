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

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:5000';

interface ScrapedUser {
  username: string;
  name?: string;
  [key: string]: unknown;
}

export default function GrowthScraperPage() {
  const [target, setTarget] = React.useState('');
  const [mode, setMode] = React.useState<'following' | 'followers'>('following');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [users, setUsers] = React.useState<ScrapedUser[]>([]);
  const [stats, setStats] = React.useState<Record<string, unknown> | null>(null);

  const loadStats = React.useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/stats`);
      if (resp.ok) setStats(await resp.json());
    } catch {
      /* stats optional */
    }
  }, []);

  React.useEffect(() => {
    loadStats();
  }, [loadStats]);

  const run = async () => {
    if (!target.trim()) return;
    setLoading(true);
    setError(null);
    setUsers([]);
    try {
      const resp = await fetch(`${API_BASE}/api/scrape/${mode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: target.trim() })
      });
      if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(`Scrape failed (${resp.status}): ${txt.slice(0, 200)}`);
      }
      const data = await resp.json();
      setUsers(data.users || data.followers || data.following || []);
    } catch (e: any) {
      setError(e?.message || 'Scrape failed');
    } finally {
      setLoading(false);
      loadStats();
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

      {stats && (
        <Card className='mb-6'>
          <CardContent className='pt-6 flex flex-wrap gap-6 text-sm'>
            <div className='flex items-center gap-2'>
              <IconDatabase className='w-4 h-4 text-primary' />
              <span className='text-muted-foreground'>Database:</span>
              <span className='font-semibold'>
                {String((stats as any).total_followers ?? (stats as any).followers ?? 0)} users
              </span>
            </div>
            <div className='flex items-center gap-2'>
              <span className='text-muted-foreground'>Groups:</span>
              <span className='font-semibold'>
                {String((stats as any).total_groups ?? (stats as any).groups ?? 0)}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className='mb-6'>
        <CardHeader>
          <CardTitle>Scrape connections</CardTitle>
          <CardDescription>
            Choose what to extract from the target account
          </CardDescription>
        </CardHeader>
        <CardContent className='space-y-4'>
          <div className='flex gap-2'>
            <Button
              variant={mode === 'following' ? 'default' : 'outline'}
              onClick={() => setMode('following')}
            >
              <IconUsers className='w-4 h-4 mr-2' />
              Following
            </Button>
            <Button
              variant={mode === 'followers' ? 'default' : 'outline'}
              onClick={() => setMode('followers')}
            >
              <IconUserPlus className='w-4 h-4 mr-2' />
              Followers
            </Button>
          </div>
          <div className='flex gap-2'>
            <Input
              placeholder={`Account to scrape ${mode} of`}
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && run()}
              className='max-w-md'
            />
            <Button onClick={run} disabled={loading || !target.trim()}>
              {loading ? 'Scraping… (can take a minute)' : 'Scrape'}
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
              {users.length} {mode} found for @{target}
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
            Enter an account above and pick Following or Followers to extract their network.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
