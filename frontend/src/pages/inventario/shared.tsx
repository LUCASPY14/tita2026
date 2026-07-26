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

export function formatFecha(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
  })
}

export interface Producto { id: number; descripcion: string }

export interface DetalleAjuste {
  producto: Producto | null
  cantidad: number
  motivo_detalle: string
}

export interface AjusteInventario {
  id: number; tipo: string; estado: string; motivo: string; fecha: string
  usuario_nombre: string
  detalles: { id: number; producto_nombre: string; cantidad: number; motivo_detalle: string }[]
}

export interface MovimientoStock {
  id: number; producto: number; producto_nombre: string; tipo: string
  cantidad: number; motivo: string; fecha: string; usuario_nombre?: string
}

export interface Lote {
  id: number; producto: number; producto_nombre: string; numero_lote: string
  fecha_vencimiento: string; cantidad: number; dias_hasta_vencimiento: number
  esta_vencido: boolean; bloqueado: boolean
}

export interface AlertaStock {
  id: number; producto: number; producto_nombre: string; tipo: string
  stock_actual: string | number; stock_minimo: string | number; activa: boolean; fecha_generada: string
}

export interface AlertaVencimiento {
  id: number; lote: number; lote_numero: string; producto_nombre: string; tipo: string
  dias_restantes: number; fecha_vencimiento: string; cantidad_lote: string | number
  accion_tomada: string | null; fecha_accion: string | null; responsable: number | null; fecha_generada: string
}

export const ESTADO_COLOR: Record<string, BadgeColor> = {
  PENDIENTE: 'orange', APROBADO: 'green', RECHAZADO: 'red',
}
export const TIPO_AJUSTE_COLOR: Record<string, BadgeColor> = { AUMENTO: 'green', MERMA: 'red' }
export const TIPO_MOV_COLOR: Record<string, BadgeColor> = {
  ENTRADA: 'green', SALIDA: 'red', AJUSTE: 'orange', TRANSFERENCIA: 'blue',
}
export const ALERTA_COLOR: Record<string, BadgeColor> = {
  STOCK_CERO: 'red', STOCK_CRITICO: 'orange', STOCK_MINIMO: 'yellow',
}
export const VENC_COLOR: Record<string, BadgeColor> = {
  VENCIDO: 'red', '3_DIAS': 'red', '7_DIAS': 'orange', '15_DIAS': 'orange', '30_DIAS': 'yellow',
}
export const VENC_LABEL: Record<string, string> = {
  VENCIDO: 'VENCIDO', '3_DIAS': '≤ 3 días', '7_DIAS': '≤ 7 días', '15_DIAS': '≤ 15 días', '30_DIAS': '≤ 30 días',
}
export const ACCION_COLOR: Record<string, BadgeColor> = {
  PENDIENTE: 'orange', DESCUENTO: 'blue', DEVUELTO: 'default', DONADO: 'green', DESCARTADO: 'red', VENDIDO: 'green',
}

export type TabKey = 'ajustes' | 'movimientos' | 'lotes' | 'alertas'
export const DETALLE_EMPTY: DetalleAjuste = { producto: null, cantidad: 1, motivo_detalle: '' }
