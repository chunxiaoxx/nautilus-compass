/**
 * GovernancePanel · 平台治理提案 + 投票写交互(指挥中心 admin 件).
 *
 * 接 GET /api/platform/control-plane/governance/proposals(authFetch · admin 门).
 * 后端形状**不确定**(cloud 治理后端可能分叉)· 防御式解析:
 *   - data 可能是 {proposals:[...]} / 直接 list / summary dict.
 *   - 单条提案常见字段:proposal_id/title/status/votes(尽量解析)· 解析不到就友好
 *     显示原始 JSON 摘要 + "治理数据结构待对齐"提示 · 绝不白屏.
 * 每条提案两个写按钮「批准/驳回」(仅 admin)→ 交回父级走统一 ConfirmDialog →
 *   POST /governance/review {proposal_id, decision} → 结果显示 + 刷新列表.
 * 自身拉取 + 暴露 reload(父级写动作成功后调用刷新).
 */
import { useEffect, useImperativeHandle, useState, forwardRef } from 'react'
import { Panel, Shimmer, EmptyState, Hint } from './PanelKit'

// 防御式解析后的一条提案(字段可能缺 · 都可选).
export type Proposal = {
  proposal_id: string
  title?: string
  status?: string
  votes?: number | string
  /** 解析不到结构化字段时,保留原始对象用于兜底渲染. */
  raw: unknown
}

type ProposalsState = {
  proposals: Proposal[]
  /** 后端返回了内容但无法解析成提案列表 → 原始摘要兜底. */
  fallback: string | null
}

export interface GovernancePanelHandle {
  reload: () => void
}

// 从任意后端形状里尽量提取提案列表(fail-soft · 永不抛).
function parseProposals(data: unknown): ProposalsState {
  // 候选数组:data 本身是 list,或 data.proposals / data.items / data.data 是 list.
  let arr: unknown[] | null = null
  if (Array.isArray(data)) {
    arr = data
  } else if (data && typeof data === 'object') {
    const obj = data as Record<string, unknown>
    for (const key of ['proposals', 'items', 'data', 'results']) {
      if (Array.isArray(obj[key])) {
        arr = obj[key] as unknown[]
        break
      }
    }
  }

  if (arr) {
    const proposals: Proposal[] = []
    arr.forEach((row, i) => {
      if (row && typeof row === 'object') {
        const r = row as Record<string, unknown>
        const idRaw =
          r.proposal_id ?? r.id ?? r.uid ?? r.proposalId ?? `proposal-${i}`
        const title = r.title ?? r.summary ?? r.name ?? r.description
        const status = r.status ?? r.state ?? r.decision
        const votes = r.votes ?? r.vote_count ?? r.voteCount
        proposals.push({
          proposal_id: String(idRaw),
          title: title != null ? String(title) : undefined,
          status: status != null ? String(status) : undefined,
          votes:
            typeof votes === 'number' || typeof votes === 'string'
              ? votes
              : undefined,
          raw: row,
        })
      } else {
        // 非对象元素(如纯字符串)→ 当 id 处理.
        proposals.push({ proposal_id: String(row), raw: row })
      }
    })
    return { proposals, fallback: null }
  }

  // 解析不到列表 → 原始摘要兜底(不白屏).
  if (data == null) return { proposals: [], fallback: null }
  let fallback: string
  try {
    fallback = JSON.stringify(data, null, 2)
  } catch {
    fallback = String(data)
  }
  return { proposals: [], fallback }
}

const GovernancePanel = forwardRef<
  GovernancePanelHandle,
  {
    isAdmin: boolean
    /** 请求确认(交回父级统一 ConfirmDialog). */
    onReview: (proposalId: string, decision: 'approve' | 'reject') => void
    className?: string
  }
