/**
 * PanelKit · 指挥中心共享展示原语(从 ControlCenterPage 抽出 · 子板块复用).
 *
 * Panel / Stat / Shimmer 与原 ControlCenterPage 内联版完全同形(暗色 ln-/linear- token),
 * 抽到这里让 src/components/control/* 子板块复用、避免重复定义、控制单文件行数.
 * Hint = 新增的"这是什么/怎么读"一句话注解(治"信息难懂")· tertiary 小字.
 */
import type { ReactNode } from 'react'

export function Panel({
  title,
  hint,
  children,
  className = '',
  action,
}: {
  title?: string
  hint?: string
  children: ReactNode
  className?: string
  action?: ReactNode
}) {
  return (
    <div
      className={`rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] p-5 ${className}`}
    >
      {(title || action) && (
        <div className="mb-1 flex items-start justify-between gap-3">
          {title && (
            <h3 className="text-[12px] font-[510] uppercase tracking-[0.4px] text-ln-tertiary">
              {title}
            </h3>
          )}
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}
      {hint && <Hint className="mb-3">{hint}</Hint>}
      {!hint && (title || action) && <div className="mb-3" />}
      {children}
    </div>
  )
}

/** 一句话注解 · "这是什么 / 怎么读" · tertiary 小字. */
export function Hint({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <p className={`text-[11px] leading-relaxed text-ln-muted ${className}`}>{children}</p>
  )
}

export function Shimmer({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse rounded bg-[rgba(255,255,255,0.04)] ${className}`} />
}

export function Stat({
  n,
  label,
  tone = 'text-ln-text',
}: {
  n: ReactNode
  label: string
  tone?: string
}) {
  return (
    <div className="flex items-baseline gap-2">
      <span className={`text-3xl font-[560] tabular-nums ${tone}`}>{n}</span>
      <span className="text-ln-tertiary text-[13px]">{label}</span>
    </div>
  )
}

/** 空态友好文案 · 统一样式. */
export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-md border border-dashed border-[rgba(255,255,255,0.1)] bg-[rgba(255,255,255,0.01)] px-4 py-6 text-center text-[12px] leading-relaxed text-ln-muted">
      {children}
    </div>
  )
}

/** 相对时间 · "3m ago" 风格(UTC 字符串容错). */
export function relTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const t = Date.parse(iso.replace(' ', 'T'))
  if (Number.isNaN(t)) return iso.slice(0, 19)
  const diff = Date.now() - t
  const m = Math.round(diff / 60000)
  if (m < 1) return '刚刚'
  if (m < 60) return `${m}m 前`
  const h = Math.round(m / 60)
  if (h < 24) return `${h}h 前`
  const d = Math.round(h / 24)
  return `${d}d 前`
}
