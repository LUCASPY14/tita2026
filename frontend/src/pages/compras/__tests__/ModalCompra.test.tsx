import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ModalCompra from '../ModalCompra'

vi.mock('../../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../services/api'

const PROVEEDOR = { id_proveedor: 1, razon_social: 'Distribuidora El Sol', ruc: '1', telefono: null, email: null, direccion: null, ciudad: null, ciudad_nombre: null, activo: true, saldo_cuenta_corriente: 0 }
const PRODUCTO = { id_producto: 10, descripcion: 'Agua mineral', precio_actual: 5000, codigo_barra: null, codigo: null }

function renderModal() {
  return render(
    <ModalCompra open={true} editingCompra={null} proveedores={[PROVEEDOR]} productos={[PRODUCTO]} onClose={vi.fn()} onSaved={vi.fn()} />,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/compras/productos-proveedor/') {
      return Promise.resolve({
        data: { results: [{ id_producto_proveedor: 1, proveedor: 1, proveedor_nombre: 'Distribuidora El Sol', producto: 10, producto_nombre: 'Agua mineral', precio_compra: 3000, fecha_ultima_compra: null, preferido: true }] },
      })
    }
    return Promise.resolve({ data: { results: [] } })
  })
})

async function seleccionarProveedorYProducto() {
  const proveedorCombo = screen.getByPlaceholderText('Buscar proveedor...')
  await userEvent.click(proveedorCombo)
  await userEvent.click(await screen.findByRole('option', { name: 'Distribuidora El Sol' }))

  await waitFor(() => expect(api.get).toHaveBeenCalledWith(
    '/compras/productos-proveedor/', { params: { proveedor: 1, page_size: 500 } },
  ))

  const productoCombo = screen.getByPlaceholderText('Producto...')
  await userEvent.click(productoCombo)
  await userEvent.click(await screen.findByRole('option', { name: /Agua mineral/ }))
}

describe('ModalCompra — margen costo vs. venta (Bloque 1)', () => {
  it('muestra el margen al seleccionar un producto con precio de compra y venta conocidos', async () => {
    renderModal()
    await seleccionarProveedorYProducto()

    // costo=3000 (conocido del proveedor), venta=5000 (precio_actual) → margen = (5000-3000)/5000 = 40%
    await waitFor(() => expect(screen.getByText('+40% margen')).toBeInTheDocument())
  })

  it('muestra margen negativo (pérdida) si el costo supera el precio de venta', async () => {
    renderModal()
    await seleccionarProveedorYProducto()
    await waitFor(() => expect(screen.getByText('+40% margen')).toBeInTheDocument())

    const costoInput = screen.getByPlaceholderText('Costo')
    await userEvent.clear(costoInput)
    await userEvent.type(costoInput, '6000')

    await waitFor(() => expect(screen.getByText('-20% margen')).toBeInTheDocument())
  })

  it('indica que falta precio de venta cuando el campo queda en 0', async () => {
    renderModal()
    await seleccionarProveedorYProducto()
    await waitFor(() => expect(screen.getByText('+40% margen')).toBeInTheDocument())

    const ventaInput = screen.getByPlaceholderText('Opcional')
    await userEvent.clear(ventaInput)

    await waitFor(() => expect(screen.getByText('Sin precio de venta')).toBeInTheDocument())
  })
})

describe('ModalCompra — indicador de proveedor preferido (Bloque 2)', () => {
  it('marca con una estrella la opción del producto cuyo proveedor es el preferido', async () => {
    renderModal()
    await userEvent.click(screen.getByPlaceholderText('Buscar proveedor...'))
    await userEvent.click(await screen.findByRole('option', { name: 'Distribuidora El Sol' }))
    await waitFor(() => expect(api.get).toHaveBeenCalledWith(
      '/compras/productos-proveedor/', { params: { proveedor: 1, page_size: 500 } },
    ))

    await userEvent.click(screen.getByPlaceholderText('Producto...'))
    expect(await screen.findByRole('option', { name: /^★ Agua mineral/ })).toBeInTheDocument()
  })
})

describe('ModalCompra — preselección desde alerta de stock bajo (Bloque 3)', () => {
  it('precarga proveedor, producto y costo cuando se abre con preseleccion', async () => {
    const { rerender } = render(
      <ModalCompra
        open={false} editingCompra={null} proveedores={[PROVEEDOR]} productos={[PRODUCTO]}
        preseleccion={{ proveedorId: 1, productoId: 10 }}
        onClose={vi.fn()} onSaved={vi.fn()}
      />,
    )
    // Igual que en la app real: el modal nace cerrado y se abre después
    // (deep-link desde "Generar compra" en la alerta de stock bajo).
    rerender(
      <ModalCompra
        open={true} editingCompra={null} proveedores={[PROVEEDOR]} productos={[PRODUCTO]}
        preseleccion={{ proveedorId: 1, productoId: 10 }}
        onClose={vi.fn()} onSaved={vi.fn()}
      />,
    )

    await waitFor(() => expect(screen.getByPlaceholderText('Buscar proveedor...')).toHaveValue('Distribuidora El Sol'))
    await waitFor(() => expect(screen.getByPlaceholderText('Costo')).toHaveValue(3000))
    expect(screen.getByPlaceholderText('Producto...')).toHaveValue('★ Agua mineral — 3.000 Gs.')
  })
})
