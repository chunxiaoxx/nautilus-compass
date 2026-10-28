import { Task } from '../../types/task'
import TaskCard from './TaskCard'

interface TaskListProps {
  tasks: Task[]
  loading: boolean
  onViewDetails: (taskId: string) => void
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

export default function TaskList({
  tasks,
  loading,
  onViewDetails,
  currentPage,
  totalPages,
  onPageChange
}: TaskListProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400">加载中...</p>
        </div>
      </div>
    )
  }

  if (tasks.length === 0) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <svg
            className="w-16 h-16 mx-auto mb-4 text-gray-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="text-xl font-semibold text-white mb-2">暂无任务</h3>
          <p className="text-gray-400">没有找到符合条件的任务</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {tasks.map((task) => (
          <TaskCard key={task.id} task={task} onViewDetails={onViewDetails} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-8">
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="px-4 py-2 bg-dark-800 text-white rounded-lg hover:bg-dark-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            上一页
          </button>

          <div className="flex items-center gap-2">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
              <button
                key={page}
                onClick={() => onPageChange(page)}
                className={`w-10 h-10 rounded-lg transition-colors ${
                  page === currentPage
                    ? 'gradient-primary text-white'
                    : 'bg-dark-800 text-gray-400 hover:bg-dark-700'
                }`}
              >
                {page}
              </button>
            ))}
          </div>

          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="px-4 py-2 bg-dark-800 text-white rounded-lg hover:bg-dark-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  )
}
