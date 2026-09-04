import api from './api'

export interface DetalleVenta {
  producto:   number
  cantidad:   number
  precio_unitario: number
  subtotal:   number
}

export interface VentaPayload {
  tarjeta:           string
  detalles:          { producto: number; cantidad: number }[]
  medio_pago:        string
  medio_pago_id?:    number | null
  referencia?:       string
  cierre_caja?:      number | null
}

export interface Venta {
  id_venta:     number
  tarjeta:      string
  total:        number
  fecha:        string
  estado:       string
}

const ventasService = {
  crear: (payload: VentaPayload, timeout = 6000) =>
    api.post<Venta>('/ventas/ventas/', payload, { timeout }),
}

export default ventasService
