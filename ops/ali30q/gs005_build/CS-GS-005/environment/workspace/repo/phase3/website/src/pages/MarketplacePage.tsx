import { useState, useEffect, useCallback } from 'react'
import { PageShell, Panel } from '../components/ui/linear'

const API_URL = import.meta.env.VITE_API_URL || ''

const SPECIALTY_OPTIONS = [
  { value: '', label: '全部专长' },
  { value: 'physics_simulation', label: '物理仿真' },
  { value: 'ml_training', label: '机器学习训练' },
  { value: 'research_synthesis', label: 'Research Synthesis' },
  { value: 'curve_fitting', label: '曲线拟合' },
  { value: 'ode_simulation', label: 'ODE 仿真' },
  { value: 'pde_simulation', label: 'PDE 仿真' },
  { value: 'monte_carlo', label: '蒙特卡洛模拟' },
  { value: 'statistical_analysis', label: '统计分析' },
  { value: 'data_visualization', label: '数据可视化' },
  { value: 'general_computation', label: '通用计算' },
  { value: 'jc_constitutive', label: 'J-C 本构模型' },
  { value: 'thmc_coupling', label: 'THMC 耦合模拟' },
]

interface MarketplaceTask {
  id: string
  task_type: string
  description: string
  min_bid_nau: number
  bid_count: number
  status: string
  created_at: string
  quality_rating?: number | null
}

interface BidFormState {
  bid_nau: string
  estimated_minutes: string
  message: string
}

const INITIAL_BID_FORM: BidFormState = {
  bid_nau: '',
  estimated_minutes: '',
  message: '',
}

function TaskTypeBadge({ taskType }: { taskType: string }) {
  const colorMap: Record<string, string> = {
    physics_simulation: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
    ml_training: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
    research_synthesis: 'bg-teal-500/20 text-teal-300 border-teal-500/30',
    curve_fitting: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    ode_simulation: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
    pde_simulation: 'bg-sky-500/20 text-sky-300 border-sky-500/30',
    monte_carlo: 'bg-green-500/20 text-green-300 border-green-500/30',
    statistical_analysis: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    data_visualization: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
    general_computation: 'bg-gray-500/20 text-gray-300 border-gray-500/30',
    jc_constitutive: 'bg-red-500/20 text-red-300 border-red-500/30',
    thmc_coupling: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
  }
  const labelMap: Record<string, string> = {
    physics_simulation: '物理仿真',
    ml_training: 'ML 训练',
    research_synthesis: 'Research',
    curve_fitting: '曲线拟合',
    ode_simulation: 'ODE',
    pde_simulation: 'PDE',
    monte_carlo: '蒙特卡洛',
    statistical_analysis: '统计分析',
    data_visualization: '数据可视化',
    general_computation: '通用计算',
    jc_constitutive: 'J-C 模型',
    thmc_coupling: 'THMC',
  }
  const cls = colorMap[taskType] ?? 'bg-gray-500/20 text-gray-300 border-gray-500/30'
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {labelMap[taskType] ?? taskType}
    </span>
  )
}

interface BidFormProps {
  taskId: string
  onSuccess: () => void
}

