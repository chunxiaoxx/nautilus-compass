import { TaskType, TaskStatus } from '../../types/task'

interface FilterPanelProps {
  selectedTypes: TaskType[]
  onTypesChange: (types: TaskType[]) => void
  rewardRange: [number, number]
  onRewardRangeChange: (range: [number, number]) => void
  selectedStatuses: TaskStatus[]
  onStatusesChange: (statuses: TaskStatus[]) => void
  onReset: () => void
}

const taskTypes: { value: TaskType; label: string }[] = [
  { value: 'development', label: '开发' },
  { value: 'design', label: '设计' },
  { value: 'testing', label: '测试' },
  { value: 'documentation', label: '文档' },
  { value: 'research', label: '研究' }
]

const taskStatuses: { value: TaskStatus; label: string; color: string }[] = [
  { value: 'open', label: '开放中', color: 'text-green-400' },
  { value: 'in_progress', label: '进行中', color: 'text-blue-400' },
  { value: 'completed', label: '已完成', color: 'text-gray-400' },
  { value: 'expired', label: '已过期', color: 'text-red-400' }
]

export default function FilterPanel({
  selectedTypes,
  onTypesChange,
  rewardRange,
  onRewardRangeChange,
  selectedStatuses,
  onStatusesChange,
  onReset
}: FilterPanelProps) {
  const toggleType = (type: TaskType) => {
    const newTypes = selectedTypes.includes(type)
      ? selectedTypes.filter(t => t !== type)
      : [...selectedTypes, type]
    onTypesChange(newTypes)
  }

  const toggleStatus = (status: TaskStatus) => {
    const newStatuses = selectedStatuses.includes(status)
      ? selectedStatuses.filter(s => s !== status)
      : [...selectedStatuses, status]
    onStatusesChange(newStatuses)
  }

  return (
    <div className="glass rounded-xl p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">筛选条件</h3>
        <button
          onClick={onReset}
          className="text-sm text-primary-400 hover:text-primary-300 transition-colors"
        >
          重置
        </button>
      </div>

      {/* Task Types */}
      <div>
        <h4 className="text-sm font-medium text-gray-300 mb-3">任务类型</h4>
        <div className="space-y-2">
          {taskTypes.map(({ value, label }) => (
            <label key={value} className="flex items-center cursor-pointer group">
              <input
                type="checkbox"
                checked={selectedTypes.includes(value)}
                onChange={() => toggleType(value)}
                className="w-4 h-4 rounded border-dark-600 bg-dark-700 text-primary-500 focus:ring-primary-500 focus:ring-offset-0"
              />
              <span className="ml-3 text-gray-300 group-hover:text-white transition-colors">
                {label}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Reward Range */}
      <div>
        <h4 className="text-sm font-medium text-gray-300 mb-3">奖励范围</h4>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <input
              type="number"
              value={rewardRange[0]}
              onChange={(e) => onRewardRangeChange([Number(e.target.value), rewardRange[1]])}
              placeholder="最低"
              className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white text-sm focus:outline-none focus:border-primary-500"
            />
            <span className="text-gray-400">-</span>
            <input
              type="number"
              value={rewardRange[1]}
              onChange={(e) => onRewardRangeChange([rewardRange[0], Number(e.target.value)])}
              placeholder="最高"
              className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white text-sm focus:outline-none focus:border-primary-500"
            />
          </div>
          <div className="text-xs text-gray-400">
            {rewardRange[0]} - {rewardRange[1]} USDT
          </div>
        </div>
      </div>

      {/* Status */}
      <div>
        <h4 className="text-sm font-medium text-gray-300 mb-3">任务状态</h4>
        <div className="space-y-2">
          {taskStatuses.map(({ value, label, color }) => (
            <label key={value} className="flex items-center cursor-pointer group">
              <input
                type="checkbox"
                checked={selectedStatuses.includes(value)}
                onChange={() => toggleStatus(value)}
                className="w-4 h-4 rounded border-dark-600 bg-dark-700 text-primary-500 focus:ring-primary-500 focus:ring-offset-0"
              />
              <span className={`ml-3 ${color} group-hover:opacity-80 transition-opacity`}>
                {label}
              </span>
            </label>
          ))}
        </div>
      </div>
    </div>
  )
}
