import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest'
import Cajas from '../Cajas'

// ── Modal stubs ────────────────────────────────────────────────────────────────

vi.mock('../cajas/ModalAbrir', () => ({
  default: (props: Record<string, unknown>) =>
    props.open ? <div data-testid="modal-abrir" /> : null,
}))

vi.mock('../cajas/ModalCerrar', () => ({
  default: (props: Record<string, unknown>) =>
    props.cierre ? <div data-testid="modal-cerrar" /> : null,
}))

vi.mock('../cajas/ModalConciliar', () => ({
  default: (props: Record<string, unknown>) =>
    props.cierre ? <div data-testid="modal-conciliar" /> : null,
}))

vi.mock('../cajas/ModalMovimiento', () => ({
  default: (props: Record<string, unknown>) =>
    props.tipo
      ? <div data-testid={`modal-movimiento-${String(props.tipo).toLowerCase()}`} />
      : null,
}))

vi.mock('../../services/api', () => ({
  default: { get: vi.fn(), defaults: { baseURL: '/api/v1' } },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../services/api'
import toast from 'react-hot-toast'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const CIERRE_ABIERTO = {
  id_cierre: 1, caja: 1, caja_nombre: 'Caja Principal', caja_activo: true,
  empleado: 1, empleado_nombre: 'Carlos López',
  fecha_apertura: '2026-07-24T08:00:00Z', fecha_cierre: null,
  monto_inicial: '500000', monto_contado_fisico: null,
  diferencia_efectivo: null, estado: 'ABIERTO' as const,
  observaciones_conciliacion: null,
}

const CIERRE_CERRADO = {
  ...CIERRE_ABIERTO, id_cierre: 2, estado: 'CERRADO' as const,
  fecha_cierre: '2026-07-24T16:00:00Z',
  monto_contado_fisico: '498000', diferencia_efectivo: '-2000',
}

const CIERRE_DIFERENCIA_NEGATIVA = {
  ...CIERRE_ABIERTO, id_cierre: 3, estado: 'CERRADO' as const,
  fecha_cierre: '2026-07-24T16:00:00Z',
  monto_contado_fisico: '490000', diferencia_efectivo: '-10000',
}

const ARQUEO = {
  monto_inicial: 500000, efectivo_esperado: 520000,
  efectivo_ingresos: 20000, efectivo_egresos: 0,
  prepago_total: 80000,
  ingresos_total: 20000, egresos_total: 0,
  medios_pago_totales: [
    { medio: 'POS Bancario crédito', total: 100000 },
    { medio: 'POS Bancario debito', total: 50000 },
  ],
  egresos_por_medio: [],
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function mockGet(overrides: Record<string, unknown> = {}) {
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (overrides[url] !== undefined) return overrides[url] as Promise<unknown>
    if (url === '/contabilidad/cierres-caja/') return Promise.resolve({ data: { results: [], count: 0 } })
    if (url === '/contabilidad/cierres-caja/mi-caja/') return Promise.resolve({ data: null })
    if (url.includes('/arqueo/')) return Promise.resolve({ data: ARQUEO })
    return Promise.resolve({ data: { results: [] } })
  })
}

beforeAll(() => {
  vi.stubGlobal('open', vi.fn())
})

beforeEach(() => {
  vi.clearAllMocks()
})

// ── Renderizado inicial ───────────────────────────────────────────────────────

describe('Cajas — renderizado inicial', () => {
  it('sin caja abierta no muestra panel de turno activo', async () => {
    mockGet()
    render(<Cajas />)
    await waitFor(() => expect(vi.mocked(api.get)).toHaveBeenCalled())
    expect(screen.queryByText(/Turno activo/)).not.toBeInTheDocument()
  })

  it('con caja abierta muestra panel de turno activo con botones Ingreso y Egreso', async () => {
    mockGet({
      '/contabilidad/cierres-caja/': Promise.resolve({ data: { results: [CIERRE_ABIERTO], count: 1 } }),
      '/contabilidad/cierres-caja/mi-caja/': Promise.resolve({ data: CIERRE_ABIERTO }),
    })
    render(<Cajas />)
    await screen.findByText(/Turno activo/)
    expect(screen.getByRole('button', { name: /Ingreso/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Egreso/i })).toBeInTheDocument()
  })

  it('el arqueo muestra una tarjeta por cada medio de pago real, sin "Prepago RFID" ni "POS / Transferencia"', async () => {
    mockGet({
      '/contabilidad/cierres-caja/': Promise.resolve({ data: { results: [CIERRE_ABIERTO], count: 1 } }),
      '/contabilidad/cierres-caja/mi-caja/': Promise.resolve({ data: CIERRE_ABIERTO }),
    })
    render(<Cajas />)
    await screen.findByText(/Turno activo/)

    // Una tarjeta dinámica por cada medio de pago real devuelto por el backend
    expect(await screen.findByText('POS Bancario crédito')).toBeInTheDocument()
    expect(screen.getByText('POS Bancario debito')).toBeInTheDocument()
    // La categoría "Prepago" sigue existiendo, pero sin la etiqueta "RFID"
    expect(screen.getByText('Prepago')).toBeInTheDocument()
    expect(screen.queryByText('Prepago RFID')).not.toBeInTheDocument()
    expect(screen.queryByText('POS / Transferencia')).not.toBeInTheDocument()
  })

  it('muestra cierres recibidos de la API en la tabla', async () => {
    mockGet({
      '/contabilidad/cierres-caja/': Promise.resolve({
        data: { results: [CIERRE_ABIERTO, CIERRE_CERRADO], count: 2 },
      }),
    })
    render(<Cajas />)
    const rows = await screen.findAllByText('Carlos López')
    expect(rows).toHaveLength(2)
  })

  it('error de API → toast.error "Error al cargar cierres"', async () => {
    mockGet({
      '/contabilidad/cierres-caja/': Promise.reject(new Error('network')),
    })
    render(<Cajas />)
    await waitFor(() => {
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Error al cargar cierres')
    })
  })
})

// ── Filtros ───────────────────────────────────────────────────────────────────

describe('Cajas — filtros', () => {
  it('al cambiar el selector de estado recarga con el param correspondiente', async () => {
    mockGet()
    render(<Cajas />)
    await waitFor(() => expect(vi.mocked(api.get)).toHaveBeenCalled())

    vi.mocked(api.get).mockClear()
    await userEvent.selectOptions(screen.getByDisplayValue('Todos los estados'), 'ABIERTO')

    await waitFor(() => {
      const call = vi.mocked(api.get).mock.calls.find(c => c[0] === '/contabilidad/cierres-caja/')
      expect(call?.[1]).toMatchObject({ params: expect.objectContaining({ estado: 'ABIERTO' }) })
    })
  })
})

// ── Tabla ─────────────────────────────────────────────────────────────────────

describe('Cajas — tabla', () => {
  it('diferencia negativa se muestra con clase text-red-600', async () => {
    mockGet({
      '/contabilidad/cierres-caja/': Promise.resolve({
        data: { results: [CIERRE_DIFERENCIA_NEGATIVA], count: 1 },
      }),
    })
    render(<Cajas />)
    const row = await screen.findByText('Carlos López')
    const tr = row.closest('tr')!
    expect(tr.querySelector('.text-red-600')).toBeInTheDocument()
  })

  it('paginación Siguiente → recarga la lista con page 2', async () => {
    const veinte = Array.from({ length: 15 }, (_, i) => ({ ...CIERRE_ABIERTO, id_cierre: i + 1 }))
    mockGet({
      '/contabilidad/cierres-caja/': Promise.resolve({ data: { results: veinte, count: 20 } }),
    })
    render(<Cajas />)
    await screen.findAllByText('Carlos López')

    vi.mocked(api.get).mockClear()
    mockGet({
      '/contabilidad/cierres-caja/': Promise.resolve({ data: { results: [], count: 20 } }),
    })
    await userEvent.click(screen.getByRole('button', { name: 'Página siguiente' }))

    await waitFor(() => {
      const call = vi.mocked(api.get).mock.calls.find(c => c[0] === '/contabilidad/cierres-caja/')
      expect(call?.[1]).toMatchObject({ params: expect.objectContaining({ page: 2 }) })
    })
  })
})

// ── Modales ───────────────────────────────────────────────────────────────────

describe('Cajas — modales', () => {
  it('click "Abrir Caja" → ModalAbrir visible', async () => {
    mockGet()
    render(<Cajas />)
    await waitFor(() => expect(vi.mocked(api.get)).toHaveBeenCalled())

    await userEvent.click(screen.getByRole('button', { name: /Abrir Caja/i }))
    expect(screen.getByTestId('modal-abrir')).toBeInTheDocument()
  })

  it('click "Ingreso" en turno activo → ModalMovimiento con tipo INGRESO', async () => {
    mockGet({
      '/contabilidad/cierres-caja/': Promise.resolve({ data: { results: [CIERRE_ABIERTO], count: 1 } }),
      '/contabilidad/cierres-caja/mi-caja/': Promise.resolve({ data: CIERRE_ABIERTO }),
    })
    render(<Cajas />)
    await userEvent.click(await screen.findByRole('button', { name: /^Ingreso$/i }))
    expect(screen.getByTestId('modal-movimiento-ingreso')).toBeInTheDocument()
  })

  it('click "Egreso" en turno activo → ModalMovimiento con tipo EGRESO', async () => {
    mockGet({
      '/contabilidad/cierres-caja/': Promise.resolve({ data: { results: [CIERRE_ABIERTO], count: 1 } }),
      '/contabilidad/cierres-caja/mi-caja/': Promise.resolve({ data: CIERRE_ABIERTO }),
    })
    render(<Cajas />)
    await userEvent.click(await screen.findByRole('button', { name: /^Egreso$/i }))
    expect(screen.getByTestId('modal-movimiento-egreso')).toBeInTheDocument()
  })

  it('click "Cerrar" en fila ABIERTO → ModalCerrar visible', async () => {
    mockGet({
      '/contabilidad/cierres-caja/': Promise.resolve({ data: { results: [CIERRE_ABIERTO], count: 1 } }),
    })
    render(<Cajas />)
    await userEvent.click(await screen.findByRole('button', { name: /^Cerrar$/i }))
    expect(screen.getByTestId('modal-cerrar')).toBeInTheDocument()
  })

  it('click "Conciliar" en fila CERRADO → ModalConciliar visible', async () => {
    mockGet({
      '/contabilidad/cierres-caja/': Promise.resolve({ data: { results: [CIERRE_CERRADO], count: 1 } }),
    })
    render(<Cajas />)
    await userEvent.click(await screen.findByRole('button', { name: /Conciliar/i }))
    expect(screen.getByTestId('modal-conciliar')).toBeInTheDocument()
  })
})
