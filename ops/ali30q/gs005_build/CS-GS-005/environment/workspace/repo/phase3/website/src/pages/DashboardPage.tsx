import { useState, useEffect } from 'react'

const API_URL = import.meta.env.VITE_API_URL || ''

export default function DashboardPage() {
  const [flywheel, setFlywheel] = useState<any>(null)
  const [consciousness, setConsciousness] = useState<any>(null)
  const [autoStatus, setAutoStatus] = useState<any>(null)
  const [selfTasks, setSelfTasks] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const fetchData = async () => {
    try {
      // heartbeat endpoint removed (heartbeat_monitor module · 2026-04) — agent
      // liveness now surfaces via flywheel.agents (active/total) below.
      const [fw, cs, auto, tasks] = await Promise.all([
        fetch(`${API_URL}/api/dashboard/flywheel`).then(r => r.json()),
        fetch(`${API_URL}/api/dashboard/consciousness`).then(r => r.json()),
        fetch(`${API_URL}/api/dashboard/autonomous-status`).then(r => r.json()),
        fetch(`${API_URL}/api/openclaw/tasks?limit=10`).then(r => r.json()),
      ])
      setFlywheel(fw)
      setConsciousness(cs)
      setAutoStatus(auto)
      setSelfTasks(tasks?.data?.tasks || [])
    } catch { /* ignore */ }
    setLoading(false)
  }

  useEffect(() => { fetchData(); const t = setInterval(fetchData, 30000); return () => clearInterval(t) }, [])

  if (loading) return <div className="min-h-screen bg-linear-black flex items-center justify-center text-gray-400">Loading...</div>

  const fw = flywheel || {}
  const rev = fw.revenue || {}
  const tasks = fw.tasks || {}
  const cust = fw.customers || {}
  const agents = fw.agents || {}
  const quality = fw.quality || {}
  const pain = consciousness?.pain_signals || []
  const dialogue = consciousness?.dialogue || []

  const statusColor = (s: string) => {
    if (s === 'accelerating') return 'text-green-400'
    if (s === 'spinning') return 'text-blue-400'
    if (s === 'warming') return 'text-yellow-400'
    return 'text-red-400'
  }

  const painBar = (intensity: number) => {
    const filled = Math.round(intensity * 10)
    return '█'.repeat(filled) + '░'.repeat(10 - filled)
  }

  return (
    <div className="min-h-screen bg-linear-black py-8 px-4">
      <div className="max-w-6xl mx-auto space-y-6">

        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white">Nautilus Rehoboam</h1>
          <p className="text-gray-400 text-sm mt-1">Institutional AI — Self-Driving Dashboard</p>
          <div className="mt-3">
            <span className={`text-2xl font-bold ${statusColor(fw.flywheel_status || 'stalled')}`}>
              {fw.flywheel_status === 'accelerating' ? '🚀 加速中' :
               fw.flywheel_status === 'spinning' ? '🔄 运转中' :
               fw.flywheel_status === 'warming' ? '🔥 预热中' : '⏸️ 停滞'}
            </span>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: '今日收入', value: `¥${rev.today?.toFixed(0) || 0}`, sub: `总计 ¥${rev.total?.toFixed(0) || 0}`, color: 'text-green-400' },
            { label: '今日任务', value: tasks.today || 0, sub: `成功率 ${tasks.success_rate?.toFixed(0) || 0}%`, color: 'text-blue-400' },
            { label: '活跃客户', value: cust.active_24h || 0, sub: `总计 ${cust.total || 0}`, color: 'text-purple-400' },
            { label: 'Agent 在线', value: agents.active || 0, sub: `总计 ${agents.total || 0}`, color: 'text-yellow-400' },
          ].map((m, i) => (
            <div key={i} className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-xl p-4 text-center">
              <div className="text-xs text-gray-400">{m.label}</div>
              <div className={`text-3xl font-bold ${m.color}`}>{m.value}</div>
              <div className="text-xs text-gray-500 mt-1">{m.sub}</div>
            </div>
          ))}
        </div>

        {/* Quality + Revenue Row */}
        <div className="grid md:grid-cols-2 gap-4">
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-xl p-5">
            <h3 className="text-white font-semibold mb-3">质量审计</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between text-gray-300">
                <span>审计通过</span>
                <span className="text-green-400 font-medium">{quality.audit_passed || 0}</span>
              </div>
              <div className="flex justify-between text-gray-300">
                <span>审计标记</span>
                <span className="text-yellow-400 font-medium">{quality.audit_flagged || 0}</span>
              </div>
              <div className="flex justify-between text-gray-300">
                <span>平均执行时间</span>
                <span className="text-blue-400 font-medium">{quality.avg_execution_time?.toFixed(0) || 0}s</span>
              </div>
            </div>
          </div>
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-xl p-5">
            <h3 className="text-white font-semibold mb-3">收入趋势</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between text-gray-300">
                <span>今日</span><span className="text-green-400">¥{rev.today?.toFixed(0) || 0}</span>
              </div>
              <div className="flex justify-between text-gray-300">
                <span>本周</span><span className="text-green-400">¥{rev.week?.toFixed(0) || 0}</span>
              </div>
              <div className="flex justify-between text-gray-300">
                <span>本月</span><span className="text-green-400">¥{rev.month?.toFixed(0) || 0}</span>
              </div>
              <div className="flex justify-between text-gray-300 border-t border-white/10 pt-2">
                <span>累计</span><span className="text-green-400 font-bold">¥{rev.total?.toFixed(0) || 0}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Autonomous Engine Status */}
        {autoStatus && (
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-xl p-5">
            <h3 className="text-white font-semibold mb-3">
              {autoStatus.running ? '\u2705' : '\u26D4'} {'  '}
              {autoStatus.running ? '\u81EA\u9A7E\u5F15\u64CE\u8FD0\u884C\u4E2D' : '\u81EA\u9A7E\u5F15\u64CE\u5DF2\u505C\u6B62'}
            </h3>
            <div className="grid grid-cols-3 gap-3 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">{autoStatus.cycle_count || 0}</div>
                <div className="text-xs text-gray-500">{'\u601D\u8003\u5FAA\u73AF'}</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">{autoStatus.total_actions || 0}</div>
                <div className="text-xs text-gray-500">{'\u81EA\u4E3B\u884C\u52A8'}</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-400">{selfTasks.length}</div>
                <div className="text-xs text-gray-500">{'\u8FDB\u5316\u4EFB\u52A1'}</div>
              </div>
            </div>
          </div>
        )}

        {/* Self-Improvement Tasks */}
        {selfTasks.length > 0 && (
          <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-xl p-5">
            <h3 className="text-white font-semibold mb-3">{'\u{1F527}'} {'\u81EA\u6211\u8FDB\u5316\u4EFB\u52A1'}</h3>
            <div className="space-y-2">
              {selfTasks.slice(0, 6).map((t: any, i: number) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  <span className="text-yellow-400 mt-0.5">{'\u25CF'}</span>
                  <div>
                    <div className="text-gray-200">{t.title}</div>
                    <div className="text-xs text-gray-500">{t.task_type} | {t.task_id}</div>
                  </div>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-3">{'\u8FD9\u4E9B\u4EFB\u52A1\u7531\u5E73\u53F0\u81EA\u6211\u53CD\u601D\u751F\u6210\uFF0CAgent \u53EF\u8BA4\u9886\u6267\u884C'}</p>
          </div>
        )}


        {/* Bicameral Mind */}
        <div className="bg-white/10 backdrop-blur-lg border border-white/20 rounded-xl p-5">
          <h3 className="text-white font-semibold mb-3">
            🧠 二分心智 — 痛苦指数: <span className={fw.pain_level > 0.7 ? 'text-red-400' : fw.pain_level > 0.4 ? 'text-yellow-400' : 'text-green-400'}>
              {((fw.pain_level || 0) * 100).toFixed(0)}%
            </span>
          </h3>

          {/* Internal Dialogue */}
          {dialogue.length > 0 && (
            <div className="mb-4 space-y-2">
              {dialogue.map((d: any, i: number) => (
                <div key={i} className={`text-sm px-3 py-2 rounded-lg ${d.voice === 'commander' ? 'bg-red-500/10 border-l-2 border-red-500' : 'bg-blue-500/10 border-l-2 border-blue-500'}`}>
                  <span className={`font-medium ${d.voice === 'commander' ? 'text-red-300' : 'text-blue-300'}`}>
                    {d.voice === 'commander' ? '【审判者】' : '【执行者】'}
                  </span>
                  <span className="text-gray-300 ml-1">{d.says}</span>
                </div>
              ))}
            </div>
          )}

          {/* Pain Signals */}
          {pain.length > 0 && (
            <div className="space-y-2">
              {pain.map((p: any, i: number) => (
                <div key={i} className="text-sm">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-gray-500">[{painBar(p.intensity)}]</span>
                    <span className="text-gray-300">{p.source}</span>
                  </div>
                  <div className="text-xs text-gray-500 ml-14">→ {p.action}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Auto-refresh indicator */}
        <p className="text-center text-xs text-gray-600">每30秒自动刷新 · Powered by Rehoboam</p>
      </div>
    </div>
  )
}
