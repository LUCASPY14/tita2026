import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import CargaSaldo from '../CargaSaldo'

function renderCargaSaldo() {
  return render(
    <MemoryRouter>
      <CargaSaldo />
    </MemoryRouter>,
  )
}

vi.mock('../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

let mockUser: { rol: string } | null = null
vi.mock('../../store/authStore', () => ({
  useAuthStore: () => ({ user: mockUser }),
}))

import api from '../../services/api'
import toast from 'react-hot-toast'

const TARJETA = {
  nro_tarjeta: 'T-00001',
  codigo_barras: null,
  hijo_nombre: 'Juan Pérez',
  hijo_grado: '3° A',
  cliente_nombre: 'Carlos Pérez',
  saldo_actual: '50000',
  saldo_disponible: '50000',
  estado: 'ACTIVA',
  cliente_permite_cuenta_corriente: true,
}

const TARJETA_CON_HIJO = { ...TARJETA, hijo: 7 }

function mockBuscarSuccess() {
  vi.mocked(api.get)
    .mockResolvedValueOnce({ data: { results: [TARJETA] } })
    .mockResolvedValueOnce({ data: { results: [] } })
    .mockResolvedValueOnce({ data: { results: [] } })
}

function mockBuscarSuccessConHijo(saldoAlmuerzo = -15000) {
  vi.mocked(api.get)
    .mockResolvedValueOnce({ data: { results: [TARJETA_CON_HIJO] } }) // buscar
    .mockResolvedValueOnce({ data: { results: [] } })                 // movimientos
    .mockResolvedValueOnce({ data: { results: [] } })                 // cargas
    .mockResolvedValueOnce({ data: { results: [] } })                 // recargas-saldo almuerzo
    .mockResolvedValueOnce({ data: { results: [{ saldo_actual: saldoAlmuerzo }] } }) // saldo almuerzo
}

beforeEach(() => {
  vi.clearAllMocks()
  mockUser = null
})

// ─── Búsqueda ──────────────────────────────────────────────────────────────────

describe('CargaSaldo — búsqueda', () => {
  it('muestra el formulario de búsqueda inicialmente', () => {
    renderCargaSaldo()
    expect(screen.getByText('Carga de Saldo')).toBeInTheDocument()
    expect(screen.getByText('Pasá la tarjeta')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Nro. de tarjeta...')).toBeInTheDocument()
  })

  it('muestra toast.error si busqueda está vacía', async () => {
    renderCargaSaldo()
    await userEvent.click(screen.getByRole('button'))
    expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Ingresá el número de tarjeta')
  })

  it('busca al presionar Enter en el input', async () => {
    mockBuscarSuccess()
    renderCargaSaldo()
    const input = screen.getByPlaceholderText('Nro. de tarjeta...')
    await userEvent.type(input, 'T-00001')
    await userEvent.keyboard('{Enter}')
    await screen.findByText('Juan Pérez')
  })

  it('muestra toast.error si la tarjeta no se encuentra', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: { results: [] } })
    renderCargaSaldo()
    await userEvent.type(screen.getByPlaceholderText('Nro. de tarjeta...'), 'T-99999')
    await userEvent.click(screen.getByRole('button'))
    await waitFor(() => {
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Tarjeta no encontrada')
    })
  })

  it('muestra toast.error si la tarjeta está BLOQUEADA', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { results: [{ ...TARJETA, estado: 'BLOQUEADA' }] },
    })
    renderCargaSaldo()
    await userEvent.type(screen.getByPlaceholderText('Nro. de tarjeta...'), 'T-00001')
    await userEvent.click(screen.getByRole('button'))
    await waitFor(() => {
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith(
        expect.stringContaining('bloqueada')
      )
    })
  })

  it('muestra los datos de la tarjeta al encontrarla', async () => {
    mockBuscarSuccess()
    renderCargaSaldo()
    await userEvent.type(screen.getByPlaceholderText('Nro. de tarjeta...'), 'T-00001')
    await userEvent.click(screen.getByRole('button'))
    expect(await screen.findByText('Juan Pérez')).toBeInTheDocument()
    expect(screen.getByText('3° A · Carlos Pérez')).toBeInTheDocument()
    expect(screen.getByText('T-00001')).toBeInTheDocument()
  })
})

// ─── Formulario de carga ───────────────────────────────────────────────────────

