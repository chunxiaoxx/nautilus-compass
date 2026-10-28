import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Card from '../Card'

describe('Card', () => {
  it('should render with children', () => {
    render(
      <Card>
        <div>Card Content</div>
      </Card>
    )

    expect(screen.getByText('Card Content')).toBeInTheDocument()
  })

  it('should apply default styles', () => {
    const { container } = render(
      <Card>
        <div>Content</div>
      </Card>
    )

    const card = container.firstChild
    expect(card).toHaveClass('glass')
    expect(card).toHaveClass('rounded-xl')
    expect(card).toHaveClass('p-6')
  })

  it('should apply custom className', () => {
    const { container } = render(
   <Card className="custom-card">
        <div>Content</div>
      </Card>
    )

    const card = container.firstChild
    expect(card).toHaveClass('custom-card')
    expect(card).toHaveClass('glass') // Should still have base classes
  })

  it('should apply hover styles when hover prop is true', () => {
    const { container } = render(
      <Card hover>
        <div>Content</div>
      </Card>
    )

    const card = container.firstChild
    expect(card).toHaveClass('hover:scale-105')
    expect(card).toHaveClass('transition-transform')
  })

  it('should not apply hover styles by default', () => {
    const { container } = render(
      <Card>
        <div>Content</div>
      </Card>
    )

    const card = container.firstChild
    expect(card).not.toHaveClass('hover:scale-105')
  })

  it('should render multiple children', () => {
    render(
      <Card>
     <h2>Title</h2>
        <p>Description</p>
        <button>Action</button>
      </Card>
    )

    expect(screen.getByText('Title')).toBeInTheDocument()
    expect(screen.getByText('Description')).toBeInTheDocument()
    expect(screen.getByText('Action')).toBeInTheDocument()
  })

  it('should render with complex nested content', () => {
    render(
    <Card>
        <div className="header">
          <h3>Card Header</h3>
        </div>
        <div className="body">
          <p>Card Body</p>
        </div>
      <div className="footer">
          <span>Card Footer</span>
      </div>
      </Card>
    )

    expect(screen.getByText('Card Header')).toBeInTheDocument()
    expect(screen.getByText('Card Body')).toBeInTheDocument()
    expect(screen.getByText('Card Footer')).toBeInTheDocument()
  })
})
