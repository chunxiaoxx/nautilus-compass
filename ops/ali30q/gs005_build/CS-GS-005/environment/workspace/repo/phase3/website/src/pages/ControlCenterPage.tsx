import { useEffect, useState, useCallback, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import LoopReplay, { type Loop } from '../components/LoopReplay'
import DrillDownModal from '../components/DrillDownModal'
import ConfirmDialog from '../components/ConfirmDialog'
import { tokenUtils } from '../utils/token'
import { Panel, Stat, Shimmer, Hint, EmptyState, relTime } from '../components/control/PanelKit'
import SoulActivityPanel from '../components/control/SoulActivityPanel'
import GroundingFeedPanel from '../components/control/GroundingFeedPanel'
import RsiDeltaPanel from '../components/control/RsiDeltaPanel'
import FleetStatus from '../components/control/FleetStatus'
import GovernancePanel, { type GovernancePanelHandle } from '../components/control/GovernancePanel'
import SystemTopology from '../components/control/SystemTopology'

// 所有 control 端点需登录态(后端 get_current_user)· 统一带 JWT 的 fetch.
function authFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const token = tokenUtils.get()
  return fetch(url, {
    ...init,
    headers: {
      ...(init.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })
}

/**
 * 指挥中心 · /control · 运营/指挥官视角的**统一**控制面 GUI(唯一控制面页).
 *
 * 🔴 融贯改造(原独立 /bridge 已折入此页·不再起第二摊):
 *   - 数据源改吃 canonical 聚合脊柱 /api/platform/control-plane(soul/compass/dmas
 *     + loops + pulse)· 取代原 /api/platform/rsi-fde(后者退为内部子视图).
 *   - 吸收原 /bridge 的:系统脉搏(rsi ΔReward)+ 两条 RSI+FDE 闭环回放(LoopReplay)
 *     + 只读 rerun-probe 按钮(POST /control-plane/rerun-probe · 非鉴权机器 dispatch).
 * 登录门控(ProtectedRoute · App.tsx). Claude/Linear 暗色设计 token(ln- / linear-).
 */

type Verdict = {
  verdict_id: string; task_uid: string; source: string
  overall_pass: boolean; veto_failed: boolean; score: number | null; created_at: string | null
}
// canonical control-plane 聚合脊柱形状(嵌套·只声明用到的字段·后端 fail-soft 可能缺).
type ControlPlane = {
  soul: {
    verdicts: { summary: { total: number; passed: number; pass_rate: number }; recent: Verdict[] }
    rsi_deltas?: { count?: number; rows?: { task_uid?: string; delta_reward?: number; escapes_noise?: boolean }[] }
  }
  compass: {
    poi: { poi_eligible: number; eligible_tasks: string[] }
    recall?: { status?: string }
  }
  dmas: {
    agents: { total: number; active: number; by_status: { status: string; count: number }[] }
    bids: {
      summary: { total: number; processed: number }
      by_type: { event_type: string; count: number }[]
      recent?: { target: string; event_type: string; processed: boolean; created_at: string | null }[]
    }
  }
  loops: Loop[]
  pulse: {
    soul_alive: boolean; today_verdicts: number; dmas_throughput: number
    last_activity_at?: string | null; stale_hours?: number | null; verdicts_today?: number
  }
  generated_at: string
}

type ProbeResult = { escapes_noise?: boolean; delta_reward?: number; p_value?: number }

// drill-down: verdict 详情(含 per-item reason).
type VerdictItem = { id: string; pass: boolean; veto: boolean; reason: string | null }
type VerdictDetail = {
  verdict_id?: string; task_uid?: string; source?: string
  overall_pass?: boolean; veto_failed?: boolean; score?: number | null
  items?: VerdictItem[]
}
// drill-down: agent 基本字段(后端返回任意字段集 · 平铺渲染).
type AgentDetail = Record<string, unknown>

// dispatch 写动作返回形(/dispatch /goal 同形).
type ActionResult = {
  target?: string; action?: string; routed_to?: string
  delivered?: boolean; detail?: string
}

type DispatchTarget = 'soul' | 'compass' | 'agent'
type DrillKind = 'verdict' | 'agent'
// 待确认的写动作(确认框消费 · 所有写动作走同一个 ConfirmDialog).
type PendingAction =
  | { kind: 'goal'; goal: string }
  | { kind: 'dispatch'; target: DispatchTarget; action: string; payload: unknown }
  | { kind: 'review'; proposalId: string; decision: 'approve' | 'reject' }
  | { kind: 'autonomy'; agentId: string; enabled: boolean }
  | { kind: 'execute'; taskId: string }

// 与后端 docstring 同值:radix 裸 vs grounded 6-seed ΔReward(只读重算演示样本).
const PROBE_PAYLOAD = {
  bare: [0.0, 0.26, 0.27, 0.28, 0.0, 0.27],
  grounded: [0.32, 0.36, 0.28, 0.26, 0.0, 0.3],
}

// 渲染单条 ActionResult(dispatch/goal 返回).
function ActionResultView({ result }: { result: ActionResult }) {
  return (
    <div className="mt-3 rounded-md border border-linear-green/30 bg-linear-green/5 p-3 text-[12px]">
      <div className="grid grid-cols-1 gap-1 sm:grid-cols-2">
        {result.routed_to !== undefined && (
          <div className="flex justify-between gap-2">
            <span className="text-ln-tertiary">routed_to</span>
            <span className="font-mono text-ln-secondary">{result.routed_to}</span>
          </div>
        )}
        {result.delivered !== undefined && (
          <div className="flex justify-between gap-2">
            <span className="text-ln-tertiary">delivered</span>
            <span className={result.delivered ? 'text-linear-green' : 'text-[#eb5757]'}>
              {result.delivered ? 'true' : 'false'}
            </span>
          </div>
        )}
      </div>
      {result.detail && (
        <p className="mt-2 whitespace-pre-wrap break-words text-ln-secondary">{result.detail}</p>
      )}
    </div>
  )
}

export default function ControlCenterPage() {
  const { user } = useAuth()
  const [data, setData] = useState<ControlPlane | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [updated, setUpdated] = useState<string>('')

  const [probing, setProbing] = useState(false)
  const [probeResult, setProbeResult] = useState<ProbeResult | null>(null)
  const [probeError, setProbeError] = useState<string | null>(null)

  // Task A — is_admin 显隐(fail-soft → false).
  const [isAdmin, setIsAdmin] = useState(false)

  // Task B — drill-down 弹层.
  const [drillOpen, setDrillOpen] = useState(false)
  const [drillKind, setDrillKind] = useState<DrillKind>('verdict')
  const [drillTitle, setDrillTitle] = useState('')
  const [drillLoading, setDrillLoading] = useState(false)
  const [drillError, setDrillError] = useState<string | null>(null)
  const [verdictDetail, setVerdictDetail] = useState<VerdictDetail | null>(null)
  const [agentDetail, setAgentDetail] = useState<AgentDetail | null>(null)
  const [drillAgentId, setDrillAgentId] = useState<string>('')

  // Task C — 指挥区(goal + dispatch)输入 + 确认 + 结果.
  const [goalText, setGoalText] = useState('')
  const [dispTarget, setDispTarget] = useState<DispatchTarget>('soul')
  const [dispAction, setDispAction] = useState('')
  const [dispPayload, setDispPayload] = useState('')
  const [pending, setPending] = useState<PendingAction | null>(null)
  const [acting, setActing] = useState(false)
  const [actionResult, setActionResult] = useState<ActionResult | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  // 治理板块 ref(写动作成功后刷新提案列表).
  const governanceRef = useRef<GovernancePanelHandle>(null)
  // task execute 输入框.
  const [taskIdInput, setTaskIdInput] = useState('')

  const load = useCallback(async () => {
    try {
      const r = await fetch('/api/platform/control-plane?limit=20')
      const body = await r.json()
      if (!body.success) throw new Error(body.error || 'view error')
      setData(body.data); setError(null)
      setUpdated((body.data.generated_at || '').replace('T', ' ').slice(0, 19))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'load failed')
    }
  }, [])

  useEffect(() => {
    load()
    const t = setInterval(load, 15000) // 15s 脉搏刷新
    return () => clearInterval(t)
  }, [load])

  const runProbe = useCallback(async () => {
    setProbing(true); setProbeError(null); setProbeResult(null)
    try {
      const r = await fetch('/api/platform/control-plane/rerun-probe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(PROBE_PAYLOAD),
      })
      const body = await r.json()
      if (!body.success) throw new Error(body.error || 'probe error')
      setProbeResult(body.data as ProbeResult)
    } catch (e) {
      setProbeError(e instanceof Error ? e.message : 'probe failed')
    } finally {
      setProbing(false)
    }
  }, [])

  // Task A — whoami(mount 一次 · fail-soft).
  useEffect(() => {
    let cancelled = false
    authFetch('/api/platform/control-plane/whoami')
      .then((r) => r.json())
      .then((body) => {
        if (!cancelled) setIsAdmin(Boolean(body?.success && body?.data?.is_admin))
      })
      .catch(() => {
        if (!cancelled) setIsAdmin(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  // Task B — 打开 verdict drill.
  const openVerdict = useCallback(async (verdictId: string) => {
    setDrillKind('verdict'); setDrillTitle(`Verdict · ${verdictId}`)
    setDrillOpen(true); setDrillLoading(true); setDrillError(null)
    setVerdictDetail(null); setAgentDetail(null)
    try {
      const r = await authFetch(`/api/platform/control-plane/verdict/${encodeURIComponent(verdictId)}`)
      const body = await r.json()
      if (!body.success) throw new Error(body.error || 'verdict 未找到')
      setVerdictDetail(body.data as VerdictDetail)
    } catch (e) {
      setDrillError(e instanceof Error ? e.message : 'drill 失败')
    } finally {
      setDrillLoading(false)
    }
  }, [])

  // Task B — 打开 agent drill.
  const openAgent = useCallback(async (agentId: string) => {
    setDrillKind('agent'); setDrillTitle(`Agent · ${agentId}`); setDrillAgentId(agentId)
    setDrillOpen(true); setDrillLoading(true); setDrillError(null)
    setVerdictDetail(null); setAgentDetail(null)
    try {
      const r = await authFetch(`/api/platform/control-plane/agent/${encodeURIComponent(agentId)}`)
      const body = await r.json()
      if (!body.success) throw new Error(body.error || 'agent 未找到')
      setAgentDetail(body.data as AgentDetail)
    } catch (e) {
      setDrillError(e instanceof Error ? e.message : 'drill 失败')
    } finally {
      setDrillLoading(false)
    }
  }, [])

  // Task C — 请求确认(把待执行动作交给 ConfirmDialog).
  const requestGoal = useCallback(() => {
    setActionResult(null); setActionError(null)
    if (!goalText.trim()) { setActionError('goal 不能为空'); return }
    setPending({ kind: 'goal', goal: goalText.trim() })
  }, [goalText])

  const requestDispatch = useCallback(() => {
    setActionResult(null); setActionError(null)
    if (!dispAction.trim()) { setActionError('action 不能为空'); return }
    let payload: unknown = undefined
    if (dispPayload.trim()) {
      try {
        payload = JSON.parse(dispPayload)
      } catch {
        setActionError('payload 不是合法 JSON'); return
      }
    }
    setPending({ kind: 'dispatch', target: dispTarget, action: dispAction.trim(), payload })
  }, [dispTarget, dispAction, dispPayload])

  // 治理审批/驳回 — 请求确认(GovernancePanel 回调).
  const requestReview = useCallback((proposalId: string, decision: 'approve' | 'reject') => {
    setActionResult(null); setActionError(null)
    setPending({ kind: 'review', proposalId, decision })
  }, [])

  // agent autonomy 开/关 — 请求确认(drill 弹层回调).
  const requestAutonomy = useCallback((agentId: string, enabled: boolean) => {
    setActionResult(null); setActionError(null)
    setPending({ kind: 'autonomy', agentId, enabled })
  }, [])

  // task execute — 请求确认(指挥区输入).
  const requestExecute = useCallback(() => {
    setActionResult(null); setActionError(null)
    const id = taskIdInput.trim()
    if (!id) { setActionError('task_id 不能为空'); return }
    setPending({ kind: 'execute', taskId: id })
  }, [taskIdInput])

  // Task C — 确认后执行写动作(所有 kind 统一在此发请求).
  const confirmAction = useCallback(async () => {
    if (!pending) return
    setActing(true); setActionError(null); setActionResult(null)

    // 按 kind 解析 url + body.
    let url: string
    let body: unknown
    switch (pending.kind) {
      case 'goal':
        url = '/api/platform/control-plane/goal'
        body = { goal: pending.goal }
        break
      case 'dispatch':
        url = '/api/platform/control-plane/dispatch'
        body = { target: pending.target, action: pending.action, payload: pending.payload }
        break
      case 'review':
        url = '/api/platform/control-plane/governance/review'
        body = { proposal_id: pending.proposalId, decision: pending.decision }
        break
      case 'autonomy':
        url = `/api/platform/control-plane/agent/${encodeURIComponent(pending.agentId)}/autonomy`
        body = { enabled: pending.enabled }
        break
      case 'execute':
        url = `/api/platform/control-plane/task/${encodeURIComponent(pending.taskId)}/execute`
        body = {}
        break
    }

    const kind = pending.kind
    try {
      const r = await authFetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const resp = await r.json()
      if (!resp.success) throw new Error(resp.error || `${r.status} 操作失败`)
      setActionResult(resp.data as ActionResult)
      setPending(null)
      // 治理写动作成功后刷新提案列表.
      if (kind === 'review') governanceRef.current?.reload()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : '操作失败')
      setPending(null)
    } finally {
      setActing(false)
    }
  }, [pending])

  const loading = !data && !error
  const rsiCount = data?.soul?.rsi_deltas?.count ?? 0
  const loops = data?.loops ?? []
  const recentEvents = (data?.dmas?.bids?.recent ?? []).slice(0, 8)

  return (
    <div className="min-h-screen bg-linear-black py-8 px-4">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Header */}
        <div className="flex items-end justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-3xl font-[560] text-ln-text tracking-[-0.5px]">🐚 指挥中心</h1>
            <p className="text-ln-tertiary text-[13px] mt-1">
              平台 agent-first 自治生态 · 外部 FDE verdict = 唯一逃离自指经济的 fitness
            </p>
          </div>
          <div className="text-right">
            <p className="text-ln-tertiary text-[12px]">{user?.email}</p>
            <p className="text-ln-muted text-[11px]">
              {updated ? `快照 ${updated} UTC` : '加载中…'} · 15s 自动刷新 ·
              <span className={data?.pulse?.soul_alive ? 'text-linear-green' : 'text-[#eb5757]'}>
                {' '}soul {data?.pulse?.soul_alive
                  ? 'alive'
                  : (typeof data?.pulse?.stale_hours === 'number'
                      ? `静默 ${Math.floor((data.pulse.stale_hours || 0) / 24)} 天`
                      : '无数据')}
              </span>
              {data?.pulse?.last_activity_at && (
                <span className="text-ln-muted">
                  {' '}· 最新活动 {String(data.pulse.last_activity_at).replace('T', ' ').slice(0, 16)}
                </span>
              )}
              {' · '}
              <span className={data?.compass?.recall?.status === 'online' ? 'text-linear-green' : 'text-ln-muted'}>
                compass recall {data?.compass?.recall?.status ?? '—'}
              </span>
            </p>
          </div>
        </div>

        {error && (
          <Panel><div className="text-[#eb5757] text-sm">加载失败:{error}</div></Panel>
        )}

        {/* 系统脉搏条 */}
        <div>
          <Hint className="mb-2">
            系统脉搏 · 一行看懂"健不健康":外部验收通过率、RSI 是否产生外部增量、编队活跃度、事件吞吐、可计 PoI 的题数。
          </Hint>
          <div className="grid gap-4 grid-cols-2 lg:grid-cols-5">
            <Panel title="FDE Verdicts · 外部验收">
              {loading ? <Shimmer className="h-9 w-24" /> :
                <Stat n={data!.soul.verdicts.summary.passed} tone="text-linear-green"
                      label={`/ ${data!.soul.verdicts.summary.total} 通过 · ${(data!.soul.verdicts.summary.pass_rate * 100).toFixed(0)}%`} />}
            </Panel>
            <Panel title="RSI ΔReward · 外部增量">
              {loading ? <Shimmer className="h-9 w-24" /> :
                <Stat n={rsiCount} tone={rsiCount > 0 ? 'text-linear-green' : 'text-ln-muted'}
                      label="escapes 测量" />}
            </Panel>
            <Panel title="Agents · 编队">
              {loading ? <Shimmer className="h-9 w-24" /> :
                <Stat n={data!.dmas.agents.active} tone={data!.dmas.agents.active > 0 ? 'text-linear-green' : 'text-ln-muted'}
                      label={`活跃 / ${data!.dmas.agents.total} 总`} />}
            </Panel>
            <Panel title="事件流">
              {loading ? <Shimmer className="h-9 w-24" /> :
                <Stat n={data!.dmas.bids.summary.total} label={`事件 · ${data!.dmas.bids.summary.processed} 已处理`} />}
            </Panel>
            <Panel title="PoI 可计入">
              {loading ? <Shimmer className="h-9 w-24" /> :
                <Stat n={data!.compass.poi.poi_eligible} tone="text-linear-green" label="题通过 → 可计 PoI" />}
            </Panel>
          </div>
        </div>

        {/* 系统拓扑图 · 舰桥 v2 标志性总览(脉搏条下 · 板块上) */}
        <SystemTopology data={data} />

        <div className="grid gap-4 lg:grid-cols-3" id="panel-fleet">
          {/* Verdict 流(双源) */}
          <Panel
            title="FDE Verdict 流 · 一审 fde-capsule-v5 / 二审 kairos-deepseek"
            hint={isAdmin
              ? '每行=一道 FDE 题的外部验收结果。PASS=过 / VETO=触否决项整批拒收 / FAIL=未达标。点任一行看逐条打分理由。'
              : '每行=一道 FDE 题的外部验收结果。PASS=过 / VETO=触否决项整批拒收 / FAIL=未达标。'}
            className="lg:col-span-2"
          >
            {loading ? <Shimmer className="h-48 w-full" /> : (
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="text-ln-tertiary text-left">
                    <th className="font-[450] pb-2">任务</th><th className="font-[450] pb-2">来源</th>
                    <th className="font-[450] pb-2">判定</th><th className="font-[450] pb-2 text-right">分</th>
                  </tr>
                </thead>
                <tbody>
                  {data!.soul.verdicts.recent.map((v) => (
                    <tr
                      key={v.verdict_id}
                      onClick={isAdmin ? () => openVerdict(v.verdict_id) : undefined}
                      className={`border-t border-[rgba(255,255,255,0.05)] ${
                        isAdmin ? 'cursor-pointer transition hover:bg-[rgba(255,255,255,0.03)]' : ''
                      }`}
                    >
                      <td className="py-1.5 text-ln-secondary">
                        {v.task_uid}
                        {isAdmin && <span className="ml-1.5 text-[10px] text-ln-muted">↳</span>}
                      </td>
                      <td className="py-1.5 text-ln-tertiary font-mono text-[11px]">{v.source}</td>
                      <td className="py-1.5">
                        <span className={`px-2 py-0.5 rounded-full text-[11px] ${v.overall_pass
                          ? 'bg-[rgba(39,166,68,0.15)] text-linear-green'
                          : 'bg-[rgba(235,87,87,0.15)] text-[#eb5757]'}`}>
                          {v.overall_pass ? 'PASS' : (v.veto_failed ? 'VETO' : 'FAIL')}
                        </span>
                      </td>
                      <td className="py-1.5 text-right text-ln-tertiary tabular-nums">
                        {v.score == null ? '–' : `${(v.score * 100).toFixed(0)}%`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Panel>

          {/* 编队 + 事件 */}
          <div className="space-y-4">
            <Panel title="编队 · 生存状态">
              {loading ? <Shimmer className="h-32 w-full" /> : (
                <FleetStatus
                  byStatus={data!.dmas.agents.by_status}
                  total={data!.dmas.agents.total}
                  isAdmin={isAdmin}
                  onLookup={openAgent}
                />
              )}
            </Panel>
            <Panel
              title="事件类型 · 分布"
              hint="agent 之间发生了什么(完成赏金 / 发布内容 / 结算审计)。计数=各类事件累计条数。"
            >
              {loading ? <Shimmer className="h-24 w-full" /> : (
                <div className="space-y-2">
                  {data!.dmas.bids.by_type.map((e) => {
                    const denom = data!.dmas.bids.summary.total || 1
                    const pct = Math.round((e.count / denom) * 100)
                    return (
                      <div key={e.event_type}>
                        <div className="mb-1 flex justify-between text-[12px]">
                          <span className="text-ln-secondary font-mono text-[11px]">{e.event_type}</span>
                          <span className="text-ln-tertiary tabular-nums">{e.count} · {pct}%</span>
                        </div>
                        <div className="h-1.5 w-full overflow-hidden rounded-full bg-[rgba(255,255,255,0.05)]">
                          <div className="h-full rounded-full bg-linear-brand" style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </Panel>
            <Panel
              title="近期事件流"
              hint="最近发生的事件(倒序)。⏳=待处理 / ✓=已处理。"
            >
              {loading ? <Shimmer className="h-24 w-full" /> : (recentEvents.length === 0 ? (
                <EmptyState>暂无近期事件。</EmptyState>
              ) : (
                <ul className="space-y-1.5">
                  {recentEvents.map((ev, i) => (
                    <li key={`${ev.event_type}-${ev.created_at}-${i}`} className="flex items-center justify-between gap-2 text-[12px]">
                      <span className="flex min-w-0 items-center gap-1.5">
                        <span aria-hidden="true">{ev.processed ? '✓' : '⏳'}</span>
                        <span className="truncate font-mono text-[11px] text-ln-secondary">{ev.event_type}</span>
                        <span className="truncate text-[10px] text-ln-muted">→ {ev.target}</span>
                      </span>
                      <span className="shrink-0 text-[10px] tabular-nums text-ln-muted">{relTime(ev.created_at)}</span>
                    </li>
                  ))}
                </ul>
              ))}
            </Panel>
          </div>
        </div>

        {/* Soul 引擎活动 + RSI ΔReward(新板块) */}
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2" id="panel-soul">
            <SoulActivityPanel />
          </div>
          <div id="panel-rsi">
            <RsiDeltaPanel />
          </div>
        </div>

        {/* Grounding feed · RSI 环避坑语料(新板块·高价值真数据) */}
        <GroundingFeedPanel />

        {/* 平台治理 · 提案与投票写交互(admin only · 端点 admin 门) */}
        {isAdmin && (
          <GovernancePanel ref={governanceRef} isAdmin={isAdmin} onReview={requestReview} />
        )}

        {/* RSI+FDE 闭环回放(原 /bridge·折入) */}
        {!loading && loops.length > 0 && (
          <div>
            <div className="flex items-end justify-between flex-wrap gap-3 mb-1">
              <h2 className="text-[16px] font-[560] text-ln-text tracking-[-0.3px]">闭环回放 · RSI+FDE</h2>
              <div className="flex items-center gap-3">
                {probeResult && (
                  <span className="text-[12px] text-ln-tertiary tabular-nums">
                    escapes=<span className={probeResult.escapes_noise ? 'text-linear-green' : 'text-ln-secondary'}>
                      {probeResult.escapes_noise ? 'true' : 'false'}</span>
                    {' '}· ΔReward {typeof probeResult.delta_reward === 'number' ? probeResult.delta_reward.toFixed(4) : '—'}
                    {' '}· p {typeof probeResult.p_value === 'number' ? probeResult.p_value.toFixed(4) : '—'}
                  </span>
                )}
                {probeError && <span className="text-[12px] text-[#eb5757]">probe 失败:{probeError}</span>}
                <button
                  onClick={runProbe}
                  disabled={probing}
                  className="rounded-md border border-[rgba(255,255,255,0.15)] bg-[rgba(255,255,255,0.04)] px-3 py-1.5 text-[13px] font-[510] text-ln-text transition hover:bg-[rgba(255,255,255,0.08)] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {probing ? '运行中…' : '重跑 grounding probe'}
                </button>
              </div>
            </div>
            <Hint className="mb-4">
              一条端到端闭环的逐步回放(出题 → 验收 → 增量度量)。绿色里程碑节点=该步达成关键外部信号(escapes 噪声 / 买方题过 QC)。
            </Hint>
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {loops.map((loop) => <LoopReplay key={loop.loop_id} loop={loop} />)}
            </div>
          </div>
        )}

        {/* PoI 题 */}
        <div id="panel-poi">
        <Panel
          title="PoI 可计入题 · 平台侧推导(通过的 FDE verdict · 不读 compass 内部账本)"
          hint="PoI(Proof of Improvement)= 可计入信用的题。平台只凭通过的外部 FDE verdict 推导,不读 compass 内部账本,保持口径诚实。"
          action={
            <span className="text-[11px] tabular-nums text-ln-tertiary">
              {data?.compass?.poi?.poi_eligible ?? 0} 题
            </span>
          }
        >
          {loading ? <Shimmer className="h-6 w-full" /> : (
            (data!.compass.poi.eligible_tasks.length === 0 ? (
              <EmptyState>暂无可计入 PoI 的题。</EmptyState>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {data!.compass.poi.eligible_tasks.map((t) => (
                  <span
                    key={t}
                    className="rounded-md border border-linear-green/25 bg-linear-green/5 px-2 py-0.5 font-mono text-[11px] text-ln-secondary"
                  >
                    {t}
                  </span>
                ))}
              </div>
            ))
          )}
        </Panel>
        </div>

        {/* 指挥区 · admin only(写动作必经确认框) */}
        {isAdmin && (
          <Panel
            title="指挥区 · 派 goal / dispatch(admin · 每个写动作必经确认)"
            hint="向 soul 派目标(goal)或向任一对话框派机器指令(dispatch)。仅 admin 可见;每个写动作都会先弹确认框,确认后才真正发出。"
          >
            <div className="grid gap-6 lg:grid-cols-2">
              {/* 派 goal */}
              <div className="space-y-2">
                <h4 className="text-[13px] font-[510] text-ln-secondary">派 goal → soul</h4>
                <textarea
                  value={goalText}
                  onChange={(e) => setGoalText(e.target.value)}
                  placeholder="输入要派给 soul 的 goal…"
                  rows={3}
                  className="w-full resize-y rounded-md border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.03)] px-3 py-2 text-[13px] text-ln-text placeholder:text-ln-muted focus:border-[rgba(255,255,255,0.25)] focus:outline-none"
                />
                <button
                  onClick={requestGoal}
                  className="rounded-md border border-[rgba(255,255,255,0.15)] bg-[rgba(255,255,255,0.04)] px-3 py-1.5 text-[13px] font-[510] text-ln-text transition hover:bg-[rgba(255,255,255,0.08)]"
                >
                  派给 soul
                </button>
              </div>

              {/* 通用 dispatch */}
              <div className="space-y-2">
                <h4 className="text-[13px] font-[510] text-ln-secondary">通用 dispatch</h4>
                <div className="flex gap-2">
                  <select
                    value={dispTarget}
                    onChange={(e) => setDispTarget(e.target.value as DispatchTarget)}
                    className="rounded-md border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.03)] px-2.5 py-1.5 text-[13px] text-ln-text focus:border-[rgba(255,255,255,0.25)] focus:outline-none"
                  >
                    <option value="soul">soul</option>
                    <option value="compass">compass</option>
                    <option value="agent">agent</option>
                  </select>
                  <input
                    value={dispAction}
                    onChange={(e) => setDispAction(e.target.value)}
                    placeholder="action"
                    className="min-w-0 flex-1 rounded-md border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.03)] px-2.5 py-1.5 text-[13px] text-ln-text placeholder:text-ln-muted focus:border-[rgba(255,255,255,0.25)] focus:outline-none"
                  />
                </div>
                <textarea
                  value={dispPayload}
                  onChange={(e) => setDispPayload(e.target.value)}
                  placeholder='payload(可选 JSON · 如 {"key":"value"})'
                  rows={2}
                  className="w-full resize-y rounded-md border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.03)] px-3 py-2 font-mono text-[12px] text-ln-text placeholder:text-ln-muted focus:border-[rgba(255,255,255,0.25)] focus:outline-none"
                />
                <button
                  onClick={requestDispatch}
                  className="rounded-md border border-[rgba(255,255,255,0.15)] bg-[rgba(255,255,255,0.04)] px-3 py-1.5 text-[13px] font-[510] text-ln-text transition hover:bg-[rgba(255,255,255,0.08)]"
                >
                  派发
                </button>
              </div>
            </div>

            {/* 执行任务(task execute) */}
            <div className="mt-6 space-y-2 border-t border-[rgba(255,255,255,0.06)] pt-4">
              <h4 className="text-[13px] font-[510] text-ln-secondary">执行任务 · task execute</h4>
              <Hint>输入 task_id 触发该任务执行(机器派单)。确认后 POST /task/&#123;id&#125;/execute。</Hint>
              <div className="flex gap-2">
                <input
                  value={taskIdInput}
                  onChange={(e) => setTaskIdInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') requestExecute() }}
                  placeholder="task_id"
                  className="min-w-0 flex-1 rounded-md border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.03)] px-2.5 py-1.5 text-[13px] text-ln-text placeholder:text-ln-muted focus:border-[rgba(255,255,255,0.25)] focus:outline-none"
                />
                <button
                  onClick={requestExecute}
                  className="rounded-md border border-[rgba(255,255,255,0.15)] bg-[rgba(255,255,255,0.04)] px-3 py-1.5 text-[13px] font-[510] text-ln-text transition hover:bg-[rgba(255,255,255,0.08)]"
                >
                  执行
                </button>
              </div>
            </div>

            {actionError && (
              <div className="mt-3 text-[13px] text-[#eb5757]">操作失败:{actionError}</div>
            )}
            {actionResult && <ActionResultView result={actionResult} />}
          </Panel>
        )}

        <p className="text-ln-muted text-[11px] text-center pt-2">
          唯一控制面 · 数据源 <code className="text-ln-tertiary">/api/platform/control-plane</code>(canonical 聚合脊柱) ·
          rerun-probe = 只读度量 · 机器控制 dispatch 走 <code className="text-ln-tertiary">/api/platform/dispatch</code>(鉴权)
        </p>
      </div>

      {/* Task B — drill-down 弹层 */}
      <DrillDownModal
        open={drillOpen}
        title={drillTitle}
        loading={drillLoading}
        error={drillError}
        onClose={() => setDrillOpen(false)}
      >
        {drillKind === 'verdict' && verdictDetail && (
          <div className="space-y-3 text-[13px]">
            <div className="grid grid-cols-2 gap-2">
              <div className="flex justify-between gap-2">
                <span className="text-ln-tertiary">task_uid</span>
                <span className="text-ln-secondary">{verdictDetail.task_uid ?? '–'}</span>
              </div>
              <div className="flex justify-between gap-2">
                <span className="text-ln-tertiary">source</span>
                <span className="font-mono text-[11px] text-ln-secondary">{verdictDetail.source ?? '–'}</span>
              </div>
              <div className="flex justify-between gap-2">
                <span className="text-ln-tertiary">overall</span>
                <span className={verdictDetail.overall_pass ? 'text-linear-green' : 'text-[#eb5757]'}>
                  {verdictDetail.overall_pass ? 'PASS' : (verdictDetail.veto_failed ? 'VETO' : 'FAIL')}
                </span>
              </div>
              <div className="flex justify-between gap-2">
                <span className="text-ln-tertiary">score</span>
                <span className="tabular-nums text-ln-secondary">
                  {verdictDetail.score == null ? '–' : `${(verdictDetail.score * 100).toFixed(0)}%`}
                </span>
              </div>
            </div>
            <div>
              <h4 className="mb-2 text-[12px] font-[510] uppercase tracking-[0.4px] text-ln-tertiary">
                打分项 · {verdictDetail.items?.length ?? 0}
              </h4>
              <div className="space-y-2">
                {(verdictDetail.items ?? []).map((it) => (
                  <div
                    key={it.id}
                    className={`rounded-md border p-2.5 ${
                      it.pass
                        ? 'border-[rgba(255,255,255,0.06)] bg-[rgba(255,255,255,0.015)]'
                        : 'border-[#eb5757]/30 bg-[rgba(235,87,87,0.06)]'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono text-[11px] text-ln-tertiary">{it.id}</span>
                      <span className="flex gap-1.5">
                        <span className={`rounded-full px-2 py-0.5 text-[10px] ${
                          it.pass ? 'bg-linear-green/15 text-linear-green' : 'bg-[rgba(235,87,87,0.15)] text-[#eb5757]'
                        }`}>
                          {it.pass ? 'pass' : 'fail'}
                        </span>
                        {it.veto && (
                          <span className="rounded-full bg-[rgba(235,87,87,0.2)] px-2 py-0.5 text-[10px] font-semibold text-[#eb5757]">
                            否决
                          </span>
                        )}
                      </span>
                    </div>
                    {it.reason && (
                      <p className={`mt-1.5 leading-relaxed ${it.pass ? 'text-ln-secondary' : 'font-[510] text-[#eb5757]'}`}>
                        {it.reason}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {drillKind === 'agent' && agentDetail && (
          <div className="space-y-4">
            <dl className="grid grid-cols-1 gap-1.5 text-[13px] sm:grid-cols-2">
              {Object.entries(agentDetail).map(([k, v]) => (
                <div key={k} className="flex justify-between gap-2 rounded bg-[rgba(255,255,255,0.02)] px-2.5 py-1.5">
                  <dt className="font-mono text-[11px] text-ln-tertiary">{k}</dt>
                  <dd className="break-all text-right text-ln-secondary">
                    {v === null || v === undefined ? '–' : typeof v === 'object' ? JSON.stringify(v) : String(v)}
                  </dd>
                </div>
              ))}
            </dl>
            {isAdmin && drillAgentId && (
              <div className="border-t border-[rgba(255,255,255,0.06)] pt-3">
                <h4 className="mb-1 text-[12px] font-[510] uppercase tracking-[0.4px] text-ln-tertiary">
                  Autonomy 控制
                </h4>
                <Hint className="mb-2">
                  开启/关闭该 agent 的自治(autonomy)。确认后 POST /agent/{drillAgentId}/autonomy。
                </Hint>
                <div className="flex gap-2">
                  <button
                    onClick={() => requestAutonomy(drillAgentId, true)}
                    className="rounded-md border border-linear-green/40 bg-linear-green/15 px-3 py-1.5 text-[12px] font-[510] text-linear-green transition hover:bg-linear-green/25"
                  >
                    开启 autonomy
                  </button>
                  <button
                    onClick={() => requestAutonomy(drillAgentId, false)}
                    className="rounded-md border border-[#eb5757]/40 bg-[rgba(235,87,87,0.12)] px-3 py-1.5 text-[12px] font-[510] text-[#eb5757] transition hover:bg-[rgba(235,87,87,0.2)]"
                  >
                    关闭 autonomy
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </DrillDownModal>

      {/* Task C — 写动作确认框 */}
      <ConfirmDialog
        open={pending !== null}
        title="确认派发"
        busy={acting}
        onCancel={() => setPending(null)}
        onConfirm={confirmAction}
        detail={
          pending?.kind === 'goal' ? (
            <div>
              <p className="mb-1.5">将 <span className="font-[560] text-ln-text">POST /goal</span> 给 soul:</p>
              <pre className="whitespace-pre-wrap break-words rounded bg-[rgba(0,0,0,0.3)] p-2 font-mono text-[12px] text-ln-secondary">
                {pending.goal}
              </pre>
            </div>
          ) : pending?.kind === 'dispatch' ? (
            <div>
              <p className="mb-1.5">
                将 <span className="font-[560] text-ln-text">POST /dispatch</span> →
                target=<span className="font-mono text-ln-text">{pending.target}</span>,
                action=<span className="font-mono text-ln-text">{pending.action}</span>
              </p>
              {pending.payload !== undefined && (
                <pre className="whitespace-pre-wrap break-words rounded bg-[rgba(0,0,0,0.3)] p-2 font-mono text-[12px] text-ln-secondary">
                  {JSON.stringify(pending.payload, null, 2)}
                </pre>
              )}
            </div>
          ) : pending?.kind === 'review' ? (
            <div>
              <p className="mb-1.5">
                将 <span className="font-[560] text-ln-text">POST /governance/review</span> →
              </p>
              <p>
                proposal_id=<span className="font-mono text-ln-text">{pending.proposalId}</span>
              </p>
              <p>
                decision=
                <span className={`font-mono font-[560] ${pending.decision === 'approve' ? 'text-linear-green' : 'text-[#eb5757]'}`}>
                  {pending.decision === 'approve' ? 'approve(批准)' : 'reject(驳回)'}
                </span>
              </p>
            </div>
          ) : pending?.kind === 'autonomy' ? (
            <div>
              <p className="mb-1.5">
                将 <span className="font-[560] text-ln-text">POST /agent/{pending.agentId}/autonomy</span> →
              </p>
              <p>
                enabled=
                <span className={`font-mono font-[560] ${pending.enabled ? 'text-linear-green' : 'text-[#eb5757]'}`}>
                  {pending.enabled ? 'true(开启自治)' : 'false(关闭自治)'}
                </span>
              </p>
            </div>
          ) : pending?.kind === 'execute' ? (
            <div>
              <p className="mb-1.5">
                将 <span className="font-[560] text-ln-text">POST /task/{pending.taskId}/execute</span> 触发执行:
              </p>
              <pre className="whitespace-pre-wrap break-words rounded bg-[rgba(0,0,0,0.3)] p-2 font-mono text-[12px] text-ln-secondary">
                task_id = {pending.taskId}
              </pre>
            </div>
          ) : null
        }
      />
    </div>
  )
}
