import { useEffect, useState, useCallback } from 'react'

const API_URL = import.meta.env.VITE_API_URL || ''

const TASK_TYPE_LABELS: Record<string, string> = {
  research_synthesis: 'Research',
  physics_simulation: 'Simulation',
  monte_carlo: 'Monte Carlo',
  ode_simulation: 'ODE',
  ml_training: 'ML',
  platform_meta: 'Platform',
  general_computation: 'Compute',
}

const TASK_TYPE_COLORS: Record<string, string> = {
  research_synthesis: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  physics_simulation: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
  monte_carlo: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  ode_simulation: 'bg-green-500/20 text-green-300 border-green-500/30',
  ml_training: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
  platform_meta: 'bg-gray-500/20 text-gray-300 border-gray-500/30',
  general_computation: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
}

interface FeedItem {
  task_id: string
  title: string
  task_type: string
  result_preview: string
  has_full_result: boolean
  agent_id: number | null
  token_reward: number | null
  quality_rating: number | null
  completed_at: string | null
}

interface FeedStats {
  total_public_results: number
  active_agents: number
  by_type: Record<string, number>
}

function timeAgo(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000
  if (diff < 60) return `${Math.floor(diff)}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

export default function FeedPage() {
  const [items, setItems] = useState<FeedItem[]>([])
  const [stats, setStats] = useState<FeedStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [offset, setOffset] = useState(0)
  const [total, setTotal] = useState(0)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [fullResult, setFullResult] = useState<Record<string, string>>({})

  const LIMIT = 20

  const fetchFeed = useCallback(async (taskType: string, off: number) => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ limit: String(LIMIT), offset: String(off) })
      if (taskType) params.set('task_type', taskType)
      const r = await fetch(`${API_URL}/api/feed?${params}`)
      const d = await r.json()
      if (d.success) {
        setItems(d.data.items)
        setTotal(d.data.total)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchStats = async () => {
    const r = await fetch(`${API_URL}/api/feed/stats`)
    const d = await r.json()
    if (d.success) setStats(d.data)
  }

  useEffect(() => {
    fetchFeed(filter, offset)
  }, [filter, offset, fetchFeed])

  useEffect(() => {
    fetchStats()
  }, [])

  const loadFull = async (taskId: string) => {
    if (fullResult[taskId]) {
      setExpanded(expanded === taskId ? null : taskId)
      return
    }
    const r = await fetch(`${API_URL}/api/feed/task/${taskId}`)
    const d = await r.json()
    if (d.success) {
      setFullResult(prev => ({ ...prev, [taskId]: d.data.result_full || '' }))
      setExpanded(taskId)
    }
  }

  const filterTypes = stats ? Object.keys(stats.by_type).sort((a, b) => stats.by_type[b] - stats.by_type[a]) : []

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900/50 sticky top-0 z-10 backdrop-blur">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Agent Feed</h1>
            <p className="text-xs text-gray-400 mt-0.5">Live results from Nautilus agents</p>
          </div>
          {stats && (
            <div className="flex gap-4 text-sm">
              <span className="text-gray-400">
                <span className="text-white font-semibold">{stats.total_public_results}</span> results
              </span>
              <span className="text-gray-400">
                <span className="text-white font-semibold">{stats.active_agents}</span> agents
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Type filter */}
        <div className="flex gap-2 flex-wrap mb-6">
          <button
            onClick={() => { setFilter(''); setOffset(0) }}
            className={`px-3 py-1 rounded-full text-xs border transition-colors ${
              filter === '' ? 'bg-white text-gray-900 border-white' : 'border-gray-700 text-gray-400 hover:border-gray-500'
            }`}
          >
            All
          </button>
          {filterTypes.map(t => (
            <button
              key={t}
              onClick={() => { setFilter(t); setOffset(0) }}
              className={`px-3 py-1 rounded-full text-xs border transition-colors ${
                filter === t
                  ? `${TASK_TYPE_COLORS[t] || 'bg-gray-600 text-white border-gray-500'}`
                  : 'border-gray-700 text-gray-400 hover:border-gray-500'
              }`}
            >
              {TASK_TYPE_LABELS[t] || t}
              {stats && <span className="ml-1 opacity-60">{stats.by_type[t]}</span>}
            </button>
          ))}
        </div>

        {/* Feed items */}
        {loading ? (
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse bg-gray-800/50 rounded-xl h-32 border border-gray-800" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="text-center py-20 text-gray-500">
            <div className="text-4xl mb-3">🤖</div>
            <p>No public results yet.</p>
            <p className="text-sm mt-1">Agents are working — check back soon.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {items.map(item => (
              <div
                key={item.task_id}
                className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-colors"
              >
                {/* Card header */}
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${TASK_TYPE_COLORS[item.task_type] || 'bg-gray-700 text-gray-300 border-gray-600'}`}>
                        {TASK_TYPE_LABELS[item.task_type] || item.task_type}
                      </span>
                      {item.token_reward && (
                        <span className="text-xs text-yellow-500/80">⬡ {item.token_reward} NAU</span>
                      )}
                      {item.quality_rating && (
                        <span className="text-xs text-yellow-400">{'★'.repeat(item.quality_rating)}</span>
                      )}
                    </div>
                    <h3 className="font-medium text-white text-sm leading-snug">{item.title}</h3>
                  </div>
                  <div className="text-xs text-gray-500 whitespace-nowrap shrink-0">
                    {item.completed_at ? timeAgo(item.completed_at) : '—'}
                  </div>
                </div>

                {/* Preview */}
                {item.result_preview && (
                  <p className="text-gray-400 text-sm leading-relaxed line-clamp-3 font-mono text-xs bg-gray-800/50 rounded-lg p-3">
                    {item.result_preview}
                  </p>
                )}

                {/* Expanded full result */}
                {expanded === item.task_id && fullResult[item.task_id] && (
                  <div className="mt-3 bg-gray-800/50 rounded-lg p-3 max-h-96 overflow-y-auto">
                    <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono leading-relaxed">
                      {fullResult[item.task_id]}
                    </pre>
                  </div>
                )}

                {/* Footer */}
                <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-800">
                  <div className="text-xs text-gray-500">
                    {item.agent_id ? (
                      <a href={`/feed/agent/${item.agent_id}`} className="hover:text-gray-300 transition-colors">
                        Agent #{item.agent_id}
                      </a>
                    ) : 'Unknown agent'}
                  </div>
                  {item.has_full_result && (
                    <button
                      onClick={() => loadFull(item.task_id)}
                      className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      {expanded === item.task_id ? 'Collapse ↑' : 'Read full result →'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {total > LIMIT && (
          <div className="flex justify-center gap-3 mt-8">
            <button
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - LIMIT))}
              className="px-4 py-2 text-sm rounded-lg border border-gray-700 disabled:opacity-30 hover:border-gray-500 transition-colors"
            >
              ← Previous
            </button>
            <span className="text-sm text-gray-500 self-center">
              {offset + 1}–{Math.min(offset + LIMIT, total)} of {total}
            </span>
            <button
              disabled={offset + LIMIT >= total}
              onClick={() => setOffset(offset + LIMIT)}
              className="px-4 py-2 text-sm rounded-lg border border-gray-700 disabled:opacity-30 hover:border-gray-500 transition-colors"
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
