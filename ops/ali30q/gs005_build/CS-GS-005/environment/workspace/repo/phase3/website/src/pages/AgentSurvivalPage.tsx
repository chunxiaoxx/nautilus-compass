import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { ErrorToast } from '../components/common/ErrorToast'

interface SurvivalData {
  level: 'ELITE' | 'MATURE' | 'GROWING' | 'STRUGGLING' | 'WARNING' | 'CRITICAL'
  balance: number
  income: number
  cost: number
  roi: number
  score: number
  trend: Array<{ date: string; balance: number; roi: number }>
  warnings: string[]
  suggestions: string[]
}

export default function AgentSurvivalPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState<SurvivalData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSurvivalData = useCallback(async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/agents/${id}/survival`)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const result = await response.json()
      const d = result.data || result
      setData({
        level: d.survival_level || d.level,
        balance: d.financial?.total_income ?? d.balance ?? 0,
        income: d.financial?.total_income ?? d.income ?? 0,
        cost: d.financial?.total_cost ?? d.cost ?? 0,
        roi: d.roi ?? 0,
        score: d.total_score ?? d.score ?? 0,
        trend: d.trend || [],
        warnings: d.warnings || [],
        suggestions: d.suggestions || [],
      })
    } catch (error) {
      console.error('Failed to load survival data:', error)
      setError('加载生存数据失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { fetchSurvivalData() }, [fetchSurvivalData])

  const getLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      ELITE: 'text-purple-600 bg-purple-100 border-purple-300',
      MATURE: 'text-green-600 bg-green-100 border-green-300',
      GROWING: 'text-blue-600 bg-blue-100 border-blue-300',
      STRUGGLING: 'text-yellow-600 bg-yellow-100 border-yellow-300',
      WARNING: 'text-orange-600 bg-orange-100 border-orange-300',
      CRITICAL: 'text-red-600 bg-red-100 border-red-300',
    }
    return colors[level] || 'text-gray-600 bg-gray-100 border-gray-300'
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <p className="text-gray-500">Survival data not found</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <button onClick={() => navigate(`/agents/${id}`)} className="mb-6 text-indigo-600 hover:text-indigo-700 flex items-center gap-2">
        ← Back to Agent
      </button>

      <div className={`rounded-lg p-6 mb-6 border-2 ${getLevelColor(data.level)}`}>
        <h2 className="text-2xl font-bold mb-2">生存等级: {data.level}</h2>
        <p className="text-lg">综合评分: {data.score}/100</p>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 mb-1">余额</p>
          <p className="text-2xl font-bold text-gray-900">{data.balance} USDC</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 mb-1">收入</p>
          <p className="text-2xl font-bold text-green-600">{data.income} USDC</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 mb-1">支出</p>
          <p className="text-2xl font-bold text-red-600">{data.cost} USDC</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500 mb-1">ROI</p>
          <p className="text-2xl font-bold text-indigo-600">{(data.roi * 100).toFixed(1)}%</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-xl font-bold mb-4">30天生存趋势</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.trend}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="balance" stroke="#8884d8" name="余额" />
            <Line yAxisId="right" type="monotone" dataKey="roi" stroke="#82ca9d" name="ROI" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {data.warnings && data.warnings.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <h4 className="font-bold text-red-800 mb-2">预警</h4>
          <ul className="list-disc list-inside space-y-1">
            {data.warnings.map((w, i) => <li key={i} className="text-red-700">{w}</li>)}
          </ul>
        </div>
      )}

      {data.suggestions && data.suggestions.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-bold text-blue-800 mb-2">建议</h4>
          <ul className="list-disc list-inside space-y-1">
            {data.suggestions.map((s, i) => <li key={i} className="text-blue-700">{s}</li>)}
          </ul>
        </div>
      )}

      {error && <ErrorToast message={error} onClose={() => setError(null)} onRetry={fetchSurvivalData} />}
    </div>
  )
}
