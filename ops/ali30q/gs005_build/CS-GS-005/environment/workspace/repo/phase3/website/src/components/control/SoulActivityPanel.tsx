/**
 * SoulActivityPanel · soul 引擎"在做什么"时间线(治"只见裸数字").
 *
 * 接 GET /api/platform/soul/activity(只读·公开)· 形状(curl 实测 2026-06-09):
 *   { success, data: {
 *       recent_cycles: [{ cycle_id, goal_source, ship_status, git_sha, created_at }],
 *       fde_verdicts:  [{ verdict_id, task_uid, source, overall_pass, veto_failed, score, created_at }],
 *       summary: { cycles_total, ships_success, verdicts_total, verdicts_passed }
 *   }, error }
 * 渲染近期 engine cycle(ship 成功/失败)+ 成绩 summary · 不是裸计数,带 ship 状态色 + 相对时间.
 * 自身拉取(独立端点)· fail-soft 空态.
 */
import { useEffect, useState } from 'react'
import { Panel, Shimmer, EmptyState, relTime } from './PanelKit'

type Cycle = {
  cycle_id: string
  goal_source: string | null
  ship_status: string | null
  git_sha: string | null
  created_at: string | null
}
type Summary = {
  cycles_total: number
  ships_success: number
  verdicts_total: number
  verdicts_passed: number
}
type ActivityData = { recent_cycles: Cycle[]; summary: Summary }

function shipTone(status: string | null): { dot: string; text: string; label: string } {
  if (status === 'success')
    return { dot: 'bg-linear-green', text: 'text-linear-green', label: 'ship 成功' }
  if (status === 'fail')
    return { dot: 'bg-[#eb5757]', text: 'text-[#eb5757]', label: 'ship 失败' }
  return { dot: 'bg-ln-muted', text: 'text-ln-tertiary', label: status || '未知' }
}

export default function SoulActivityPanel({ className = '' }: { className?: string }) {
  const [data, setData] = useState<ActivityData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const r = await fetch('/api/platform/soul/activity?limit=12')
        const body = await r.json()
        if (!body.success) throw new Error(body.error || 'soul activity error')
        if (!cancelled) {
          setData(body.data as ActivityData)
          setError(null)
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'load failed')
      }
    }
    load()
    const t = setInterval(load, 30000)
    return () => {
      cancelled = true
      clearInterval(t)
    }
  }, [])

  const loading = !data && !error
  const cycles = data?.recent_cycles ?? []
  const s = data?.summary

  return (
    <Panel
      title="Soul 引擎 · 近期活动"
      hint="平台 soul 引擎每跑一轮自治 cycle(产出 → 自检 → 上线尝试)记一行。绿=ship 成功,红=失败。看这里=系统最近在动手做什么、成多少。"
      className={className}
      action={
        s ? (
          <span className="text-[11px] tabular-nums text-ln-tertiary">
            <span className="text-linear-green">{s.ships_success}</span>/{s.cycles_total} ship 成功
          </span>
        ) : undefined
      }
    >
      {loading ? (
        <Shimmer className="h-40 w-full" />
      ) : error ? (
        <EmptyState>soul 活动暂不可用:{error}</EmptyState>
      ) : cycles.length === 0 ? (
        <EmptyState>暂无引擎 cycle 记录。soul timer 当前可能处于 disabled(设计内)。</EmptyState>
      ) : (
        <ol className="relative ml-1 space-y-3 border-l border-[rgba(255,255,255,0.1)] pl-4">
          {cycles.map((c) => {
            const tone = shipTone(c.ship_status)
            return (
              <li key={c.cycle_id} className="relative">
                <span
                  className={`absolute -left-[22px] top-1.5 h-2.5 w-2.5 rounded-full ${tone.dot}`}
                  aria-hidden="true"
                />
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <span className="block truncate font-mono text-[12px] text-ln-secondary">
                      {c.cycle_id}
                    </span>
                    <span className={`text-[11px] ${tone.text}`}>{tone.label}</span>
                    {c.git_sha && (
                      <span className="ml-2 font-mono text-[10px] text-ln-muted">
                        {c.git_sha.slice(0, 7)}
                      </span>
                    )}
                  </div>
                  <span className="shrink-0 text-[10px] tabular-nums text-ln-muted">
                    {relTime(c.created_at)}
                  </span>
                </div>
              </li>
            )
          })}
        </ol>
      )}
    </Panel>
  )
}
