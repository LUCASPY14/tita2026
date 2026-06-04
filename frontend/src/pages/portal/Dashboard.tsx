import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  CreditCard, AlertTriangle, UtensilsCrossed, History,
  CalendarCheck, CheckCircle2, Clock, AlertCircle, RefreshCw, Wallet,
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

interface ConsumoReciente {
  fecha_consumo: string
  costo_almuerzo: string
  ya_cobrado: boolean
}

interface CuentaMensual {
  cantidad_almuerzos: number
  monto_total: number
  monto_pagado: number
  monto_pendiente: number
  estado: string
}

interface HijoData {
  id: number
  nombre: string
  grado: string | null
  tarjeta: Tarjeta | null
  restricciones: Restriccion[]
  consumos_mes: { total: number; cobrados: number; ultimos: ConsumoReciente[] }
  cuenta_mensual: CuentaMensual | null
}

interface PortalData {
  cliente: { id: number; nombre: string; email: string }
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

// ─── Constants ────────────────────────────────────────────────────────────────

type HijoTab = 'resumen' | 'historial' | 'plan'

const MESES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

const SEVERIDAD_COLOR: Record<string, BadgeColor> = {
  CRITICA: 'red', ALTA: 'orange', MEDIA: 'yellow', BAJA: 'default',
}

const CUENTA_COLOR: Record<string, BadgeColor> = {
  PAGADO: 'green', PARCIAL: 'blue', PENDIENTE: 'orange',
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatGs(n: number) {
  return 'Gs. ' + (Number(n) || 0).toLocaleString('es-PY')
}

function formatFecha(iso: string) {
  return new Date(iso).toLocaleDateString('es-PY', { day: '2-digit', month: '2-digit', year: '2-digit' })
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
          {/* Botón cargar saldo */}
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

      {/* Cuenta mensual */}
      {hijo.cuenta_mensual ? (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-4 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <UtensilsCrossed className="w-4 h-4 text-slate-500" />
              <p className="text-base font-semibold text-slate-700">
                Almuerzo — {MESES[mes.mes]} {mes.anio}
              </p>
            </div>
            <Badge color={CUENTA_COLOR[hijo.cuenta_mensual.estado] ?? 'default'}>
              {hijo.cuenta_mensual.estado}
            </Badge>
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
          {hijo.cuenta_mensual.monto_pendiente > 0 && (
            <div className="px-4 py-3 bg-red-50 border-t border-red-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-red-500" />
                <p className="text-sm font-medium text-red-700">Pendiente de pago</p>
              </div>
              <p className="text-sm font-bold text-red-700 tabular-nums">
                {formatGs(hijo.cuenta_mensual.monto_pendiente)}
              </p>
            </div>
          )}
          {hijo.cuenta_mensual.monto_pendiente === 0 && (
            <div className="px-4 py-3 bg-green-50 border-t border-green-100 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-green-600" />
              <p className="text-sm font-medium text-green-700">Cuenta al día</p>
            </div>
          )}
        </div>
      ) : (
        <div className="rounded-2xl border border-slate-100 bg-white px-4 py-6 text-center text-slate-400 text-sm">
          Sin cuenta de almuerzo en {MESES[mes.mes]}
        </div>
      )}
    </div>
  )
}

function HistorialTab({ hijo }: { hijo: HijoData }) {
  if (hijo.consumos_mes.total === 0) {
    return (
      <div className="py-12 text-center text-slate-400">
        <UtensilsCrossed className="w-10 h-10 mx-auto mb-3 opacity-30" />
        <p className="text-base">Sin consumos registrados este mes</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-3">
        <div className="flex-1 bg-white rounded-xl border border-slate-100 px-4 py-3 text-center">
          <p className="text-sm text-slate-500">Total almuerzos</p>
          <p className="text-2xl font-bold text-slate-800 tabular-nums">{hijo.consumos_mes.total}</p>
        </div>
        <div className="flex-1 bg-white rounded-xl border border-slate-100 px-4 py-3 text-center">
          <p className="text-sm text-slate-500">Cobrados</p>
          <p className="text-2xl font-bold text-emerald-700 tabular-nums">{hijo.consumos_mes.cobrados}</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-100 bg-slate-50">
          <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">Últimos consumos</p>
        </div>
        <div className="divide-y divide-slate-100">
          {hijo.consumos_mes.ultimos.length === 0 && (
            <p className="px-4 py-4 text-sm text-slate-400 text-center">Sin registros disponibles</p>
          )}
          {hijo.consumos_mes.ultimos.map((c, i) => (
            <div key={i} className="flex items-center justify-between px-4 py-3">
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
  const [suscripciones, setSuscripciones] = useState<Record<number, Suscripcion[]>>({})
  const [loadingPlan, setLoadingPlan] = useState<Record<number, boolean>>({})
  // Tracks which hijo plan requests have been initiated (prevents duplicate fetches)
  const planRequestedRef = useRef<Set<number>>(new Set())

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

  const setTab = useCallback((hijoId: number, tab: HijoTab) => {
    setTabs(prev => ({ ...prev, [hijoId]: tab }))
    if (tab === 'plan') loadPlan(hijoId)
  }, [loadPlan])

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
          <TabBtn active={tab === 'plan'} onClick={() => setTab(hijo.id, 'plan')}>
            <span className="flex items-center gap-1.5">
              <CalendarCheck className="w-3.5 h-3.5" />
              Plan
            </span>
          </TabBtn>
        </div>

        {/* Tab content */}
        <div className="p-5">
          {tab === 'resumen' && <ResumenTab hijo={hijo} mes={data.mes} />}
          {tab === 'historial' && <HistorialTab hijo={hijo} />}
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
