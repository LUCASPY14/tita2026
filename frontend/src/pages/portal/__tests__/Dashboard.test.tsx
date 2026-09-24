import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import PortalDashboard from '../Dashboard'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

let mockUser: Record<string, unknown> = { nombre: 'María López' }
vi.mock('../../../store/authStore', () => ({
  useAuthStore: () => ({ user: mockUser }),
}))

// PortalDashboard ahora usa <Link> (banner de 2FA) — necesita un Router real
function renderDashboard() {
  return render(<PortalDashboard />, { wrapper: MemoryRouter })
}

vi.mock('../../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../services/api'
import toast from 'react-hot-toast'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const HIJO_BASE = {
  id_hijo: 1,
  nombre: 'Juan García',
  grado: '3° A',
  tarjeta: { nro_tarjeta: 'T-001', saldo_actual: 75_000, estado: 'ACTIVA', en_alerta: false },
  restricciones: [] as { tipo: string; severidad: string; descripcion: string; requiere_autorizacion: boolean }[],
  consumos_mes: {
    total: 0, cobrados: 0,
    ultimos: [] as { fecha_consumo: string; costo_almuerzo: string; ya_cobrado: boolean }[],
  },
  consumo_mes: null as { cantidad_almuerzos: number; monto_total: number } | null,
  saldo_almuerzo: 0,
  top_productos: [] as { producto: string; cantidad: number }[],
}

const HIJO_CON_CUENTA = {
  ...HIJO_BASE,
  id_hijo: 1,
  consumos_mes: {
    total: 5, cobrados: 3,
    ultimos: [] as { fecha_consumo: string; costo_almuerzo: string; ya_cobrado: boolean }[],
  },
  consumo_mes: { cantidad_almuerzos: 5, monto_total: 100_000 } as { cantidad_almuerzos: number; monto_total: number } | null,
}

const HIJO2 = {
  ...HIJO_BASE,
  id_hijo: 2,
  nombre: 'Lucía García',
  grado: '5° B',
  tarjeta: { nro_tarjeta: 'T-002', saldo_actual: 20_000, estado: 'ACTIVA', en_alerta: true },
}

const PORTAL_DATA = {
  cliente: {
    id: 99, nombre: 'María López', email: 'maria@test.com',
    saldo_cuenta_corriente: 0, limite_credito: 0,
  },
  mes: { anio: 2026, mes: 7 },
  hijos: [HIJO_CON_CUENTA],
}

function setupPortal(
  override: Record<string, unknown> = {},
  historial: Record<string, unknown> = {},
  recargas: Record<string, unknown> = {},
) {
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/usuarios/portal/mi-hijo/') return Promise.resolve({ data: { ...PORTAL_DATA, ...override } })
    if (url === '/usuarios/portal/historial-cantina/') return Promise.resolve({ data: { results: [], next: null } })
    if (url === '/usuarios/portal/historial-recargas/') {
      return Promise.resolve({ data: { count: 0, next: false, results: [], ...recargas } })
    }
    if (url === '/usuarios/portal/historial-consumos/') {
      return Promise.resolve({
        data: { anio: 2026, mes: 7, consumos: [], saldo_almuerzo: 0, total: 0, monto_total: 0, ...historial },
      })
    }
    return Promise.resolve({ data: {} })
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  // Con 2FA activo por defecto para no mostrar el banner en los tests que no lo prueban
  mockUser = { nombre: 'María López', tiene_2fa_activo: true }
  localStorage.clear()
})

// ── Loading y error ───────────────────────────────────────────────────────────

