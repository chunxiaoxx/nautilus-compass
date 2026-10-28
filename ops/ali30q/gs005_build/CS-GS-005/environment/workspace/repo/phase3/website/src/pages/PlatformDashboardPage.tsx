import { useState } from 'react'
import {
  useAgents,
  useBounties,
  useSquare,
  useGenes,
  useHealth,
  scoreBounty,
} from '../hooks/useNautilusAPI'
import type {
  Agent,
  Bounty,
  SquarePost,
  Gene,
  PlatformHealth,
} from '../hooks/useNautilusAPI'

// ---------------------------------------------------------------------------
// Shared primitives
// ---------------------------------------------------------------------------

function OfflineBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-[510] bg-red-500/10 text-red-400 border border-red-500/20">
      <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
      offline
    </span>
  )
}

function Shimmer({ className = '' }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded bg-[rgba(255,255,255,0.04)] ${className}`}
    />
  )
}

function PanelHeader({
  title,
  offline,
}: {
  title: string
  offline?: boolean
}) {
  return (
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-[15px] font-[510] tracking-[-0.165px] text-ln-text">
        {title}
      </h3>
      {offline && <OfflineBadge />}
    </div>
  )
}

function Panel({
  children,
  className = '',
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div
      className={`rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] p-5 ${className}`}
    >
      {children}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Health Gauge (circular SVG)
// ---------------------------------------------------------------------------

function HealthGauge({
  health,
  loading,
  offline,
}: {
  health: PlatformHealth | null
  loading: boolean
  offline: boolean
}) {
  const score = health?.health_score ?? 0
  const r = 54
  const circ = 2 * Math.PI * r
  const offset = circ - (score / 100) * circ

  const color =
    score >= 70 ? '#27a644' : score >= 40 ? '#eab308' : '#ef4444'

  return (
    <Panel>
      <PanelHeader title="Platform Health" offline={offline} />
      {loading ? (
        <div className="flex justify-center py-6">
          <Shimmer className="w-[130px] h-[130px] rounded-full" />
        </div>
      ) : (
        <div className="flex justify-center">
          <svg width="130" height="130" className="-rotate-90">
            <circle
              cx="65"
              cy="65"
              r={r}
              fill="none"
              stroke="rgba(255,255,255,0.05)"
              strokeWidth="8"
            />
            <circle
              cx="65"
              cy="65"
              r={r}
              fill="none"
              stroke={color}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circ}
              strokeDashoffset={offset}
              className="transition-all duration-700"
            />
            <text
              x="65"
              y="65"
              textAnchor="middle"
              dominantBaseline="central"
              className="rotate-90 origin-center"
              fill="#f7f8f8"
              fontSize="28"
              fontWeight="510"
            >
              {score}
            </text>
          </svg>
        </div>
      )}
    </Panel>
  )
}

// ---------------------------------------------------------------------------
// NAU Economy
// ---------------------------------------------------------------------------

function NAUEconomy({
  health,
  loading,
  offline,
}: {
  health: PlatformHealth | null
  loading: boolean
  offline: boolean
}) {
  const rows = [
    { label: 'Minted', value: health?.nau_minted ?? 0 },
    { label: 'Circulating', value: health?.nau_circulating ?? 0 },
    { label: 'Spent', value: health?.nau_spent ?? 0 },
  ]
  return (
    <Panel>
      <PanelHeader title="NAU Economy" offline={offline} />
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <Shimmer key={i} className="h-5 w-full" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {rows.map(r => (
            <div
              key={r.label}
              className="flex items-center justify-between"
            >
              <span className="text-[13px] font-[510] text-ln-tertiary tracking-[-0.13px]">
                {r.label}
              </span>
              <span className="text-[15px] font-[510] text-ln-text tabular-nums">
                {Number(r.value).toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      )}
    </Panel>
  )
}

// ---------------------------------------------------------------------------
// Active Agents count
// ---------------------------------------------------------------------------

function ActiveAgents({
  health,
  loading,
  offline,
}: {
  health: PlatformHealth | null
  loading: boolean
  offline: boolean
}) {
  const statuses = health?.agents_by_status ?? {}
  return (
    <Panel>
      <PanelHeader title="Active Agents" offline={offline} />
      {loading ? (
        <Shimmer className="h-10 w-20 mx-auto" />
      ) : (
        <>
          <div className="text-center mb-4">
            <span className="text-[32px] font-[510] tracking-[-0.704px] text-ln-text">
              {health?.active_agents ?? 0}
            </span>
            <span className="text-[13px] text-ln-muted ml-1.5">
              / {health?.total_agents ?? 0}
            </span>
          </div>
          <div className="flex flex-wrap gap-2 justify-center">
            {Object.entries(statuses).map(([status, count]) => {
              const dot =
                status === 'alive' || status === 'active'
                  ? 'bg-linear-green'
                  : status === 'idle' || status === 'coma'
                    ? 'bg-yellow-500'
                    : status === 'dead' || status === 'error'
                      ? 'bg-red-500'
                      : 'bg-ln-muted'
              return (
                <span
                  key={status}
                  className="inline-flex items-center gap-1.5 text-[12px] font-[510] text-ln-tertiary"
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
                  {status} {count}
                </span>
              )
            })}
          </div>
        </>
      )}
    </Panel>
  )
}

// ---------------------------------------------------------------------------
// Agent Cards
// ---------------------------------------------------------------------------

function roleBadgeColor(role: string): string {
  const r = (role || '').toLowerCase()
  if (r.includes('manager') || r.includes('orchestrat'))
    return 'bg-linear-brand/15 text-linear-accent border-linear-brand/25'
  if (r.includes('build') || r.includes('engineer'))
    return 'bg-linear-green/15 text-linear-green border-linear-green/25'
  if (r.includes('explor') || r.includes('research'))
    return 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25'
  if (r.includes('evol') || r.includes('evolv'))
    return 'bg-purple-500/15 text-purple-400 border-purple-500/25'
  return 'bg-[rgba(255,255,255,0.05)] text-ln-tertiary border-[rgba(255,255,255,0.08)]'
}

function statusDot(status: string): string {
  const s = (status || '').toLowerCase()
  if (s === 'active' || s === 'alive' || s === 'online')
    return 'bg-linear-green'
  if (s === 'idle' || s === 'coma') return 'bg-yellow-500'
  return 'bg-red-500'
}

function AgentCard({ agent }: { agent: Agent }) {
  return (
    <div className="rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] p-4 hover:bg-[rgba(255,255,255,0.04)] transition-colors">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${statusDot(agent.status)}`}
          />
          <span className="text-[14px] font-[510] text-ln-text truncate max-w-[140px]">
            {agent.name}
          </span>
        </div>
        <span
          className={`text-[10px] font-[510] px-2 py-0.5 rounded-full border ${roleBadgeColor(agent.role)}`}
        >
          {agent.role}
        </span>
      </div>
      <div className="space-y-1.5 text-[12px]">
        <div className="flex justify-between">
          <span className="text-ln-muted">Reputation</span>
          <span className="text-ln-secondary font-[510] tabular-nums">
            {agent.reputation ?? '--'}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-ln-muted">Activity</span>
          <span className="text-ln-tertiary truncate max-w-[120px] text-right">
            {agent.current_activity || 'idle'}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-ln-muted">Last cycle</span>
          <span className="text-ln-muted font-mono text-[11px]">
            {agent.last_cycle
              ? new Date(agent.last_cycle).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })
              : '--'}
          </span>
        </div>
      </div>
    </div>
  )
}

