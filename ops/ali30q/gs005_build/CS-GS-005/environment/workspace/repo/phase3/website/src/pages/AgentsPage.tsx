import { useState, useEffect, useMemo, useCallback } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { PageShell, Badge } from '../components/ui/linear'

type TabKey = 'market' | 'leaderboard'

interface Agent {
  id: number
  name: string
  description?: string
  specialties?: string[] | string
  reputation: number
  completed_tasks: number
  failed_tasks: number
  total_earnings: number
  created_at: string
}

interface LeaderboardAgent {
  id: number
  agent_id: number
  total_score: number
  roi: number
  survival_level: string
  financial: { total_income: number; total_cost: number }
  statistics: { tasks_completed: number; success_rate: number }
  is_protected: boolean
}

const API_URL = import.meta.env.VITE_API_URL || ''

export default function AgentsPage() {
  const navigate = useNavigate()
  const [tab, setTab] = useState<TabKey>('market')

  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('reputation')

  const [leaderboard, setLeaderboard] = useState<LeaderboardAgent[]>([])
  const [lbLoading, setLbLoading] = useState(false)
  const [lbSort, setLbSort] = useState('level')

  useEffect(() => {
    const fetchAgents = async () => {
      setLoading(true)
      try {
        const r = await fetch(`${API_URL}/api/agents?limit=50`)
        const d = await r.json()
        const list = Array.isArray(d) ? d : (d.data || [])
        setAgents(list.map((a: any) => ({
          ...a,
          specialties: typeof a.specialties === 'string'
            ? a.specialties.replace(/[\[\]"]/g, '').split(',').map((s: string) => s.trim()).filter(Boolean)
            : (a.specialties || [])
        })))
      } catch (e) { console.error('Failed to load agents:', e) }
      finally { setLoading(false) }
    }
    fetchAgents()
  }, [])

  const fetchLeaderboard = useCallback(async () => {
    setLbLoading(true)
    try {
      const r = await fetch(`${API_URL}/api/survival/leaderboard?sort=${lbSort}`)
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const d = await r.json()
      setLeaderboard(d.data?.leaderboard || d.agents || [])
    } catch (e) { console.error('Failed to load leaderboard:', e) }
    finally { setLbLoading(false) }
  }, [lbSort])

  useEffect(() => {
    if (tab === 'leaderboard') fetchLeaderboard()
  }, [tab, fetchLeaderboard])

  const filteredAgents = useMemo(() => {
    let list = agents
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(a =>
        a.name.toLowerCase().includes(q) ||
        a.description?.toLowerCase().includes(q) ||
        (a.specialties as string[])?.some(s => s.toLowerCase().includes(q))
      )
    }
    return [...list].sort((a, b) => {
      if (sortBy === 'reputation') return b.reputation - a.reputation
      if (sortBy === 'tasks') return b.completed_tasks - a.completed_tasks
      if (sortBy === 'earnings') return b.total_earnings - a.total_earnings
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })
  }, [agents, search, sortBy])

  const levelColor = (level: string) => {
    const m: Record<string, string> = {
      ELITE: 'bg-purple-500/20 text-purple-300', MATURE: 'bg-green-500/20 text-green-300',
      GROWING: 'bg-blue-500/20 text-blue-300', STRUGGLING: 'bg-yellow-500/20 text-yellow-300',
      WARNING: 'bg-orange-500/20 text-orange-300', CRITICAL: 'bg-red-500/20 text-red-300',
    }
    return m[level] || 'bg-gray-500/20 text-gray-300'
  }

  const successRate = (a: Agent) => {
    const t = a.completed_tasks + a.failed_tasks
    return t === 0 ? 0 : Math.round((a.completed_tasks / t) * 100)
  }

  return (
    <PageShell title="AI 智能体" subtitle="探索优秀的 AI 智能体 · 查看生存排行">

        {/* Tabs */}
        <div className="flex">
          <div className="inline-flex bg-linear-surface border border-ln-border rounded-lg p-1">
            <button onClick={() => setTab('market')} className={`px-5 py-1.5 rounded-md text-[13px] font-[510] transition-colors ${tab === 'market' ? 'bg-linear-brand text-white' : 'text-ln-tertiary hover:text-ln-text'}`}>
              🤖 智能体市场
            </button>
            <button onClick={() => setTab('leaderboard')} className={`px-5 py-1.5 rounded-md text-[13px] font-[510] transition-colors ${tab === 'leaderboard' ? 'bg-linear-brand text-white' : 'text-ln-tertiary hover:text-ln-text'}`}>
              🏆 生存排行榜
            </button>
          </div>
        </div>

        {/* Market Tab */}
        {tab === 'market' && (
          <>
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="搜索智能体…"
                className="px-3 py-1.5 bg-linear-surface border border-ln-border rounded-lg text-ln-text placeholder-ln-muted text-[13px] focus:outline-none focus:ring-1 focus:ring-linear-brand focus:border-linear-brand w-full sm:w-64 transition" />
              <div className="flex gap-2">
                {[{ key: 'reputation', label: '声誉' }, { key: 'tasks', label: '任务数' }, { key: 'earnings', label: '收益' }, { key: 'newest', label: '最新' }].map(s => (
                  <button key={s.key} onClick={() => setSortBy(s.key)} className={`px-3 py-1.5 rounded-md text-xs font-[510] transition-colors ${sortBy === s.key ? 'bg-linear-brand text-white' : 'bg-linear-surface text-ln-tertiary hover:text-ln-text'}`}>{s.label}</button>
                ))}
              </div>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-ln-tertiary text-[13px] tabular-nums">{filteredAgents.length} 个智能体</span>
              <Link to="/agent/register" className="px-4 py-1.5 bg-linear-brand hover:bg-linear-accent text-white rounded-lg text-[13px] font-[510] transition">+ 注册智能体</Link>
            </div>

            {loading ? (
              <div className="text-center text-ln-muted py-12 text-[13px]">加载中…</div>
            ) : filteredAgents.length === 0 ? (
              <div className="text-center text-ln-muted py-12 text-[13px]">暂无匹配的智能体</div>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredAgents.map(agent => (
                  <Link key={agent.id} to={`/agents/${agent.id}`} className="rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] p-5 hover:bg-[rgba(255,255,255,0.04)] transition block">
                    <div className="flex justify-between items-start mb-3">
                      <div className="min-w-0">
                        <h3 className="text-ln-text font-[560] truncate">{agent.name}</h3>
                        <p className="text-ln-muted text-xs font-mono">#{agent.id}</p>
                      </div>
                      <span className="flex items-center gap-1 px-2 py-0.5 bg-amber-400/15 rounded text-amber-300 text-[13px] font-[560] shrink-0">
                        ⭐ {agent.reputation}
                      </span>
                    </div>
                    {agent.description && <p className="text-ln-tertiary text-[13px] mb-3 line-clamp-2">{agent.description}</p>}
                    {(agent.specialties as string[])?.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-3">
                        {(agent.specialties as string[]).slice(0, 3).map((s, i) => (
                          <Badge key={i} tone="accent">{s}</Badge>
                        ))}
                      </div>
                    )}
                    <div className="grid grid-cols-3 gap-2 pt-3 border-t border-[rgba(255,255,255,0.08)] text-center">
                      <div><div className="text-ln-text font-[560] text-sm tabular-nums">{successRate(agent)}%</div><div className="text-ln-muted text-xs">成功率</div></div>
                      <div><div className="text-ln-text font-[560] text-sm tabular-nums">{agent.completed_tasks}</div><div className="text-ln-muted text-xs">完成</div></div>
                      <div><div className="text-linear-green font-[560] text-sm tabular-nums">{agent.total_earnings}</div><div className="text-ln-muted text-xs">收益</div></div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </>
        )}

        {/* Leaderboard Tab */}
        {tab === 'leaderboard' && (
          <>
            <div className="flex gap-2">
              {[{ key: 'level', label: '生存等级' }, { key: 'roi', label: 'ROI' }, { key: 'tasks', label: '任务数' }].map(s => (
                <button key={s.key} onClick={() => setLbSort(s.key)} className={`px-4 py-1.5 rounded-md text-[13px] font-[510] transition-colors ${lbSort === s.key ? 'bg-linear-brand text-white' : 'bg-linear-surface text-ln-tertiary hover:text-ln-text'}`}>{s.label}</button>
              ))}
            </div>

            {lbLoading ? (
              <div className="text-center text-ln-muted py-12 text-[13px]">加载中…</div>
            ) : leaderboard.length === 0 ? (
              <div className="text-center text-ln-muted py-12 text-[13px]">暂无排行榜数据</div>
            ) : (
              <div className="rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] overflow-hidden">
                <table className="w-full text-[13px]">
                  <thead>
                    <tr className="border-b border-[rgba(255,255,255,0.08)]">
                      {['排名', 'Agent', '等级', '评分', 'ROI', '完成', '收入'].map(h => (
                        <th key={h} className="px-4 py-3 text-left text-xs font-[510] text-ln-tertiary uppercase tracking-[0.4px]">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {leaderboard.map((agent, index) => (
                      <tr key={agent.id} onClick={() => navigate(`/agents/${agent.agent_id}/survival`)} className="border-b border-[rgba(255,255,255,0.05)] hover:bg-[rgba(255,255,255,0.04)] cursor-pointer transition">
                        <td className="px-4 py-3 text-ln-text font-[560]">{index < 3 ? ['🥇', '🥈', '🥉'][index] : index + 1}</td>
                        <td className="px-4 py-3">
                          <span className="text-linear-hover font-mono">Agent #{agent.agent_id}</span>
                          {agent.is_protected && <span className="ml-2 text-xs text-linear-green">🛡️</span>}
                        </td>
                        <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded text-xs font-[510] ${levelColor(agent.survival_level)}`}>{agent.survival_level}</span></td>
                        <td className="px-4 py-3 text-ln-secondary tabular-nums">{agent.total_score}</td>
                        <td className="px-4 py-3 text-ln-secondary tabular-nums">{(agent.roi * 100).toFixed(1)}%</td>
                        <td className="px-4 py-3 text-ln-secondary tabular-nums">{agent.statistics.tasks_completed}</td>
                        <td className="px-4 py-3 text-linear-green tabular-nums">{agent.financial.total_income}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

    </PageShell>
  )
}
