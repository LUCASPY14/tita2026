import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import TabProductosProveedor from '../TabProductosProveedor'

vi.mock('../../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../services/api'

const PROVEEDOR = { id_proveedor: 1, razon_social: 'Distribuidora El Sol', ruc: '1', telefono: null, email: null, direccion: null, ciudad: null, ciudad_nombre: null, activo: true, saldo_cuenta_corriente: 0 }
const PRODUCTO_MARGEN_ALTO = { id_producto: 10, descripcion: 'Agua mineral', precio_actual: 5000, codigo_barra: null, codigo: null }
const PRODUCTO_PERDIDA = { id_producto: 11, descripcion: 'Yogur bebible', precio_actual: 2000, codigo_barra: null, codigo: null }
const PRODUCTO_SIN_VENTA = { id_producto: 12, descripcion: 'Producto sin lista', precio_actual: 0, codigo_barra: null, codigo: null }

function mockVinculos() {
  vi.mocked(api.get).mockResolvedValue({
    data: {
      results: [
        { id_producto_proveedor: 1, proveedor: 1, proveedor_nombre: 'Distribuidora El Sol', producto: 10, producto_nombre: 'Agua mineral', precio_compra: 3000, fecha_ultima_compra: null },
        { id_producto_proveedor: 2, proveedor: 1, proveedor_nombre: 'Distribuidora El Sol', producto: 11, producto_nombre: 'Yogur bebible', precio_compra: 2500, fecha_ultima_compra: null },
        { id_producto_proveedor: 3, proveedor: 1, proveedor_nombre: 'Distribuidora El Sol', producto: 12, producto_nombre: 'Producto sin lista', precio_compra: 1000, fecha_ultima_compra: null },
      ],
      count: 3,
    },
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('TabProductosProveedor — columna Margen (Bloque 1)', () => {
  it('calcula el margen % comparando precio de compra vs. precio de venta actual', async () => {
    mockVinculos()
    render(<TabProductosProveedor proveedores={[PROVEEDOR]} productos={[PRODUCTO_MARGEN_ALTO, PRODUCTO_PERDIDA, PRODUCTO_SIN_VENTA]} />)

    // Agua mineral: compra 3000, venta 5000 → +40%
    await waitFor(() => expect(screen.getByText('+40%')).toBeInTheDocument())
    // Yogur bebible: compra 2500, venta 2000 → pérdida, -25%
    expect(screen.getByText('-25%')).toBeInTheDocument()
    // Producto sin lista de precio: sin venta configurada → '—'
    expect(screen.getByText('—')).toBeInTheDocument()
  })
})
