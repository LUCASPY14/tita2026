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
}

function setupPagos(...pagos: PagoBancard[]) {
  vi.mocked(api.get).mockResolvedValue({ data: { count: pagos.length, results: pagos, next: null, previous: null } })
}

beforeEach(() => {
  vi.clearAllMocks()
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
