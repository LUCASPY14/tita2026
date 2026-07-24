import type { BadgeColor } from '../../components/ui/Badge'

export function extractErrorMessage(err: unknown): string {
  const e = err as { response?: { data?: unknown } }
  const data = e?.response?.data
  if (!data) return 'Error inesperado'
  if (typeof data === 'string') return data
  if (typeof data === 'object') {
    const d = data as Record<string, unknown>
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

export function formatFecha(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

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
  id: number
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
