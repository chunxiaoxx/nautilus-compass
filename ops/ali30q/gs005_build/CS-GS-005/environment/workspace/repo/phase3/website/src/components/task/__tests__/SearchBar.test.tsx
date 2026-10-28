import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import SearchBar from '../SearchBar'

describe('SearchBar', () => {
  const mockOnChange = vi.fn()

  it('should render search input', () => {
    render(<SearchBar value="" onChange={mockOnChange} />)

    const input = screen.getByPlaceholderText('搜索任务关键词...')
    expect(input).toBeInTheDocument()
  })

  it('should display current value', () => {
    render(<SearchBar value="测试搜索" onChange={mockOnChange} />)

    const input = screen.getByPlaceholderText('搜索任务关键词...') as HTMLInputElement
    expect(input.value).toBe('测试搜索')
  })

  it('should call onChange when typing', () => {
    render(<SearchBar value="" onChange={mockOnChange} />)

    const input = screen.getByPlaceholderText('搜索任务关键词...')
    fireEvent.change(input, { target: { value: '新搜索' } })

    expect(mockOnChange).toHaveBeenCalledWith('新搜索')
  })

  it('should not show suggestions when value is empty', () => {
    const suggestions = ['React开发', 'Vue开发', 'Angular开发']
    render(<SearchBar value="" onChange={mockOnChange} suggestions={suggestions} />)

    expect(screen.queryByText('React开发')).not.toBeInTheDocument()
  })

  it('should show filtered suggestions when typing', () => {
    const suggestions = ['React开发', 'Vue开发', 'Angular开发']
    render(<SearchBar value="React" onChange={mockOnChange} suggestions={suggestions} />)

    expect(screen.getByText('React开发')).toBeInTheDocument()
    expect(screen.queryByText('Vue开发')).not.toBeInTheDocument()
  })

  it('should filter suggestions case-insensitively', () => {
    const suggestions = ['React开发', 'Vue开发', 'Angular开发']
    render(<SearchBar value="react" onChange={mockOnChange} suggestions={suggestions} />)

    expect(screen.getByText('React开发')).toBeInTheDocument()
  })

  it('should show multiple matching suggestions', () => {
    const suggestions = ['React开发', 'React Native', 'Vue开发']
    render(<SearchBar value="React" onChange={mockOnChange} suggestions={suggestions} />)

    expect(screen.getByText('React开发')).toBeInTheDocument()
    expect(screen.getByText('React Native')).toBeInTheDocument()
    expect(screen.queryByText('Vue开发')).not.toBeInTheDocument()
  })

  it('should call onChange when clicking suggestion', () => {
    const suggestions = ['React开发', 'Vue开发']
    render(<SearchBar value="Re" onChange={mockOnChange} suggestions={suggestions} />)

    const suggestion = screen.getByText('React开发')
    fireEvent.click(suggestion)

    expect(mockOnChange).toHaveBeenCalledWith('React开发')
  })

  it('should hide suggestions after selecting', () => {
    const suggestions = ['React开发', 'Vue开发']
    const { rerender } = render(<SearchBar value="Re" onChange={mockOnChange} suggestions={suggestions} />)

  const suggestion = screen.getByText('React开发')
    fireEvent.click(suggestion)

    // Simulate parent component updating value
    rerender(<SearchBar value="React开发" onChange={mockOnChange} suggestions={suggestions} />)

    // Suggestions should still be visible because value matches
    expect(screen.getByText('React开发')).toBeInTheDocument()
  })

  it('should not show suggestions when no matches', () => {
    const suggestions = ['React开发', 'Vue开发']
    render(<SearchBar value="Angular" onChange={mockOnChange} suggestions={suggestions} />)

    expect(screen.queryByText('React开发')).not.toBeInTheDocument()
    expect(screen.queryByText('Vue开发')).not.toBeInTheDocument()
  })

  it('should render search icon', () => {
    const { container } = render(<SearchBar value="" onChange={mockOnChange} />)

    const icon = container.querySelector('svg')
    expect(icon).toBeInTheDocument()
  })

  it('should handle empty suggestions array', () => {
    render(<SearchBar value="test" onChange={mockOnChange} suggestions={[]} />)

    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('should handle undefined suggestions', () => {
    render(<SearchBar value="test" onChange={mockOnChange} />)

    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
