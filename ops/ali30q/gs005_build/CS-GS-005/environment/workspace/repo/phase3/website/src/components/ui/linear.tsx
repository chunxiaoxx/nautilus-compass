import { ReactNode } from 'react'

/**
 * 共享 Linear/Claude 暗色设计语言组件(从指挥中心 /control 抽出 · 全站融合复用)。
 *
 * 设计 token(tailwind.config):
 *   底色 bg-linear-black · 面板 bg-linear-panel/surface · 主色 linear-brand/accent
 *   文字 ln-text(主)/ ln-secondary / ln-tertiary / ln-muted · 边框 ln-border
 *   状态 linear-green(通过)· #eb5757(失败)
 *
 * 用法:页面用 <PageShell>,卡片/分区用 <Panel>,标签用 <Badge>。
 */

export function PageShell({
  title,
  subtitle,
  right,
  children,
  maxWidth = 'max-w-7xl',
}: {
  title?: ReactNode
  subtitle?: ReactNode
  right?: ReactNode
  children: ReactNode
  maxWidth?: string
}) {
  return (
    <div className="min-h-screen bg-linear-black py-8 px-4">
      <div className={`${maxWidth} mx-auto space-y-6`}>
        {(title || right) && (
          <div className="flex items-end justify-between flex-wrap gap-3">
            <div>
              {title && (
                <h1 className="text-3xl font-[560] text-ln-text tracking-[-0.5px]">{title}</h1>
              )}
              {subtitle && <p className="text-ln-tertiary text-[13px] mt-1">{subtitle}</p>}
            </div>
            {right && <div className="text-right shrink-0">{right}</div>}
          </div>
        )}
        {children}
      </div>
    </div>
  )
}

export function Panel({
  title,
  children,
  className = '',
  interactive = false,
}: {
  title?: ReactNode
  children: ReactNode
  className?: string
  interactive?: boolean
}) {
  return (
    <div
      className={`rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.08)] p-5 ${
        interactive ? 'hover:bg-[rgba(255,255,255,0.04)] transition' : ''
      } ${className}`}
    >
      {title && (
        <h3 className="text-[12px] font-[510] uppercase tracking-[0.4px] text-ln-tertiary mb-4">
          {title}
        </h3>
      )}
      {children}
    </div>
  )
}

type BadgeTone = 'default' | 'accent' | 'pass' | 'fail' | 'muted'

const BADGE_TONES: Record<BadgeTone, string> = {
  default: 'bg-[rgba(255,255,255,0.06)] text-ln-secondary border-[rgba(255,255,255,0.1)]',
  accent: 'bg-linear-brand/15 text-linear-hover border-linear-brand/30',
  pass: 'bg-[rgba(39,166,68,0.15)] text-linear-green border-[rgba(39,166,68,0.3)]',
  fail: 'bg-[rgba(235,87,87,0.15)] text-[#eb5757] border-[rgba(235,87,87,0.3)]',
  muted: 'bg-[rgba(255,255,255,0.04)] text-ln-tertiary border-[rgba(255,255,255,0.08)]',
}

export function Badge({
  children,
  tone = 'default',
  className = '',
}: {
  children: ReactNode
  tone?: BadgeTone
  className?: string
}) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-[450] border ${BADGE_TONES[tone]} ${className}`}
    >
      {children}
    </span>
  )
}
