import { formatDateOnly } from '../../lib/format'
import type { BadgeColor } from '../../components/ui/Badge'

// ─── Helpers ──────────────────────────────────────────────────────────────────

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

export const formatFecha = formatDateOnly

// ─── Interfaces ───────────────────────────────────────────────────────────────

export interface Proveedor {
  id_proveedor: number
  razon_social: string
  ruc: string
  telefono: string | null
  email: string | null
  direccion: string | null
  ciudad: number | null
  ciudad_nombre: string | null
  activo: boolean
  saldo_cuenta_corriente: number | string
}

export interface Producto {
  id_producto: number
  descripcion: string
  precio_actual: string | number
  codigo_barra?: string | null
  codigo?: string | null
}

export interface DetalleCompra {
  id_detalle_compra: number
  producto: number
  producto_nombre: string
  cantidad: number
  costo_unitario: string | number
  subtotal: string | number
}

export interface Compra {
  id_compra: number
  proveedor: number
  proveedor_nombre: string
  fecha: string
  monto_total: string | number
  estado_pago: string
  estado_entrega: string
  tipo_pago: string
  nro_factura_proveedor: string
  saldo_pendiente: string | number
  detalles: DetalleCompra[]
}

export interface PagoProveedor {
  id_pago_proveedor: number
  compra_id: number | null
  proveedor: number
  proveedor_nombre: string
  monto_total: string | number
  fecha: string
  medio_pago: number
  medio_pago_nombre: string
  observaciones: string
  estado: string
}

export interface NCDetalle {
  producto: number
  producto_nombre: string
  cantidad: number
  precio_unitario: number
}

export interface NotaCredito {
  id_nc_proveedor: number
  proveedor: number
  proveedor_nombre: string
  compra_original: number | null
  monto_total: string | number
  nro_factura_compra: string | null
  observacion: string | null
  tipo_nc: 'AJUSTE_PRECIO' | 'DEVOLUCION'
  estado: 'EMITIDA' | 'APLICADA' | 'ANULADA'
  fecha: string
  fecha_creacion: string
  detalles: { id_detalle_ncp: number; producto: number; producto_nombre: string; cantidad: string; precio_unitario: string; subtotal: string }[]
}

export interface CuentaCorriente {
  id_movimiento_ccp: number
  tipo: string
  descripcion: string
  monto: string | number
  saldo_resultante: string | number
  fecha: string
}

export interface ProductoProveedorRecord {
  id_producto_proveedor: number
  proveedor: number
  proveedor_nombre: string
  producto: number
  producto_nombre: string
  precio_compra: number
  fecha_ultima_compra: string | null
  preferido: boolean
}

export interface ItemForm {
  producto: Producto | null
  cantidad: number
  costo_unitario: number
  subtotal: number
  precio_venta: number
}

export interface DetalleOC {
  id_detalle_oc: number
  producto: number
  producto_nombre: string
  cantidad: number
  costo_unitario: string | number
  subtotal: string | number
}

export interface OrdenCompra {
  id_orden_compra: number
  proveedor: number
  proveedor_nombre: string
  estado: 'BORRADOR' | 'PENDIENTE' | 'APROBADA' | 'RECHAZADA' | 'CONVERTIDA'
  tipo_pago: string
  monto_total: string | number
  nro_factura_esperada: string | null
  observaciones: string | null
  motivo_rechazo: string | null
  aprobado_por_nombre: string | null
  fecha_aprobacion: string | null
  compra_generada: number | null
  creado_por_nombre: string
  fecha_creacion: string
  detalles: DetalleOC[]
}

export interface CompraFormFields {
  proveedor_id: number | ''
  tipo_pago: string
  nro_factura: string
}

// ─── Constants ────────────────────────────────────────────────────────────────

export const ESTADO_PAGO_COLOR: Record<string, BadgeColor> = {
  PAGADO: 'green',
  PENDIENTE: 'orange',
  PARCIAL: 'blue',
  ANULADA: 'red',
}

export const TIPO_PAGO_COLOR: Record<string, BadgeColor> = {
  CONTADO: 'green',
  CREDITO: 'orange',
}

export const ESTADO_ENTREGA_COLOR: Record<string, BadgeColor> = {
  PENDIENTE: 'orange',
  RECIBIDA: 'green',
}

export const NC_ESTADO_COLOR: Record<string, BadgeColor> = {
  EMITIDA: 'blue',
  APLICADA: 'green',
  ANULADA: 'default',
}

export const OC_ESTADO_COLOR: Record<string, BadgeColor> = {
  BORRADOR: 'default',
  PENDIENTE: 'orange',
  APROBADA: 'green',
  RECHAZADA: 'red',
  CONVERTIDA: 'blue',
}

export const OC_ESTADO_LABEL: Record<string, string> = {
  BORRADOR: 'Borrador',
  PENDIENTE: 'En revisión',
  APROBADA: 'Aprobada',
  RECHAZADA: 'Rechazada',
  CONVERTIDA: 'Convertida',
}

export const ITEM_EMPTY: ItemForm = { producto: null, cantidad: 1, costo_unitario: 0, subtotal: 0, precio_venta: 0 }

// ─── Margen (costo de compra vs. precio de venta) ──────────────────────────────

export interface Margen {
  /** null cuando no hay precio de venta para comparar. */
  pct: number | null
  color: 'red' | 'orange' | 'green' | 'default'
}

/** Margen % = (venta - costo) / venta. <0% = pérdida, <15% = bajo, resto = ok. */
export function calcularMargen(costo: number, precioVenta: number): Margen {
  if (!precioVenta || precioVenta <= 0) return { pct: null, color: 'default' }
  const pct = ((precioVenta - costo) / precioVenta) * 100
  const color = pct < 0 ? 'red' : pct < 15 ? 'orange' : 'green'
  return { pct, color }
}

export const MARGEN_TEXT_COLOR: Record<Margen['color'], string> = {
  red: 'text-red-600',
  orange: 'text-orange-600',
  green: 'text-emerald-600',
  default: 'text-slate-400',
}

export function formatMargen(margen: Margen): string {
  if (margen.pct === null) return '—'
  return `${margen.pct >= 0 ? '+' : ''}${margen.pct.toFixed(0)}%`
}
