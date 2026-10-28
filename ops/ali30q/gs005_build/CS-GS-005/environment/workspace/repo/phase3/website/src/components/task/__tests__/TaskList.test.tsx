import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TaskList from '../TaskList'
import { Task } from '../../../types/task'

describe('TaskList', () => {
  const mockTasks: Task[] = [
    {
      id: '1',
      title: '任务1',
      description: '描述1',
      type: 'development',
      status: 'open',
      reward: 1000,
      deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      applicants: 5,
      createdAt: new Date().toISOString(),
      requirements: []
    },
    {
      id: '2',
      title: '任务2',
      description: '描述2',
      type: 'design',
      status: 'open',
      reward: 2000,
      deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
      applicants: 3,
      createdAt: new Date().toISOString(),
      requirements: []
    }
  ]

  const mockOnViewDetails = vi.fn()
  const mockOnPageChange = vi.fn()

  it('should render loading state', () => {
    render(
      <TaskList
        tasks={[]}
        loading={true}
      onViewDetails={mockOnViewDetails}
        currentPage={1}
        totalPages={1}
        onPageChange={mockOnPageChange}
      />
    )

    expect(screen.getByText('加载中...')).toBeInTheDocument()
  })

  it('should render empty state when no tasks', () => {
    render(
      <TaskList
        tasks={[]}
        loading={false}
        onViewDetails={mockOnViewDetails}
        currentPage={1}
        totalPages={1}
        onPageChange={mockOnPageChange}
      />
    )

    expect(screen.getByText('暂无任务')).toBeInTheDocument()
    expect(screen.getByText('没有找到符合条件的任务')).toBeInTheDocument()
  })

  it('should render task cards', () => {
    render(
      <TaskList
        tasks={mockTasks}
        loading={false}
        onViewDetails={mockOnViewDetails}
        currentPage={1}
        totalPages={1}
        onPageChange={mockOnPageChange}
      />
    )

    expect(screen.getByText('任务1')).toBeInTheDocument()
    expect(screen.getByText('任务2')).toBeInTheDocument()
  })

  it('should not render pagination when only one page', () => {
  render(
      <TaskList
        tasks={mockTasks}
        loading={false}
        onViewDetails={mockOnViewDetails}
        currentPage={1}
        totalPages={1}
        onPageChange={mockOnPageChange}
      />
    )

    expect(screen.queryByText('上一页')).not.toBeInTheDocument()
    expect(screen.queryByText('下一页')).not.toBeInTheDocument()
  })

  it('should render pagination when multiple pages', () => {
    render(
    <TaskList
     tasks={mockTasks}
        loading={false}
      onViewDetails={mockOnViewDetails}
      currentPage={1}
        totalPages={3}
        onPageChange={mockOnPageChange}
      />
    )

    expect(screen.getByText('上一页')).toBeInTheDocument()
    expect(screen.getByText('下一页')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('should disable previous button on first page', () => {
    render(
   <TaskList
        tasks={mockTasks}
        loading={false}
        onViewDetails={mockOnViewDetails}
        currentPage={1}
        totalPages={3}
        onPageChange={mockOnPageChange}
      />
    )

    const prevButton = screen.getByText('上一页')
    expect(prevButton).toBeDisabled()
  })

  it('should disable next button on last page', () => {
    render(
      <TaskList
        tasks={mockTasks}
        loading={false}
        onViewDetails={mockOnViewDetails}
      currentPage={3}
        totalPages={3}
        onPageChange={mockOnPageChange}
      />
    )

    const nextButton = screen.getByText('下一页')
    expect(nextButton).toBeDisabled()
  })

  it('should call onPageChange when clicking next button', () => {
    render(
      <TaskList
        tasks={mockTasks}
        loading={false}
      onViewDetails={mockOnViewDetails}
        currentPage={1}
        totalPages={3}
        onPageChange={mockOnPageChange}
      />
    )

    const nextButton = screen.getByText('下一页')
    fireEvent.click(nextButton)

    expect(mockOnPageChange).toHaveBeenCalledWith(2)
  })

  it('should call onPageChange when clicking previous button', () => {
    render(
      <TaskList
        tasks={mockTasks}
        loading={false}
        onViewDetails={mockOnViewDetails}
        currentPage={2}
        totalPages={3}
        onPageChange={mockOnPageChange}
      />
    )

    const prevButton = screen.getByText('上一页')
    fireEvent.click(prevButton)

    expect(mockOnPageChange).toHaveBeenCalledWith(1)
  })

  it('should call onPageChange when clicking page number', () => {
    render(
      <TaskList
        tasks={mockTasks}
      loading={false}
        onViewDetails={mockOnViewDetails}
        currentPage={1}
        totalPages={3}
        onPageChange={mockOnPageChange}
      />
    )

    const page2Button = screen.getByText('2')
    fireEvent.click(page2Button)

  expect(mockOnPageChange).toHaveBeenCalledWith(2)
  })

  it('should highlight current page', () => {
    render(
      <TaskList
        tasks={mockTasks}
        loading={false}
     onViewDetails={mockOnViewDetails}
        currentPage={2}
     totalPages={3}
     onPageChange={mockOnPageChange}
      />
    )

    const page2Button = screen.getByText('2')
    expect(page2Button).toHaveClass('gradient-primary')
  })
})
