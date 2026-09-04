import type { BadgeColor } from '../../components/ui/Badge'

// ─── Helpers ──────────────────────────────────────────────────────────────────

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
  return new Date(iso).toLocaleDateString('es-PY', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

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
  producto: number
  producto_nombre: string
  precio_compra: number
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
