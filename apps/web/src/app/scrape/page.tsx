'use client';

import { useCallback, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import {
  IconDownload,
  IconUsers,
  IconUserPlus,
  IconRefresh,
  IconLoader
} from '@tabler/icons-react';
import { getStats, scrapeFollowers, scrapeFollowing, type Stats } from '@/lib/api';

export default function ScrapePage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loadingStats, setLoadingStats] = useState(true);
  const [username, setUsername] = useState('me');
  const [limit, setLimit] = useState(1000);
  const [running, setRunning] = useState<'following' | 'followers' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);

  const loadStats = useCallback(async () => {
    setLoadingStats(true);
    try {
      setStats(await getStats());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stats');
    } finally {
      setLoadingStats(false);
    }
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const run = async (kind: 'following' | 'followers') => {
    setRunning(kind);
    setError(null);
    setResult(null);
    try {
      const res =
        kind === 'following'
          ? await scrapeFollowing(username.trim() || 'me', limit)
          : await scrapeFollowers(username.trim() || 'me', limit);
      setResult(JSON.stringify(res, null, 2));
      await loadStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scrape failed');
    } finally {
      setRunning(null);
    }
  };

  return (
    <div className="container mx-auto py-8 max-w-5xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Scrape Data</h1>
        <p className="text-muted-foreground">
          Fetch the accounts you follow and your followers. Scraping uses your
          browser session cookies (<code>X_AUTH_TOKEN</code> and <code>CT0</code>) —
          no paid API is involved.
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <Card>
          <CardHeader>
            {loadingStats ? (
              <Skeleton className="h-9 w-20" />
            ) : (
              <CardTitle className="text-3xl">
                {stats?.total_followers?.toLocaleString() ?? 0}
              </CardTitle>
            )}
            <p className="text-sm text-muted-foreground">Followers stored</p>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            {loadingStats ? (
              <Skeleton className="h-9 w-20" />
            ) : (
              <CardTitle className="text-3xl">{stats?.total_groups ?? 0}</CardTitle>
            )}
            <p className="text-sm text-muted-foreground">Groups</p>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-normal text-muted-foreground">
              Members per group
            </CardTitle>
            <div className="flex flex-wrap gap-1 pt-1">
              {stats && Object.keys(stats.group_counts || {}).length > 0 ? (
                Object.entries(stats.group_counts).map(([name, count]) => (
                  <Badge key={name} variant="secondary">
                    {name}: {count}
                  </Badge>
                ))
              ) : (
                <span className="text-sm text-muted-foreground">No groups yet</span>
              )}
            </div>
          </CardHeader>
        </Card>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Fetch accounts</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-end gap-3">
            <div className="min-w-40">
              <label className="text-sm text-muted-foreground">Account</label>
              <Input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="me or a username"
              />
            </div>
            <div className="min-w-32">
              <label className="text-sm text-muted-foreground">Limit</label>
              <Input
                type="number"
                min={1}
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value) || 1000)}
              />
            </div>
            <Button variant="outline" onClick={loadStats}>
              <IconRefresh className="w-4 h-4 mr-2" />
              Refresh stats
            </Button>
          </div>

          <div className="flex flex-wrap gap-3">
            <Button onClick={() => run('following')} disabled={running !== null}>
              {running === 'following' ? (
                <IconLoader className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <IconUserPlus className="w-4 h-4 mr-2" />
              )}
              Fetch Following
            </Button>
            <Button
              variant="outline"
              onClick={() => run('followers')}
              disabled={running !== null}
            >
              {running === 'followers' ? (
                <IconLoader className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <IconUsers className="w-4 h-4 mr-2" />
              )}
              Fetch Followers
            </Button>
          </div>

          <p className="text-xs text-muted-foreground">
            High-volume scrapes may take a while and can be rate limited by X.
            Configure <code>X_PROXY</code> in the API service for larger runs.
          </p>
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <IconDownload className="w-5 h-5" />
              Last result
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-xs bg-muted/40 rounded-lg p-4 overflow-auto max-h-96">
              {result}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
