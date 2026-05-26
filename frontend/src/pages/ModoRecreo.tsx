/**
 * Modo Recreo — POS ultra-rápido para recreo escolar.
 * Objetivo: 3-5 segundos por alumno.
 * Flujo: escanear tarjeta → agregar productos → F9 para cobrar → reset automático.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  Zap, X, Plus, Minus, CheckCircle, XCircle,
  User, CreditCard, ShoppingCart, AlertTriangle,
  Banknote, RefreshCw, Clock, Search,
} from 'lucide-react'
import api from '../services/api'

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

// ─── Metadata de categorías ───────────────────────────────────────────────────

const CAT: Record<string, { emoji: string; bg: string; border: string; accent: string }> = {
  bebidas:   { emoji: '🥤', bg: 'bg-blue-950/70',    border: 'border-blue-700/60',    accent: 'text-blue-300' },
  snacks:    { emoji: '🍟', bg: 'bg-orange-950/70',  border: 'border-orange-700/60',  accent: 'text-orange-300' },
  lácteos:   { emoji: '🥛', bg: 'bg-sky-950/70',     border: 'border-sky-700/60',     accent: 'text-sky-300' },
  panaderia: { emoji: '🍞', bg: 'bg-amber-950/70',   border: 'border-amber-700/60',   accent: 'text-amber-300' },
  panadería: { emoji: '🍞', bg: 'bg-amber-950/70',   border: 'border-amber-700/60',   accent: 'text-amber-300' },
  frutas:    { emoji: '🍎', bg: 'bg-green-950/70',   border: 'border-green-700/60',   accent: 'text-green-300' },
  postres:   { emoji: '🍰', bg: 'bg-pink-950/70',    border: 'border-pink-700/60',    accent: 'text-pink-300' },
  golosinas: { emoji: '🍬', bg: 'bg-purple-950/70',  border: 'border-purple-700/60',  accent: 'text-purple-300' },
  alimentos: { emoji: '🍽️', bg: 'bg-emerald-950/70', border: 'border-emerald-700/60', accent: 'text-emerald-300' },
}

function catMeta(cat: string) {
  const key = cat.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
  return CAT[key] ?? { emoji: '📦', bg: 'bg-slate-800', border: 'border-slate-700', accent: 'text-slate-300' }
}

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface Producto {
  id: number; codigo_barra: string; descripcion: string
  precio_actual: string; categoria_nombre: string
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

  // Reloj
  const [clock, setClock] = useState('')

  // Frecuencia de ventas
  const [salesMap, setSalesMap] = useState<Record<number, number>>(getSalesMap)

  // Refs
  const tarjetaRef = useRef<HTMLInputElement>(null)
  const prodSearchRef = useRef<HTMLInputElement>(null)
  const flashTimer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const productosFiltradosRef = useRef<Producto[]>([])
  const handleAgregarRef = useRef<(p: Producto) => void>(() => {})
  const handleCobrarRef = useRef<() => void>(() => {})
  const handleCancelarRef = useRef<() => void>(() => {})

  // Reloj
  useEffect(() => {
    const tick = () => setClock(new Date().toLocaleTimeString('es-PY', { hour: '2-digit', minute: '2-digit' }))
    tick(); const t = setInterval(tick, 10000); return () => clearInterval(t)
  }, [])

  // Carga inicial
  useEffect(() => {
    Promise.all([
      api.get('/productos/productos/', { params: { page_size: 300 } }),
      api.get('/productos/categorias/'),
    ]).then(([pRes, cRes]) => {
      setProductos(pRes.data.results ?? [])
      setCategorias((cRes.data.results ?? []).map((c: { nombre: string }) => c.nombre))
    }).catch(() => toast.error('Error al cargar datos'))
      .finally(() => setLoadingProductos(false))
  }, [])

  // Auto-foco en tarjeta
  useEffect(() => { tarjetaRef.current?.focus() }, [])

  // Teclado global (usa refs para evitar re-register)
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName.toLowerCase()
      const inInput = tag === 'input' || tag === 'textarea' || tag === 'select'

      if (e.key === 'F2') { e.preventDefault(); prodSearchRef.current?.focus(); return }
      if (e.key === 'F3') { e.preventDefault(); tarjetaRef.current?.focus(); return }
      if (e.key === 'F9') { e.preventDefault(); handleCobrarRef.current(); return }
      if (e.key === 'Escape') { e.preventDefault(); handleCancelarRef.current(); return }

      // 1-9: agregar producto N del grid visible
      if (!inInput && /^[1-9]$/.test(e.key)) {
        const p = productosFiltradosRef.current[parseInt(e.key) - 1]
        if (p) handleAgregarRef.current(p)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

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
  const buscarTarjeta = useCallback(async () => {
    const nro = tarjetaInput.trim()
    if (!nro || buscandoTarjeta) return
    setBuscandoTarjeta(true)
    try {
      const { data } = await api.get('/core/tarjetas/', { params: { search: nro } })
      const found = (data.results ?? []).find(
        (t: Tarjeta) => t.nro_tarjeta === nro)
      if (!found) {
        sfx.error(); toast.error('Tarjeta no encontrada')
        setTarjetaInput(''); return
      }
      if (found.estado !== 'ACTIVA') {
        sfx.error(); toast.error(`Tarjeta ${found.estado.toLowerCase()}`)
        setTarjetaInput(''); return
      }
      sfx.card()
      setTarjeta(found)
      setCarrito([])
      setTarjetaInput('')
      const criticas = (found.hijo_restricciones ?? []).filter((r: RestriccionHijo) => r.severidad === 'CRITICA')
      if (criticas.length > 0) {
        sfx.restrict()
        toast.error(`⚠️ ${criticas.length} restricción CRÍTICA`, { duration: 4000 })
      }
      if (Number(found.saldo_disponible || found.saldo_actual) < 5000) {
        sfx.lowBal()
        toast(`Saldo bajo: ${gs(found.saldo_disponible || found.saldo_actual)}`, { icon: '⚠️' })
      }
    } catch {
      sfx.error(); toast.error('Error al buscar tarjeta')
    } finally {
      setBuscandoTarjeta(false)
    }
  }, [tarjetaInput, buscandoTarjeta])

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
    if (carrito.length === 0 || cobrando) return
    if (!tarjeta) { toast.error('Escanear tarjeta del alumno'); tarjetaRef.current?.focus(); return }
    setCobrando(true)
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
      })
      sfx.ok()
      addSales(carrito.map(i => i.producto.id))
      setSalesMap(getSalesMap())
      clearTimeout(flashTimer.current)
      setFlash('ok')
      setFlashMsg(`✅  ${tarjeta.hijo_nombre}  —  ${gs(total)}`)
      flashTimer.current = setTimeout(() => {
        setFlash('none')
        setCarrito([])
        setTarjeta(null)
        setTimeout(() => tarjetaRef.current?.focus(), 60)
      }, 2500)
    } catch (err) {
      sfx.error()
      toast.error(extractError(err))
    } finally {
      setCobrando(false)
    }
  }, [carrito, cobrando, tarjeta, total])

  // Cancelar
  const handleCancelar = useCallback(() => {
    clearTimeout(flashTimer.current)
    setFlash('none'); setCarrito([]); setTarjeta(null)
    setTarjetaInput(''); setProdSearch('')
    setTimeout(() => tarjetaRef.current?.focus(), 60)
  }, [])

  // Sincronizar refs para keyboard handler
  handleAgregarRef.current  = handleAgregar
  handleCobrarRef.current   = handleCobrar
  handleCancelarRef.current = handleCancelar

  // ─── JSX ─────────────────────────────────────────────────────────────────

  const flashCfg = {
    ok:       { overlay: 'bg-green-500/25', card: 'bg-green-950 border-green-500' },
    error:    { overlay: 'bg-red-500/25',   card: 'bg-red-950 border-red-500' },
    restrict: { overlay: 'bg-red-600/30',   card: 'bg-red-950 border-red-600' },
    none:     { overlay: '', card: '' },
  }[flash]

  return (
    <div className="fixed inset-0 bg-slate-950 text-white flex flex-col overflow-hidden" style={{ zIndex: 100 }}>

      {/* ── Flash overlay ── */}
      {flash !== 'none' && (
        <div className={`absolute inset-0 flex items-center justify-center pointer-events-none ${flashCfg.overlay}`} style={{ zIndex: 200 }}>
          <div className={`border-2 rounded-3xl px-14 py-8 text-center ${flashCfg.card}`}>
            <p className="text-3xl font-black text-white">{flashMsg}</p>
            {flash === 'ok' && saldoTrasCompra !== null && (
              <p className="text-slate-400 text-lg mt-2 tabular-nums">Saldo restante: {gs(saldoTrasCompra)}</p>
            )}
          </div>
        </div>
      )}

      {/* ── Header ── */}
      <header className="flex items-center justify-between px-4 py-0 bg-slate-900 border-b border-white/5 h-11 shrink-0">
        <div className="flex items-center gap-3">
          <img src="/logo_tita.png" alt="" className="h-6 w-auto bg-white rounded p-0.5" />
          <div className="flex items-center gap-1.5 bg-yellow-500/15 border border-yellow-500/30 rounded-full px-2.5 py-0.5">
            <Zap className="w-3 h-3 text-yellow-400" />
            <span className="text-yellow-300 text-[11px] font-bold uppercase tracking-widest">Modo Recreo</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-slate-500 text-xs tabular-nums font-mono flex items-center gap-1">
            <Clock className="w-3 h-3" />{clock}
          </span>
          <button onClick={() => navigate('/ventas')}
            className="flex items-center gap-1 px-2.5 py-1 bg-slate-700 hover:bg-slate-600 rounded-lg text-xs font-medium transition-colors cursor-pointer">
            <X className="w-3 h-3" />Salir
          </button>
        </div>
      </header>

      {/* ── Cuerpo 3 columnas ── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ══ PANEL IZQUIERDO: ALUMNO (22%) ══ */}
        <aside className="w-52 xl:w-60 bg-slate-900 border-r border-white/5 flex flex-col shrink-0">
          {/* Scan input */}
          <div className="p-2.5 border-b border-white/5">
            <input
              ref={tarjetaRef}
              value={tarjetaInput}
              onChange={e => setTarjetaInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') buscarTarjeta() }}
              placeholder="Escanear tarjeta… (F3)"
              disabled={buscandoTarjeta}
              className="w-full bg-slate-800 border border-slate-700 focus:border-green-500 focus:ring-1 focus:ring-green-500/30 rounded-xl px-3 py-2 text-sm text-white placeholder:text-slate-500 outline-none transition-all"
            />
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {tarjeta ? (
              <>
                {/* Avatar + nombre */}
                <div className="text-center">
                  {tarjeta.hijo_foto ? (
                    <img src={tarjeta.hijo_foto} alt={tarjeta.hijo_nombre}
                      className="w-20 h-20 rounded-full object-cover border-2 border-green-500/50 mx-auto mb-2" />
                  ) : (
                    <div className="w-20 h-20 rounded-full bg-slate-700 border-2 border-green-500/30 flex items-center justify-center mx-auto mb-2">
                      <User className="w-10 h-10 text-slate-500" />
                    </div>
                  )}
                  <p className="text-white font-bold leading-tight">{tarjeta.hijo_nombre}</p>
                  {tarjeta.hijo_grado && <p className="text-slate-400 text-xs mt-0.5">{tarjeta.hijo_grado}</p>}
                </div>

                {/* Saldo */}
                <div className="bg-slate-800 rounded-xl p-3 text-center">
                  <p className="text-slate-500 text-[10px] uppercase tracking-widest font-bold mb-1">Saldo</p>
                  <p className={`text-3xl font-black tabular-nums leading-none ${
                    (saldoDisponible ?? 0) < 5000 ? 'text-red-400' :
                    (saldoDisponible ?? 0) < 15000 ? 'text-yellow-400' : 'text-green-400'
                  }`}>
                    {gs(tarjeta.saldo_disponible || tarjeta.saldo_actual)}
                  </p>
                  {saldoTrasCompra !== null && carrito.length > 0 && (
                    <p className={`text-xs tabular-nums mt-1.5 font-semibold ${saldoTrasCompra < 0 ? 'text-red-400' : 'text-slate-400'}`}>
                      → {gs(saldoTrasCompra)}
                    </p>
                  )}
                </div>

                {/* Estado */}
                <div className="flex items-center gap-2 bg-green-900/25 border border-green-700/30 rounded-lg px-3 py-1.5">
                  <div className="w-2 h-2 rounded-full bg-green-400 shrink-0" />
                  <span className="text-green-300 text-xs font-bold">ACTIVA</span>
                </div>

                {/* Restricciones */}
                {tarjeta.hijo_restricciones?.length > 0 && (
                  <div>
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                      <span className="text-red-400 text-[10px] font-black uppercase tracking-wider">Restricciones</span>
                    </div>
                    <div className="space-y-1">
                      {tarjeta.hijo_restricciones.map(r => (
                        <div key={r.id} className="bg-red-950/50 border border-red-800/40 rounded-lg px-2 py-1 flex items-center gap-1.5">
                          <span className="text-xs">🚫</span>
                          <span className="text-red-300 text-xs leading-tight">{r.descripcion || r.tipo}</span>
                          <span className={`ml-auto text-[9px] font-bold px-1 rounded ${
                            r.severidad === 'CRITICA' ? 'bg-red-700 text-red-100' :
                            r.severidad === 'ALTA' ? 'bg-orange-700 text-orange-100' : 'bg-slate-700 text-slate-300'
                          }`}>{r.severidad}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-40 text-center">
                <CreditCard className="w-12 h-12 text-slate-700 mb-3" />
                <p className="text-slate-500 text-sm font-semibold">Sin alumno</p>
                <p className="text-slate-600 text-xs mt-1">Escanear tarjeta</p>
              </div>
            )}
          </div>
        </aside>

        {/* ══ PANEL CENTRAL: PRODUCTOS (55%) ══ */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Filtros */}
          <div className="px-3 pt-2.5 pb-2 border-b border-white/5 space-y-2 shrink-0">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500 pointer-events-none" />
              <input
                ref={prodSearchRef}
                value={prodSearch}
                onChange={e => setProdSearch(e.target.value)}
                placeholder="Buscar… (F2)"
                className="w-full bg-slate-800 border border-slate-700 focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 rounded-xl pl-8 pr-3 py-1.5 text-sm text-white placeholder:text-slate-500 outline-none transition-all"
              />
            </div>
            <div className="flex gap-1.5 overflow-x-auto scrollbar-hide">
              {['', ...categorias].map(c => (
                <button key={c || '__all__'}
                  onClick={() => setCatFiltro(c)}
                  className={`shrink-0 px-3 py-1 rounded-full text-xs font-bold transition-colors cursor-pointer ${
                    catFiltro === c ? 'bg-white text-slate-900' : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                  }`}>
                  {c || 'Todos'}
                </button>
              ))}
            </div>
          </div>

          {/* Grid de productos */}
          <div className="flex-1 overflow-y-auto p-3">
            {loadingProductos ? (
              <div className="flex items-center justify-center h-full text-slate-500 text-sm">Cargando...</div>
            ) : productosFiltrados.length === 0 ? (
              <div className="flex items-center justify-center h-32 text-slate-600 text-sm">Sin productos</div>
            ) : (
              <div className="grid grid-cols-3 xl:grid-cols-4 gap-2.5">
                {productosFiltrados.slice(0, 12).map((p, idx) => {
                  const meta = catMeta(p.categoria_nombre)
                  const restr = isRestricto(p)
                  const bloqueado = !!restr && (restr.severidad === 'CRITICA' || restr.severidad === 'ALTA')
                  const precio = Number(p.precio_actual) || 0
                  return (
                    <button
                      key={p.id}
                      onClick={() => handleAgregar(p)}
                      disabled={bloqueado}
                      title={bloqueado ? `Restringido: ${restr?.descripcion}` : p.descripcion}
                      className={[
                        'relative flex flex-col items-center justify-center text-center',
                        'rounded-2xl border-2 p-3 min-h-[110px] xl:min-h-[120px]',
                        'transition-all duration-100 select-none',
                        bloqueado
                          ? 'bg-red-950/50 border-red-800/50 opacity-50 cursor-not-allowed'
                          : `${meta.bg} ${meta.border} cursor-pointer hover:brightness-125 hover:scale-[1.03] active:scale-95`,
                      ].join(' ')}
                    >
                      {idx < 9 && (
                        <span className="absolute top-1.5 left-2 text-[10px] font-bold text-white/30">{idx + 1}</span>
                      )}
                      {bloqueado && <span className="absolute top-1.5 right-2 text-base">🚫</span>}
                      <span className="text-3xl mb-1 leading-none">{meta.emoji}</span>
                      <span className="text-white text-[11px] font-semibold leading-tight line-clamp-2 px-1">
                        {p.descripcion}
                      </span>
                      <span className={`text-sm font-black tabular-nums mt-1.5 ${meta.accent}`}>
                        {gs(precio)}
                      </span>
                    </button>
                  )
                })}
              </div>
            )}
          </div>
        </main>

        {/* ══ PANEL DERECHO: CARRITO + COBRO (23%) ══ */}
        <aside className="w-56 xl:w-72 bg-slate-900 border-l border-white/5 flex flex-col shrink-0">
          {/* Header carrito */}
          <div className="px-4 py-2.5 border-b border-white/5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShoppingCart className="w-4 h-4 text-slate-400" />
              <span className="text-sm font-bold text-slate-300">Carrito ({carrito.reduce((s,i)=>s+i.cantidad,0)})</span>
            </div>
            {carrito.length > 0 && (
              <button onClick={() => setCarrito([])} className="text-slate-600 hover:text-red-400 cursor-pointer transition-colors">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Items */}
          <div className="flex-1 overflow-y-auto">
            {carrito.length === 0 ? (
              <div className="flex items-center justify-center h-20">
                <p className="text-slate-700 text-sm">Vacío</p>
              </div>
            ) : (
              <ul className="divide-y divide-white/5">
                {carrito.map(item => {
                  const precio = Number(item.producto.precio_actual) || 0
                  return (
                    <li key={item.producto.id} className="px-3 py-2">
                      <div className="flex items-start gap-1.5">
                        <p className="text-xs text-white font-medium flex-1 leading-tight">{item.producto.descripcion}</p>
                        <button onClick={() => setCarrito(p => p.filter(i => i.producto.id !== item.producto.id))}
                          className="text-slate-600 hover:text-red-400 cursor-pointer shrink-0">
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                      <div className="flex items-center justify-between mt-1.5 gap-2">
                        <div className="flex items-center gap-1">
                          <button onClick={() => handleQuitar(item.producto.id)}
                            className="w-5 h-5 rounded bg-slate-700 hover:bg-slate-600 flex items-center justify-center cursor-pointer">
                            <Minus className="w-2.5 h-2.5" />
                          </button>
                          <span className="text-sm font-black text-white tabular-nums w-5 text-center">{item.cantidad}</span>
                          <button onClick={() => handleAgregar(item.producto)}
                            className="w-5 h-5 rounded bg-slate-700 hover:bg-slate-600 flex items-center justify-center cursor-pointer">
                            <Plus className="w-2.5 h-2.5" />
                          </button>
                        </div>
                        <span className="text-xs font-bold text-emerald-400 tabular-nums">{gs(precio * item.cantidad)}</span>
                      </div>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>

          {/* Total + Cobrar */}
          <div className="border-t border-white/10 p-3 space-y-2">
            <div className="flex items-baseline justify-between">
              <span className="text-slate-400 text-[10px] font-black uppercase tracking-widest">Total</span>
              <span className="text-white text-2xl font-black tabular-nums">{gs(total)}</span>
            </div>

            {/* Método de pago detectado */}
            {tarjeta ? (
              <div className="flex items-center gap-1.5 bg-green-900/20 border border-green-700/25 rounded-lg px-2.5 py-1.5">
                <CreditCard className="w-3 h-3 text-green-400 shrink-0" />
                <span className="text-green-300 text-[11px] font-semibold">Prepago automático</span>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 bg-slate-800/60 border border-slate-700 rounded-lg px-2.5 py-1.5">
                <Banknote className="w-3 h-3 text-slate-500 shrink-0" />
                <span className="text-slate-500 text-[11px]">Escanear tarjeta primero</span>
              </div>
            )}

            {/* COBRAR */}
            <button
              onClick={handleCobrar}
              disabled={carrito.length === 0 || cobrando || !tarjeta}
              className={[
                'w-full py-4 rounded-2xl font-black text-base tracking-wide',
                'flex items-center justify-center gap-2 transition-all duration-150',
                carrito.length > 0 && tarjeta && !cobrando
                  ? 'bg-green-500 hover:bg-green-400 text-white cursor-pointer active:scale-95 shadow-lg shadow-green-500/25'
                  : 'bg-slate-700 text-slate-500 cursor-not-allowed',
              ].join(' ')}
            >
              {cobrando
                ? <><RefreshCw className="w-4 h-4 animate-spin" />Procesando…</>
                : <><CheckCircle className="w-4 h-4" />COBRAR (F9)</>
              }
            </button>

            {/* CANCELAR */}
            <button
              onClick={handleCancelar}
              className="w-full py-2 rounded-xl bg-slate-800 hover:bg-red-900/40 text-slate-500 hover:text-red-300 text-xs font-bold transition-colors cursor-pointer flex items-center justify-center gap-1.5"
            >
              <XCircle className="w-3.5 h-3.5" />
              Cancelar (Esc)
            </button>
          </div>
        </aside>
      </div>

      {/* ── Barra de atajos ── */}
      <footer className="h-8 bg-slate-900 border-t border-white/5 flex items-center px-4 gap-5 text-[10px] text-slate-600 shrink-0">
        {[['F2','Buscar'],['F3','Tarjeta'],['F9','Cobrar'],['Esc','Cancelar'],['1–9','Producto rápido']].map(([k,v]) => (
          <span key={k}>
            <kbd className="bg-slate-700 text-slate-300 rounded px-1.5 py-0.5 font-mono text-[9px] mr-1">{k}</kbd>
            {v}
          </span>
        ))}
        <span className="ml-auto text-slate-700">Modo Recreo v2 — {productosFiltrados.length} productos</span>
      </footer>
    </div>
  )
}