describe('PortalDashboard — loading y error', () => {
  it('muestra Spinner mientras la API no responde', () => {
    vi.mocked(api.get).mockReturnValue(new Promise(() => {}))
    renderDashboard()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('error de red → muestra "No se pudieron cargar los datos"', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('network'))
    renderDashboard()

    await screen.findByText(/No se pudieron cargar los datos/i)
    expect(vi.mocked(toast.error)).toHaveBeenCalled()
  })

  it('click "Reintentar" vuelve a llamar la API', async () => {
    vi.mocked(api.get)
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValue({ data: PORTAL_DATA })

    renderDashboard()
    await screen.findByText(/No se pudieron cargar/i)

    await userEvent.click(screen.getByRole('button', { name: /Reintentar/i }))

    await screen.findByText('Hola, María López')
  })
})

// ── Estados vacíos y datos ────────────────────────────────────────────────────

describe('PortalDashboard — datos', () => {
  it('sin hijos → "Sin hijos asociados"', async () => {
    setupPortal({ hijos: [] })
    renderDashboard()

    await screen.findByText(/Sin hijos asociados/i)
  })

  it('muestra saludo con nombre del usuario', async () => {
    setupPortal()
    renderDashboard()

    await screen.findByText('Hola, María López')
  })

  it('con top_productos → muestra la sección "Lo más consumido"', async () => {
    setupPortal({
      hijos: [{
        ...HIJO_CON_CUENTA,
        top_productos: [
          { producto: 'Sandwich de milanesa', cantidad: 8 },
          { producto: 'Coca Cola 500ml', cantidad: 6 },
        ],
      }],
    })
    renderDashboard()

    await screen.findByText(/Lo más consumido/i)
    expect(screen.getByText('Sandwich de milanesa')).toBeInTheDocument()
    expect(screen.getByText('8 veces')).toBeInTheDocument()
    expect(screen.getByText('Coca Cola 500ml')).toBeInTheDocument()
  })

  it('cantidad=1 → usa singular "1 vez" en vez de "1 veces"', async () => {
    setupPortal({
      hijos: [{
        ...HIJO_CON_CUENTA,
        top_productos: [{ producto: 'Sandwich de milanesa', cantidad: 1 }],
      }],
    })
    renderDashboard()

    await screen.findByText('1 vez')
    expect(screen.queryByText('1 veces')).not.toBeInTheDocument()
  })

  it('sin top_productos → no muestra la sección "Lo más consumido"', async () => {
    setupPortal()
    renderDashboard()

    await screen.findByText('Hola, María López')
    expect(screen.queryByText(/Lo más consumido/i)).not.toBeInTheDocument()
  })

  it('múltiples hijos → muestra selector con el nombre de cada hijo', async () => {
    setupPortal({ hijos: [HIJO_CON_CUENTA, HIJO2] })
    renderDashboard()

    // Esperar al botón del selector (no al texto del card header, que también dice "Juan García")
    await screen.findByRole('button', { name: 'Juan García' })
    expect(screen.getByRole('button', { name: 'Lucía García' })).toBeInTheDocument()
  })

  it('click en hijo secundario lo selecciona como activo', async () => {
    setupPortal({ hijos: [HIJO_CON_CUENTA, HIJO2] })
    renderDashboard()
    await screen.findByRole('button', { name: 'Juan García' })

    await userEvent.click(screen.getByRole('button', { name: 'Lucía García' }))

    // El grado de Lucía aparece en el header del card activo
    await screen.findByText('5° B')
  })
})

// ── Saldo de almuerzo ─────────────────────────────────────────────────────────

