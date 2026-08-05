import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ModalConsumo from '../ModalConsumo'
import type { Hijo } from '../shared'

vi.mock('../../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../services/api'

const HIJO: Hijo = { id: 1, nombre: 'Juan', apellido: 'Pérez', grado: '3° A', nombre_completo: 'Juan Pérez' }

const TARJETA = { nro_tarjeta: 'T-001', hijo_nombre: 'Juan Pérez', saldo_actual: 50000, estado: 'ACTIVA' }

beforeEach(() => vi.clearAllMocks())

describe('ModalConsumo — sin selector de tipo de almuerzo', () => {
  it('no muestra ningún campo de tipo de almuerzo', () => {
    render(<ModalConsumo open hijos={[HIJO]} onClose={vi.fn()} onSaved={vi.fn()} />)
    expect(screen.queryByText(/Tipo de Almuerzo/i)).not.toBeInTheDocument()
  })

  it('registra el consumo sin enviar tipo_almuerzo en el payload', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { results: [TARJETA] } })
    vi.mocked(api.post).mockResolvedValue({ data: { id: 1 } })
    render(<ModalConsumo open hijos={[HIJO]} onClose={vi.fn()} onSaved={vi.fn()} />)

    await userEvent.type(screen.getByPlaceholderText('Nro. tarjeta'), 'T-001')
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))
    await screen.findByText('Juan Pérez')

    await userEvent.click(screen.getByRole('button', { name: 'Registrar' }))

    expect(api.post).toHaveBeenCalledWith('/almuerzos/registros-consumo/', {
      hijo: 1,
      fecha_consumo: expect.any(String),
      nro_tarjeta: 'T-001',
    })
  })
})
