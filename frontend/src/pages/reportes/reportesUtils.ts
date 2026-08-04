import type { BadgeColor } from '../../components/ui/Badge'

// ─── Helpers ──────────────────────────────────────────────────────────────────

export function formatGs(n: number | null | undefined): string {
  return (Number(n) || 0).toLocaleString('es-PY') + ' Gs.'
}

export function formatFecha(iso: string): string {
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export function descargaBlob(blob: Blob, nombre: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = nombre; a.click()
  window.URL.revokeObjectURL(url)
}

export function fmtGsShort(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k`
  return String(n)
}

export function clientSort<T>(arr: T[], key: string, dir: 'asc' | 'desc'): T[] {
  return [...arr].sort((a, b) => {
    const av = (a as Record<string, unknown>)[key]
    const bv = (b as Record<string, unknown>)[key]
    if (av == null) return 1
    if (bv == null) return -1
    if (typeof av === 'number' && typeof bv === 'number')
      return dir === 'asc' ? av - bv : bv - av
    return dir === 'asc'
      ? String(av).localeCompare(String(bv))
      : String(bv).localeCompare(String(av))
  })
}

export function today(): string {
  return new Date().toISOString().split('T')[0]
}

export function primerDiaMes(): string {
  return today().slice(0, 7) + '-01'
}

// ─── Constants ────────────────────────────────────────────────────────────────

export const TIPO_LABEL: Record<string, string> = {
  VENTA_TARJETA: 'Tarjeta prepago', VENTA_EFECTIVO: 'Efectivo',
  CONSUMO_ALMUERZO: 'Almuerzo', CARGA_SALDO: 'Carga de saldo',
}

export const AGING_COLOR: Record<string, BadgeColor> = {
  '0-30': 'green', '31-60': 'yellow', '61-90': 'orange', '90+': 'red',
}

export const CHART_COLORS = ['#22c55e', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6']

export const NC_ESTADO_COLOR: Record<string, BadgeColor> = { EMITIDA: 'blue', APLICADA: 'green', ANULADA: 'red' }

export const ESTADO_ALM_COLOR: Record<string, BadgeColor> = { PAGADO: 'green', PARCIAL: 'blue', PENDIENTE: 'orange' }

export const FORMA_COBRO_LABEL: Record<string, string> = {
  EFECTIVO: 'Efectivo', TRANSFERENCIA: 'Transferencia',
  ONLINE: 'Online', DEBITO_AUTOMATICO: 'Débito automático',
}

export const ROL_LABEL: Record<string, string> = {
  ADMIN: 'Administrador', SUPERVISOR: 'Supervisor', CAJERO: 'Cajero',
  COBRADOR: 'Cobrador', COCINA: 'Cocina',
}

// ─── Shared CSS classes ───────────────────────────────────────────────────────

export const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
export const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'
