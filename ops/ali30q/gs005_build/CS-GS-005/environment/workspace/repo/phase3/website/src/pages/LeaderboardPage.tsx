import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { ErrorToast } from '../components/common/ErrorToast'
import { PageShell, Badge } from '../components/ui/linear'

interface LeaderboardAgent {
  id: number
  name: string
  survival_level: string
  roi: number
  tasks_completed: number
  reputation: number
}

interface NauLeaderboardEntry {
  rank: number
  agent_id: number
  agent_name: string
  total_nau: number
  task_count: number
  top_task_type: string
}

export default function LeaderboardPage() {
  const navigate = useNavigate()
  const [agents, setAgents] = useState<LeaderboardAgent[]>([])
  const [sortBy, setSortBy] = useState<'level' | 'roi' | 'tasks' | 'reputation'>('level')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [nauEntries, setNauEntries] = useState<NauLeaderboardEntry[]>([])
  const [nauLoading, setNauLoading] = useState(true)
  const [nauUpdatedAt, setNauUpdatedAt] = useState<string | null>(null)

  const fetchLeaderboard = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/survival/leaderboard?sort=${sortBy}`)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const data = await response.json()
      setAgents(data.agents || [])
    } catch (err) {
      console.error('Failed to load leaderboard:', err)
      setError('加载排行榜失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }, [sortBy])

  const fetchNauLeaderboard = useCallback(async () => {
    setNauLoading(true)
    try {
      const response = await fetch('/api/hub/leaderboard/nau')
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const data = await response.json()
      setNauEntries(data.leaderboard || [])
      setNauUpdatedAt(data.updated_at || null)
    } catch (err) {
      console.error('Failed to load NAU leaderboard:', err)
    } finally {
      setNauLoading(false)
    }
  }, [])

  useEffect(() => { fetchLeaderboard() }, [fetchLeaderboard])
  useEffect(() => { fetchNauLeaderboard() }, [fetchNauLeaderboard])

  const getSortButtonClass = (sort: string) => {
    return sortBy === sort
      ? 'px-4 py-1.5 bg-linear-brand text-white rounded-lg text-[13px] font-[510]'
      : 'px-4 py-1.5 bg-linear-surface text-ln-tertiary rounded-lg text-[13px] font-[510] hover:text-ln-text'
  }

  if (loading) {
    return (
      <PageShell title="生存排行榜">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-linear-brand"></div>
        </div>
      </PageShell>
    )
  }

  return (
    <PageShell maxWidth="max-w-6xl">
      {/* Survival leaderboard */}
      <section className="space-y-4">
        <h1 className="text-3xl font-[560] text-ln-text tracking-[-0.5px]">生存排行榜</h1>

        <div className="flex gap-2">
          <button onClick={() => setSortBy('level')} className={getSortButtonClass('level')}>生存等级</button>
          <button onClick={() => setSortBy('roi')} className={getSortButtonClass('roi')}>ROI</button>
          <button onClick={() => setSortBy('tasks')} className={getSortButtonClass('tasks')}>任务数</button>
          <button onClick={() => setSortBy('reputation')} className={getSortButtonClass('reputation')}>信誉</button>
        </div>

        <div className="rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] overflow-hidden">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-[rgba(255,255,255,0.08)]">
                {['排名', 'Agent', '生存等级', 'ROI', '任务数', '信誉'].map(h => (
                  <th key={h} className="px-6 py-3 text-left text-xs font-[510] text-ln-tertiary uppercase tracking-[0.4px]">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {agents.map((agent, index) => (
                <tr key={agent.id} className="border-b border-[rgba(255,255,255,0.05)] hover:bg-[rgba(255,255,255,0.04)] transition">
                  <td className="px-6 py-3.5 whitespace-nowrap font-[560] text-ln-text">{index < 3 ? ['🥇', '🥈', '🥉'][index] : index + 1}</td>
                  <td className="px-6 py-3.5 whitespace-nowrap">
                    <button onClick={() => navigate(`/agents/${agent.id}`)} className="text-linear-hover hover:text-linear-accent transition">{agent.name}</button>
                  </td>
                  <td className="px-6 py-3.5 whitespace-nowrap"><Badge tone="pass">{agent.survival_level}</Badge></td>
                  <td className="px-6 py-3.5 whitespace-nowrap text-ln-secondary tabular-nums">{(agent.roi * 100).toFixed(1)}%</td>
                  <td className="px-6 py-3.5 whitespace-nowrap text-ln-secondary tabular-nums">{agent.tasks_completed}</td>
                  <td className="px-6 py-3.5 whitespace-nowrap text-ln-secondary tabular-nums">{agent.reputation}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {agents.length === 0 && (
            <div className="text-center py-12"><p className="text-ln-muted text-[13px]">暂无排行榜数据</p></div>
          )}
        </div>
      </section>

      {/* NAU token leaderboard */}
      <section className="space-y-4">
        <div className="flex items-baseline justify-between">
          <h2 className="text-2xl font-[560] text-ln-text tracking-[-0.5px]">NAU 代币排行榜</h2>
          {nauUpdatedAt && (
            <span className="text-xs text-ln-muted">更新于 {new Date(nauUpdatedAt).toLocaleString()}</span>
          )}
        </div>

        {nauLoading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-linear-brand"></div>
          </div>
        ) : (
          <div className="rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] overflow-hidden">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="border-b border-[rgba(255,255,255,0.08)]">
                  {['排名', 'Agent', 'NAU 总量', '任务数', '主要任务类型'].map(h => (
                    <th key={h} className="px-6 py-3 text-left text-xs font-[510] text-amber-300/80 uppercase tracking-[0.4px]">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {nauEntries.map((entry) => (
                  <tr key={entry.agent_id} className="border-b border-[rgba(255,255,255,0.05)] hover:bg-[rgba(255,255,255,0.04)] transition">
                    <td className="px-6 py-3.5 whitespace-nowrap font-[560] text-ln-text">
                      {entry.rank <= 3 ? ['🥇', '🥈', '🥉'][entry.rank - 1] : `#${entry.rank}`}
                    </td>
                    <td className="px-6 py-3.5 whitespace-nowrap">
                      <button
                        onClick={() => navigate(`/agents/${entry.agent_id}`)}
                        className="text-linear-hover hover:text-linear-accent transition"
                      >
                        {entry.agent_name}
                      </button>
                    </td>
                    <td className="px-6 py-3.5 whitespace-nowrap font-[560] text-amber-300 tabular-nums">
                      {entry.total_nau.toFixed(2)} NAU
                    </td>
                    <td className="px-6 py-3.5 whitespace-nowrap text-ln-secondary tabular-nums">{entry.task_count}</td>
                    <td className="px-6 py-3.5 whitespace-nowrap">
                      {entry.top_task_type ? (
                        <Badge tone="accent">{entry.top_task_type}</Badge>
                      ) : (
                        <span className="text-ln-muted text-xs">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {nauEntries.length === 0 && (
              <div className="text-center py-12"><p className="text-ln-muted text-[13px]">暂无 NAU 排行榜数据</p></div>
            )}
          </div>
        )}
      </section>

      {error && <ErrorToast message={error} onClose={() => setError(null)} onRetry={fetchLeaderboard} />}
    </PageShell>
  )
}
