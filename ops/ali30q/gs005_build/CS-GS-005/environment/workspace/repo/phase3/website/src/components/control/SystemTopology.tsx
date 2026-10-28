/**
 * SystemTopology · 舰桥 v2 系统拓扑图(service-map)· /control 顶部标志性总览.
 *
 * 纯 SVG/CSS 手画(无 react-flow/d3 等新依赖 · 避免 build 膨胀).
 * 中心 hub = verdict-bus(FDE verdict 中枢)· 环绕 5 节点(soul/compass/dmas/agent fleet/RSI).
 * 边 = 节点↔hub 连线(SVG path · 体现 produce→verdict→grounding→PoI 流向 · 轻量流动动画).
 * 每节点显 名称 + 1-2 关键活指标(从 control-plane data 取)+ 健康色边框.
 * 点击节点 → 平滑滚动到页面对应板块(scrollIntoView · 板块容器需有对应 id).
 *
 * 只读 view · 不写交互 · 对所有登录用户可见. data 作 prop 传入(不新 fetch).
 */
import { useCallback } from 'react'
import { Hint } from './PanelKit'

// 与 ControlCenterPage 的 ControlPlane 同形(只声明本组件用到的字段 · 可选链防御).
type TopologyData = {
  soul?: {
    verdicts?: { summary?: { total?: number; passed?: number } }
    rsi_deltas?: { count?: number }
  }
  compass?: {
    poi?: { poi_eligible?: number }
    recall?: { status?: string }
  }
  dmas?: {
    agents?: { total?: number; active?: number }
    bids?: { summary?: { total?: number } }
  }
  pulse?: { soul_alive?: boolean }
} | null

// 健康度 → 边框/文字色(linear-green=活/正常 · ln-muted=offline/0 · 红=异常).
type Health = 'ok' | 'idle' | 'bad'
const HEALTH_RING: Record<Health, string> = {
  ok: 'border-linear-green/50 shadow-[0_0_0_1px_rgba(39,166,68,0.15)]',
  idle: 'border-[rgba(255,255,255,0.1)]',
  bad: 'border-[#eb5757]/50 shadow-[0_0_0_1px_rgba(235,87,87,0.15)]',
}
const HEALTH_DOT: Record<Health, string> = {
  ok: 'bg-linear-green',
  idle: 'bg-ln-muted',
  bad: 'bg-[#eb5757]',
}

type NodeDef = {
  key: string
  label: string
  panelId: string // 点击滚动目标(板块容器 id)
  health: Health
  metrics: { label: string; value: string; tone?: string }[]
  pulse?: boolean // 活跃脉冲点(soul_alive)
}

// 节点在 viewBox(0..100 x 0..72)的归一坐标 · hub 居中 · 5 节点环绕.
const HUB = { x: 50, y: 36 }
const NODE_POS: Record<string, { x: number; y: number }> = {
  soul: { x: 16, y: 14 },
  compass: { x: 84, y: 14 },
  dmas: { x: 12, y: 58 },
  fleet: { x: 88, y: 58 },
  rsi: { x: 50, y: 66 },
}

function buildNodes(data: TopologyData): NodeDef[] {
  const v = data?.soul?.verdicts?.summary
  const passed = v?.passed ?? 0
  const total = v?.total ?? 0
  const rsiCount = data?.soul?.rsi_deltas?.count ?? 0
  const poi = data?.compass?.poi?.poi_eligible ?? 0
  const recall = data?.compass?.recall?.status ?? '—'
  const recallOnline = recall === 'online'
  const agentsActive = data?.dmas?.agents?.active ?? 0
  const agentsTotal = data?.dmas?.agents?.total ?? 0
  const events = data?.dmas?.bids?.summary?.total ?? 0
  const soulAlive = Boolean(data?.pulse?.soul_alive)

  return [
    {
      key: 'soul',
      label: 'soul · QC/verdict',
      panelId: 'panel-soul',
      health: soulAlive ? 'ok' : 'idle',
      pulse: soulAlive,
      metrics: [
        { label: '验收', value: `${passed}/${total}`, tone: 'text-linear-green' },
      ],
    },
    {
      key: 'compass',
      label: 'compass · 记忆/PoI',
      panelId: 'panel-poi',
      health: recallOnline ? 'ok' : 'idle',
      metrics: [
        { label: 'PoI', value: String(poi), tone: poi > 0 ? 'text-linear-green' : 'text-ln-tertiary' },
        { label: 'recall', value: recall, tone: recallOnline ? 'text-linear-green' : 'text-ln-muted' },
      ],
    },
    {
      key: 'dmas',
      label: 'dmas · 编队/事件',
      panelId: 'panel-fleet',
      health: agentsActive > 0 ? 'ok' : 'idle',
      metrics: [
        { label: '活跃', value: `${agentsActive}/${agentsTotal}`, tone: agentsActive > 0 ? 'text-linear-green' : 'text-ln-tertiary' },
        { label: '事件', value: String(events) },
      ],
    },
    {
      key: 'fleet',
      label: 'agent fleet · producer',
      panelId: 'panel-fleet',
      health: agentsActive > 0 ? 'ok' : 'idle',
      metrics: [
        { label: '在线', value: String(agentsActive), tone: agentsActive > 0 ? 'text-linear-green' : 'text-ln-muted' },
      ],
    },
    {
      key: 'rsi',
      label: 'RSI ΔReward',
      panelId: 'panel-rsi',
      health: rsiCount > 0 ? 'ok' : 'idle',
      metrics: [
        { label: '外部增量', value: String(rsiCount), tone: rsiCount > 0 ? 'text-linear-green' : 'text-ln-muted' },
      ],
    },
  ]
}

