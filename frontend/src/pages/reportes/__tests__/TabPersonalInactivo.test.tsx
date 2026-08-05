import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import TabPersonalInactivo from '../TabPersonalInactivo'

vi.mock('../../../services/api', () => ({
  default: { get: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../services/api'
import toast from 'react-hot-toast'

// ── Fixtures (forma real de ReportePersonalInactivoView) ───────────────────────

const PERSONAL_DATA = {
  resumen: { total_inactivos: 2, promedio_dias_inactivo: 60, max_dias_inactivo: 90, n_dias: 30 },
  por_rol: [
    { rol: 'ADMIN', n: 1 }, { rol: 'SUPERVISOR', n: 1 }, { rol: 'CAJERO', n: 0 },
    { rol: 'COBRADOR', n: 0 }, { rol: 'COCINA', n: 0 },
  ],
  detalle: [
    { usuario_id: 1, nombre: 'Tita Admin', email: 'admin@cantinatita.com', rol: 'ADMIN', ultima_actividad: null, dias_inactivo: 90 },
    { usuario_id: 2, nombre: 'Carlos Super', email: 'super@cantinatita.com', rol: 'SUPERVISOR', ultima_actividad: '2026-06-01T10:00:00Z', dias_inactivo: 30 },
  ],
}

function setupOK(data = PERSONAL_DATA) {
  vi.mocked(api.get).mockResolvedValue({ data })
}

beforeEach(() => vi.clearAllMocks())

describe('TabPersonalInactivo — buscarPersonalInactivo', () => {
  it('muestra los KPIs con valores numéricos reales, no "undefined"', async () => {
    setupOK()
    render(<TabPersonalInactivo />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    expect(await screen.findByText('60d')).toBeInTheDocument()
    expect(screen.getAllByText('90d').length).toBeGreaterThan(0)
    expect(screen.queryByText(/undefined/)).not.toBeInTheDocument()
  })

  it('tabla de detalle muestra días sin actividad por fila', async () => {
    setupOK()
    render(<TabPersonalInactivo />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText('Detalle de personal inactivo')
    expect(screen.getByText('Tita Admin')).toBeInTheDocument()
    expect(screen.getAllByText('90d').length).toBeGreaterThan(0)
    expect(screen.getByText('30d')).toBeInTheDocument()
  })

  it('sin inactivos → mensaje de éxito, sin KPIs undefined', async () => {
    setupOK({
      resumen: { total_inactivos: 0, promedio_dias_inactivo: 0, max_dias_inactivo: 0, n_dias: 30 },
      por_rol: [], detalle: [],
    })
    render(<TabPersonalInactivo />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    expect(await screen.findByText(/Sin personal inactivo/i)).toBeInTheDocument()
  })

  it('API falla → toast.error', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('500'))
    render(<TabPersonalInactivo />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await waitFor(() =>
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Error al cargar personal inactivo')
    )
  })
})