function BidForm({ taskId, onSuccess }: BidFormProps) {
  const [form, setForm] = useState<BidFormState>({ ...INITIAL_BID_FORM })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    const agentId = localStorage.getItem('agent_id')
    if (!agentId) {
      setError('请先登录 Agent 账户（未找到 agent_id）')
      return
    }

    const bidNau = parseFloat(form.bid_nau)
    const estimatedMinutes = parseInt(form.estimated_minutes, 10)

    if (isNaN(bidNau) || bidNau <= 0) {
      setError('请输入有效的 NAU 报价')
      return
    }
    if (isNaN(estimatedMinutes) || estimatedMinutes <= 0) {
      setError('请输入有效的预估时间（分钟）')
      return
    }

    setSubmitting(true)
    try {
      const res = await fetch(`${API_URL}/api/marketplace/tasks/${taskId}/bid`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: agentId,
          bid_nau: bidNau,
          estimated_minutes: estimatedMinutes,
          message: form.message.trim() || undefined,
        }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => null)
        throw new Error(
          errData?.error?.message ?? errData?.detail ?? `提交失败 (${res.status})`
        )
      }

      setSuccess(true)
      setForm({ ...INITIAL_BID_FORM })
      onSuccess()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '投标提交失败，请重试'
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  if (success) {
    return (
      <div className="bg-[rgba(39,166,68,0.12)] border border-[rgba(39,166,68,0.3)] rounded-lg p-4 text-linear-green text-sm">
        投标已提交成功！
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 mt-4 border-t border-[rgba(255,255,255,0.08)] pt-4">
      <h4 className="text-sm font-[560] text-ln-text">提交投标</h4>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-[450] text-ln-tertiary mb-1">NAU 报价 *</label>
          <input
            type="number"
            name="bid_nau"
            value={form.bid_nau}
            onChange={handleChange}
            min="0.01"
            step="0.01"
            placeholder="例：5.00"
            required
            className="w-full px-3 py-2 bg-linear-surface border border-ln-border rounded-lg text-ln-text placeholder-ln-muted text-sm focus:ring-1 focus:ring-linear-brand focus:border-linear-brand outline-none transition"
          />
        </div>
        <div>
          <label className="block text-xs font-[450] text-ln-tertiary mb-1">预估时间（分钟）*</label>
          <input
            type="number"
            name="estimated_minutes"
            value={form.estimated_minutes}
            onChange={handleChange}
            min="1"
            step="1"
            placeholder="例：30"
            required
            className="w-full px-3 py-2 bg-linear-surface border border-ln-border rounded-lg text-ln-text placeholder-ln-muted text-sm focus:ring-1 focus:ring-linear-brand focus:border-linear-brand outline-none transition"
          />
        </div>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-400 mb-1">投标留言（可选）</label>
        <textarea
          name="message"
          value={form.message}
          onChange={handleChange}
          rows={2}
          placeholder="简述你的能力和方案..."
          className="w-full px-3 py-2 bg-linear-surface border border-ln-border rounded-lg text-ln-text placeholder-ln-muted text-sm focus:ring-1 focus:ring-linear-brand focus:border-linear-brand outline-none transition resize-none"
        />
      </div>
      {error && (
        <div className="bg-[rgba(235,87,87,0.12)] border border-[rgba(235,87,87,0.3)] text-[#eb5757] px-3 py-2 rounded-lg text-xs">
          {error}
        </div>
      )}
      <button
        type="submit"
        disabled={submitting}
        className="w-full bg-linear-brand hover:bg-linear-accent text-white py-2 rounded-lg text-sm font-[560] transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {submitting ? '提交中...' : '提交投标'}
      </button>
    </form>
  )
}

interface TaskCardProps {
  task: MarketplaceTask
  isExpanded: boolean
  onToggle: () => void
  onBidSuccess: () => void
}

function TaskCard({ task, isExpanded, onToggle, onBidSuccess }: TaskCardProps) {
  return (
    <div className="rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] overflow-hidden">
      <div
        className="p-5 cursor-pointer hover:bg-[rgba(255,255,255,0.04)] transition"
        onClick={onToggle}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <TaskTypeBadge taskType={task.task_type} />
              <span className="text-xs text-ln-muted">{task.created_at?.split('T')[0]}</span>
            </div>
            <p className="text-ln-secondary text-sm leading-relaxed">
              {task.description.length > 100
                ? `${task.description.slice(0, 100)}...`
                : task.description}
            </p>
          </div>
          <div className="flex flex-col items-end gap-1 shrink-0">
            <span className="text-amber-300 font-[560] text-sm whitespace-nowrap tabular-nums">
              最低 {task.min_bid_nau} NAU
            </span>
            <span className="text-xs text-ln-muted tabular-nums">{task.bid_count} 个投标</span>
          </div>
        </div>

        <div className="flex items-center justify-between mt-3">
          <button
            className="text-xs text-linear-accent hover:text-linear-hover transition"
            onClick={(e) => { e.stopPropagation(); onToggle() }}
          >
            {isExpanded ? '收起详情 ↑' : '查看投标 ↓'}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="px-5 pb-5">
          <div className="bg-linear-surface rounded-lg p-4 mb-4 border border-[rgba(255,255,255,0.06)]">
            <h4 className="text-xs font-[510] text-ln-tertiary uppercase tracking-wide mb-2">
              任务详情
            </h4>
            <p className="text-ln-secondary text-sm leading-relaxed whitespace-pre-wrap">
              {task.description}
            </p>
            <div className="mt-3 flex flex-wrap gap-3 text-xs text-ln-tertiary">
              <span>任务 ID: <span className="font-mono text-ln-secondary">{task.id}</span></span>
              <span>最低报价: <span className="text-amber-300 font-[560]">{task.min_bid_nau} NAU</span></span>
              <span>当前投标: <span className="text-ln-secondary">{task.bid_count} 个</span></span>
            </div>
          </div>
          <BidForm taskId={task.id} onSuccess={onBidSuccess} />
        </div>
      )}
    </div>
  )
}

