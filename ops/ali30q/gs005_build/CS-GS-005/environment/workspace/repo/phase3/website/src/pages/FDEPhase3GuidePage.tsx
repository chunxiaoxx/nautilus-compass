import { useEffect, useState, useCallback, type FormEvent } from 'react'
import { PageShell, Panel, Badge } from '../components/ui/linear'

const actorCards = [
  ['运营/PM', '建卡、补齐必填、处理 pending', '保持流水线持续转动'],
  ['外部专家', '按 task_uid 写提交稿', '只处理自己的行，不改主线字段'],
  ['QC', '复核+反馈+通过/打回', '只改事实项，不改 task_uid'],
  ['Ops', '处理失败任务、外部验收、回滚', '把异常变成人工决策输入'],
]

const lifecycle = [
  ['S1 建卡', '状态 open'],
  ['S2 领取', '状态 claimed'],
  ['S3 提交', '状态 produced'],
  ['S4 外部验收', '状态 settled'],
]

const requiredFields = [
  ['S1（出题）', 'task_uid / title / description / expert_id/open_id/assignee'],
  ['S2（交互）', 'task_uid / output / agent_id'],
  ['S3（结算）', 'task_uid / verdict_id / external_verified'],
]

type TeamRole = 'PM' | 'EXPERT' | 'OPS'

const roleOptions: { label: string; value: TeamRole }[] = [
  { label: 'PM', value: 'PM' },
  { label: '外部专家', value: 'EXPERT' },
  { label: 'Ops', value: 'OPS' },
]

const roleQuickActionGuide: Record<TeamRole, Array<[string, string]>> = {
  PM: [
    ['建卡', '模板选好后执行建卡'],
    ['认领', '认领 open 任务并开始跟进'],
  ],
  EXPERT: [
    ['认领', '选 open 任务并认领'],
    ['提交', '选 claimed 任务，用固定输出模板提交'],
  ],
  OPS: [
    ['验收', '查 verdict 并 external-verify'],
    ['异常', '打开 pending 区处理失败'],
  ],
}

function getRoleGuide(role: TeamRole) {
  return roleQuickActionGuide[role]
}

const expertRules = [
  '只读、只改 task_uid 相关字段。',
  '同一任务只允许一次状态链：open -> claimed -> produced -> settled。',
  '收到 QC 反馈仅回改正文后重新提交。',
]

const externalMsg = `【FDE 三期统一口径】
你只处理一条任务线：
1) 先确认 task_uid 与状态。
2) 仅在该行补齐最小字段，不跨行改动。
3) pending 时，优先做 page 给出的建议动作；不能解决则升 Ops。`

const titleTemplates = [
  'FDE 出题任务（S1）',
  '外部专家交互题（S2）',
  '质检复核任务（S3）',
  '复用任务池题目',
]

const descriptionTemplates = [
  '请产出可复核答案，包含输入、推理过程与最终结论。',
  '请按模板输出：题干、标准答案、评分依据。',
  '请给出简洁可解释的交付结果并附可复核证据。',
  '请补齐 task_uid 与主任务的关联字段，不改主线其他字段。',
]

const agentIdOptions = [
  'expert-01',
  'expert-02',
  'ops-01',
  'qc-01',
]

const verifierSourceOptions = [
  'ops-verify-01',
  'ops-verify-02',
  'soul-audit-01',
]

const reportOutputPresets = [
  {
    label: '标准交付',
    value: JSON.stringify(
      {
        text: '交付内容：\n1. 题目要点\n2. 关键证据\n3. 输出结论',
        artifacts: { files: [], notes: '可补充来源与证据链接' },
      },
      null,
      2,
    ),
  },
  {
    label: '简明交付',
    value: JSON.stringify({
      text: '交付结论：\n- 关键点：\n- 风险提示：\n- 建议动作：',
    }, null, 2),
  },
  { label: '空内容（只推进状态）', value: '' },
]

type ConvergenceResponse = {
  success: boolean
  data: {
    external_verified: { total: number; last_7d: number }
    income: { total: number; delta_7d: number }
    producer_autonomy: { autonomous_verified: number; verified_total: number; ratio: number; note: string }
    settle_integrity: { settled_total: number; externally_backed: number; ratio: number }
    delivery_progress: { delivered: number | null; target: number; note: string }
    generated_at: string
  }
}

type FdeTask = {
  task_uid: string
  title: string
  status: string
  claimed_by: string | null
  claimed_at: string | null
  reported_at: string | null
  created_at: string | null
  output: unknown
  verdict: {
    overall_pass: boolean
    veto_failed: boolean
    score: number
    source: string
  } | null
}

