import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TaskCard from '../TaskCard'
import { Task } from '../../../types/task'

describe('TaskCard', () => {
  const mockTask: Task = {
    id: '1',
    title: '开发新功能',
    description: '这是一个测试任务的描述',
    type: 'development',
    status: 'open',
    reward: 1000,
    deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days from now
    applicants: 5,
    createdAt: new Date().toISOString(),
    requirements: []
  }

  const mockOnViewDetails = vi.fn()

  it('should render task title', () => {
    render(<TaskCard task={mockTask} onViewDetails={mockOnViewDetails} />)

    expect(screen.getByText('开发新功能')).toBeInTheDocument()
  })

  it('should render task description', () => {
    render(<TaskCard task={mockTask} onViewDetails={mockOnViewDetails} />)

    expect(screen.getByText('这是一个测试任务的描述')).toBeInTheDocument()
  })

  it('should render task type label', () => {
    render(<TaskCard task={mockTask} onViewDetails={mockOnViewDetails} />)

    expect(screen.getByText('开发')).toBeInTheDocument()
  })

  it('should render task status label', () => {
    render(<TaskCard task={mockTask} onViewDetails={mockOnViewDetails} />)

    expect(screen.getByText('开放中')).toBeInTheDocument()
  })

  it('should render reward amount', () => {
    render(<TaskCard task={mockTask} onViewDetails={mockOnViewDetails} />)

    expect(screen.getByText('1000 USDT')).toBeInTheDocument()
  })

  it('should render applicants count', () => {
    render(<TaskCard task={mockTask} onViewDetails={mockOnViewDetails} />)

    expect(screen.getByText('5 人申请')).toBeInTheDocument()
  })

  it('should render days left until deadline', () => {
    render(<TaskCard task={mockTask} onViewDetails={mockOnViewDetails} />)

    expect(screen.getByText('7天后截止')).toBeInTheDocument()
  })

  it('should show "已截止" for expired tasks', () => {
    const expiredTask = {
      ...mockTask,
      deadline: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString() // 1 day ago
    }

    render(<TaskCard task={expiredTask} onViewDetails={mockOnViewDetails} />)

    expect(screen.getByText('已截止')).toBeInTheDocument()
  })

  it('should call onViewDetails when button is clicked', () => {
    render(<TaskCard task={mockTask} onViewDetails={mockOnViewDetails} />)

    const button = screen.getByText('查看详情')
    fireEvent.click(button)

    expect(mockOnViewDetails).toHaveBeenCalledWith('1')
    expect(mockOnViewDetails).toHaveBeenCalledTimes(1)
  })

  it('should render different task types correctly', () => {
    const designTask = { ...mockTask, type: 'design' as const }
    const { rerender } = render(<TaskCard task={designTask} onViewDetails={mockOnViewDetails} />)
    expect(screen.getByText('设计')).toBeInTheDocument()

  const testingTask = { ...mockTask, type: 'testing' as const }
    rerender(<TaskCard task={testingTask} onViewDetails={mockOnViewDetails} />)
    expect(screen.getByText('测试')).toBeInTheDocument()

    const documentationTask = { ...mockTask, type: 'documentation' as const }
    rerender(<TaskCard task={documentationTask} onViewDetails={mockOnViewDetails} />)
    expect(screen.getByText('文档')).toBeInTheDocument()

    const researchTask = { ...mockTask, type: 'research' as const }
    rerender(<TaskCard task={researchTask} onViewDetails={mockOnViewDetails} />)
    expect(screen.getByText('研究')).toBeInTheDocument()
  })
  it('should render different task statuses correctly', () => {
    const inProgressTask = { ...mockTask, status: 'in_progress' as const }
    const { rerender } = render(<TaskCard task={inProgressTask} onViewDetails={mockOnViewDetails} />)
    expect(screen.getByText('进行中')).toBeInTheDocument()

    const completedTask = { ...mockTask, status: 'completed' as const }
    rerender(<TaskCard task={completedTask} onViewDetails={mockOnViewDetails} />)
    expect(screen.getByText('已完成')).toBeInTheDocument()

    const expiredTask = { ...mockTask, status: 'expired' as const }
    rerender(<TaskCard task={expiredTask} onViewDetails={mockOnViewDetails} />)
    expect(screen.getByText('已过期')).toBeInTheDocument()
  })

  it('should apply hover effect class', () => {
    const { container } = render(<TaskCard task={mockTask} onViewDetails={mockOnViewDetails} />)

    const card = container.firstChild
    expect(card).toHaveClass('hover:scale-[1.02]')
    expect(card).toHaveClass('transition-transform')
  })
})