// 节点卡片(绝对定位 · 以 NODE_POS 百分比为中心).
function NodeCard({ node, onJump }: { node: NodeDef; onJump: (id: string) => void }) {
  const pos = NODE_POS[node.key]
  return (
    <button
      type="button"
      onClick={() => onJump(node.panelId)}
      style={{ left: `${pos.x}%`, top: `${pos.y}%` }}
      className={`absolute z-10 w-[150px] -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-linear-panel/95 px-3 py-2 text-left backdrop-blur transition hover:bg-linear-surface hover:-translate-y-[calc(50%+2px)] focus:outline-none focus:ring-1 focus:ring-linear-brand ${HEALTH_RING[node.health]}`}
      aria-label={`跳到 ${node.label} 板块`}
    >
      <div className="mb-1 flex items-center gap-1.5">
        {node.pulse ? (
          <span className="relative flex h-2 w-2 shrink-0">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-linear-green opacity-60" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-linear-green" />
          </span>
        ) : (
          <span className={`h-2 w-2 shrink-0 rounded-full ${HEALTH_DOT[node.health]}`} />
        )}
        <span className="truncate text-[11px] font-[510] text-ln-secondary">{node.label}</span>
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-0.5">
        {node.metrics.map((m) => (
          <span key={m.label} className="text-[10px] text-ln-muted">
            {m.label}{' '}
            <span className={`font-mono tabular-nums ${m.tone ?? 'text-ln-secondary'}`}>{m.value}</span>
          </span>
        ))}
      </div>
    </button>
  )
}

export default function SystemTopology({ data }: { data: TopologyData }) {
  const loading = !data

  const onJump = useCallback((panelId: string) => {
    const el = document.getElementById(panelId)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [])

  if (loading) {
    return (
      <div className="rounded-lg border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.02)] p-5">
        <Hint className="mb-3">系统拓扑 · 4 子系统围绕 verdict-bus 中枢 · 点节点跳对应板块</Hint>
        <div className="animate-pulse rounded-md bg-[rgba(255,255,255,0.04)]" style={{ height: 280 }} />
      </div>
    )
  }

  const nodes = buildNodes(data)
  const soulAlive = Boolean(data?.pulse?.soul_alive)

  return (
    <div className="rounded-lg border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.02)] p-5">
      <Hint className="mb-3">
        系统拓扑 · 5 个子系统围绕 <span className="text-ln-tertiary">verdict-bus</span> 中枢(出题 → 验收 → grounding → PoI)·
        节点边框=健康色(绿=活/灰=闲/红=异常)· 点任一节点平滑跳到对应板块。
      </Hint>

      {/* 画布 · aspect 比例保持 · SVG 连线在底层 · 节点卡片绝对定位在上层 */}
      <div className="relative w-full" style={{ aspectRatio: '100 / 72', minHeight: 240 }}>
        {/* 连线层(SVG · 流向 hub) */}
        <svg
          viewBox="0 0 100 72"
          preserveAspectRatio="none"
          className="absolute inset-0 h-full w-full"
          aria-hidden="true"
        >
          <defs>
            <linearGradient id="edge-flow" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#5e6ad2" stopOpacity="0.05" />
              <stop offset="50%" stopColor="#5e6ad2" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#5e6ad2" stopOpacity="0.05" />
            </linearGradient>
          </defs>
          {nodes.map((n) => {
            const p = NODE_POS[n.key]
            return (
              <line
                key={n.key}
                x1={p.x}
                y1={p.y}
                x2={HUB.x}
                y2={HUB.y}
                stroke="url(#edge-flow)"
                strokeWidth={0.6}
                strokeDasharray="2 2"
                className="topo-flow"
              />
            )
          })}
        </svg>

        {/* 中心 hub · verdict-bus */}
        <div
          style={{ left: `${HUB.x}%`, top: `${HUB.y}%` }}
          className="absolute z-10 flex w-[140px] -translate-x-1/2 -translate-y-1/2 flex-col items-center rounded-full border border-linear-brand/50 bg-linear-brand/10 px-3 py-4 text-center shadow-[0_0_24px_rgba(94,106,210,0.25)]"
        >
          {soulAlive && (
            <span className="relative mb-1 flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-linear-accent opacity-60" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-linear-accent" />
            </span>
          )}
          <span className="text-[12px] font-[560] text-ln-text">verdict-bus</span>
          <span className="text-[10px] text-ln-muted">FDE verdict 中枢</span>
        </div>

        {/* 节点卡片层 */}
        {nodes.map((n) => (
          <NodeCard key={n.key} node={n} onJump={onJump} />
        ))}
      </div>

      {/* 流动动画(局部 · 不污染全局 · CSS dash 偏移) */}
      <style>{`
        .topo-flow { animation: topo-dash 1.6s linear infinite; }
        @keyframes topo-dash { to { stroke-dashoffset: -8; } }
        @media (prefers-reduced-motion: reduce) { .topo-flow { animation: none; } }
      `}</style>
    </div>
  )
}
