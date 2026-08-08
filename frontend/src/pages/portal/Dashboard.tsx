import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  CreditCard, AlertTriangle, UtensilsCrossed, History,
  CalendarCheck, AlertCircle, RefreshCw, Wallet,
  ShoppingBag, ChevronDown, ChevronUp, ChevronLeft, ChevronRight, TrendingUp,
} from 'lucide-react'
import api from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import Spinner from '../../components/ui/Spinner'
import Badge, { type BadgeColor } from '../../components/ui/Badge'

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface Tarjeta {
  nro_tarjeta: string
  saldo_actual: number
  estado: string
  en_alerta: boolean
}

interface Restriccion {
  tipo: string
  severidad: string
  descripcion: string
  requiere_autorizacion: boolean
}

interface ConsumoHistorial {
  id: number
  fecha_consumo: string
  costo_almuerzo: string | number
  ya_cobrado: boolean
}

interface HistorialData {
  anio: number
  mes: number
  consumos: ConsumoHistorial[]
  total: number
  monto_total: number
  cobrados: number
}

interface CuentaMensual {
  id: number
  cantidad_almuerzos: number
  monto_total: number
  monto_pagado: number
  monto_pendiente: number
  estado: string
}

interface TopProducto {
  producto: string
  cantidad: number
}

interface HijoData {
  id: number
  nombre: string
  grado: string | null
  tarjeta: Tarjeta | null
  restricciones: Restriccion[]
  cuenta_mensual: CuentaMensual | null
  saldo_almuerzo: number
  top_productos?: TopProducto[]
}

interface PortalData {
  cliente: { id: number; nombre: string; email: string; pin_es_defecto: boolean }
  mes: { anio: number; mes: number }
  hijos: HijoData[]
}

interface Suscripcion {
  id: number
  plan: number
  plan_nombre: string
  estado: string
  fecha_inicio: string
  fecha_fin: string | null
  observaciones: string
}

interface DetalleCantina {
  producto_nombre: string
  cantidad: number
  precio_unitario: number
  subtotal: number
}

interface VentaCantina {
  id: number
  fecha: string
  monto_total: number
  detalles: DetalleCantina[]
}

// ─── Constants ────────────────────────────────────────────────────────────────

type HijoTab = 'resumen' | 'historial' | 'cantina' | 'plan'

const MESES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

