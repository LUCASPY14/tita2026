import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Badge, { BADGE_COLORS } from '../Badge'

describe('Badge', () => {
  it('renderiza el texto children', () => {
    render(<Badge>Activo</Badge>)
    expect(screen.getByText('Activo')).toBeInTheDocument()
  })

  it('aplica color "default" cuando no se especifica color', () => {
    render(<Badge>Estado</Badge>)
    const el = screen.getByText('Estado')
    BADGE_COLORS.default.split(' ').forEach((cls) => {
      expect(el.className).toContain(cls)
    })
  })

  it('aplica las clases correctas para color "green"', () => {
    render(<Badge color="green">Aprobado</Badge>)
    const el = screen.getByText('Aprobado')
    BADGE_COLORS.green.split(' ').forEach((cls) => {
      expect(el.className).toContain(cls)
    })
  })

  it('aplica las clases correctas para color "red"', () => {
    render(<Badge color="red">Rechazado</Badge>)
    const el = screen.getByText('Rechazado')
    BADGE_COLORS.red.split(' ').forEach((cls) => {
      expect(el.className).toContain(cls)
    })
  })

  it('acepta className personalizado adicional', () => {
    render(<Badge className="font-bold">Texto</Badge>)
    expect(screen.getByText('Texto')).toHaveClass('font-bold')
  })

  it('renderiza como un <span> inline', () => {
    render(<Badge>X</Badge>)
    expect(screen.getByText('X').tagName).toBe('SPAN')
  })
})
