import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import PagarCC from '../PagarCC'

// PagarCC usa <Link> (Términos y Condiciones) — necesita un Router real
function renderPagarCC() {
  return render(<PagarCC />, { wrapper: MemoryRouter })
}

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return {
    ...actual,
    useSearchParams: vi.fn(() => [new URLSearchParams(), vi.fn()]),
  }
})

vi.mock('../../../store/authStore', () => ({
  useAuthStore: () => ({ user: { nombre: 'María López' }, resetInactivityTimer: vi.fn() }),
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

// ── Helpers ───────────────────────────────────────────────────────────────────

const TARJETA_GUARDADA = {
  card_id: 1, card_masked_number: '5418********0014', card_brand: 'MasterCard', expiration_date: '08/26',
}

function setupDeuda(saldo_cuenta_corriente: number, saldo_cc_cantina = 0, saldo_cc_almuerzo = 0) {
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/core/bancard/tarjetas/') return Promise.resolve({ data: { tarjetas: [] } })
    return Promise.resolve({ data: { cliente: { saldo_cuenta_corriente, saldo_cc_cantina, saldo_cc_almuerzo } } })
  })
}

function setupDeudaYTarjetas(saldo_cuenta_corriente: number, tarjetas: (typeof TARJETA_GUARDADA)[]) {
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/core/bancard/tarjetas/') return Promise.resolve({ data: { tarjetas } })
    return Promise.resolve({ data: { cliente: { saldo_cuenta_corriente } } })
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
  vi.mocked(useSearchParams).mockReturnValue([new URLSearchParams(), vi.fn()])
  vi.stubGlobal('location', { href: '', pathname: '/portal/pagar-cc' })
})

// ── Carga inicial ─────────────────────────────────────────────────────────────

describe('PagarCC — carga inicial', () => {
  it('muestra Spinner mientras la API no responde', () => {
    vi.mocked(api.get).mockReturnValue(new Promise(() => {})) // never resolves
    renderPagarCC()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('sin deuda → "No tenés deuda pendiente"', async () => {
    setupDeuda(0)
    renderPagarCC()
    await screen.findByText(/No tenés deuda pendiente/i)
  })

  it('con deuda → muestra el monto actual', async () => {
    setupDeuda(80_000)
    renderPagarCC()
    await screen.findByText('Deuda actual')
    expect(screen.getByText('Gs. 80.000')).toBeInTheDocument()
  })
})

// ── Resultado de pago ──────────────────────────────────────────────────────────

describe('PagarCC — resultado de pago', () => {
  it('estado=aprobado → "¡Pago aprobado!" con "pagados"', async () => {
    setParams('estado=aprobado&monto=30000')
    setupDeuda(0)
    renderPagarCC()
    await screen.findByText(/Pago aprobado/i)
    expect(screen.getByText(/pagados/i)).toBeInTheDocument()
  })

  it('estado=cancelado → "Pago cancelado"', async () => {
    setParams('estado=cancelado')
    setupDeuda(0)
    renderPagarCC()
    await screen.findByText(/Pago cancelado/i)
  })

  it('estado=rechazado → mensaje de rechazo', async () => {
    setParams('estado=rechazado')
    setupDeuda(0)
    renderPagarCC()
    await screen.findByText(/rechazado/i)
  })

  it('click "Volver a intentar" llama setSearchParams({}) y recarga la deuda', async () => {
    const mockSet = setParams('estado=aprobado&monto=30000')
    setupDeuda(50_000)
    renderPagarCC()
    await screen.findByText(/Pago aprobado/i)

    await userEvent.click(screen.getByRole('button', { name: /Volver a intentar/i }))

    expect(mockSet).toHaveBeenCalledWith({})
    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith('/usuarios/portal/mi-hijo/')
    })
  })
})

// ── Formulario de pago ────────────────────────────────────────────────────────