describe('PortalDashboard — saldo de almuerzo', () => {
  it('saldo positivo → se muestra sin aviso de deuda', async () => {
    setupPortal({ hijos: [{ ...HIJO_CON_CUENTA, saldo_almuerzo: 30_000 }] })
    renderDashboard()

    await screen.findByText('Gs. 30.000')
    expect(screen.queryByText(/Debe/i)).not.toBeInTheDocument()
  })

  it('saldo negativo → se muestra en rojo con mensaje "Debe"', async () => {
    setupPortal({ hijos: [{ ...HIJO_CON_CUENTA, saldo_almuerzo: -20_000 }] })
    renderDashboard()

    await screen.findByText('Gs. -20.000')
    expect(screen.getByText(/Debe/i)).toBeInTheDocument()
  })

  it('botón "Recargar saldo de almuerzo" navega con el hijo_id correcto', async () => {
    setupPortal({ hijos: [{ ...HIJO_CON_CUENTA, saldo_almuerzo: -20_000 }] })
    renderDashboard()
    await screen.findByText('Gs. -20.000')

    await userEvent.click(screen.getByRole('button', { name: /Recargar saldo de almuerzo/i }))

    expect(mockNavigate).toHaveBeenCalledWith('/portal/carga-saldo?tipo=ALMUERZO&hijo_id=1')
  })
})

describe('PortalDashboard — cuenta corriente', () => {
  it('sin deuda → no muestra la tarjeta de cuenta corriente', async () => {
    setupPortal()
    renderDashboard()
    await screen.findByText('Hola, María López')

    expect(screen.queryByText('Cuenta corriente')).not.toBeInTheDocument()
  })

  it('con deuda → muestra el monto y el botón "Pagar ahora"', async () => {
    setupPortal({ cliente: { ...PORTAL_DATA.cliente, saldo_cuenta_corriente: 45_000 } })
    renderDashboard()

    await screen.findByText('Cuenta corriente')
    expect(screen.getByText('Gs. 45.000')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Pagar ahora/i })).toHaveAttribute('href', '/portal/pagar-cc')
  })
})

// ── Tabs ──────────────────────────────────────────────────────────────────────

