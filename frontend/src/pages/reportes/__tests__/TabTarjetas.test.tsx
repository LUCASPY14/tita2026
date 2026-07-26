import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import TabTarjetas from '../TabTarjetas'

vi.mock('../../../services/api', () => ({
  default: { get: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../services/api'
import toast from 'react-hot-toast'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const TARJETA_JUAN = {
  nro_tarjeta: 'T-001', alumno: 'Juan García', grado: '3° A',
  saldo_actual: 75_000, total_recargado: 200_000, total_consumido: 125_000,
  num_recargas: 4, num_consumos: 30,
}

const TARJETA_ANA = {
  nro_tarjeta: 'T-002', alumno: 'Ana Pérez', grado: '5° B',
  saldo_actual: 10_000, total_recargado: 100_000, total_consumido: 90_000,
  num_recargas: 2, num_consumos: 20,
}

const RESUMEN = {
  total_tarjetas: 2, saldo_total: 85_000,
  total_recargado: 300_000, total_consumido: 215_000,
}

const TARJETAS_DATA = {
  periodo: { desde: null, hasta: null },
  resumen: RESUMEN,
  tarjetas: [TARJETA_JUAN, TARJETA_ANA],
}

function setupOK(data = TARJETAS_DATA) {
  vi.mocked(api.get).mockImplementation((_url: string, opts?: { params?: Record<string, string> }) => {
    if (opts?.params?.formato === 'csv') return Promise.resolve({ data: new Blob(['a,b']) })
    if (opts?.params?.formato === 'pdf') return Promise.resolve({ data: new Blob(['%PDF']) })
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

describe('TabTarjetas — estado inicial', () => {
  it('muestra EmptyState antes de cargar', () => {
    render(<TabTarjetas />)
    expect(screen.getByText(/Hacé clic en "Generar Reporte"/i)).toBeInTheDocument()
  })

  it('muestra hint "Sin período" cuando no hay fechas ni datos', () => {
    render(<TabTarjetas />)
    expect(screen.getByText(/Sin período/i)).toBeInTheDocument()
  })
})

// ── cargarTarjetas ────────────────────────────────────────────────────────────

describe('TabTarjetas — cargarTarjetas', () => {
  it('llama /core/reporte-tarjetas/ sin parámetros cuando no hay fechas', async () => {
    setupOK()
    render(<TabTarjetas />)
    await userEvent.click(screen.getByRole('button', { name: /Generar Reporte/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/core/reporte-tarjetas/',
        expect.objectContaining({ params: {} }),
      )
    })
  })

  it('incluye desde y hasta cuando se ingresan fechas', async () => {
    setupOK()
    render(<TabTarjetas />)
    const [desdeInput, hastaInput] = document.querySelectorAll<HTMLInputElement>('input[type="date"]')
    fireEvent.change(desdeInput, { target: { value: '2026-07-01' } })
    fireEvent.change(hastaInput, { target: { value: '2026-07-24' } })

    await userEvent.click(screen.getByRole('button', { name: /Generar Reporte/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/core/reporte-tarjetas/',
        expect.objectContaining({ params: { desde: '2026-07-01', hasta: '2026-07-24' } }),
      )
    })
  })

  it('muestra KPI "Tarjetas activas" y la cantidad en el encabezado de tabla', async () => {
    setupOK()
    render(<TabTarjetas />)
    await userEvent.click(screen.getByRole('button', { name: /Generar Reporte/i }))

    await screen.findByText('Tarjetas activas')
    // El encabezado de la tabla muestra el total entre paréntesis
    expect(screen.getByText(/Tarjetas \(2\)/)).toBeInTheDocument()
  })

  it('renderiza los alumnos en la tabla', async () => {
    setupOK()
    render(<TabTarjetas />)
    await userEvent.click(screen.getByRole('button', { name: /Generar Reporte/i }))

    await screen.findByText('Juan García')
    expect(screen.getByText('Ana Pérez')).toBeInTheDocument()
  })

  it('API falla → toast.error', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('network'))
    render(<TabTarjetas />)
    await userEvent.click(screen.getByRole('button', { name: /Generar Reporte/i }))

    await waitFor(() => expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Error al cargar tarjetas'))
  })
})

// ── Filtro cliente ────────────────────────────────────────────────────────────

describe('TabTarjetas — filtro alumno/grado', () => {
  async function cargarYBuscar() {
    setupOK()
    render(<TabTarjetas />)
    await userEvent.click(screen.getByRole('button', { name: /Generar Reporte/i }))
    await screen.findByText('Juan García')
  }

  it('filtrar por alumno oculta las filas que no coinciden', async () => {
    await cargarYBuscar()
    const filtro = screen.getByPlaceholderText('Filtrar alumno/grado...')
    await userEvent.type(filtro, 'Juan')

    expect(screen.getByText('Juan García')).toBeInTheDocument()
    expect(screen.queryByText('Ana Pérez')).toBeNull()
  })

  it('filtrar por grado oculta los alumnos de otros grados', async () => {
    await cargarYBuscar()
    const filtro = screen.getByPlaceholderText('Filtrar alumno/grado...')
    await userEvent.type(filtro, '5°')

    expect(screen.getByText('Ana Pérez')).toBeInTheDocument()
    expect(screen.queryByText('Juan García')).toBeNull()
  })
})

// ── Exportaciones ─────────────────────────────────────────────────────────────

describe('TabTarjetas — exportaciones', () => {
  async function cargarYBuscar() {
    setupOK()
    render(<TabTarjetas />)
    await userEvent.click(screen.getByRole('button', { name: /Generar Reporte/i }))
    await screen.findByText('Juan García')
  }

  it('CSV → llama API con formato=csv y descarga el blob', async () => {
    await cargarYBuscar()
    await userEvent.click(screen.getByRole('button', { name: /^CSV$/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/core/reporte-tarjetas/',
        expect.objectContaining({ params: expect.objectContaining({ formato: 'csv' }) }),
      )
    })
    expect(window.URL.createObjectURL).toHaveBeenCalled()
  })

  it('PDF → llama API con formato=pdf y descarga el blob', async () => {
    await cargarYBuscar()
    await userEvent.click(screen.getByRole('button', { name: /^PDF$/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/core/reporte-tarjetas/',
        expect.objectContaining({ params: expect.objectContaining({ formato: 'pdf' }) }),
      )
    })
    expect(window.URL.createObjectURL).toHaveBeenCalled()
  })
})