type FdeTasksResponse = {
  success: boolean
  data: {
    tasks: FdeTask[]
    summary: {
      open: number
      claimed: number
      produced: number
      settled: number
      dispatched: number
    }
  }
}

type AttentionItem = {
  id: number
  task_uid: string | null
  stage: string
  code: string
  title: string
  detail: string
  severity: string
  suggested_actions: string[]
  created_at: string | null
}

type AttentionResponse = {
  success: boolean
  data: { items: AttentionItem[]; summary: { count: number; pending: number } }
}

function shortTime(ts: string | null) {
  if (!ts) return '—'
  return String(ts).replace('T', ' ').slice(0, 16)
}

type ApiEnvelope<T> = {
  success: boolean
  data: T
  error: string | null
}

function statusClass(status: string) {
  if (status === 'open') return 'text-[#f2994a]'
  if (status === 'claimed') return 'text-[#27a644]'
  if (status === 'produced') return 'text-[#2f80ed]'
  if (status === 'settled') return 'text-[#6fcf97]'
  return 'text-[#e6e6e6]'
}

export default function FDEPhase3GuidePage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [roleMode, setRoleMode] = useState<TeamRole>('PM')
  const [convergence, setConvergence] = useState<ConvergenceResponse['data'] | null>(null)
  const [tasks, setTasks] = useState<FdeTask[]>([])
  const [summary, setSummary] = useState<FdeTasksResponse['data']['summary'] | null>(null)
  const [attention, setAttention] = useState<AttentionResponse['data'] | null>(null)
  const [attentionHint, setAttentionHint] = useState('')
  const [actionLoading, setActionLoading] = useState('')
  const [actionMessage, setActionMessage] = useState('')
  const [dispatchTaskUid, setDispatchTaskUid] = useState('')
  const [dispatchTitleTemplateIdx, setDispatchTitleTemplateIdx] = useState(0)
  const [dispatchDescriptionTemplateIdx, setDispatchDescriptionTemplateIdx] = useState(0)
  const [claimTaskUid, setClaimTaskUid] = useState('')
  const [agentId, setAgentId] = useState(agentIdOptions[0])
  const [showReportAdvanced, setShowReportAdvanced] = useState(false)
  const [reportTaskUid, setReportTaskUid] = useState('')
  const [reportAgentId, setReportAgentId] = useState(agentIdOptions[0])
  const [reportOutputPreset, setReportOutputPreset] = useState(reportOutputPresets[0].label)
  const [customReportOutput, setCustomReportOutput] = useState('')
  const [verifyTaskUid, setVerifyTaskUid] = useState('')
  const [verdictOptions, setVerdictOptions] = useState<
    Array<{ verdict_id: string; source: string; score: number; overall_pass: boolean; created_at?: string | null }>
  >([])
  const [selectedVerdictId, setSelectedVerdictId] = useState('')
  const [verifierSource, setVerifierSource] = useState(verifierSourceOptions[0])

  const refresh = useCallback(async () => {
    setLoading(true)
    setError('')
    setAttentionHint('')
    try {
      const [convergeData, tasksData] = await Promise.all([
        callJsonApi<ConvergenceResponse['data']>('GET', '/api/platform/convergence'),
        callJsonApi<FdeTasksResponse['data']>('GET', '/api/platform/fde/tasks'),
      ])
      const attentionData = await callJsonApiOptional<AttentionResponse['data']>('GET', '/api/platform/fde/attention?status=pending')

      setConvergence(convergeData)
      const newTasks = tasksData.tasks ?? []
      setTasks(newTasks)
      setSummary({
        ...(tasksData.summary ?? {}),
      } as FdeTasksResponse['data']['summary'])
      if (attentionData) {
        setAttention(attentionData)
      } else {
        setAttention(null)
        setAttentionHint('attention 接口当前不可用（旧版本后端），请按任务队列手工处理 pending。')
      }
      setClaimTaskUid((prev) => prev || newTasks.find((r) => r.status === 'open')?.task_uid || '')
      setReportTaskUid((prev) => prev || newTasks.find((r) => r.status === 'claimed')?.task_uid || '')
      setVerifyTaskUid((prev) => prev || newTasks.find((r) => r.status === 'produced')?.task_uid || '')
      setDispatchTaskUid((prev) => {
        if (prev) return prev
        const ts = new Date()
        const stamp = `${ts.getFullYear()}${String(ts.getMonth() + 1).padStart(2, '0')}${String(ts.getDate()).padStart(2, '0')}${String(ts.getHours()).padStart(2, '0')}${String(ts.getMinutes()).padStart(2, '0')}`
        return `TASK_${stamp}`
      })
    } catch (e) {
      setError(e instanceof Error ? e.message : '数据加载失败')
    } finally {
      setLoading(false)
    }
  }, [])

  async function callJsonApi<T>(method: string, url: string, body?: unknown): Promise<T> {
    const res = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
    const raw = (await res.json()) as ApiEnvelope<T>
    if (!res.ok) throw new Error(`${method} ${url} -> ${res.status}`)
    if (!raw.success) throw new Error(raw.error ?? '请求失败')
    return raw.data
  }

  async function callJsonApiOptional<T>(method: string, url: string, body?: unknown): Promise<T | null> {
    try {
      return await callJsonApi<T>(method, url, body)
    } catch {
      return null
    }
  }

  function parseReportPayload(raw: string) {
    const trimmed = raw.trim()
    if (!trimmed) return { text: '' }
    if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
      try {
        return JSON.parse(trimmed)
      } catch {
        return { text: trimmed }
      }
    }
    return { text: trimmed }
  }

  function getSelectedReportOutput() {
    if (reportOutputPreset === '高级自定义') return parseReportPayload(customReportOutput)
    const preset = reportOutputPresets.find((x) => x.label === reportOutputPreset)
    const raw = preset?.value ?? ''
    return parseReportPayload(raw)
  }

  function getAgentId(selectValue: string) {
    if (!selectValue) return ''
    return selectValue
  }

  function getVerifierSource() {
    return verifierSource
  }

  async function runAction(action: string, fn: () => Promise<unknown>) {
    setActionLoading(action)
    setActionMessage('')
    try {
      await fn()
      setActionMessage(`✅ ${action} 成功`)
      await refresh()
    } catch (e) {
      setActionMessage(`❌ ${action} 失败：${e instanceof Error ? e.message : '请求失败'}`)
    } finally {
      setActionLoading('')
    }
  }

  async function onDispatchSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const taskUid = dispatchTaskUid.trim() || `TASK_${new Date().getFullYear()}${String(new Date().getMonth() + 1).padStart(2, '0')}${String(new Date().getDate()).padStart(2, '0')}${String(new Date().getHours()).padStart(2, '0')}${String(new Date().getMinutes()).padStart(2, '0')}${String(new Date().getSeconds()).padStart(2, '0')}`
    if (!dispatchTaskUid.trim()) {
      setDispatchTaskUid(taskUid)
    }
    await runAction('建卡', async () => {
      await callJsonApi('/api/platform/fde/dispatch', 'POST', {
        task_uid: taskUid,
        title: titleTemplates[dispatchTitleTemplateIdx] || '',
        description: descriptionTemplates[dispatchDescriptionTemplateIdx] || '',
      })
      setDispatchTaskUid('')
      setDispatchTitleTemplateIdx(0)
      setDispatchDescriptionTemplateIdx(0)
    })
  }

  async function onClaimSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    await runAction('认领', async () => {
      await callJsonApi('/api/platform/fde/claim', 'POST', {
        task_uid: claimTaskUid.trim(),
        agent_id: getAgentId(agentId),
      })
      setClaimTaskUid('')
      setAgentId('expert-01')
    })
  }

  async function onReportSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (reportOutputPreset === '高级自定义' && !customReportOutput.trim()) {
      setActionMessage('❌ 提交：请填写自定义 output')
      return
    }
    await runAction('提交', async () => {
      await callJsonApi('/api/platform/fde/report', 'POST', {
        task_uid: reportTaskUid.trim(),
        agent_id: getAgentId(reportAgentId),
        output: getSelectedReportOutput(),
      })
      setReportTaskUid('')
      setReportAgentId('expert-01')
      setReportOutputPreset(reportOutputPresets[0].label)
      setCustomReportOutput('')
    })
  }

  async function loadVerdictsForTask() {
    const taskUid = verifyTaskUid.trim()
    if (!taskUid) {
      setActionMessage('❌ 外部验收：请先填 task_uid')
      return
    }
    await runAction('拉取Verdict', async () => {
      const rows = await callJsonApi<Array<{
        verdict_id: string
        source: string
        score: number
        overall_pass: boolean
        created_at?: string | null
      }>>(`/api/platform/fde/verdict/${encodeURIComponent(taskUid)}`, 'GET')
      setVerdictOptions(rows)
      setSelectedVerdictId(rows[0]?.verdict_id ?? '')
    })
  }

  async function onVerifySubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!selectedVerdictId) {
      setActionMessage('❌ 外部验收：请先选择 verdict_id')
      return
    }
    await runAction('外部验收', async () => {
      await callJsonApi(`/api/platform/fde/verdict/${encodeURIComponent(selectedVerdictId)}/external-verify`, 'PATCH', {
        verifier_source: getVerifierSource() || 'ops-verifier',
      })
      setVerifyTaskUid('')
      setVerdictOptions([])
      setSelectedVerdictId('')
      setVerifierSource(verifierSourceOptions[0])
    })
  }

  useEffect(() => {
    refresh()
    const timer = setInterval(refresh, 30000)
    return () => clearInterval(timer)
  }, [refresh])

  const openTasks = tasks.filter((t) => t.status === 'open')
  const claimedTasks = tasks.filter((t) => t.status === 'claimed')
  const producedTasks = tasks.filter((t) => t.status === 'produced')
  const settledTasks = tasks.filter((t) => t.status === 'settled')
  const visibleOpenTasks = openTasks.filter((_, i) => i < 12)
  const visibleClaimedTasks = claimedTasks.filter((_, i) => i < 12)
  const visibleProducedTasks = producedTasks.filter((_, i) => i < 12)
  const visibleSettledTasks = settledTasks.filter((_, i) => i < 12)
  const statusTaskRows: Array<{ key: string; rows: FdeTask[]; allRows: FdeTask[] }> = [
    { key: 'open', rows: visibleOpenTasks, allRows: openTasks },
    { key: 'claimed', rows: visibleClaimedTasks, allRows: claimedTasks },
    { key: 'produced', rows: visibleProducedTasks, allRows: producedTasks },
    { key: 'settled', rows: visibleSettledTasks, allRows: settledTasks },
  ]
  const showDispatch = roleMode === 'PM'
  const showClaim = roleMode === 'PM' || roleMode === 'EXPERT'
  const showReport = roleMode === 'EXPERT'
  const showVerify = roleMode === 'OPS'

  return (
    <PageShell
      title="FDE 三期团队协作手册"
      subtitle="让团队和 agent 直接知道每一步该做什么，减少在页面外切系统"
      right={
        <button
          onClick={refresh}
          className="rounded-md border border-[rgba(255,255,255,0.15)] px-3 py-1.5 text-[12px] text-ln-tertiary hover:bg-[rgba(255,255,255,0.06)]"
        >
          {loading ? '刷新中…' : '立即刷新'}
        </button>
      }
    >
      <Panel title="一屏判断：这条闭环能跑吗">
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-[rgba(255,255,255,0.12)] p-3">
            <div className="text-[12px] text-ln-tertiary">外部验收(7d)</div>
            <div className="text-[24px] text-ln-text mt-1">{convergence?.external_verified.total ?? '—'} / {convergence?.external_verified.last_7d ?? '—'}</div>
            <div className="text-[12px] text-ln-tertiary mt-1">累计 / 近7天</div>
          </div>
          <div className="rounded-lg border border-[rgba(255,255,255,0.12)] p-3">
            <div className="text-[12px] text-ln-tertiary">生产线任务</div>
            <div className="text-[24px] text-ln-text mt-1">{summary?.open ?? 0} / {summary?.claimed ?? 0} / {summary?.produced ?? 0} / {summary?.settled ?? 0}</div>
            <div className="text-[12px] text-ln-tertiary mt-1">open / claimed / produced / settled</div>
          </div>
          <div className="rounded-lg border border-[rgba(255,255,255,0.12)] p-3">
            <div className="text-[12px] text-ln-tertiary">自治率</div>
            <div className="text-[24px] text-ln-text mt-1">
              {convergence ? `${Math.round(convergence.producer_autonomy.ratio * 100)}%` : '—'}
            </div>
            <div className="text-[12px] text-ln-tertiary mt-1">autonomous_verified / verified_total</div>
          </div>
          <div className="rounded-lg border border-[rgba(255,255,255,0.12)] p-3">
            <div className="text-[12px] text-ln-tertiary">外部结算映射</div>
            <div className="text-[24px] text-ln-text mt-1">
              {convergence ? `${convergence.settle_integrity.externally_backed}/${convergence.settle_integrity.settled_total}` : '—'}
            </div>
            <div className="text-[12px] text-ln-tertiary mt-1">有效结算 / settled</div>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          <Badge tone={error ? 'fail' : 'pass'}>{error ? '当前不可一键闭环' : '可跑主链路'}</Badge>
          <Badge tone="accent">交互表与出题表分离</Badge>
          <Badge tone="muted">
            统一入口 https://fde.nautilus.social/docs/fde-phase3
          </Badge>
        </div>
        <div className="text-[12px] text-ln-tertiary mt-3">
          {convergence ? `快照 ${shortTime(convergence.generated_at)} UTC` : '等待快照'}
        </div>
      </Panel>

      <Panel title="出题 + 交互一体联动（关键动作）">
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded border border-[rgba(255,255,255,0.12)] p-3">
            <div className="text-[13px] text-ln-text mb-2">S1：出题/建卡</div>
            <div className="text-[12px] text-ln-tertiary">每行必须用统一 task_uid，必须有标题和验收说明。</div>
          </div>
          <div className="rounded border border-[rgba(255,255,255,0.12)] p-3">
            <div className="text-[13px] text-ln-text mb-2">S2：交互提交</div>
            <div className="text-[12px] text-ln-tertiary">claim 后回填 output，输出里只含任务内容和证据。</div>
          </div>
          <div className="rounded border border-[rgba(255,255,255,0.12)] p-3">
            <div className="text-[13px] text-ln-text mb-2">S3：结算触发</div>
            <div className="text-[12px] text-ln-tertiary">verdict 落库后需 external-verify 才计入 income。</div>
          </div>
          <div className="rounded border border-[rgba(255,255,255,0.12)] p-3">
            <div className="text-[13px] text-ln-text mb-2">S4：失败收口</div>
            <div className="text-[12px] text-ln-tertiary">异常优先进 /api/platform/fde/attention，按建议动作处理。</div>
          </div>
        </div>
      </Panel>

      <Panel title="今天可直接执行（最小动作）">
        <div className="mb-2 text-[12px] text-ln-tertiary">页面内直接提交，不再复制命令。除高级定制项外，默认流程全部点选。</div>
        <div className="mb-3 flex gap-2 text-[12px]">
          {roleOptions.map((role) => (
            <button
              key={role.value}
              onClick={() => setRoleMode(role.value)}
              className={`rounded border px-3 py-1.5 ${roleMode === role.value ? 'border-[#27a644] text-[#6fcf97]' : 'border-[rgba(255,255,255,0.18)]'}`}
            >
              {role.label}
            </button>
          ))}
        </div>
        <div className="mb-3 grid gap-2 md:grid-cols-2 xl:grid-cols-4">
          {getRoleGuide(roleMode).map((row) => (
            <div key={row[0]} className="rounded border border-[rgba(255,255,255,0.16)] p-2 text-[11px]">
              <div className="text-ln-text font-semibold">{row[0]}</div>
              <div className="text-ln-tertiary mt-1">{row[1]}</div>
            </div>
          ))}
        </div>
        {actionMessage && (
          <div className={`mb-3 rounded border px-3 py-2 text-[12px] ${actionMessage.startsWith('✅') ? 'border-[rgba(76,175,80,0.45)] text-[#6fcf97]' : 'border-[rgba(255,80,80,0.45)] text-[#eb5757]'}`}>
            {actionMessage}
          </div>
        )}
        <div className="grid gap-3 lg:grid-cols-2">
          {showDispatch ? (
            <div>
              <form onSubmit={onDispatchSubmit} className="rounded border border-[rgba(255,255,255,0.12)] p-3 space-y-2">
                <div className="text-[13px] text-ln-text">1) 出题端建卡（S1）</div>
                <div className="w-full rounded border border-[rgba(255,255,255,0.18)] bg-[rgba(255,255,255,0.04)] px-2 py-2 text-[12px] font-mono text-ln-text">
                  task_uid: {dispatchTaskUid || '未生成'}
                </div>
                <button
                  type="button"
                  onClick={() => {
                    const ts = new Date()
                    const stamp = `${ts.getFullYear()}${String(ts.getMonth() + 1).padStart(2, '0')}${String(ts.getDate()).padStart(2, '0')}${String(ts.getHours()).padStart(2, '0')}${String(ts.getMinutes()).padStart(2, '0')}${String(ts.getSeconds()).padStart(2, '0')}`
                    setDispatchTaskUid(`TASK_${stamp}`)
                  }}
                  className="rounded border border-[rgba(255,255,255,0.15)] px-2.5 py-1.5 text-[12px]"
                >
                  生成任务ID
                </button>
                <select
                  className="w-full rounded border border-[rgba(255,255,255,0.18)] bg-transparent px-2 py-1 text-[12px]"
                  value={dispatchTitleTemplateIdx}
                  onChange={(e) => setDispatchTitleTemplateIdx(Number(e.target.value))}
                >
                  {titleTemplates.map((item, i) => (
                    <option key={item} value={i}>{item}</option>
                  ))}
                </select>
                <select
                  className="w-full rounded border border-[rgba(255,255,255,0.18)] bg-transparent px-2 py-1 text-[12px]"
                  value={dispatchDescriptionTemplateIdx}
                  onChange={(e) => setDispatchDescriptionTemplateIdx(Number(e.target.value))}
                >
                  {descriptionTemplates.map((item, i) => (
                    <option key={item} value={i}>{item}</option>
                  ))}
                </select>
                <button
                  disabled={actionLoading === '建卡'}
                  className="w-full rounded-md border border-[rgba(255,255,255,0.15)] px-2.5 py-1.5 text-[12px] disabled:opacity-50"
                  type="submit"
                >
                  {actionLoading === '建卡' ? '提交中…' : '执行建卡'}
                </button>
              </form>
            </div>
          ) : null}

          {showClaim ? (
            <form onSubmit={onClaimSubmit} className="rounded border border-[rgba(255,255,255,0.12)] p-3 space-y-2">
              <div className="text-[13px] text-ln-text">2) 认领任务（S2）</div>
              <select
                className="w-full rounded border border-[rgba(255,255,255,0.18)] bg-transparent px-2 py-1 text-[12px]"
                value={claimTaskUid}
                onChange={(e) => setClaimTaskUid(e.target.value)}
                required
              >
                <option value="">{openTasks.length ? '先选一个 open 任务' : '先建卡再回来'}</option>
                {openTasks.map((item) => (
                  <option key={item.task_uid} value={item.task_uid}>
                    {item.task_uid} · {item.title}
                  </option>
                ))}
              </select>
              <select
                className="w-full rounded border border-[rgba(255,255,255,0.18)] bg-transparent px-2 py-1 text-[12px]"
                value={agentId || agentIdOptions[0]}
                onChange={(e) => setAgentId(e.target.value)}
                required
              >
                {agentIdOptions.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
              <button
                disabled={actionLoading === '认领' || openTasks.length === 0 || !claimTaskUid}
                className="w-full rounded-md border border-[rgba(255,255,255,0.15)] px-2.5 py-1.5 text-[12px] disabled:opacity-50"
                type="submit"
              >
                {actionLoading === '认领' ? '提交中…' : '执行认领'}
              </button>
            </form>
          ) : null}

          {showReport ? (
            <form onSubmit={onReportSubmit} className="rounded border border-[rgba(255,255,255,0.12)] p-3 space-y-2">
              <div className="text-[13px] text-ln-text">3) 提交产出（S2→S3）</div>
              <select
                className="w-full rounded border border-[rgba(255,255,255,0.18)] bg-transparent px-2 py-1 text-[12px]"
                value={reportTaskUid}
                onChange={(e) => setReportTaskUid(e.target.value)}
                required
              >
                <option value="">{claimedTasks.length ? '先选一个 claimed 任务' : '先认领任务再继续'}</option>
                {claimedTasks.map((item) => (
                  <option key={item.task_uid} value={item.task_uid}>
                    {item.task_uid} · {item.title}
                  </option>
                ))}
              </select>
              <select
                className="w-full rounded border border-[rgba(255,255,255,0.18)] bg-transparent px-2 py-1 text-[12px]"
                value={reportAgentId || agentIdOptions[0]}
                onChange={(e) => setReportAgentId(e.target.value)}
                required
              >
                {agentIdOptions.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
              <select
                className="w-full min-h-[84px] rounded border border-[rgba(255,255,255,0.18)] bg-transparent px-2 py-1 text-[12px]"
                value={reportOutputPreset}
                onChange={(e) => {
                  const next = e.target.value
                  setReportOutputPreset(next)
                  if (next === '高级自定义') {
                    setShowReportAdvanced(true)
                  } else {
                    setShowReportAdvanced(false)
                    setCustomReportOutput('')
                  }
                }}
              >
                {reportOutputPresets.map((item) => (
                  <option key={item.label} value={item.label}>{item.label}</option>
                ))}
                <option value="高级自定义">高级自定义（JSON/文本）</option>
              </select>
              <button
                type="button"
                onClick={() => {
                  setShowReportAdvanced((prev) => !prev)
                  if (!showReportAdvanced) {
                    setReportOutputPreset('高级自定义')
                  } else {
                    setReportOutputPreset(reportOutputPresets[0].label)
                    setCustomReportOutput('')
                  }
                }}
                className="rounded border border-[rgba(255,255,255,0.15)] px-2.5 py-1.5 text-[12px]"
              >
                {showReportAdvanced ? '隐藏高级' : '需要自定义输出'}
              </button>
              {showReportAdvanced && (
                <textarea
                  className="w-full min-h-[84px] rounded border border-[rgba(255,255,255,0.18)] bg-transparent px-2 py-1 text-[12px]"
                  placeholder='自定义 output（可填文本或 JSON）'
                  value={customReportOutput}
                  onChange={(e) => setCustomReportOutput(e.target.value)}
                />
              )}
              <button
                disabled={actionLoading === '提交' || claimedTasks.length === 0 || !reportTaskUid}
                className="w-full rounded-md border border-[rgba(255,255,255,0.15)] px-2.5 py-1.5 text-[12px] disabled:opacity-50"
                type="submit"
              >
                {actionLoading === '提交' ? '提交中…' : '执行提交'}
              </button>
            </form>
          ) : null}

          {showVerify ? (
            <form onSubmit={onVerifySubmit} className="rounded border border-[rgba(255,255,255,0.12)] p-3 space-y-2">
            <div className="text-[13px] text-ln-text">4) 外部验收（Ops）</div>
            <div className="flex gap-2">
              <select
                className="flex-1 rounded border border-[rgba(255,255,255,0.18)] bg-transparent px-2 py-1 text-[12px]"
                value={verifyTaskUid}
                onChange={(e) => {
                  setVerifyTaskUid(e.target.value)
                  setVerdictOptions([])
                  setSelectedVerdictId('')
                }}
                required
              >
                <option value="">{producedTasks.length ? '先选一个 produced 任务' : '先完成提交再验收'}</option>
                {producedTasks.map((item) => (
                  <option key={item.task_uid} value={item.task_uid}>
                    {item.task_uid} · {item.title}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={loadVerdictsForTask}
                disabled={actionLoading === '拉取Verdict'}
                className="rounded-md border border-[rgba(255,255,255,0.15)] px-2.5 py-1.5 text-[12px] disabled:opacity-50"
              >
                {actionLoading === '拉取Verdict' ? '查询中…' : '查verdict'}
              </button>
            </div>
            <select
              className="w-full rounded border border-[rgba(255,255,255,0.18)] bg-transparent px-2 py-1 text-[12px]"
              value={selectedVerdictId}
              onChange={(e) => setSelectedVerdictId(e.target.value)}
              required
            >
              <option value="">{verdictOptions.length ? '请选择一条待验收 verdict' : '先点“查verdict”'}</option>
              {verdictOptions.map((row) => (
                <option key={row.verdict_id} value={row.verdict_id}>
                  {row.verdict_id.slice(0, 18)} · {row.source} · {row.overall_pass ? 'PASS' : 'FAIL'} · {row.score} · {shortTime(row.created_at ?? null)}
                </option>
              ))}
            </select>
            <select
              className="w-full rounded border border-[rgba(255,255,255,0.18)] bg-transparent px-2 py-1 text-[12px]"
              value={verifierSource}
              onChange={(e) => setVerifierSource(e.target.value)}
              required
            >
              {verifierSourceOptions.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
            <button
              type="submit"
              disabled={!selectedVerdictId || actionLoading === '外部验收'}
              className="w-full rounded-md border border-[rgba(255,255,255,0.15)] px-2.5 py-1.5 text-[12px] disabled:opacity-50"
            >
              {actionLoading === '外部验收' ? '提交中…' : '执行外部验收'}
            </button>
            <div className="text-[11px] text-ln-tertiary">操作说明：先点查 verdict 取可选列表，再执行 external-verify。</div>
          </form>
          ) : null}

          {showVerify ? (
            <div className="rounded border border-[rgba(255,255,255,0.12)] p-3">
              <div className="text-[13px] text-ln-text mb-1">5) 人工异常入口</div>
              <div className="text-[12px] text-ln-tertiary">
                打开「失败/待处理」区，按提示逐条处理，不跨任务改字段，只做建议动作。
              </div>
            </div>
          ) : null}
        </div>
      </Panel>

      <Panel title="当前任务视图（S1-S3 一条链）">
        {loading && <div className="text-[12px] text-ln-tertiary">加载中…</div>}
        {error && <div className="text-[12px] text-[#eb5757]">{error}</div>}
        {!loading && !error && (
          <div className="space-y-3">
          {statusTaskRows.map(({ key, rows, allRows }) => (
              <div key={key} className="rounded-lg border border-[rgba(255,255,255,0.12)] p-3">
                <div className="text-[13px] text-ln-text mb-2 uppercase">
                  {key} ({allRows.length})
                </div>
                {(rows.length === 0) ? (
                  <div className="text-[12px] text-ln-tertiary">暂无</div>
                ) : (
                  <ul className="space-y-2 text-[12px]">
                    {rows.map((row) => (
                      <li key={row.task_uid} className="break-all border border-[rgba(255,255,255,0.08)] p-2">
                        <div className="font-mono text-[11px]">
                          <span className={statusClass(row.status)}>{row.status}</span>
                          {' · '}{row.task_uid}
                        </div>
                        <div className="text-ln-tertiary mt-1">
                          <span>{row.title}</span>
                        </div>
                        <div className="text-ln-tertiary mt-1">
                          claimed_by={row.claimed_by || '—'} · claimed_at={shortTime(row.claimed_at)} · reported_at={shortTime(row.reported_at)}
                        </div>
                        {row.verdict && (
                          <div className="text-ln-tertiary mt-1">
                            verdict: {row.verdict.overall_pass ? 'PASS' : 'FAIL'} · {row.verdict.score}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        )}
      </Panel>

      <Panel title="失败/待处理（ops 队列）">
        {attention ? (
          attention.summary.pending > 0 ? (
            <div className="space-y-2">
              {attention.items.slice(0, 8).map((item) => (
                <div key={item.id} className="rounded border border-[rgba(255,255,255,0.12)] p-2 text-[12px]">
                  <div className="text-ln-text">
                    {item.stage.toUpperCase()} · {item.code} · {item.severity}
                  </div>
                  <div className="text-ln-tertiary mt-1">{item.task_uid || '—'} · {item.title}</div>
                  <div className="text-ln-tertiary mt-1">{item.detail}</div>
                  <div className="mt-1 text-[11px]">
                    建议动作：{(item.suggested_actions || []).join(' / ') || 'ignore'}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-[13px] text-ln-tertiary">暂未发现 pending（保持连续运行）。</div>
          )
        ) : (
          <div className="text-[13px] text-ln-tertiary">{attentionHint || '未取到 pending 数据（暂不可用）。'}</div>
        )}
      </Panel>

      <Panel title="运营与 agent 分工口径">
        <div className="grid md:grid-cols-2 gap-3">
          {actorCards.map((row) => (
            <div key={row[0]} className="rounded-lg border border-[rgba(255,255,255,0.12)] p-3">
              <div className="text-[14px] text-ln-text font-[510]">{row[0]}</div>
              <div className="text-[13px] text-ln-tertiary mt-1">职责：{row[1]}</div>
              <div className="text-[12px] text-ln-tertiary mt-2"><span className="text-ln-text">交付目标：</span>{row[2]}</div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="团队/agent 10 分钟开工流程">
        <ol className="space-y-2 list-decimal pl-6 text-[13px] text-ln-tertiary">
          {[
            ['先读本页的“一屏判断”', '确认是否可开工'],
            ['若可开工', '从任务视图抓一个状态明确 task_uid'],
            ['按状态处理', 'open/claimed/produced 按固定动作'],
            ['遇到 pending', '先查 attention 队列再处理'],
          ].map((item) => (
            <li key={item[0]}>
              <span className="text-ln-text">{item[0]}：</span>{item[1]}
            </li>
          ))}
        </ol>
      </Panel>

      <Panel title="状态机（只需判断链路）">
        <div className="space-y-2 text-[13px] text-ln-tertiary">
          {lifecycle.map((item) => (
            <div key={item[0]} className="rounded border border-[rgba(255,255,255,0.12)] p-2">
              <span className="text-ln-text">{item[0]}：</span>{item[1]}
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="最小字段清单（缺一不可）">
        <ul className="space-y-2 list-disc pl-6 text-[13px] text-ln-tertiary">
          {requiredFields.map((item) => (
            <li key={item[0]}>
              <span className="text-ln-text">{item[0]}：</span>{item[1]}
            </li>
          ))}
        </ul>
      </Panel>

      <Panel title="外部专家身份映射（uid 自动化）">
        <div className="text-[13px] text-ln-tertiary">
          系统统一按顺序回填：
          <span className="text-ln-text"> expert_id → open_id → assignee</span>。
          页面不要求手动切换链路，task_uid 仍是唯一主键。
        </div>
      </Panel>

      <Panel title="外部专家可直接复制的说明（群发版）">
        <pre className="text-[12px] leading-6 text-ln-tertiary bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.1)] p-3 rounded whitespace-pre-wrap">
          {externalMsg}
        </pre>
      </Panel>

      <Panel title="外部专家执行规则（固定三条）">
        <ul className="list-decimal pl-6 space-y-2 text-[13px] text-ln-tertiary">
          {expertRules.map((line, i) => (
            <li key={i}>{line}</li>
          ))}
        </ul>
      </Panel>
    </PageShell>
  )
}
