import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import TabConsumoGrado from '../TabConsumoGrado'

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

const CONSUMO_DATA = {
  periodo: { desde: '2026-07-01', hasta: '2026-07-24' },
  resumen: { total_consumos: 180, total_rechazados: 4, tasa_rechazo_global: 2 },
  por_grado: [
    { grado: '3° A', nivel: 3, n_consumos: 60, n_rechazados: 1, n_anulados: 0, tasa_rechazo: 1.7, monto_total: 600_000 },
    { grado: '5° B', nivel: 5, n_consumos: 120, n_rechazados: 3, n_anulados: 1, tasa_rechazo: 2.5, monto_total: 1_200_000 },
  ],
  horarios_pico: [
    { hora: 10, n: 90 },
    { hora: 11, n: 80 },
    { hora: 12, n: 10 },
  ],
}

const CONSUMO_SIN_HORARIOS = {
  ...CONSUMO_DATA,
  horarios_pico: [],
}

beforeEach(() => {
  vi.clearAllMocks()
  window.URL.createObjectURL = vi.fn(() => 'blob:fake')
  window.URL.revokeObjectURL = vi.fn()
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
})

// ── Estado inicial ─────────────────────────────────────────────────────────────

describe('TabConsumoGrado — estado inicial', () => {
  it('muestra EmptyState antes de buscar', () => {
    render(<TabConsumoGrado />)
    expect(screen.getByText(/Seleccioná un período/i)).toBeInTheDocument()
  })

  it('inputs de fecha vienen pre-cargados (primer día del mes y hoy)', () => {
    render(<TabConsumoGrado />)
    const inputs = document.querySelectorAll<HTMLInputElement>('input[type="date"]')
    expect(inputs[0].value).toMatch(/^\d{4}-\d{2}-01$/)
    expect(inputs[1].value).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })
})

// ── Validación ────────────────────────────────────────────────────────────────

describe('TabConsumoGrado — validación', () => {
  it('fecha desde vacía → toast.error sin llamar API', async () => {
    render(<TabConsumoGrado />)
    const [desdeInput] = document.querySelectorAll<HTMLInputElement>('input[type="date"]')
    fireEvent.change(desdeInput, { target: { value: '' } })

    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Seleccioná ambas fechas')
    expect(vi.mocked(api.get)).not.toHaveBeenCalled()
  })
})

// ── Reporte exitoso ────────────────────────────────────────────────────────────

describe('TabConsumoGrado — buscar OK', () => {
  function setup(data = CONSUMO_DATA) {
    vi.mocked(api.get).mockImplementation((_url: string, opts?: { params?: Record<string, string> }) => {
      if (opts?.params?.formato === 'csv') return Promise.resolve({ data: new Blob(['a,b']) })
      return Promise.resolve({ data })
    })
  }

  it('llama /almuerzos/reporte-consumo-grado/ con desde y hasta', async () => {
    setup()
    render(<TabConsumoGrado />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/almuerzos/reporte-consumo-grado/',
        expect.objectContaining({ params: expect.objectContaining({ desde: expect.any(String), hasta: expect.any(String) }) }),
      )
    })
  })

  it('muestra KPI "Total consumos"', async () => {
    setup()
    render(<TabConsumoGrado />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText('Total consumos')
    expect(screen.getByText('180')).toBeInTheDocument()
  })

  it('muestra KPI "Rechazados" con su valor', async () => {
    setup()
    render(<TabConsumoGrado />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText('Total consumos')
    expect(screen.getByText('4')).toBeInTheDocument()
  })

  it('muestra KPI "Tasa de rechazo" con símbolo %', async () => {
    setup()
    render(<TabConsumoGrado />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText('Tasa de rechazo')
    expect(screen.getByText('2%')).toBeInTheDocument()
  })

  it('tabla detalle por grado muestra los grados cargados', async () => {
    setup()
    render(<TabConsumoGrado />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText('3° A')
    expect(screen.getByText('5° B')).toBeInTheDocument()
  })

  it('sección "Distribución horaria" visible cuando hay horarios pico', async () => {
    setup()
    render(<TabConsumoGrado />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText(/Distribución horaria/i)
  })

  it('sin horarios pico → sección "Distribución horaria" no se renderiza', async () => {
    setup(CONSUMO_SIN_HORARIOS)
    render(<TabConsumoGrado />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText('Total consumos')
    expect(screen.queryByText(/Distribución horaria/i)).toBeNull()
  })

  it('API falla → toast.error', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('500'))
    render(<TabConsumoGrado />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await waitFor(() => expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Error al cargar consumo por grado'))
  })
})

// ── Exportación CSV ───────────────────────────────────────────────────────────

describe('TabConsumoGrado — exportación CSV', () => {
  it('llama API con formato=csv y descarga el blob', async () => {
    vi.mocked(api.get).mockImplementation((_url: string, opts?: { params?: Record<string, string> }) => {
      if (opts?.params?.formato === 'csv') return Promise.resolve({ data: new Blob(['a,b']) })
      return Promise.resolve({ data: CONSUMO_DATA })
    })
    render(<TabConsumoGrado />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))
    await screen.findByText('Total consumos')

    await userEvent.click(screen.getByRole('button', { name: /CSV/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/almuerzos/reporte-consumo-grado/',
        expect.objectContaining({ params: expect.objectContaining({ formato: 'csv' }) }),
      )
    })
    expect(window.URL.createObjectURL).toHaveBeenCalled()
  })
})