>(function GovernancePanel({ isAdmin, onReview, className = '' }, ref) {
  const [state, setState] = useState<ProposalsState | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    try {
      const { tokenUtils } = await import('../../utils/token')
      const token = tokenUtils.get()
      const r = await fetch('/api/platform/control-plane/governance/proposals', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      const body = await r.json()
      if (!body.success) throw new Error(body.error || 'governance error')
      setState(parseProposals(body.data))
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'load failed')
    }
  }

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      if (!cancelled) await load()
    }
    run()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useImperativeHandle(ref, () => ({ reload: load }))

  const loading = !state && !error
  const proposals = state?.proposals ?? []
  const fallback = state?.fallback ?? null

  return (
    <Panel
      title="平台治理 · 提案与投票(admin)"
      hint="平台自治治理提案 = agent/对话框对平台做出的改动议案,经议会投票后路由执行。每条提案下可「批准/驳回」,批准会路由给下游执行方。批准/驳回都会先弹确认框。"
      className={className}
      action={
        proposals.length > 0 ? (
          <span className="text-[11px] tabular-nums text-ln-tertiary">
            {proposals.length} 提案
          </span>
        ) : undefined
      }
    >
      {loading ? (
        <Shimmer className="h-40 w-full" />
      ) : error ? (
        <EmptyState>治理数据暂不可用:{error}</EmptyState>
      ) : proposals.length === 0 && fallback ? (
        <div>
          <Hint className="mb-2 text-[#e2b340]">
            治理数据结构待对齐 · 后端返回了内容但未能解析成提案列表,以下为原始摘要:
          </Hint>
          <pre className="max-h-72 overflow-auto whitespace-pre-wrap break-words rounded-md border border-[rgba(255,255,255,0.06)] bg-[rgba(0,0,0,0.3)] p-3 font-mono text-[11px] leading-relaxed text-ln-secondary">
            {fallback}
          </pre>
        </div>
      ) : proposals.length === 0 ? (
        <EmptyState>暂无治理提案 · 当前没有待议的平台改动议案。</EmptyState>
      ) : (
        <div className="max-h-[28rem] space-y-2.5 overflow-y-auto pr-1">
          {proposals.map((p) => (
            <div
              key={p.proposal_id}
              className="rounded-md border border-[rgba(255,255,255,0.06)] bg-[rgba(255,255,255,0.015)] p-3"
            >
              <div className="mb-1.5 flex items-start justify-between gap-2">
                <span className="font-mono text-[11px] text-ln-tertiary">
                  {p.proposal_id}
                </span>
                <span className="flex shrink-0 items-center gap-2">
                  {p.votes !== undefined && (
                    <span className="text-[10px] tabular-nums text-ln-muted">
                      {p.votes} 票
                    </span>
                  )}
                  {p.status && (
                    <span className="rounded-full bg-[rgba(255,255,255,0.06)] px-2 py-0.5 text-[10px] text-ln-secondary">
                      {p.status}
                    </span>
                  )}
                </span>
              </div>
              {p.title ? (
                <p className="text-[12px] leading-relaxed text-ln-secondary">
                  {p.title}
                </p>
              ) : (
                <p className="text-[11px] italic leading-relaxed text-ln-muted">
                  (无标题 · 仅提案 id)
                </p>
              )}
              {isAdmin && (
                <div className="mt-2.5 flex gap-2">
                  <button
                    onClick={() => onReview(p.proposal_id, 'approve')}
                    className="rounded-md border border-linear-green/40 bg-linear-green/15 px-3 py-1 text-[12px] font-[510] text-linear-green transition hover:bg-linear-green/25"
                  >
                    批准
                  </button>
                  <button
                    onClick={() => onReview(p.proposal_id, 'reject')}
                    className="rounded-md border border-[#eb5757]/40 bg-[rgba(235,87,87,0.12)] px-3 py-1 text-[12px] font-[510] text-[#eb5757] transition hover:bg-[rgba(235,87,87,0.2)]"
                  >
                    驳回
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Panel>
  )
})

export default GovernancePanel
