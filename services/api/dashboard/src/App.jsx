import { useEffect, useState } from 'react'
import Overview from './sections/Overview.jsx'
import Watchlist from './sections/Watchlist.jsx'
import Insights from './sections/Insights.jsx'
import Approvals from './sections/Approvals.jsx'
import Pipeline from './sections/Pipeline.jsx'
import Memory from './sections/Memory.jsx'
import Activity from './sections/Activity.jsx'

const NAV = [
  { id: 'overview', label: 'Overview' },
  { id: 'pipeline', label: 'Pipeline' },
  { id: 'watchlist', label: 'Watchlist' },
  { id: 'insights', label: 'Insights' },
  { id: 'memory', label: 'Memory' },
  { id: 'approvals', label: 'Approvals' },
  { id: 'activity', label: 'Activity' }
]

async function get(path) {
  const r = await fetch(path, { headers: { 'X-Auto-Post-Secret': import.meta.env.VITE_AUTO_POST_SECRET || '' } })
  if (!r.ok) throw new Error(path + ' ' + r.status)
  return r.json()
}

async function post(path, body) {
  return fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Auto-Post-Secret': import.meta.env.VITE_AUTO_POST_SECRET || '' }, body: JSON.stringify(body) })
}

export default function App() {
  const [view, setView] = useState('overview')
  const [summary, setSummary] = useState({})
  const [topTopics, setTopTopics] = useState([])
  const [watchlist, setWatchlist] = useState([])
  const [approvals, setApprovals] = useState([])
  const [recentActions, setRecentActions] = useState([])
  const [err, setErr] = useState(null)
  const [lastSync, setLastSync] = useState(null)

  async function refresh() {
    try {
      const [s, t, w, a, acts] = await Promise.all([
        get('/api/memory/summary'),
        get('/api/memory/topics?limit=8'),
        get('/api/watchlist?limit=40'),
        get('/api/approvals/pending?limit=20'),
        get('/api/memory/recent_actions?limit=20')
      ])
      setSummary(s)
      setTopTopics(t)
      setWatchlist(w)
      setApprovals(a)
      setRecentActions(acts)
      setLastSync(new Date())
      setErr(null)
    } catch (e) {
      setErr(e.message || String(e))
    }
  }

  useEffect(() => {
    refresh()
    const t = setInterval(refresh, 20000)
    return () => clearInterval(t)
  }, [])

  const currentLabel = NAV.find(n => n.id === view)?.label

  return (
    <div className="min-h-screen grid-bg">
      <div className="grid grid-cols-[260px_1fr] min-h-screen">
        <aside className="border-r border-border bg-panel/80 backdrop-blur-sm">
          <div className="p-6 border-b border-border">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-md bg-accent flex items-center justify-center text-bg font-mono font-bold text-sm">A</div>
              <div>
                <div className="text-[15px] font-semibold tracking-tight">Agent Pipeline</div>
                <div className="text-[11px] text-dim font-mono">v0.1 · personal</div>
              </div>
            </div>
          </div>

          <nav className="p-3 space-y-0.5">
            {NAV.map(n => (
              <button
                key={n.id}
                onClick={() => setView(n.id)}
                className={
                  'w-full text-left px-3 py-2 rounded-lg text-[13px] transition-colors flex items-center gap-3 ' +
                  (view === n.id
                    ? 'bg-panel2 text-ink border border-border'
                    : 'text-dim hover:text-ink hover:bg-panel2/50 border border-transparent')
                }
              >
                <span className={'w-1.5 h-1.5 rounded-full ' + (view === n.id ? 'bg-accent' : 'bg-border')}></span>
                {n.label}
              </button>
            ))}
          </nav>

          <div className="px-3 mt-4">
            <div className="card p-4">
              <div className="text-[10px] uppercase tracking-wider text-dim font-medium mb-2">Live</div>
              <div className="space-y-2 text-[12px]">
                <div className="flex justify-between"><span className="text-dim">Posts</span><span className="font-mono">{summary.posts ?? '—'}</span></div>
                <div className="flex justify-between"><span className="text-dim">Analyzed</span><span className="font-mono">{summary.analyzed ?? '—'}</span></div>
                <div className="flex justify-between"><span className="text-dim">Accounts</span><span className="font-mono">{summary.accounts ?? '—'}</span></div>
                <div className="flex justify-between"><span className="text-dim">Watchlist</span><span className="font-mono">{summary.watchlist ?? '—'}</span></div>
              </div>
            </div>
          </div>
        </aside>

        <main className="p-10 max-w-[1400px]">
          <header className="flex items-end justify-between mb-8">
            <div>
              <div className="text-[11px] font-mono text-dim uppercase tracking-widest mb-1">agent dashboard</div>
              <h1 className="text-[32px] font-semibold tracking-tight">{currentLabel}</h1>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-[11px] text-dim font-mono">
                {lastSync ? 'sync ' + lastSync.toLocaleTimeString() : 'syncing…'}
              </div>
              <button onClick={refresh} className="btn btn-outline">Refresh</button>
              <button onClick={() => runObserve()} className="btn btn-primary">Run cycle</button>
            </div>
          </header>

          {err && (
            <div className="card p-4 mb-6 border-err/40 bg-err/5 text-err text-[13px] font-mono">
              {err} — check Flask app on :5000
            </div>
          )}

          {view === 'overview' && <Overview summary={summary} topics={topTopics} watchlist={watchlist.slice(0,6)} actions={recentActions.slice(0,5)} />}
          {view === 'pipeline' && <Pipeline />}
          {view === 'watchlist' && <Watchlist items={watchlist} />}
          {view === 'insights' && <Insights topics={topTopics} summary={summary} />}
          {view === 'memory' && <Memory summary={summary} />}
          {view === 'approvals' && <Approvals items={approvals} onAction={refresh} />}
          {view === 'activity' && <Activity actions={recentActions} />}
        </main>
      </div>
    </div>
  )
}

async function runObserve() {
  try {
    const r = await post('/api/observe/run', { max_new: 10 })
    const j = await r.json()
    alert('cycle: analyzed ' + j.analyzed + ', watchlist ' + j.watchlist_size)
  } catch (e) {
    alert('cycle failed: ' + e.message)
  }
}
