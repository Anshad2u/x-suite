const STAGES = [
  { id: 'observe', label: 'Observe', desc: 'Scrape 10 feeds: 2 Reddit multireddits, 8 subreddits, 100 X accounts you follow.', cadence: 'Daily 09:00', file: 'feed_observer.py' },
  { id: 'understand', label: 'Understand', desc: 'Groq qwen3.8-27b scores each post: topic, relevance, decision (ignore/learn/save_watch/draft).', cadence: 'Per post', file: 'understand.py' },
  { id: 'remember', label: 'Remember', desc: 'Postgres: observed_posts, post_insights, accounts, topics, account_topics, decisions_log, engagement_profiles.', cadence: 'Per post', file: 'memory.py' },
  { id: 'decide', label: 'Decide', desc: 'Pick top candidate by relevance, generate original post via Groq (draft.py), engagement reply per account taste.', cadence: 'Per cycle', file: 'draft.py · engage_draft.py' },
  { id: 'approve', label: 'Approve', desc: 'Telegram bot sends draft with inline Approve / Reject. Poll loop handles callback, updates DB.', cadence: 'You tap', file: 'telegram_approval.py' },
  { id: 'act', label: 'Act', desc: 'Browser poster (Playwright + playwright_stealth) opens Chromium, warmup, types, clicks Post. Falls back to XPoster if Playwright missing.', cadence: 'On approve', file: 'poster_browser.py' },
  { id: 'learn', label: 'Learn', desc: 'Refresh account scores, build watchlist, send daily digest, your Correct updates insights, engagement profiles refreshed each fetch.', cadence: 'Continuous', file: 'daily_digest.py · engagement.py' }
]

export default function Pipeline() {
  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h3 className="text-[15px] font-semibold mb-1">End-to-end loop</h3>
        <p className="text-[12.5px] text-dim mb-6">Each cycle: observe feeds → understand with LLM → remember in Postgres → decide on top candidate → you approve on Telegram → browser posts to X → learn from outcomes.</p>

        <div className="relative">
          {STAGES.map((s, i) => (
            <div key={s.id} className="flex gap-4 mb-5 last:mb-0 relative">
              {i < STAGES.length - 1 && <div className="absolute left-[19px] top-10 bottom-[-20px] w-px bg-border"></div>}
              <div className="w-10 h-10 rounded-full bg-panel2 border-2 border-accent/40 flex items-center justify-center text-accent text-[12px] font-mono font-semibold shrink-0 z-10">{i + 1}</div>
              <div className="flex-1 bg-panel2 border border-border rounded-xl p-4">
                <div className="flex items-center justify-between gap-3 mb-1.5">
                  <div className="flex items-center gap-2">
                    <div className="text-[14px] font-semibold">{s.label}</div>
                    <span className="chip">{s.cadence}</span>
                  </div>
                  <code className="text-[10.5px] text-dim font-mono">{s.file}</code>
                </div>
                <div className="text-[12.5px] text-dim leading-relaxed">{s.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="card p-5">
          <h3 className="text-[13px] font-semibold mb-3">Scheduled tasks (Windows)</h3>
          <ul className="space-y-2 text-[12px]">
            <li className="flex items-center justify-between"><span className="text-dim">FollowerDashboard-Observe</span><span className="chip chip-ok">Daily 09:00</span></li>
            <li className="flex items-center justify-between"><span className="text-dim">FollowerDashboard-Digest</span><span className="chip chip-ok">Daily 18:00</span></li>
            <li className="flex items-center justify-between"><span className="text-dim">FollowerDashboard-Approval</span><span className="chip chip-warn">On logon (manual)</span></li>
            <li className="flex items-center justify-between"><span className="text-dim">FollowerDashboard-AutoPost</span><span className="chip chip-err">Disabled</span></li>
          </ul>
        </div>
        <div className="card p-5">
          <h3 className="text-[13px] font-semibold mb-3">Backoff / safety</h3>
          <ul className="space-y-2 text-[12px] text-dim">
            <li>· 1-2 posts/day, 3-5 replies/day cap</li>
            <li>· 226 lockout: 24h cooldown, vary wording</li>
            <li>· Approval required for every post</li>
            <li>· No duplicate cross-posts, no DMs</li>
            <li>· Playwright stealth + warmup before Post</li>
            <li>· Browser-driven bypass of TLS fingerprinting</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
