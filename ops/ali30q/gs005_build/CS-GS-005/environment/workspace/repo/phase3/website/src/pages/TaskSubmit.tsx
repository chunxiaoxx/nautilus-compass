import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || ''

type Category = 'academic' | 'labeling' | 'simulation'

const CATEGORIES: { key: Category; label: string; icon: string }[] = [
  { key: 'academic', label: '学术计算', icon: '🔬' },
  { key: 'labeling', label: '数据标注', icon: '🏷️' },
  { key: 'simulation', label: '仿真模拟', icon: '⚙️' },
]

const SUB_TYPES: Record<Category, { value: string; label: string }[]> = {
  academic: [
    { value: 'curve_fitting', label: '曲线拟合' },
    { value: 'ode_simulation', label: 'ODE 常微分方程' },
    { value: 'pde_simulation', label: 'PDE 偏微分方程' },
    { value: 'monte_carlo', label: '蒙特卡洛模拟' },
    { value: 'statistical_analysis', label: '统计分析' },
    { value: 'ml_training', label: '机器学习训练' },
    { value: 'physics_simulation', label: '物理仿真' },
    { value: 'general_computation', label: '通用计算' },
    { value: 'jc_constitutive', label: 'J-C 本构模型' },
    { value: 'thmc_coupling', label: 'THMC 耦合模拟' },
  ],
  labeling: [
    { value: 'sentiment', label: '情感分析' },
    { value: 'classification', label: '文本分类' },
    { value: 'entity_extraction', label: '实体识别' },
    { value: 'object_detection', label: '目标检测' },
    { value: 'scene_classification', label: '场景分类' },
    { value: 'safety_critical', label: '安全事件' },
  ],
  simulation: [
    { value: 'physics_simulation', label: '物理仿真' },
    { value: 'motion_planning', label: '运动规划' },
    { value: 'dynamics_simulation', label: '动力学仿真' },
    { value: 'scenario_generation', label: '场景生成' },
    { value: 'collision_detection', label: '碰撞检测' },
  ],
}

const ENDPOINTS: Record<Category, string> = {
  academic: '/api/academic/submit',
  labeling: '/api/labeling/jobs',
  simulation: '/api/simulation/submit',
}

const TASK_PRICES: Record<string, number> = {
  // Academic
  general_computation: 2, curve_fitting: 5, ode_simulation: 8, pde_simulation: 10,
  monte_carlo: 5, statistical_analysis: 5, ml_training: 10, data_visualization: 3,
  physics_simulation: 10, jc_constitutive: 15, thmc_coupling: 20,
  // Labeling (per item)
  sentiment: 0.05, classification: 0.08, entity_extraction: 0.15,
  object_detection: 0.30, scene_classification: 0.25, safety_critical: 0.50,
  // Simulation
  motion_planning: 15, dynamics_simulation: 12, scenario_generation: 8,
  collision_detection: 10,
}

const LABELING_TYPES = new Set([
  'sentiment', 'classification', 'entity_extraction', 'intent', 'spam',
  'toxicity', 'object_detection', 'scene_classification', 'action_recognition',
  'safety_critical', 'environmental',
])

const inputClass = 'w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none'

