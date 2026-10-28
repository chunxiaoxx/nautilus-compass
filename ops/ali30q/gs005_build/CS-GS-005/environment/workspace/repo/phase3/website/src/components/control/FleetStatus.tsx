/**
 * FleetStatus · 编队生存状态(by_status)更直观渲染.
 *
 * 数据来自 control-plane 聚合(dmas.agents.by_status: [{status, count}])· 不自取.
 * 把裸 "status: count" 列表升级为:状态色点 + 标签 + 占比条 + 计数,一眼看懂编队构成.
 * admin 时附 agent_id 查询入口(原 AgentLookup 行为保留).
 */
import { useState } from 'react'
import { Hint } from './PanelKit'

type StatusRow = { status: string; count: number }

// 生存状态 → 色 + 中文标签(未知状态 fail-soft 走默认灰).
const STATUS_META: Record<string, { color: string; label: string }> = {
  alive: { color: '#27a644', label: '存活' },
  active: { color: '#10b981', label: '活跃' },
  inactive: { color: '#8a8f98', label: '不活跃' },
  suspended: { color: '#e2b340', label: '暂停' },
  dead: { color: '#eb5757', label: '死亡' },
  archived: { color: '#62666d', label: '归档' },
}

function meta(status: string) {
  return STATUS_META[status] || { color: '#62666d', label: status }
}

export default function FleetStatus({
  byStatus,
  total,
  isAdmin,
  onLookup,
}: {
  byStatus: StatusRow[]
  total: number
  isAdmin: boolean
  onLookup: (id: string) => void
}) {
  const [id, setId] = useState('')
  const denom = total > 0 ? total : byStatus.reduce((a, r) => a + r.count, 0) || 1

  const submit = () => {
    if (id.trim()) onLookup(id.trim())
  }

  return (
    <div>
      <Hint className="mb-3">
        编队按生存状态分布。存活/活跃=在干活,死亡/归档=已淘汰退场。条越长该状态占比越大。
      </Hint>
      <div className="space-y-2.5">
        {byStatus.map((s) => {
          const m = meta(s.status)
          const pct = Math.round((s.count / denom) * 100)
          return (
            <div key={s.status}>
              <div className="mb-1 flex items-center justify-between text-[12px]">
                <span className="flex items-center gap-2">
                  <span
                    className="inline-block h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: m.color }}
                    aria-hidden="true"
                  />
                  <span className="text-ln-secondary">{m.label}</span>
                  <span className="font-mono text-[10px] text-ln-muted">{s.status}</span>
                </span>
                <span className="tabular-nums text-ln-tertiary">
                  {s.count} <span className="text-ln-muted">· {pct}%</span>
                </span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-[rgba(255,255,255,0.05)]">
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${pct}%`, backgroundColor: m.color }}
                />
              </div>
            </div>
          )
        })}
      </div>

      {isAdmin && (
        <div className="mt-4 border-t border-[rgba(255,255,255,0.06)] pt-3">
          <label className="mb-1.5 block text-[11px] text-ln-tertiary">按 agent_id 查详情</label>
          <div className="flex gap-2">
            <input
              value={id}
              onChange={(e) => setId(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') submit()
              }}
              placeholder="agent_id"
              className="min-w-0 flex-1 rounded-md border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.03)] px-2.5 py-1.5 text-[13px] text-ln-text placeholder:text-ln-muted focus:border-[rgba(255,255,255,0.25)] focus:outline-none"
            />
            <button
              onClick={submit}
              className="rounded-md border border-[rgba(255,255,255,0.15)] bg-[rgba(255,255,255,0.04)] px-3 py-1.5 text-[13px] font-[510] text-ln-text transition hover:bg-[rgba(255,255,255,0.08)]"
            >
              查
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
