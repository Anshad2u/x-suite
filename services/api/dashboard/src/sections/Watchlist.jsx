export default function Watchlist({ items }) {
  return (
    <div className="space-y-4">
      <div className="card p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-[15px] font-semibold">Curated accounts</h3>
            <p className="text-[12px] text-dim">Auto-grown from your feeds. Relevance = relevant_posts / observed_posts. Confidence grows with observations.</p>
          </div>
          <span className="chip">{items.length}</span>
        </div>

        <div className="space-y-2">
          {items.map(a => (
            <div key={a.username} className="flex items-center gap-4 bg-panel2 border border-border rounded-xl p-3.5">
              <div className="w-10 h-10 rounded-full bg-accent/20 border border-accent/30 flex items-center justify-center text-accent text-[13px] font-mono font-bold">{(a.username || '?')[0].toUpperCase()}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <div className="text-[14px] font-medium">@{a.username}</div>
                  <span className="chip">{a.platform}</span>
                  {a.watchlisted && <span className="chip chip-accent">★ watchlist</span>}
                </div>
                <div className="text-[11px] text-dim font-mono mt-0.5">{a.observed_posts} posts observed · {a.relevant_posts} relevant · last seen {a.last_seen ? a.last_seen.slice(0,10) : '—'}</div>
              </div>
              <div className="text-right">
                <div className="text-[20px] font-mono font-semibold text-ink">{Number(a.relevance_score).toFixed(2)}</div>
                <div className="text-[10px] text-dim font-mono">conf {Number(a.confidence).toFixed(2)}</div>
              </div>
              <div className="w-40 h-1.5 bg-bg rounded-full overflow-hidden">
                <div className="h-full bg-accent" style={{ width: Math.min(100, Number(a.relevance_score) * 100) + '%' }}></div>
              </div>
            </div>
          ))}
          {items.length === 0 && <div className="text-center text-dim py-12 text-[13px]">No accounts in watchlist. Run observe cycle to populate.</div>}
        </div>
      </div>
    </div>
  )
}
