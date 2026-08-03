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

const pagosBancardService = {
  listar: (params?: Record<string, unknown>) =>
    api.get<Paginated<PagoBancard>>('/core/bancard/pagos/', { params }),

  anular: (shopProcessId: string) =>
    api.post<{ detail: string }>(`/core/bancard/pagos/${shopProcessId}/anular/`),
}

export default pagosBancardService
