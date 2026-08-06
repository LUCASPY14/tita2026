import type { BadgeColor } from '../../components/ui/Badge'

export function extractErrorMessage(err: unknown): string {
  const e = err as { response?: { data?: unknown } }
  const data = e?.response?.data
  if (!data) return 'Error inesperado'
  if (typeof data === 'string') return data
  if (typeof data === 'object') {
    const d = data as Record<string, unknown>
    if (d.detail) return String(d.detail)
    if (d.error) return String(d.error)
    const first = Object.values(d)[0]
    if (Array.isArray(first)) return String(first[0])
    return JSON.stringify(data)
  }
  return 'Error inesperado'
}

export function formatGs(value: string | number | null | undefined): string {
  return (Number(value) || 0).toLocaleString('es-PY') + ' Gs.'
}

export function formatDatetime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export function elapsedLabel(isoApertura: string): string {
  const mins = Math.floor((Date.now() - new Date(isoApertura).getTime()) / 60000)
  if (mins < 60) return `${mins} min`
  const h = Math.floor(mins / 60), m = mins % 60
  return `${h}h ${m}min`
}

export interface Caja {
  id: number
  nombre: string
  ubicacion: string | null
  activo: boolean
}

export interface MedioPago {
  id: number
  descripcion: string
  activo: boolean
}

export interface CierreCaja {
  id: number
  caja: number
  caja_nombre: string
  caja_activo: boolean
  empleado: number
  empleado_nombre: string
  fecha_apertura: string
  fecha_cierre: string | null
  monto_inicial: string
  monto_contado_fisico: string | null
  diferencia_efectivo: string | null
  estado: 'ABIERTO' | 'CERRADO' | 'CONCILIADO'
  observaciones_conciliacion: string | null
}

export interface ArqueoData {
  monto_inicial: number
  efectivo_esperado: number
  efectivo_ingresos: number
  efectivo_egresos: number
  prepago_total: number
  ingresos_total: number
  egresos_total: number
  medios_pago_totales: { medio: string; total: number }[]
  egresos_por_medio: { medio: string; total: number }[]
}

export const ESTADO_COLOR: Record<string, BadgeColor> = {
  ABIERTO: 'green', CERRADO: 'blue', CONCILIADO: 'purple',
}

export const ESTADO_LABEL: Record<string, string> = {
  ABIERTO: 'Abierta', CERRADO: 'Cerrada', CONCILIADO: 'Conciliada',
}
