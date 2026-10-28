export type TaskStatus = 'open' | 'in_progress' | 'completed' | 'expired'

export type TaskType = 'development' | 'design' | 'testing' | 'documentation' | 'research'

export interface Task {
  id: string
  title: string
  description: string
  type: TaskType
  reward: number
  deadline: string
  status: TaskStatus
  createdAt: string
  applicants: number
  requirements: string[]
}

export interface TaskFilters {
  search: string
  types: TaskType[]
  rewardRange: [number, number]
  status: TaskStatus[]
  deadline?: string
}