describe('PagarCC — formulario', () => {
  it('muestra "Pagar el total" con el monto de la deuda', async () => {
    setupDeuda(80_000)
    renderPagarCC()
    await screen.findByText('Deuda actual')

    expect(screen.getByRole('button', { name: /Pagar el total \(Gs\. 80\.000\)/i })).toBeInTheDocument()
  })

  it('seleccionar "Pagar el total" habilita el botón "Ir a pagar"', async () => {
    setupDeuda(80_000)
    renderPagarCC()
    await screen.findByText('Deuda actual')

    const pagarBtn = screen.getByRole('button', { name: /Ir a pagar/i })
    expect(pagarBtn).toBeDisabled()

    await userEvent.click(screen.getByRole('button', { name: /Pagar el total/i }))

    await waitFor(() => expect(pagarBtn).not.toBeDisabled())
  })

  it('monto personalizado mayor a la deuda mantiene el botón deshabilitado y muestra error', async () => {
    setupDeuda(80_000)
    renderPagarCC()
    await screen.findByText('Deuda actual')

    await userEvent.click(screen.getByRole('button', { name: /Otro monto/i }))
    const montoInput = await screen.findByPlaceholderText('50000')
    await userEvent.type(montoInput, '999999')

    expect(screen.getByRole('button', { name: /Ir a pagar/i })).toBeDisabled()
    expect(screen.getByText(/no puede superar tu deuda actual/i)).toBeInTheDocument()
  })

  it('click "Ir a pagar" → api.post a iniciar-cc y muestra el checkout embebido de Bancard', async () => {
    setupDeuda(80_000)
    vi.mocked(api.post).mockResolvedValue({
      data: { process_id: 'proc-cc-1', script_url: 'https://vpos.test/checkout.js' },
    })
    renderPagarCC()
    await screen.findByText('Deuda actual')

    await userEvent.click(screen.getByRole('button', { name: /Pagar el total/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /Ir a pagar/i })).not.toBeDisabled())
    await userEvent.click(screen.getByRole('button', { name: /Ir a pagar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/core/bancard/iniciar-cc/',
        expect.objectContaining({ monto: 80_000 }),
      )
    })
    await screen.findByText(/Ingresá los datos de tu tarjeta/i)
    expect(document.getElementById('bancard-cc-checkout-container')).toBeTruthy()
  })

  it('api.post falla → toast.error con mensaje del servidor', async () => {
    setupDeuda(80_000)
    vi.mocked(api.post).mockRejectedValue({
      response: { data: { detail: 'El monto no puede superar tu deuda actual.' } },
    })
    renderPagarCC()
    await screen.findByText('Deuda actual')

    await userEvent.click(screen.getByRole('button', { name: /Pagar el total/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /Ir a pagar/i })).not.toBeDisabled())
    await userEvent.click(screen.getByRole('button', { name: /Ir a pagar/i }))

    await waitFor(() => {
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('El monto no puede superar tu deuda actual.')
    })
  })
})

// ── Método de pago: tarjeta guardada ──────────────────────────────────────────

describe('PagarCC — tarjeta guardada', () => {
  it('seleccionar tarjeta y pagar (aprobado síncrono) redirige con estado=aprobado', async () => {
    setupDeudaYTarjetas(80_000, [TARJETA_GUARDADA])
    vi.mocked(api.post).mockResolvedValue({ data: { estado: 'aprobado', monto: 80_000 } })
    renderPagarCC()
    await screen.findByText('Deuda actual')

    await userEvent.click(screen.getByRole('button', { name: /Pagar el total/i }))
    await userEvent.click(screen.getByRole('button', { name: /Tarjeta guardada/i }))
    await screen.findByText(/5418\*+0014/)

    await userEvent.click(screen.getByText(/5418\*+0014/))
    await waitFor(() => expect(screen.getByRole('button', { name: /Ir a pagar/i })).not.toBeDisabled())
    await userEvent.click(screen.getByRole('button', { name: /Ir a pagar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/core/bancard/pagar-cc-con-tarjeta/',
        expect.objectContaining({ monto: 80_000, card_id: 1 }),
      )
    })
    expect(window.location.href).toContain('estado=aprobado')
    expect(window.location.href).toContain('tipo=cc')
  })

  it('pago con tarjeta guardada que requiere 3DS muestra el paso de verificación', async () => {
    setupDeudaYTarjetas(80_000, [TARJETA_GUARDADA])
    vi.mocked(api.post).mockResolvedValue({
      data: { requires_3ds: true, process_id: 'proc-cc-3ds-1', script_url: 'https://vpos.test/checkout.js' },
    })
    renderPagarCC()
    await screen.findByText('Deuda actual')

    await userEvent.click(screen.getByRole('button', { name: /Pagar el total/i }))
    await userEvent.click(screen.getByRole('button', { name: /Tarjeta guardada/i }))
    await screen.findByText(/5418\*+0014/)

    await userEvent.click(screen.getByText(/5418\*+0014/))
    await waitFor(() => expect(screen.getByRole('button', { name: /Ir a pagar/i })).not.toBeDisabled())
    await userEvent.click(screen.getByRole('button', { name: /Ir a pagar/i }))

    await screen.findByText(/Verificación de seguridad/i)
  })

  it('botón "Ir a pagar" queda deshabilitado sin tarjeta seleccionada', async () => {
    setupDeudaYTarjetas(80_000, [TARJETA_GUARDADA])
    renderPagarCC()
    await screen.findByText('Deuda actual')

    await userEvent.click(screen.getByRole('button', { name: /Pagar el total/i }))
    await userEvent.click(screen.getByRole('button', { name: /Tarjeta guardada/i }))
    await screen.findByText(/5418\*+0014/)

    expect(screen.getByRole('button', { name: /Ir a pagar/i })).toBeDisabled()
  })
})