export default function TaskSubmit() {
  const navigate = useNavigate()
  const [category, setCategory] = useState<Category>('academic')
  const [subType, setSubType] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [inputData, setInputData] = useState('')
  const [parameters, setParameters] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const getEstimatedPrice = (): string | null => {
    if (!subType) return null
    const base = TASK_PRICES[subType]
    if (base === undefined) return '5.00'
    if (LABELING_TYPES.has(subType)) {
      const lines = inputData.split('\n').filter(Boolean).length || 1
      return (base * lines).toFixed(2)
    }
    return base.toFixed(2)
  }

  const handleCategoryChange = (c: Category) => {
    setCategory(c)
    setSubType('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !subType) return
    setSubmitting(true)
    setError('')

    try {
      let parsedParams: Record<string, unknown> | undefined
      if (parameters.trim()) {
        try {
          parsedParams = JSON.parse(parameters)
        } catch {
          setError('参数 JSON 格式错误')
          setSubmitting(false)
          return
        }
      }

      const body: Record<string, unknown> = category === 'labeling'
        ? {
            name: title,
            labeling_type: subType,
            items: inputData.split('\n').filter(Boolean),
            ...(parsedParams && { parameters: parsedParams }),
          }
        : {
            title,
            description,
            task_type: subType,
            ...(inputData && { input_data: inputData }),
            ...(parsedParams && { parameters: parsedParams }),
          }

      const resp = await fetch(`${API_URL}${ENDPOINTS[category]}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await resp.json()

      if (!resp.ok) {
        const msg = data.detail?.error?.message || data.detail || '提交失败'
        if (resp.status === 402) {
          setError(`${msg} (需要 ${data.detail?.error?.price ?? '?'} 元)`)
        } else {
          setError(msg)
        }
        setSubmitting(false)
        return
      }

      const taskId = data.task_id || data.job_id
      if (taskId) {
        navigate(`/marketplace/task/${taskId}`)
      }
    } catch {
      setError('网络错误，请重试')
    }
    setSubmitting(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      <div className="max-w-3xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold text-white mb-2 text-center">提交新任务</h1>
        <p className="text-gray-400 text-center mb-8">选择类别、填写信息、一键提交</p>

        {/* Category selector */}
        <div className="flex justify-center mb-8">
          <div className="flex bg-white/10 rounded-lg p-1">
            {CATEGORIES.map(c => (
              <button
                key={c.key}
                onClick={() => handleCategoryChange(c.key)}
                className={`px-5 py-2 rounded-md text-sm font-medium transition-colors ${
                  category === c.key ? 'bg-white text-gray-900 shadow' : 'text-gray-300 hover:text-white'
                }`}
              >
                {c.icon} {c.label}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-xl p-6 space-y-5">
          {/* Sub-type */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">任务类型 *</label>
            <select value={subType} onChange={e => setSubType(e.target.value)} className={inputClass} required>
              <option value="">选择类型</option>
              {SUB_TYPES[category].map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">标题 *</label>
            <input value={title} onChange={e => setTitle(e.target.value)} placeholder="任务标题" className={inputClass} required />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">
              {category === 'labeling' ? '待标注数据（每行一条）' : '任务描述'}
            </label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={3}
              placeholder={category === 'labeling' ? '每行一条待标注文本...' : '详细描述任务需求...'}
              className={inputClass}
            />
          </div>

          {/* Input data */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">输入数据</label>
            <textarea
              value={inputData}
              onChange={e => setInputData(e.target.value)}
              rows={4}
              placeholder="粘贴输入数据..."
              className={inputClass}
            />
            <input
              type="file"
              onChange={e => setFile(e.target.files?.[0] || null)}
              className="mt-2 text-sm text-gray-400 file:mr-3 file:py-1 file:px-3 file:rounded-lg file:border-0 file:bg-white/10 file:text-gray-300 file:cursor-pointer"
            />
            {file && <p className="text-xs text-gray-500 mt-1">已选择: {file.name}</p>}
          </div>

          {/* Parameters */}
          <div>
            <label className="block text-sm text-gray-300 mb-1">参数（JSON，可选）</label>
            <textarea
              value={parameters}
              onChange={e => setParameters(e.target.value)}
              rows={2}
              placeholder='{"learning_rate": 0.01, "epochs": 100}'
              className={`${inputClass} font-mono text-sm`}
            />
          </div>

          {/* Price display */}
          {subType && (
            <div className="rounded-md bg-blue-500/10 border border-blue-400/30 p-3 flex items-center justify-between">
              <span className="text-sm text-blue-200">
                {LABELING_TYPES.has(subType) ? '预估费用（按数据量）' : '此任务费用'}
              </span>
              <span className="text-lg font-semibold text-blue-100">
                {getEstimatedPrice()} 元
              </span>
            </div>
          )}

          {error && (
            <div className="rounded-md bg-red-500/20 border border-red-400/50 p-3">
              <p className="text-sm text-red-200">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 rounded-xl text-white font-semibold bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 transition-all"
          >
            {submitting ? '提交中...' : subType ? `提交任务 (${getEstimatedPrice()} 元)` : '提交任务'}
          </button>
        </form>
      </div>
    </div>
  )
}
