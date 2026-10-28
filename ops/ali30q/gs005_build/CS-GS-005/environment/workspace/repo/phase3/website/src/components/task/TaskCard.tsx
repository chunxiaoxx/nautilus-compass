import { Task, TaskStatus, TaskType } from '../../types/task'

interface TaskCardProps {
  task: Task
  onViewDetails: (taskId: string) => void
}

const typeLabels: Record<TaskType, string> = {
  development: '开发',
  design: '设计',
  testing: '测试',
  documentation: '文档',
  research: '研究'
}

const statusConfig: Record<TaskStatus, { label: string; color: string; bgColor: string }> = {
  open: { label: '开放中', color: 'text-green-400', bgColor: 'bg-green-400/10' },
  in_progress: { label: '进行中', color: 'text-blue-400', bgColor: 'bg-blue-400/10' },
  completed: { label: '已完成', color: 'text-gray-400', bgColor: 'bg-gray-400/10' },
  expired: { label: '已过期', color: 'text-red-400', bgColor: 'bg-red-400/10' }
}

export default function TaskCard({ task, onViewDetails }: TaskCardProps) {
  const status = statusConfig[task.status]
  const daysLeft = Math.ceil(
    (new Date(task.deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
  )

  return (
    <div className="glass rounded-xl p-6 hover:scale-[1.02] transition-transform duration-300">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <span className="px-3 py-1 bg-primary-500/10 text-primary-400 text-xs font-medium rounded-full">
              {typeLabels[task.type]}
            </span>
            <span className={`px-3 py-1 ${status.bgColor} ${status.color} text-xs font-medium rounded-full`}>
              {status.label}
            </span>
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">{task.title}</h3>
        </div>
      </div>

      <p className="text-gray-400 text-sm mb-4 line-clamp-2">{task.description}</p>

      <div className="flex items-center gap-4 mb-4 text-sm text-gray-400">
        <div className="flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>{daysLeft > 0 ? `${daysLeft}天后截止` : '已截止'}</span>
        </div>
        <div className="flex items-center gap-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
          <span>{task.applicants} 人申请</span>
        </div>
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-dark-700">
        <div>
          <div className="text-sm text-gray-400 mb-1">奖励</div>
          <div className="text-2xl font-bold gradient-text">{task.reward} USDT</div>
        </div>
        <button
          onClick={() => onViewDetails(task.id)}
          className="px-6 py-2 gradient-primary text-white rounded-lg hover:opacity-90 transition-opacity"
        >
          查看详情
        </button>
      </div>
    </div>
  )
}
