import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import TabAuditoria from '../TabAuditoria'

vi.mock('../../../services/api', () => ({
  default: { get: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../services/api'
import toast from 'react-hot-toast'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const OPCIONES = {
  operaciones: ['CREAR_USUARIO', 'LOGIN'],
  resultados: ['EXITO', 'FALLA'],
}

const AUDITORIA_DATA = {
  resumen: { total_eventos: 3, por_resultado: { EXITO: 2, FALLA: 1 } },
  top_operaciones: [{ operacion: 'LOGIN', n: 2 }, { operacion: 'CREAR_USUARIO', n: 1 }],
  top_tablas: [{ tabla: 'usuarios_usuario', n: 3 }],
  detalle: [
    { fecha: '2026-08-01T10:00:00Z', usuario: 'admin@tita.local', operacion: 'LOGIN', tabla: 'usuarios_usuario', objeto_id: 1, resultado: 'EXITO', ip: '127.0.0.1', descripcion: null, mensaje_error: null },
    { fecha: '2026-08-01T09:00:00Z', usuario: null, operacion: 'CREAR_USUARIO', tabla: 'usuarios_usuario', objeto_id: 2, resultado: 'FALLA', ip: null, descripcion: null, mensaje_error: 'error de validación' },
  ],
}

function setupOK(data = AUDITORIA_DATA) {
  vi.mocked(api.get).mockImplementation((url: string, opts?: { params?: Record<string, unknown> }) => {
    if (url.endsWith('/opciones/')) return Promise.resolve({ data: OPCIONES })
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

// ── Opciones dinámicas ───────────────────────────────────────────────────────

describe('TabAuditoria — opciones dinámicas', () => {
  it('carga /reporte-auditoria/opciones/ al montar', async () => {
    setupOK()
    render(<TabAuditoria />)
    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith('/usuarios/reporte-auditoria/opciones/')
    })
  })

  it('el select de Operación se puebla con los valores reales, no una lista fija', async () => {
    setupOK()
    render(<TabAuditoria />)
    await screen.findByText('CREAR_USUARIO')
    expect(screen.getByText('LOGIN')).toBeInTheDocument()
    // Los valores viejos hardcodeados (nunca reales) no deben aparecer
    expect(screen.queryByText('ACCESS')).not.toBeInTheDocument()
  })

  it('si falla la carga de opciones, el filtro queda vacío sin romper la página', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('500'))
    render(<TabAuditoria />)
    expect(await screen.findByText('Seleccioná un período y hacé clic en "Buscar"')).toBeInTheDocument()
  })
})

// ── buscarAuditoria ───────────────────────────────────────────────────────────

describe('TabAuditoria — buscarAuditoria', () => {
  it('muestra KPIs de Éxito/Fallas con los valores reales del backend', async () => {
    setupOK()
    render(<TabAuditoria />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText('Total eventos')
    expect(screen.getByText('Fallas')).toBeInTheDocument()
  })

  it('tabla de detalle muestra las operaciones reales', async () => {
    setupOK()
    render(<TabAuditoria />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await screen.findByText('Detalle de eventos')
    expect(screen.getAllByText('LOGIN').length).toBeGreaterThan(0)
  })

  it('API falla → toast.error', async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.endsWith('/opciones/')) return Promise.resolve({ data: OPCIONES })
      return Promise.reject(new Error('500'))
    })
    render(<TabAuditoria />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))

    await waitFor(() =>
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Error al cargar reporte de auditoría')
    )
  })
})

// ── Exportación CSV ───────────────────────────────────────────────────────────

describe('TabAuditoria — exportación CSV', () => {
  it('CSV → llama API con formato=csv y descarga el blob', async () => {
    setupOK()
    render(<TabAuditoria />)
    await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))
    await screen.findByText('Total eventos')

    await userEvent.click(screen.getByRole('button', { name: /CSV/i }))

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/usuarios/reporte-auditoria/',
        expect.objectContaining({ params: expect.objectContaining({ formato: 'csv' }) }),
      )
    })
    expect(window.URL.createObjectURL).toHaveBeenCalled()
  })
})
