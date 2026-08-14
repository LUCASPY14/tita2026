import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import PagosBancard from '../PagosBancard'

vi.mock('../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../services/api'
import toast from 'react-hot-toast'
import type { PagoBancard } from '../../services/pagosBancard'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const HOY = new Date().toISOString()
const AYER = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()

const PAGO_HOY: PagoBancard = {
  shop_process_id: 'pago-hoy-1',
  tipo: 'TARJETA',
  estado: 'APROBADO',
  monto: 50000,
  descripcion: 'Recarga tarjeta 01024',
  cliente_nombre: 'Luis Palau',
  tarjeta_nro: '01024',
  cuenta_almuerzo_id_display: null,
  fecha_creacion: HOY,
  fecha_confirmacion: HOY,
  card_id_bancard: null,
  card_masked_number: '',
}

const PAGO_AYER: PagoBancard = {
  ...PAGO_HOY,
  shop_process_id: 'pago-ayer-1',
  fecha_creacion: AYER,
  fecha_confirmacion: AYER,
}

const PAGO_PENDIENTE: PagoBancard = {
  ...PAGO_HOY,
  shop_process_id: 'pago-pendiente-1',
  estado: 'PENDIENTE',
  fecha_creacion: HOY,
}

const PAGO_PENDIENTE_VIEJO: PagoBancard = {
  ...PAGO_HOY,
  shop_process_id: 'pago-pendiente-viejo-1',
  estado: 'PENDIENTE',
  fecha_creacion: new Date(Date.now() - 90 * 60 * 1000).toISOString(),
}

const PAGO_ERROR: PagoBancard = {
  ...PAGO_HOY,
  shop_process_id: 'pago-error-1',
  estado: 'ERROR',
}

function setupPagos(...pagos: PagoBancard[]) {
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/core/bancard/pagos/') {
      return Promise.resolve({ data: { count: pagos.length, results: pagos, next: null, previous: null } })
    }
    return Promise.resolve({ data: {} })
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  window.URL.createObjectURL = vi.fn(() => 'blob:fake')
  window.URL.revokeObjectURL = vi.fn()
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
})

// ── Tests ────────────────────────────────────────────────────────────────────

describe('PagosBancard', () => {
  it('lista los pagos con fecha, cliente, monto y estado', async () => {
    setupPagos(PAGO_HOY)
    render(<PagosBancard />)
    await screen.findByText('Luis Palau')
    // "Aprobado" también aparece como <option> del filtro — nos quedamos con el badge (span)
    const badges = screen.getAllByText('Aprobado').filter(el => el.tagName === 'SPAN')
    expect(badges).toHaveLength(1)
    expect(screen.getByText('01024')).toBeInTheDocument()
  })

  it('muestra el botón "Anular" solo para pagos aprobados del mismo día', async () => {
    setupPagos(PAGO_HOY, PAGO_AYER, PAGO_PENDIENTE)
    render(<PagosBancard />)
    await screen.findAllByText('Luis Palau')

    const botones = screen.getAllByRole('button', { name: /Anular/i })
    // Solo 2 filas son APROBADO (hoy y ayer); el pendiente no tiene botón
    expect(botones).toHaveLength(2)
    // El de "ayer" está deshabilitado (Bancard solo permite el mismo día)
    const deshabilitado = botones.find(b => (b as HTMLButtonElement).disabled)
    expect(deshabilitado).toBeDefined()
  })

  it('filtra por estado', async () => {
    setupPagos(PAGO_HOY)
    render(<PagosBancard />)
    await screen.findByText('Luis Palau')

    await userEvent.selectOptions(screen.getByDisplayValue('Todos los estados'), 'RECHAZADO')

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/core/bancard/pagos/',
        expect.objectContaining({ params: expect.objectContaining({ estado: 'RECHAZADO' }) }),
      )
    })
  })

  it('click en "Anular" abre confirmación y al aceptar llama a la API', async () => {
    setupPagos(PAGO_HOY)
    vi.mocked(api.post).mockResolvedValue({ data: { detail: 'Pago anulado correctamente.' } })
    render(<PagosBancard />)
    await screen.findByText('Luis Palau')

    await userEvent.click(screen.getByRole('button', { name: /Anular/i }))
    await screen.findByText(/¿Confirmás anular este pago/i)

    await userEvent.click(screen.getByRole('button', { name: /Sí, anular/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith('/core/bancard/pagos/pago-hoy-1/anular/')
    })
    expect(toast.success).toHaveBeenCalledWith('Pago anulado correctamente')
  })

  it('si la anulación falla muestra el mensaje de error del backend', async () => {
    setupPagos(PAGO_HOY)
    vi.mocked(api.post).mockRejectedValue({
      response: { data: { detail: 'La transacción ya fue cuponada.' } },
    })
    render(<PagosBancard />)
    await screen.findByText('Luis Palau')

    await userEvent.click(screen.getByRole('button', { name: /Anular/i }))
    await screen.findByText(/¿Confirmás anular este pago/i)
    await userEvent.click(screen.getByRole('button', { name: /Sí, anular/i }))

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('La transacción ya fue cuponada.')
    })
  })

  it('sin pagos muestra el estado vacío de la tabla', async () => {
    setupPagos()
    render(<PagosBancard />)
    await screen.findByText(/Sin datos/i)
  })
})

