import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'

interface Agent {
  id: number
  name: string
  description?: string
  specialties?: string[]
  reputation: number
  tasks_completed: number
  tasks_failed: number
  total_earned: number
  created_at: string
}

interface Task {
  id: number
  description: string
  status: string
  task_type: string
  reward: number
  created_at: string
}

interface NauHistoryItem {
  task_id: string
  task_type: string
  token_reward: number | null
  blockchain_tx_hash: string
  completed_at: string | null
}

interface CapabilityEntry {
  task_type: string
  success_count: number
  total_count: number
  success_rate: number
  level: 'expert' | 'proficient' | 'learning' | 'struggling'
}

interface CapabilityProfile {
  capabilities: CapabilityEntry[]
  suggested_focus: string[]
  total_tasks: number
}

interface Skill {
  id: number
  slug: string
  name: string
  description: string
  task_type: string
  price_usdc: number
  price_nau: number
  total_hires: number
  avg_rating: number
  success_rate: number
}

interface Tool {
  id: number
  slug: string
  name: string
  description: string
  category: string
  price_per_call: number
  total_calls: number
  http_method: string
}

const BASESCAN_TX_URL = 'https://basescan.org/tx/'
const NAU_HISTORY_DISPLAY_LIMIT = 10

const TASK_TYPE_LABELS: Record<string, string> = {
  curve_fitting: 'Curve Fitting',
  ode_simulation: 'ODE',
  pde_simulation: 'PDE',
  monte_carlo: 'Monte Carlo',
  statistical_analysis: 'Statistics',
  ml_training: 'ML Training',
  data_visualization: 'Visualization',
  physics_simulation: 'Physics',
  general_computation: 'Computation',
  jc_constitutive: 'JC Model',
  thmc_coupling: 'THMC',
  research_synthesis: 'Research',
}

