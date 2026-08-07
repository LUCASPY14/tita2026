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

const HIJO_JUAN: Record<string, unknown> = { id: 1, nombre: 'Juan García', saldo_almuerzo: -150_000 }
const HIJO_LUCIA: Record<string, unknown> = { id: 2, nombre: 'Lucía García', saldo_almuerzo: 20_000 }

const TARJETA_GUARDADA = {
  card_id: 1, card_masked_number: '5418********0014', card_brand: 'MasterCard', expiration_date: '08/26',
}

function setupNoRetorno(hijos: unknown[] = [HIJO_JUAN], tarjetas: (typeof TARJETA_GUARDADA)[] = []) {
  mockGetSearchParam.mockImplementation((key: string) => {
    const map: Record<string, null> = { estado: null, monto: null, hijo_id: null }
    return map[key] ?? null
  })
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/core/bancard/tarjetas/') return Promise.resolve({ data: { tarjetas } })
    return Promise.resolve({ data: { hijos } })
  })
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
  it('estado=aprobado → muestra "¡Recarga aprobada!" y no llama la API', () => {
    setupRetorno('aprobado')
    render(<PagarAlmuerzo />)

    expect(screen.getByText('¡Recarga aprobada!')).toBeInTheDocument()
    expect(vi.mocked(api.get)).not.toHaveBeenCalled()
  })

  it('estado=cancelado → muestra "Recarga cancelada"', () => {
    setupRetorno('cancelado')
    render(<PagarAlmuerzo />)

    expect(screen.getByText('Recarga cancelada')).toBeInTheDocument()
  })

  it('estado=rechazado → muestra "Recarga rechazada"', () => {
    setupRetorno('rechazado')
    render(<PagarAlmuerzo />)

    expect(screen.getByText('Recarga rechazada')).toBeInTheDocument()
  })

  it('"Ver saldo" llama setSearchParams({})', async () => {
    setupRetorno('aprobado')
    vi.mocked(api.get).mockResolvedValue({ data: { hijos: [HIJO_JUAN] } })
    render(<PagarAlmuerzo />)

    await userEvent.click(screen.getByRole('button', { name: /Ver saldo/i }))

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

  it('sin hijos → mensaje "Sin hijos asociados"', async () => {
    setupNoRetorno([])
    render(<PagarAlmuerzo />)

    await screen.findByText('Sin hijos asociados')
    expect(vi.mocked(api.get)).toHaveBeenCalledWith('/usuarios/portal/mi-hijo/')
  })

  it('API falla → toast.error', async () => {
    mockGetSearchParam.mockReturnValue(null)
    vi.mocked(api.get).mockRejectedValue(new Error('500'))
    render(<PagarAlmuerzo />)

    await waitFor(() =>
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Error al cargar el saldo de almuerzo')
    )
  })
})

// ── Auto-selección ────────────────────────────────────────────────────────────

describe('PagarAlmuerzo — auto-selección', () => {
  it('un solo hijo → se auto-selecciona y muestra su saldo', async () => {
    setupNoRetorno([HIJO_JUAN])
    render(<PagarAlmuerzo />)

    await screen.findByText('Juan García')
    expect(screen.getByText('Gs. -150.000')).toBeInTheDocument()
  })

  it('múltiples hijos → muestra selector con ambos', async () => {
    setupNoRetorno([HIJO_JUAN, HIJO_LUCIA])
    render(<PagarAlmuerzo />)

    await screen.findByText('Juan García')
    expect(screen.getByText('Lucía García')).toBeInTheDocument()
  })

  it('seleccionar a Lucía y un monto activa el resumen', async () => {
    setupNoRetorno([HIJO_JUAN, HIJO_LUCIA])
    render(<PagarAlmuerzo />)
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('button', { name: /Lucía García/i }))
    await userEvent.click(screen.getByRole('button', { name: 'Gs. 25.000' }))

    await screen.findByText('Resumen')
  })

  it('?hijo_id= preselecciona al hijo indicado', async () => {
    mockGetSearchParam.mockImplementation((key: string) => {
      if (key === 'hijo_id') return '2'
      return null
    })
    vi.mocked(api.get).mockResolvedValue({ data: { hijos: [HIJO_JUAN, HIJO_LUCIA] } })
    render(<PagarAlmuerzo />)

    await screen.findByText('Juan García')
    // Lucía queda resaltada como seleccionada — el botón de monto rápido ya está disponible
    expect(screen.getByRole('button', { name: 'Gs. 25.000' })).toBeInTheDocument()
  })
})

