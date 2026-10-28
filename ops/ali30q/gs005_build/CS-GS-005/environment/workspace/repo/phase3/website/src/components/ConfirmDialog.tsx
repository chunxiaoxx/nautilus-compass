import { useEffect } from 'react'

/**
 * ConfirmDialog · 写动作前的确认框(指挥中心 admin 件).
 *
 * 每个会改变系统状态的 dispatch/goal 动作前必经此框 · 明示"将要执行什么".
 * 暗色 token(ln- / linear-)· ESC/点遮罩 = 取消 · 确认按钮高亮.
 */

interface ConfirmDialogProps {
  open: boolean
  title: string
  /** 将要执行的动作摘要(明示给操作者). */
  detail: React.ReactNode
  confirmLabel?: string
  busy?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export default function ConfirmDialog({
  open,
  title,
  detail,
  confirmLabel = '确认执行',
  busy = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !busy) onCancel()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, busy, onCancel])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onClick={() => !busy && onCancel()}
    >
      <div
        className="w-full max-w-md rounded-lg border border-[rgba(255,255,255,0.12)] bg-linear-panel p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-[15px] font-[560] tracking-[-0.2px] text-ln-text">{title}</h3>
        <div className="mt-3 rounded-md border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.02)] p-3 text-[13px] leading-relaxed text-ln-secondary">
          {detail}
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onCancel}
            disabled={busy}
            className="rounded-md border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.04)] px-3 py-1.5 text-[13px] font-[510] text-ln-tertiary transition hover:bg-[rgba(255,255,255,0.08)] hover:text-ln-text disabled:cursor-not-allowed disabled:opacity-50"
          >
            取消
          </button>
          <button
            onClick={onConfirm}
            disabled={busy}
            className="rounded-md border border-linear-green/40 bg-linear-green/15 px-3 py-1.5 text-[13px] font-[560] text-linear-green transition hover:bg-linear-green/25 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy ? '执行中…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
