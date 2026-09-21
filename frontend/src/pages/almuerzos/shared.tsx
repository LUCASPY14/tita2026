import type { BadgeColor } from '../../components/ui/Badge'

// ─── Helpers ─────────────────────────────────────────────────────────────────
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
  id_hijo: number
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
  id_tipo_almuerzo: number
  nombre: string
  descripcion: string
  precio_unitario: string | number
  incluye_plato_principal: boolean
  incluye_postre: boolean
  incluye_bebida: boolean
  activo: boolean
  es_predeterminado: boolean
}

export interface Suscripcion {
  id_suscripcion: number
  hijo: number
  hijo_nombre: string
  estado: string
  fecha_inicio: string
  fecha_fin: string | null
}

export interface MenuDiario {
  id_menu: number
  fecha: string
  plato_principal: string
  guarnicion: string
  postre: string
  bebida: string
  descripcion: string
  activo: boolean
}

export interface RegistroConsumo {
  id_registro_consumo: number
  hijo_nombre: string
  fecha_consumo: string
  tipo_almuerzo_nombre: string
  costo_almuerzo: string | number
  estado: string
  ya_cobrado: boolean
}

export interface CuentaMensual {
  id: string
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

export interface SaldoAlmuerzoItem {
  id_saldo_almuerzo: number
  hijo: number
  hijo_nombre: string
  hijo_grado: string | null
  nro_tarjeta: string
  saldo_actual: string | number
  limite_credito: string | number
  deuda_maxima: number | null
  fecha_actualizacion: string
}

export interface ResumenSaldos {
  deuda_total: number
  alumnos_con_deuda: number
  saldo_a_favor_total: number
  alumnos_con_saldo_a_favor: number
}

export interface RecargaPendiente {
  id_recarga_almuerzo: number
  hijo: number
  hijo_nombre: string
  monto_cargado: string | number
  metodo_pago: string
  referencia: string | null
  fecha_carga: string
  registrado_por_nombre: string | null
}

/** Alumno al que se le va a cargar saldo de almuerzo (desde cualquier tab). */
export interface CargaAlmuerzoTarget {
  hijo: number
  hijo_nombre: string
  /** Monto sugerido (deuda actual). 0 si no hay deuda. */
  monto_sugerido: number
  /** Línea informativa bajo el nombre. */
  detalle: string
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

export type TabKey = 'consumos' | 'cuentas' | 'saldos' | 'suscripciones' | 'menu'