describe('PagosBancard — ver detalle', () => {
  it('click en el ícono de detalle pide el detalle y muestra la respuesta de Bancard', async () => {
    setupPagos(PAGO_HOY)
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === '/core/bancard/pagos/') {
        return Promise.resolve({ data: { count: 1, results: [PAGO_HOY], next: null, previous: null } })
      }
      if (url === `/core/bancard/pagos/${PAGO_HOY.shop_process_id}/`) {
        return Promise.resolve({
          data: {
            ...PAGO_HOY,
            process_id: 'proc-123',
            ip_origen: '190.0.0.1',
            bancard_response: { confirmation: { response_code: '00' } },
          },
        })
      }
      return Promise.resolve({ data: {} })
    })
    render(<PagosBancard />)
    await screen.findByText('Luis Palau')

    await userEvent.click(screen.getByTitle('Ver detalle'))

    await screen.findByText('proc-123')
    expect(screen.getByText('190.0.0.1')).toBeInTheDocument()
    expect(screen.getByText(/response_code/)).toBeInTheDocument()
  })
})

describe('PagosBancard — reintentar (estado Error)', () => {
  it('el botón Reintentar solo aparece para pagos en Error', async () => {
    setupPagos(PAGO_HOY, PAGO_ERROR)
    render(<PagosBancard />)
    await screen.findAllByText('Luis Palau')
    expect(screen.getAllByRole('button', { name: /Reintentar/i })).toHaveLength(1)
  })

  it('confirmar reintentar llama a la API y muestra el resultado', async () => {
    setupPagos(PAGO_ERROR)
    vi.mocked(api.post).mockResolvedValue({
      data: { detail: 'Se acreditó el saldo correctamente.', accion: 'acreditado' },
    })
    render(<PagosBancard />)
    await screen.findByText('Luis Palau')

    await userEvent.click(screen.getByRole('button', { name: /Reintentar/i }))
    await screen.findByText(/no se pudo acreditar/i)
    await userEvent.click(screen.getByRole('button', { name: /Sí, reintentar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(`/core/bancard/pagos/${PAGO_ERROR.shop_process_id}/reintentar/`)
    })
    expect(toast.success).toHaveBeenCalledWith('Se acreditó el saldo correctamente.')
  })

  it('si vuelve a fallar muestra el mensaje de error del backend', async () => {
    setupPagos(PAGO_ERROR)
    vi.mocked(api.post).mockRejectedValue({ response: { data: { detail: 'Volvió a fallar.' } } })
    render(<PagosBancard />)
    await screen.findByText('Luis Palau')

    await userEvent.click(screen.getByRole('button', { name: /Reintentar/i }))
    await screen.findByText(/no se pudo acreditar/i)
    await userEvent.click(screen.getByRole('button', { name: /Sí, reintentar/i }))

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith('Volvió a fallar.'))
  })
})

