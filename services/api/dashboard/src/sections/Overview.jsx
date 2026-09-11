export default function Overview({ summary, topics, watchlist, actions }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Stat label="Observed posts" value={summary.posts ?? 0} hint="feeds scraped" />
        <Stat label="Analyzed" value={summary.analyzed ?? 0} hint="LLM-judged" />
        <Stat label="Accounts" value={summary.accounts ?? 0} hint="tracked" />
        <Stat label="Watchlist" value={summary.watchlist ?? 0} hint="curated" hint2="engagement profiles: 30" />
      </div>

      <div className="grid grid-cols-[1.4fr_1fr] gap-6">
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[15px] font-semibold">Top topics</h3>
            <span className="text-[11px] text-dim font-mono">{topics.length}</span>
          </div>
          <div className="space-y-2">
            {(topics || []).map(t => (
              <div key={t.name} className="flex items-center gap-3">
                <div className="text-[13px] text-ink flex-1 truncate">{t.name}</div>
                <div className="text-[11px] text-dim font-mono w-16 text-right">{t.relevant_count}/{t.observed_count}</div>
                <div className="w-32 h-1.5 bg-panel2 rounded-full overflow-hidden">
                  <div className="h-full bg-accent" style={{ width: Math.min(100, (t.relevant_count / Math.max(1, t.observed_count)) * 100) + '%' }}></div>
                </div>
              </div>
            ))}
            {(!topics || topics.length === 0) && <div className="text-[13px] text-dim">No topics yet. Run a cycle.</div>}
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[15px] font-semibold">Recent activity</h3>
            <span className="chip">{actions.length} decisions</span>
          </div>
          <div className="space-y-2.5">
            {(actions || []).map((a, i) => (
              <div key={i} className="flex items-start gap-3 text-[12.5px]">
                <div className={'mt-0.5 chip ' + (a.decision === 'draft_post' || a.decision === 'draft_reply' ? 'chip-accent' : a.decision === 'learn' || a.decision === 'save_watch' ? 'chip-ok' : 'chip-warn')}>{a.decision}</div>
                <div className="text-dim leading-snug flex-1">{(a.reason || '').slice(0, 120)}</div>
                <div className="text-[10px] text-dim font-mono whitespace-nowrap">{(a.created_at || '').slice(11, 16)}</div>
              </div>
            ))}
            {(!actions || actions.length === 0) && <div className="text-[13px] text-dim">Idle.</div>}
          </div>
        </div>
      </div>

      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[15px] font-semibold">Top of watchlist</h3>
          <span className="text-[11px] text-dim">accounts worth following</span>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {(watchlist || []).map(a => (
            <div key={a.username} className="bg-panel2 border border-border rounded-xl p-3.5">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-accent/20 border border-accent/30 flex items-center justify-center text-accent text-[12px] font-mono font-bold">{(a.username || '?')[0].toUpperCase()}</div>
                <div className="flex-1 min-w-0">
                  <div className="text-[13.5px] font-medium truncate">@{a.username}</div>
                  <div className="text-[11px] text-dim font-mono">{a.platform} · score {Number(a.relevance_score).toFixed(2)} · conf {Number(a.confidence).toFixed(2)}</div>
                </div>
                <div className="text-[10px] text-dim font-mono whitespace-nowrap">{a.relevant_posts}/{a.observed_posts}</div>
              </div>
            </div>
          ))}
          {(!watchlist || watchlist.length === 0) && <div className="col-span-2 text-[13px] text-dim text-center py-8">No watchlist yet.</div>}
        </div>
      </div>
    </div>
  )
}

function Stat({ label, value, hint, hint2 }) {
  return (
    <div className="card p-5">
      <div className="text-[10px] uppercase tracking-wider text-dim font-medium mb-2">{label}</div>
      <div className="stat-num">{value}</div>
      <div className="text-[11px] text-dim mt-2 font-mono">{hint}{hint2 ? ' · ' + hint2 : ''}</div>
    </div>
  )
}
