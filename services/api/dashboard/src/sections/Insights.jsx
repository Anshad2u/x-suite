export default function Insights({ topics, summary }) {
  const total = (topics || []).reduce((s, t) => s + Number(t.observed_count || 0), 0)
  const relevant = (topics || []).reduce((s, t) => s + Number(t.relevant_count || 0), 0)
  const ratio = total ? Math.round((relevant / total) * 100) : 0
  const colors = ['bg-accent', 'bg-ok', 'bg-warn', 'bg-err']

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        <div className="card p-5">
          <div className="text-[10px] uppercase tracking-wider text-dim font-medium mb-2">Topics discovered</div>
          <div className="stat-num">{topics.length}</div>
        </div>
        <div className="card p-5">
          <div className="text-[10px] uppercase tracking-wider text-dim font-medium mb-2">Total observations</div>
          <div className="stat-num">{total}</div>
        </div>
        <div className="card p-5">
          <div className="text-[10px] uppercase tracking-wider text-dim font-medium mb-2">Relevance ratio</div>
          <div className="stat-num">{ratio}<span className="text-[20px] text-dim ml-1">%</span></div>
        </div>
      </div>

      <div className="card p-6">
        <h3 className="text-[15px] font-semibold mb-4">Topic distribution</h3>
        <div className="space-y-2.5">
          {topics.map((t, i) => (
            <div key={t.name} className="flex items-center gap-3">
              <div className="text-[13px] text-ink w-44 truncate">{t.name}</div>
              <div className="flex-1 h-6 bg-panel2 rounded-md overflow-hidden flex">
                <div className={colors[i % colors.length] + ' opacity-90'} style={{ width: Math.min(100, (t.relevant_count / Math.max(1, t.observed_count)) * 100) + '%' }} title="relevant"></div>
                <div className="bg-border/60" style={{ width: Math.max(0, 100 - (t.relevant_count / Math.max(1, t.observed_count)) * 100) + '%' }} title="seen-only"></div>
              </div>
              <div className="text-[11px] text-dim font-mono w-20 text-right">{t.relevant_count}/{t.observed_count}</div>
            </div>
          ))}
          {topics.length === 0 && <div className="text-center text-dim py-12 text-[13px]">No topics yet.</div>}
        </div>
      </div>

      <div className="card p-6">
        <h3 className="text-[15px] font-semibold mb-3">How insights are produced</h3>
        <div className="space-y-2 text-[12.5px] text-dim">
          <p>· Each observed post is scored by Groq <code className="text-ink font-mono">qwen/qwen3.8-27b</code> on topic, relevance (0-1), insight text, decision (ignore/learn/save_watch/draft_post/draft_reply).</p>
          <p>· Decision defaults to <span className="text-ink">ignore</span>; only high-relevance + new items surface as drafts.</p>
          <p>· Your Telegram <span className="text-ink">Correct</span> on summary updates <code className="font-mono">post_insights</code> and <code className="font-mono">accounts</code> — the agent learns from feedback.</p>
        </div>
      </div>
    </div>
  )
}