// ── Botón "Ir a pagar" ────────────────────────────────────────────────────────

describe('PagarAlmuerzo — botón "Ir a pagar"', () => {
  it('botón deshabilitado sin monto seleccionado', async () => {
    setupNoRetorno([HIJO_JUAN])
    render(<PagarAlmuerzo />)
    await screen.findByText('Juan García')

    expect(screen.getByRole('button', { name: /Ir a pagar/i })).toBeDisabled()
  })

  it('botón habilitado con monto rápido y llama api.post con hijo_id al hacer clic', async () => {
    setupNoRetorno([HIJO_JUAN])
    vi.mocked(api.post).mockResolvedValue({ data: { redirect_url: 'https://bancard.com/pay' } })
    delete (window as { location?: unknown }).location
    ;(window as { location: { href: string } }).location = { href: '' }

    render(<PagarAlmuerzo />)
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('button', { name: 'Gs. 50.000' }))
    await userEvent.click(screen.getByRole('button', { name: /Ir a pagar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/core/bancard/iniciar-almuerzo/',
        expect.objectContaining({ hijo_id: 1, monto: 50_000 }),
      )
    })
  })

  it('API post falla → toast.error', async () => {
    setupNoRetorno([HIJO_JUAN])
    vi.mocked(api.post).mockRejectedValue({
      response: { data: { detail: 'Bancard error' } },
    })
    render(<PagarAlmuerzo />)
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('button', { name: 'Gs. 50.000' }))
    await userEvent.click(screen.getByRole('button', { name: /Ir a pagar/i }))

    await waitFor(() =>
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Bancard error')
    )
  })
})

// ── Método de pago: tarjeta guardada ──────────────────────────────────────────

describe('PagarAlmuerzo — tarjeta guardada', () => {
  it('pestaña "Tarjeta guardada" muestra las tarjetas guardadas del cliente', async () => {
    setupNoRetorno([HIJO_JUAN], [TARJETA_GUARDADA])
    render(<PagarAlmuerzo />)
    await screen.findByText('Juan García')
    await userEvent.click(screen.getByRole('button', { name: 'Gs. 50.000' }))

    await userEvent.click(screen.getByRole('button', { name: /Tarjeta guardada/i }))

    await screen.findByText(/5418\*+0014/)
  })

  it('pagar con tarjeta guardada (aprobado síncrono) redirige con estado=aprobado', async () => {
    setupNoRetorno([HIJO_JUAN], [TARJETA_GUARDADA])
    vi.mocked(api.post).mockResolvedValue({ data: { estado: 'aprobado', monto: 50_000 } })
    render(<PagarAlmuerzo />)
    await screen.findByText('Juan García')
    await userEvent.click(screen.getByRole('button', { name: 'Gs. 50.000' }))
    await userEvent.click(screen.getByRole('button', { name: /Tarjeta guardada/i }))
    await screen.findByText(/5418\*+0014/)

    await userEvent.click(screen.getByText(/5418\*+0014/))
    await waitFor(() => expect(screen.getByRole('button', { name: /Ir a pagar/i })).not.toBeDisabled())
    await userEvent.click(screen.getByRole('button', { name: /Ir a pagar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/core/bancard/pagar-almuerzo-con-tarjeta/',
        expect.objectContaining({ hijo_id: 1, monto: 50_000, card_id: 1 }),
      )
    })
    expect(window.location.href).toContain('estado=aprobado')
  })

  it('botón "Ir a pagar" queda deshabilitado sin tarjeta seleccionada', async () => {
    setupNoRetorno([HIJO_JUAN], [TARJETA_GUARDADA])
    render(<PagarAlmuerzo />)
    await screen.findByText('Juan García')
    await userEvent.click(screen.getByRole('button', { name: 'Gs. 50.000' }))
    await userEvent.click(screen.getByRole('button', { name: /Tarjeta guardada/i }))
    await screen.findByText(/5418\*+0014/)

    expect(screen.getByRole('button', { name: /Ir a pagar/i })).toBeDisabled()
  })
})