describe('CargaSaldo — formulario de carga', () => {
  async function renderConTarjeta() {
    const user = userEvent.setup()
    mockBuscarSuccess()
    renderCargaSaldo()
    await user.type(screen.getByPlaceholderText('Nro. de tarjeta...'), 'T-00001')
    // único botón visible antes de encontrar tarjeta
    await user.click(screen.getByRole('button'))
    await screen.findByText('Juan Pérez')
    return user
  }

  it('muestra botones de monto rápido', async () => {
    await renderConTarjeta()
    expect(screen.getByRole('button', { name: '10.000' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '50.000' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '200.000' })).toBeInTheDocument()
  })

  it('al hacer click en monto rápido rellena el input', async () => {
    const user = await renderConTarjeta()
    await user.click(screen.getByRole('button', { name: '10.000' }))
    const montoInput = screen.getByPlaceholderText('0') as HTMLInputElement
    expect(montoInput.value).toBe('10000')
  })

  it('el método TRANSFERENCIA muestra "queda pendiente"', async () => {
    await renderConTarjeta()
    expect(screen.getByText('queda pendiente')).toBeInTheDocument()
  })

  it('aparece campo Referencia al seleccionar TRANSFERENCIA', async () => {
    const user = await renderConTarjeta()
    await user.click(screen.getByRole('button', { name: /Transferencia/i }))
    expect(screen.getByPlaceholderText('Nro. de transferencia...')).toBeInTheDocument()
  })

  it('muestra toast.error si monto es 0 al cargar', async () => {
    const user = await renderConTarjeta()
    await user.click(screen.getByRole('button', { name: /Cargar saldo/i }))
    expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Ingresá un monto válido')
  })

  it('registra carga exitosamente y muestra "Carga realizada"', async () => {
    const user = await renderConTarjeta()

    vi.mocked(api.post).mockResolvedValueOnce({ data: { id: 99, estado: 'CONFIRMADA' } })
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { ...TARJETA, saldo_disponible: '60000' } })
      .mockResolvedValueOnce({ data: { results: [] } })
      .mockResolvedValueOnce({ data: { results: [] } })

    await user.click(screen.getByRole('button', { name: '10.000' }))
    await user.click(screen.getByRole('button', { name: /Cargar saldo/i }))

    await waitFor(() => {
      expect(vi.mocked(toast.success)).toHaveBeenCalledWith(
        expect.stringContaining('confirmada')
      )
    })
    await screen.findByText('Carga realizada')
  })
})

// ─── Saldo de almuerzo ──────────────────────────────────────────────────────────

