import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  CreditCard, AlertTriangle, UtensilsCrossed, History,
  CalendarCheck, CheckCircle2, Clock, AlertCircle, RefreshCw, Wallet,
  ShoppingBag, Lock, ChevronDown, ChevronUp, Eye, EyeOff,
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

function PinChangeSection({ clienteId }: { clienteId: number }) {
  const [open, setOpen] = useState(false)
  const [pinActual, setPinActual] = useState('')
  const [pinNuevo, setPinNuevo] = useState('')
  const [pinConfirmar, setPinConfirmar] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [showActual, setShowActual] = useState(false)
  const [showNuevo, setShowNuevo] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (pinNuevo !== pinConfirmar) {
      toast.error('Los PINs no coinciden')
      return
    }
    setSubmitting(true)
    try {
      await api.post(`/clientes/clientes/${clienteId}/cambiar-pin/`, {
        pin_actual: pinActual,
        pin_nuevo: pinNuevo,
      })
      toast.success('PIN actualizado correctamente')
      setOpen(false)
      setPinActual('')
      setPinNuevo('')
      setPinConfirmar('')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error
      toast.error(msg || 'Error al cambiar el PIN')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="rounded-2xl border border-slate-100 bg-white overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-4 py-3.5 cursor-pointer hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Lock className="w-4 h-4 text-slate-400" />
          <span className="text-sm font-medium text-slate-700">Cambiar PIN de autorización</span>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
      </button>
      {open && (
        <form onSubmit={handleSubmit} className="border-t border-slate-100 px-4 py-4 space-y-3">
          <div>
            <label className="text-xs font-medium text-slate-500 block mb-1">PIN actual</label>
            <div className="relative">
              <input
                type={showActual ? 'text' : 'password'}
                value={pinActual}
                onChange={e => setPinActual(e.target.value.replace(/\D/g, '').slice(0, 4))}
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-400 pr-10"
                placeholder="••••"
                maxLength={4}
                inputMode="numeric"
                autoComplete="current-password"
              />
              <button
                type="button"
                onClick={() => setShowActual(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 cursor-pointer"
                tabIndex={-1}
              >
                {showActual ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 block mb-1">PIN nuevo</label>
            <div className="relative">
              <input
                type={showNuevo ? 'text' : 'password'}
                value={pinNuevo}
                onChange={e => setPinNuevo(e.target.value.replace(/\D/g, '').slice(0, 4))}
                className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-400 pr-10"
                placeholder="••••"
                maxLength={4}
                inputMode="numeric"
                autoComplete="new-password"
              />
              <button
                type="button"
                onClick={() => setShowNuevo(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 cursor-pointer"
                tabIndex={-1}
              >
                {showNuevo ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 block mb-1">Confirmar PIN nuevo</label>
            <input
              type="password"
              value={pinConfirmar}
              onChange={e => setPinConfirmar(e.target.value.replace(/\D/g, '').slice(0, 4))}
              className="w-full border border-slate-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-400"
              placeholder="••••"
              maxLength={4}
              inputMode="numeric"
              autoComplete="new-password"
            />
          </div>
          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={() => { setOpen(false); setPinActual(''); setPinNuevo(''); setPinConfirmar('') }}
              className="flex-1 py-2.5 text-sm text-slate-600 border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting || pinActual.length < 4 || pinNuevo.length < 4 || pinConfirmar.length < 4}
              className="flex-1 py-2.5 text-sm text-white bg-green-600 rounded-xl hover:bg-green-700 transition-colors disabled:opacity-40 cursor-pointer font-medium"
            >
              {submitting ? 'Guardando…' : 'Guardar PIN'}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}

function ResumenTab({ hijo, mes, clienteId }: { hijo: HijoData; mes: { anio: number; mes: number }; clienteId: number }) {
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

      {/* PIN change */}
      <PinChangeSection clienteId={clienteId} />
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

  const setTab = useCallback((hijoId: number, tab: HijoTab) => {
    setTabs(prev => ({ ...prev, [hijoId]: tab }))
    if (tab === 'plan') loadPlan(hijoId)
    if (tab === 'cantina') loadCantina(hijoId)
  }, [loadPlan, loadCantina])

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

      {/* Aviso PIN por defecto */}
      {data.cliente.pin_es_defecto && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl px-4 py-3 flex gap-3 items-start">
          <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-amber-800">PIN de autorización pendiente de cambio</p>
            <p className="text-xs text-amber-700 mt-0.5">
              Tu PIN actual es <span className="font-bold">0000</span>. Cambialo desde la sección
              {' '}<span className="font-medium">Resumen → Cambiar PIN</span> para mayor seguridad.
            </p>
          </div>
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
            <ResumenTab hijo={hijo} mes={data.mes} clienteId={data.cliente.id} />
          )}
          {tab === 'historial' && <HistorialTab hijo={hijo} />}
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
