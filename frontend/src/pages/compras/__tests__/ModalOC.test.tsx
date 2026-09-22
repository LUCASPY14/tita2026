import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ModalOC from '../ModalOC'

vi.mock('../../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn() },
}))

vi.mock('react-hot-toast', () => {
  const toastFn = Object.assign(vi.fn(), { error: vi.fn(), success: vi.fn() })
  return { default: toastFn }
})

import api from '../../../services/api'
import toast from 'react-hot-toast'

const PROVEEDOR = { id_proveedor: 1, razon_social: 'Distribuidora El Sol', ruc: '1', telefono: null, email: null, direccion: null, ciudad: null, ciudad_nombre: null, activo: true, saldo_cuenta_corriente: 0 }
const PRODUCTO = { id_producto: 10, descripcion: 'Agua mineral', precio_actual: 5000, codigo_barra: null, codigo: null }

function renderModal() {
  return render(
    <ModalOC open={true} editingOC={null} proveedores={[PROVEEDOR]} productos={[PRODUCTO]} onClose={vi.fn()} onSaved={vi.fn()} />,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/compras/productos-proveedor/') {
      return Promise.resolve({
        data: { results: [{ id_producto_proveedor: 1, proveedor: 1, proveedor_nombre: 'Distribuidora El Sol', producto: 10, producto_nombre: 'Agua mineral', precio_compra: 3000, fecha_ultima_compra: null }] },
      })
    }
    return Promise.resolve({ data: { results: [] } })
  })
  vi.mocked(api.post).mockResolvedValue({ data: {} })
})

async function seleccionarProveedorYProducto() {
  await userEvent.click(screen.getByPlaceholderText('Buscar proveedor...'))
  await userEvent.click(await screen.findByRole('option', { name: 'Distribuidora El Sol' }))
  await waitFor(() => expect(api.get).toHaveBeenCalledWith(
    '/compras/productos-proveedor/', { params: { proveedor: 1, page_size: 500 } },
  ))
  await userEvent.click(screen.getByPlaceholderText('Producto...'))
  await userEvent.click(await screen.findByRole('option', { name: /Agua mineral/ }))
}

describe('ModalOC — margen de referencia (Bloque 1)', () => {
  it('muestra el margen de referencia (costo vs. precio de venta actual) al elegir un producto', async () => {
    renderModal()
    await seleccionarProveedorYProducto()

    // costo=3000 (conocido del proveedor), venta actual=5000 → margen = 40%
    await waitFor(() => expect(screen.getByText('+40% margen ref.')).toBeInTheDocument())
  })
})

describe('ModalOC — alerta de margen negativo al crear la OC (Bloque 4)', () => {
  it('avisa (sin bloquear) si un producto queda con margen negativo vs. el precio de venta actual', async () => {
    renderModal()
    await seleccionarProveedorYProducto()

    const costoInput = screen.getByPlaceholderText('Costo')
    await userEvent.clear(costoInput)
    await userEvent.type(costoInput, '6000')
    await waitFor(() => expect(screen.getByText('-20% margen ref.')).toBeInTheDocument())

    await userEvent.click(screen.getByRole('button', { name: 'Crear OC' }))

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/compras/ordenes/', expect.anything()))
    expect(toast).toHaveBeenCalledWith(
      expect.stringContaining('Agua mineral'),
      expect.objectContaining({ icon: '⚠️' }),
    )
    expect(toast.success).toHaveBeenCalledWith(expect.stringContaining('Orden de Compra creada'))
  })
})