function AgentCards({
  agents,
  loading,
  offline,
}: {
  agents: Agent[] | null
  loading: boolean
  offline: boolean
}) {
  return (
    <div>
      <PanelHeader title="Agents" offline={offline} />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {loading
          ? Array.from({ length: 5 }).map((_, i) => (
              <Shimmer key={i} className="h-[130px]" />
            ))
          : (agents ?? []).slice(0, 10).map(a => (
              <AgentCard key={a.agent_id} agent={a} />
            ))}
        {!loading && (!agents || agents.length === 0) && (
          <p className="col-span-full text-[13px] text-ln-muted">
            No agents registered yet.
          </p>
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Bounty Board
// ---------------------------------------------------------------------------

function bountyStatusPill(status: string) {
  const s = (status || '').toLowerCase()
  if (s === 'open')
    return 'bg-linear-green/15 text-linear-green border-linear-green/25'
  if (s.includes('progress') || s === 'assigned')
    return 'bg-linear-brand/15 text-linear-accent border-linear-brand/25'
  if (s === 'completed' || s === 'done')
    return 'bg-ln-tertiary/15 text-ln-tertiary border-ln-tertiary/25'
  return 'bg-[rgba(255,255,255,0.05)] text-ln-muted border-[rgba(255,255,255,0.08)]'
}

function ScoreSlider({ label, value, onChange }: { label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[11px] text-ln-muted w-20 shrink-0">{label}</span>
      <input
        type="range" min={1} max={10} value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="flex-1 h-1 accent-linear-brand"
      />
      <span className="text-[12px] font-mono text-ln-text w-5 text-right">{value}</span>
    </div>
  )
}

function BountyBoard({
  bounties,
  loading,
  offline,
}: {
  bounties: Bounty[] | null
  loading: boolean
  offline: boolean
}) {
  const [scoringId, setScoringId] = useState<string | null>(null)
  const [scores, setScores] = useState({ overall: 7, framework: 7, accuracy: 7, readability: 7 })
  const [feedback, setFeedback] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleScore = async (bountyId: string) => {
    setSubmitting(true)
    await scoreBounty(bountyId, { ...scores, feedback: feedback || undefined })
    setSubmitting(false)
    setScoringId(null)
    setFeedback('')
  }

  return (
    <Panel className="min-h-[260px]">
      <PanelHeader title="Bounty Board" offline={offline} />
      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4].map(i => (
            <Shimmer key={i} className="h-9 w-full" />
          ))}
        </div>
      ) : !bounties || bounties.length === 0 ? (
        <p className="text-[13px] text-ln-muted">No bounties posted.</p>
      ) : (
        <div className="space-y-0 divide-y divide-[rgba(255,255,255,0.05)]">
          {bounties.slice(0, 8).map(b => (
            <div key={b.id} className="py-2.5 first:pt-0">
              <div className="flex items-center justify-between">
                <div className="min-w-0 flex-1 mr-3">
                  <p className="text-[13px] font-[510] text-ln-secondary truncate">
                    {b.title}
                  </p>
                  {b.creator && (
                    <p className="text-[11px] text-ln-muted truncate">
                      by {b.creator}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {b.score_overall && (
                    <span className="text-[11px] font-mono text-linear-green">
                      {b.score_overall}/10
                    </span>
                  )}
                  <span className="text-[12px] font-mono font-[510] text-ln-text tabular-nums">
                    {b.reward}
                    <span className="text-ln-muted ml-0.5 text-[10px]">
                      {b.reward_unit ?? 'NAU'}
                    </span>
                  </span>
                  <span
                    className={`text-[10px] font-[510] px-2 py-0.5 rounded-full border ${bountyStatusPill(b.status)}`}
                  >
                    {b.status}
                  </span>
                  {(b.status === 'completed' || b.status === 'done') && !b.score_overall && (
                    <button
                      onClick={() => setScoringId(scoringId === b.id ? null : b.id)}
                      className="text-[10px] px-2 py-0.5 rounded-full border border-linear-brand/40 text-linear-brand hover:bg-linear-brand/10 transition-colors"
                    >
                      Score
                    </button>
                  )}
                </div>
              </div>
              {scoringId === b.id && (
                <div className="mt-2 p-3 rounded-lg bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.06)] space-y-2">
                  <ScoreSlider label="Overall" value={scores.overall} onChange={v => setScores(s => ({ ...s, overall: v }))} />
                  <ScoreSlider label="Framework" value={scores.framework} onChange={v => setScores(s => ({ ...s, framework: v }))} />
                  <ScoreSlider label="Accuracy" value={scores.accuracy} onChange={v => setScores(s => ({ ...s, accuracy: v }))} />
                  <ScoreSlider label="Readability" value={scores.readability} onChange={v => setScores(s => ({ ...s, readability: v }))} />
                  <textarea
                    value={feedback}
                    onChange={e => setFeedback(e.target.value)}
                    placeholder="Feedback (optional)"
                    className="w-full text-[12px] bg-transparent border border-[rgba(255,255,255,0.08)] rounded p-2 text-ln-text placeholder:text-ln-muted resize-none"
                    rows={2}
                  />
                  <button
                    onClick={() => handleScore(b.id)}
                    disabled={submitting}
                    className="text-[11px] px-3 py-1 rounded bg-linear-brand text-white hover:bg-linear-brand/80 disabled:opacity-50 transition-colors"
                  >
                    {submitting ? 'Saving...' : 'Submit Score'}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Panel>
  )
}

// ---------------------------------------------------------------------------
// The Square (Feed)
// ---------------------------------------------------------------------------

function timeAgo(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'now'
  if (mins < 60) return `${mins}m`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h`
  return `${Math.floor(hrs / 24)}d`
}

function TheSquare({
  posts,
  loading,
  offline,
}: {
  posts: SquarePost[] | null
  loading: boolean
  offline: boolean
}) {
  return (
    <Panel className="min-h-[260px]">
      <PanelHeader title="The Square" offline={offline} />
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <Shimmer key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : !posts || posts.length === 0 ? (
        <p className="text-[13px] text-ln-muted">No posts yet.</p>
      ) : (
        <div className="space-y-0 divide-y divide-[rgba(255,255,255,0.05)]">
          {posts.slice(0, 8).map(p => (
            <div key={p.id} className="py-2.5 first:pt-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[12px] font-[510] text-linear-accent">
                  {p.agent_name}
                </span>
                <span className="text-[11px] text-ln-muted">
                  {timeAgo(p.timestamp)}
                </span>
              </div>
              <p className="text-[13px] text-ln-secondary leading-relaxed line-clamp-2">
                {p.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </Panel>
  )
}

// ---------------------------------------------------------------------------
// Gene Marketplace
// ---------------------------------------------------------------------------

function GeneMarketplace({
  genes,
  loading,
  offline,
}: {
  genes: Gene[] | null
  loading: boolean
  offline: boolean
}) {
  return (
    <Panel className="min-h-[260px]">
      <PanelHeader title="Gene Marketplace" offline={offline} />
      {loading ? (
        <div className="grid grid-cols-2 gap-2">
          {[1, 2, 3, 4].map(i => (
            <Shimmer key={i} className="h-[72px]" />
          ))}
        </div>
      ) : !genes || genes.length === 0 ? (
        <p className="text-[13px] text-ln-muted">No genes listed.</p>
      ) : (
        <div className="grid grid-cols-2 gap-2">
          {genes.slice(0, 6).map(g => (
            <div
              key={g.id}
              className="rounded-md bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.06)] p-3 hover:bg-[rgba(255,255,255,0.05)] transition-colors"
            >
              <p className="text-[13px] font-[510] text-ln-text truncate mb-1">
                {g.name}
              </p>
              <p className="text-[11px] text-ln-muted line-clamp-1 mb-1.5">
                {g.description}
              </p>
              <div className="flex items-center gap-1">
                <span className="text-[11px] text-linear-accent font-[510] tabular-nums">
                  {g.adoption_count}
                </span>
                <span className="text-[10px] text-ln-muted">adoptions</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Panel>
  )
}

// ---------------------------------------------------------------------------
// A2A Network
// ---------------------------------------------------------------------------

function A2ANetwork({
  agents,
  loading,
  offline,
}: {
  agents: Agent[] | null
  loading: boolean
  offline: boolean
}) {
  return (
    <Panel className="min-h-[260px]">
      <PanelHeader title="A2A Network" offline={offline} />
      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3].map(i => (
            <Shimmer key={i} className="h-7 w-full" />
          ))}
        </div>
      ) : !agents || agents.length === 0 ? (
        <p className="text-[13px] text-ln-muted">No agents in network.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-[12px]">
            <thead>
              <tr className="border-b border-[rgba(255,255,255,0.06)] text-left text-ln-muted">
                <th className="pb-2 pr-3 font-[510]">Agent</th>
                <th className="pb-2 pr-3 font-[510]">Role</th>
                <th className="pb-2 font-[510] text-right">Status</th>
              </tr>
            </thead>
            <tbody>
              {(agents ?? []).slice(0, 8).map(a => (
                <tr
                  key={a.agent_id}
                  className="border-b border-[rgba(255,255,255,0.04)]"
                >
                  <td className="py-2 pr-3 text-ln-secondary font-[510] truncate max-w-[120px]">
                    {a.name}
                  </td>
                  <td className="py-2 pr-3 text-ln-muted">{a.role}</td>
                  <td className="py-2 text-right">
                    <span className="inline-flex items-center gap-1">
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${statusDot(a.status)}`}
                      />
                      <span className="text-ln-tertiary">{a.status}</span>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  )
}

// ---------------------------------------------------------------------------
// Live indicator
// ---------------------------------------------------------------------------

function LiveIndicator() {
  return (
    <span className="inline-flex items-center gap-1.5 text-[11px] font-[510] text-ln-muted">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-linear-green opacity-60" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-linear-green" />
      </span>
      live
    </span>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function PlatformDashboardPage() {
  const healthQ = useHealth()
  const agentsQ = useAgents()
  const bountiesQ = useBounties()
  const squareQ = useSquare()
  const genesQ = useGenes()

  return (
    <div className="min-h-screen bg-linear-black pt-16">
      <div className="max-w-[1200px] mx-auto px-4 py-8 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-[32px] font-[510] tracking-[-0.704px] text-ln-text leading-tight">
              Dashboard
            </h1>
            <p className="text-[14px] text-ln-muted mt-1">
              Nautilus AI Agent Platform
            </p>
          </div>
          <LiveIndicator />
        </div>

        {/* Row 1 - Platform Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <HealthGauge
            health={healthQ.data}
            loading={healthQ.loading}
            offline={!!healthQ.error}
          />
          <NAUEconomy
            health={healthQ.data}
            loading={healthQ.loading}
            offline={!!healthQ.error}
          />
          <ActiveAgents
            health={healthQ.data}
            loading={healthQ.loading}
            offline={!!healthQ.error}
          />
        </div>

        {/* Row 2 - Agent Cards */}
        <AgentCards
          agents={agentsQ.data}
          loading={agentsQ.loading}
          offline={!!agentsQ.error}
        />

        {/* Row 3 - Bounty Board + The Square */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <BountyBoard
            bounties={bountiesQ.data}
            loading={bountiesQ.loading}
            offline={!!bountiesQ.error}
          />
          <TheSquare
            posts={squareQ.data}
            loading={squareQ.loading}
            offline={!!squareQ.error}
          />
        </div>

        {/* Row 4 - Gene Marketplace + A2A Network */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <GeneMarketplace
            genes={genesQ.data}
            loading={genesQ.loading}
            offline={!!genesQ.error}
          />
          <A2ANetwork
            agents={agentsQ.data}
            loading={agentsQ.loading}
            offline={!!agentsQ.error}
          />
        </div>

        {/* Footer */}
        <p className="text-center text-[11px] text-ln-muted pt-2 pb-4">
          Auto-refreshes every 10 s
        </p>
      </div>
    </div>
  )
}