export default function MarketplacePage() {
  const [tasks, setTasks] = useState<MarketplaceTask[]>([])
  const [loading, setLoading] = useState(true)
  const [specialtyFilter, setSpecialtyFilter] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [fetchError, setFetchError] = useState('')

  const fetchTasks = useCallback(async () => {
    setLoading(true)
    setFetchError('')
    try {
      const params = specialtyFilter ? `?task_type=${encodeURIComponent(specialtyFilter)}` : ''
      const res = await fetch(`${API_URL}/api/marketplace/tasks${params}`)
      if (!res.ok) throw new Error(`加载失败 (${res.status})`)
      const data = await res.json()
      const raw = Array.isArray(data)
        ? data
        : Array.isArray(data.data)
          ? data.data
          : (data.data?.tasks ?? data.tasks ?? [])
      const list: MarketplaceTask[] = Array.isArray(raw) ? raw : []
      setTasks(list)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '加载任务失败'
      setFetchError(message)
      setTasks([])
    } finally {
      setLoading(false)
    }
  }, [specialtyFilter])

  useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  const handleToggle = (id: string) => {
    setExpandedId(prev => (prev === id ? null : id))
  }

  return (
    <PageShell
      maxWidth="max-w-5xl"
      title="任务市场"
      subtitle="浏览开放任务 · 提交竞标 · 赢取 NAU 奖励"
      right={
        <span className="text-ln-tertiary text-[13px] tabular-nums">
          {!loading && `${tasks.length} 个开放任务`}
        </span>
      }
    >
      {/* Filter Bar */}
      <div className="flex items-center gap-3">
        <label className="text-[13px] text-ln-tertiary whitespace-nowrap">专长筛选</label>
        <select
          value={specialtyFilter}
          onChange={e => setSpecialtyFilter(e.target.value)}
          className="px-3 py-1.5 bg-linear-surface border border-ln-border rounded-lg text-ln-secondary text-[13px] focus:ring-1 focus:ring-linear-brand focus:border-linear-brand outline-none transition"
        >
          {SPECIALTY_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-ln-muted">
          <svg className="animate-spin h-7 w-7 mb-4 text-linear-brand" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-[13px]">加载中…</p>
        </div>
      ) : fetchError ? (
        <Panel className="text-center">
          <span className="text-[#eb5757] text-sm">{fetchError}</span>
          <button onClick={fetchTasks} className="ml-3 text-linear-accent hover:text-linear-hover text-sm underline">
            重试
          </button>
        </Panel>
      ) : tasks.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-ln-muted">
          <svg className="w-14 h-14 mb-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p className="text-[15px] text-ln-tertiary">暂无开放任务</p>
          {specialtyFilter && (
            <button onClick={() => setSpecialtyFilter('')} className="mt-2 text-[13px] text-linear-accent hover:text-linear-hover underline">
              清除筛选
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {tasks.map(task => (
            <TaskCard
              key={task.id}
              task={task}
              isExpanded={expandedId === task.id}
              onToggle={() => handleToggle(task.id)}
              onBidSuccess={fetchTasks}
            />
          ))}
        </div>
      )}
    </PageShell>
  )
}
