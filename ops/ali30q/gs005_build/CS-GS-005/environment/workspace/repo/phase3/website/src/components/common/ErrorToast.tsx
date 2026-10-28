import { X } from 'lucide-react'

interface ErrorToastProps {
  message: string
  onClose: () => void
  onRetry?: () => void
}

export const ErrorToast = ({ message, onClose, onRetry }: ErrorToastProps) => {
  return (
    <div className="fixed bottom-4 right-4 bg-red-500 text-white p-4 rounded-lg shadow-lg max-w-md z-50">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="font-semibold mb-1">操作失败</p>
          <p className="text-sm">{message}</p>
        </div>
        <button onClick={onClose} className="ml-4 hover:bg-red-600 rounded p-1">
          <X size={20} />
        </button>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 w-full bg-white text-red-500 py-2 rounded font-semibold hover:bg-red-50 transition-colors"
        >
          重试
        </button>
      )}
    </div>
  )
}
