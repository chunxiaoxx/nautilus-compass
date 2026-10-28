/**
 * GroundingFeedPanel · RSI 环的"避坑语料"feed(高价值真数据).
 *
 * 接 GET /api/platform/fde/grounding(只读·公开)· 形状(curl 实测 2026-06-09):
 *   { success, data: [
 *       { reason, task_uid, checklist_uid, item_id, veto, source, score, created_at }
 *   ], error }
 * 每条 = 一道 FDE 题被打回的具体原因(per-item fail-reason)· 这是 RSI grounded-retrieval
 * 喂给 producer 的真实"别再踩"语料。按 task_uid 分组、reason 高亮、veto 项加红标。
 * 自身拉取 · fail-soft 空态。
 */
import { useEffect, useMemo, useState } from 'react'
import { Panel, Shimmer, EmptyState, relTime } from './PanelKit'

type GroundingItem = {
  reason: string
  task_uid: string | null
  checklist_uid: string | null
  item_id: string | null
  veto: boolean
  source: string | null
  score: number | null
  created_at: string | null
}

export default function GroundingFeedPanel({ className = '' }: { className?: string }) {
  const [items, setItems] = useState<GroundingItem[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const r = await fetch('/api/platform/fde/grounding?limit=40')
        const body = await r.json()
        if (!body.success) throw new Error(body.error || 'grounding error')
        if (!cancelled) {
          setItems(Array.isArray(body.data) ? (body.data as GroundingItem[]) : [])
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

  // 按 task_uid 分组(保持后端的近期优先顺序).
  const groups = useMemo(() => {
    const order: string[] = []
    const map = new Map<string, GroundingItem[]>()
    for (const it of items ?? []) {
      const key = it.task_uid || '(未知题)'
      if (!map.has(key)) {
        map.set(key, [])
        order.push(key)
      }
      map.get(key)!.push(it)
    }
    return order.map((k) => ({ task_uid: k, items: map.get(k)! }))
  }, [items])

  const loading = !items && !error
  const total = items?.length ?? 0
  const vetoCount = (items ?? []).filter((i) => i.veto).length

  return (
    <Panel
      title="Grounding Feed · 避坑语料(RSI 环输入)"
      hint="FDE 题被打回的每一条具体原因。RSI grounded-retrieval 把这些'别再踩'喂回出题 producer,让下一轮更不容易翻同样的错。红=否决级(整批拒收)规则。"
      className={className}
      action={
        total > 0 ? (
          <span className="text-[11px] tabular-nums text-ln-tertiary">
            {total} 条 · <span className="text-[#eb5757]">{vetoCount}</span> 否决
          </span>
        ) : undefined
      }
    >
      {loading ? (
        <Shimmer className="h-40 w-full" />
      ) : error ? (
        <EmptyState>grounding feed 暂不可用:{error}</EmptyState>
      ) : total === 0 ? (
        <EmptyState>暂无打回记录 · 近期 FDE 题全部通过,无避坑语料产生。</EmptyState>
      ) : (
        <div className="max-h-[28rem] space-y-4 overflow-y-auto pr-1">
          {groups.map((g) => (
            <div key={g.task_uid}>
              <div className="mb-1.5 flex items-center gap-2">
                <span className="font-mono text-[11px] text-ln-secondary">{g.task_uid}</span>
                <span className="text-[10px] text-ln-muted">{g.items.length} 条打回</span>
              </div>
              <div className="space-y-1.5">
                {g.items.map((it, idx) => (
                  <div
                    key={`${it.item_id ?? 'x'}-${idx}`}
                    className={`rounded-md border p-2.5 ${
                      it.veto
                        ? 'border-[#eb5757]/40 bg-[rgba(235,87,87,0.07)]'
                        : 'border-[rgba(255,255,255,0.06)] bg-[rgba(255,255,255,0.015)]'
                    }`}
                  >
                    <div className="mb-1 flex items-center justify-between gap-2">
                      <span className="flex items-center gap-1.5">
                        {it.item_id && (
                          <span className="font-mono text-[10px] text-ln-tertiary">
                            {it.item_id}
                          </span>
                        )}
                        {it.veto && (
                          <span className="rounded-full bg-[rgba(235,87,87,0.2)] px-1.5 py-0.5 text-[9px] font-semibold text-[#eb5757]">
                            否决
                          </span>
                        )}
                        {it.source && (
                          <span className="font-mono text-[10px] text-ln-muted">{it.source}</span>
                        )}
                      </span>
                      <span className="shrink-0 text-[10px] tabular-nums text-ln-muted">
                        {relTime(it.created_at)}
                      </span>
                    </div>
                    <p
                      className={`text-[12px] leading-relaxed ${
                        it.veto ? 'text-[#f0a0a0]' : 'text-ln-secondary'
                      }`}
                    >
                      {it.reason || '(无原因文本)'}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </Panel>
  )
}
