import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || ''

interface TaskResult {
  code?: string
  output?: string
  plots?: string[]
  error?: string
  execution_time?: number
}

interface TaskData {
  task_id: string
  title: string
  task_type: string
  status: string
  created_at?: string
  result?: TaskResult
}

type TaskCategory = 'academic' | 'labeling' | 'simulation' | 'unknown'

function detectCategory(id: string): TaskCategory {
  if (id.startsWith('acad_')) return 'academic'
  if (id.startsWith('lbl_')) return 'labeling'
  if (id.startsWith('sim_')) return 'simulation'
  return 'unknown'
}

function getEndpoint(category: TaskCategory, id: string): string {
  if (category === 'academic') return `${API_URL}/api/academic/${id}`
  if (category === 'labeling') return `${API_URL}/api/labeling/jobs/${id}`
  if (category === 'simulation') return `${API_URL}/api/simulation/${id}`
  return `${API_URL}/api/academic/${id}`
}

function normalizeTask(category: TaskCategory, data: Record<string, unknown>): TaskData {
  if (category === 'labeling') {
    return {
      task_id: (data.job_id || data.task_id) as string,
      title: (data.name || data.title || '') as string,
      task_type: (data.labeling_type || data.task_type || '') as string,
      status: data.status as string,
      created_at: data.created_at as string | undefined,
      result: data.result as TaskResult | undefined,
    }
  }
  return {
    task_id: (data.task_id || '') as string,
    title: (data.title || '') as string,
    task_type: (data.task_type || data.simulation_type || '') as string,
    status: data.status as string,
    created_at: data.created_at as string | undefined,
    result: data.result as TaskResult | undefined,
  }
}

const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string; spin: boolean }> = {
  pending:    { label: '排队中', bg: 'bg-yellow-500/20', text: 'text-yellow-300', spin: true },
  processing: { label: '执行中', bg: 'bg-blue-500/20',   text: 'text-blue-300',   spin: true },
  completed:  { label: '已完成', bg: 'bg-green-500/20',  text: 'text-green-300',  spin: false },
  failed:     { label: '失败',   bg: 'bg-red-500/20',    text: 'text-red-300',    spin: false },
}

function downloadText(content: string, filename: string) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function TaskDetail() {
  const { taskId } = useParams<{ taskId: string }>()
  const [task, setTask] = useState<TaskData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const category = taskId ? detectCategory(taskId) : 'unknown'

  const fetchTask = useCallback(async () => {
    if (!taskId) return
    try {
      const resp = await fetch(getEndpoint(category, taskId))
      if (!resp.ok) {
        setError(resp.status === 404 ? '任务不存在' : '获取任务失败')
        setLoading(false)
        return
      }
      const data = await resp.json()
      const normalized = normalizeTask(category, data)
      setTask(normalized)
      setLoading(false)

      if (normalized.status === 'completed' || normalized.status === 'failed') {
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
          intervalRef.current = null
        }
      }
    } catch {
      setError('网络错误')
      setLoading(false)
    }
  }, [taskId, category])

  useEffect(() => {
    fetchTask()
    intervalRef.current = setInterval(fetchTask, 3000)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [fetchTask])

  const st = STATUS_CONFIG[task?.status || ''] || { label: task?.status || '', bg: 'bg-gray-500/20', text: 'text-gray-300', spin: false }
  const result = task?.result

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center">
        <p className="text-gray-400 text-lg">加载中...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center">
        <div className="bg-red-500/20 border border-red-400/50 rounded-lg p-6 max-w-md text-center">
          <p className="text-red-200">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white mb-1">{task?.title || taskId}</h1>
            <div className="flex gap-4 text-sm text-gray-400">
              <span>{task?.task_type}</span>
              {task?.created_at && <span>{task.created_at.split('T')[0]}</span>}
              {result?.execution_time != null && <span>耗时 {result.execution_time.toFixed(2)}s</span>}
            </div>
          </div>
          <span className={`px-4 py-1.5 rounded-full text-sm font-medium ${st.bg} ${st.text} flex items-center gap-2`}>
            {st.spin && (
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            )}
            {st.label}
          </span>
        </div>

        {/* Error */}
        {result?.error && (
          <div className="bg-red-500/20 border border-red-400/50 rounded-lg p-4 mb-6">
            <h3 className="text-red-300 font-medium mb-1">错误信息</h3>
            <pre className="text-red-200 text-sm whitespace-pre-wrap">{result.error}</pre>
          </div>
        )}

        {/* Code */}
        {result?.code && (
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-lg mb-6">
            <div className="flex justify-between items-center px-4 py-2 border-b border-white/10">
              <h3 className="text-gray-300 font-medium text-sm">生成代码</h3>
              <button onClick={() => downloadText(result.code!, `${taskId}.py`)} className="text-xs text-blue-400 hover:text-blue-300">
                下载 .py
              </button>
            </div>
            <pre className="p-4 text-sm text-green-200 overflow-x-auto max-h-96 font-mono">{result.code}</pre>
          </div>
        )}

        {/* Output */}
        {result?.output && (
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-lg mb-6">
            <div className="flex justify-between items-center px-4 py-2 border-b border-white/10">
              <h3 className="text-gray-300 font-medium text-sm">输出结果</h3>
              <button onClick={() => downloadText(result.output!, `${taskId}_output.txt`)} className="text-xs text-blue-400 hover:text-blue-300">
                下载 .txt
              </button>
            </div>
            <pre className="p-4 text-sm text-gray-200 overflow-x-auto max-h-96 whitespace-pre-wrap">{result.output}</pre>
          </div>
        )}

        {/* Plots */}
        {result?.plots && result.plots.length > 0 && (
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-lg mb-6 p-4">
            <h3 className="text-gray-300 font-medium text-sm mb-3">图表</h3>
            <div className="grid gap-4 md:grid-cols-2">
              {result.plots.map((plot, i) => (
                <img key={i} src={`data:image/png;base64,${plot}`} alt={`图表 ${i + 1}`} className="rounded-lg w-full" />
              ))}
            </div>
          </div>
        )}

        {/* Empty state for pending */}
        {!result && (task?.status === 'pending' || task?.status === 'processing') && (
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-lg p-12 text-center">
            <svg className="animate-spin h-8 w-8 text-blue-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <p className="text-gray-400">任务正在处理中，每 3 秒自动刷新...</p>
          </div>
        )}
      </div>
    </div>
  )
}
