import { useEffect } from 'react'

/**
 * DrillDownModal · 暗色 drill-down 弹层(指挥中心 admin 件).
 *
 * 受控组件:open 控制显隐 · onClose 关闭(ESC + 点遮罩 + 关闭按钮).
 * 内容由调用方传入(verdict 详情 / agent 字段),自身只管壳 + loading/error 态.
 * 复用 ln- / linear- 暗色 token,与 ControlCenterPage Panel 风格一致.
 */

interface DrillDownModalProps {
  open: boolean
  title: string
  loading: boolean
  error: string | null
  onClose: () => void
  children: React.ReactNode
}

export default function DrillDownModal({
  open,
  title,
  loading,
  error,
  onClose,
  children,
}: DrillDownModalProps) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onClick={onClose}
    >
      <div
        className="max-h-[80vh] w-full max-w-2xl overflow-y-auto rounded-lg border border-[rgba(255,255,255,0.12)] bg-linear-panel p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <h3 className="text-[15px] font-[560] leading-snug tracking-[-0.2px] text-ln-text">
            {title}
          </h3>
          <button
            onClick={onClose}
            aria-label="关闭"
            className="rounded-md border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.04)] px-2.5 py-1 text-[13px] text-ln-tertiary transition hover:bg-[rgba(255,255,255,0.08)] hover:text-ln-text"
          >
            ✕
          </button>
        </div>

        {loading && (
          <div className="animate-pulse space-y-2">
            <div className="h-5 w-2/3 rounded bg-[rgba(255,255,255,0.04)]" />
            <div className="h-5 w-1/2 rounded bg-[rgba(255,255,255,0.04)]" />
            <div className="h-5 w-3/4 rounded bg-[rgba(255,255,255,0.04)]" />
          </div>
        )}

        {!loading && error && (
          <div className="text-[13px] text-[#eb5757]">加载失败:{error}</div>
        )}

        {!loading && !error && children}
      </div>
    </div>
  )
}
