/**
 * Modo Recreo v4 — POS escolar rápido.
 * Mejoras v4:
 * - Tema claro con alto contraste, tipografía grande y legible
 * - Multi-medio de pago: Prepago, Efectivo, POS, Transferencia
 * - Modal PIN del padre/tutor para autorizar ventas con saldo insuficiente
 * - Calculadora de cambio para cobros en efectivo
 * - Carga dinámica de medios de pago desde /core/medios-pago/
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
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
  MoneyIcon,
  LockKeyIcon,
  BankIcon,
  DeviceMobileIcon,
  CashRegisterIcon,
} from '@phosphor-icons/react'
import api from '../services/api'
import tarjetasService from '../services/tarjetas'
import ventasService from '../services/ventas'
import cajasService from '../services/cajas'
import { useCatalogoStore } from '../store/catalogoStore'
import { useOfflineQueue } from '../hooks/useOfflineQueue'

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

// ─── Metadata de categorías ───────────────────────────────────────────────────
const CAT: Record<string, { emoji: string; bg: string; border: string; accent: string }> = {
  bebidas:   { emoji: '🥤', bg: 'bg-blue-50',   border: 'border-blue-400',    accent: 'text-blue-700' },
  snacks:    { emoji: '🍟', bg: 'bg-orange-50', border: 'border-orange-400',  accent: 'text-orange-700' },
  lácteos:   { emoji: '🥛', bg: 'bg-sky-50',    border: 'border-sky-400',     accent: 'text-sky-700' },
  panaderia: { emoji: '🍞', bg: 'bg-amber-50',  border: 'border-amber-400',   accent: 'text-amber-700' },
  panadería: { emoji: '🍞', bg: 'bg-amber-50',  border: 'border-amber-400',   accent: 'text-amber-700' },
  frutas:    { emoji: '🍎', bg: 'bg-green-50',  border: 'border-green-400',   accent: 'text-green-700' },
  postres:   { emoji: '🍰', bg: 'bg-pink-50',   border: 'border-pink-400',    accent: 'text-pink-700' },
  golosinas: { emoji: '🍬', bg: 'bg-purple-50', border: 'border-purple-400',  accent: 'text-purple-700' },
  alimentos: { emoji: '🍽️', bg: 'bg-emerald-50',border: 'border-emerald-400', accent: 'text-emerald-700' },
}
function catMeta(cat: string) {
  const key = cat.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
  return CAT[key] ?? { emoji: '📦', bg: 'bg-slate-50', border: 'border-slate-300', accent: 'text-slate-600' }
}

const CARD_PREFIX = 'T-'
function detectInputType(value: string): 'card' | 'product' {
  if (!value) return 'product'
  if (value.startsWith(CARD_PREFIX)) return 'card'
  if (!/^\d+$/.test(value)) return 'card'
  return 'product'
}

// ─── Interfaces ───────────────────────────────────────────────────────────────
interface Producto {
  id: number; codigo_barra: string; descripcion: string
  precio_actual: string; categoria_nombre: string
  stock_actual?: number | null
}
interface RestriccionHijo {
  id: number; tipo: string; descripcion: string | null
  severidad: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA'; requiere_autorizacion: boolean
}
interface Tarjeta {
  nro_tarjeta: string; hijo_nombre: string; hijo_foto: string | null
  hijo_grado: string | null; hijo_restricciones: RestriccionHijo[]
  saldo_actual: string; saldo_disponible: string; estado: string
  permite_saldo_negativo: boolean; limite_credito: string
  cliente_id: number; cliente_nombre: string; cliente_ruc: string
}
interface ItemCarrito { producto: Producto; cantidad: number }
interface MedioPagoDB { id: number; descripcion: string; activo: boolean; requiere_validacion: boolean }

type ModoPago = 'PREPAGO' | 'MEDIO'
type Flash = 'none' | 'ok' | 'error' | 'restrict'

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
    if (obj.error)  return String(obj.error)
    const first = Object.values(obj)[0]
    if (Array.isArray(first)) return String(first[0])
    if (typeof first === 'string') return first
  }
  return 'Error al registrar la venta'
}

// ─── Modal PIN ────────────────────────────────────────────────────────────────
interface PinModalProps {
  saldoActual: number
  total: number
  limiteCreditoTarjeta: number
  onConfirm: (pin: string) => void
  onCancel: () => void
  loading: boolean
}
function PinModal({ saldoActual, total, limiteCreditoTarjeta, onConfirm, onCancel, loading }: PinModalProps) {
  const [pin, setPin] = useState('')
  const PIN_LEN = 4

  const deficit = total - saldoActual
  const puedeAutorizar = deficit <= limiteCreditoTarjeta

  const press = (digit: string) => {
    if (digit === '←') { setPin(p => p.slice(0, -1)); return }
    if (pin.length < PIN_LEN) setPin(p => p + digit)
  }

  const confirm = () => {
    if (pin.length === PIN_LEN && puedeAutorizar) onConfirm(pin)
  }

  const keys = ['1','2','3','4','5','6','7','8','9','←','0','✓']

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-[300]" onClick={e => { if (e.target === e.currentTarget) onCancel() }}>
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        {/* Header */}
        <div className="bg-amber-500 px-6 py-4 flex items-center gap-3">
          <LockKeyIcon size={28} weight="fill" className="text-white" />
          <div>
            <p className="text-white font-black text-xl">Autorización requerida</p>
            <p className="text-amber-100 text-sm">PIN del padre/tutor</p>
          </div>
        </div>

        {/* Resumen financiero */}
        <div className="px-6 py-4 bg-amber-50 border-b border-amber-200 grid grid-cols-3 gap-3 text-center">
          <div>
            <p className="text-amber-700 text-xs font-bold uppercase tracking-wide">Saldo actual</p>
            <p className="text-amber-900 text-lg font-black tabular-nums">{gs(saldoActual)}</p>
          </div>
          <div>
            <p className="text-slate-600 text-xs font-bold uppercase tracking-wide">Total compra</p>
            <p className="text-slate-900 text-lg font-black tabular-nums">{gs(total)}</p>
          </div>
          <div>
            <p className={`text-xs font-bold uppercase tracking-wide ${puedeAutorizar ? 'text-red-600' : 'text-red-700'}`}>Déficit</p>
            <p className={`text-lg font-black tabular-nums ${puedeAutorizar ? 'text-red-600' : 'text-red-700'}`}>{gs(deficit)}</p>
          </div>
        </div>

        {!puedeAutorizar && (
          <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-300 rounded-xl text-center">
            <p className="text-red-700 font-bold text-sm">Excede el límite de crédito ({gs(limiteCreditoTarjeta)})</p>
            <p className="text-red-600 text-xs mt-0.5">No es posible autorizar esta venta</p>
          </div>
        )}

        {puedeAutorizar && (
          <div className="px-6 pt-5 pb-2">
            {/* Dots */}
            <div className="flex justify-center gap-4 mb-6">
              {Array.from({ length: PIN_LEN }).map((_, i) => (
                <div key={i} className={`w-5 h-5 rounded-full border-2 transition-all ${
                  i < pin.length ? 'bg-amber-500 border-amber-500 scale-110' : 'bg-white border-slate-300'
                }`} />
              ))}
            </div>

            {/* Numpad */}
            <div className="grid grid-cols-3 gap-3">
              {keys.map(k => {
                const isBack = k === '←'
                const isOk = k === '✓'
                const disabled = isOk ? (pin.length !== PIN_LEN || loading) : (isBack ? pin.length === 0 : false)
                return (
                  <button
                    key={k}
                    onClick={() => { if (!loading) { if (isOk) { confirm() } else { press(k) } } }}
                    disabled={disabled}
                    className={[
                      'h-14 rounded-2xl text-xl font-black transition-all select-none',
                      isOk
                        ? 'bg-green-500 text-white hover:bg-green-600 disabled:opacity-40'
                        : isBack
                          ? 'bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-30'
                          : 'bg-slate-100 text-slate-900 hover:bg-amber-50 active:bg-amber-100',
                      !disabled && 'active:scale-95 cursor-pointer',
                      disabled && 'cursor-not-allowed',
                    ].join(' ')}
                  >
                    {loading && isOk ? <SpinnerIcon size={20} className="animate-spin mx-auto" /> : k}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="px-6 py-4 flex gap-3">
          <button
            onClick={onCancel}
            disabled={loading}
            className="flex-1 py-3 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-base transition-colors cursor-pointer disabled:opacity-50"
          >
            Cancelar
          </button>
          {puedeAutorizar && (
            <button
              onClick={confirm}
              disabled={pin.length !== PIN_LEN || loading}
              className="flex-1 py-3 rounded-2xl bg-amber-500 hover:bg-amber-600 text-white font-black text-base transition-colors cursor-pointer disabled:opacity-40 flex items-center justify-center gap-2"
            >
              {loading
                ? <><SpinnerIcon size={18} className="animate-spin" />Verificando…</>
                : <><CheckCircleIcon size={18} weight="fill" />Autorizar</>
              }
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Componente principal ─────────────────────────────────────────────────────
export default function ModoRecreo() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { getProductos, getCategorias } = useCatalogoStore()

  // Conectividad + cola offline
  const { isOnline, pendingCount, syncing, syncNow, enqueue } = useOfflineQueue()
  useEffect(() => {
    const offlineToastId = 'offline-warning'
    if (!isOnline) {
      toast.error('Sin conexión — ventas se guardan offline', { id: offlineToastId, duration: Infinity })
    } else {
      toast.dismiss(offlineToastId)
      if (pendingCount > 0) {
        toast.success(`Conexión restaurada — sincronizando ${pendingCount} venta(s)...`)
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOnline])

  // Caja abierta
  interface CierreCajaInfo { id: number; caja_nombre: string; monto_inicial: string; fecha_apertura: string }
  const [cierreCaja, setCierreCaja] = useState<CierreCajaInfo | null | false>(null) // null=cargando, false=no hay caja

  // Datos
  const [productos, setProductos] = useState<Producto[]>([])
  const [loadingProductos, setLoadingProductos] = useState(true)
  const [categorias, setCategorias] = useState<string[]>([])
  const [mediosPago, setMediosPago] = useState<MedioPagoDB[]>([])

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

  // Modo de pago
  const [modoPago, setModoPago] = useState<ModoPago>('PREPAGO')
  const [medioPagoSelId, setMedioPagoSelId] = useState<number | null>(null)
  const [montoEfectivo, setMontoEfectivo] = useState('')
  const [referencia, setReferencia] = useState('')

  // PIN modal
  const [showPin, setShowPin] = useState(false)
  const [pinLoading, setPinLoading] = useState(false)

  // Input con foco activo
  const [focusedInput, setFocusedInput] = useState<'scanner' | 'search' | 'efectivo' | null>(null)

  // Refs
  const scannerRef = useRef<HTMLInputElement>(null)
  const prodSearchRef = useRef<HTMLInputElement>(null)
  const efectivoRef = useRef<HTMLInputElement>(null)
  const flashTimer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const cobrandoRef = useRef(false)
  const productosFiltradosRef = useRef<Producto[]>([])
  const handleAgregarRef = useRef<(p: Producto) => void>(() => {})
  const handleCobrarRef = useRef<() => void>(() => {})
  const handleCancelarRef = useRef<() => void>(() => {})
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
    Promise.all([
      getProductos(),
      getCategorias(),
      api.get('/core/medios-pago/', { params: { activo: true } }),
    ])
      .then(([prods, cats, mpRes]) => {
        setProductos(prods as Producto[])
        setCategorias(cats.map((c: { nombre: string }) => c.nombre))
        const mp: MedioPagoDB[] = (mpRes.data.results ?? mpRes.data) as MedioPagoDB[]
        setMediosPago(mp.filter(m => m.activo))
      })
      .catch(() => toast.error('Error al cargar datos'))
      .finally(() => setLoadingProductos(false))

    // Verificar caja abierta (separado para no bloquear la carga del catálogo)
    cajasService.getMiCaja<CierreCajaInfo>()
      .then(res => setCierreCaja(res.data ?? false))
      .catch(() => setCierreCaja(false))
  }, [getProductos, getCategorias])

  // Auto-foco persistente en scanner
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
      if (!inInput && /^[1-9]$/.test(e.key)) {
        const p = productosFiltradosRef.current[parseInt(e.key) - 1]
        if (p) handleAgregarRef.current(p)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [carrito])

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
    // eslint-disable-next-line react-hooks/refs
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

  const vuelto = useMemo(() => {
    const recibido = parseFloat(montoEfectivo.replace(/\./g, '').replace(',', '.')) || 0
    return recibido - total
  }, [montoEfectivo, total])

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
      const { data } = await tarjetasService.buscar<Tarjeta>(nro)
      const found = (data.results ?? []).find((t) => t.nro_tarjeta === nro)
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
    // Validar saldo solo en modo PREPAGO
    if (modoPago === 'PREPAGO' && saldoDisponible !== null && !tarjeta?.permite_saldo_negativo) {
      const nuevoTotal = total + (Number(producto.precio_actual) || 0)
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
    setAddedProductId(producto.id)
    clearTimeout(addedTimer.current)
    addedTimer.current = setTimeout(() => setAddedProductId(null), 200)
  }, [isRestricto, saldoDisponible, tarjeta, total, modoPago])

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

  // ─── Ejecución real del cobro ─────────────────────────────────────────────
  const ejecutarCobro = useCallback(async (pinAutorizacion?: string) => {
    if (cobrandoRef.current || carrito.length === 0 || !tarjeta) return
    cobrandoRef.current = true
    setCobrando(true)
    const inicio = ventaStartTime.current || performance.now()

    try {
      const payload: Record<string, unknown> = {
        cliente: tarjeta.cliente_id,
        tipo: 'CONTADO',
        items: carrito.map(i => ({
          producto: i.producto.id,
          cantidad: i.cantidad,
          precio_unitario: Number(i.producto.precio_actual) || 0,
          iva_10: 0, iva_5: 0, monto_exenta: 0,
        })),
      }

      if (modoPago === 'PREPAGO') {
        payload.tarjeta = tarjeta.nro_tarjeta
        payload.medio_pago = null
        if (pinAutorizacion) payload.pin_autorizacion = pinAutorizacion
      } else {
        payload.tarjeta = null
        payload.medio_pago = medioPagoSelId
        if (referencia.trim()) payload.referencia = referencia.trim()
      }

      if (!navigator.onLine) {
        await enqueue({
          url:     '/api/v1/ventas/ventas/',
          method:  'POST',
          body:    JSON.stringify(payload),
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('access_token') ?? ''}`,
          },
        })
      } else {
        await ventasService.crear(payload, 6000)
      }
      sfx.ok()
      addSales(carrito.map(i => i.producto.id))
      setSalesMap(getSalesMap())
      const tiempoMs = performance.now() - inicio
      updateDailyStats(tiempoMs)
      setDailyStats(getDailyStats())
      clearTimeout(flashTimer.current)
      setFlash('ok')
      setFlashMsg(
        navigator.onLine
          ? `✅  ${tarjeta.hijo_nombre}  —  ${gs(total)}`
          : `📶  ${tarjeta.hijo_nombre}  —  guardado offline`,
      )
      flashTimer.current = setTimeout(() => {
        setFlash('none')
        setCarrito([])
        setTarjeta(null)
        setMontoEfectivo('')
        setReferencia('')
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
  }, [carrito, tarjeta, total, modoPago, medioPagoSelId, enqueue])

  // ─── Cobrar ───────────────────────────────────────────────────────────────
  const handleCobrar = useCallback(async () => {
    if (cobrandoRef.current || carrito.length === 0) return
    if (!tarjeta) { toast.error('Escanear tarjeta del alumno'); scannerRef.current?.focus(); return }

    if (modoPago === 'MEDIO' && !medioPagoSelId) {
      toast.error('Seleccione un medio de pago'); return
    }

    if (modoPago === 'PREPAGO' && !tarjeta.permite_saldo_negativo) {
      const saldoAct = Number(tarjeta.saldo_actual) || 0
      if (total > saldoAct) {
        // Insuficiente saldo — pedir PIN del padre
        setShowPin(true)
        return
      }
    }

    await ejecutarCobro()
  }, [carrito, tarjeta, total, modoPago, medioPagoSelId, ejecutarCobro])

  // ─── Cancelar ─────────────────────────────────────────────────────────────
  const handleCancelar = useCallback(() => {
    clearTimeout(flashTimer.current)
    setFlash('none'); setCarrito([]); setTarjeta(null)
    setTarjetaInput(''); setProdSearch('')
    setMontoEfectivo(''); setReferencia(''); setShowPin(false)
    ventaStartTime.current = 0
    setTimeout(() => scannerRef.current?.focus(), 60)
  }, [])

  // Sincronizar refs (useEffect to avoid ref mutation during render)
  useEffect(() => {
    handleAgregarRef.current  = handleAgregar
    handleCobrarRef.current   = handleCobrar
    handleCancelarRef.current = handleCancelar
  })

  // Procesar escaneo automático (Enter)
  const processScan = useCallback(async (value: string) => {
    if (!value.trim()) return
    const trimmed = value.trim()
    setTarjetaInput('')
    if (detectInputType(trimmed) === 'card') {
      // Tiene prefijo T- o contiene caracteres no numéricos → definitivamente tarjeta
      if (tarjeta) setCarrito([])
      await buscarTarjeta(trimmed)
    } else {
      // Todo dígitos: primero buscamos en productos locales (O(1), sin red)
      const prod = productos.find(p => p.codigo_barra === trimmed)
      if (prod) {
        if (!tarjeta) {
          sfx.error(); toast.error('Escanee una tarjeta primero')
          setTimeout(() => scannerRef.current?.focus(), 100)
          return
        }
        const now = Date.now()
        if (lastScannedProduct.current?.id === prod.id && (now - lastScannedProduct.current.time) < 1000) {
          // incremento manejado por handleAgregar
        }
        lastScannedProduct.current = { id: prod.id, time: now }
        handleAgregarRef.current(prod)
        setTimeout(() => scannerRef.current?.focus(), 30)
      } else {
        // No es un producto conocido → intentar como número de tarjeta
        if (tarjeta) setCarrito([])
        await buscarTarjeta(trimmed)
      }
    }
  }, [tarjeta, productos, buscarTarjeta])

  // ─── Icono por descripción de medio de pago ───────────────────────────────
  const iconMedio = (desc: string) => {
    const d = desc.toLowerCase()
    if (d.includes('pos') || d.includes('tarjet') || d.includes('débito') || d.includes('crédito'))
      return <DeviceMobileIcon size={18} weight="fill" />
    if (d.includes('transfer') || d.includes('banco'))
      return <BankIcon size={18} weight="fill" />
    return <MoneyIcon size={18} weight="fill" />
  }

  // ─── JSX ──────────────────────────────────────────────────────────────────
  const flashCfg = {
    ok:       { overlay: 'bg-green-500/20', card: 'bg-white border-green-500 shadow-green-200' },
    error:    { overlay: 'bg-red-500/20',   card: 'bg-white border-red-500 shadow-red-200' },
    restrict: { overlay: 'bg-red-600/25',   card: 'bg-white border-red-600 shadow-red-200' },
    none:     { overlay: '', card: '' },
  }[flash]

  const avgTime = dailyStats.count > 0 ? (dailyStats.totalTime / dailyStats.count / 1000).toFixed(1) : '—'

  const medioPagoSeleccionado = mediosPago.find(m => m.id === medioPagoSelId) ?? null

  const referenciaRequerida = modoPago === 'MEDIO' && (medioPagoSeleccionado?.requiere_validacion ?? false)
  // isOnline ya no bloquea: las ventas offline se encolan en IndexedDB
  const canCobrar = carrito.length > 0 && !cobrando && tarjeta &&
    (modoPago === 'PREPAGO' || (modoPago === 'MEDIO' && medioPagoSelId !== null)) &&
    (!referenciaRequerida || referencia.trim().length > 0)

  // Pantalla de bloqueo: sin caja abierta
  if (cierreCaja === false) {
    return (
      <div className="fixed inset-0 bg-slate-100 flex flex-col items-center justify-center" style={{ zIndex: 100 }}>
        <div className="bg-white rounded-3xl shadow-2xl p-12 max-w-md w-full mx-4 text-center">
          <div className="w-24 h-24 rounded-full bg-orange-100 flex items-center justify-center mx-auto mb-6">
            <CashRegisterIcon size={52} weight="fill" className="text-orange-500" />
          </div>
          <h2 className="text-3xl font-black text-slate-900 mb-2">Caja no iniciada</h2>
          <p className="text-slate-500 text-lg mb-8">{t('pos.cashRegister')}</p>
          <div className="flex flex-col gap-3">
            <button
              onClick={() => navigate('/cajas')}
              className="w-full py-4 bg-orange-500 hover:bg-orange-600 text-white font-black text-lg rounded-2xl transition-colors cursor-pointer"
            >
              Ir a Cajas
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="w-full py-3 bg-slate-100 hover:bg-slate-200 text-slate-600 font-bold rounded-2xl transition-colors cursor-pointer"
            >
              Volver al inicio
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Cargando caja
  if (cierreCaja === null) {
    return (
      <div className="fixed inset-0 bg-slate-100 flex items-center justify-center" style={{ zIndex: 100 }}>
        <SpinnerIcon size={48} className="animate-spin text-slate-400" />
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-slate-100 text-slate-900 flex flex-col overflow-hidden" style={{ zIndex: 100 }} translate="no">

      {/* ── PIN Modal ── */}
      {showPin && tarjeta && (
        <PinModal
          saldoActual={Number(tarjeta.saldo_actual) || 0}
          total={total}
          limiteCreditoTarjeta={Number(tarjeta.limite_credito) || 0}
          loading={pinLoading}
          onCancel={() => { setShowPin(false); setTimeout(() => scannerRef.current?.focus(), 60) }}
          onConfirm={async (pin) => {
            setPinLoading(true)
            try {
              await ejecutarCobro(pin)
              setShowPin(false)
            } catch {
              // error ya mostrado por ejecutarCobro
            } finally {
              setPinLoading(false)
            }
          }}
        />
      )}

      {/* ── Flash overlay ── */}
      {flash !== 'none' && (
        <div className={`absolute inset-0 flex items-center justify-center pointer-events-none ${flashCfg.overlay}`} style={{ zIndex: 200 }}>
          <div className={`border-4 rounded-3xl px-16 py-10 text-center shadow-2xl ${flashCfg.card}`}>
            <p className="text-5xl font-black text-slate-900">{flashMsg}</p>
            {flash === 'ok' && saldoTrasCompra !== null && modoPago === 'PREPAGO' && (
              <p className="text-slate-500 text-2xl mt-3 tabular-nums">Saldo restante: {gs(saldoTrasCompra)}</p>
            )}
          </div>
        </div>
      )}

      {/* ── Offline banner ── */}
      {!isOnline && (
        <div className="flex items-center justify-center gap-2 bg-red-600 text-white text-sm font-bold py-1.5 px-4 shrink-0">
          <WarningIcon size={16} weight="fill" />
          SIN CONEXIÓN — los cobros están deshabilitados hasta restaurar la red
        </div>
      )}

      {/* ── Header ── */}
      <header className="flex items-center justify-between px-5 py-2 bg-white border-b-2 border-slate-200 shadow-sm h-16 shrink-0">
        <div className="flex items-center gap-4">
          <img src="/logo_tita.png" alt="" className="h-9 w-auto rounded" />
          <div className="flex items-center gap-2 bg-yellow-100 border border-yellow-300 rounded-full px-4 py-1.5">
            <LightningIcon size={16} weight="fill" className="text-yellow-500" />
            <span className="text-yellow-700 text-sm font-black uppercase tracking-widest">{t('pos.title')}</span>
          </div>
          <div className="flex items-center gap-4 ml-2 text-sm text-slate-500">
            <span className="flex items-center gap-1.5"><ClockIcon size={15} weight="fill" className="text-slate-400" />{clock}</span>
            <span className="flex items-center gap-1.5 text-emerald-700 font-semibold">
              <CashRegisterIcon size={15} weight="fill" className="text-emerald-500" />
              {cierreCaja.caja_nombre}
            </span>
            <span>{t('pos.todaySales')}: <strong className="text-slate-800">{dailyStats.count}</strong></span>
            <span>Promedio: <strong className="text-slate-800">{dailyStats.count > 0 ? `${avgTime}s` : '—'}</strong></span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {/* Badge de ventas offline pendientes */}
          {pendingCount > 0 && (
            <button
              onClick={syncNow}
              disabled={syncing || !isOnline}
              title={isOnline ? 'Sincronizar ventas offline' : 'Sin conexión — se sincronizarán al reconectar'}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-100 border border-amber-300 text-amber-800 rounded-lg text-xs font-bold transition-colors cursor-pointer hover:bg-amber-200 disabled:opacity-60"
            >
              {syncing
                ? <SpinnerIcon size={13} className="animate-spin" />
                : <WarningIcon size={13} weight="fill" />}
              {pendingCount} venta{pendingCount !== 1 ? 's' : ''} offline
            </button>
          )}
          <div className="flex items-center gap-3 text-xs text-slate-500">
            {[['F2','Buscar'],['F3','Escanear'],['F9','Cobrar'],['Esc','Cancelar'],['±','Cant']].map(([k, l]) => (
              <span key={k}>
                <kbd className={`rounded px-1.5 py-0.5 font-mono mr-1 text-[11px] ${k === 'F9' ? 'bg-green-100 text-green-700 border border-green-300' : 'bg-slate-100 text-slate-600 border border-slate-200'}`}>{k}</kbd>
                {l}
              </span>
            ))}
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-red-50 text-slate-600 hover:text-red-600 rounded-lg text-sm font-medium transition-colors cursor-pointer border border-slate-200"
          >
            <XIcon size={14} weight="fill" />Salir
          </button>
        </div>
      </header>

      {/* ── Cuerpo 3 columnas ── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ══ PANEL IZQUIERDO: ALUMNO ══ */}
        <aside className="w-80 bg-white border-r-2 border-slate-200 flex flex-col shrink-0">

          {/* Input scanner */}
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
                'w-full bg-slate-50 border-2 rounded-xl px-4 py-3 text-base text-slate-900 placeholder:text-slate-400 outline-none transition-all',
                focusedInput === 'scanner'
                  ? 'border-blue-500 ring-4 ring-blue-400/20'
                  : 'border-slate-300',
              ].join(' ')}
            />
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {tarjeta ? (
              <>
                {/* Foto y nombre */}
                <div className="text-center">
                  {tarjeta.hijo_foto ? (
                    <img src={tarjeta.hijo_foto} alt={tarjeta.hijo_nombre}
                      className="w-32 h-32 rounded-full object-cover border-4 border-blue-400 mx-auto mb-3 shadow-md" />
                  ) : (
                    <div className="w-32 h-32 rounded-full bg-slate-100 border-4 border-blue-300 flex items-center justify-center mx-auto mb-3">
                      <UserIcon size={64} weight="fill" className="text-slate-400" />
                    </div>
                  )}
                  <p className="text-2xl font-black text-slate-900 leading-tight">{tarjeta.hijo_nombre}</p>
                  {tarjeta.hijo_grado && <p className="text-slate-500 text-base mt-0.5">{tarjeta.hijo_grado}</p>}
                  <p className="text-slate-300 text-xs mt-1 font-mono tracking-wider">{tarjeta.nro_tarjeta}</p>
                </div>

                {/* Restricciones */}
                {tarjeta.hijo_restricciones?.length > 0 && (
                  <div className="bg-red-50 border-2 border-red-300 rounded-xl p-3 space-y-2">
                    <div className="flex items-center gap-1.5">
                      <WarningIcon size={15} weight="fill" className="text-red-500 shrink-0" />
                      <span className="text-red-700 text-sm font-black uppercase tracking-wide">
                        {tarjeta.hijo_restricciones.length} Restricción{tarjeta.hijo_restricciones.length > 1 ? 'es' : ''}
                      </span>
                    </div>
                    {tarjeta.hijo_restricciones.map(r => (
                      <div key={r.id} className="flex items-center gap-2">
                        <span className="text-sm">🚫</span>
                        <span className="text-red-700 text-sm font-semibold leading-tight flex-1">{r.descripcion || r.tipo}</span>
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0 ${
                          r.severidad === 'CRITICA' ? 'bg-red-600 text-white' :
                          r.severidad === 'ALTA' ? 'bg-orange-500 text-white' : 'bg-slate-200 text-slate-600'
                        }`}>{r.severidad}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Saldo */}
                <div className={`rounded-2xl p-4 border-2 ${
                  (saldoDisponible ?? 0) < 5000 ? 'bg-red-50 border-red-300' :
                  (saldoDisponible ?? 0) < 15000 ? 'bg-yellow-50 border-yellow-300' : 'bg-green-50 border-green-300'
                }`}>
                  <div className="flex items-baseline justify-between mb-1">
                    <p className="text-slate-500 text-xs uppercase tracking-widest font-bold">Saldo actual</p>
                    <p className={`text-3xl font-black tabular-nums leading-none ${
                      (saldoDisponible ?? 0) < 5000 ? 'text-red-600' :
                      (saldoDisponible ?? 0) < 15000 ? 'text-yellow-600' : 'text-green-600'
                    }`}>
                      {gs(tarjeta.saldo_disponible || tarjeta.saldo_actual)}
                    </p>
                  </div>
                  {carrito.length > 0 && saldoTrasCompra !== null && modoPago === 'PREPAGO' && (
                    <div className="flex items-baseline justify-between border-t border-current/20 pt-1.5 mt-1.5">
                      <p className="text-slate-500 text-xs uppercase tracking-widest font-bold">Tras compra</p>
                      <p className={`text-xl font-black tabular-nums ${saldoTrasCompra < 0 ? 'text-red-600' : 'text-slate-600'}`}>
                        {gs(saldoTrasCompra)}
                      </p>
                    </div>
                  )}
                  {Number(tarjeta.limite_credito) > 0 && (
                    <p className="text-xs text-slate-400 mt-1.5">
                      Crédito disponible: <span className="font-bold">{gs(tarjeta.limite_credito)}</span>
                    </p>
                  )}
                </div>

                {/* Estado */}
                <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg px-4 py-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-green-500 shrink-0" />
                  <span className="text-green-700 text-sm font-bold">Tarjeta ACTIVA</span>
                </div>

                {/* Padre */}
                <div className="bg-slate-50 border border-slate-200 rounded-lg px-4 py-2.5">
                  <p className="text-slate-400 text-xs uppercase tracking-wide font-bold mb-0.5">Padre/Tutor</p>
                  <p className="text-slate-800 text-sm font-semibold leading-tight">{tarjeta.cliente_nombre}</p>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center h-56 text-center">
                <CreditCardIcon size={72} weight="fill" className="text-slate-200 mb-4" />
                <p className="text-slate-600 text-xl font-bold">Sin alumno</p>
                <p className="text-slate-400 text-base mt-1">Escanear tarjeta para comenzar</p>
              </div>
            )}
          </div>
        </aside>

        {/* ══ PANEL CENTRAL: PRODUCTOS ══ */}
        <main className="flex-1 flex flex-col overflow-hidden bg-slate-50">
          <div className="px-4 pt-3 pb-2 border-b border-slate-200 space-y-3 shrink-0 bg-white shadow-sm">
            {/* Buscador */}
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
                  'w-full bg-slate-50 border-2 rounded-xl pl-11 pr-4 py-3 text-base text-slate-900 placeholder:text-slate-400 outline-none transition-all',
                  focusedInput === 'search'
                    ? 'border-blue-500 ring-4 ring-blue-400/20'
                    : 'border-slate-300',
                ].join(' ')}
              />
            </div>
            {/* Filtros de categoría */}
            <div className="flex gap-2 overflow-x-auto pb-0.5">
              {['', ...categorias].map(c => (
                <button key={c || '__all__'}
                  onClick={() => setCatFiltro(c)}
                  className={`shrink-0 px-4 py-1.5 rounded-full text-sm font-bold transition-colors cursor-pointer ${
                    catFiltro === c
                      ? 'bg-slate-800 text-white'
                      : 'bg-white text-slate-600 border border-slate-300 hover:bg-slate-50'
                  }`}>
                  {c || 'Todos'}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Favoritos */}
            {favoritos.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-base">🔥</span>
                  <span className="text-slate-500 text-xs font-bold uppercase tracking-wider">Más vendidos</span>
                </div>
                <div className="flex gap-3 overflow-x-auto pb-1">
                  {favoritos.map(p => {
                    const meta = catMeta(p.categoria_nombre)
                    const restr = isRestricto(p)
                    const bloqueado = !!restr && (restr.severidad === 'CRITICA' || restr.severidad === 'ALTA')
                    return (
                      <button key={p.id} onClick={() => handleAgregar(p)} disabled={bloqueado}
                        className={[
                          'relative flex flex-col items-center justify-center shrink-0 w-36 h-28 rounded-2xl border-2 p-2 transition-all duration-100',
                          bloqueado
                            ? 'bg-red-50 border-red-200 opacity-50 cursor-not-allowed'
                            : `${meta.bg} ${meta.border} cursor-pointer hover:shadow-md hover:scale-105 active:scale-95`,
                        ].join(' ')}
                      >
                        {p.stock_actual != null && p.stock_actual <= 3 && (
                          <span className="absolute top-1 right-1 text-[9px] font-bold text-red-600 bg-red-100 rounded px-1">
                            {p.stock_actual === 0 ? 'AGOTADO' : `${p.stock_actual}u`}
                          </span>
                        )}
                        <span className="text-3xl mb-0.5">{meta.emoji}</span>
                        <span className="text-xs text-slate-700 font-semibold leading-tight line-clamp-1 text-center">{p.descripcion}</span>
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
                    <button key={p.id} onClick={() => handleAgregar(p)} disabled={bloqueado}
                      className={[
                        'relative flex flex-col items-center justify-center text-center rounded-2xl border-2 p-3 min-h-[150px] transition-all duration-100 select-none',
                        bloqueado
                          ? 'bg-red-50 border-red-200 opacity-50 cursor-not-allowed'
                          : `${meta.bg} ${meta.border} cursor-pointer hover:shadow-md hover:scale-[1.03] active:scale-95`,
                        isAdded && 'ring-4 ring-blue-400 scale-105',
                      ].join(' ')}
                    >
                      {idx < 9 && (
                        <span className="absolute top-2 left-2.5 text-xs font-bold text-slate-300">{idx + 1}</span>
                      )}
                      {bloqueado && <span className="absolute top-2 right-2 text-sm">🚫</span>}
                      {p.stock_actual != null && !bloqueado && (
                        <span className={`absolute bottom-1.5 right-2 text-[10px] font-bold px-1.5 py-0.5 rounded tabular-nums ${
                          p.stock_actual === 0     ? 'bg-red-600 text-white' :
                          p.stock_actual <= 3      ? 'bg-red-100 text-red-700' :
                          p.stock_actual <= 10     ? 'bg-orange-100 text-orange-700' :
                          'text-slate-200'
                        }`}>
                          {p.stock_actual === 0 ? 'AGOTADO' : `${p.stock_actual}u`}
                        </span>
                      )}
                      <span className="text-4xl mb-1.5">{meta.emoji}</span>
                      <span className={`text-lg font-black tabular-nums ${meta.accent}`}>{gs(p.precio_actual)}</span>
                      <span className="text-slate-700 text-sm font-medium leading-tight line-clamp-2 mt-1 px-1">
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
        <aside className="w-96 bg-white border-l-2 border-slate-200 flex flex-col shrink-0">

          {/* Header carrito */}
          <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShoppingCartIcon size={22} weight="fill" className="text-slate-600" />
              <span className="text-lg font-black text-slate-800">
                {carrito.reduce((s, i) => s + i.cantidad, 0)} productos
              </span>
            </div>
            {carrito.length > 0 && (
              <button onClick={() => setCarrito([])} className="text-slate-400 hover:text-red-500 transition-colors p-1">
                <XIcon size={20} weight="fill" />
              </button>
            )}
          </div>

          {/* Selector de medio de pago */}
          <div className="px-4 py-3 border-b border-slate-100 bg-slate-50">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Medio de pago</p>
            <div className="flex flex-wrap gap-2">
              {/* PREPAGO */}
              <button
                onClick={() => { setModoPago('PREPAGO'); setMedioPagoSelId(null) }}
                className={[
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-bold border-2 transition-all cursor-pointer',
                  modoPago === 'PREPAGO'
                    ? 'bg-blue-600 border-blue-600 text-white shadow-sm'
                    : 'bg-white border-slate-300 text-slate-600 hover:border-blue-300',
                ].join(' ')}
              >
                <CreditCardIcon size={15} weight="fill" />
                Prepago
              </button>
              {/* Medios dinámicos */}
              {mediosPago.map(mp => (
                <button key={mp.id}
                  onClick={() => { setModoPago('MEDIO'); setMedioPagoSelId(mp.id) }}
                  className={[
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-bold border-2 transition-all cursor-pointer',
                    modoPago === 'MEDIO' && medioPagoSelId === mp.id
                      ? 'bg-emerald-600 border-emerald-600 text-white shadow-sm'
                      : 'bg-white border-slate-300 text-slate-600 hover:border-emerald-300',
                  ].join(' ')}
                >
                  {iconMedio(mp.descripcion)}
                  {mp.descripcion}
                </button>
              ))}
            </div>
          </div>

          {/* Lista del carrito */}
          <div className="flex-1 overflow-y-auto">
            {carrito.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center px-4 py-6">
                <ShoppingCartIcon size={48} weight="fill" className="text-slate-200 mb-3" />
                <p className="text-slate-500 text-base font-semibold mb-1">Sin productos</p>
                <p className="text-slate-400 text-sm">Escanear tarjeta y seleccionar productos</p>
                {dailyStats.count > 0 && (
                  <div className="mt-6 w-full border-t border-slate-100 pt-4 space-y-2">
                    <div className="flex justify-between text-sm px-4">
                      <span className="text-slate-400">{t('pos.todaySales')}</span>
                      <span className="font-bold text-slate-700">{dailyStats.count}</span>
                    </div>
                    <div className="flex justify-between text-sm px-4">
                      <span className="text-slate-400">Tiempo promedio</span>
                      <span className="font-bold text-slate-700">{avgTime}s</span>
                    </div>
                  </div>
                )}
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
                          className="text-slate-300 hover:text-red-500 transition-colors shrink-0 p-0.5">
                          <XIcon size={16} weight="fill" />
                        </button>
                      </div>
                      <div className="flex items-center justify-between mt-2">
                        <div className="flex items-center gap-2">
                          <button onClick={() => handleQuitar(item.producto.id)}
                            className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600 cursor-pointer">
                            <MinusIcon size={15} weight="fill" />
                          </button>
                          <span className="text-xl font-black text-slate-900 tabular-nums w-7 text-center">{item.cantidad}</span>
                          <button onClick={() => handleAgregar(item.producto)}
                            className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600 cursor-pointer">
                            <PlusIcon size={15} weight="fill" />
                          </button>
                        </div>
                        <span className="text-base font-bold text-emerald-700 tabular-nums">{gs(precio * item.cantidad)}</span>
                      </div>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>

          {/* Footer: total + pago + botones */}
          <div className="border-t-2 border-slate-200 p-4 space-y-3 bg-white">

            {/* Total */}
            <div className="flex items-baseline justify-between">
              <span className="text-slate-500 text-sm font-black uppercase tracking-widest">Total</span>
              <span className="text-slate-900 text-4xl font-black tabular-nums">{gs(total)}</span>
            </div>

            {/* Restante (modo prepago) */}
            {tarjeta && modoPago === 'PREPAGO' && (
              <div className="flex items-baseline justify-between text-sm -mt-1">
                <span className="text-slate-400">Saldo tras cobro</span>
                <span className={`font-bold tabular-nums ${(saldoTrasCompra ?? saldoDisponible ?? 0) < 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                  {gs(saldoTrasCompra ?? saldoDisponible ?? 0)}
                </span>
              </div>
            )}

            {/* Campo efectivo + vuelto */}
            {modoPago === 'MEDIO' && medioPagoSeleccionado &&
             medioPagoSeleccionado.descripcion.toLowerCase().includes('efectivo') && (
              <div className="space-y-2 bg-emerald-50 border border-emerald-200 rounded-xl p-3">
                <div className="flex items-center gap-2">
                  <MoneyIcon size={16} weight="fill" className="text-emerald-600" />
                  <p className="text-emerald-700 text-sm font-bold">Monto recibido</p>
                </div>
                <input
                  ref={efectivoRef}
                  value={montoEfectivo}
                  onChange={e => setMontoEfectivo(e.target.value.replace(/[^\d]/g, ''))}
                  onFocus={() => setFocusedInput('efectivo')}
                  onBlur={() => setFocusedInput(null)}
                  placeholder="0"
                  inputMode="numeric"
                  className="w-full bg-white border-2 border-emerald-300 rounded-lg px-3 py-2 text-xl font-black text-slate-900 tabular-nums text-right outline-none focus:border-emerald-500"
                />
                {montoEfectivo && (
                  <div className="flex justify-between items-center pt-1">
                    <span className="text-emerald-700 text-sm font-bold">Vuelto:</span>
                    <span className={`text-xl font-black tabular-nums ${vuelto < 0 ? 'text-red-600' : 'text-emerald-700'}`}>
                      {gs(vuelto)}
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* Nro. de transacción (POS / Transferencia / cualquier medio con requiere_validacion) */}
            {modoPago === 'MEDIO' && medioPagoSeleccionado?.requiere_validacion && (
              <div className="space-y-1.5 bg-blue-50 border border-blue-200 rounded-xl p-3">
                <label className="flex items-center gap-2 text-blue-700 text-sm font-bold">
                  <CreditCardIcon size={15} weight="fill" />
                  Nro. de transacción
                  <span className="text-red-500 text-xs font-black">*</span>
                </label>
                <input
                  value={referencia}
                  onChange={e => setReferencia(e.target.value)}
                  placeholder="Ingrese el código generado por el terminal"
                  autoComplete="off"
                  className="w-full bg-white border-2 border-blue-300 rounded-lg px-3 py-2 text-base font-mono font-semibold text-slate-900 outline-none focus:border-blue-500 placeholder:text-slate-300 placeholder:font-normal tracking-wider uppercase"
                  onKeyDown={e => { if (e.key === 'Enter') e.currentTarget.blur() }}
                />
                {referencia.trim() && (
                  <p className="text-blue-600 text-xs font-mono tracking-widest uppercase">{referencia.trim()}</p>
                )}
              </div>
            )}

            {/* Info medio de pago seleccionado */}
            {modoPago === 'PREPAGO' ? (
              tarjeta ? (
                <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2">
                  <CreditCardIcon size={16} weight="fill" className="text-blue-500 shrink-0" />
                  <span className="text-blue-700 text-sm font-semibold">Descuento de saldo prepago</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
                  <CreditCardIcon size={16} weight="fill" className="text-slate-300 shrink-0" />
                  <span className="text-slate-400 text-sm">Escanear tarjeta del alumno</span>
                </div>
              )
            ) : medioPagoSeleccionado ? (
              <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
                {iconMedio(medioPagoSeleccionado.descripcion)}
                <span className="text-emerald-700 text-sm font-semibold">{medioPagoSeleccionado.descripcion}</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 bg-orange-50 border border-orange-200 rounded-lg px-3 py-2">
                <WarningIcon size={16} weight="fill" className="text-orange-400 shrink-0" />
                <span className="text-orange-600 text-sm font-semibold">Seleccionar medio de pago</span>
              </div>
            )}

            {/* Botón COBRAR */}
            <button
              onClick={handleCobrar}
              disabled={!canCobrar}
              className={[
                'w-full py-5 rounded-2xl font-black text-xl tracking-wide flex items-center justify-center gap-3 transition-all duration-150',
                canCobrar
                  ? 'bg-green-500 hover:bg-green-600 text-white cursor-pointer active:scale-95 shadow-lg shadow-green-500/25'
                  : 'bg-slate-200 text-slate-400 cursor-not-allowed',
              ].join(' ')}
            >
              {cobrando
                ? <><SpinnerIcon size={24} weight="fill" className="animate-spin" />Procesando…</>
                : <><CheckCircleIcon size={24} weight="fill" />COBRAR (F9)</>
              }
            </button>

            {/* Botón CANCELAR */}
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
