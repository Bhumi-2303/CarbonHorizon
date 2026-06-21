import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Button } from './Button'

describe('Button component', () => {
  it('renders children correctly', () => {
    render(<Button variant="primary">Click Me</Button>)
    expect(screen.getByText('Click Me')).toBeInTheDocument()
  })

  it('applies the correct class based on variant', () => {
    render(<Button variant="danger">Delete</Button>)
    const btn = screen.getByText('Delete')
    expect(btn.className).toContain('bg-danger')
  })
})
