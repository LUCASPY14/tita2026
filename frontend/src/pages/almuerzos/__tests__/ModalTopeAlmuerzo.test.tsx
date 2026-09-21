import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ModalTopeAlmuerzo from '../ModalTopeAlmuerzo'
import type { SaldoAlmuerzoItem } from '../shared'

vi.mock('../../../services/api', () => ({
  default: { patch: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../services/api'

const SALDO: SaldoAlmuerzoItem = {
  id_saldo_almuerzo: 5,
  hijo: 1,
  hijo_nombre: 'Lucca Palau',
  hijo_grado: '1° Grado E',
  nro_tarjeta: '01024',
  saldo_actual: 470000,
  limite_credito: 0,
  deuda_maxima: null,
  fecha_actualizacion: '2026-09-17T12:00:00Z',
}

beforeEach(() => vi.clearAllMocks())

describe('ModalTopeAlmuerzo', () => {
  it('precarga el tope actual del alumno', () => {
    render(<ModalTopeAlmuerzo saldo={{ ...SALDO, limite_credito: 80000 }} onClose={vi.fn()} onSaved={vi.fn()} />)
    expect(screen.getByDisplayValue('80000')).toBeInTheDocument()
  })

  it('guarda el nuevo tope contra el saldo correspondiente', async () => {
    vi.mocked(api.patch).mockResolvedValue({ data: {} })
    const onSaved = vi.fn()
    render(<ModalTopeAlmuerzo saldo={SALDO} onClose={vi.fn()} onSaved={onSaved} />)

    const input = screen.getByPlaceholderText('0')
    await userEvent.clear(input)
    await userEvent.type(input, '100000')
    await userEvent.click(screen.getByRole('button', { name: 'Guardar' }))

    expect(api.patch).toHaveBeenCalledWith('/almuerzos/saldos/5/', { limite_credito: 100000 })
    expect(onSaved).toHaveBeenCalled()
  })

  it('sin saldo seleccionado no se muestra', () => {
    render(<ModalTopeAlmuerzo saldo={null} onClose={vi.fn()} onSaved={vi.fn()} />)
    expect(screen.queryByText('Tope de deuda de almuerzo')).not.toBeInTheDocument()
  })
})
