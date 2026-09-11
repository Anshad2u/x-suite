export default function Activity({ actions }) {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-[15px] font-semibold">Decision log</h3>
        <span className="text-[11px] text-dim font-mono">{actions.length} recent</span>
      </div>
      <p className="text-[12px] text-dim mb-4">Every LLM judgment on a post is recorded with reason. Use this to audit what the agent is doing and tune prompts.</p>

      <div className="space-y-2">
        {actions.map((a, i) => (
          <div key={i} className="flex items-start gap-3 bg-panel2 border border-border rounded-lg p-3.5">
            <div className={'chip ' + (a.decision === 'draft_post' || a.decision === 'draft_reply' ? 'chip-accent' : a.decision === 'learn' || a.decision === 'save_watch' ? 'chip-ok' : 'chip-warn')}>{a.decision}</div>
            <div className="flex-1 text-[12.5px] text-dim leading-relaxed">{a.reason || '—'}</div>
            <code className="text-[10px] text-dim font-mono whitespace-nowrap">{a.post_id?.slice(0, 28) || '—'}</code>
            <div className="text-[10px] text-dim font-mono whitespace-nowrap">{(a.created_at || '').slice(11, 19)}</div>
          </div>
        ))}
        {actions.length === 0 && <div className="text-center text-dim py-12 text-[13px]">No decisions logged yet.</div>}
      </div>
    </div>
  )
}
