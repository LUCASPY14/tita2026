import { render, screen } from '@testing-library/react'
import { createRef } from 'react'
import Input from '../Input'

describe('Input', () => {
  it('renders an input element', () => {
    render(<Input />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('renders label when provided', () => {
    render(<Input label="Email" />)
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByText('Email')).toBeInTheDocument()
  })

  it('does not render label element when label is omitted', () => {
    const { container } = render(<Input placeholder="Sin label" />)
    expect(container.querySelector('label')).not.toBeInTheDocument()
  })

  it('label htmlFor matches input id', () => {
    const { container } = render(<Input label="Nombre" />)
    const label = container.querySelector('label')!
    const input = container.querySelector('input')!
    expect(label.htmlFor).toBe(input.id)
  })

  it('shows error message when error prop is provided', () => {
    render(<Input error="Campo requerido" />)
    expect(screen.getByText('Campo requerido')).toBeInTheDocument()
  })

  it('does not show error message when error is not provided', () => {
    render(<Input />)
    expect(screen.queryByRole('paragraph')).not.toBeInTheDocument()
  })

  it('sets aria-invalid true when error is provided', () => {
    render(<Input error="Error" />)
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'true')
  })

  it('sets aria-invalid false when no error', () => {
    render(<Input />)
    expect(screen.getByRole('textbox')).toHaveAttribute('aria-invalid', 'false')
  })

  it('sets aria-describedby to error element id when error provided', () => {
    const { container } = render(<Input error="Inválido" />)
    const input = container.querySelector('input')!
    const errorEl = screen.getByText('Inválido')
    expect(input.getAttribute('aria-describedby')).toBe(errorEl.id)
  })

  it('does not set aria-describedby when no error', () => {
    render(<Input />)
    expect(screen.getByRole('textbox')).not.toHaveAttribute('aria-describedby')
  })

  it('applies red border classes when error is provided', () => {
    render(<Input error="Error" />)
    expect(screen.getByRole('textbox').className).toContain('border-red-300')
  })

  it('forwards ref to the underlying input', () => {
    const ref = createRef<HTMLInputElement>()
    render(<Input ref={ref} />)
    expect(ref.current).toBeInstanceOf(HTMLInputElement)
  })

  it('passes extra props to the input element', () => {
    render(<Input placeholder="Escribí aquí" maxLength={50} />)
    const input = screen.getByRole('textbox')
    expect(input).toHaveAttribute('placeholder', 'Escribí aquí')
    expect(input).toHaveAttribute('maxlength', '50')
  })
})
