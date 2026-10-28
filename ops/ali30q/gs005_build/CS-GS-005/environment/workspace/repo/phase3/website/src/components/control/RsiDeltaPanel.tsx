/**
 * RsiDeltaPanel · RSI 外部增量(ΔReward)真数据面.
 *
 * 接 GET /api/platform/fde/rsi_delta/{task_uid}(只读·公开)· 形状(curl 实测 2026-06-09):
 *   { success, data: [
 *       { delta_id, benchmark, task_uid, producer_model, n_bare, n_grounded,
 *         bare_mean, grounded_mean, delta_reward, p_value, escapes_noise,
 *         grounding_source, created_at }
 *   ], error }
 * ΔReward = grounded 出题 vs 裸出题在可复现 benchmark 上的客观增量 = RSI 唯一"逃离自指经济"
 * 的外部 fitness。escapes_noise=true(ΔReward>0 且 p<0.05)才计入 PoI。
 * 当前 radix_sort 端点返回空 → 友好空态("尚无外部增量·待 bvh 泛化")。
 * 默认查 radix_sort · 也可输入别的 task_uid。
 */
import { useCallback, useEffect, useState } from 'react'
import { Panel, Shimmer, EmptyState, Stat, relTime } from './PanelKit'

type RsiDelta = {
  delta_id: string
  benchmark: string
  task_uid: string
  producer_model: string | null
  n_bare: number
  n_grounded: number
  bare_mean: number
  grounded_mean: number
  delta_reward: number
  p_value: number | null
  escapes_noise: boolean
  created_at: string | null
}

const DEFAULT_TASK = 'radix_sort'

export default function RsiDeltaPanel({ className = '' }: { className?: string }) {
  const [taskUid, setTaskUid] = useState(DEFAULT_TASK)
  const [query, setQuery] = useState(DEFAULT_TASK)
  const [rows, setRows] = useState<RsiDelta[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async (uid: string) => {
    setRows(null)
    setError(null)
    try {
      const r = await fetch(`/api/platform/fde/rsi_delta/${encodeURIComponent(uid)}`)
      const body = await r.json()
      if (!body.success) throw new Error(body.error || 'rsi_delta error')
      setRows(Array.isArray(body.data) ? (body.data as RsiDelta[]) : [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'load failed')
    }
  }, [])

  useEffect(() => {
    load(taskUid)
  }, [taskUid, load])

  const submit = () => {
    const q = query.trim()
    if (q) setTaskUid(q)
  }

  const loading = !rows && !error

  return (
    <Panel
      title="RSI ΔReward · 外部增量"
      hint="grounded 出题 vs 裸出题在可复现 benchmark 上的客观分差(ΔReward)= RSI 唯一逃离自指经济的外部尺。escapes=true(增量>0 且统计显著)才计入 PoI。"
      className={className}
      action={
        <div className="flex gap-1.5">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') submit()
            }}
            placeholder="task_uid"
            className="w-28 min-w-0 rounded-md border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.03)] px-2 py-1 text-[11px] text-ln-text placeholder:text-ln-muted focus:border-[rgba(255,255,255,0.25)] focus:outline-none"
          />
          <button
            onClick={submit}
            className="rounded-md border border-[rgba(255,255,255,0.15)] bg-[rgba(255,255,255,0.04)] px-2.5 py-1 text-[11px] font-[510] text-ln-text transition hover:bg-[rgba(255,255,255,0.08)]"
          >
            查
          </button>
        </div>
      }
    >
      {loading ? (
        <Shimmer className="h-24 w-full" />
      ) : error ? (
        <EmptyState>ΔReward 暂不可用:{error}</EmptyState>
      ) : (rows?.length ?? 0) === 0 ? (
        <EmptyState>
          <span className="font-mono text-ln-tertiary">{taskUid}</span> 尚无外部增量。
          <br />
          radix 单题 escapes=true 已落库(护城河),bvh 等 deepseek 复跑定泛化后才计入。
        </EmptyState>
      ) : (
        <div className="space-y-3">
          {rows!.map((d) => (
            <div
              key={d.delta_id}
              className={`rounded-md border p-3 ${
                d.escapes_noise
                  ? 'border-linear-green/40 bg-linear-green/5'
                  : 'border-[rgba(255,255,255,0.06)] bg-[rgba(255,255,255,0.015)]'
              }`}
            >
              <div className="mb-2 flex items-center justify-between gap-2">
                <span className="font-mono text-[11px] text-ln-secondary">{d.benchmark}</span>
                <span className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                      d.escapes_noise
                        ? 'bg-linear-green/15 text-linear-green'
                        : 'bg-[rgba(255,255,255,0.06)] text-ln-tertiary'
                    }`}
                  >
                    escapes={d.escapes_noise ? 'true' : 'false'}
                  </span>
                  <span className="text-[10px] tabular-nums text-ln-muted">
                    {relTime(d.created_at)}
                  </span>
                </span>
              </div>
              <Stat
                n={(d.delta_reward >= 0 ? '+' : '') + d.delta_reward.toFixed(4)}
                tone={d.delta_reward > 0 ? 'text-linear-green' : 'text-ln-tertiary'}
                label="ΔReward"
              />
              <div className="mt-2 grid grid-cols-2 gap-1.5 text-[12px] sm:grid-cols-4">
                <Field k="bare" v={d.bare_mean.toFixed(3)} />
                <Field k="grounded" v={d.grounded_mean.toFixed(3)} />
                <Field k="p_value" v={d.p_value == null ? '–' : d.p_value.toFixed(4)} />
                <Field k="N" v={`${d.n_bare}/${d.n_grounded}`} />
              </div>
              {d.producer_model && (
                <p className="mt-2 text-[10px] text-ln-muted">
                  producer · <span className="font-mono">{d.producer_model}</span>
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </Panel>
  )
}

function Field({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex flex-col rounded bg-[rgba(255,255,255,0.02)] px-2 py-1">
      <span className="text-[10px] text-ln-tertiary">{k}</span>
      <span className="tabular-nums text-ln-secondary">{v}</span>
    </div>
  )
}
