'use client';

import { useCallback, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import {
  IconCheck,
  IconX,
  IconRefresh,
  IconPlayerPlay,
  IconLoader
} from '@tabler/icons-react';
import {
  approveDraft,
  getMemorySummary,
  getMemoryTopics,
  getPendingApprovals,
  getPostedLog,
  getSourceScores,
  getWatchlist,
  rejectDraft,
  runObserve,
  type MemoryTopic,
  type PendingApproval,
  type PostedLogEntry,
  type SourceScore,
  type WatchlistEntry
} from '@/lib/api';

export default function ActivityPage() {
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistEntry[]>([]);
  const [topics, setTopics] = useState<MemoryTopic[]>([]);
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const [posted, setPosted] = useState<PostedLogEntry[]>([]);
  const [scores, setScores] = useState<SourceScore[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    // Settle individually so one failing endpoint (e.g. Reddit not configured)
    // doesn't blank the whole page.
    const results = await Promise.allSettled([
      getPendingApprovals(),
      getWatchlist(),
      getMemoryTopics(),
      getMemorySummary(),
      getPostedLog(),
      getSourceScores()
    ]);
    const [a, w, t, s, p, sc] = results;
    if (a.status === 'fulfilled') setApprovals(a.value);
    if (w.status === 'fulfilled') setWatchlist(w.value);
    if (t.status === 'fulfilled') setTopics(t.value);
    if (s.status === 'fulfilled') setSummary(s.value);
    if (p.status === 'fulfilled') setPosted(p.value);
    if (sc.status === 'fulfilled') setScores(sc.value);

    const failed = results.filter((r) => r.status === 'rejected').length;
    if (failed === results.length) {
      setError('Could not reach the API. Is the Flask service running on :5000?');
    } else if (failed > 0) {
      setError(`${failed} of ${results.length} panels failed to load.`);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleObserve = async () => {
    setBusy(true);
    setNotice(null);
    setError(null);
    try {
      const res = await runObserve(20, false);
      setNotice(`Observe run complete: ${JSON.stringify(res).slice(0, 200)}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Observe run failed');
    } finally {
      setBusy(false);
    }
  };

  const handleDecision = async (id: number, action: 'approve' | 'reject') => {
    setBusy(true);
    setError(null);
    try {
      if (action === 'approve') await approveDraft(id);
      else await rejectDraft(id);
      setNotice(`Draft #${id} ${action}d`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setBusy(false);
    }
  };

  const Loading = () => (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-10 w-full" />
      ))}
    </div>
  );

  const Empty = ({ children }: { children: React.ReactNode }) => (
    <p className="text-sm text-muted-foreground py-8 text-center">{children}</p>
  );

  return (
    <div className="container mx-auto py-8 max-w-7xl">
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-2">Activity</h1>
          <p className="text-muted-foreground">
            Autopilot state: pending approvals, discovered accounts, learned topics,
            and what has actually been posted.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={load} disabled={loading}>
            <IconRefresh className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={handleObserve} disabled={busy}>
            {busy ? (
              <IconLoader className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <IconPlayerPlay className="w-4 h-4 mr-2" />
            )}
            Run Observe Now
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {notice && (
        <Alert className="mb-6">
          <AlertDescription>{notice}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="approvals">
        <TabsList>
          <TabsTrigger value="approvals">
            Approvals {approvals.length > 0 && `(${approvals.length})`}
          </TabsTrigger>
          <TabsTrigger value="watchlist">Watchlist</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
          <TabsTrigger value="posted">Posted</TabsTrigger>
        </TabsList>

        {/* Approvals */}
        <TabsContent value="approvals">
          <Card>
            <CardHeader>
              <CardTitle>Pending drafts</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Loading />
              ) : approvals.length === 0 ? (
                <Empty>
                  Nothing awaiting approval. The autopilot posts directly when
                  approval mode is off.
                </Empty>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>#</TableHead>
                      <TableHead>Draft</TableHead>
                      <TableHead>Topic</TableHead>
                      <TableHead>Reason</TableHead>
                      <TableHead className="text-right">Decision</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {approvals.map((a) => (
                      <TableRow key={a.id}>
                        <TableCell className="font-mono text-sm">{a.id}</TableCell>
                        <TableCell className="max-w-md">
                          <p className="text-sm line-clamp-3">{a.draft}</p>
                          {a.source_link && (
                            <a
                              href={a.source_link}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-blue-500 hover:underline"
                            >
                              source →
                            </a>
                          )}
                        </TableCell>
                        <TableCell>
                          {a.topic ? <Badge variant="secondary">{a.topic}</Badge> : '—'}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground max-w-xs">
                          {a.reason || '—'}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              size="sm"
                              disabled={busy}
                              onClick={() => handleDecision(a.id, 'approve')}
                            >
                              <IconCheck className="w-4 h-4 mr-1" />
                              Approve
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={busy}
                              onClick={() => handleDecision(a.id, 'reject')}
                            >
                              <IconX className="w-4 h-4 mr-1" />
                              Reject
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Watchlist */}
        <TabsContent value="watchlist">
          <Card>
            <CardHeader>
              <CardTitle>Watched accounts</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Loading />
              ) : watchlist.length === 0 ? (
                <Empty>No accounts on the watchlist yet.</Empty>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Handle</TableHead>
                      <TableHead>Reason</TableHead>
                      <TableHead>Topics</TableHead>
                      <TableHead>Last seen</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {watchlist.map((w) => (
                      <TableRow key={w.id ?? w.handle}>
                        <TableCell>
                          <a
                            href={`https://x.com/${w.handle}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-500 hover:underline font-medium"
                          >
                            @{w.handle}
                          </a>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground max-w-sm">
                          {w.reason || '—'}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {(w.topics ?? []).length === 0 ? (
                              <span className="text-xs text-muted-foreground">—</span>
                            ) : (
                              (w.topics ?? []).map((t) => (
                                <Badge key={t} variant="secondary">
                                  {t}
                                </Badge>
                              ))
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {w.last_seen ? new Date(w.last_seen).toLocaleString() : '—'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Insights */}
        <TabsContent value="insights">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Top topics</CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Loading />
                ) : topics.length === 0 ? (
                  <Empty>No topics learned yet.</Empty>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Topic</TableHead>
                        <TableHead className="text-right">Mentions</TableHead>
                        <TableHead>Last seen</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {topics.map((t) => (
                        <TableRow key={t.topic}>
                          <TableCell className="font-medium">{t.topic}</TableCell>
                          <TableCell className="text-right">{t.count}</TableCell>
                          <TableCell className="text-xs text-muted-foreground">
                            {t.last_seen ? new Date(t.last_seen).toLocaleDateString() : '—'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Memory summary</CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Loading />
                ) : !summary || Object.keys(summary).length === 0 ? (
                  <Empty>No memory recorded yet.</Empty>
                ) : (
                  <dl className="space-y-2">
                    {Object.entries(summary).map(([k, v]) => (
                      <div key={k} className="flex justify-between gap-4 text-sm">
                        <dt className="text-muted-foreground">{k.replace(/_/g, ' ')}</dt>
                        <dd className="font-mono">
                          {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                        </dd>
                      </div>
                    ))}
                  </dl>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Posted */}
        <TabsContent value="posted">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Recently posted</CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Loading />
                ) : posted.length === 0 ? (
                  <Empty>Nothing posted yet.</Empty>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Content</TableHead>
                        <TableHead>Source</TableHead>
                        <TableHead>Posted</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {posted.map((p) => (
                        <TableRow key={p.id}>
                          <TableCell className="max-w-md">
                            <p className="text-sm line-clamp-2">{p.content}</p>
                            {p.posted_tweet_id && (
                              <a
                                href={`https://x.com/i/status/${p.posted_tweet_id}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-xs text-blue-500 hover:underline"
                              >
                                view on X →
                              </a>
                            )}
                          </TableCell>
                          <TableCell>
                            {p.source_key ? (
                              <Badge variant="outline">{p.source_key}</Badge>
                            ) : (
                              '—'
                            )}
                          </TableCell>
                          <TableCell className="text-xs text-muted-foreground">
                            {p.posted_at ? new Date(p.posted_at).toLocaleString() : '—'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Source scores</CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Loading />
                ) : scores.length === 0 ? (
                  <Empty>No engagement data yet.</Empty>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Source</TableHead>
                        <TableHead className="text-right">Posts</TableHead>
                        <TableHead className="text-right">Engagement</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {scores.map((s) => (
                        <TableRow key={s.source_key}>
                          <TableCell className="text-sm font-medium truncate max-w-32">
                            {s.source_key}
                          </TableCell>
                          <TableCell className="text-right text-sm">{s.posts}</TableCell>
                          <TableCell className="text-right text-sm font-mono">
                            {s.sum_engagement.toLocaleString()}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
