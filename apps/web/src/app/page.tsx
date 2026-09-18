import Link from 'next/link';
import {
  IconUsers,
  IconFolder,
  IconUserSearch,
  IconMessage2,
  IconSend,
  IconClipboardCheck,
  IconHash,
  IconStar,
  IconArrowRight
} from '@tabler/icons-react';
import {
  getDashboardStats,
  getRecentPosted,
  getTopTopics,
  getPendingDrafts,
  getWatchlist
} from '@/lib/server/queries';

function fmtDate(d: Date | string | null): string {
  if (!d) return '—';
  const date = typeof d === 'string' ? new Date(d) : d;
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function StatCard({
  label,
  value,
  icon: Icon
}: {
  label: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">{label}</span>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <p className="mt-2 text-2xl font-bold">{value.toLocaleString()}</p>
    </div>
  );
}

export default async function DashboardPage() {
  const [stats, recent, topics, pending, watchlist] = await Promise.all([
    getDashboardStats(),
    getRecentPosted(5),
    getTopTopics(6),
    getPendingDrafts(5),
    getWatchlist(5)
  ]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="mt-1 text-muted-foreground">
          Live view of your X growth &amp; autopilot database.
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Followers" value={stats.followers} icon={IconUsers} />
        <StatCard label="Groups" value={stats.groups} icon={IconFolder} />
        <StatCard label="Observed accounts" value={stats.accounts} icon={IconUserSearch} />
        <StatCard label="Observed posts" value={stats.observedPosts} icon={IconMessage2} />
        <StatCard label="Posts published" value={stats.posted} icon={IconSend} />
        <StatCard label="Pending drafts" value={stats.pendingDrafts} icon={IconClipboardCheck} />
        <StatCard label="Topics learned" value={stats.topics} icon={IconHash} />
        <StatCard label="On watchlist" value={stats.watchlist} icon={IconStar} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Recent posted */}
        <section className="rounded-xl border bg-card">
          <div className="flex items-center justify-between border-b px-5 py-4">
            <h2 className="font-semibold">Recently posted</h2>
            <Link href="/activity" className="text-sm text-primary hover:underline">
              View all
            </Link>
          </div>
          <div className="p-5">
            {recent.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">Nothing posted yet.</p>
            ) : (
              <ul className="space-y-3">
                {recent.map((p) => (
                  <li key={p.id} className="border-b pb-3 last:border-0 last:pb-0">
                    <p className="line-clamp-2 text-sm">{p.content}</p>
                    <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{p.source_key || p.group_name || '—'}</span>
                      <span>·</span>
                      <span>{fmtDate(p.posted_at)}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        {/* Top topics */}
        <section className="rounded-xl border bg-card">
          <div className="border-b px-5 py-4">
            <h2 className="font-semibold">Top topics</h2>
          </div>
          <div className="p-5">
            {topics.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">No topics learned yet.</p>
            ) : (
              <ul className="space-y-2">
                {topics.map((t) => (
                  <li key={t.name} className="flex items-center justify-between text-sm">
                    <span className="font-medium">{t.name}</span>
                    <span className="text-muted-foreground">
                      {t.relevant_count} relevant / {t.observed_count} seen
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>

      {/* Pending drafts + watchlist */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="rounded-xl border bg-card">
          <div className="flex items-center justify-between border-b px-5 py-4">
            <h2 className="font-semibold">Pending drafts</h2>
            <Link href="/activity" className="text-sm text-primary hover:underline">
              Review
            </Link>
          </div>
          <div className="p-5">
            {pending.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">No drafts awaiting approval.</p>
            ) : (
              <ul className="space-y-3">
                {pending.map((d) => (
                  <li key={d.id} className="border-b pb-3 last:border-0 last:pb-0">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span>#{d.id}</span>
                      {d.topic && <span className="rounded bg-muted px-1.5 py-0.5">#{d.topic}</span>}
                    </div>
                    <p className="mt-1 line-clamp-2 text-sm">{d.draft}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        <section className="rounded-xl border bg-card">
          <div className="border-b px-5 py-4">
            <h2 className="font-semibold">Watchlist</h2>
          </div>
          <div className="p-5">
            {watchlist.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">No accounts on the watchlist yet.</p>
            ) : (
              <ul className="space-y-3">
                {watchlist.map((w) => (
                  <li key={w.username} className="flex items-center justify-between border-b pb-3 last:border-0 last:pb-0">
                    <div>
                      <a
                        href={`https://x.com/${w.username}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-medium text-blue-500 hover:underline"
                      >
                        @{w.username}
                      </a>
                      {w.display_name && (
                        <p className="text-xs text-muted-foreground">{w.display_name}</p>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground">
                      rel {w.relevance_score.toFixed(2)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>
      </div>

      {/* Single action: review the drafts the autopilot wrote */}
      <section className="flex flex-wrap gap-3">
        <Link
          href="/activity"
          className="flex items-center gap-2 rounded-lg border bg-card px-4 py-2 text-sm font-medium transition hover:bg-muted"
        >
          Review drafts <IconArrowRight className="h-4 w-4" />
        </Link>
      </section>
    </div>
  );
}
