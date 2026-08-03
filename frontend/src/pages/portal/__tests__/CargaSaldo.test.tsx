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

const TARJETA_GUARDADA = {
  card_id: 1, card_masked_number: '5418********0014', card_brand: 'MasterCard', expiration_date: '08/26',
}

function setupHijosYTarjetas(hijos: typeof HIJO[], tarjetas: (typeof TARJETA_GUARDADA)[] = []) {
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/core/bancard/tarjetas/') return Promise.resolve({ data: { tarjetas } })
    return Promise.resolve({ data: { hijos } })
  })
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
    // The saldo should be visible next to the "Saldo actual" label
    await waitFor(() => {
      expect(screen.getByText('Saldo actual').nextElementSibling).toHaveTextContent('50.000')
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
    await userEvent.click(screen.getByRole('button', { name: 'Gs. 50.000' }))

    // Con hijo único auto-seleccionado y monto válido, el botón debería habilitarse
    await waitFor(() => {
      expect(pagarBtn).not.toBeDisabled()
    })
  })

  it('monto personalizado inválido (< 5.000) mantiene el botón deshabilitado', async () => {
    setupHijos(HIJO)
    render(<CargaSaldo />)
    await screen.findByText('Juan')

    await userEvent.click(screen.getByRole('button', { name: /Otro monto/i }))
    const montoInput = await screen.findByPlaceholderText('150000')
    await userEvent.clear(montoInput)
    await userEvent.type(montoInput, '4000')

    expect(screen.getByRole('button', { name: /Ir a pagar/i })).toBeDisabled()
  })

  it('click "Ir a pagar" → api.post y muestra el checkout embebido de Bancard', async () => {
    setupHijos(HIJO)
    vi.mocked(api.post).mockResolvedValue({
      data: { process_id: 'proc-single-buy-1', script_url: 'https://vpos.test/checkout.js' },
    })
    render(<CargaSaldo />)
    await screen.findByText('Juan')

    await userEvent.click(screen.getByRole('button', { name: 'Gs. 50.000' }))
    await waitFor(() => expect(screen.getByRole('button', { name: /Ir a pagar/i })).not.toBeDisabled())

    await userEvent.click(screen.getByRole('button', { name: /Ir a pagar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/core/bancard/iniciar/',
        expect.objectContaining({ nro_tarjeta: 'T-001', monto: 50_000 }),
      )
    })
    await screen.findByText(/Ingresá los datos de tu tarjeta/i)
    expect(document.getElementById('bancard-checkout-container')).toBeTruthy()
  })

  it('api.post falla → toast.error con mensaje del servidor', async () => {
    setupHijos(HIJO)
    vi.mocked(api.post).mockRejectedValue({
      response: { data: { detail: 'Tarjeta no habilitada para Bancard' } },
    })
    render(<CargaSaldo />)
    await screen.findByText('Juan')

    await userEvent.click(screen.getByRole('button', { name: 'Gs. 50.000' }))
    await waitFor(() => expect(screen.getByRole('button', { name: /Ir a pagar/i })).not.toBeDisabled())
    await userEvent.click(screen.getByRole('button', { name: /Ir a pagar/i }))

    await waitFor(() => {
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Tarjeta no habilitada para Bancard')
    })
  })
})

// ── Método de pago: tarjeta guardada ──────────────────────────────────────────

describe('CargaSaldo — tarjeta guardada', () => {
  it('pestaña "Tarjeta guardada" muestra las tarjetas guardadas del cliente', async () => {
    setupHijosYTarjetas([HIJO], [TARJETA_GUARDADA])
    render(<CargaSaldo />)
    await screen.findByText('Juan')
    await userEvent.click(screen.getByRole('button', { name: 'Gs. 50.000' }))

    await userEvent.click(screen.getByRole('button', { name: /Tarjeta guardada/i }))

    await screen.findByText(/5418\*+0014/)
  })

  it('sin tarjetas guardadas muestra el estado vacío y botón "Agregar tarjeta"', async () => {
    setupHijosYTarjetas([HIJO], [])
    render(<CargaSaldo />)
    await screen.findByText('Juan')
    await userEvent.click(screen.getByRole('button', { name: 'Gs. 50.000' }))
    await userEvent.click(screen.getByRole('button', { name: /Tarjeta guardada/i }))

    await screen.findByText(/Todavía no guardaste ninguna tarjeta/i)
    expect(screen.getByRole('button', { name: /Agregar tarjeta/i })).toBeInTheDocument()
  })

  it('seleccionar tarjeta y pagar (aprobado síncrono) redirige con estado=aprobado', async () => {
    setupHijosYTarjetas([HIJO], [TARJETA_GUARDADA])
    vi.mocked(api.post).mockResolvedValue({ data: { estado: 'aprobado', monto: 50_000 } })
    render(<CargaSaldo />)
    await screen.findByText('Juan')
    await userEvent.click(screen.getByRole('button', { name: 'Gs. 50.000' }))
    await userEvent.click(screen.getByRole('button', { name: /Tarjeta guardada/i }))
    await screen.findByText(/5418\*+0014/)

    await userEvent.click(screen.getByText(/5418\*+0014/))
    await waitFor(() => expect(screen.getByRole('button', { name: /Ir a pagar/i })).not.toBeDisabled())
    await userEvent.click(screen.getByRole('button', { name: /Ir a pagar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/core/bancard/pagar-con-tarjeta/',
        expect.objectContaining({ nro_tarjeta: 'T-001', monto: 50_000, card_id: 1 }),
      )
    })
    expect(window.location.href).toContain('estado=aprobado')
  })

  it('pago con tarjeta guardada que requiere 3DS muestra el paso de verificación', async () => {
    setupHijosYTarjetas([HIJO], [TARJETA_GUARDADA])
    vi.mocked(api.post).mockResolvedValue({
      data: { requires_3ds: true, process_id: 'proc-3ds-1', script_url: 'https://vpos.test/checkout.js' },
    })
    render(<CargaSaldo />)
    await screen.findByText('Juan')
    await userEvent.click(screen.getByRole('button', { name: 'Gs. 50.000' }))
    await userEvent.click(screen.getByRole('button', { name: /Tarjeta guardada/i }))
    await screen.findByText(/5418\*+0014/)

    await userEvent.click(screen.getByText(/5418\*+0014/))
    await waitFor(() => expect(screen.getByRole('button', { name: /Ir a pagar/i })).not.toBeDisabled())
    await userEvent.click(screen.getByRole('button', { name: /Ir a pagar/i }))

    await screen.findByText(/Verificación de seguridad/i)
  })

  it('botón "Ir a pagar" queda deshabilitado sin tarjeta seleccionada', async () => {
    setupHijosYTarjetas([HIJO], [TARJETA_GUARDADA])
    render(<CargaSaldo />)
    await screen.findByText('Juan')
    await userEvent.click(screen.getByRole('button', { name: 'Gs. 50.000' }))
    await userEvent.click(screen.getByRole('button', { name: /Tarjeta guardada/i }))
    await screen.findByText(/5418\*+0014/)

    expect(screen.getByRole('button', { name: /Ir a pagar/i })).toBeDisabled()
  })
})
