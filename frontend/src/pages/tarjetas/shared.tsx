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

export function formatFechaCorta(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
  })
}

export interface Tarjeta {
  nro_tarjeta: string
  codigo_barras: string
  es_alumno: boolean
  hijo_nombre: string | null
  hijo_grado: string | null
  cliente_nombre: string | null
  cliente_ruc: string | null
  saldo_actual: string | number
  saldo_disponible: string | number
  limite_credito: string | number
  estado: string
  fecha_vencimiento: string | null
  permite_saldo_negativo: boolean
  saldo_alerta: string | number | null
  notificar_saldo_bajo: boolean
}

export interface ClienteBasico {
  id_cliente: number
  nombre_completo: string
  ruc_ci: string
}

export interface Hijo {
  id_hijo: number
  nombre: string
  apellido: string
  grado: string
  activo: boolean
}

export interface MovimientoTarjeta {
  id_movimiento_tarjeta: number
  tarjeta: string
  tipo: string
  monto: string | number
  saldo_anterior: string | number
  saldo_resultante: string | number
  descripcion: string
  fecha: string
}

export interface CargaSaldo {
  id_carga: number
  tarjeta: string
  monto_cargado: string | number
  metodo_pago: string
  estado: string
  fecha: string
  fecha_carga: string
  usuario_nombre?: string
}

export type TipoTitular = 'alumno' | 'funcionario'

export interface TarjetaForm {
  nro_tarjeta: string
  codigo_barras: string
  tipoTitular: TipoTitular
  hijo: number | ''
  cliente_directo: number | ''
  limite_credito: string
  permite_saldo_negativo: boolean
  estado: string
  fecha_vencimiento: string
}

export interface TarjetaEditForm {
  limite_credito: string
  permite_saldo_negativo: boolean
  estado: string
  fecha_vencimiento: string
  saldo_alerta: string
  notificar_saldo_bajo: boolean
}

export const ESTADO_COLOR: Record<string, BadgeColor> = {
  ACTIVA: 'green', BLOQUEADA: 'orange', VENCIDA: 'red', CANCELADA: 'default',
}

export const TIPO_MOV_LABEL: Record<string, string> = {
  RECARGA: 'Recarga', CONSUMO: 'Consumo', AJUSTE: 'Ajuste', REVERSO: 'Reverso',
}

export const TIPO_MOV_COLOR: Record<string, BadgeColor> = {
  RECARGA: 'green', CONSUMO: 'blue', AJUSTE: 'orange', REVERSO: 'purple',
}

export const ESTADO_CARGA_COLOR: Record<string, BadgeColor> = {
  CONFIRMADA: 'green', PENDIENTE: 'yellow', RECHAZADA: 'red',
}

export const FORM_INITIAL: TarjetaForm = {
  nro_tarjeta: '', codigo_barras: '',
  tipoTitular: 'alumno', hijo: '', cliente_directo: '',
  limite_credito: '', permite_saldo_negativo: false,
  estado: 'ACTIVA', fecha_vencimiento: '',
}