describe('CargaSaldo — saldo de almuerzo', () => {
  async function renderConTarjetaConHijo(saldoAlmuerzo = -15000) {
    const user = userEvent.setup()
    mockBuscarSuccessConHijo(saldoAlmuerzo)
    renderCargaSaldo()
    await user.type(screen.getByPlaceholderText('Nro. de tarjeta...'), 'T-00001')
    await user.click(screen.getByRole('button'))
    await screen.findByText('Juan Pérez')
    return user
  }

  it('tarjeta sin hijo asociado → no muestra el toggle "Saldo a cargar"', async () => {
    await (async () => {
      const user = userEvent.setup()
      mockBuscarSuccess()
      renderCargaSaldo()
      await user.type(screen.getByPlaceholderText('Nro. de tarjeta...'), 'T-00001')
      await user.click(screen.getByRole('button'))
      await screen.findByText('Juan Pérez')
    })()
    expect(screen.queryByText('Saldo a cargar')).not.toBeInTheDocument()
  })

  it('tarjeta con hijo → muestra el saldo de almuerzo y el toggle', async () => {
    await renderConTarjetaConHijo(-15000)
    expect(screen.getByText('Saldo a cargar')).toBeInTheDocument()
    expect(screen.getByText('Saldo almuerzo')).toBeInTheDocument()
    expect(screen.getByText('Gs. -15.000')).toBeInTheDocument()
    expect(screen.getByText('debe')).toBeInTheDocument()
  })

  it('cliente sin cuenta corriente habilitada → botón "Crédito CC" deshabilitado', async () => {
    const user = userEvent.setup()
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { results: [{ ...TARJETA_CON_HIJO, cliente_permite_cuenta_corriente: false }] } })
      .mockResolvedValueOnce({ data: { results: [] } })
      .mockResolvedValueOnce({ data: { results: [] } })
      .mockResolvedValueOnce({ data: { results: [{ saldo_actual: -15000 }] } })
    renderCargaSaldo()
    await user.type(screen.getByPlaceholderText('Nro. de tarjeta...'), 'T-00001')
    await user.click(screen.getByRole('button'))
    await screen.findByText('Juan Pérez')

    expect(screen.getByRole('button', { name: /Crédito CC/i })).toBeDisabled()
    expect(screen.getByText(/no tiene habilitada la cuenta corriente/i)).toBeInTheDocument()
  })

  it('seleccionar "Almuerzo" mantiene visible el toggle Contado/Crédito', async () => {
    const user = await renderConTarjetaConHijo()
    expect(screen.getByText('Tipo de cobro')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Almuerzo' }))

    expect(screen.getByText('Tipo de cobro')).toBeInTheDocument()
  })

  it('recargar saldo de almuerzo llama a /almuerzos/recargas-saldo/ con hijo_id', async () => {
    const user = await renderConTarjetaConHijo(-15000)
    await user.click(screen.getByRole('button', { name: 'Almuerzo' }))

    vi.mocked(api.post).mockResolvedValueOnce({ data: { id: 1, estado: 'CONFIRMADA' } })
    vi.mocked(api.get).mockResolvedValueOnce({ data: { results: [{ saldo_actual: 10000 }] } })

    await user.click(screen.getByRole('button', { name: '20.000' }))
    await user.click(screen.getByRole('button', { name: /Cargar saldo de almuerzo/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/almuerzos/recargas-saldo/',
        expect.objectContaining({ hijo: 7, monto_cargado: 20000, metodo_pago: 'EFECTIVO' }),
      )
    })
    await screen.findByText('Recarga de almuerzo realizada')
    expect(screen.getByText('Gs. 10.000')).toBeInTheDocument()
  })

  it('almuerzo con Crédito CC llama a /almuerzos/recargas-saldo/ con CUENTA_CORRIENTE', async () => {
    const user = await renderConTarjetaConHijo(-15000)
    await user.click(screen.getByRole('button', { name: 'Almuerzo' }))
    await user.click(screen.getByRole('button', { name: /Crédito CC/i }))

    vi.mocked(api.post).mockResolvedValueOnce({ data: { id: 1, estado: 'CONFIRMADA' } })
    vi.mocked(api.get).mockResolvedValueOnce({ data: { results: [{ saldo_actual: 5000 }] } })

    await user.click(screen.getByRole('button', { name: '20.000' }))
    await user.click(screen.getByRole('button', { name: /Cargar a cuenta corriente/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/almuerzos/recargas-saldo/',
        expect.objectContaining({ hijo: 7, monto_cargado: 20000, metodo_pago: 'CUENTA_CORRIENTE' }),
      )
    })
    await screen.findByText('Recarga de almuerzo realizada')
  })
})

// ─── Anular carga confirmada ────────────────────────────────────────────────

const CARGA_CONFIRMADA = {
  id_carga: 55,
  monto_cargado: 20000,
  metodo_pago: 'EFECTIVO',
  estado: 'CONFIRMADA',
  fecha_carga: '2026-10-20T10:00:00Z',
}

function mockBuscarSuccessConCarga() {
  vi.mocked(api.get)
    .mockResolvedValueOnce({ data: { results: [TARJETA] } })
    .mockResolvedValueOnce({ data: { results: [] } })
    .mockResolvedValueOnce({ data: { results: [CARGA_CONFIRMADA] } })
}

async function irATabCargas() {
  const user = userEvent.setup()
  renderCargaSaldo()
  await user.type(screen.getByPlaceholderText('Nro. de tarjeta...'), 'T-00001')
  await user.keyboard('{Enter}')
  await screen.findByText('Juan Pérez')
  await user.click(screen.getByRole('button', { name: 'Cargas de saldo' }))
  return user
}

describe('CargaSaldo — anular carga confirmada', () => {
  it('ADMIN ve el botón Anular en una carga CONFIRMADA', async () => {
    mockUser = { rol: 'ADMIN' }
    mockBuscarSuccessConCarga()
    await irATabCargas()
    expect(await screen.findByRole('button', { name: 'Anular' })).toBeInTheDocument()
  })

  it('un rol que no es ADMIN no ve el botón Anular', async () => {
    mockUser = { rol: 'CAJERO' }
    mockBuscarSuccessConCarga()
    await irATabCargas()
    await screen.findByText('Gs. 20.000')
    expect(screen.queryByRole('button', { name: 'Anular' })).not.toBeInTheDocument()
  })

  it('confirmar la anulación llama al endpoint y refresca el historial', async () => {
    mockUser = { rol: 'ADMIN' }
    mockBuscarSuccessConCarga()
    const user = await irATabCargas()

    await user.click(await screen.findByRole('button', { name: 'Anular' }))
    expect(await screen.findByText('Esta acción es irreversible')).toBeInTheDocument()

    vi.mocked(api.post).mockResolvedValueOnce({ data: { id_carga: 55, estado: 'ANULADA' } })
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { results: [TARJETA] } })
      .mockResolvedValueOnce({ data: { results: [] } })
      .mockResolvedValueOnce({ data: { results: [{ ...CARGA_CONFIRMADA, estado: 'ANULADA' }] } })

    await user.click(screen.getByRole('button', { name: 'Confirmar anulación' }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith('/core/cargas-saldo/55/anular/')
      expect(vi.mocked(toast.success)).toHaveBeenCalledWith('Carga #55 anulada')
    })
  })
})

