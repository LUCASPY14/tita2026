/**
 * Modo Recreo v3 — POS ultra-rápido para recreo escolar.
 * Mejoras aplicadas:
 * - Escaneo inteligente (detecta automáticamente tarjeta/producto)
 * - Fila de favoritos (top 5 más vendidos)
 * - Feedback visual al agregar producto (parpadeo verde)
 * - Panel alumno dominante (foto, nombre, saldo gigantes)
 * - Total y botón COBRAR de gran tamaño
 * - Atajos visibles en header, Ctrl+Backspace, +/- numérico
 * - Colores de alto contraste, mejor aprovechamiento del espacio
 * - Íconos Phosphor (estilo fill) para mayor peso visual
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  LightningIcon,
  XIcon,
  PlusIcon,
  MinusIcon,
  CheckCircleIcon,
  XCircleIcon,
  UserIcon,
  CreditCardIcon,
  ShoppingCartIcon,
  WarningIcon,
  SpinnerIcon,
  ClockIcon,
  MagnifyingGlassIcon,
  TrendUpIcon,
  MoneyIcon,
} from '@phosphor-icons/react'
import api from '../services/api'
import { useCatalogoStore } from '../store/catalogoStore'

// ─── Audio ────────────────────────────────────────────────────────────────────
function tone(freq: number, ms: number, type: OscillatorType = 'sine', vol = 0.22) {
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
const sfx = {
  card:     () => { tone(880, 80); setTimeout(() => tone(1100, 130), 100) },
  add:      () => tone(660, 55),
  ok:       () => { tone(660, 80); setTimeout(() => tone(990, 200), 95) },
  error:    () => tone(180, 320, 'sawtooth', 0.3),
  restrict: () => { tone(200, 170, 'square'); setTimeout(() => tone(160, 260, 'square'), 190) },
  lowBal:   () => { tone(440, 130); setTimeout(() => tone(320, 180), 150) },
}

// ─── Frecuencia de ventas (localStorage) ─────────────────────────────────────
const SALES_KEY = 'recreo_sales_v2'
const getSalesMap = (): Record<number, number> => {
  try { return JSON.parse(localStorage.getItem(SALES_KEY) || '{}') }
  catch { return {} }
}
const addSales = (ids: number[]) => {
  const m = getSalesMap()
  ids.forEach(id => { m[id] = (m[id] || 0) + 1 })
  localStorage.setItem(SALES_KEY, JSON.stringify(m))
}

// ─── Contadores diarios ──────────────────────────────────────────────────────
const DAILY_KEY = 'recreo_daily_stats'
interface DailyStats { date: string; count: number; totalTime: number }
const getDailyStats = (): DailyStats => {
  try {
    const stored = JSON.parse(localStorage.getItem(DAILY_KEY) || '{}')
    const today = new Date().toISOString().slice(0, 10)
    if (stored.date !== today) return { date: today, count: 0, totalTime: 0 }
    return stored
  } catch { return { date: new Date().toISOString().slice(0, 10), count: 0, totalTime: 0 } }
}
const updateDailyStats = (timeMs: number) => {
  const stats = getDailyStats()
  stats.count += 1
  stats.totalTime += timeMs
  localStorage.setItem(DAILY_KEY, JSON.stringify(stats))
}

// ─── Metadata de categorías (ajustada para alto contraste) ──────────────────
const CAT: Record<string, { emoji: string; border: string; accent: string }> = {
  bebidas:   { emoji: '🥤', border: 'border-blue-500',    accent: 'text-blue-700' },
  snacks:    { emoji: '🍟', border: 'border-orange-500',  accent: 'text-orange-700' },
  lácteos:   { emoji: '🥛', border: 'border-sky-500',     accent: 'text-sky-700' },
  panaderia: { emoji: '🍞', border: 'border-amber-500',   accent: 'text-amber-700' },
  panadería: { emoji: '🍞', border: 'border-amber-500',   accent: 'text-amber-700' },
  frutas:    { emoji: '🍎', border: 'border-green-500',   accent: 'text-green-700' },
  postres:   { emoji: '🍰', border: 'border-pink-500',    accent: 'text-pink-700' },
  golosinas: { emoji: '🍬', border: 'border-purple-500',  accent: 'text-purple-700' },
  alimentos: { emoji: '🍽️', border: 'border-emerald-500', accent: 'text-emerald-700' },
}
function catMeta(cat: string) {
  const key = cat.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
  return CAT[key] ?? { emoji: '📦', border: 'border-slate-400', accent: 'text-slate-600' }
}

// ─── Detección de tipo de código escaneado ────────────────────────────────────
// Si el código empieza por CARD_PREFIX O contiene caracteres no numéricos
// se trata como tarjeta. Ajustar el prefijo según el sistema de tarjetas.
const CARD_PREFIX = 'T-'

function detectInputType(value: string): 'card' | 'product' {
  if (!value) return 'product'
  if (value.startsWith(CARD_PREFIX)) return 'card'
  if (!/^\d+$/.test(value)) return 'card'  // letras/guiones → tarjeta
  return 'product'
}

// ─── Interfaces ───────────────────────────────────────────────────────────────
interface Producto {
  id: number; codigo_barra: string; descripcion: string
  precio_actual: string; categoria_nombre: string
  stock_actual?: number | null  // presente cuando el backend lo incluye
}
interface RestriccionHijo {
  id: number; tipo: string; descripcion: string | null
  severidad: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA'; requiere_autorizacion: boolean
}
interface Tarjeta {
  nro_tarjeta: string; hijo_nombre: string; hijo_foto: string | null
  hijo_grado: string | null; hijo_restricciones: RestriccionHijo[]
  saldo_actual: string; saldo_disponible: string; estado: string
  permite_saldo_negativo: boolean; cliente_id: number
  cliente_nombre: string; cliente_ruc: string
}
interface ItemCarrito { producto: Producto; cantidad: number }

// ─── Helpers ──────────────────────────────────────────────────────────────────
const gs = (n: number | string | null | undefined) =>
  (Number(n) || 0).toLocaleString('es-PY') + ' Gs.'

function extractError(err: unknown): string {
  const e = err as { response?: { data?: unknown } }
  const d = e?.response?.data
  if (!d) return 'Error al registrar la venta'
  if (typeof d === 'string') return d
  if (typeof d === 'object') {
    const obj = d as Record<string, unknown>
    if (obj.detail) return String(obj.detail)
    const first = Object.values(obj)[0]
    if (Array.isArray(first)) return String(first[0])
  }
  return 'Error al registrar la venta'
}

// ─── Tipos de flash ───────────────────────────────────────────────────────────
type Flash = 'none' | 'ok' | 'error' | 'restrict'

// ─── Componente principal ─────────────────────────────────────────────────────
export default function ModoRecreo() {
  const navigate = useNavigate()
  const { getProductos, getCategorias } = useCatalogoStore()

  // Datos
  const [productos, setProductos] = useState<Producto[]>([])
  const [loadingProductos, setLoadingProductos] = useState(true)
  const [categorias, setCategorias] = useState<string[]>([])

  // Tarjeta / alumno
  const [tarjetaInput, setTarjetaInput] = useState('')
  const [tarjeta, setTarjeta] = useState<Tarjeta | null>(null)
  const [buscandoTarjeta, setBuscandoTarjeta] = useState(false)

  // Catálogo
  const [catFiltro, setCatFiltro] = useState('')
  const [prodSearch, setProdSearch] = useState('')

  // Carrito
  const [carrito, setCarrito] = useState<ItemCarrito[]>([])

  // Cobro
  const [cobrando, setCobrando] = useState(false)
  const [flash, setFlash] = useState<Flash>('none')
  const [flashMsg, setFlashMsg] = useState('')

  // Feedback visual de agregado
  const [addedProductId, setAddedProductId] = useState<number | null>(null)
  const addedTimer = useRef<ReturnType<typeof setTimeout>>(undefined)

  // Reloj
  const [clock, setClock] = useState(() =>
    new Date().toLocaleTimeString('es-PY', { hour: '2-digit', minute: '2-digit' })
  )

  // Frecuencia de ventas
  const [salesMap, setSalesMap] = useState<Record<number, number>>(getSalesMap)

  // Estadísticas diarias
  const [dailyStats, setDailyStats] = useState<DailyStats>(getDailyStats)
  const ventaStartTime = useRef<number>(0)

  // Refs
  const scannerRef = useRef<HTMLInputElement>(null)
  const prodSearchRef = useRef<HTMLInputElement>(null)
  const flashTimer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const cobrandoRef = useRef(false)
  const productosFiltradosRef = useRef<Producto[]>([])
  const handleAgregarRef = useRef<(p: Producto) => void>(() => {})
  const handleCobrarRef = useRef<() => void>(() => {})
  const handleCancelarRef = useRef<() => void>(() => {})

  // Input con foco activo (para ring visual)
  const [focusedInput, setFocusedInput] = useState<'scanner' | 'search' | null>(null)

  // Ref para debounce de re-escaneo
  const lastScannedProduct = useRef<{ id: number; time: number } | null>(null)

  // Reloj
  useEffect(() => {
    const t = setInterval(() =>
      setClock(new Date().toLocaleTimeString('es-PY', { hour: '2-digit', minute: '2-digit' }))
    , 10000)
    return () => clearInterval(t)
  }, [])

  // Carga inicial
  useEffect(() => {
    Promise.all([getProductos(), getCategorias()])
      .then(([prods, cats]) => {
        setProductos(prods as Producto[])
        setCategorias(cats.map(c => c.nombre))
      })
      .catch(() => toast.error('Error al cargar datos'))
      .finally(() => setLoadingProductos(false))
  }, [getProductos, getCategorias])

  // Auto-foco persistente
  useEffect(() => {
    const t = setTimeout(() => scannerRef.current?.focus(), 50)
    return () => clearTimeout(t)
  }, [])
  useEffect(() => {
    const handler = () => {
      if (document.activeElement?.tagName === 'BODY') scannerRef.current?.focus()
    }
    window.addEventListener('focus', handler)
    return () => window.removeEventListener('focus', handler)
  }, [])

  // Teclado global
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName.toLowerCase()
      const inInput = tag === 'input' || tag === 'textarea' || tag === 'select'

      if (e.key === 'F2') { e.preventDefault(); prodSearchRef.current?.focus(); return }
      if (e.key === 'F3') { e.preventDefault(); scannerRef.current?.focus(); return }
      if (e.key === 'F9') { e.preventDefault(); handleCobrarRef.current(); return }
      if (e.key === 'Escape') { e.preventDefault(); handleCancelarRef.current(); return }
      if (e.ctrlKey && e.key === 'Backspace') {
        e.preventDefault()
        setCarrito(prev => prev.slice(0, -1))
        return
      }
      // Teclado numérico + / -
      if (!inInput && e.key === '+') {
        e.preventDefault()
        const last = carrito[carrito.length - 1]
        if (last) handleAgregarRef.current(last.producto)
        return
      }
      if (!inInput && e.key === '-') {
        e.preventDefault()
        const last = carrito[carrito.length - 1]
        if (last) {
          setCarrito(prev => {
            if (last.cantidad <= 1) return prev.slice(0, -1)
            return prev.map(i => i.producto.id === last.producto.id ? { ...i, cantidad: i.cantidad - 1 } : i)
          })
        }
        return
      }
      // 1-9: agregar producto N del grid visible
      if (!inInput && /^[1-9]$/.test(e.key)) {
        const p = productosFiltradosRef.current[parseInt(e.key) - 1]
        if (p) handleAgregarRef.current(p)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [carrito]) // dependencia de carrito para +/- último

  // Productos filtrados y ordenados por frecuencia
  const productosFiltrados = useMemo(() => {
    let list = productos
    if (catFiltro) list = list.filter(p => p.categoria_nombre === catFiltro)
    if (prodSearch) list = list.filter(p =>
      p.descripcion.toLowerCase().includes(prodSearch.toLowerCase()) ||
      p.codigo_barra.includes(prodSearch))
    const sorted = [...list].sort(
      (a, b) => ((salesMap[b.id] || 0) - (salesMap[a.id] || 0)) ||
                a.descripcion.localeCompare(b.descripcion)
    )
    productosFiltradosRef.current = sorted
    return sorted
  }, [productos, catFiltro, prodSearch, salesMap])

  // Top 5 favoritos
  const favoritos = useMemo(() => {
    return [...productos]
      .sort((a, b) => (salesMap[b.id] || 0) - (salesMap[a.id] || 0))
      .slice(0, 5)
  }, [productos, salesMap])

  // Totales
  const total = useMemo(() =>
    carrito.reduce((s, i) => s + (Number(i.producto.precio_actual) || 0) * i.cantidad, 0),
  [carrito])

  const saldoDisponible = tarjeta
    ? (Number(tarjeta.saldo_disponible) || Number(tarjeta.saldo_actual) || 0)
    : null
  const saldoTrasCompra = saldoDisponible !== null ? saldoDisponible - total : null

  // Check restricción
  const isRestricto = useCallback((producto: Producto): RestriccionHijo | null => {
    if (!tarjeta?.hijo_restricciones?.length) return null
    return tarjeta.hijo_restricciones.find(r => {
      const desc = (r.descripcion || '').toLowerCase()
      if (!desc) return false
      if (r.tipo === 'CATEGORIA') return producto.categoria_nombre.toLowerCase().includes(desc)
      if (r.tipo === 'PRODUCTO')  return producto.descripcion.toLowerCase().includes(desc)
      return producto.descripcion.toLowerCase().includes(desc) ||
             producto.categoria_nombre.toLowerCase().includes(desc)
    }) ?? null
  }, [tarjeta])

  // Buscar tarjeta
  const buscarTarjeta = useCallback(async (nro: string) => {
    if (!nro || buscandoTarjeta) return
    setBuscandoTarjeta(true)
    try {
      const { data } = await api.get('/core/tarjetas/', { params: { search: nro } })
      const found = (data.results ?? []).find(
        (t: Tarjeta) => t.nro_tarjeta === nro)
      if (!found) {
        sfx.error(); toast.error('Tarjeta no encontrada'); return
      }
      if (found.estado !== 'ACTIVA') {
        sfx.error(); toast.error(`Tarjeta ${found.estado.toLowerCase()}`); return
      }
      sfx.card()
      setTarjeta(found)
      setCarrito([])
      const criticas = (found.hijo_restricciones ?? []).filter((r: RestriccionHijo) => r.severidad === 'CRITICA')
      if (criticas.length > 0) {
        sfx.restrict()
        toast.error(`⚠️ ${criticas.length} restricción CRÍTICA`, { duration: 4000 })
      }
      if (Number(found.saldo_disponible || found.saldo_actual) < 5000) {
        sfx.lowBal()
        toast(`Saldo bajo: ${gs(found.saldo_disponible || found.saldo_actual)}`, { icon: '⚠️' })
      }
      ventaStartTime.current = performance.now()
    } catch {
      sfx.error(); toast.error('Error al buscar tarjeta')
    } finally {
      setBuscandoTarjeta(false)
      setTarjetaInput('')
      setTimeout(() => scannerRef.current?.focus(), 50)
    }
  }, [buscandoTarjeta])

  // Agregar al carrito
  const handleAgregar = useCallback((producto: Producto) => {
    const restriccion = isRestricto(producto)
    const bloqueado = restriccion && (restriccion.severidad === 'CRITICA' || restriccion.severidad === 'ALTA')
    if (bloqueado) {
      sfx.restrict()
      clearTimeout(flashTimer.current)
      setFlash('restrict')
      setFlashMsg(`🚫 RESTRINGIDO — ${producto.descripcion}`)
      flashTimer.current = setTimeout(() => setFlash('none'), 1800)
      return
    }
    const precio = Number(producto.precio_actual) || 0
    if (saldoDisponible !== null && !tarjeta?.permite_saldo_negativo) {
      const nuevoTotal = total + precio
      if (nuevoTotal > saldoDisponible) {
        sfx.error(); toast.error('Saldo insuficiente'); return
      }
    }
    sfx.add()
    setCarrito(prev => {
      const ex = prev.find(i => i.producto.id === producto.id)
      if (ex) return prev.map(i => i.producto.id === producto.id ? { ...i, cantidad: i.cantidad + 1 } : i)
      return [...prev, { producto, cantidad: 1 }]
    })
    // Feedback visual
    setAddedProductId(producto.id)
    clearTimeout(addedTimer.current)
    addedTimer.current = setTimeout(() => setAddedProductId(null), 200)
  }, [isRestricto, saldoDisponible, tarjeta, total])

  // Quitar cantidad
  const handleQuitar = useCallback((id: number) => {
    setCarrito(prev => {
      const item = prev.find(i => i.producto.id === id)
      if (!item) return prev
      return item.cantidad <= 1
        ? prev.filter(i => i.producto.id !== id)
        : prev.map(i => i.producto.id === id ? { ...i, cantidad: i.cantidad - 1 } : i)
    })
  }, [])

  // Cobrar
  const handleCobrar = useCallback(async () => {
    if (cobrandoRef.current || carrito.length === 0) return
    if (!tarjeta) { toast.error('Escanear tarjeta del alumno'); scannerRef.current?.focus(); return }
    cobrandoRef.current = true
    setCobrando(true)
    const inicio = ventaStartTime.current || performance.now()
    try {
      await api.post('/ventas/ventas/', {
        cliente: tarjeta.cliente_id,
        tipo: 'CONTADO',
        tarjeta: tarjeta.nro_tarjeta,
        medio_pago: null,
        items: carrito.map(i => ({
          producto: i.producto.id,
          cantidad: i.cantidad,
          precio_unitario: Number(i.producto.precio_actual) || 0,
          iva_10: 0, iva_5: 0, monto_exenta: 0,
        })),
      }, { timeout: 6000 })
      sfx.ok()
      addSales(carrito.map(i => i.producto.id))
      setSalesMap(getSalesMap())
      const tiempoMs = performance.now() - inicio
      updateDailyStats(tiempoMs)
      setDailyStats(getDailyStats())
      clearTimeout(flashTimer.current)
      setFlash('ok')
      setFlashMsg(`✅  ${tarjeta.hijo_nombre}  —  ${gs(total)}`)
      flashTimer.current = setTimeout(() => {
        setFlash('none')
        setCarrito([])
        setTarjeta(null)
        ventaStartTime.current = 0
        setTimeout(() => scannerRef.current?.focus(), 60)
      }, 2500)
    } catch (err) {
      sfx.error()
      toast.error(extractError(err))
    } finally {
      cobrandoRef.current = false
      setCobrando(false)
    }
  }, [carrito, tarjeta, total])

  // Cancelar
  const handleCancelar = useCallback(() => {
    clearTimeout(flashTimer.current)
    setFlash('none'); setCarrito([]); setTarjeta(null)
    setTarjetaInput(''); setProdSearch(''); ventaStartTime.current = 0
    setTimeout(() => scannerRef.current?.focus(), 60)
  }, [])

  // Sincronizar refs
  handleAgregarRef.current  = handleAgregar
  handleCobrarRef.current   = handleCobrar
  handleCancelarRef.current = handleCancelar

  // Procesar escaneo automático (Enter)
  const processScan = useCallback(async (value: string) => {
    if (!value.trim()) return
    const trimmed = value.trim()
    setTarjetaInput('')
    if (detectInputType(trimmed) === 'card') {
      // Es tarjeta
      if (tarjeta) {
        setCarrito([]) // Nueva tarjeta limpia carrito
      }
      await buscarTarjeta(trimmed)
    } else {
      // Es producto
      if (!tarjeta) {
        sfx.error(); toast.error('Escanee una tarjeta primero')
        setTimeout(() => scannerRef.current?.focus(), 100)
        return
      }
      const prod = productos.find(p => p.codigo_barra === trimmed)
      if (prod) {
        // Debounce de re-escaneo (<1s) para incrementar cantidad (manejado por handleAgregar)
        const now = Date.now()
        if (lastScannedProduct.current?.id === prod.id && (now - lastScannedProduct.current.time) < 1000) {
          // ya se maneja el incremento en handleAgregar
        }
        lastScannedProduct.current = { id: prod.id, time: now }
        handleAgregarRef.current(prod)
        setTimeout(() => scannerRef.current?.focus(), 30)
      } else {
        sfx.error(); toast.error(`Código no encontrado: ${trimmed}`)
        setTimeout(() => scannerRef.current?.focus(), 100)
      }
    }
  }, [tarjeta, productos, buscarTarjeta])

  // ─── JSX ─────────────────────────────────────────────────────────────────
  const flashCfg = {
    ok:       { overlay: 'bg-green-500/25', card: 'bg-green-950 border-green-500' },
    error:    { overlay: 'bg-red-500/25',   card: 'bg-red-950 border-red-500' },
    restrict: { overlay: 'bg-red-600/30',   card: 'bg-red-950 border-red-600' },
    none:     { overlay: '', card: '' },
  }[flash]

  const avgTime = dailyStats.count > 0 ? (dailyStats.totalTime / dailyStats.count / 1000).toFixed(1) : '—'

  return (
    <div className="fixed inset-0 bg-white text-slate-900 flex flex-col overflow-hidden" style={{ zIndex: 100 }} translate="no">

      {/* ── Flash overlay ── */}
      {flash !== 'none' && (
        <div className={`absolute inset-0 flex items-center justify-center pointer-events-none ${flashCfg.overlay}`} style={{ zIndex: 200 }}>
          <div className={`border-2 rounded-3xl px-16 py-10 text-center ${flashCfg.card}`}>
            <p className="text-4xl font-black text-white">{flashMsg}</p>
            {flash === 'ok' && saldoTrasCompra !== null && (
              <p className="text-slate-300 text-xl mt-2 tabular-nums">Saldo restante: {gs(saldoTrasCompra)}</p>
            )}
          </div>
        </div>
      )}

      {/* ── Header ── */}
      <header className="flex items-center justify-between px-4 py-1.5 bg-slate-900 text-white shadow-md h-14 shrink-0">
        <div className="flex items-center gap-4">
          <img src="/logo_tita.png" alt="" className="h-7 w-auto bg-white rounded p-0.5" />
          <div className="flex items-center gap-1.5 bg-yellow-500/20 border border-yellow-400/30 rounded-full px-3 py-1">
            <LightningIcon size={14} weight="fill" className="text-yellow-400" />
            <span className="text-yellow-300 text-xs font-bold uppercase tracking-widest">Modo Recreo</span>
          </div>
          <div className="flex items-center gap-3 ml-4 text-[11px] text-slate-400">
            <span className="flex items-center gap-1"><ClockIcon size={14} weight="fill" />{clock}</span>
            <span>Ventas hoy: <strong className="text-white">{dailyStats.count}</strong></span>
            <span>Tiempo medio: <strong className="text-white">{dailyStats.count > 0 ? `${avgTime}s` : '—'}</strong></span>
          </div>
        </div>
        <div className="flex items-center gap-4 text-[11px]">
          <div className="flex items-center gap-3">
            <span><kbd className="bg-slate-700 text-slate-300 rounded px-1.5 py-0.5 font-mono text-[10px] mr-1">F2</kbd>Buscar</span>
            <span><kbd className="bg-slate-700 text-slate-300 rounded px-1.5 py-0.5 font-mono text-[10px] mr-1">F3</kbd>Escanear</span>
            <span><kbd className="bg-slate-700 text-green-400 rounded px-1.5 py-0.5 font-mono text-[10px] mr-1">F9</kbd>Cobrar</span>
            <span><kbd className="bg-slate-700 text-slate-300 rounded px-1.5 py-0.5 font-mono text-[10px] mr-1">Esc</kbd>Cancelar</span>
            <span><kbd className="bg-slate-700 text-slate-300 rounded px-1.5 py-0.5 font-mono text-[10px] mr-1">+/-</kbd>Cant</span>
          </div>
          <button onClick={() => navigate('/dashboard')}
            className="flex items-center gap-1 px-2.5 py-1 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-xs font-medium transition-colors cursor-pointer">
            <XIcon size={14} weight="fill" />Salir
          </button>
        </div>
      </header>

      {/* ── Cuerpo 3 columnas ── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ══ PANEL IZQUIERDO: ALUMNO ══ */}
        <aside className="w-72 bg-white border-r border-slate-200 flex flex-col shrink-0 shadow-inner">
          <div className="p-3 border-b border-slate-100">
            <input
              ref={scannerRef}
              value={tarjetaInput}
              onChange={e => setTarjetaInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') processScan(tarjetaInput) }}
              onFocus={() => setFocusedInput('scanner')}
              onBlur={() => setFocusedInput(null)}
              placeholder="Escanear tarjeta o código…"
              disabled={buscandoTarjeta}
              className={[
                'w-full bg-slate-50 border rounded-xl px-4 py-3 text-base text-slate-900 placeholder:text-slate-400 outline-none transition-all',
                focusedInput === 'scanner'
                  ? 'border-green-500 ring-4 ring-green-400/30 ring-offset-1'
                  : 'border-slate-300',
              ].join(' ')}
            />
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {tarjeta ? (
              <>
                <div className="text-center">
                  {tarjeta.hijo_foto ? (
                    <img src={tarjeta.hijo_foto} alt={tarjeta.hijo_nombre}
                      className="w-36 h-36 rounded-full object-cover border-4 border-green-500 mx-auto mb-3 shadow-md" />
                  ) : (
                    <div className="w-36 h-36 rounded-full bg-slate-100 border-4 border-green-300 flex items-center justify-center mx-auto mb-3">
                      <UserIcon size={72} weight="fill" className="text-slate-400" />
                    </div>
                  )}
                  <p className="text-2xl font-black text-slate-900 leading-tight">{tarjeta.hijo_nombre}</p>
                  {tarjeta.hijo_grado && <p className="text-slate-500 text-base mt-0.5">{tarjeta.hijo_grado}</p>}
                  <p className="text-slate-300 text-xs mt-1 font-mono tracking-wider">
                    {tarjeta.nro_tarjeta}
                  </p>
                </div>

                {/* Restricciones — siempre visibles, antes del saldo */}
                {tarjeta.hijo_restricciones?.length > 0 && (
                  <div className="bg-red-50 border-2 border-red-400 rounded-xl p-2.5 space-y-1.5">
                    <div className="flex items-center gap-1.5">
                      <WarningIcon size={14} weight="fill" className="text-red-500 shrink-0" />
                      <span className="text-red-600 text-xs font-black uppercase tracking-wider">
                        {tarjeta.hijo_restricciones.length} Restricción{tarjeta.hijo_restricciones.length > 1 ? 'es' : ''}
                      </span>
                    </div>
                    {tarjeta.hijo_restricciones.map(r => (
                      <div key={r.id} className="flex items-center gap-1.5">
                        <span className="text-xs">🚫</span>
                        <span className="text-red-700 text-xs font-semibold leading-tight flex-1">{r.descripcion || r.tipo}</span>
                        <span className={`text-[9px] font-bold px-1 py-0.5 rounded shrink-0 ${
                          r.severidad === 'CRITICA' ? 'bg-red-600 text-white' :
                          r.severidad === 'ALTA' ? 'bg-orange-500 text-white' : 'bg-slate-300 text-slate-700'
                        }`}>{r.severidad}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Saldo con labels explícitos */}
                <div className={`rounded-2xl p-4 border-2 ${
                  (saldoDisponible ?? 0) < 5000 ? 'bg-red-50 border-red-400' :
                  (saldoDisponible ?? 0) < 15000 ? 'bg-yellow-50 border-yellow-400' : 'bg-green-50 border-green-400'
                }`}>
                  <div className="flex items-baseline justify-between mb-1">
                    <p className="text-slate-500 text-[10px] uppercase tracking-widest font-bold">Saldo actual</p>
                    <p className={`text-3xl font-black tabular-nums leading-none ${
                      (saldoDisponible ?? 0) < 5000 ? 'text-red-600' :
                      (saldoDisponible ?? 0) < 15000 ? 'text-yellow-600' : 'text-green-600'
                    }`}>
                      {gs(tarjeta.saldo_disponible || tarjeta.saldo_actual)}
                    </p>
                  </div>
                  {carrito.length > 0 && saldoTrasCompra !== null && (
                    <div className="flex items-baseline justify-between border-t border-current/20 pt-1.5 mt-1.5">
                      <p className="text-slate-500 text-[10px] uppercase tracking-widest font-bold">Después de compra</p>
                      <p className={`text-xl font-black tabular-nums ${saldoTrasCompra < 0 ? 'text-red-600' : 'text-slate-600'}`}>
                        {gs(saldoTrasCompra)}
                      </p>
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2 bg-green-50 border border-green-300 rounded-lg px-4 py-2">
                  <div className="w-3 h-3 rounded-full bg-green-500 shrink-0" />
                  <span className="text-green-700 text-sm font-bold">ACTIVA</span>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-48 text-center">
                <CreditCardIcon size={64} weight="fill" className="text-slate-300 mb-4" />
                <p className="text-slate-500 text-lg font-semibold">Sin alumno</p>
                <p className="text-slate-400 text-sm mt-1">Escanear tarjeta para comenzar</p>
              </div>
            )}
          </div>
        </aside>

        {/* ══ PANEL CENTRAL: PRODUCTOS ══ */}
        <main className="flex-1 flex flex-col overflow-hidden bg-slate-50">
          <div className="px-4 pt-3 pb-2 border-b border-slate-200 space-y-3 shrink-0 bg-white">
            <div className="relative">
              <MagnifyingGlassIcon size={20} weight="fill" className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
              <input
                ref={prodSearchRef}
                value={prodSearch}
                onChange={e => setProdSearch(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' && productosFiltrados.length > 0) {
                    handleAgregarRef.current(productosFiltrados[0])
                    setProdSearch('')
                    setTimeout(() => scannerRef.current?.focus(), 50)
                  }
                }}
                onFocus={() => setFocusedInput('search')}
                onBlur={() => setFocusedInput(null)}
                placeholder="Buscar producto… (F2)"
                className={[
                  'w-full bg-white border-2 rounded-xl pl-11 pr-4 py-3 text-base text-slate-900 placeholder:text-slate-400 outline-none transition-all',
                  focusedInput === 'search'
                    ? 'border-green-500 ring-4 ring-green-400/30 ring-offset-1'
                    : 'border-slate-300',
                ].join(' ')}
              />
            </div>
            <div className="flex gap-2 overflow-x-auto scrollbar-hide">
              {['', ...categorias].map(c => (
                <button key={c || '__all__'}
                  onClick={() => setCatFiltro(c)}
                  className={`shrink-0 px-4 py-1.5 rounded-full text-sm font-bold transition-colors cursor-pointer ${
                    catFiltro === c
                      ? 'bg-slate-800 text-white'
                      : 'bg-white text-slate-600 border border-slate-300 hover:bg-slate-100'
                  }`}>
                  {c || 'Todos'}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Fila de favoritos */}
            {favoritos.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-base">🔥</span>
                  <span className="text-slate-500 text-xs font-bold uppercase tracking-wider">Top más vendidos</span>
                </div>
                <div className="flex gap-3 overflow-x-auto pb-1">
                  {favoritos.map(p => {
                    const meta = catMeta(p.categoria_nombre)
                    const restr = isRestricto(p)
                    const bloqueado = !!restr && (restr.severidad === 'CRITICA' || restr.severidad === 'ALTA')
                    return (
                      <button
                        key={p.id}
                        onClick={() => handleAgregar(p)}
                        disabled={bloqueado}
                        className={[
                          'relative flex flex-col items-center justify-center shrink-0 w-32 h-24 rounded-2xl border-2 p-2 transition-all duration-100',
                          bloqueado
                            ? 'bg-red-50 border-red-300 opacity-60 cursor-not-allowed'
                            : `bg-white ${meta.border} cursor-pointer hover:shadow-lg hover:scale-105 active:scale-95`,
                        ].join(' ')}
                      >
                        {p.stock_actual != null && p.stock_actual <= 3 && (
                          <span className="absolute top-1 right-1 text-[9px] font-bold text-red-600 bg-red-100 rounded px-1">
                            {p.stock_actual === 0 ? 'AGOTADO' : `${p.stock_actual}u`}
                          </span>
                        )}
                        <span className="text-3xl mb-0.5">{meta.emoji}</span>
                        <span className="text-[11px] text-slate-700 font-semibold leading-tight line-clamp-1">{p.descripcion}</span>
                        <span className={`text-sm font-black tabular-nums mt-0.5 ${meta.accent}`}>{gs(p.precio_actual)}</span>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Grid de productos */}
            {loadingProductos ? (
              <div className="flex items-center justify-center h-full text-slate-400 text-base">Cargando...</div>
            ) : productosFiltrados.length === 0 ? (
              <div className="flex items-center justify-center h-32 text-slate-400 text-base">Sin productos</div>
            ) : (
              <div className="grid grid-cols-3 xl:grid-cols-4 gap-3">
                {productosFiltrados.slice(0, 12).map((p, idx) => {
                  const meta = catMeta(p.categoria_nombre)
                  const restr = isRestricto(p)
                  const bloqueado = !!restr && (restr.severidad === 'CRITICA' || restr.severidad === 'ALTA')
                  const isAdded = p.id === addedProductId
                  return (
                    <button
                      key={p.id}
                      onClick={() => handleAgregar(p)}
                      disabled={bloqueado}
                      className={[
                        'relative flex flex-col items-center justify-center text-center rounded-2xl border-2 p-3 min-h-[130px] transition-all duration-100 select-none',
                        bloqueado
                          ? 'bg-red-50 border-red-300 opacity-60 cursor-not-allowed'
                          : `bg-white ${meta.border} cursor-pointer hover:shadow-md hover:scale-[1.03] active:scale-95`,
                        isAdded && 'ring-4 ring-green-400 scale-105',
                      ].join(' ')}
                    >
                      {idx < 9 && (
                        <span className="absolute top-1.5 left-2 text-xs font-bold text-slate-400/60">{idx + 1}</span>
                      )}
                      {bloqueado && <span className="absolute top-1.5 right-2 text-sm">🚫</span>}
                      {p.stock_actual != null && !bloqueado && (
                        <span className={`absolute bottom-1 right-1.5 text-[9px] font-bold px-1 py-0.5 rounded tabular-nums ${
                          p.stock_actual === 0     ? 'bg-red-600 text-white' :
                          p.stock_actual <= 3      ? 'bg-red-100 text-red-700' :
                          p.stock_actual <= 10     ? 'bg-orange-100 text-orange-700' :
                          'text-slate-300'
                        }`}>
                          {p.stock_actual === 0 ? 'AGOTADO' : `${p.stock_actual}u`}
                        </span>
                      )}
                      <span className="text-3xl mb-1">{meta.emoji}</span>
                      <span className={`text-base font-black tabular-nums ${meta.accent}`}>{gs(p.precio_actual)}</span>
                      <span className="text-slate-600 text-xs font-medium leading-tight line-clamp-2 mt-0.5 px-1">
                        {p.descripcion}
                      </span>
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        </main>

        {/* ══ PANEL DERECHO: CARRITO + COBRO ══ */}
        <aside className="w-80 bg-white border-l border-slate-200 flex flex-col shrink-0 shadow-inner">
          <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShoppingCartIcon size={20} weight="fill" className="text-slate-600" />
              <span className="text-lg font-black text-slate-800">
                🛒 {carrito.reduce((s,i)=>s+i.cantidad,0)} PRODUCTOS
              </span>
            </div>
            {carrito.length > 0 && (
              <button onClick={() => setCarrito([])} className="text-slate-400 hover:text-red-500 transition-colors">
                <XIcon size={20} weight="fill" />
              </button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto">
            {carrito.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center px-4 py-6">
                <ShoppingCartIcon size={40} weight="fill" className="text-slate-200 mb-3" />
                <p className="text-slate-400 text-sm font-semibold mb-1">Sin productos</p>
                <p className="text-slate-300 text-xs">Escanee tarjeta y seleccione productos</p>
                <div className="mt-5 w-full border-t border-slate-100 pt-4 space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Ventas hoy</span>
                    <span className="font-mono font-bold text-slate-600">{dailyStats.count}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Tiempo medio</span>
                    <span className="font-mono font-bold text-slate-600">{avgTime}s</span>
                  </div>
                </div>
              </div>
            ) : (
              <ul className="divide-y divide-slate-100">
                {carrito.map(item => {
                  const precio = Number(item.producto.precio_actual) || 0
                  return (
                    <li key={item.producto.id} className="px-4 py-3">
                      <div className="flex items-start gap-2">
                        <p className="text-base text-slate-800 font-semibold flex-1 leading-tight">{item.producto.descripcion}</p>
                        <button onClick={() => setCarrito(p => p.filter(i => i.producto.id !== item.producto.id))}
                          className="text-slate-400 hover:text-red-500 shrink-0">
                          <XIcon size={16} weight="fill" />
                        </button>
                      </div>
                      <div className="flex items-center justify-between mt-2">
                        <div className="flex items-center gap-2">
                          <button onClick={() => handleQuitar(item.producto.id)}
                            className="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600">
                            <MinusIcon size={14} weight="fill" />
                          </button>
                          <span className="text-lg font-black text-slate-900 tabular-nums w-6 text-center">{item.cantidad}</span>
                          <button onClick={() => handleAgregar(item.producto)}
                            className="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600">
                            <PlusIcon size={14} weight="fill" />
                          </button>
                        </div>
                        <span className="text-base font-bold text-emerald-600 tabular-nums">{gs(precio * item.cantidad)}</span>
                      </div>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>

          <div className="border-t-2 border-slate-200 p-4 space-y-3">
            <div className="flex items-baseline justify-between">
              <span className="text-slate-500 text-sm font-black uppercase tracking-widest">Total</span>
              <span className="text-slate-900 text-4xl font-black tabular-nums">{gs(total)}</span>
            </div>
            {tarjeta && (
              <div className="flex items-baseline justify-between text-sm -mt-1">
                <span className="text-slate-400">Restante tras cobro</span>
                <span className={`font-bold tabular-nums ${(saldoTrasCompra ?? saldoDisponible ?? 0) < 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                  {gs(saldoTrasCompra ?? saldoDisponible ?? 0)}
                </span>
              </div>
            )}

            {tarjeta ? (
              <div className="flex items-center gap-2 bg-green-50 border border-green-300 rounded-lg px-3 py-2">
                <CreditCardIcon size={16} weight="fill" className="text-green-600 shrink-0" />
                <span className="text-green-700 text-sm font-semibold">Prepago automático</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
                <MoneyIcon size={16} weight="fill" className="text-slate-400 shrink-0" />
                <span className="text-slate-400 text-sm">Escanear tarjeta</span>
              </div>
            )}

            <button
              onClick={handleCobrar}
              disabled={carrito.length === 0 || cobrando || !tarjeta}
              className={[
                'w-full py-5 rounded-2xl font-black text-xl tracking-wide flex items-center justify-center gap-3 transition-all duration-150',
                carrito.length > 0 && tarjeta && !cobrando
                  ? 'bg-green-500 hover:bg-green-600 text-white cursor-pointer active:scale-95 shadow-xl shadow-green-500/30'
                  : 'bg-slate-200 text-slate-400 cursor-not-allowed',
              ].join(' ')}
            >
              {cobrando
                ? <><SpinnerIcon size={24} weight="fill" className="animate-spin" />Procesando…</>
                : <><CheckCircleIcon size={24} weight="fill" />COBRAR (F9)</>
              }
            </button>

            <button
              onClick={handleCancelar}
              className="w-full py-2.5 rounded-xl bg-slate-100 hover:bg-red-50 text-slate-500 hover:text-red-600 text-sm font-bold transition-colors cursor-pointer flex items-center justify-center gap-2"
            >
              <XCircleIcon size={16} weight="fill" />
              Cancelar (Esc)
            </button>
          </div>
        </aside>
      </div>
    </div>
  )
}