import api from './api'
import type { Paginated } from './tarjetas'

export interface PagoBancard {
  shop_process_id:            string
  tipo:                       'TARJETA' | 'ALMUERZO'
  estado:                     'PENDIENTE' | 'APROBADO' | 'RECHAZADO' | 'CANCELADO' | 'ERROR'
  monto:                      number | string
  descripcion:                string
  cliente_nombre:             string
  tarjeta_nro:                string | null
  cuenta_almuerzo_id_display: number | null
  fecha_creacion:             string
  fecha_confirmacion:         string | null
  card_id_bancard:            number | null
  card_masked_number:         string
}

export interface PagoBancardDetalle extends PagoBancard {
  process_id:       string | null
  ip_origen:        string | null
  bancard_response: Record<string, unknown>
}

export interface AccionPagoResponse {
  detail: string
  accion?: 'vinculado' | 'acreditado'
  resuelto?: boolean
  pago?: PagoBancard
}

const pagosBancardService = {
  listar: (params?: Record<string, unknown>) =>
    api.get<Paginated<PagoBancard>>('/core/bancard/pagos/', { params }),

  detalle: (shopProcessId: string) =>
    api.get<PagoBancardDetalle>(`/core/bancard/pagos/${shopProcessId}/`),

  anular: (shopProcessId: string) =>
    api.post<{ detail: string }>(`/core/bancard/pagos/${shopProcessId}/anular/`),

  reintentar: (shopProcessId: string) =>
    api.post<AccionPagoResponse>(`/core/bancard/pagos/${shopProcessId}/reintentar/`),

  reconsultar: (shopProcessId: string) =>
    api.post<AccionPagoResponse>(`/core/bancard/pagos/${shopProcessId}/reconsultar/`),

  cerrarManual: (shopProcessId: string) =>
    api.post<AccionPagoResponse>(`/core/bancard/pagos/${shopProcessId}/cerrar-manual/`),

  exportarCsv: (params?: Record<string, unknown>) =>
    api.get<Blob>('/core/bancard/pagos/', {
      params: { ...params, formato: 'csv' },
      responseType: 'blob',
    }),
}

export default pagosBancardService
