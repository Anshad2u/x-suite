'use client';

import { useCallback, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import { IconTrash, IconPlus, IconRefresh, IconDownload } from '@tabler/icons-react';
import {
  createGroup,
  deleteGroup,
  getGroups,
  getScrapeConfig,
  scrapeGroup,
  updateScrapeConfig,
  type Group,
  type ScrapeConfig
} from '@/lib/api';

const EMPTY_CONFIG: ScrapeConfig = { keywords: '', since: '', max_tweets: 50 };

export default function GroupsPage() {
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newColor, setNewColor] = useState('#6366f1');

  const [selected, setSelected] = useState<string | null>(null);
  const [config, setConfig] = useState<ScrapeConfig>(EMPTY_CONFIG);
  const [savingConfig, setSavingConfig] = useState(false);
  const [scraping, setScraping] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setGroups(await getGroups());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load groups');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Load the selected group's scrape config.
  useEffect(() => {
    if (!selected) return;
    let cancelled = false;
    getScrapeConfig(selected)
      .then((cfg) => {
        if (!cancelled) setConfig({ ...EMPTY_CONFIG, ...cfg });
      })
      .catch(() => {
        if (!cancelled) setConfig(EMPTY_CONFIG);
      });
    return () => {
      cancelled = true;
    };
  }, [selected]);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setError(null);
    try {
      await createGroup(newName.trim(), newDesc.trim(), newColor);
      setNewName('');
      setNewDesc('');
      setNotice(`Created group "${newName.trim()}"`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Create failed');
    }
  };

  const handleDelete = async (name: string) => {
    setError(null);
    try {
      await deleteGroup(name);
      if (selected === name) setSelected(null);
      setNotice(`Deleted group "${name}"`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  };

  const handleSaveConfig = async () => {
    if (!selected) return;
    setSavingConfig(true);
    setError(null);
    try {
      await updateScrapeConfig(selected, {
        keywords: config.keywords ?? '',
        since: config.since ?? '',
        max_tweets: Number(config.max_tweets) || 50
      });
      setNotice(`Saved scrape config for "${selected}"`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSavingConfig(false);
    }
  };

  const handleScrape = async () => {
    if (!selected) return;
    setScraping(true);
    setError(null);
    setNotice(null);
    try {
      const res = await scrapeGroup(selected);
      setNotice(
        `Scrape finished for "${selected}": ${JSON.stringify(res).slice(0, 160)}`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scrape failed');
    } finally {
      setScraping(false);
    }
  };

  return (
    <div className="container mx-auto py-8 max-w-7xl">
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-2">Groups</h1>
          <p className="text-muted-foreground">
            Group followers by topic, then configure what to scrape from each group.
            The autopilot curates from these groups.
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
      {notice && (
        <Alert className="mb-6">
          <AlertDescription>{notice}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Create + list */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Create group</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap items-end gap-3">
              <div className="flex-1 min-w-40">
                <label className="text-sm text-muted-foreground">Name</label>
                <Input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g. Tech & AI"
                />
              </div>
              <div className="flex-1 min-w-40">
                <label className="text-sm text-muted-foreground">Description</label>
                <Input
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="optional"
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Color</label>
                <input
                  type="color"
                  value={newColor}
                  onChange={(e) => setNewColor(e.target.value)}
                  className="h-9 w-12 rounded border bg-transparent"
                />
              </div>
              <Button onClick={handleCreate} disabled={!newName.trim()}>
                <IconPlus className="w-4 h-4 mr-2" />
                Create
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Groups overview</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-2">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <Skeleton key={i} className="h-10 w-full" />
                  ))}
                </div>
              ) : groups.length === 0 ? (
                <p className="text-sm text-muted-foreground py-6 text-center">
                  No groups yet. Create one above.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Group</TableHead>
                      <TableHead className="text-right">Members</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {groups.map((g) => (
                      <TableRow
                        key={g.name}
                        className={selected === g.name ? 'bg-muted/50' : undefined}
                      >
                        <TableCell>
                          <button
                            className="flex items-center gap-2 text-left"
                            onClick={() => setSelected(g.name)}
                          >
                            <span
                              className="inline-block w-3 h-3 rounded-full"
                              style={{ backgroundColor: g.color }}
                            />
                            <span className="font-medium">{g.name}</span>
                            {g.description && (
                              <span className="text-xs text-muted-foreground">
                                {g.description}
                              </span>
                            )}
                          </button>
                        </TableCell>
                        <TableCell className="text-right">
                          <Badge variant="secondary">{g.count}</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setSelected(g.name)}
                            >
                              Configure
                            </Button>
                            <Button
                              size="icon"
                              variant="outline"
                              title="Delete group"
                              onClick={() => handleDelete(g.name)}
                            >
                              <IconTrash className="w-4 h-4" />
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
        </div>

        {/* Config panel */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Scrape config</CardTitle>
          </CardHeader>
          <CardContent>
            {!selected ? (
              <p className="text-sm text-muted-foreground">
                Select a group to edit its scrape configuration.
              </p>
            ) : (
              <div className="space-y-4">
                <div>
                  <span className="text-sm text-muted-foreground">Group</span>
                  <p className="font-medium">{selected}</p>
                </div>
                <Separator />
                <div>
                  <label className="text-sm text-muted-foreground">
                    Keywords (comma-separated)
                  </label>
                  <Input
                    value={config.keywords ?? ''}
                    onChange={(e) =>
                      setConfig((c) => ({ ...c, keywords: e.target.value }))
                    }
                    placeholder="AI, agents, SaaS"
                  />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">
                    Since (date)
                  </label>
                  <Input
                    type="date"
                    value={config.since ?? ''}
                    onChange={(e) => setConfig((c) => ({ ...c, since: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">
                    Tweets per account
                  </label>
                  <Input
                    type="number"
                    min={1}
                    value={config.max_tweets ?? 50}
                    onChange={(e) =>
                      setConfig((c) => ({ ...c, max_tweets: Number(e.target.value) }))
                    }
                  />
                </div>
                <div className="flex gap-2 pt-2">
                  <Button onClick={handleSaveConfig} disabled={savingConfig}>
                    {savingConfig ? 'Saving...' : 'Save config'}
                  </Button>
                  <Button variant="outline" onClick={handleScrape} disabled={scraping}>
                    <IconDownload className="w-4 h-4 mr-2" />
                    {scraping ? 'Scraping...' : 'Start scraping'}
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