// ── Deuda en ambas categorías ──────────────────────────────────────────────────

describe('PagarCC — deuda en cantina y almuerzo', () => {
  it('deuda en una sola categoría no muestra el selector', async () => {
    setupDeuda(80_000, 80_000, 0)
    renderPagarCC()
    await screen.findByText('Deuda actual')

    expect(screen.queryByText(/A qué deuda corresponde/i)).not.toBeInTheDocument()
  })

  it('deuda en ambas categorías muestra el selector y desglose', async () => {
    setupDeuda(150_000, 100_000, 50_000)
    renderPagarCC()
    await screen.findByText('Deuda actual')

    expect(screen.getByText(/¿A qué deuda corresponde el pago\?/i)).toBeInTheDocument()
    expect(screen.getByText(/Cantina: Gs\. 100\.000/)).toBeInTheDocument()
    expect(screen.getByText(/Almuerzo: Gs\. 50\.000/)).toBeInTheDocument()
  })

  it('sin elegir categoría, el botón Ir a pagar queda deshabilitado', async () => {
    setupDeuda(150_000, 100_000, 50_000)
    renderPagarCC()
    await screen.findByText('Deuda actual')

    await userEvent.click(screen.getByRole('button', { name: /Pagar el total/i }))

    expect(screen.getByRole('button', { name: /Ir a pagar/i })).toBeDisabled()
    expect(screen.getByText(/Elegí primero a qué deuda corresponde/i)).toBeInTheDocument()
  })

  it('elegir categoría envía origen a iniciar-cc y topea el monto a esa deuda', async () => {
    setupDeuda(150_000, 100_000, 50_000)
    vi.mocked(api.post).mockResolvedValue({
      data: { process_id: 'proc-cc-origen', script_url: 'https://vpos.test/checkout.js' },
    })
    renderPagarCC()
    await screen.findByText('Deuda actual')

    await userEvent.click(screen.getByRole('button', { name: /^Almuerzo/i }))
    expect(screen.getByRole('button', { name: /Pagar el total \(Gs\. 50\.000\)/i })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: /Pagar el total/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /Ir a pagar/i })).not.toBeDisabled())
    await userEvent.click(screen.getByRole('button', { name: /Ir a pagar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/core/bancard/iniciar-cc/',
        expect.objectContaining({ monto: 50_000, origen: 'ALMUERZO' }),
      )
    })
  })

  it('cambiar de categoría resetea el monto elegido', async () => {
    setupDeuda(150_000, 100_000, 50_000)
    renderPagarCC()
    await screen.findByText('Deuda actual')

    await userEvent.click(screen.getByRole('button', { name: /^Cantina/i }))
    await userEvent.click(screen.getByRole('button', { name: /Pagar el total \(Gs\. 100\.000\)/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /Ir a pagar/i })).not.toBeDisabled())

    await userEvent.click(screen.getByRole('button', { name: /^Almuerzo/i }))

    expect(screen.getByRole('button', { name: /Ir a pagar/i })).toBeDisabled()
  })
})