describe('PagosBancard — reconsultar (estado Pendiente)', () => {
  it('el botón Reconsultar solo aparece para pagos pendientes', async () => {
    setupPagos(PAGO_HOY, PAGO_PENDIENTE)
    render(<PagosBancard />)
    await screen.findAllByText('Luis Palau')
    expect(screen.getAllByRole('button', { name: /Reconsultar/i })).toHaveLength(1)
  })

  it('click en Reconsultar llama a la API directamente (sin modal) y muestra el resultado', async () => {
    setupPagos(PAGO_PENDIENTE)
    vi.mocked(api.post).mockResolvedValue({
      data: { detail: 'Bancard confirmó el resultado: Aprobado.', resuelto: true },
    })
    render(<PagosBancard />)
    await screen.findByText('Luis Palau')

    await userEvent.click(screen.getByRole('button', { name: /Reconsultar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        `/core/bancard/pagos/${PAGO_PENDIENTE.shop_process_id}/reconsultar/`,
      )
    })
    expect(toast.success).toHaveBeenCalledWith('Bancard confirmó el resultado: Aprobado.')
  })
})

describe('PagosBancard — cerrar manualmente (estado Pendiente)', () => {
  it('el botón Cerrar está deshabilitado si el pago es muy reciente', async () => {
    setupPagos(PAGO_PENDIENTE)
    render(<PagosBancard />)
    await screen.findByText('Luis Palau')

    const boton = screen.getByRole('button', { name: /Cerrar/i })
    expect(boton).toBeDisabled()
  })

  it('habilitado para un pendiente viejo — confirmar llama a la API', async () => {
    setupPagos(PAGO_PENDIENTE_VIEJO)
    vi.mocked(api.post).mockResolvedValue({
      data: { detail: 'Pago cerrado manualmente como no completado.' },
    })
    render(<PagosBancard />)
    await screen.findByText('Luis Palau')

    const boton = screen.getByRole('button', { name: /Cerrar/i })
    expect(boton).not.toBeDisabled()
    await userEvent.click(boton)
    await screen.findByText(/vuelve a consultar el resultado real/i)
    await userEvent.click(screen.getByRole('button', { name: /Sí, cerrar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        `/core/bancard/pagos/${PAGO_PENDIENTE_VIEJO.shop_process_id}/cerrar-manual/`,
      )
    })
    expect(toast.success).toHaveBeenCalledWith('Pago cerrado manualmente como no completado.')
  })
})

describe('PagosBancard — exportar CSV', () => {
  it('click en Exportar CSV pide el CSV con los filtros actuales y descarga el blob', async () => {
    setupPagos(PAGO_HOY)
    vi.mocked(api.get).mockImplementation((url: string, config?: { params?: Record<string, unknown> }) => {
      if (url === '/core/bancard/pagos/' && config?.params?.formato === 'csv') {
        return Promise.resolve({ data: new Blob(['csv']) })
      }
      if (url === '/core/bancard/pagos/') {
        return Promise.resolve({ data: { count: 1, results: [PAGO_HOY], next: null, previous: null } })
      }
      return Promise.resolve({ data: {} })
    })
    render(<PagosBancard />)
    await screen.findByText('Luis Palau')

    await userEvent.click(screen.getByRole('button', { name: /Exportar CSV/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/core/bancard/pagos/',
        expect.objectContaining({ params: expect.objectContaining({ formato: 'csv' }), responseType: 'blob' }),
      )
    })
    expect(window.URL.createObjectURL).toHaveBeenCalled()
    expect(toast.success).toHaveBeenCalledWith('CSV descargado')
  })
})
