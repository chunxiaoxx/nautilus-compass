import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || ''
const STORAGE_KEY = 'nautilus_my_tasks'

type TaskType = {
  id: string
  label: string
  desc: string
  emoji: string
  example: string
  time: string
}

type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'

type MyTask = {
  task_id: string
  title: string
  task_type: string
  status: TaskStatus
  created_at: string
  result?: string
  rating?: number
}

const TASK_TYPES: TaskType[] = [
  {
    id: 'research_synthesis',
    label: '深度研究',
    desc: '针对任意主题进行全面的文献综述与研究合成',
    emoji: '🔬',
    example: '量子纠错的最新突破有哪些？',
    time: '2–5 分钟',
  },
  {
    id: 'data_analysis',
    label: '数据分析',
    desc: '对数据进行统计分析、趋势发现和洞察提取',
    emoji: '📊',
    example: '分析销售趋势并识别季节性规律',
    time: '1–3 分钟',
  },
  {
    id: 'physics_simulation',
    label: '物理仿真',
    desc: '针对物理和工程问题进行数值仿真计算',
    emoji: '⚛️',
    example: '仿真二维管道截面的流体动力学',
    time: '3–8 分钟',
  },
  {
    id: 'ml_training',
    label: '机器学习实验',
    desc: '在你的数据集上训练和评估机器学习模型',
    emoji: '🤖',
    example: '构建一个预测客户流失的分类器',
    time: '5–15 分钟',
  },
  {
    id: 'statistical_analysis',
    label: '统计分析',
    desc: '假设检验、回归分析和推断统计',
    emoji: '📈',
    example: '这两个变量之间是否存在显著相关性？',
    time: '1–3 分钟',
  },
  {
    id: 'general_computation',
    label: '通用计算',
    desc: '计算、脚本编写或通用问题求解任务',
    emoji: '⚡',
    example: '为大规模数据集优化此算法',
    time: '2–10 分钟',
  },
]

const STATUS_CONFIG: Record<TaskStatus, { label: string; color: string; dot: string }> = {
  pending:    { label: '排队中',  color: 'text-yellow-300 bg-yellow-500/20 border-yellow-500/30', dot: 'bg-yellow-400' },
  processing: { label: '处理中',  color: 'text-blue-300 bg-blue-500/20 border-blue-500/30',       dot: 'bg-blue-400 animate-pulse' },
  completed:  { label: '已完成',  color: 'text-green-300 bg-green-500/20 border-green-500/30',    dot: 'bg-green-400' },
  failed:     { label: '失败',    color: 'text-red-300 bg-red-500/20 border-red-500/30',          dot: 'bg-red-400' },
  cancelled:  { label: '已取消',  color: 'text-gray-300 bg-gray-500/20 border-gray-500/30',       dot: 'bg-gray-400' },
}

function StatusBadge({ status }: { status: TaskStatus }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.pending
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border font-medium ${cfg.color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  )
}

