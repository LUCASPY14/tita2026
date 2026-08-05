import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import TabAlmuerzos from '../TabAlmuerzos'

vi.mock('recharts', () => ({
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ResponsiveContainer: ({ children }: any) => children,
  PieChart: () => null,
  Pie: () => null,
  Cell: () => null,
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

// ── Fixtures ──────────────────────────────────────────────────────────────────

const GRADOS = [
  { id: 1, nombre: '1° Grado A', activo: true },
  { id: 2, nombre: '1° Grado B', activo: true },
  { id: 3, nombre: 'Inactivo', activo: false },
]

const ALMUERZOS_DATA = {
  periodo: { anio: 2026, mes: 8 },
  totales: { alumnos: 1, cantidad_almuerzos: 10, monto_total: 150000, monto_pagado: 150000, monto_pendiente: 0, con_deuda: 0 },
  filas: [
    { hijo_id: 1, hijo: 'Agustín Benítez', grado: '1° Grado A', nro_tarjeta: 'T-01001', cantidad_almuerzos: 10, monto_total: 150000, monto_pagado: 150000, monto_pendiente: 0, estado: 'PAGADO' },
  ],
}

function setupOK() {
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/clientes/grados/') return Promise.resolve({ data: { results: GRADOS } })
    return Promise.resolve({ data: ALMUERZOS_DATA })
  })
}

beforeEach(() => vi.clearAllMocks())

describe('TabAlmuerzos — selector de grado', () => {
  it('carga /clientes/grados/ al montar y puebla el select con los grados activos', async () => {
    setupOK()
    render(<TabAlmuerzos />)

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith('/clientes/grados/', { params: { page_size: 100 } })
    })
    expect(await screen.findByText('1° Grado A')).toBeInTheDocument()
    expect(screen.getByText('1° Grado B')).toBeInTheDocument()
    // Grados inactivos no deben aparecer en el filtro
    expect(screen.queryByText('Inactivo')).not.toBeInTheDocument()
  })

  it('si falla la carga de grados, el filtro queda en "Todos" sin romper la página', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('500'))
    render(<TabAlmuerzos />)
    expect(await screen.findByText('Todos')).toBeInTheDocument()
  })

  it('seleccionar un grado y buscar envía el filtro al backend', async () => {
    setupOK()
    render(<TabAlmuerzos />)
    await screen.findByText('1° Grado A')

    await userEvent.selectOptions(screen.getByDisplayValue('Todos'), '1° Grado A')
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/almuerzos/reportes/',
        expect.objectContaining({ params: expect.objectContaining({ grado: '1° Grado A' }) }),
      )
    })
  })
})
