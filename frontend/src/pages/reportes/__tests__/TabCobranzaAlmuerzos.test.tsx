import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import TabCobranzaAlmuerzos from '../TabCobranzaAlmuerzos'

vi.mock('recharts', () => ({
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ResponsiveContainer: ({ children }: any) => children,
  BarChart: () => null,
  Bar: () => null,
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

import api from '../../../services/api'
import toast from 'react-hot-toast'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const COBRANZA_DATA = {
  resumen: {
    total_cobrado: 1_500_000,
    total_pendiente: 300_000,
    n_cobros: 45,
    tasa_cobranza: 83,
  },
  por_mes: [
    { mes: 6, facturado: 900_000, cobrado: 750_000, pendiente: 150_000, tasa_cobranza: 83, n_cobros: 22 },
    { mes: 7, facturado: 900_000, cobrado: 750_000, pendiente: 150_000, tasa_cobranza: 83, n_cobros: 23 },
  ],
  por_forma_cobro: [
    { forma_cobro: 'EFECTIVO',      n_cobros: 30, monto: 900_000, porcentaje: 60 },
    { forma_cobro: 'TRANSFERENCIA', n_cobros: 15, monto: 600_000, porcentaje: 40 },
  ],
}

function setupOK(data = COBRANZA_DATA) {
  vi.mocked(api.get).mockImplementation((_url: string, opts?: { params?: Record<string, unknown> }) => {
    if (opts?.params?.formato === 'csv')   return Promise.resolve({ data: new Blob(['a,b']) })
    if (opts?.params?.formato === 'excel') return Promise.resolve({ data: new Blob(['PK...']) })
    return Promise.resolve({ data })
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  window.URL.createObjectURL = vi.fn(() => 'blob:fake')
  window.URL.revokeObjectURL = vi.fn()
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
})

// ── Estado inicial ─────────────────────────────────────────────────────────────

describe('TabCobranzaAlmuerzos — estado inicial', () => {
  it('muestra EmptyState antes de buscar', () => {
    render(<TabCobranzaAlmuerzos />)
    expect(screen.getByText(/Seleccioná un año y hacé clic en "Buscar"/i)).toBeInTheDocument()
  })

  it('select de año tiene el año actual como opción', () => {
    render(<TabCobranzaAlmuerzos />)
    const currentYear = new Date().getFullYear()
    expect(screen.getByRole('combobox')).toHaveValue(String(currentYear))
  })
})

// ── buscarCobranza ────────────────────────────────────────────────────────────

describe('TabCobranzaAlmuerzos — buscarCobranza', () => {
  it('llama /almuerzos/reporte-cobranza/ con el año seleccionado', async () => {
    setupOK()
    render(<TabCobranzaAlmuerzos />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/almuerzos/reporte-cobranza/',
        expect.objectContaining({ params: expect.objectContaining({ anio: expect.any(Number) }) }),
      )
    })
  })

  it('muestra KPIs "Total cobrado" y "Cobros" tras la búsqueda', async () => {
    setupOK()
    render(<TabCobranzaAlmuerzos />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText('Total cobrado')
    // "Cobros" aparece solo en la KPI card (tabla tiene "N° Cobros")
    expect(screen.getByText('Cobros')).toBeInTheDocument()
  })

  it('tabla por mes muestra abreviaciones (Jun, Jul)', async () => {
    setupOK()
    render(<TabCobranzaAlmuerzos />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText('Total cobrado')
    expect(screen.getByText('Jun')).toBeInTheDocument()
    expect(screen.getByText('Jul')).toBeInTheDocument()
  })

  it('tabla por_forma_cobro muestra etiquetas localizadas (EFECTIVO→Efectivo, TRANSFERENCIA→Transferencia)', async () => {
    setupOK()
    render(<TabCobranzaAlmuerzos />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText('Total cobrado')
    expect(screen.getByText('Efectivo')).toBeInTheDocument()
    expect(screen.getByText('Transferencia')).toBeInTheDocument()
  })

  it('API falla → toast.error', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('500'))
    render(<TabCobranzaAlmuerzos />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await waitFor(() =>
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Error al cargar reporte de cobranza')
    )
  })
})

// ── Exportaciones ─────────────────────────────────────────────────────────────

describe('TabCobranzaAlmuerzos — exportaciones', () => {
  async function cargarReporte() {
    setupOK()
    render(<TabCobranzaAlmuerzos />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))
    await screen.findByText('Total cobrado')
  }

  it('CSV → llama API con formato=csv y descarga el blob', async () => {
    await cargarReporte()
    await userEvent.click(screen.getByRole('button', { name: /CSV/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/almuerzos/reporte-cobranza/',
        expect.objectContaining({ params: expect.objectContaining({ formato: 'csv' }) }),
      )
    })
    expect(window.URL.createObjectURL).toHaveBeenCalled()
  })

  it('Excel → llama API con formato=excel y descarga el blob', async () => {
    await cargarReporte()
    await userEvent.click(screen.getByRole('button', { name: /Excel/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/almuerzos/reporte-cobranza/',
        expect.objectContaining({ params: expect.objectContaining({ formato: 'excel' }) }),
      )
    })
    expect(window.URL.createObjectURL).toHaveBeenCalled()
  })
})
