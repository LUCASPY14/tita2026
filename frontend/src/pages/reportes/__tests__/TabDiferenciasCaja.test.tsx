import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import TabDiferenciasCaja from '../TabDiferenciasCaja'

vi.mock('recharts', () => ({
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ResponsiveContainer: ({ children }: any) => children,
  BarChart: () => null,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
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

const DIFERENCIAS_DATA = {
  resumen: {
    total_diferencia: 25_000,
    n_cierres: 10,
    n_positivos: 2,
    n_negativos: 3,
  },
  por_empleado: [
    {
      empleado_id: 1,
      empleado: 'Carlos López',
      n_cierres: 5,
      diferencia_total: 15_000,
      diferencia_promedio: 3_000,
      mayor_diferencia: 8_000,
    },
  ],
  tendencia: [
    { fecha: '2026-07-10', diferencia: 5_000, empleado: 'Carlos López' },
    { fecha: '2026-07-15', diferencia: 10_000, empleado: 'Carlos López' },
  ],
}

const DIFERENCIAS_SIN_FALTANTE = {
  ...DIFERENCIAS_DATA,
  resumen: { ...DIFERENCIAS_DATA.resumen, n_positivos: 0 },
}

const DIFERENCIAS_SIN_TENDENCIA = {
  ...DIFERENCIAS_DATA,
  tendencia: [],
}

function setupOK(data = DIFERENCIAS_DATA) {
  vi.mocked(api.get).mockImplementation((_url: string, opts?: { params?: Record<string, unknown> }) => {
    if (opts?.params?.formato === 'csv') return Promise.resolve({ data: new Blob(['a,b']) })
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

describe('TabDiferenciasCaja — estado inicial', () => {
  it('muestra EmptyState antes de buscar', () => {
    render(<TabDiferenciasCaja />)
    expect(screen.getByText(/Seleccioná un período y hacé clic en "Buscar"/i)).toBeInTheDocument()
  })

  it('inputs de fecha vienen pre-cargados (primer día del mes y hoy)', () => {
    render(<TabDiferenciasCaja />)
    const inputs = document.querySelectorAll<HTMLInputElement>('input[type="date"]')
    expect(inputs[0].value).toMatch(/^\d{4}-\d{2}-01$/)
    expect(inputs[1].value).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })
})

// ── Validación ────────────────────────────────────────────────────────────────

describe('TabDiferenciasCaja — validación', () => {
  it('fecha vacía → toast.error sin llamar API', async () => {
    render(<TabDiferenciasCaja />)
    const [desdeInput] = document.querySelectorAll<HTMLInputElement>('input[type="date"]')
    fireEvent.change(desdeInput, { target: { value: '' } })

    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Seleccioná ambas fechas')
    expect(vi.mocked(api.get)).not.toHaveBeenCalled()
  })
})

// ── buscarDiferencias ─────────────────────────────────────────────────────────

describe('TabDiferenciasCaja — buscarDiferencias', () => {
  it('llama /contabilidad/reporte-diferencias-caja/ con desde y hasta', async () => {
    setupOK()
    render(<TabDiferenciasCaja />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/contabilidad/reporte-diferencias-caja/',
        expect.objectContaining({ params: expect.objectContaining({ desde: expect.any(String), hasta: expect.any(String) }) }),
      )
    })
  })

  it('muestra alerta naranja cuando hay cierres con faltante (n_positivos > 0)', async () => {
    setupOK()
    render(<TabDiferenciasCaja />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText(/cierre.*faltante/i)
  })

  it('no muestra alerta cuando n_positivos es 0', async () => {
    setupOK(DIFERENCIAS_SIN_FALTANTE)
    render(<TabDiferenciasCaja />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText('Diferencia total')
    expect(screen.queryByText(/faltante — revisá/i)).toBeNull()
  })

  it('muestra KPIs "Diferencia total", "Con faltante", "Con sobrante"', async () => {
    setupOK()
    render(<TabDiferenciasCaja />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText('Diferencia total')
    expect(screen.getByText('Con faltante')).toBeInTheDocument()
    expect(screen.getByText('Con sobrante')).toBeInTheDocument()
  })

  it('tabla por_empleado muestra el nombre del empleado', async () => {
    setupOK()
    render(<TabDiferenciasCaja />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText('Carlos López')
  })

  it('sección "Tendencia cronológica" visible cuando hay datos de tendencia', async () => {
    setupOK()
    render(<TabDiferenciasCaja />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText(/Tendencia cronológica/i)
  })

  it('sin tendencia → sección "Tendencia cronológica" no se renderiza', async () => {
    setupOK(DIFERENCIAS_SIN_TENDENCIA)
    render(<TabDiferenciasCaja />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText('Diferencia total')
    expect(screen.queryByText(/Tendencia cronológica/i)).toBeNull()
  })

  it('API falla → toast.error', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('500'))
    render(<TabDiferenciasCaja />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await waitFor(() =>
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Error al cargar diferencias de caja')
    )
  })
})

// ── Exportación CSV ───────────────────────────────────────────────────────────

describe('TabDiferenciasCaja — exportación CSV', () => {
  it('CSV → llama API con formato=csv y descarga el blob', async () => {
    setupOK()
    render(<TabDiferenciasCaja />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))
    await screen.findByText('Diferencia total')

    await userEvent.click(screen.getByRole('button', { name: /CSV/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/contabilidad/reporte-diferencias-caja/',
        expect.objectContaining({ params: expect.objectContaining({ formato: 'csv' }) }),
      )
    })
    expect(window.URL.createObjectURL).toHaveBeenCalled()
  })
})
