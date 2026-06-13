import { render, screen, fireEvent } from '@testing-library/react'
import Button from '../Button'

describe('Button', () => {
  it('renders children text', () => {
    render(<Button>Guardar</Button>)
    expect(screen.getByRole('button', { name: /guardar/i })).toBeInTheDocument()
  })

  it('shows spinner when loading', () => {
    render(<Button loading>Guardar</Button>)
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('is disabled when loading prop is true', () => {
    render(<Button loading>Guardar</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Guardar</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('calls onClick when clicked', () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Click</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('shows icon when not loading', () => {
    const icon = <span data-testid="btn-icon">★</span>
    render(<Button icon={icon}>Guardar</Button>)
    expect(screen.getByTestId('btn-icon')).toBeInTheDocument()
  })

  it('hides icon when loading', () => {
    const icon = <span data-testid="btn-icon">★</span>
    render(<Button loading icon={icon}>Guardar</Button>)
    expect(screen.queryByTestId('btn-icon')).not.toBeInTheDocument()
  })

  it('applies w-full when block is true', () => {
    render(<Button block>Block</Button>)
    expect(screen.getByRole('button').className).toContain('w-full')
  })

  it('does not apply w-full when block is false', () => {
    render(<Button>Inline</Button>)
    expect(screen.getByRole('button').className).not.toContain('w-full')
  })

  it('applies primary variant classes', () => {
    render(<Button variant="primary">Primary</Button>)
    expect(screen.getByRole('button').className).toContain('bg-green-600')
  })

  it('applies danger variant classes', () => {
    render(<Button variant="danger">Danger</Button>)
    expect(screen.getByRole('button').className).toContain('bg-red-600')
  })

  it('applies sm size classes', () => {
    render(<Button size="sm">Small</Button>)
    expect(screen.getByRole('button').className).toContain('text-sm')
  })

  it('renders without children', () => {
    render(<Button aria-label="icon-only" />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })
})