// ─── Anular recarga de almuerzo ─────────────────────────────────────────────

const RECARGA_ALMUERZO_CONFIRMADA = {
  id_recarga_almuerzo: 77,
  monto_cargado: 15000,
  metodo_pago: 'EFECTIVO',
  estado: 'CONFIRMADA',
  fecha_carga: '2026-10-20T10:00:00Z',
}

function mockBuscarConHijoYRecarga() {
  vi.mocked(api.get)
    .mockResolvedValueOnce({ data: { results: [TARJETA_CON_HIJO] } })          // buscar
    .mockResolvedValueOnce({ data: { results: [] } })                          // movimientos
    .mockResolvedValueOnce({ data: { results: [] } })                          // cargas
    .mockResolvedValueOnce({ data: { results: [RECARGA_ALMUERZO_CONFIRMADA] } }) // recargas-saldo almuerzo
    .mockResolvedValueOnce({ data: { results: [{ saldo_actual: 5000 }] } })     // saldo almuerzo
}

async function irATabRecargasAlmuerzo() {
  const user = userEvent.setup()
  renderCargaSaldo()
  await user.type(screen.getByPlaceholderText('Nro. de tarjeta...'), 'T-00001')
  await user.keyboard('{Enter}')
  await screen.findByText('Juan Pérez')
  await user.click(screen.getByRole('button', { name: 'Recargas de almuerzo' }))
  return user
}

describe('CargaSaldo — anular recarga de almuerzo', () => {
  it('ADMIN ve el botón Anular en una recarga de almuerzo CONFIRMADA', async () => {
    mockUser = { rol: 'ADMIN' }
    mockBuscarConHijoYRecarga()
    await irATabRecargasAlmuerzo()
    expect(await screen.findByRole('button', { name: 'Anular' })).toBeInTheDocument()
  })

  it('un rol que no es ADMIN no ve el botón Anular', async () => {
    mockUser = { rol: 'CAJERO' }
    mockBuscarConHijoYRecarga()
    await irATabRecargasAlmuerzo()
    await screen.findByText('Gs. 15.000')
    expect(screen.queryByRole('button', { name: 'Anular' })).not.toBeInTheDocument()
  })

  it('confirmar la anulación llama al endpoint de almuerzo y refresca', async () => {
    mockUser = { rol: 'ADMIN' }
    mockBuscarConHijoYRecarga()
    const user = await irATabRecargasAlmuerzo()

    await user.click(await screen.findByRole('button', { name: 'Anular' }))
    expect(await screen.findByText('Esta acción es irreversible')).toBeInTheDocument()

    vi.mocked(api.post).mockResolvedValueOnce({ data: { id_recarga_almuerzo: 77, estado: 'ANULADA' } })
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { results: [{ ...RECARGA_ALMUERZO_CONFIRMADA, estado: 'ANULADA' }] } })
      .mockResolvedValueOnce({ data: { results: [{ saldo_actual: 0 }] } })

    await user.click(screen.getByRole('button', { name: 'Confirmar anulación' }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith('/almuerzos/recargas-saldo/77/anular/')
      expect(vi.mocked(toast.success)).toHaveBeenCalledWith('Recarga #77 anulada')
    })
  })

  it('tarjeta sin hijo no muestra la pestaña "Recargas de almuerzo"', async () => {
    mockUser = { rol: 'ADMIN' }
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { results: [TARJETA] } })
      .mockResolvedValueOnce({ data: { results: [] } })
      .mockResolvedValueOnce({ data: { results: [] } })
    const user = userEvent.setup()
    renderCargaSaldo()
    await user.type(screen.getByPlaceholderText('Nro. de tarjeta...'), 'T-00001')
    await user.keyboard('{Enter}')
    await screen.findByText('Juan Pérez')
    expect(screen.queryByRole('button', { name: 'Recargas de almuerzo' })).not.toBeInTheDocument()
  })
})
