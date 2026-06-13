import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Card from '../Card'

describe('Card', () => {
  it('renderiza el children', () => {
    render(<Card>Contenido de prueba</Card>)
    expect(screen.getByText('Contenido de prueba')).toBeInTheDocument()
  })

  it('no muestra header cuando no se pasa title', () => {
    const { container } = render(<Card>hijo</Card>)
    // El header tiene border-b; sin title no debe existir ese div
    expect(container.querySelector('.border-b')).not.toBeInTheDocument()
  })

  it('muestra el title cuando se lo provee', () => {
    render(<Card title="Ventas del día">hijo</Card>)
    expect(screen.getByText('Ventas del día')).toBeInTheDocument()
  })

  it('el title aparece en un bloque separado del children', () => {
    const { container } = render(<Card title="Encabezado">Cuerpo</Card>)
    const header = container.querySelector('.border-b') as HTMLElement
    expect(header).toBeInTheDocument()
    expect(header.textContent).toBe('Encabezado')
    expect(header.textContent).not.toContain('Cuerpo')
  })

  it('acepta className personalizado', () => {
    const { container } = render(<Card className="mi-clase">hijo</Card>)
    expect(container.firstChild).toHaveClass('mi-clase')
  })
})
