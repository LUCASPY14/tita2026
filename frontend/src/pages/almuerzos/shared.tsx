import type { BadgeColor } from '../../components/ui/Badge'

// ─── Helpers ─────────────────────────────────────────────────────────────────
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

export function todayISO() {
  return new Date().toISOString().split('T')[0]
}

export function formatFecha(iso: string | null | undefined): string {
  if (!iso) return '—'
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

export const MESES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

// ─── Interfaces ──────────────────────────────────────────────────────────────
export interface Hijo {
  id: number
  nombre: string
  apellido: string
  grado: string
  nombre_completo?: string
}

export interface TarjetaBusqueda {
  nro_tarjeta: string
  hijo_nombre: string
  saldo_actual: string | number
  estado: string
}

export interface TipoAlmuerzo {
  id: number
  nombre: string
  descripcion: string
  precio_unitario: string | number
  incluye_plato_principal: boolean
  incluye_postre: boolean
  incluye_bebida: boolean
  activo: boolean
  es_predeterminado: boolean
}

export interface PlanAlmuerzo {
  id: number
  nombre: string
  tipo: string
  precio_mensual: string | number
  cantidad_almuerzos_mes: number | null
  dias_semana_incluidos: number[]
  activo: boolean
  es_predeterminado: boolean
}

export interface Suscripcion {
  id: number
  hijo: number
  hijo_nombre: string
  plan: number
  plan_nombre: string
  tipo_cobro: 'CUENTA' | 'MENSUAL'
  estado: string
  fecha_inicio: string
  fecha_fin: string | null
}

export interface MenuDiario {
  id: number
  fecha: string
  plato_principal: string
  guarnicion: string
  postre: string
  bebida: string
  descripcion: string
  activo: boolean
}

export interface RegistroConsumo {
  id: number
  hijo_nombre: string
  fecha_consumo: string
  tipo_almuerzo_nombre: string
  costo_almuerzo: string | number
  estado: string
  ya_cobrado: boolean
}

export interface CuentaMensual {
  id: number
  hijo: number
  hijo_nombre: string
  hijo_grado: string
  nro_tarjeta: string
  anio: number
  mes: number
  cantidad_almuerzos: number
  monto_total: string | number
  monto_pagado: string | number
  saldo_pendiente: string | number
  estado: string
}

// ─── Constants ───────────────────────────────────────────────────────────────
export const ESTADO_REGISTRO_COLOR: Record<string, BadgeColor> = {
  REGISTRADO: 'green',
  RECHAZADO: 'red',
  ANULADO: 'default',
}

export const ESTADO_CUENTA_COLOR: Record<string, BadgeColor> = {
  PENDIENTE: 'orange',
  PAGADO: 'green',
  PARCIAL: 'blue',
  ANULADO: 'default',
}

export const ESTADO_SUSCRIPCION_COLOR: Record<string, BadgeColor> = {
  ACTIVA: 'green',
  INACTIVA: 'default',
  SUSPENDIDA: 'orange',
}

export type TabKey = 'consumos' | 'cuentas' | 'suscripciones' | 'menu'