describe('PortalDashboard — tabs', () => {
  it('tab Resumen (por defecto) muestra nro de tarjeta del hijo', async () => {
    setupPortal()
    renderDashboard()

    await screen.findByText('T-001')
    expect(screen.getByText('Tarjeta escolar')).toBeInTheDocument()
  })

  it('tab Almuerzos → muestra "Sin ingresos al comedor" cuando total es 0', async () => {
    setupPortal({ hijos: [HIJO_BASE] })
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Almuerzos/i }))

    await screen.findByText(/Sin ingresos al comedor registrados este mes/i)
  })

  it('tab Almuerzos → llama historial-consumos con el mes actual y muestra los consumos', async () => {
    setupPortal({}, {
      total: 2, monto_total: 25000,
      consumos: [{ id_registro_consumo: 1, fecha_consumo: '2026-07-15', costo_almuerzo: '25000' }],
    })
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Almuerzos/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/usuarios/portal/historial-consumos/',
        expect.objectContaining({ params: expect.objectContaining({ hijo_id: 1, anio: 2026, mes: 7 }) }),
      )
    })
    await screen.findByLabelText('Mes anterior')
    expect(screen.getAllByText('Gs. 25.000').length).toBeGreaterThan(0)
  })

  it('tab Almuerzos → muestra la fecha del consumo sin corrimiento de un día (bug de UTC)', async () => {
    setupPortal({}, {
      total: 1, monto_total: 25000,
      consumos: [{ id_registro_consumo: 1, fecha_consumo: '2026-09-23', costo_almuerzo: '25000' }],
    })
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Almuerzos/i }))

    // new Date('2026-09-23') sin hora se interpreta como UTC medianoche; en
    // Paraguay (UTC-3) eso mostraba "22/09/2026" en vez de "23/09/2026".
    await screen.findByText('23/09/2026')
  })

  it('tab Almuerzos → muestra la hora exacta del ingreso al comedor', async () => {
    // Para poder demostrarle a un padre a qué hora exacta entró su hijo,
    // no solo el día — hora_registro viaja de la API junto a fecha_consumo.
    setupPortal({}, {
      total: 1, monto_total: 25000,
      consumos: [{
        id_registro_consumo: 1, fecha_consumo: '2026-09-23',
        hora_registro: '12:47:30', costo_almuerzo: '25000',
      }],
    })
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Almuerzos/i }))

    await screen.findByText(/12:47/)
  })

  it('tab Almuerzos → con saldo de almuerzo en deuda, muestra el saldo real en rojo', async () => {
    setupPortal({}, {
      total: 1, monto_total: 25000, saldo_almuerzo: -125000,
      consumos: [{ id_registro_consumo: 1, fecha_consumo: '2026-07-15', costo_almuerzo: '25000' }],
    })
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Almuerzos/i }))

    await screen.findByText('Gs. -125.000')
    expect(screen.getByText(/Pendiente de pago/i)).toBeInTheDocument()
  })

  it('tab Almuerzos → con saldo de almuerzo al día, no muestra aviso de deuda', async () => {
    setupPortal({}, {
      total: 1, monto_total: 25000, saldo_almuerzo: 0,
      consumos: [{ id_registro_consumo: 1, fecha_consumo: '2026-07-15', costo_almuerzo: '25000' }],
    })
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Almuerzos/i }))

    await screen.findByText('Gs. 0')
    expect(screen.queryByText(/Pendiente de pago/i)).not.toBeInTheDocument()
  })

  it('tab Almuerzos → "Mes siguiente" queda deshabilitado en el mes actual', async () => {
    setupPortal()
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Almuerzos/i }))
    await screen.findByLabelText('Mes siguiente')

    expect(screen.getByLabelText('Mes siguiente')).toBeDisabled()
  })

  it('tab Almuerzos → "Mes anterior" navega y vuelve a consultar la API', async () => {
    setupPortal()
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Almuerzos/i }))
    await screen.findByLabelText('Mes anterior')

    await userEvent.click(screen.getByLabelText('Mes anterior'))

    await screen.findByText('Junio 2026')
    expect(vi.mocked(api.get)).toHaveBeenCalledWith(
      '/usuarios/portal/historial-consumos/',
      expect.objectContaining({ params: expect.objectContaining({ hijo_id: 1, anio: 2026, mes: 6 }) }),
    )
  })

  it('tab Historial → muestra "Sin recargas" cuando no hay resultados', async () => {
    setupPortal()
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Historial/i }))

    await screen.findByText(/Sin recargas registradas/i)
  })

  it('tab Historial → llama historial-recargas con el hijo correcto y muestra recargas de cantina y almuerzo', async () => {
    setupPortal({}, {}, {
      count: 2, next: false,
      results: [
        { id: 'cantina-1', tipo: 'CANTINA', fecha: '2026-07-10T10:00:00Z', monto: 50000, estado: 'CONFIRMADA', metodo_pago: 'EFECTIVO' },
        { id: 'almuerzo-1', tipo: 'ALMUERZO', fecha: '2026-07-05T10:00:00Z', monto: 100000, estado: 'CONFIRMADA', metodo_pago: null },
      ],
    })
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Historial/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/usuarios/portal/historial-recargas/',
        expect.objectContaining({ params: expect.objectContaining({ hijo_id: 1, page: 1, page_size: 15 }) }),
      )
    })
    await screen.findByText('Gs. 50.000')
    // "Cantina" también es el nombre del tab, así que puede haber más de un match
    expect(screen.getAllByText('Cantina').length).toBeGreaterThan(0)
    expect(screen.getByText('Almuerzo')).toBeInTheDocument()
    expect(screen.getByText('Gs. 100.000')).toBeInTheDocument()
    // recarga.fecha es DateTimeField (con hora) — parsear con new Date(iso)
    // + 'T00:00:00' (el fix para fecha_consumo) rompería esto con "Invalid Date"
    expect(screen.getByText(/10\/07\/2026/)).toBeInTheDocument()
    expect(screen.queryByText(/Invalid Date/i)).not.toBeInTheDocument()
  })

  it('tab Cantina → muestra la fecha de la compra sin "Invalid Date" (fecha es DateTimeField, con hora y offset)', async () => {
    setupPortal({ hijos: [HIJO_CON_CUENTA] })
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === '/usuarios/portal/mi-hijo/') return Promise.resolve({ data: PORTAL_DATA })
      if (url === '/usuarios/portal/historial-cantina/') {
        return Promise.resolve({
          data: {
            results: [{
              id_venta: 1,
              fecha: '2026-09-23T14:30:00-03:00',
              monto_total: 15000,
              detalles: [{ producto_nombre: 'Sandwich', cantidad: 1, precio_unitario: 15000, subtotal: 15000 }],
            }],
            next: null,
          },
        })
      }
      if (url === '/usuarios/portal/historial-recargas/') return Promise.resolve({ data: { count: 0, next: false, results: [] } })
      if (url === '/usuarios/portal/historial-consumos/') {
        return Promise.resolve({ data: { anio: 2026, mes: 7, consumos: [], saldo_almuerzo: 0, total: 0, monto_total: 0 } })
      }
      return Promise.resolve({ data: {} })
    })
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Cantina/i }))

    // Cantina muestra fecha Y hora (formatDateTime) — la hora ayuda a
    // demostrarle a un padre exactamente cuándo se hizo la compra.
    await screen.findByText(/23\/09\/2026/)
    expect(screen.queryByText(/Invalid Date/i)).not.toBeInTheDocument()
  })

  it('tab Historial → "Ver más" pide la página siguiente', async () => {
    let page = 0
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === '/usuarios/portal/mi-hijo/') return Promise.resolve({ data: PORTAL_DATA })
      if (url === '/usuarios/portal/historial-recargas/') {
        page += 1
        return Promise.resolve({
          data: {
            count: 20, next: page < 2,
            results: [{ id: `cantina-${page}`, tipo: 'CANTINA', fecha: '2026-07-10T10:00:00Z', monto: 50000, estado: 'CONFIRMADA', metodo_pago: null }],
          },
        })
      }
      return Promise.resolve({ data: {} })
    })
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Historial/i }))
    await screen.findByRole('button', { name: /Ver más/i })

    await userEvent.click(screen.getByRole('button', { name: /Ver más/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/usuarios/portal/historial-recargas/',
        expect.objectContaining({ params: expect.objectContaining({ hijo_id: 1, page: 2, page_size: 15 }) }),
      )
    })
  })
})