const SEVERIDAD_COLOR: Record<string, BadgeColor> = {
  CRITICA: 'red', ALTA: 'orange', MEDIA: 'yellow', BAJA: 'default',
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatGs(n: number) {
  return 'Gs. ' + (Number(n) || 0).toLocaleString('es-PY')
}

function formatFecha(iso: string) {
  return new Date(iso).toLocaleDateString('es-PY', { day: '2-digit', month: '2-digit', year: '2-digit' })
}

function formatVeces(n: number) {
  const cantidad = n % 1 === 0 ? n : Number(n.toFixed(2))
  return cantidad === 1 ? '1 vez' : `${cantidad} veces`
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function TabBtn({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={[
        'px-4 py-2.5 text-base font-medium border-b-2 transition-colors cursor-pointer whitespace-nowrap',
        active ? 'border-green-500 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700',
      ].join(' ')}
    >
      {children}
    </button>
  )
}

function ResumenTab({ hijo, mes }: { hijo: HijoData; mes: { anio: number; mes: number } }) {
  const navigate = useNavigate()

  return (
    <div className="space-y-4">
      {/* Tarjeta saldo */}
      {hijo.tarjeta ? (
        <div className={[
          'rounded-2xl border p-4',
          hijo.tarjeta.en_alerta
            ? 'bg-red-50 border-red-200'
            : hijo.tarjeta.estado === 'BLOQUEADA'
              ? 'bg-slate-100 border-slate-300'
              : 'bg-green-50 border-green-200',
        ].join(' ')}>
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <CreditCard className={`w-4 h-4 ${hijo.tarjeta.en_alerta ? 'text-red-500' : 'text-green-600'}`} />
                <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">Tarjeta escolar</p>
              </div>
              <p className={`text-4xl font-bold tabular-nums ${hijo.tarjeta.en_alerta ? 'text-red-700' : 'text-emerald-700'}`}>
                {formatGs(hijo.tarjeta.saldo_actual)}
              </p>
              <p className="text-sm text-slate-400 mt-1">{hijo.tarjeta.nro_tarjeta}</p>
            </div>
            <div className="text-right space-y-1.5">
              <Badge color={hijo.tarjeta.estado === 'ACTIVA' ? 'green' : 'default'}>
                {hijo.tarjeta.estado}
              </Badge>
              {hijo.tarjeta.en_alerta && (
                <div className="flex items-center gap-1 justify-end">
                  <AlertTriangle className="w-3 h-3 text-red-500" />
                  <span className="text-sm text-red-600 font-medium">Saldo bajo</span>
                </div>
              )}
            </div>
          </div>
          {hijo.tarjeta.estado === 'ACTIVA' && (
            <button
              type="button"
              onClick={() => navigate('/portal/carga-saldo')}
              className="mt-3 w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-white border border-green-300 text-green-700 font-semibold text-base hover:bg-green-50 transition-colors cursor-pointer"
            >
              <Wallet className="w-4 h-4" />
              Cargar saldo con tarjeta
            </button>
          )}
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-200 bg-white p-4 flex items-center gap-3 text-slate-400">
          <CreditCard className="w-5 h-5" />
          <p className="text-sm">Sin tarjeta asignada</p>
        </div>
      )}

      {/* Saldo de almuerzo — cuenta corriente, separada de la tarjeta */}
      <div className={[
        'rounded-2xl border p-4',
        hijo.saldo_almuerzo < 0 ? 'bg-red-50 border-red-200' : 'bg-orange-50 border-orange-200',
      ].join(' ')}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <UtensilsCrossed className={`w-4 h-4 ${hijo.saldo_almuerzo < 0 ? 'text-red-500' : 'text-orange-600'}`} />
              <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">Saldo de almuerzo</p>
            </div>
            <p className={`text-4xl font-bold tabular-nums ${hijo.saldo_almuerzo < 0 ? 'text-red-700' : 'text-orange-700'}`}>
              {formatGs(hijo.saldo_almuerzo)}
            </p>
            {hijo.saldo_almuerzo < 0 && (
              <p className="text-sm text-slate-400 mt-1">
                Debe — se descuenta de cada ingreso al comedor
              </p>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={() => navigate(`/portal/carga-saldo?tipo=ALMUERZO&hijo_id=${hijo.id}`)}
          className={[
            'mt-3 w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-white border font-semibold text-base transition-colors cursor-pointer',
            hijo.saldo_almuerzo < 0
              ? 'border-red-300 text-red-700 hover:bg-red-50'
              : 'border-orange-300 text-orange-700 hover:bg-orange-50',
          ].join(' ')}
        >
          <Wallet className="w-4 h-4" />
          Recargar saldo de almuerzo
        </button>
      </div>

      {/* Restricciones */}
      {hijo.restricciones.length > 0 && (
        <div className="space-y-2">
          {hijo.restricciones.map((r, i) => (
            <div
              key={i}
              className={[
                'rounded-xl border px-4 py-3 flex items-start gap-3',
                r.severidad === 'CRITICA' ? 'bg-red-50 border-red-200' : 'bg-amber-50 border-amber-200',
              ].join(' ')}
            >
              <AlertCircle className={`w-4 h-4 mt-0.5 shrink-0 ${r.severidad === 'CRITICA' ? 'text-red-500' : 'text-amber-500'}`} />
              <div className="flex-1 min-w-0">
                <p className="text-base font-semibold text-slate-800">{r.tipo}</p>
                {r.descripcion && <p className="text-sm text-slate-500 mt-0.5">{r.descripcion}</p>}
              </div>
              <Badge color={SEVERIDAD_COLOR[r.severidad] ?? 'default'}>{r.severidad}</Badge>
            </div>
          ))}
        </div>
      )}

      {/* Consumo del mes — informativo, el saldo de almuerzo de arriba es lo que se cobra */}
      {hijo.cuenta_mensual ? (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-4 py-3 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
            <UtensilsCrossed className="w-4 h-4 text-slate-500" />
            <p className="text-base font-semibold text-slate-700">
              Consumo — {MESES[mes.mes]} {mes.anio}
            </p>
          </div>
          <div className="grid grid-cols-2 divide-x divide-slate-100">
            <div className="p-4 text-center">
              <p className="text-sm text-slate-500 mb-1">Almuerzos tomados</p>
              <p className="text-3xl font-bold text-slate-800 tabular-nums">{hijo.cuenta_mensual.cantidad_almuerzos}</p>
            </div>
            <div className="p-4 text-center">
              <p className="text-sm text-slate-500 mb-1">Total del mes</p>
              <p className="text-2xl font-bold text-emerald-700 tabular-nums">{formatGs(hijo.cuenta_mensual.monto_total)}</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-100 bg-white px-4 py-6 text-center text-slate-400 text-sm">
          Sin consumo de almuerzo en {MESES[mes.mes]}
        </div>
      )}

      {/* Lo más consumido en cantina */}
      {(hijo.top_productos ?? []).length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-4 py-3 bg-slate-50 border-b border-slate-100 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-slate-500" />
            <p className="text-base font-semibold text-slate-700">
              Lo más consumido — {MESES[mes.mes]}
            </p>
          </div>
          <div className="divide-y divide-slate-100">
            {(hijo.top_productos ?? []).map((p, i) => (
              <div key={p.producto} className="flex items-center justify-between px-4 py-2.5">
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className="w-5 h-5 shrink-0 rounded-full bg-slate-100 text-slate-500 text-xs font-bold flex items-center justify-center">
                    {i + 1}
                  </span>
                  <span className="text-sm text-slate-700 truncate">{p.producto}</span>
                </div>
                <span className="text-sm font-semibold text-slate-500 tabular-nums shrink-0 ml-2">
                  {formatVeces(p.cantidad)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  )
}

function HistorialTab({
  data,
  loading,
  anio,
  mes,
  isCurrentMonth,
  onPrevMes,
  onNextMes,
}: {
  data: HistorialData | null
  loading: boolean
  anio: number
  mes: number
  isCurrentMonth: boolean
  onPrevMes: () => void
  onNextMes: () => void
}) {
  return (
    <div className="space-y-3">
      {/* Navegador de mes */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3 flex items-center justify-between">
        <button
          type="button"
          onClick={onPrevMes}
          className="p-2 rounded-xl hover:bg-slate-100 text-slate-600 cursor-pointer transition-colors"
          aria-label="Mes anterior"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <p className="text-base font-semibold text-slate-800">{MESES[mes]} {anio}</p>
        <button
          type="button"
          onClick={onNextMes}
          disabled={isCurrentMonth}
          className={[
            'p-2 rounded-xl transition-colors',
            isCurrentMonth ? 'text-slate-300 cursor-not-allowed' : 'hover:bg-slate-100 text-slate-600 cursor-pointer',
          ].join(' ')}
          aria-label="Mes siguiente"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>

      {loading ? (
        <Spinner className="mt-8" />
      ) : !data || data.total === 0 ? (
        <div className="py-12 text-center text-slate-400">
          <UtensilsCrossed className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="text-base">Sin consumos registrados este mes</p>
        </div>
      ) : (
        <>
          <div className="flex gap-3">
            <div className="flex-1 bg-white rounded-xl border border-slate-100 px-4 py-3 text-center">
              <p className="text-sm text-slate-500">Total almuerzos</p>
              <p className="text-2xl font-bold text-slate-800 tabular-nums">{data.total}</p>
            </div>
            <div className="flex-1 bg-white rounded-xl border border-slate-100 px-4 py-3 text-center">
              <p className="text-sm text-slate-500">Cobrados</p>
              <p className="text-2xl font-bold text-emerald-700 tabular-nums">{data.cobrados}</p>
            </div>
            <div className="flex-1 bg-white rounded-xl border border-slate-100 px-4 py-3 text-center">
              <p className="text-sm text-slate-500">Total</p>
              <p className="text-2xl font-bold text-orange-700 tabular-nums">{formatGs(data.monto_total)}</p>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 bg-slate-50">
              <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">Consumos</p>
            </div>
            <div className="divide-y divide-slate-100">
              {data.consumos.map(c => (
                <div key={c.id} className="flex items-center justify-between px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center">
                      <UtensilsCrossed className="w-4 h-4 text-slate-500" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-800">Almuerzo</p>
                      <p className="text-sm text-slate-400">{formatFecha(c.fecha_consumo)}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-slate-800 tabular-nums">
                      {c.ya_cobrado ? formatGs(Number(c.costo_almuerzo)) : '—'}
                    </p>
                    <Badge color={c.ya_cobrado ? 'orange' : 'green'}>
                      {c.ya_cobrado ? 'Cobrado' : 'Sin cargo'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function CantinaTab({
  ventas,
  loading,
  hasMore,
  onLoadMore,
  expandedId,
  onToggle,
}: {
  ventas: VentaCantina[] | undefined
  loading: boolean
  hasMore: boolean
  onLoadMore: () => void
  expandedId: number | null
  onToggle: (id: number) => void
}) {
  if (loading && !ventas) return <Spinner className="mt-8" />

  if (!ventas || ventas.length === 0) {
    return (
      <div className="py-12 text-center text-slate-400">
        <ShoppingBag className="w-10 h-10 mx-auto mb-3 opacity-30" />
        <p className="text-base">Sin compras en cantina</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {ventas.map(v => (
        <div key={v.id} className="bg-white rounded-xl border border-slate-100 overflow-hidden">
          <button
            type="button"
            onClick={() => onToggle(v.id)}
            className="w-full flex items-center justify-between px-4 py-3 text-left cursor-pointer hover:bg-slate-50 transition-colors"
          >
            <div>
              <p className="text-sm font-medium text-slate-800">{formatFecha(v.fecha)}</p>
              <p className="text-xs text-slate-400">{`${v.detalles.length} ítem${v.detalles.length !== 1 ? 's' : ''}`}</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <p className="text-sm font-semibold text-emerald-700 tabular-nums">{formatGs(v.monto_total)}</p>
              {expandedId === v.id
                ? <ChevronUp className="w-4 h-4 text-slate-400" />
                : <ChevronDown className="w-4 h-4 text-slate-400" />}
            </div>
          </button>
          {expandedId === v.id && (
            <div className="border-t border-slate-100 divide-y divide-slate-50">
              {v.detalles.map((d, i) => (
                <div key={i} className="flex items-center justify-between px-4 py-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-xs text-slate-400 tabular-nums shrink-0">{d.cantidad}×</span>
                    <span className="text-sm text-slate-700 truncate">{d.producto_nombre}</span>
                  </div>
                  <span className="text-sm text-slate-600 tabular-nums shrink-0 ml-2">{formatGs(d.subtotal)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
      {hasMore && (
        <button
          type="button"
          onClick={onLoadMore}
          disabled={loading}
          className="w-full py-2.5 text-sm text-green-700 font-medium border border-green-200 rounded-xl hover:bg-green-50 transition-colors disabled:opacity-40 cursor-pointer"
        >
          {loading ? 'Cargando…' : 'Ver más'}
        </button>
      )}
    </div>
  )
}

function PlanTab({ suscripciones, loading }: { suscripciones: Suscripcion[] | undefined; loading: boolean }) {
  if (loading) return <Spinner className="mt-8" />

  if (!suscripciones || suscripciones.length === 0) {
    return (
      <div className="py-12 text-center text-slate-400">
        <CalendarCheck className="w-10 h-10 mx-auto mb-3 opacity-30" />
        <p className="text-base">Sin plan de almuerzo activo</p>
        <p className="text-sm mt-1">Consultá con la cantina para suscribirte</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {suscripciones.map(s => (
        <div key={s.id} className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-4 py-3 bg-green-50 border-b border-green-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CalendarCheck className="w-4 h-4 text-green-600" />
              <p className="text-base font-semibold text-green-800">{s.plan_nombre}</p>
            </div>
            <Badge color={s.estado === 'ACTIVA' ? 'green' : 'default'}>{s.estado}</Badge>
          </div>
          <div className="px-4 py-3 space-y-2 text-base">
            <div className="flex justify-between">
              <span className="text-slate-500">Inicio</span>
              <span className="font-medium text-slate-800">{formatFecha(s.fecha_inicio)}</span>
            </div>
            {s.fecha_fin && (
              <div className="flex justify-between">
                <span className="text-slate-500">Vencimiento</span>
                <span className="font-medium text-slate-800">{formatFecha(s.fecha_fin)}</span>
              </div>
            )}
            {s.observaciones && (
              <p className="text-sm text-slate-400 pt-1 border-t border-slate-100">{s.observaciones}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function PortalDashboard() {
  const { user } = useAuthStore()
  const [data, setData] = useState<PortalData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [selectedHijoId, setSelectedHijoId] = useState<number | null>(null)
  const [tabs, setTabs] = useState<Record<number, HijoTab>>({})

  // Plan tab state
  const [suscripciones, setSuscripciones] = useState<Record<number, Suscripcion[]>>({})
  const [loadingPlan, setLoadingPlan] = useState<Record<number, boolean>>({})
  const planRequestedRef = useRef<Set<number>>(new Set())

  // Historial tab state
  const today = useMemo(() => new Date(), [])
  const [historial, setHistorial] = useState<Record<number, HistorialData | null>>({})
  const [loadingHistorial, setLoadingHistorial] = useState<Record<number, boolean>>({})
  const [historialMes, setHistorialMes] = useState<Record<number, { anio: number; mes: number }>>({})

  // Cantina tab state
  const [cantina, setCantina] = useState<Record<number, VentaCantina[]>>({})
  const [loadingCantina, setLoadingCantina] = useState<Record<number, boolean>>({})
  const [hasMoreCantina, setHasMoreCantina] = useState<Record<number, boolean>>({})
  const [expandedCantinaId, setExpandedCantinaId] = useState<Record<number, number | null>>({})
  const cantinaRequestedRef = useRef<Set<number>>(new Set())
  const pageCantinaRef = useRef<Record<number, number>>({})

  const cargar = useCallback(async () => {
    setLoading(true)
    setError(false)
    try {
      const { data: res } = await api.get('/usuarios/portal/mi-hijo/')
      setData(res)
      if (res.hijos.length > 0) {
        setSelectedHijoId(res.hijos[0].id)
        const init: Record<number, HijoTab> = {}
        res.hijos.forEach((h: HijoData) => { init[h.id] = 'resumen' })
        setTabs(init)
      }
    } catch {
      toast.error('Error al cargar los datos')
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { cargar() }, [user, cargar])

  const loadPlan = useCallback(async (hijoId: number) => {
    if (planRequestedRef.current.has(hijoId)) return
    planRequestedRef.current.add(hijoId)
    setLoadingPlan(prev => ({ ...prev, [hijoId]: true }))
    try {
      const { data: res } = await api.get('/almuerzos/suscripciones/', {
        params: { hijo: hijoId, estado: 'ACTIVA', page_size: 10 },
      })
      setSuscripciones(prev => ({ ...prev, [hijoId]: res.results ?? [] }))
    } catch {
      setSuscripciones(prev => ({ ...prev, [hijoId]: [] }))
      planRequestedRef.current.delete(hijoId)
    } finally {
      setLoadingPlan(prev => ({ ...prev, [hijoId]: false }))
    }
  }, [])

  const loadCantina = useCallback(async (hijoId: number, loadMore = false) => {
    if (!loadMore && cantinaRequestedRef.current.has(hijoId)) return
    if (!loadMore) cantinaRequestedRef.current.add(hijoId)
    const page = loadMore ? (pageCantinaRef.current[hijoId] ?? 1) + 1 : 1
    pageCantinaRef.current[hijoId] = page
    setLoadingCantina(prev => ({ ...prev, [hijoId]: true }))
    try {
      const { data: res } = await api.get('/usuarios/portal/historial-cantina/', {
        params: { hijo_id: hijoId, page, page_size: 15 },
      })
      setCantina(prev => ({
        ...prev,
        [hijoId]: loadMore ? [...(prev[hijoId] ?? []), ...res.results] : res.results,
      }))
      setHasMoreCantina(prev => ({ ...prev, [hijoId]: Boolean(res.next) }))
    } catch {
      if (!loadMore) cantinaRequestedRef.current.delete(hijoId)
    } finally {
      setLoadingCantina(prev => ({ ...prev, [hijoId]: false }))
    }
  }, [])

  const toggleCantinaRow = useCallback((hijoId: number, ventaId: number) => {
    setExpandedCantinaId(prev => ({
      ...prev,
      [hijoId]: prev[hijoId] === ventaId ? null : ventaId,
    }))
  }, [])

  const loadHistorial = useCallback(async (hijoId: number, anio: number, mes: number) => {
    setLoadingHistorial(prev => ({ ...prev, [hijoId]: true }))
    try {
      const { data: res } = await api.get('/usuarios/portal/historial-consumos/', {
        params: { hijo_id: hijoId, anio, mes },
      })
      setHistorial(prev => ({ ...prev, [hijoId]: res }))
    } catch {
      setHistorial(prev => ({ ...prev, [hijoId]: null }))
    } finally {
      setLoadingHistorial(prev => ({ ...prev, [hijoId]: false }))
    }
  }, [])

  // Mes "actual" según el servidor (el mismo que ya se muestra en el saludo),
  // no el reloj del navegador — evita desincronías de huso horario.
  const dataAnio = data?.mes.anio
  const dataMes = data?.mes.mes
  const mesServidor = useMemo(
    () => (dataAnio && dataMes) ? { anio: dataAnio, mes: dataMes } : { anio: today.getFullYear(), mes: today.getMonth() + 1 },
    [dataAnio, dataMes, today],
  )

  const cambiarMesHistorial = useCallback((hijoId: number, delta: number) => {
    const actual = historialMes[hijoId] ?? mesServidor
    let { anio, mes } = actual
    mes += delta
    if (mes < 1) { mes = 12; anio -= 1 }
    if (mes > 12) { mes = 1; anio += 1 }
    setHistorialMes(prev => ({ ...prev, [hijoId]: { anio, mes } }))
    loadHistorial(hijoId, anio, mes)
  }, [historialMes, loadHistorial, mesServidor])

  const setTab = useCallback((hijoId: number, tab: HijoTab) => {
    setTabs(prev => ({ ...prev, [hijoId]: tab }))
    if (tab === 'plan') loadPlan(hijoId)
    if (tab === 'cantina') loadCantina(hijoId)
    if (tab === 'historial') {
      const actual = historialMes[hijoId] ?? mesServidor
      loadHistorial(hijoId, actual.anio, actual.mes)
    }
  }, [loadPlan, loadCantina, loadHistorial, historialMes, mesServidor])

  if (loading) return <Spinner className="mt-12" />

  if (error) {
    return (
      <div className="py-16 text-center text-slate-400">
        <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-40" />
        <p className="text-base font-medium text-slate-600">No se pudieron cargar los datos</p>
        <button
          type="button"
          onClick={cargar}
          className="mt-4 px-4 py-2 text-sm font-medium text-green-700 border border-green-200 rounded-xl hover:bg-green-50 transition-colors cursor-pointer"
        >
          Reintentar
        </button>
      </div>
    )
  }

  if (!data || data.hijos.length === 0) {
    return (
      <div className="py-16 text-center text-slate-400">
        <UtensilsCrossed className="w-12 h-12 mx-auto mb-4 opacity-20" />
        <p className="text-base font-medium text-slate-600">Sin hijos asociados</p>
        <p className="text-sm mt-1">Contactá con la administración de la cantina.</p>
      </div>
    )
  }

  const hijo = data.hijos.find(h => h.id === selectedHijoId) ?? data.hijos[0]
  const tab = tabs[hijo.id] ?? 'resumen'

  return (
    <div className="space-y-5">
      {/* Welcome */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Hola, {user?.nombre}</h1>
          <p className="text-base text-slate-500 mt-0.5">
            {MESES[data.mes.mes]} {data.mes.anio}
          </p>
        </div>
        <button
          type="button"
          onClick={cargar}
          disabled={loading}
          className="p-2 rounded-xl border border-slate-200 text-slate-500 hover:bg-slate-50 transition-colors disabled:opacity-40 cursor-pointer shrink-0"
          aria-label="Actualizar datos"
          title="Actualizar datos"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Hijo selector */}
      {data.hijos.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {data.hijos.map(h => (
            <button
              type="button"
              key={h.id}
              onClick={() => setSelectedHijoId(h.id)}
              aria-pressed={h.id === selectedHijoId}
              className={[
                'px-4 py-2 rounded-full text-base font-medium whitespace-nowrap transition-colors cursor-pointer shrink-0',
                h.id === selectedHijoId
                  ? 'bg-green-500 text-white'
                  : 'bg-white border border-slate-200 text-slate-600 hover:border-green-300',
              ].join(' ')}
            >
              {h.nombre}
            </button>
          ))}
        </div>
      )}

      {/* Hijo card */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        {/* Hijo header */}
        <div className="px-5 py-4 border-b border-slate-100">
          <p className="text-lg font-bold text-slate-800">{hijo.nombre}</p>
          <p className="text-sm text-slate-400 mt-0.5">{hijo.grado || 'Sin grado'}</p>
        </div>

        {/* Tabs */}
        <div role="tablist" className="border-b border-slate-100 px-5 flex gap-1 overflow-x-auto">
          <TabBtn active={tab === 'resumen'} onClick={() => setTab(hijo.id, 'resumen')}>
            Resumen
          </TabBtn>
          <TabBtn active={tab === 'historial'} onClick={() => setTab(hijo.id, 'historial')}>
            <span className="flex items-center gap-1.5">
              <History className="w-3.5 h-3.5" />
              Historial
            </span>
          </TabBtn>
          <TabBtn active={tab === 'cantina'} onClick={() => setTab(hijo.id, 'cantina')}>
            <span className="flex items-center gap-1.5">
              <ShoppingBag className="w-3.5 h-3.5" />
              Cantina
            </span>
          </TabBtn>
          <TabBtn active={tab === 'plan'} onClick={() => setTab(hijo.id, 'plan')}>
            <span className="flex items-center gap-1.5">
              <CalendarCheck className="w-3.5 h-3.5" />
              Almuerzos
            </span>
          </TabBtn>
        </div>

        {/* Tab content */}
        <div className="p-5">
          {tab === 'resumen' && (
            <ResumenTab hijo={hijo} mes={data.mes} />
          )}
          {tab === 'historial' && (() => {
            const mesActual = historialMes[hijo.id] ?? mesServidor
            const esMesActual = mesActual.anio === mesServidor.anio && mesActual.mes === mesServidor.mes
            return (
              <HistorialTab
                data={historial[hijo.id] ?? null}
                loading={loadingHistorial[hijo.id] ?? false}
                anio={mesActual.anio}
                mes={mesActual.mes}
                isCurrentMonth={esMesActual}
                onPrevMes={() => cambiarMesHistorial(hijo.id, -1)}
                onNextMes={() => cambiarMesHistorial(hijo.id, 1)}
              />
            )
          })()}
          {tab === 'cantina' && (
            <CantinaTab
              ventas={cantina[hijo.id]}
              loading={loadingCantina[hijo.id] ?? false}
              hasMore={hasMoreCantina[hijo.id] ?? false}
              onLoadMore={() => loadCantina(hijo.id, true)}
              expandedId={expandedCantinaId[hijo.id] ?? null}
              onToggle={(ventaId) => toggleCantinaRow(hijo.id, ventaId)}
            />
          )}
          {tab === 'plan' && (
            <PlanTab
              suscripciones={suscripciones[hijo.id]}
              loading={loadingPlan[hijo.id] ?? false}
            />
          )}
        </div>
      </div>
    </div>
  )
}
