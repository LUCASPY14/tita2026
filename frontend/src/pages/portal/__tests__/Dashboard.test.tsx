import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import PortalDashboard from '../Dashboard'

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: vi.fn(() => vi.fn()) }
})

vi.mock('../../../store/authStore', () => {
  const stableUser = { nombre: 'María López' }
  return { useAuthStore: () => ({ user: stableUser }) }
})

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
  cliente: { id: 99, nombre: 'María López', email: 'maria@test.com', pin_es_defecto: false },
  mes: { anio: 2026, mes: 7 },
  hijos: [HIJO_CON_CUENTA],
}

function setupPortal(override: Record<string, unknown> = {}) {
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/usuarios/portal/mi-hijo/') return Promise.resolve({ data: { ...PORTAL_DATA, ...override } })
    if (url === '/almuerzos/suscripciones/') return Promise.resolve({ data: { results: [] } })
    if (url === '/usuarios/portal/historial-cantina/') return Promise.resolve({ data: { results: [], next: null } })
    return Promise.resolve({ data: {} })
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

// ── Loading y error ───────────────────────────────────────────────────────────

describe('PortalDashboard — loading y error', () => {
  it('muestra Spinner mientras la API no responde', () => {
    vi.mocked(api.get).mockReturnValue(new Promise(() => {}))
    render(<PortalDashboard />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('error de red → muestra "No se pudieron cargar los datos"', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('network'))
    render(<PortalDashboard />)

    await screen.findByText(/No se pudieron cargar los datos/i)
    expect(vi.mocked(toast.error)).toHaveBeenCalled()
  })

  it('click "Reintentar" vuelve a llamar la API', async () => {
    vi.mocked(api.get)
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValue({ data: PORTAL_DATA })

    render(<PortalDashboard />)
    await screen.findByText(/No se pudieron cargar/i)

    await userEvent.click(screen.getByRole('button', { name: /Reintentar/i }))

    await screen.findByText('Hola, María López')
  })
})

// ── Estados vacíos y datos ────────────────────────────────────────────────────

describe('PortalDashboard — datos', () => {
  it('sin hijos → "Sin hijos asociados"', async () => {
    setupPortal({ hijos: [] })
    render(<PortalDashboard />)

    await screen.findByText(/Sin hijos asociados/i)
  })

  it('muestra saludo con nombre del usuario', async () => {
    setupPortal()
    render(<PortalDashboard />)

    await screen.findByText('Hola, María López')
  })

  it('múltiples hijos → muestra selector con el nombre de cada hijo', async () => {
    setupPortal({ hijos: [HIJO_CON_CUENTA, HIJO2] })
    render(<PortalDashboard />)

    // Esperar al botón del selector (no al texto del card header, que también dice "Juan García")
    await screen.findByRole('button', { name: 'Juan García' })
    expect(screen.getByRole('button', { name: 'Lucía García' })).toBeInTheDocument()
  })

  it('click en hijo secundario lo selecciona como activo', async () => {
    setupPortal({ hijos: [HIJO_CON_CUENTA, HIJO2] })
    render(<PortalDashboard />)
    await screen.findByRole('button', { name: 'Juan García' })

    await userEvent.click(screen.getByRole('button', { name: 'Lucía García' }))

    // El grado de Lucía aparece en el header del card activo
    await screen.findByText('5° B')
  })
})

// ── Tabs ──────────────────────────────────────────────────────────────────────

describe('PortalDashboard — tabs', () => {
  it('tab Resumen (por defecto) muestra nro de tarjeta del hijo', async () => {
    setupPortal()
    render(<PortalDashboard />)

    await screen.findByText('T-001')
    expect(screen.getByText('Tarjeta escolar')).toBeInTheDocument()
  })

  it('tab Historial → muestra "Sin consumos" cuando total es 0', async () => {
    setupPortal({ hijos: [HIJO_BASE] })
    render(<PortalDashboard />)
    await screen.findByText('Juan García')

    await userEvent.click(screen.getByRole('tab', { name: /Historial/i }))

    await screen.findByText(/Sin consumos registrados este mes/i)
  })

  it('tab Almuerzos → llama /almuerzos/suscripciones/ con el hijo correcto', async () => {
    setupPortal()
    render(<PortalDashboard />)
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
