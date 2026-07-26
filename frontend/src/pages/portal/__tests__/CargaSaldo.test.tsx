import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import CargaSaldo from '../CargaSaldo'

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useSearchParams: vi.fn(() => [new URLSearchParams(), vi.fn()]),
  }
})

vi.mock('../../../store/authStore', () => ({
  useAuthStore: () => ({ user: { nombre: 'María López' } }),
}))

vi.mock('../../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import { useSearchParams } from 'react-router-dom'
import api from '../../../services/api'
import toast from 'react-hot-toast'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const HIJO = {
  id: 1, nombre: 'Juan', grado: '3° A',
  tarjeta: { nro_tarjeta: 'T-001', saldo_actual: 50_000, estado: 'ACTIVA' },
}

const HIJO2 = {
  id: 2, nombre: 'Lucía', grado: '5° B',
  tarjeta: { nro_tarjeta: 'T-002', saldo_actual: 20_000, estado: 'ACTIVA' },
}

const HIJO_SIN_TARJETA = {
  id: 3, nombre: 'Pedro', grado: '1° C',
  tarjeta: null,
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function setupHijos(...hijos: typeof HIJO[]) {
  vi.mocked(api.get).mockResolvedValue({ data: { hijos } })
}

function setParams(params: string) {
  const mockSet = vi.fn()
  vi.mocked(useSearchParams).mockReturnValue([
    new URLSearchParams(params),
    mockSet as unknown as ReturnType<typeof useSearchParams>[1],
  ])
  return mockSet
}

beforeEach(() => {
  vi.clearAllMocks()
  // Default: no URL params (form view)
  vi.mocked(useSearchParams).mockReturnValue([new URLSearchParams(), vi.fn()])
  // Default: stub window.location
  vi.stubGlobal('location', { href: '' })
})

// ── Carga inicial ─────────────────────────────────────────────────────────────

describe('CargaSaldo — carga inicial', () => {
  it('muestra Spinner mientras la API no responde', () => {
    vi.mocked(api.get).mockReturnValue(new Promise(() => {})) // never resolves
    render(<CargaSaldo />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('muestra nombre, grado y saldo de hijos con tarjeta', async () => {
    setupHijos(HIJO, HIJO2)
    render(<CargaSaldo />)
    await screen.findByText('Juan')
    expect(screen.getByText('Lucía')).toBeInTheDocument()
  })

  it('hijos sin tarjeta son filtrados → muestra empty state', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { hijos: [HIJO_SIN_TARJETA] } })
    render(<CargaSaldo />)
    await screen.findByText(/Sin tarjetas asignadas/i)
  })

  it('hijo único se auto-selecciona y muestra su saldo', async () => {
    setupHijos(HIJO)
    render(<CargaSaldo />)
    // With a single child, the selection section shows that child selected
    // and saldo is visible in some form (balance display or card)
    await screen.findByText('Juan')
    // The saldo should be visible
    await waitFor(() => {
      expect(screen.getByText(/50\.000/)).toBeInTheDocument()
    })
  })

  it('muestra saludo con el nombre del usuario en el pie', async () => {
    setupHijos(HIJO)
    render(<CargaSaldo />)
    await screen.findByText(/Hola.*María López/i)
  })
})

// ── Estados de retorno Bancard ────────────────────────────────────────────────

describe('CargaSaldo — resultado de pago', () => {
  it('estado=aprobado → "¡Pago aprobado!"', async () => {
    setParams('estado=aprobado&monto=100000')
    vi.mocked(api.get).mockResolvedValue({ data: { hijos: [] } })
    render(<CargaSaldo />)
    await screen.findByText(/Pago aprobado/i)
  })

  it('estado=cancelado → "Pago cancelado"', async () => {
    setParams('estado=cancelado')
    vi.mocked(api.get).mockResolvedValue({ data: { hijos: [] } })
    render(<CargaSaldo />)
    await screen.findByText(/Pago cancelado/i)
  })

  it('estado=rechazado → mensaje de rechazo', async () => {
    setParams('estado=rechazado')
    vi.mocked(api.get).mockResolvedValue({ data: { hijos: [] } })
    render(<CargaSaldo />)
    await screen.findByText(/rechazado/i)
  })

  it('click "Realizar otra carga" llama setSearchParams({}) y recarga hijos', async () => {
    const mockSet = setParams('estado=aprobado&monto=50000')
    vi.mocked(api.get).mockResolvedValue({ data: { hijos: [HIJO] } })
    render(<CargaSaldo />)
    await screen.findByText(/Pago aprobado/i)

    await userEvent.click(screen.getByRole('button', { name: /Realizar otra carga/i }))

    expect(mockSet).toHaveBeenCalledWith({})
    // cargarHijos() fires once (mount skips it when estadoRetorno is set)
    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith('/usuarios/portal/mi-hijo/')
    })
  })
})

// ── Formulario de pago ────────────────────────────────────────────────────────

describe('CargaSaldo — formulario', () => {
  it('seleccionar monto rápido habilita el botón "Ir a pagar"', async () => {
    setupHijos(HIJO)
    render(<CargaSaldo />)
    await screen.findByText('Juan')

    // botón deshabilitado al inicio
    const pagarBtn = screen.getByRole('button', { name: /Ir a pagar/i })
    expect(pagarBtn).toBeDisabled()

    // click en el monto rápido 50k
    await userEvent.click(screen.getByRole('button', { name: '50k' }))

    // Con hijo único auto-seleccionado y monto válido, el botón debería habilitarse
    await waitFor(() => {
      expect(pagarBtn).not.toBeDisabled()
    })
  })

  it('monto personalizado inválido (< 10.000) mantiene el botón deshabilitado', async () => {
    setupHijos(HIJO)
    render(<CargaSaldo />)
    await screen.findByText('Juan')

    await userEvent.click(screen.getByRole('button', { name: /Otro monto/i }))
    const montoInput = await screen.findByPlaceholderText('150000')
    await userEvent.clear(montoInput)
    await userEvent.type(montoInput, '5000')

    expect(screen.getByRole('button', { name: /Ir a pagar/i })).toBeDisabled()
  })

  it('click "Ir a pagar" → api.post y redirige a redirect_url', async () => {
    setupHijos(HIJO)
    vi.mocked(api.post).mockResolvedValue({ data: { redirect_url: 'https://vpos.infonet.com.py/pay/xyz' } })
    render(<CargaSaldo />)
    await screen.findByText('Juan')

    await userEvent.click(screen.getByRole('button', { name: '50k' }))
    await waitFor(() => expect(screen.getByRole('button', { name: /Ir a pagar/i })).not.toBeDisabled())

    await userEvent.click(screen.getByRole('button', { name: /Ir a pagar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/core/bancard/iniciar/',
        expect.objectContaining({ nro_tarjeta: 'T-001', monto: 50_000 }),
      )
    })
    expect(window.location.href).toBe('https://vpos.infonet.com.py/pay/xyz')
  })

  it('api.post falla → toast.error con mensaje del servidor', async () => {
    setupHijos(HIJO)
    vi.mocked(api.post).mockRejectedValue({
      response: { data: { detail: 'Tarjeta no habilitada para Bancard' } },
    })
    render(<CargaSaldo />)
    await screen.findByText('Juan')

    await userEvent.click(screen.getByRole('button', { name: '50k' }))
    await waitFor(() => expect(screen.getByRole('button', { name: /Ir a pagar/i })).not.toBeDisabled())
    await userEvent.click(screen.getByRole('button', { name: /Ir a pagar/i }))

    await waitFor(() => {
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Tarjeta no habilitada para Bancard')
    })
  })
})
