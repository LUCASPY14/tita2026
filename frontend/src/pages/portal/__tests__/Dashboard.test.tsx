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
  id: 1,
  nombre: 'Juan García',
  grado: '3° A',
  tarjeta: { nro_tarjeta: 'T-001', saldo_actual: 75_000, estado: 'ACTIVA', en_alerta: false },
  restricciones: [] as { tipo: string; severidad: string; descripcion: string; requiere_autorizacion: boolean }[],
  consumos_mes: {
    total: 0, cobrados: 0,
    ultimos: [] as { fecha_consumo: string; costo_almuerzo: string; ya_cobrado: boolean }[],
  },
  cuenta_mensual: null as {
    id: number; cantidad_almuerzos: number; monto_total: number
    monto_pagado: number; monto_pendiente: number; estado: string
  } | null,
  saldo_almuerzo: 0,
  top_productos: [] as { producto: string; cantidad: number }[],
}

const HIJO_CON_CUENTA = {
  ...HIJO_BASE,
  id: 1,
  consumos_mes: {
    total: 5, cobrados: 3,
    ultimos: [] as { fecha_consumo: string; costo_almuerzo: string; ya_cobrado: boolean }[],
  },
  cuenta_mensual: {
    id: 10, cantidad_almuerzos: 5, monto_total: 100_000,
    monto_pagado: 100_000, monto_pendiente: 0, estado: 'PAGADO',
  } as { id: number; cantidad_almuerzos: number; monto_total: number; monto_pagado: number; monto_pendiente: number; estado: string } | null,
}

const HIJO2 = {
  ...HIJO_BASE,
  id: 2,
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

function setupPortal(override: Record<string, unknown> = {}, historial: Record<string, unknown> = {}) {
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/usuarios/portal/mi-hijo/') return Promise.resolve({ data: { ...PORTAL_DATA, ...override } })
    if (url === '/almuerzos/suscripciones/') return Promise.resolve({ data: { results: [] } })
    if (url === '/usuarios/portal/historial-cantina/') return Promise.resolve({ data: { results: [], next: null } })
    if (url === '/usuarios/portal/historial-consumos/') {
      return Promise.resolve({
        data: { anio: 2026, mes: 7, consumos: [], total: 0, monto_total: 0, cobrados: 0, ...historial },
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

  it('tab Historial → muestra "Sin consumos" cuando total es 0', async () => {
    setupPortal({ hijos: [HIJO_BASE] })
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Historial/i }))

    await screen.findByText(/Sin consumos registrados este mes/i)
  })

  it('tab Historial → llama historial-consumos con el mes actual y muestra los consumos', async () => {
    setupPortal({}, {
      total: 2, cobrados: 1, monto_total: 25000,
      consumos: [{ id: 1, fecha_consumo: '2026-07-15', costo_almuerzo: '25000', ya_cobrado: true }],
    })
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Historial/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/usuarios/portal/historial-consumos/',
        expect.objectContaining({ params: expect.objectContaining({ hijo_id: 1, anio: 2026, mes: 7 }) }),
      )
    })
    await screen.findByLabelText('Mes anterior')
    expect(screen.getAllByText('Gs. 25.000').length).toBeGreaterThan(0)
  })

  it('tab Historial → "Mes siguiente" queda deshabilitado en el mes actual', async () => {
    setupPortal()
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Historial/i }))
    await screen.findByLabelText('Mes siguiente')

    expect(screen.getByLabelText('Mes siguiente')).toBeDisabled()
  })

  it('tab Historial → "Mes anterior" navega y vuelve a consultar la API', async () => {
    setupPortal()
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Historial/i }))
    await screen.findByLabelText('Mes anterior')

    await userEvent.click(screen.getByLabelText('Mes anterior'))

    await screen.findByText('Junio 2026')
    expect(vi.mocked(api.get)).toHaveBeenCalledWith(
      '/usuarios/portal/historial-consumos/',
      expect.objectContaining({ params: expect.objectContaining({ hijo_id: 1, anio: 2026, mes: 6 }) }),
    )
  })

  it('tab Almuerzos → llama /almuerzos/suscripciones/ con el hijo correcto', async () => {
    setupPortal()
    renderDashboard()
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Almuerzos/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/almuerzos/suscripciones/',
        expect.objectContaining({ params: expect.objectContaining({ hijo: 1 }) }),
      )
    })
    await screen.findByText(/Sin plan de almuerzo activo/i)
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
