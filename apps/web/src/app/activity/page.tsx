import {
  IconCheck,
  IconX,
  IconStar,
  IconHash,
  IconSend,
  IconChartBar
} from '@tabler/icons-react';
import {
  getFullPendingDrafts,
  getWatchlist,
  getTopTopics,
  getMemorySummary,
  getPostedLog,
  getSourceScores
} from '@/lib/server/queries';
import { approveDraftAction, rejectDraftAction } from './actions';

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

export default async function ActivityPage() {
  const [approvals, watchlist, topics, summary, posted, scores] = await Promise.all([
    getFullPendingDrafts(),
    getWatchlist(50),
    getTopTopics(50),
    getMemorySummary(),
    getPostedLog(30),
    getSourceScores()
  ]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Activity</h1>
        <p className="mt-1 text-muted-foreground">
          Autopilot state: pending drafts, watched accounts, learned topics, and what has
          actually been posted.
        </p>
      </div>

      {/* Pending drafts */}
      <section className="rounded-xl border bg-card">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h2 className="flex items-center gap-2 font-semibold">
            <IconCheck className="h-5 w-5" /> Pending drafts
            {approvals.length > 0 && (
              <span className="rounded bg-primary px-2 py-0.5 text-xs text-primary-foreground">
                {approvals.length}
              </span>
            )}
          </h2>
        </div>
        <div className="p-5">
          {approvals.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              Nothing awaiting approval. The autopilot posts directly when approval mode is off.
            </p>
          ) : (
            <ul className="space-y-4">
              {approvals.map((a) => (
                <li key={a.id} className="rounded-lg border p-4">
                  <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
                    <span>#{a.id}</span>
                    {a.topic && <span className="rounded bg-muted px-1.5 py-0.5">#{a.topic}</span>}
                  </div>
                  <p className="text-sm">{a.draft}</p>
                  {a.reason && (
                    <p className="mt-1 text-xs text-muted-foreground">Why: {a.reason}</p>
                  )}
                  {a.source_link && (
                    <a
                      href={a.source_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-1 inline-block text-xs text-blue-500 hover:underline"
                    >
                      source →
                    </a>
                  )}
                  <div className="mt-3 flex gap-2">
                    <form action={approveDraftAction}>
                      <input type="hidden" name="id" value={a.id} />
                      <button
                        type="submit"
                        className="flex h-8 items-center gap-1 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground transition hover:bg-primary/90"
                      >
                        <IconCheck className="h-4 w-4" /> Approve
                      </button>
                    </form>
                    <form action={rejectDraftAction}>
                      <input type="hidden" name="id" value={a.id} />
                      <button
                        type="submit"
                        className="flex h-8 items-center gap-1 rounded-md border px-3 text-sm font-medium transition hover:bg-muted"
                      >
                        <IconX className="h-4 w-4" /> Reject
                      </button>
                    </form>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      {/* Watchlist + Insights */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="rounded-xl border bg-card">
          <div className="flex items-center gap-2 border-b px-5 py-4">
            <IconStar className="h-5 w-5" />
            <h2 className="font-semibold">Watched accounts</h2>
          </div>
          <div className="p-5">
            {watchlist.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">No accounts on the watchlist yet.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 font-medium">Handle</th>
                    <th className="py-2 font-medium">Topics</th>
                    <th className="py-2 text-right font-medium">Relevance</th>
                  </tr>
                </thead>
                <tbody>
                  {watchlist.map((w) => (
                    <tr key={w.username} className="border-b last:border-0">
                      <td className="py-2">
                        <a
                          href={`https://x.com/${w.username}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-medium text-blue-500 hover:underline"
                        >
                          @{w.username}
                        </a>
                      </td>
                      <td className="py-2 text-xs text-muted-foreground">
                        {Array.isArray(w.topics)
                          ? (w.topics as unknown[]).slice(0, 4).join(', ')
                          : '—'}
                      </td>
                      <td className="py-2 text-right font-mono text-xs">
                        {Number(w.relevance_score).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>

        <section className="rounded-xl border bg-card">
          <div className="flex items-center gap-2 border-b px-5 py-4">
            <IconHash className="h-5 w-5" />
            <h2 className="font-semibold">Top topics</h2>
          </div>
          <div className="p-5">
            {topics.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">No topics learned yet.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 font-medium">Topic</th>
                    <th className="py-2 text-right font-medium">Relevant</th>
                    <th className="py-2 text-right font-medium">Seen</th>
                  </tr>
                </thead>
                <tbody>
                  {topics.map((t) => (
                    <tr key={t.name} className="border-b last:border-0">
                      <td className="py-2 font-medium">{t.name}</td>
                      <td className="py-2 text-right">{t.relevant_count}</td>
                      <td className="py-2 text-right text-muted-foreground">{t.observed_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      </div>

      {/* Memory summary */}
      <section className="rounded-xl border bg-card">
        <div className="flex items-center gap-2 border-b px-5 py-4">
          <IconChartBar className="h-5 w-5" />
          <h2 className="font-semibold">Memory summary</h2>
        </div>
        <div className="grid grid-cols-2 gap-4 p-5 sm:grid-cols-3 lg:grid-cols-6">
          {Object.entries(summary).map(([k, v]) => (
            <div key={k}>
              <p className="text-xs capitalize text-muted-foreground">{k.replace(/_/g, ' ')}</p>
              <p className="text-xl font-bold">{Number(v).toLocaleString()}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Posted + source scores */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <section className="rounded-xl border bg-card lg:col-span-2">
          <div className="flex items-center gap-2 border-b px-5 py-4">
            <IconSend className="h-5 w-5" />
            <h2 className="font-semibold">Recently posted</h2>
          </div>
          <div className="p-5">
            {posted.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">Nothing posted yet.</p>
            ) : (
              <ul className="space-y-3">
                {posted.map((p) => (
                  <li key={p.id} className="border-b pb-3 last:border-0 last:pb-0">
                    <p className="line-clamp-2 text-sm">{p.content}</p>
                    <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                      <span>{p.source_key || p.group_name || '—'}</span>
                      <span>·</span>
                      <span>{fmtDate(p.posted_at)}</span>
                      {p.posted_tweet_id && (
                        <a
                          href={`https://x.com/i/status/${p.posted_tweet_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-500 hover:underline"
                        >
                          view →
                        </a>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        <section className="rounded-xl border bg-card">
          <div className="border-b px-5 py-4">
            <h2 className="font-semibold">Source scores</h2>
          </div>
          <div className="p-5">
            {scores.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">No engagement data yet.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2 font-medium">Source</th>
                    <th className="py-2 text-right font-medium">Posts</th>
                    <th className="py-2 text-right font-medium">Eng.</th>
                  </tr>
                </thead>
                <tbody>
                  {scores.map((s) => (
                    <tr key={s.source_key} className="border-b last:border-0">
                      <td className="py-2 text-xs font-medium">{s.source_key}</td>
                      <td className="py-2 text-right text-xs">{s.posts}</td>
                      <td className="py-2 text-right font-mono text-xs">{s.sum_engagement.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
