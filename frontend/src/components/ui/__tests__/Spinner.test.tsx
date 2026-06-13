import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Spinner from '../Spinner'

describe('Spinner', () => {
  it('tiene role="status" para accesibilidad', () => {
    render(<Spinner />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('muestra texto accesible "Cargando..." para lectores de pantalla', () => {
    render(<Spinner />)
    expect(screen.getByText('Cargando...')).toBeInTheDocument()
  })

  it('acepta y aplica un className personalizado al contenedor', () => {
    render(<Spinner className="h-32 w-32" />)
    expect(screen.getByRole('status')).toHaveClass('h-32', 'w-32')
  })
})
