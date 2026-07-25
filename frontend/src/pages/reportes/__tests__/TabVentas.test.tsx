import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import TabVentas from '../TabVentas'

vi.mock('recharts', () => ({
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ResponsiveContainer: ({ children }: any) => children,
  AreaChart: () => null,
  Area: () => null,
  BarChart: () => null,
  Bar: () => null,
  PieChart: () => null,
  Pie: () => null,
  Cell: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
}))

vi.mock('../../../services/api', () => ({
  default: { get: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

vi.mock('../../../utils/pdf', () => ({
  exportarReporteVentasPDF: vi.fn(),
}))

import api from '../../../services/api'
import toast from 'react-hot-toast'
import { exportarReporteVentasPDF } from '../../../utils/pdf'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const REPORTE = {
  periodo: { desde: '2026-07-01', hasta: '2026-07-24' },
  ventas: {
    cantidad: 42,
    monto_total: 1_500_000,
    por_tipo: [
      { tipo: 'VENTA_TARJETA', cantidad: 30, monto: 1_000_000 },
      { tipo: 'VENTA_EFECTIVO', cantidad: 12, monto: 500_000 },
    ],
  },
  cierres_caja: [
    {
      id: 1, caja: 'Caja Principal',
      fecha_apertura: '2026-07-24T08:00:00Z',
      fecha_cierre: '2026-07-24T16:00:00Z',
      monto_inicial: 500_000, monto_contado_fisico: 498_000, diferencia: -2_000,
    },
  ],
}

const TENDENCIA = {
  data: [
    { fecha: '2026-07-23', cantidad: 5, monto: 100_000 },
    { fecha: '2026-07-24', cantidad: 7, monto: 150_000 },
  ],
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function setupOK(reporte = REPORTE as any) {
  vi.mocked(api.get).mockImplementation((url: string, opts?: { params?: Record<string, string> }) => {
    if (opts?.params?.formato === 'csv') return Promise.resolve({ data: new Blob(['a,b']) })
    if (url.includes('tendencia')) return Promise.resolve({ data: TENDENCIA })
    return Promise.resolve({ data: reporte })
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  window.URL.createObjectURL = vi.fn(() => 'blob:fake')
  window.URL.revokeObjectURL = vi.fn()
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
})

// ── Estado inicial ─────────────────────────────────────────────────────────────

describe('TabVentas — estado inicial', () => {
  it('muestra EmptyState antes de buscar', () => {
    render(<TabVentas />)
    expect(screen.getByText(/Seleccioná un período/i)).toBeInTheDocument()
  })

  it('botones CSV y PDF no visibles antes de buscar', () => {
    render(<TabVentas />)
    expect(screen.queryByRole('button', { name: /^CSV$/i })).toBeNull()
    expect(screen.queryByRole('button', { name: /^PDF$/i })).toBeNull()
  })
})

// ── Validación de fechas ───────────────────────────────────────────────────────

describe('TabVentas — validación de fechas', () => {
  it('desde > hasta → toast.error y no llama la API', async () => {
    render(<TabVentas />)
    const [desdeInput] = document.querySelectorAll<HTMLInputElement>('input[type="date"]')
    fireEvent.change(desdeInput, { target: { value: '2099-12-31' } })

    await userEvent.click(screen.getByRole('button', { name: /Generar Reporte/i }))

    expect(vi.mocked(toast.error)).toHaveBeenCalledWith('La fecha Desde no puede ser mayor a Hasta')
    expect(vi.mocked(api.get)).not.toHaveBeenCalled()
  })
})

// ── Reporte exitoso ────────────────────────────────────────────────────────────

describe('TabVentas — buscar OK', () => {
  it('llama /contabilidad/reportes/ y /dashboard/tendencia/ en paralelo', async () => {
    setupOK()
    render(<TabVentas />)
    await userEvent.click(screen.getByRole('button', { name: /Generar Reporte/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/contabilidad/reportes/',
        expect.objectContaining({ params: expect.objectContaining({ fecha_desde: expect.any(String) }) }),
      )
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/contabilidad/dashboard/tendencia/',
        expect.any(Object),
      )
    })
  })

  it('muestra KPI "Total Vendido" con el período cargado', async () => {
    setupOK()
    render(<TabVentas />)
    await userEvent.click(screen.getByRole('button', { name: /Generar Reporte/i }))

    await screen.findByText('Total Vendido')
  })

  it('muestra cantidad de ventas del reporte', async () => {
    setupOK()
    render(<TabVentas />)
    await userEvent.click(screen.getByRole('button', { name: /Generar Reporte/i }))

    await screen.findByText('42')
  })

  it('tabla de por_tipo muestra etiquetas localizadas', async () => {
    setupOK()
    render(<TabVentas />)
    await userEvent.click(screen.getByRole('button', { name: /Generar Reporte/i }))

    await screen.findByText('Tarjeta prepago')
    expect(screen.getByText('Efectivo')).toBeInTheDocument()
  })

  it('tabla de cierres muestra nombre de caja', async () => {
    setupOK()
    render(<TabVentas />)
    await userEvent.click(screen.getByRole('button', { name: /Generar Reporte/i }))

    await screen.findByText('Caja Principal')
  })

  it('sin cierres de caja → mensaje "No hay cierres en este período"', async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes('tendencia')) return Promise.resolve({ data: { data: [] } })
      return Promise.resolve({ data: { ...REPORTE, cierres_caja: [] } })
    })
    render(<TabVentas />)
    await userEvent.click(screen.getByRole('button', { name: /Generar Reporte/i }))

    await screen.findByText(/No hay cierres en este período/i)
  })

  it('API falla → toast.error y EmptyState permanece', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('500'))
    render(<TabVentas />)
    await userEvent.click(screen.getByRole('button', { name: /Generar Reporte/i }))

    await waitFor(() => expect(vi.mocked(toast.error)).toHaveBeenCalled())
    expect(screen.getByText(/Seleccioná un período/i)).toBeInTheDocument()
  })
})

// ── Exportaciones ─────────────────────────────────────────────────────────────

describe('TabVentas — exportaciones', () => {
  async function cargarReporte() {
    setupOK()
    render(<TabVentas />)
    await userEvent.click(screen.getByRole('button', { name: /Generar Reporte/i }))
    await screen.findByText(/Total Vendido/i)
  }

  it('CSV → llama API con formato=csv y descarga el blob', async () => {
    await cargarReporte()
    await userEvent.click(screen.getByRole('button', { name: /^CSV$/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/contabilidad/reportes/',
        expect.objectContaining({ params: expect.objectContaining({ formato: 'csv' }) }),
      )
    })
    expect(window.URL.createObjectURL).toHaveBeenCalled()
  })

  it('PDF → llama exportarReporteVentasPDF con los datos y fechas', async () => {
    await cargarReporte()
    await userEvent.click(screen.getByRole('button', { name: /^PDF$/i }))

    expect(vi.mocked(exportarReporteVentasPDF)).toHaveBeenCalledWith(
      REPORTE,
      expect.any(String),
      expect.any(String),
    )
  })
})
