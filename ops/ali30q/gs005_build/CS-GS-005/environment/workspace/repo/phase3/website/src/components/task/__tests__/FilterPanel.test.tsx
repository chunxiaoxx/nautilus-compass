import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import FilterPanel from '../FilterPanel'
import { TaskType, TaskStatus } from '../../../types/task'

describe('FilterPanel', () => {
  const mockOnTypesChange = vi.fn()
  const mockOnRewardRangeChange = vi.fn()
  const mockOnStatusesChange = vi.fn()
  const mockOnReset = vi.fn()

  const defaultProps = {
    selectedTypes: [] as TaskType[],
    onTypesChange: mockOnTypesChange,
    rewardRange: [0, 10000] as [number, number],
    onRewardRangeChange: mockOnRewardRangeChange,
    selectedStatuses: [] as TaskStatus[],
  onStatusesChange: mockOnStatusesChange,
    onReset: mockOnReset
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render filter panel title', () => {
    render(<FilterPanel {...defaultProps} />)

    expect(screen.getByText('筛选条件')).toBeInTheDocument()
  })

  it('should render reset button', () => {
    render(<FilterPanel {...defaultProps} />)

    expect(screen.getByText('重置')).toBeInTheDocument()
  })

  it('should call onReset when clicking reset button', () => {
    render(<FilterPanel {...defaultProps} />)

    const resetButton = screen.getByText('重置')
    fireEvent.click(resetButton)

    expect(mockOnReset).toHaveBeenCalledTimes(1)
  })

  it('should render all task type checkboxes', () => {
    render(<FilterPanel {...defaultProps} />)

    expect(screen.getByText('开发')).toBeInTheDocument()
    expect(screen.getByText('设计')).toBeInTheDocument()
    expect(screen.getByText('测试')).toBeInTheDocument()
    expect(screen.getByText('文档')).toBeInTheDocument()
    expect(screen.getByText('研究')).toBeInTheDocument()
  })

  it('should render all task status checkboxes', () => {
    render(<FilterPanel {...defaultProps} />)

    expect(screen.getByText('开放中')).toBeInTheDocument()
    expect(screen.getByText('进行中')).toBeInTheDocument()
    expect(screen.getByText('已完成')).toBeInTheDocument()
    expect(screen.getByText('已过期')).toBeInTheDocument()
  })

  it('should check selected task types', () => {
    render(<FilterPanel {...defaultProps} selectedTypes={['development', 'design']} />)

    const developmentCheckbox = screen.getByLabelText('开发') as HTMLInputElement
    const designCheckbox = screen.getByLabelText('设计') as HTMLInputElement
    const testingCheckbox = screen.getByLabelText('测试') as HTMLInputElement

    expect(developmentCheckbox.checked).toBe(true)
    expect(designCheckbox.checked).toBe(true)
  expect(testingCheckbox.checked).toBe(false)
  })

  it('should check selected task statuses', () => {
    render(<FilterPanel {...defaultProps} selectedStatuses={['open', 'in_progress']} />)

    const openCheckbox = screen.getByLabelText('开放中') as HTMLInputElement
    const inProgressCheckbox = screen.getByLabelText('进行中') as HTMLInputElement
  const completedCheckbox = screen.getByLabelText('已完成') as HTMLInputElement

    expect(openCheckbox.checked).toBe(true)
    expect(inProgressCheckbox.checked).toBe(true)
    expect(completedCheckbox.checked).toBe(false)
  })

  it('should call onTypesChange when toggling task type', () => {
    render(<FilterPanel {...defaultProps} />)

  const developmentCheckbox = screen.getByLabelText('开发')
    fireEvent.click(developmentCheckbox)

    expect(mockOnTypesChange).toHaveBeenCalledWith(['development'])
  })

  it('should call onTypesChange to remove type when unchecking', () => {
    render(<FilterPanel {...defaultProps} selectedTypes={['development', 'design']} />)

    const developmentCheckbox = screen.getByLabelText('开发')
    fireEvent.click(developmentCheckbox)

    expect(mockOnTypesChange).toHaveBeenCalledWith(['design'])
  })

  it('should call onStatusesChange when toggling task status', () => {
    render(<FilterPanel {...defaultProps} />)

    const openCheckbox = screen.getByLabelText('开放中')
    fireEvent.click(openCheckbox)

    expect(mockOnStatusesChange).toHaveBeenCalledWith(['open'])
  })

  it('should call onStatusesChange to remove status when unchecking', () => {
    render(<FilterPanel {...defaultProps} selectedStatuses={['open', 'in_progress']} />)

    const openCheckbox = screen.getByLabelText('开放中')
    fireEvent.click(openCheckbox)

    expect(mockOnStatusesChange).toHaveBeenCalledWith(['in_progress'])
  })

  it('should render reward range inputs', () => {
    render(<FilterPanel {...defaultProps} />)

    const minInput = screen.getByPlaceholderText('最低') as HTMLInputElement
    const maxInput = screen.getByPlaceholderText('最高') as HTMLInputElement

    expect(minInput.value).toBe('0')
    expect(maxInput.value).toBe('10000')
  })

  it('should display reward range text', () => {
    render(<FilterPanel {...defaultProps} rewardRange={[100, 5000]} />)
    expect(screen.getByText('100 - 5000 USDT')).toBeInTheDocument()
  })

  it('should call onRewardRangeChange when changing min value', () => {
    render(<FilterPanel {...defaultProps} />)

    const minInput = screen.getByPlaceholderText('最低')
    fireEvent.change(minInput, { target: { value: '500' } })

    expect(mockOnRewardRangeChange).toHaveBeenCalledWith([500, 10000])
  })
  it('should call onRewardRangeChange when changing max value', () => {
    render(<FilterPanel {...defaultProps} />)

    const maxInput = screen.getByPlaceholderText('最高')
    fireEvent.change(maxInput, { target: { value: '8000' } })

    expect(mockOnRewardRangeChange).toHaveBeenCalledWith([0, 8000])
  })

  it('should render section headers', () => {
    render(<FilterPanel {...defaultProps} />)

    expect(screen.getByText('任务类型')).toBeInTheDocument()
    expect(screen.getByText('奖励范围')).toBeInTheDocument()
    expect(screen.getByText('任务状态')).toBeInTheDocument()
  })
})
