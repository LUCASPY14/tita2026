import toast from 'react-hot-toast'
import api from '../../services/api'

// ─── Shared CSS ───────────────────────────────────────────────────────────────

export const inputClass =
  'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'

export const labelClass =
  'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

// ─── Shared helpers ───────────────────────────────────────────────────────────

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

export function toggleSwitch(
  checked: boolean,
  onChange: (v: boolean) => void,
  label: string,
) {
  return (
    <label className="flex items-center gap-3 cursor-pointer">
      <div className="relative shrink-0">
        <input
          type="checkbox"
          className="sr-only peer"
          checked={checked}
          onChange={e => onChange(e.target.checked)}
        />
        <div className="w-9 h-5 bg-slate-200 rounded-full peer-checked:bg-green-500 transition-colors" />
        <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
      </div>
      <span className="text-sm text-slate-700">{label}</span>
    </label>
  )
}

// ─── Shared delete handler ────────────────────────────────────────────────────

export type DeleteTarget = {
  url: string
  label: string
  reloadFn: () => void
}

export async function executeDelete(
  target: DeleteTarget,
  onSuccess: () => void,
): Promise<void> {
  await api.delete(target.url)
  toast.success(`"${target.label}" eliminado`)
  target.reloadFn()
  onSuccess()
}

// ─── Shared interfaces ────────────────────────────────────────────────────────

export interface Categoria {
  id: number
  nombre: string
  descripcion: string
}

export interface TipoCliente {
  id: number
  nombre: string
  descripcion: string
  descuento_porcentaje: number | string
}

export interface ListaPrecio {
  id: number
  nombre: string
  descripcion: string
  es_precio_base: boolean
}

export interface MedioPago {
  id: number
  descripcion: string
  requiere_validacion: boolean
  activo: boolean
}

export interface Grado {
  id: number
  nombre: string
  nivel: number
  orden: number
  es_ultimo: boolean
  activo: boolean
}

export interface DatosEmpresa {
  id: number
  ruc: string
  razon_social: string
  nombre_fantasia: string
  direccion: string
  ciudad: string
  pais: string
  telefono: string
  email: string
  activo: boolean
}

export interface HistoricoPrecioItem {
  id: number
  producto: number
  producto_nombre: string
  precio_anterior: string
  precio_nuevo: string
  variacion_porcentual: string
  fecha_cambio: string
}

export interface Producto {
  id: number
  descripcion: string
}

export interface Estado2FA {
  habilitado: boolean
  fecha_activacion: string | null
  tiene_backup_codes: boolean
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
  tipo: 'CANTIDAD' | 'SIN_LIMITE'
  precio_mensual: string | number
  cantidad_almuerzos_mes: number | null
  dias_semana_incluidos: number[]
  activo: boolean
  es_predeterminado: boolean
}

export interface UnidadMedida {
  id: number
  nombre: string
  abreviatura: string
  activo: boolean
}

export interface Alergeno {
  id: number
  nombre: string
  descripcion: string
  palabras_clave: string[]
  severidad: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA'
  icono: string
  activo: boolean
}

export interface Impuesto {
  id: number
  nombre: string
  porcentaje: string | number
  vigente_desde: string | null
  vigente_hasta: string | null
  activo: boolean
}
