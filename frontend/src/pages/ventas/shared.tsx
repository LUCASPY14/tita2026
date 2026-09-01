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
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

// ─── Interfaces ───────────────────────────────────────────────────────────────

export interface ClienteOption {
  id: number
  nombre_completo: string
}

export interface ProductoOption {
  id: number
  descripcion: string
}

export interface VentaOrigen {
  id: number
  fecha: string
  monto_total: string | number
  cliente: number
  detalles: { producto: number; producto_nombre: string; cantidad: string | number; precio_unitario: string | number }[]
}

export interface NCDetalle {
  producto: number
  producto_nombre: string
  cantidad: number
  precio_unitario: number
}

export interface NotaCredito {
  id: number
  cliente: number
  cliente_nombre: string
  venta_origen: number | null
  nro_nota_credito: string
  monto_total: string | number
  motivo: string
  estado: 'EMITIDA' | 'APLICADA' | 'ANULADA'
  fecha_emision: string
  fecha_creacion: string
  detalles: { id: number; producto: number; producto_nombre: string; cantidad: string; precio_unitario: string; subtotal: string }[]
}

export const NC_ESTADO_COLOR: Record<string, BadgeColor> = {
  EMITIDA: 'blue',
  APLICADA: 'green',
  ANULADA: 'red',
}
