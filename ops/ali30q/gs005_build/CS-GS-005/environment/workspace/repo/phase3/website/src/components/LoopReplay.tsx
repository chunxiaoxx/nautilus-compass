/**
 * LoopReplay · 一条 RSI+FDE 闭环的竖向 scrollytelling 回放。
 *
 * 每个 step = { phase, label, data }。竖向时间线渲染:phase 标签 → label →
 * 关键 data 字段。高亮里程碑步骤:
 *   - radix_rsi:data.escapes_noise === true(首个真外部增量 escapes 噪声)
 *   - data_001_fde:data.overall_pass === true(买方题过 QC)
 * 数据来自 /api/platform/control-plane 的 loops[]。
 */

export interface LoopStep {
  phase: string
  label: string
  data: Record<string, unknown>
}

export interface Loop {
  loop_id: string
  title: string
  steps: LoopStep[]
}

function isMilestone(step: LoopStep): boolean {
  return step.data?.escapes_noise === true || step.data?.overall_pass === true
}

function formatValue(value: unknown): string {
  if (value === true) return 'true'
  if (value === false) return 'false'
  if (value === null || value === undefined) return '—'
  if (typeof value === 'number') return String(value)
  return String(value)
}

function StepDataRows({ data }: { data: Record<string, unknown> }) {
  const entries = Object.entries(data || {})
  if (entries.length === 0) return null
  return (
    <dl className="mt-2 grid grid-cols-1 gap-1 sm:grid-cols-2">
      {entries.map(([key, value]) => {
        const milestone = key === 'escapes_noise' || key === 'overall_pass'
        return (
          <div
            key={key}
            className="flex items-baseline justify-between gap-2 rounded bg-[rgba(255,255,255,0.02)] px-2 py-1"
          >
            <dt className="font-mono text-[11px] text-ln-tertiary">{key}</dt>
            <dd
              className={`font-mono text-[12px] tabular-nums ${
                milestone && value === true
                  ? 'font-semibold text-linear-green'
                  : 'text-ln-secondary'
              }`}
            >
              {formatValue(value)}
            </dd>
          </div>
        )
      })}
    </dl>
  )
}

export default function LoopReplay({ loop }: { loop: Loop }) {
  return (
    <section
      className="rounded-lg border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.02)] p-5"
      aria-label={`闭环回放 ${loop.loop_id}`}
    >
      <header className="mb-4">
        <span className="font-mono text-[10px] uppercase tracking-wider text-ln-muted">
          {loop.loop_id}
        </span>
        <h3 className="mt-1 text-[15px] font-[510] leading-snug tracking-[-0.165px] text-ln-text">
          {loop.title}
        </h3>
      </header>

      {loop.steps.length === 0 ? (
        <p className="text-[13px] text-ln-tertiary">(无回放步骤)</p>
      ) : (
        <ol className="relative ml-2 space-y-4 border-l border-[rgba(255,255,255,0.1)] pl-5">
          {loop.steps.map((step, idx) => {
            const milestone = isMilestone(step)
            return (
              <li key={`${step.phase}-${idx}`} className="relative">
                {/* 时间线节点 */}
                <span
                  className={`absolute -left-[27px] top-1 h-3 w-3 rounded-full border-2 ${
                    milestone
                      ? 'border-linear-green bg-linear-green shadow-[0_0_8px_rgba(39,166,68,0.7)]'
                      : 'border-[rgba(255,255,255,0.25)] bg-linear-panel'
                  }`}
                  aria-hidden="true"
                />
                <div
                  className={`rounded-md border p-3 ${
                    milestone
                      ? 'border-linear-green/40 bg-linear-green/5'
                      : 'border-[rgba(255,255,255,0.06)] bg-[rgba(255,255,255,0.015)]'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-[10px] uppercase tracking-wider text-ln-muted">
                      {step.phase}
                    </span>
                    {milestone && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-linear-green/15 px-2 py-0.5 text-[10px] font-semibold text-linear-green">
                        ✓ 里程碑
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-[13px] font-[510] leading-snug text-ln-text">
                    {step.label}
                  </p>
                  <StepDataRows data={step.data} />
                </div>
              </li>
            )
          })}
        </ol>
      )}
    </section>
  )
}
