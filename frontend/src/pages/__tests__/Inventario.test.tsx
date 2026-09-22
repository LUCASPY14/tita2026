import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import Inventario from '../Inventario'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../services/api'

function renderInventario() {
  return render(
    <MemoryRouter>
      <Inventario />
    </MemoryRouter>,
  )
}

const ALERTA_SIN_PREFERIDO = {
  id: 1, producto: 10, producto_nombre: 'Agua mineral', tipo: 'STOCK_MINIMO',
  stock_actual: '2', stock_minimo: '5', activa: true, fecha_generada: '2026-09-21T10:00:00Z',
  proveedor_preferido_id: null, proveedor_preferido_nombre: null, precio_compra_preferido: null,
}

const ALERTA_CON_PREFERIDO = {
  id: 2, producto: 20, producto_nombre: 'Yogur bebible', tipo: 'STOCK_CERO',
  stock_actual: '0', stock_minimo: '10', activa: true, fecha_generada: '2026-09-21T10:00:00Z',
  proveedor_preferido_id: 5, proveedor_preferido_nombre: 'Distribuidora El Sol', precio_compra_preferido: '2500',
}

function mockApi(alertas: object[]) {
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/inventario/alertas-stock/') {
      return Promise.resolve({ data: { results: alertas, count: alertas.length } })
    }
    return Promise.resolve({ data: { results: [], count: 0 } })
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('Inventario — alertas de stock con proveedor sugerido (Bloque 3)', () => {
  it('muestra "Sin proveedor preferido" y enlace de configuración cuando no hay ninguno marcado', async () => {
    mockApi([ALERTA_SIN_PREFERIDO])
    renderInventario()
    await userEvent.click(screen.getByRole('button', { name: /Alertas de Stock/i }))

    await waitFor(() => expect(screen.getByText('Agua mineral')).toBeInTheDocument())
    expect(screen.getByText('Sin proveedor preferido')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: /Configurar proveedor/ }))
    expect(mockNavigate).toHaveBeenCalledWith('/compras?tab=vinculos')
  })

  it('muestra el proveedor preferido y navega a Nueva Compra precargada al hacer clic en "Generar compra"', async () => {
    mockApi([ALERTA_CON_PREFERIDO])
    renderInventario()
    await userEvent.click(screen.getByRole('button', { name: /Alertas de Stock/i }))

    await waitFor(() => expect(screen.getByText('Yogur bebible')).toBeInTheDocument())
    expect(screen.getByText('Distribuidora El Sol')).toBeInTheDocument()
    expect(screen.getByText('2.500 Gs.')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: /Generar compra/ }))
    expect(mockNavigate).toHaveBeenCalledWith('/compras?nueva_compra=1&proveedor=5&producto=20')
  })
})