// ── Banner de 2FA (opcional) ────────────────────────────────────────────────

describe('PortalDashboard — banner de 2FA', () => {
  it('sin 2FA ni huella activos, muestra el banner sugiriendo activarla', async () => {
    mockUser = { nombre: 'María López' }
    setupPortal()
    renderDashboard()
    await screen.findByText('Juan García')

    expect(screen.getByText('Activá el acceso con huella')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Activar' })).toHaveAttribute('href', '/portal/configurar-2fa')
  })

  it('con 2FA por app activo, no muestra el banner', async () => {
    mockUser = { nombre: 'María López', tiene_2fa_activo: true }
    setupPortal()
    renderDashboard()
    await screen.findByText('Juan García')

    expect(screen.queryByText('Activá el acceso con huella')).not.toBeInTheDocument()
  })

  it('con huella activa, no muestra el banner', async () => {
    mockUser = { nombre: 'María López', tiene_webauthn: true }
    setupPortal()
    renderDashboard()
    await screen.findByText('Juan García')

    expect(screen.queryByText('Activá el acceso con huella')).not.toBeInTheDocument()
  })

  it('al cerrar el banner, desaparece y no vuelve a aparecer en un remount', async () => {
    mockUser = { nombre: 'María López' }
    setupPortal()
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByLabelText('Cerrar aviso'))
    expect(screen.queryByText('Activá el acceso con huella')).not.toBeInTheDocument()

    renderDashboard()
    await waitFor(() => {
      expect(screen.queryByText('Activá el acceso con huella')).not.toBeInTheDocument()
    })
  })
})
