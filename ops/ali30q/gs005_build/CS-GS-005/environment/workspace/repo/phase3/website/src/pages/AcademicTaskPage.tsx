import { useState, useEffect, useRef, useCallback } from 'react'

const API_URL = import.meta.env.VITE_API_URL || ''

interface RatingWidgetProps {
  taskId: string
  existingRating?: number | null
}

function StarRatingWidget({ taskId, existingRating }: RatingWidgetProps) {
  const [hovered, setHovered] = useState(0)
  const [selected, setSelected] = useState(0)
  const [comment, setComment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')

  if (existingRating != null && existingRating > 0) {
    const filled = Math.round(existingRating)
    return (
      <div className="mt-4 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
        <p className="text-sm text-gray-300 mb-1">您的评分：</p>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map(star => (
            <span key={star} className={`text-2xl ${star <= filled ? 'text-yellow-400' : 'text-gray-600'}`}>
              ★
            </span>
          ))}
        </div>
      </div>
    )
  }

  if (submitted) {
    return (
      <div className="mt-4 p-4 bg-green-500/10 border border-green-500/20 rounded-lg text-green-300 text-sm">
        感谢您的评分！
      </div>
    )
  }

  const handleSubmit = async () => {
    if (selected === 0) {
      setError('请先选择星级')
      return
    }
    setError('')
    setSubmitting(true)
    try {
      const res = await fetch(`${API_URL}/api/marketplace/tasks/${taskId}/rate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rating: selected,
          comment: comment.trim() || undefined,
        }),
      })
      if (!res.ok) {
        const errData = await res.json().catch(() => null)
        throw new Error(errData?.error?.message ?? errData?.detail ?? `提交失败 (${res.status})`)
      }
      setSubmitted(true)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '评分提交失败，请重试'
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  const displayStars = hovered > 0 ? hovered : selected

  return (
    <div className="mt-4 p-4 bg-white/5 border border-white/10 rounded-lg">
      <h4 className="text-sm font-semibold text-gray-300 mb-3">为本次任务评分</h4>
      <div
        className="flex gap-1 mb-3"
        onMouseLeave={() => setHovered(0)}
      >
        {[1, 2, 3, 4, 5].map(star => (
          <button
            key={star}
            type="button"
            className={`text-3xl transition-colors ${star <= displayStars ? 'text-yellow-400' : 'text-gray-600 hover:text-yellow-300'}`}
            onMouseEnter={() => setHovered(star)}
            onClick={() => setSelected(star)}
            aria-label={`${star} 星`}
          >
            ★
          </button>
        ))}
      </div>
      <textarea
        value={comment}
        onChange={e => setComment(e.target.value.slice(0, 200))}
        placeholder="评论（可选，最多 200 字）"
        rows={2}
        className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-gray-200 placeholder-gray-500 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-none mb-2"
      />
      <p className="text-xs text-gray-500 mb-2 text-right">{comment.length}/200</p>
      {error && (
        <p className="text-xs text-red-400 mb-2">{error}</p>
      )}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={submitting || selected === 0}
        className="px-4 py-2 bg-yellow-500 text-gray-900 rounded-lg text-sm font-semibold hover:bg-yellow-400 transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {submitting ? '提交中...' : '提交评分'}
      </button>
    </div>
  )
}

const TASK_TYPE_MAP: Record<string, string> = {
  '曲线拟合': 'curve_fitting',
  'ODE 常微分方程': 'ode_simulation',
  'PDE 偏微分方程': 'pde_simulation',
  '蒙特卡洛模拟': 'monte_carlo',
  '统计分析': 'statistical_analysis',
  '机器学习训练': 'ml_training',
  '数据可视化': 'data_visualization',
  '物理仿真': 'physics_simulation',
  '通用计算': 'general_computation',
  'J-C 本构模型': 'jc_constitutive',
  'THMC 耦合模拟': 'thmc_coupling',
  'Research Synthesis (DeerFlow)': 'research_synthesis',
}

const TASK_TYPE_DESCRIPTIONS: Record<string, string> = {
  'Research Synthesis (DeerFlow)': 'Multi-agent deep research pipeline powered by DeerFlow. Earns 8 NAU.',
}

const TASK_TYPES = [
  '曲线拟合',
  'ODE 常微分方程',
  'PDE 偏微分方程',
  '蒙特卡洛模拟',
  '统计分析',
  '机器学习训练',
  '数据可视化',
  '物理仿真',
  '通用计算',
  'J-C 本构模型',
  'THMC 耦合模拟',
  'Research Synthesis (DeerFlow)',
] as const

type TaskType = typeof TASK_TYPES[number]

interface TaskResult {
  task_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  code?: string
  output?: string
  plots?: string[]
  execution_time?: number
  error?: string
  blockchain_tx_hash?: string | null
  token_reward?: number | null
  quality_rating?: number | null
}

interface FormState {
  title: string
  description: string
  task_type: TaskType | ''
  input_data: string
  parameters: string
}

const INITIAL_FORM: FormState = {
  title: '',
  description: '',
  task_type: '',
  input_data: '',
  parameters: '',
}

function StatusBadge({ status }: { status: TaskResult['status'] }) {
  const styles: Record<string, string> = {
    pending: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    processing: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    completed: 'bg-green-500/20 text-green-300 border-green-500/30',
    failed: 'bg-red-500/20 text-red-300 border-red-500/30',
  }

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${styles[status]}`}>
      {status === 'processing' && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}

export default function AcademicTaskPage() {
  const [form, setForm] = useState<FormState>({ ...INITIAL_FORM })
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<TaskResult | null>(null)
  const [submitError, setSubmitError] = useState('')
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => stopPolling()
  }, [stopPolling])

  const pollResult = useCallback((taskId: string) => {
    stopPolling()
    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/academic/${taskId}`)
        if (!res.ok) return
        const data = await res.json()
        const taskResult: TaskResult = data.data ?? data
        setResult(taskResult)
        if (taskResult.status === 'completed' || taskResult.status === 'failed') {
          stopPolling()
        }
      } catch {
        // silently retry on next interval
      }
    }, 3000)
  }, [stopPolling])

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      const text = ev.target?.result
      if (typeof text === 'string') {
        setForm({ ...form, input_data: text })
      }
    }
    reader.readAsText(file)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitError('')
    setResult(null)
    stopPolling()

    if (!form.title.trim() || !form.task_type) {
      setSubmitError('标题和任务类型为必填项')
      return
    }

    setSubmitting(true)
    try {
      const body: Record<string, unknown> = {
        title: form.title.trim(),
        description: form.description.trim(),
        task_type: TASK_TYPE_MAP[form.task_type] || form.task_type,
        input_data: form.input_data.trim() || undefined,
      }

      if (form.parameters.trim()) {
        try {
          body.parameters = JSON.parse(form.parameters.trim())
        } catch {
          setSubmitError('参数必须是有效的 JSON 格式')
          setSubmitting(false)
          return
        }
      }

      const res = await fetch(`${API_URL}/api/academic/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => null)
        throw new Error(err?.error?.message ?? err?.detail ?? `Request failed (${res.status})`)
      }

      const data = await res.json()
      const taskResult: TaskResult = data.data ?? data
      setResult(taskResult)

      if (taskResult.status === 'pending' || taskResult.status === 'processing') {
        pollResult(taskResult.task_id)
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Submission failed. Please try again.'
      setSubmitError(message)
    } finally {
      setSubmitting(false)
    }
  }

  const downloadFile = (content: string, filename: string, mimeType = 'text/plain') => {
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  const downloadBase64Image = (base64: string, index: number) => {
    const a = document.createElement('a')
    a.href = base64.startsWith('data:') ? base64 : `data:image/png;base64,${base64}`
    a.download = `plot_${index + 1}.png`
    a.click()
  }

  const inputClasses =
    'w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition'
  const labelClasses = 'block text-sm font-semibold mb-2 text-gray-200'

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      <div className="max-w-7xl mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 text-white">学术计算引擎</h1>
          <p className="text-xl text-gray-200">
            提交物理仿真、曲线拟合、机器学习等学术计算任务 —  
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-10">
          {/* Submit Section */}
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 p-8 rounded-lg shadow-xl">
            <h2 className="text-2xl font-bold mb-6 text-white">提交任务</h2>

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* 标题 */}
              <div>
                <label className={labelClasses}>标题 *</label>
                <input
                  type="text"
                  name="title"
                  value={form.title}
                  onChange={handleChange}
                  placeholder="例：Lorenz 混沌系统仿真"
                  className={inputClasses}
                  required
                />
              </div>

              {/* Description */}
              <div>
                <label className={labelClasses}>描述</label>
                <textarea
                  name="description"
                  value={form.description}
                  onChange={handleChange}
                  rows={3}
                  placeholder="详细描述你需要完成的计算任务..."
                  className={inputClasses}
                />
              </div>

              {/* 任务类型 */}
              <div>
                <label className={labelClasses}>任务类型 *</label>
                <select
                  name="task_type"
                  value={form.task_type}
                  onChange={handleChange}
                  className={inputClasses}
                  required
                >
                  <option value="">选择任务类型</option>
                  {TASK_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
                {form.task_type && TASK_TYPE_DESCRIPTIONS[form.task_type] && (
                  <p className="mt-1.5 text-xs text-purple-300">
                    {TASK_TYPE_DESCRIPTIONS[form.task_type]}
                  </p>
                )}
              </div>

              {/* Input Data */}
              <div>
                <label className={labelClasses}>输入数据 (CSV / JSON)</label>
                <textarea
                  name="input_data"
                  value={form.input_data}
                  onChange={handleChange}
                  rows={4}
                  placeholder={'在此粘贴数据，或上传文件...\n\ne.g. x,y\\n0,0\\n1,1\\n2,4'}
                  className={inputClasses}
                />
                <input
                  type="file"
                  accept=".csv,.json,.txt,.tsv"
                  onChange={handleFileUpload}
                  className="mt-2 text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-500/20 file:text-blue-300 hover:file:bg-blue-500/30 file:cursor-pointer"
                />
              </div>

              {/* Parameters */}
              <div>
                <label className={labelClasses}>参数 (可选 JSON)</label>
                <textarea
                  name="parameters"
                  value={form.parameters}
                  onChange={handleChange}
                  rows={3}
                  placeholder={'{\n  "dt": 0.01,\n  "steps": 10000\n}'}
                  className={`${inputClasses} font-mono text-sm`}
                />
              </div>

              {/* Error */}
              {submitError && (
                <div className="bg-red-500/20 border border-red-500/30 text-red-300 px-4 py-3 rounded-lg text-sm">
                  {submitError}
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-blue-500 text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {submitting ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Submitting...
                  </>
                ) : (
                  'Submit Task'
                )}
              </button>
            </form>
          </div>

          {/* Results Section */}
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 p-8 rounded-lg shadow-xl">
            <h2 className="text-2xl font-bold mb-6 text-white">Results</h2>

            {!result ? (
              <div className="flex flex-col items-center justify-center h-64 text-gray-400">
                <svg className="w-16 h-16 mb-4 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p>Submit a task to see results here</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Status + Execution Time */}
                <div className="flex items-center justify-between flex-wrap gap-3">
                  <StatusBadge status={result.status} />
                  {result.execution_time != null && (
                    <span className="text-sm text-gray-400">
                      Completed in {result.execution_time.toFixed(2)}s
                    </span>
                  )}
                </div>

                {/* NAU Token Reward */}
                {result.blockchain_tx_hash && (
                  <div className="p-3 bg-purple-50/10 border border-purple-400/30 rounded-lg text-sm">
                    <div className="flex items-center gap-2 text-purple-300 font-medium">
                      <span>⚡</span>
                      <span>NAU Token Reward: {result.token_reward ?? 1} NAU</span>
                    </div>
                    <a
                      href={`https://sepolia.basescan.org/tx/${result.blockchain_tx_hash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-purple-400 hover:text-purple-300 text-xs mt-1 block truncate"
                    >
                      {result.blockchain_tx_hash}
                    </a>
                  </div>
                )}

                {/* Error */}
                {result.error && (
                  <div className="bg-red-500/20 border border-red-500/30 text-red-300 px-4 py-3 rounded-lg text-sm">
                    {result.error}
                  </div>
                )}

                {/* Generated Code */}
                {result.code && (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
                        Generated Code
                      </h3>
                      <button
                        onClick={() => downloadFile(result.code!, `${result.task_id}_code.py`, 'text/x-python')}
                        className="text-xs text-blue-400 hover:text-blue-300 transition"
                      >
                        Download .py
                      </button>
                    </div>
                    <pre className="bg-gray-900/80 border border-gray-700 rounded-lg p-4 text-sm text-green-300 font-mono overflow-x-auto max-h-72 overflow-y-auto whitespace-pre-wrap">
                      {result.code}
                    </pre>
                  </div>
                )}

                {/* Output */}
                {result.output && (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
                        Output
                      </h3>
                      <button
                        onClick={() => downloadFile(result.output!, `${result.task_id}_output.txt`)}
                        className="text-xs text-blue-400 hover:text-blue-300 transition"
                      >
                        Download .txt
                      </button>
                    </div>
                    <pre className="bg-gray-900/80 border border-gray-700 rounded-lg p-4 text-sm text-gray-200 font-mono overflow-x-auto max-h-48 overflow-y-auto whitespace-pre-wrap">
                      {result.output}
                    </pre>
                  </div>
                )}

                {/* Plots */}
                {result.plots && result.plots.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-2">
                      Plots
                    </h3>
                    <div className="space-y-4">
                      {result.plots.map((plot, i) => (
                        <div key={i} className="relative group">
                          <img
                            src={plot.startsWith('data:') ? plot : `data:image/png;base64,${plot}`}
                            alt={`Plot ${i + 1}`}
                            className="w-full rounded-lg border border-gray-700"
                          />
                          <button
                            onClick={() => downloadBase64Image(plot, i)}
                            className="absolute top-2 right-2 bg-gray-900/80 text-gray-300 text-xs px-3 py-1 rounded opacity-0 group-hover:opacity-100 transition hover:text-white"
                          >
                            Download
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* DeerFlow Research Sections */}
                {(() => {
                  try {
                    const params = typeof (result as TaskResult & { parameters?: unknown }).parameters === 'string'
                      ? JSON.parse((result as TaskResult & { parameters?: unknown }).parameters as string)
                      : (result as TaskResult & { parameters?: unknown }).parameters
                    const deerflowData = (params as Record<string, unknown>)?._deerflow as {
                      sections?: {
                        summary?: string
                        findings?: string
                        recommendations?: string
                      }
                    } | null | undefined
                    if (!deerflowData?.sections) return null
                    const { sections } = deerflowData
                    return (
                      <div className="space-y-4">
                        {sections.summary && (
                          <div>
                            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">
                              Executive Summary
                            </h4>
                            <p className="text-gray-200 text-sm leading-relaxed">{sections.summary}</p>
                          </div>
                        )}
                        {sections.findings && (
                          <div>
                            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">
                              Key Findings
                            </h4>
                            <p className="text-gray-200 text-sm leading-relaxed">{sections.findings}</p>
                          </div>
                        )}
                        {sections.recommendations && (
                          <div>
                            <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">
                              Recommendations
                            </h4>
                            <p className="text-gray-200 text-sm leading-relaxed">{sections.recommendations}</p>
                          </div>
                        )}
                        <a
                          href={`/api/academic-tasks/${result.task_id}/pdf`}
                          className="inline-flex items-center gap-2 text-purple-400 hover:text-purple-300 text-sm"
                          download
                        >
                          Download PDF Report
                        </a>
                      </div>
                    )
                  } catch {
                    return null
                  }
                })()}

                {/* Polling indicator */}
                {(result.status === 'pending' || result.status === 'processing') && (
                  <p className="text-sm text-gray-400 animate-pulse">
                    Polling for updates every 3 seconds...
                  </p>
                )}

                {/* User Rating */}
                {result.status === 'completed' && (
                  <StarRatingWidget
                    taskId={result.task_id}
                    existingRating={result.quality_rating}
                  />
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
