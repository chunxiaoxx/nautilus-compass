import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Button from '../Button'

describe('Button', () => {
  it('should render with children', () => {
    render(<Button>Click me</Button>)

    expect(screen.getByText('Click me')).toBeInTheDocument()
  })

  it('should handle click events', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click me</Button>)

    const button = screen.getByText('Click me')
    fireEvent.click(button)

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('should apply primary variant styles by default', () => {
    render(<Button>Primary Button</Button>)

    const button = screen.getByText('Primary Button')
    expect(button).toHaveClass('gradient-primary')
    expect(button).toHaveClass('text-white')
  })

  it('should apply secondary variant styles', () => {
    render(<Button variant="secondary">Secondary Button</Button>)

    const button = screen.getByText('Secondary Button')
    expect(button).toHaveClass('bg-dark-800')
    expect(button).toHaveClass('text-white')
  })

  it('should apply outline variant styles', () => {
    render(<Button variant="outline">Outline Button</Button>)

    const button = screen.getByText('Outline Button')
    expect(button).toHaveClass('border-2')
    expect(button).toHaveClass('border-primary-500')
  })

  it('should apply small size styles', () => {
    render(<Button size="sm">Small Button</Button>)

    const button = screen.getByText('Small Button')
    expect(button).toHaveClass('px-4')
    expect(button).toHaveClass('py-2')
    expect(button).toHaveClass('text-sm')
  })

  it('should apply medium size styles by default', () => {
    render(<Button>Medium Button</Button>)

    const button = screen.getByText('Medium Button')
    expect(button).toHaveClass('px-6')
    expect(button).toHaveClass('py-3')
    expect(button).toHaveClass('text-base')
  })

  it('should apply large size styles', () => {
    render(<Button size="lg">Large Button</Button>)

    const button = screen.getByText('Large Button')
    expect(button).toHaveClass('px-8')
    expect(button).toHaveClass('py-4')
    expect(button).toHaveClass('text-lg')
  })

  it('should be disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled Button</Button>)

    const button = screen.getByText('Disabled Button')
    expect(button).toBeDisabled()
  })

  it('should not trigger click when disabled', () => {
    const handleClick = vi.fn()
    render(<Button disabled onClick={handleClick}>Disabled Button</Button>)

    const button = screen.getByText('Disabled Button')
    fireEvent.click(button)

    expect(handleClick).not.toHaveBeenCalled()
  })

  it('should apply custom className', () => {
    render(<Button className="custom-class">Custom Button</Button>)

    const button = screen.getByText('Custom Button')
    expect(button).toHaveClass('custom-class')
  })

  it('should pass through additional props', () => {
    render(<Button type="submit" data-testid="submit-btn">Submit</Button>)

    const button = screen.getByTestId('submit-btn')
    expect(button).toHaveAttribute('type', 'submit')
  })
})
