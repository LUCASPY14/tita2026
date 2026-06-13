import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import Select from '../Select'

const OPTIONS = [
  { value: 1, label: 'Efectivo' },
  { value: 2, label: 'Tarjeta' },
  { value: 3, label: 'Transferencia' },
]

describe('Select', () => {
  it('renderiza todas las opciones', () => {
    render(<Select options={OPTIONS} />)
    expect(screen.getByRole('combobox')).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Efectivo' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Tarjeta' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Transferencia' })).toBeInTheDocument()
  })

  it('muestra opción placeholder cuando se provee', () => {
    render(<Select options={OPTIONS} placeholder="Seleccioná un método" />)
    expect(screen.getByRole('option', { name: 'Seleccioná un método' })).toBeInTheDocument()
  })

  it('la opción placeholder está deshabilitada', () => {
    render(<Select options={OPTIONS} placeholder="Seleccioná" />)
    const placeholder = screen.getByRole('option', { name: 'Seleccioná' }) as HTMLOptionElement
    expect(placeholder.disabled).toBe(true)
  })

  it('llama a onChange cuando se selecciona una opción', async () => {
    const onChange = vi.fn()
    render(<Select options={OPTIONS} onChange={onChange} />)
    await userEvent.selectOptions(screen.getByRole('combobox'), 'Tarjeta')
    expect(onChange).toHaveBeenCalledTimes(1)
  })

  it('queda deshabilitado con prop disabled', () => {
    render(<Select options={OPTIONS} disabled />)
    expect(screen.getByRole('combobox')).toBeDisabled()
  })

  it('acepta className personalizado', () => {
    render(<Select options={OPTIONS} className="mi-clase" />)
    expect(screen.getByRole('combobox')).toHaveClass('mi-clase')
  })
})