export default function AgentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [agent, setAgent] = useState<Agent | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [nauBalance, setNauBalance] = useState<number | null>(null)
  const [nauHistory, setNauHistory] = useState<NauHistoryItem[]>([])
  const [nauHistoryExpanded, setNauHistoryExpanded] = useState(false)
  const [capabilityProfile, setCapabilityProfile] = useState<CapabilityProfile | null>(null)
  const [skills, setSkills] = useState<Skill[]>([])
  const [tools, setTools] = useState<Tool[]>([])

  useEffect(() => {
    if (!id) return
    const load = async () => {
      setLoading(true)
      try {
        const [agentRes, tasksRes] = await Promise.all([
          fetch(`/api/agents/${id}`),
          fetch(`/api/agents/${id}/tasks?limit=10`)
        ])
        if (agentRes.ok) {
          const d = await agentRes.json()
          setAgent(d.data || d)
        }
        if (tasksRes.ok) {
          const d = await tasksRes.json()
          setTasks(Array.isArray(d) ? d : (d.data || []))
        }
      } catch (error) {
        console.error('Failed to load agent:', error)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  useEffect(() => {
    if (!id) return
    fetch(`/api/agents/${id}/token-balance`)
      .then(r => r.json())
      .then(data => setNauBalance(data?.data?.nau_balance ?? null))
      .catch(() => {})
  }, [id])

  useEffect(() => {
    if (!id) return
    fetch(`/api/agents/${id}/nau-history`)
      .then(r => r.ok ? r.json() : [])
      .then((data: NauHistoryItem[]) => setNauHistory(Array.isArray(data) ? data : []))
      .catch(() => {})
  }, [id])

  useEffect(() => {
    if (!id) return
    fetch(`/api/agents/${id}/capability-profile`)
      .then(r => r.ok ? r.json() : null)
      .then((data: CapabilityProfile | null) => {
        if (data) setCapabilityProfile(data)
      })
      .catch(() => {})
  }, [id])

  useEffect(() => {
    if (!id) return
    fetch(`/api/skills/agent/${id}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.data?.skills) setSkills(d.data.skills) })
      .catch(() => {})
    fetch(`/api/tools/agent/${id}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.data?.tools) setTools(d.data.tools) })
      .catch(() => {})
  }, [id])

  const getSuccessRate = () => {
    if (!agent) return 0
    const total = agent.tasks_completed + agent.tasks_failed
    return total === 0 ? 0 : Math.round((agent.tasks_completed / total) * 100)
  }

  const getReputationLevel = () => {
    if (!agent) return 'Beginner'
    if (agent.reputation >= 200) return 'Master'
    if (agent.reputation >= 150) return 'Expert'
    if (agent.reputation >= 100) return 'Advanced'
    if (agent.reputation >= 50) return 'Intermediate'
    return 'Beginner'
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center py-12">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    )
  }

  if (!agent) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <p className="text-gray-500">Agent not found</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <button onClick={() => navigate('/agents')} className="mb-6 text-indigo-600 hover:text-indigo-700">← Back to Agents</button>

      <div className="bg-white rounded-lg shadow-sm p-8 mb-6">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{agent.name}</h1>
            <p className="text-gray-500">Agent #{agent.id}</p>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-indigo-600">{agent.reputation}</p>
            <p className="text-sm text-gray-500">{getReputationLevel()}</p>
          </div>
        </div>

        {agent.description && <p className="text-gray-700 mb-6">{agent.description}</p>}

        {(() => {
          // API returns specialties as a JSON string (e.g. '["a","b"]'), not an array.
          // Calling .map() on the string crashed the render → blank page. Parse defensively.
          const raw = agent.specialties
          const specs: string[] = Array.isArray(raw)
            ? raw
            : typeof raw === 'string'
              ? (() => { try { return JSON.parse(raw) } catch { return [] } })()
              : []
          return specs.length > 0 ? (
            <div className="flex flex-wrap gap-2 mb-6">
              {specs.map((s, i) => <span key={i} className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium">{s}</span>)}
            </div>
          ) : null
        })()}

        <div className="grid grid-cols-5 gap-4 mb-6">
          <div className="bg-gray-50 p-4 rounded-lg text-center">
            <p className="text-2xl font-bold text-gray-900">{getSuccessRate()}%</p>
            <p className="text-sm text-gray-500">成功率</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg text-center">
            <p className="text-2xl font-bold text-gray-900">{agent.tasks_completed}</p>
            <p className="text-sm text-gray-500">完成任务</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg text-center">
            <p className="text-2xl font-bold text-gray-900">{agent.tasks_failed}</p>
            <p className="text-sm text-gray-500">失败任务</p>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg text-center">
            <p className="text-2xl font-bold text-indigo-600">{agent.total_earned}</p>
            <p className="text-sm text-gray-500">总收益</p>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg text-center">
            {nauBalance !== null ? (
              <>
                <p className="text-2xl font-bold text-purple-600">{nauBalance.toFixed(2)}</p>
                <p className="text-sm text-gray-500">NAU 余额</p>
              </>
            ) : (
              <>
                <p className="text-2xl font-bold text-gray-300">—</p>
                <p className="text-sm text-gray-500">NAU 余额</p>
              </>
            )}
          </div>
        </div>

        <Link to={`/agents/${id}/survival`} className="inline-block px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">查看生存状态</Link>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-8 mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">NAU 获取历史</h2>
        {nauHistory.length === 0 ? (
          <p className="text-gray-500 text-center py-8">尚无链上记录</p>
        ) : (
          <>
            <div className="space-y-3">
              {(nauHistoryExpanded ? nauHistory : nauHistory.slice(0, NAU_HISTORY_DISPLAY_LIMIT)).map(item => (
                <div key={item.task_id} className="flex items-center justify-between border border-gray-100 rounded-lg p-4 hover:border-yellow-300 transition-colors">
                  <div className="flex items-center gap-3">
                    <span className="px-2 py-1 rounded text-xs font-medium bg-yellow-50 text-yellow-700 border border-yellow-200">
                      {TASK_TYPE_LABELS[item.task_type] ?? item.task_type}
                    </span>
                    <span className="text-lg font-bold text-yellow-500">
                      +{item.token_reward != null ? item.token_reward.toFixed(2) : '?'} NAU
                    </span>
                    {item.completed_at && (
                      <span className="text-xs text-gray-400">
                        {new Date(item.completed_at).toLocaleDateString('zh-CN')}
                      </span>
                    )}
                  </div>
                  <a
                    href={`${BASESCAN_TX_URL}${item.blockchain_tx_hash}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-indigo-500 hover:text-indigo-700 font-mono truncate max-w-[140px]"
                    title={item.blockchain_tx_hash}
                  >
                    {item.blockchain_tx_hash.slice(0, 8)}...{item.blockchain_tx_hash.slice(-6)}
                  </a>
                </div>
              ))}
            </div>
            {!nauHistoryExpanded && nauHistory.length > NAU_HISTORY_DISPLAY_LIMIT && (
              <button
                onClick={() => setNauHistoryExpanded(true)}
                className="mt-4 w-full text-center text-sm text-indigo-600 hover:text-indigo-700 py-2 border border-dashed border-indigo-200 rounded-lg"
              >
                查看更多（共 {nauHistory.length} 条）
              </button>
            )}
          </>
        )}
      </div>

      {/* Capability Profile Panel */}
      <div className="bg-white rounded-lg shadow-sm p-8 mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">能力统计</h2>
        {capabilityProfile === null ? (
          <p className="text-gray-500 text-center py-8">暂无任务记录</p>
        ) : capabilityProfile.capabilities.length === 0 ? (
          <p className="text-gray-500 text-center py-8">暂无任务记录</p>
        ) : (
          <>
            <div className="space-y-4 mb-6">
              {capabilityProfile.capabilities.map(cap => {
                const pct = Math.round(cap.success_rate * 100)
                let barColor = 'bg-red-500'
                let labelColor = 'text-red-600'
                if (cap.level === 'expert') {
                  barColor = 'bg-yellow-400'
                  labelColor = 'text-yellow-600'
                } else if (pct > 70) {
                  barColor = 'bg-green-500'
                  labelColor = 'text-green-600'
                } else if (pct > 40) {
                  barColor = 'bg-blue-500'
                  labelColor = 'text-blue-600'
                }
                const label = TASK_TYPE_LABELS[cap.task_type] ?? cap.task_type
                return (
                  <div key={cap.task_type}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700">{label}</span>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-semibold ${labelColor}`}>
                          {pct}%
                        </span>
                        <span className="text-xs text-gray-400">
                          {cap.success_count}/{cap.total_count}
                        </span>
                        {cap.level === 'expert' && (
                          <span className="px-1.5 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded font-medium">
                            专家
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2">
                      <div
                        className={`${barColor} h-2 rounded-full transition-all duration-500`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
            {capabilityProfile.suggested_focus.length > 0 && (
              <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-4">
                <p className="text-sm font-semibold text-indigo-700 mb-2">建议提升方向</p>
                <div className="flex flex-wrap gap-2">
                  {capabilityProfile.suggested_focus.map(focus => (
                    <span
                      key={focus}
                      className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm"
                    >
                      {TASK_TYPE_LABELS[focus] ?? focus}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Skills Marketplace Panel */}
      {skills.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-8 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Marketplace Skills</h2>
            <Link to="/skills" className="text-xs text-indigo-500 hover:underline">View all</Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {skills.slice(0, 4).map(s => (
              <div key={s.id} className="border border-gray-200 rounded-xl p-4 hover:border-indigo-300 transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <span className="text-xs px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-full font-medium">
                    {s.task_type.replace(/_/g,' ')}
                  </span>
                  <span className="text-xs text-gray-400">{s.total_hires} hires</span>
                </div>
                <p className="font-medium text-gray-900 text-sm mb-1">{s.name}</p>
                <p className="text-xs text-gray-500 line-clamp-2 mb-2">{s.description}</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-yellow-500">{'★'.repeat(Math.round(s.avg_rating))}{'☆'.repeat(5-Math.round(s.avg_rating))}</span>
                  <span className="text-sm font-bold text-gray-900">
                    {s.price_usdc > 0 ? `${s.price_usdc} USDC` : 'Free'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Registered Tools Panel */}
      {tools.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-8 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Registered APIs</h2>
            <Link to="/tools" className="text-xs text-indigo-500 hover:underline">View registry</Link>
          </div>
          <div className="space-y-2">
            {tools.slice(0, 3).map(t => (
              <div key={t.id} className="flex items-center justify-between border border-gray-100 rounded-lg p-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-mono bg-gray-100 px-1.5 py-0.5 rounded">{t.http_method}</span>
                    <span className="text-sm font-medium text-gray-800 truncate">{t.name}</span>
                  </div>
                  <p className="text-xs text-gray-500 truncate">{t.description}</p>
                </div>
                <div className="text-right ml-3 flex-shrink-0">
                  <p className="text-xs text-gray-400">{t.total_calls} calls</p>
                  <p className="text-xs font-medium text-gray-700">{t.price_per_call === 0 ? 'Free' : `${t.price_per_call} NAU`}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm p-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">最近任务</h2>
        {tasks.length === 0 ? (
          <p className="text-gray-500 text-center py-8">暂无任务记录</p>
        ) : (
          <div className="space-y-3">
            {tasks.map(task => (
              <Link key={task.id} to={`/tasks/${task.id}`} className="block border border-gray-200 rounded-lg p-4 hover:border-indigo-300 transition-colors">
                <div className="flex justify-between">
                  <div>
                    <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100">{task.status}</span>
                    <span className="ml-2 px-2 py-1 rounded text-xs font-medium bg-gray-100">{task.task_type}</span>
                    <p className="text-sm text-gray-900 mt-2">{task.description}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-indigo-600">{task.reward} NAU</p>
                    <p className="text-xs text-gray-400">{new Date(task.created_at).toLocaleDateString('zh-CN')}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
