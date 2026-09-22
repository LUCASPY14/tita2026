import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import Compras from '../Compras'

vi.mock('../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

const mockGetProductos = vi.fn()
const mockGetMediosPago = vi.fn()
const storeState = { getProductos: mockGetProductos, getMediosPago: mockGetMediosPago }
vi.mock('../../store/catalogoStore', () => ({
  useCatalogoStore: (selector?: (s: typeof storeState) => unknown) => (selector ? selector(storeState) : storeState),
}))

vi.mock('../../store/authStore', () => ({
  useAuthStore: () => ({ user: { rol: 'ADMIN' } }),
}))

import api from '../../services/api'

const PROVEEDOR = { id_proveedor: 1, razon_social: 'Distribuidora El Sol', ruc: '1', activo: true, saldo_cuenta_corriente: 0 }
const PRODUCTO = { id_producto: 10, descripcion: 'Agua mineral', precio_actual: 5000 }

function renderCompras(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Compras />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  mockGetProductos.mockResolvedValue([PRODUCTO])
  mockGetMediosPago.mockResolvedValue([])
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/compras/proveedores/') return Promise.resolve({ data: { results: [PROVEEDOR] } })
    if (url === '/compras/productos-proveedor/') {
      return Promise.resolve({
        data: { results: [{ id_producto_proveedor: 1, proveedor: 1, proveedor_nombre: 'Distribuidora El Sol', producto: 10, producto_nombre: 'Agua mineral', precio_compra: 4200, fecha_ultima_compra: null, preferido: true }] },
      })
    }
    return Promise.resolve({ data: { results: [], count: 0 } })
  })
})

describe('Compras — deep-link "Generar compra" desde alerta de stock bajo (Bloque 3)', () => {
  it('abre Nueva Compra con proveedor y producto precargados desde ?nueva_compra=1', async () => {
    renderCompras('/compras?nueva_compra=1&proveedor=1&producto=10')

    expect(await screen.findByRole('dialog')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByPlaceholderText('Buscar proveedor...')).toHaveValue('Distribuidora El Sol'))
    await waitFor(() => expect(screen.getByPlaceholderText('Costo')).toHaveValue(4200))
  })

  it('sin el query param no abre ningún modal', async () => {
    renderCompras('/compras')

    await waitFor(() => expect(mockGetProductos).toHaveBeenCalled())
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('?tab=vinculos abre directamente el tab Productos x Proveedor', async () => {
    renderCompras('/compras?tab=vinculos')

    expect(await screen.findByText('Nuevo Vínculo')).toBeInTheDocument()
  })
})
