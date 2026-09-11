const TABLES = [
  { name: 'observed_posts', cols: 'id, platform, feed, author, title, body, link, posted_at, first_seen, last_seen, seen_count' },
  { name: 'post_insights', cols: 'id, topic, insight, is_new, relevance, confidence, follow_worthy, decision, analyzed_at' },
  { name: 'accounts', cols: 'username, platform, display_name, observed_posts, relevant_posts, relevance_score, confidence, topics, watchlisted' },
  { name: 'topics', cols: 'name, observed_count, relevant_count, last_seen' },
  { name: 'account_topics', cols: 'username, topic, weight, updated_at' },
  { name: 'engagement_profiles', cols: 'username, taste, style, topics, avg_reply_length, updated_at' },
  { name: 'decisions_log', cols: 'post_id, decision, reason, created_at' },
  { name: 'pending_drafts', cols: 'id, post_id, draft, reason, topic, source_link, status, created_at' }
]

export default function Memory({ summary }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <Stat label="Posts" value={summary.posts ?? 0} />
        <Stat label="Analyzed" value={summary.analyzed ?? 0} />
        <Stat label="Accounts" value={summary.accounts ?? 0} />
        <Stat label="Watchlist" value={summary.watchlist ?? 0} />
      </div>

      <div className="card p-6">
        <h3 className="text-[15px] font-semibold mb-3">Postgres tables</h3>
        <p className="text-[12px] text-dim mb-4">All memory lives in your Neon Postgres. Schema is idempotent (CREATE TABLE IF NOT EXISTS).</p>
        <div className="space-y-2.5">
          {TABLES.map(t => (
            <div key={t.name} className="bg-panel2 border border-border rounded-lg p-3.5">
              <div className="flex items-center gap-2 mb-1.5">
                <code className="text-[12.5px] text-ink font-mono font-medium">{t.name}</code>
              </div>
              <div className="text-[10.5px] text-dim font-mono leading-relaxed">{t.cols}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="card p-5">
      <div className="text-[10px] uppercase tracking-wider text-dim font-medium mb-2">{label}</div>
      <div className="stat-num">{value}</div>
    </div>
  )
}
