export default function Approvals({ items, onAction }) {
  async function act(id, action) {
    const r = await fetch(`/api/approvals/${id}/${action}`, { method: 'POST', headers: { 'X-Auto-Post-Secret': import.meta.env.VITE_AUTO_POST_SECRET || '' } })
    const j = await r.json()
    if (j.result && j.result.startsWith('failed')) {
      alert('Failed: ' + j.result)
    }
    onAction()
  }

  return (
    <div className="space-y-4">
      <div className="card p-5">
        <div className="flex items-center justify-between mb-1">
          <h3 className="text-[15px] font-semibold">Pending drafts</h3>
          <span className="chip">{items.length}</span>
        </div>
        <p className="text-[12px] text-dim mb-4">Approve here or in Telegram. Rejected drafts are dropped. Approve opens Playwright + stealth, types the exact text, clicks Post.</p>

        <div className="space-y-3">
          {items.map(d => (
            <div key={d.id} className="bg-panel2 border border-border rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <span className="chip">#{d.id}</span>
                {d.topic && <span className="chip chip-accent">{d.topic}</span>}
                <span className="chip chip-warn">{d.status}</span>
                <span className="text-[10.5px] text-dim font-mono ml-auto">{d.created_at ? d.created_at.slice(0, 19) : ''}</span>
              </div>
              <div className="text-[13.5px] text-ink leading-relaxed whitespace-pre-wrap mb-3 pl-3 border-l-2 border-accent/40">{d.draft}</div>
              {d.source_link && (
                <div className="text-[11px] text-dim font-mono mb-3">
                  <a href={d.source_link} target="_blank" rel="noreferrer" className="text-accent hover:underline">source →</a>
                </div>
              )}
              {d.reason && <div className="text-[11.5px] text-dim mb-3"><span className="text-ink/70">Why:</span> {d.reason}</div>}
              <div className="flex gap-2">
                <button onClick={() => act(d.id, 'approve')} className="btn btn-primary">Approve & post</button>
                <button onClick={() => act(d.id, 'reject')} className="btn btn-ghost">Reject</button>
              </div>
            </div>
          ))}
          {items.length === 0 && <div className="text-center text-dim py-16 text-[13px]">No pending drafts. Observer will propose next.</div>}
        </div>
      </div>
    </div>
  )
}
