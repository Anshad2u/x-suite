'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';
import { IconPlus, IconMinus, IconRefresh, IconUsers } from '@tabler/icons-react';
import {
  assignFollower,
  getFollowers,
  getGroups,
  removeFollower,
  type Follower,
  type Group
} from '@/lib/api';

export default function FollowersPage() {
  const [followers, setFollowers] = useState<Follower[]>([]);
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [groupFilter, setGroupFilter] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [busy, setBusy] = useState<string | null>(null);
  // Per-row target group for the add/remove buttons.
  const [rowTarget, setRowTarget] = useState<Record<string, string>>({});

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [f, g] = await Promise.all([
        getFollowers(groupFilter === 'all' ? undefined : groupFilter),
        getGroups()
      ]);
      setFollowers(f);
      setGroups(g);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load followers');
    } finally {
      setLoading(false);
    }
  }, [groupFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const visible = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return followers;
    return followers.filter(
      (f) =>
        f.username.toLowerCase().includes(q) ||
        (f.display_name ?? '').toLowerCase().includes(q)
    );
  }, [followers, search]);

  const mutate = async (username: string, group: string, action: 'add' | 'remove') => {
    setBusy(`${username}:${group}:${action}`);
    setError(null);
    try {
      if (action === 'add') await assignFollower(group, username);
      else await removeFollower(group, username);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed');
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="container mx-auto py-8 max-w-7xl">
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-2">All Followers</h1>
          <p className="text-muted-foreground">
            Assign followers to groups. Group membership drives which accounts get
            scraped and which sources the autopilot curates from.
          </p>
        </div>
        <Button variant="outline" onClick={load} disabled={loading}>
          <IconRefresh className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card className="mb-6">
        <CardContent className="pt-6 flex flex-wrap items-center gap-3">
          <Select value={groupFilter} onValueChange={(v) => setGroupFilter(v ?? 'all')}>
            <SelectTrigger className="w-56">
              <SelectValue placeholder="Filter by group" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All followers</SelectItem>
              {groups.map((g) => (
                <SelectItem key={g.name} value={g.name}>
                  {g.name} ({g.count})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input
            placeholder="Search username or name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-xs"
          />
          <span className="text-sm text-muted-foreground ml-auto">
            {visible.length} shown
          </span>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <IconUsers className="w-5 h-5" />
            Followers
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : visible.length === 0 ? (
            <p className="text-sm text-muted-foreground py-8 text-center">
              No followers yet. Go to <strong>Scrape</strong> and fetch your
              following/followers first.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Username</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead className="text-right">Followers</TableHead>
                  <TableHead>Groups</TableHead>
                  <TableHead className="w-72">Assign</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {visible.map((f) => {
                  const current = (f.groups || '')
                    .split(',')
                    .map((s) => s.trim())
                    .filter(Boolean);
                  const target = rowTarget[f.username] ?? groups[0]?.name ?? '';
                  return (
                    <TableRow key={f.username}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <a
                            href={`https://x.com/${f.username}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-500 hover:underline"
                          >
                            @{f.username}
                          </a>
                          {f.verified && <Badge variant="outline">verified</Badge>}
                        </div>
                      </TableCell>
                      <TableCell className="max-w-xs truncate text-sm text-muted-foreground">
                        {f.display_name || '—'}
                      </TableCell>
                      <TableCell className="text-right font-mono text-sm">
                        {f.followers_count.toLocaleString()}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {current.length === 0 ? (
                            <span className="text-xs text-muted-foreground">none</span>
                          ) : (
                            current.map((g) => (
                              <Badge key={g} variant="secondary">
                                {g}
                              </Badge>
                            ))
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        {groups.length === 0 ? (
                          <span className="text-xs text-muted-foreground">
                            Create a group first
                          </span>
                        ) : (
                          <div className="flex items-center gap-2">
                            <Select
                              value={target}
                              onValueChange={(v) =>
                                setRowTarget((prev) => ({
                                  ...prev,
                                  [f.username]: v ?? ''
                                }))
                              }
                            >
                              <SelectTrigger className="w-36">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {groups.map((g) => (
                                  <SelectItem key={g.name} value={g.name}>
                                    {g.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <Button
                              size="icon"
                              variant="outline"
                              title="Add to group"
                              disabled={busy !== null || current.includes(target)}
                              onClick={() => mutate(f.username, target, 'add')}
                            >
                              <IconPlus className="w-4 h-4" />
                            </Button>
                            <Button
                              size="icon"
                              variant="outline"
                              title="Remove from group"
                              disabled={busy !== null || !current.includes(target)}
                              onClick={() => mutate(f.username, target, 'remove')}
                            >
                              <IconMinus className="w-4 h-4" />
                            </Button>
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
