import { formatDateTime } from '../../lib/format'
import type { BadgeColor } from '../../components/ui/Badge'

export function extractErrorMessage(err: unknown): string {
  const e = err as { response?: { data?: unknown } }
  const data = e?.response?.data
  if (!data) return 'Error inesperado'
  if (typeof data === 'string') return data
  if (typeof data === 'object') {
    const d = data as Record<string, unknown>
    const fieldErrors = d.field_errors as Record<string, unknown> | undefined
    if (fieldErrors && typeof fieldErrors === 'object' && Object.keys(fieldErrors).length > 0) {
      const [field, msgs] = Object.entries(fieldErrors)[0]
      return `${field}: ${Array.isArray(msgs) ? String(msgs[0]) : String(msgs)}`
    }
    if (d.detail) return String(d.detail)
    const first = Object.values(d)[0]
    if (Array.isArray(first)) return String(first[0])
    return JSON.stringify(data)
  }
  return 'Error inesperado'
}

export function formatGs(n: number | string | null | undefined): string {
  return (Number(n) || 0).toLocaleString('es-PY') + ' Gs.'
}

export const formatFecha = formatDateTime

export interface PendienteItem {
  tipo: string
  id: number
  cliente_id: number | null
  cliente_nombre: string
  modalidad_facturacion: string
  descripcion: string
  monto: number
  fecha: string
}

export interface Factura {
  id_factura: number
  nro_factura: string
  cliente: number | null
  cliente_nombre: string
  monto_total: string | number
  iva_10: string | number
  estado: string
  fecha_emision: string
}

export const ESTADO_COLOR: Record<string, BadgeColor> = {
  EMITIDA: 'green', ANULADA: 'red',
}

export const TIPO_LABEL: Record<string, string> = {
  CARGA_SALDO: 'Carga de saldo',
  PAGO_ALMUERZO: 'Almuerzo',
  VENTA: 'Venta',
  PAGO_CREDITO: 'Cobro crédito',
}

export const TIPO_COLOR: Record<string, BadgeColor> = {
  CARGA_SALDO: 'blue',
  PAGO_ALMUERZO: 'orange',
  VENTA: 'green',
  PAGO_CREDITO: 'purple',
}