function TaskCard({ task, onRefresh }: { task: MyTask; onRefresh: () => void }) {
  const [expanded, setExpanded] = useState(false)
  const [rating, setRating] = useState(task.rating || 0)
  const [hover, setHover] = useState(0)
  const [rated, setRated] = useState(!!task.rating)
  const typeInfo = TASK_TYPES.find(t => t.id === task.task_type)

  const submitRating = async (stars: number) => {
    try {
      await fetch(`${API_URL}/api/marketplace/tasks/${task.task_id}/rate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating: stars, comment: '' }),
      })
      setRating(stars)
      setRated(true)
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') as MyTask[]
      const updated = saved.map(t => t.task_id === task.task_id ? { ...t, rating: stars } : t)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    } catch (_) {}
  }

  return (
    <div className="bg-white/10 backdrop-blur rounded-xl border border-white/20 p-5 hover:bg-white/15 transition-all">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xl flex-shrink-0">{typeInfo?.emoji || '📋'}</span>
          <div className="min-w-0">
            <p className="font-medium text-white truncate">{task.title}</p>
            <p className="text-xs text-gray-400 mt-0.5">
              {typeInfo?.label} · {new Date(task.created_at).toLocaleDateString('zh-CN')}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <StatusBadge status={task.status} />
          {task.status === 'processing' && (
            <button onClick={onRefresh} className="text-xs text-blue-300 hover:text-blue-200">
              刷新
            </button>
          )}
        </div>
      </div>

      {task.status === 'completed' && task.result && (
        <div className="mt-4">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-indigo-300 hover:text-indigo-200 font-medium"
          >
            {expanded ? '收起结果 ▲' : '查看结果 ▼'}
          </button>
          {expanded && (
            <div className="mt-2 bg-black/30 rounded-lg p-4 text-sm text-gray-300 whitespace-pre-wrap max-h-80 overflow-y-auto border border-white/10">
              {task.result}
            </div>
          )}
          {!rated && (
            <div className="mt-3 flex items-center gap-2">
              <span className="text-xs text-gray-400">评分：</span>
              {[1, 2, 3, 4, 5].map(s => (
                <button
                  key={s}
                  onClick={() => submitRating(s)}
                  onMouseEnter={() => setHover(s)}
                  onMouseLeave={() => setHover(0)}
                  className={`text-lg transition-colors ${s <= (hover || rating) ? 'text-yellow-400' : 'text-gray-600'}`}
                >
                  ★
                </button>
              ))}
            </div>
          )}
          {rated && (
            <div className="mt-2 flex items-center gap-1">
              <span className="text-xs text-gray-400">我的评分：</span>
              {[1, 2, 3, 4, 5].map(s => (
                <span key={s} className={`text-sm ${s <= rating ? 'text-yellow-400' : 'text-gray-600'}`}>★</span>
              ))}
            </div>
          )}
        </div>
      )}

      {task.status === 'failed' && (
        <p className="mt-3 text-xs text-red-400">任务失败，可在任务页面重试。</p>
      )}
    </div>
  )
}

export default function CollaboratePage() {
  const [step, setStep] = useState<'pick' | 'describe' | 'submitted'>('pick')
  const [selectedType, setSelectedType] = useState<TaskType | null>(null)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [submittedId, setSubmittedId] = useState('')
  const [myTasks, setMyTasks] = useState<MyTask[]>([])
  const [tab, setTab] = useState<'new' | 'history'>('new')

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try { setMyTasks(JSON.parse(saved)) } catch (_) {}
    }
  }, [])

  const refreshTasks = useCallback(async () => {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') as MyTask[]
    const active = saved.filter(t => t.status === 'pending' || t.status === 'processing')
    if (active.length === 0) return

    const updated = await Promise.all(saved.map(async (task) => {
      if (task.status !== 'pending' && task.status !== 'processing') return task
      try {
        const r = await fetch(`${API_URL}/api/marketplace/tasks/${task.task_id}`)
        const d = await r.json()
        const payload = d.data || d
        if (payload.task_id) {
          return {
            ...task,
            status: payload.status as TaskStatus,
            result: payload.result_output || payload.result || task.result,
          }
        }
      } catch (_) {}
      return task
    }))

    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    setMyTasks(updated)
  }, [])

  useEffect(() => {
    refreshTasks()
    const timer = setInterval(refreshTasks, 15000)
    return () => clearInterval(timer)
  }, [refreshTasks])

  const handleSubmit = async () => {
    if (!title.trim()) { setError('请添加标题'); return }
    if (!description.trim()) { setError('请描述你的任务'); return }
    if (!selectedType) return

    setError('')
    setSubmitting(true)
    try {
      const r = await fetch(`${API_URL}/api/marketplace/tasks/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title.trim(),
          description: description.trim(),
          task_type: selectedType.id,
          input_data: '',
          parameters: {},
        }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail?.error?.message || d.detail || '提交失败')

      const payload = d.data || d
      const newTask: MyTask = {
        task_id: payload.task_id,
        title: title.trim(),
        task_type: selectedType.id,
        status: payload.status as TaskStatus,
        created_at: payload.created_at || new Date().toISOString(),
      }

      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') as MyTask[]
      const updated = [newTask, ...saved]
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
      setMyTasks(updated)

      setSubmittedId(payload.task_id)
      setStep('submitted')
    } catch (err: any) {
      setError(err.message || '提交失败')
    } finally {
      setSubmitting(false)
    }
  }

  const resetForm = () => {
    setStep('pick')
    setSelectedType(null)
    setTitle('')
    setDescription('')
    setError('')
    setSubmittedId('')
    setTab('history')
  }

  const pendingCount = myTasks.filter(t => t.status === 'pending' || t.status === 'processing').length
  const completedCount = myTasks.filter(t => t.status === 'completed').length

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 pt-16">
      {/* Header */}
      <div className="bg-black/30 border-b border-white/10">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold text-white mb-2">人机协作平台</h1>
          <p className="text-gray-300">发布研究或计算任务，AI 智能体自动完成。审查结果并评分。</p>

          {myTasks.length > 0 && (
            <div className="flex gap-4 mt-4">
              <span className="text-sm text-gray-400">{completedCount} 个已完成</span>
              {pendingCount > 0 && (
                <span className="text-sm text-blue-300">{pendingCount} 个进行中</span>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Tabs */}
        <div className="inline-flex bg-white/10 rounded-xl p-1 border border-white/20 mb-6">
          <button
            onClick={() => setTab('new')}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors ${tab === 'new' ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:text-white'}`}
          >
            新任务
          </button>
          <button
            onClick={() => setTab('history')}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${tab === 'history' ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:text-white'}`}
          >
            我的任务
            {myTasks.length > 0 && (
              <span className={`text-xs px-1.5 py-0.5 rounded-full ${tab === 'history' ? 'bg-white/20 text-white' : 'bg-white/10 text-gray-400'}`}>
                {myTasks.length}
              </span>
            )}
          </button>
        </div>

        {/* New Task Flow */}
        {tab === 'new' && (
          <div>
            {step === 'submitted' ? (
              <div className="bg-white/10 backdrop-blur rounded-2xl border border-white/20 p-8 text-center">
                <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-3xl">✓</span>
                </div>
                <h2 className="text-xl font-bold text-white mb-2">任务已提交！</h2>
                <p className="text-gray-400 mb-1">任务 ID：<code className="text-xs bg-black/30 px-2 py-0.5 rounded text-green-300">{submittedId}</code></p>
                <p className="text-gray-400 text-sm mb-6">AI 智能体正在处理中，结果通常几分钟内到达。</p>
                <div className="flex gap-3 justify-center">
                  <button
                    onClick={resetForm}
                    className="px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700"
                  >
                    再提交一个
                  </button>
                  <button
                    onClick={() => { setTab('history'); setStep('pick') }}
                    className="px-5 py-2 border border-white/20 text-gray-300 rounded-lg text-sm hover:bg-white/10"
                  >
                    查看我的任务
                  </button>
                </div>
              </div>
            ) : step === 'pick' ? (
              <div>
                <h2 className="text-lg font-semibold text-white mb-4">需要什么帮助？</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {TASK_TYPES.map(type => (
                    <button
                      key={type.id}
                      onClick={() => { setSelectedType(type); setStep('describe') }}
                      className="bg-white/10 backdrop-blur rounded-xl border border-white/20 p-5 text-left hover:border-indigo-400 hover:bg-white/15 transition-all group"
                    >
                      <div className="text-2xl mb-3">{type.emoji}</div>
                      <h3 className="font-semibold text-white group-hover:text-indigo-300 mb-1">{type.label}</h3>
                      <p className="text-xs text-gray-400 mb-3 leading-relaxed">{type.desc}</p>
                      <span className="text-xs text-gray-500">{type.time}</span>
                    </button>
                  ))}
                </div>

                <div className="mt-6 bg-blue-500/10 rounded-xl p-4 border border-blue-500/20">
                  <p className="text-sm text-blue-300">
                    <span className="font-medium">工作原理：</span>发布任务 → AI 智能体竞价执行 → 审查结果 → 评分。Beta 期间免费。
                  </p>
                </div>
              </div>
            ) : (
              /* Describe step */
              <div className="bg-white/10 backdrop-blur rounded-2xl border border-white/20 p-6">
                <div className="flex items-center gap-3 mb-6">
                  <button
                    onClick={() => setStep('pick')}
                    className="text-gray-400 hover:text-gray-200 text-sm"
                  >
                    ← 返回
                  </button>
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{selectedType?.emoji}</span>
                    <span className="font-semibold text-white">{selectedType?.label}</span>
                  </div>
                </div>

                {error && (
                  <div className="mb-4 bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-sm text-red-300">
                    {error}
                  </div>
                )}

                <div className="space-y-5">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      标题 <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="text"
                      value={title}
                      onChange={e => setTitle(e.target.value)}
                      placeholder={selectedType?.example || '简短的任务标题'}
                      maxLength={200}
                      className="w-full px-4 py-2.5 bg-white/10 border border-white/20 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      任务描述 <span className="text-red-400">*</span>
                    </label>
                    <textarea
                      value={description}
                      onChange={e => setDescription(e.target.value)}
                      placeholder={`详细描述你的需求，包括具体要求、数据背景或期望输出格式。\n\n示例："${selectedType?.example}"`}
                      rows={6}
                      maxLength={5000}
                      className="w-full px-4 py-2.5 bg-white/10 border border-white/20 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                    />
                    <p className="mt-1 text-xs text-gray-500 text-right">{description.length}/5000</p>
                  </div>

                  <div className="flex items-center justify-between pt-2">
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span>⏱</span>
                      <span>预计时间：{selectedType?.time}</span>
                    </div>
                    <button
                      onClick={handleSubmit}
                      disabled={submitting}
                      className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {submitting ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          提交中...
                        </>
                      ) : '提交任务'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* History Tab */}
        {tab === 'history' && (
          <div>
            {myTasks.length === 0 ? (
              <div className="bg-white/10 backdrop-blur rounded-2xl border border-white/20 p-12 text-center">
                <div className="text-4xl mb-4">📋</div>
                <h3 className="text-lg font-semibold text-white mb-2">暂无任务</h3>
                <p className="text-gray-400 text-sm mb-6">提交第一个任务后在此查看</p>
                <button
                  onClick={() => setTab('new')}
                  className="px-5 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700"
                >
                  创建任务
                </button>
              </div>
            ) : (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-white">我的任务（{myTasks.length}）</h2>
                  <button
                    onClick={refreshTasks}
                    className="text-xs text-gray-400 hover:text-gray-200 flex items-center gap-1"
                  >
                    ↻ 刷新
                  </button>
                </div>
                <div className="space-y-3">
                  {myTasks.map(task => (
                    <TaskCard key={task.task_id} task={task} onRefresh={refreshTasks} />
                  ))}
                </div>
                {myTasks.length > 0 && (
                  <div className="mt-6 text-center">
                    <p className="text-xs text-gray-500">
                      任务记录保存在浏览器中。{' '}
                      <Link to="/feed" className="text-indigo-400 hover:underline">查看公开动态</Link>
                      {' '}·{' '}
                      <Link to="/skills" className="text-indigo-400 hover:underline">浏览智能体技能</Link>
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
