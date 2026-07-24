// ─── Audio ────────────────────────────────────────────────────────────────────
export function tone(freq: number, ms: number, type: OscillatorType = 'sine', vol = 0.22) {
  try {
    const ctx = new AudioContext()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain); gain.connect(ctx.destination)
    osc.frequency.value = freq; osc.type = type
    gain.gain.setValueAtTime(vol, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + ms / 1000)
    osc.start(); osc.stop(ctx.currentTime + ms / 1000)
    setTimeout(() => ctx.close(), ms + 100)
  } catch { /* AudioContext blocked */ }
}
export const sfx = {
  card:     () => { tone(880, 80); setTimeout(() => tone(1100, 130), 100) },
  add:      () => tone(660, 55),
  ok:       () => { tone(660, 80); setTimeout(() => tone(990, 200), 95) },
  error:    () => tone(180, 320, 'sawtooth', 0.3),
  restrict: () => { tone(200, 170, 'square'); setTimeout(() => tone(160, 260, 'square'), 190) },
  lowBal:   () => { tone(440, 130); setTimeout(() => tone(320, 180), 150) },
}

// ─── Frecuencia de ventas ─────────────────────────────────────────────────────
const SALES_KEY = 'recreo_sales_v2'
export const getSalesMap = (): Record<number, number> => {
  try { return JSON.parse(localStorage.getItem(SALES_KEY) || '{}') }
  catch { return {} }
}
export const addSales = (ids: number[]) => {
  const m = getSalesMap()
  ids.forEach(id => { m[id] = (m[id] || 0) + 1 })
  localStorage.setItem(SALES_KEY, JSON.stringify(m))
}

// ─── Contadores diarios ──────────────────────────────────────────────────────
const DAILY_KEY = 'recreo_daily_stats'
export interface DailyStats { date: string; count: number; totalTime: number }
export const getDailyStats = (): DailyStats => {
  try {
    const stored = JSON.parse(localStorage.getItem(DAILY_KEY) || '{}')
    const today = new Date().toISOString().slice(0, 10)
    if (stored.date !== today) return { date: today, count: 0, totalTime: 0 }
    return stored
  } catch { return { date: new Date().toISOString().slice(0, 10), count: 0, totalTime: 0 } }
}
export const updateDailyStats = (timeMs: number) => {
  const stats = getDailyStats()
  stats.count += 1
  stats.totalTime += timeMs
  localStorage.setItem(DAILY_KEY, JSON.stringify(stats))
}

// ─── Metadata de categorías ───────────────────────────────────────────────────
const CAT: Record<string, { emoji: string; bg: string; border: string; accent: string }> = {
  bebidas:   { emoji: '🥤', bg: 'bg-blue-50',    border: 'border-blue-400',    accent: 'text-blue-700' },
  snacks:    { emoji: '🍟', bg: 'bg-orange-50',  border: 'border-orange-400',  accent: 'text-orange-700' },
  lácteos:   { emoji: '🥛', bg: 'bg-sky-50',     border: 'border-sky-400',     accent: 'text-sky-700' },
  panaderia: { emoji: '🍞', bg: 'bg-amber-50',   border: 'border-amber-400',   accent: 'text-amber-700' },
  panadería: { emoji: '🍞', bg: 'bg-amber-50',   border: 'border-amber-400',   accent: 'text-amber-700' },
  frutas:    { emoji: '🍎', bg: 'bg-green-50',   border: 'border-green-400',   accent: 'text-green-700' },
  postres:   { emoji: '🍰', bg: 'bg-pink-50',    border: 'border-pink-400',    accent: 'text-pink-700' },
  golosinas: { emoji: '🍬', bg: 'bg-purple-50',  border: 'border-purple-400',  accent: 'text-purple-700' },
  alimentos: { emoji: '🍽️', bg: 'bg-emerald-50', border: 'border-emerald-400', accent: 'text-emerald-700' },
}
export function catMeta(cat: string) {
  const key = cat.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
  return CAT[key] ?? { emoji: '📦', bg: 'bg-slate-50', border: 'border-slate-300', accent: 'text-slate-600' }
}

export const CARD_PREFIX = 'T-'
export function detectInputType(value: string): 'card' | 'product' {
  if (!value) return 'product'
  if (value.startsWith(CARD_PREFIX)) return 'card'
  if (!/^\d+$/.test(value)) return 'card'
  return 'product'
}

// ─── Interfaces ───────────────────────────────────────────────────────────────
export interface Producto {
  id: number; codigo_barra: string; descripcion: string
  precio_actual: string; categoria_nombre: string
  stock_actual?: number | null
}
export interface RestriccionHijo {
  id: number; tipo: string; descripcion: string | null
  severidad: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA'; requiere_autorizacion: boolean
}
export interface Tarjeta {
  nro_tarjeta: string; hijo_nombre: string | null; hijo_foto: string | null
  hijo_grado: string | null; hijo_restricciones: RestriccionHijo[]
  saldo_actual: string; saldo_disponible: string; estado: string
  permite_saldo_negativo: boolean; limite_credito: string
  cliente_id: number; cliente_nombre: string; cliente_ruc: string
  lista_precio_id: number | null; lista_es_default: boolean
  es_alumno: boolean
  cliente_modalidad_facturacion: 'INMEDIATA' | 'MENSUAL'
}
export interface ClienteBasico {
  id: number; nombre_completo: string; ruc_ci: string
  modalidad_facturacion?: 'INMEDIATA' | 'MENSUAL'
}
export interface ItemCarrito { producto: Producto; cantidad: number }
export interface MedioPagoDB { id: number; descripcion: string; activo: boolean; requiere_validacion: boolean }

export type ModoPago = 'PREPAGO' | 'MEDIO' | 'CREDITO'
export type Flash = 'none' | 'ok' | 'error' | 'restrict'

// ─── Helpers ──────────────────────────────────────────────────────────────────
export const gs = (n: number | string | null | undefined) =>
  (Number(n) || 0).toLocaleString('es-PY') + ' Gs.'

export function extractError(err: unknown): string {
  const e = err as { response?: { data?: unknown } }
  const d = e?.response?.data
  if (!d) return 'Error al registrar la venta'
  if (typeof d === 'string') return d
  if (typeof d === 'object') {
    const obj = d as Record<string, unknown>
    if (obj.detail) return String(obj.detail)
    if (obj.error)  return String(obj.error)
    const first = Object.values(obj)[0]
    if (Array.isArray(first)) return String(first[0])
    if (typeof first === 'string') return first
  }
  return 'Error al registrar la venta'
}
