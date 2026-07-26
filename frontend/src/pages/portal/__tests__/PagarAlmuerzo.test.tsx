import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'

// useSearchParams needs to be mockeable per-test
const mockGetSearchParam = vi.fn()
const mockSetSearchParams = vi.fn()

vi.mock('react-router-dom', () => ({
  useSearchParams: () => [
    { get: mockGetSearchParam },
    mockSetSearchParams,
  ],
}))

vi.mock('../../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../services/api'
import toast from 'react-hot-toast'
import PagarAlmuerzo from '../PagarAlmuerzo'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const CUENTA_JUAN: Record<string, unknown> = {
  id: 10, hijo_nombre: 'Juan García', mes: 7, anio: 2026,
  cantidad_almuerzos: 20, monto_total: 200_000,
  monto_pagado: 50_000, saldo_pendiente: 150_000, estado: 'PARCIAL',
}

const CUENTA_LUCIA: Record<string, unknown> = {
  id: 11, hijo_nombre: 'Lucía García', mes: 7, anio: 2026,
  cantidad_almuerzos: 18, monto_total: 180_000,
  monto_pagado: 0, saldo_pendiente: 180_000, estado: 'PENDIENTE',
}

function setupNoRetorno(cuentas: unknown[] = [CUENTA_JUAN]) {
  mockGetSearchParam.mockImplementation((key: string) => {
    const map: Record<string, null> = { estado: null, monto: null, cuenta_id: null }
    return map[key] ?? null
  })
  vi.mocked(api.get).mockResolvedValue({ data: { results: cuentas } })
}

function setupRetorno(estado: string, monto = '150000') {
  mockGetSearchParam.mockImplementation((key: string) => {
    if (key === 'estado') return estado
    if (key === 'monto') return monto
    return null
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

// ── Estado de retorno Bancard ─────────────────────────────────────────────────

describe('PagarAlmuerzo — resultado Bancard', () => {
  it('estado=aprobado → muestra "¡Pago aprobado!" y no llama la API', () => {
    setupRetorno('aprobado')
    render(<PagarAlmuerzo />)

    expect(screen.getByText('¡Pago aprobado!')).toBeInTheDocument()
    expect(vi.mocked(api.get)).not.toHaveBeenCalled()
  })

  it('estado=cancelado → muestra "Pago cancelado"', () => {
    setupRetorno('cancelado')
    render(<PagarAlmuerzo />)

    expect(screen.getByText('Pago cancelado')).toBeInTheDocument()
  })

  it('estado=rechazado → muestra "Pago rechazado"', () => {
    setupRetorno('rechazado')
    render(<PagarAlmuerzo />)

    expect(screen.getByText('Pago rechazado')).toBeInTheDocument()
  })

  it('"Ver cuentas pendientes" llama setSearchParams({})', async () => {
    setupRetorno('aprobado')
    vi.mocked(api.get).mockResolvedValue({ data: { results: [CUENTA_JUAN] } })
    render(<PagarAlmuerzo />)

    await userEvent.click(screen.getByRole('button', { name: /Ver cuentas pendientes/i }))

    expect(mockSetSearchParams).toHaveBeenCalledWith({})
  })
})

// ── Carga normal ──────────────────────────────────────────────────────────────

describe('PagarAlmuerzo — carga', () => {
  it('muestra spinner mientras carga', () => {
    mockGetSearchParam.mockReturnValue(null)
    vi.mocked(api.get).mockReturnValue(new Promise(() => {}))
    render(<PagarAlmuerzo />)

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('sin cuentas pendientes → mensaje "Sin cuentas pendientes"', async () => {
    setupNoRetorno([])
    render(<PagarAlmuerzo />)

    await screen.findByText('Sin cuentas pendientes')
    expect(vi.mocked(api.get)).toHaveBeenCalledWith(
      '/almuerzos/cuentas-mensuales/',
      expect.objectContaining({ params: expect.objectContaining({ estado: 'PENDIENTE,PARCIAL' }) }),
    )
  })

  it('cuenta con saldo_pendiente=0 queda excluida', async () => {
    const sinDeuda = { ...CUENTA_JUAN, saldo_pendiente: 0 }
    setupNoRetorno([sinDeuda])
    render(<PagarAlmuerzo />)

    await screen.findByText('Sin cuentas pendientes')
  })

  it('API falla → toast.error', async () => {
    mockGetSearchParam.mockReturnValue(null)
    vi.mocked(api.get).mockRejectedValue(new Error('500'))
    render(<PagarAlmuerzo />)

    await waitFor(() =>
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Error al cargar las cuentas de almuerzo')
    )
  })
})

// ── Auto-selección ────────────────────────────────────────────────────────────

describe('PagarAlmuerzo — auto-selección', () => {
  it('una sola cuenta → se auto-selecciona y muestra "Saldo pendiente"', async () => {
    setupNoRetorno([CUENTA_JUAN])
    render(<PagarAlmuerzo />)

    // El texto "Saldo pendiente" solo aparece en la tarjeta de cuenta única auto-seleccionada
    await screen.findByText('Saldo pendiente')
  })

  it('múltiples cuentas → muestra selector con ambos hijos', async () => {
    setupNoRetorno([CUENTA_JUAN, CUENTA_LUCIA])
    render(<PagarAlmuerzo />)

    await screen.findByText('Juan García')
    expect(screen.getByText('Lucía García')).toBeInTheDocument()
  })

  it('seleccionar cuenta de Lucía activa el resumen de pago', async () => {
    setupNoRetorno([CUENTA_JUAN, CUENTA_LUCIA])
    render(<PagarAlmuerzo />)
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('button', { name: /Lucía García/i }))

    // La sección "Resumen" solo aparece cuando hay cuenta seleccionada + monto válido
    await screen.findByText('Resumen')
  })
})

// ── Botón "Ir a pagar" ────────────────────────────────────────────────────────

describe('PagarAlmuerzo — botón "Ir a pagar"', () => {
  it('botón deshabilitado si el monto es 0', async () => {
    setupNoRetorno([CUENTA_JUAN])
    render(<PagarAlmuerzo />)
    // "Saldo pendiente" es único a la tarjeta de cuenta única auto-seleccionada
    await screen.findByText('Saldo pendiente')

    // Vaciar el monto (input type="text" con placeholder="0")
    const input = screen.getByPlaceholderText('0')
    await userEvent.clear(input)

    expect(screen.getByRole('button', { name: /Ir a pagar/i })).toBeDisabled()
  })

  it('botón habilitado con monto válido y llama api.post al hacer clic', async () => {
    setupNoRetorno([CUENTA_JUAN])
    vi.mocked(api.post).mockResolvedValue({ data: { redirect_url: 'https://bancard.com/pay' } })
    delete (window as { location?: unknown }).location
    ;(window as { location: { href: string } }).location = { href: '' }

    render(<PagarAlmuerzo />)
    await screen.findByText('Saldo pendiente')

    // La cuenta se auto-seleccionó y el monto fue prellenado con saldo_pendiente
    await userEvent.click(screen.getByRole('button', { name: /Ir a pagar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/core/bancard/iniciar-almuerzo/',
        expect.objectContaining({ cuenta_id: 10, monto: 150_000 }),
      )
    })
  })

  it('API post falla → toast.error', async () => {
    setupNoRetorno([CUENTA_JUAN])
    vi.mocked(api.post).mockRejectedValue({
      response: { data: { detail: 'Bancard error' } },
    })
    render(<PagarAlmuerzo />)
    await screen.findByText('Saldo pendiente')

    await userEvent.click(screen.getByRole('button', { name: /Ir a pagar/i }))

    await waitFor(() =>
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Bancard error')
    )
  })
})
