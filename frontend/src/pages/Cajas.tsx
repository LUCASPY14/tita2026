import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import {
  Plus, Lock, CheckCircle, Banknote, LayoutGrid,
  Clock, ShoppingCart, CreditCard,
  Printer, ArrowUpCircle, ArrowDownCircle, RefreshCw,
} from 'lucide-react'
import api from '../services/api'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Modal from '../components/ui/Modal'
import Table, { type Column } from '../components/ui/Table'

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface Caja { id: number; nombre: string; ubicacion: string | null; activo: boolean }

interface CierreCaja {
  id: number
  caja: number
  caja_nombre: string
  empleado: number
  empleado_nombre: string
  fecha_apertura: string
  fecha_cierre: string | null
  monto_inicial: string
  monto_contado_fisico: string | null
  diferencia_efectivo: string | null
  estado: 'ABIERTO' | 'CERRADO' | 'CONCILIADO'
  observaciones_conciliacion: string | null
}

interface ArqueoData {
  monto_inicial: number
  efectivo_esperado: number
  efectivo_ingresos: number
  efectivo_egresos: number
  pos_total: number
  prepago_total: number
  ingresos_total: number
  egresos_total: number
  ingresos_por_medio: { medio: string; total: number }[]
  egresos_por_medio: { medio: string; total: number }[]
}

interface MedioPago { id: number; descripcion: string; activo: boolean }

// ─── Helpers ──────────────────────────────────────────────────────────────────

function extractErrorMessage(err: unknown): string {
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

function formatGs(value: string | number | null | undefined): string {
  return (Number(value) || 0).toLocaleString('es-PY') + ' Gs.'
}

function formatDatetime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

const ESTADO_COLOR: Record<string, BadgeColor> = {
  ABIERTO: 'green', CERRADO: 'blue', CONCILIADO: 'purple',
}
const ESTADO_LABEL: Record<string, string> = {
  ABIERTO: 'Abierta', CERRADO: 'Cerrada', CONCILIADO: 'Conciliada',
}

function elapsedLabel(isoApertura: string): string {
  const mins = Math.floor((Date.now() - new Date(isoApertura).getTime()) / 60000)
  if (mins < 60) return `${mins} min`
  const h = Math.floor(mins / 60), m = mins % 60
  return `${h}h ${m}min`
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function CajaPage() {
  const { t } = useTranslation()

  const [cierres, setCierres] = useState<CierreCaja[]>([])
  const [cajas, setCajas] = useState<Caja[]>([])
  const [mediosPago, setMediosPago] = useState<MedioPago[]>([])
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [filterEstado, setFilterEstado] = useState('')
  const [filterCaja, setFilterCaja] = useState('')

  // Turno activo del usuario
  const [miCierre, setMiCierre] = useState<CierreCaja | null | undefined>(undefined) // undefined = cargando
  const [arqueo, setArqueo] = useState<ArqueoData | null>(null)
  const [loadingArqueo, setLoadingArqueo] = useState(false)

  // Abrir caja modal
  const [abrirModal, setAbrirModal] = useState(false)
  const [cajaSeleccionada, setCajaSeleccionada] = useState('')
  const [montoInicial, setMontoInicial] = useState('')
  const [abriendo, setAbriendo] = useState(false)

  // Cerrar caja modal
  const [cerrarModal, setCerrarModal] = useState<CierreCaja | null>(null)
  const [arqueoModal, setArqueoModal] = useState<ArqueoData | null>(null)
  const [loadingArqueoModal, setLoadingArqueoModal] = useState(false)
  const [montoContado, setMontoContado] = useState('')
  const [montoContadoDebounced, setMontoContadoDebounced] = useState('')
  const [cerrando, setCerrando] = useState(false)

  // Conciliar modal
  const [conciliarModal, setConciliarModal] = useState<CierreCaja | null>(null)
  const [obsConc, setObsConc] = useState('')
  const [conciliando, setConciliando] = useState(false)

  // Movimiento manual modal
  const [movModal, setMovModal] = useState(false)
  const [movTipo, setMovTipo] = useState<'INGRESO' | 'EGRESO'>('INGRESO')
  const [movMonto, setMovMonto] = useState('')
  const [movMedioPago, setMovMedioPago] = useState('')
  const [movDesc, setMovDesc] = useState('')
  const [movSaving, setMovSaving] = useState(false)

  const abriendoRef = useRef(false)
  const cerrandoRef = useRef(false)
  const conciliandoRef = useRef(false)
  const movSavingRef = useRef(false)
  const requestIdRef = useRef(0)

  // ── Cargar lista de cierres ────────────────────────────────────────────────

  const loadCierres = useCallback(async () => {
    const requestId = ++requestIdRef.current
    setLoading(true)
    try {
      const params: Record<string, string | number> = { page, page_size: 15 }
      if (filterEstado) params.estado = filterEstado
      if (filterCaja) params.caja = filterCaja
      const { data } = await api.get('/contabilidad/cierres-caja/', { params, timeout: 8000 })
      if (requestId !== requestIdRef.current) return
      setCierres(data.results ?? [])
      setTotal(data.count ?? 0)
    } catch {
      if (requestId !== requestIdRef.current) return
      toast.error('Error al cargar cierres')
    } finally {
      if (requestId === requestIdRef.current) setLoading(false)
    }
  }, [page, filterEstado, filterCaja])

  useEffect(() => { loadCierres() }, [loadCierres])

  // ── Turno activo del usuario (mi-caja) ────────────────────────────────────

  const loadMiCierre = useCallback(async () => {
    try {
      const { data } = await api.get('/contabilidad/cierres-caja/mi-caja/', { timeout: 6000 })
      setMiCierre(data ?? null)
    } catch {
      setMiCierre(null)
    }
  }, [])

  useEffect(() => { loadMiCierre() }, [loadMiCierre])

  // ── Arqueo del turno activo ───────────────────────────────────────────────

  const loadArqueo = useCallback(async (cierreId: number) => {
    setLoadingArqueo(true)
    try {
      const { data } = await api.get(`/contabilidad/cierres-caja/${cierreId}/arqueo/`, { timeout: 6000 })
      setArqueo(data)
    } catch {
      setArqueo(null)
    } finally {
      setLoadingArqueo(false)
    }
  }, [])

  useEffect(() => {
    if (miCierre?.id) loadArqueo(miCierre.id)
    else setArqueo(null)
  }, [miCierre, loadArqueo])

  // ── Datos auxiliares ──────────────────────────────────────────────────────

  useEffect(() => {
    api.get('/contabilidad/cajas/')
      .then(({ data }) => {
        const lista: Caja[] = data.results ?? data
        setCajas(lista)
        const primeraActiva = lista.find(c => c.activo)
        setCajaSeleccionada(primeraActiva ? String(primeraActiva.id) : '')
      })
      .catch(() => {})

    api.get('/core/medios-pago/', { params: { activo: true } })
      .then(({ data }) => setMediosPago(data.results ?? data))
      .catch(() => {})
  }, [])

  // Debounce montoContado para no mostrar diferencias intermedias mientras se tipea
  useEffect(() => {
    const t = setTimeout(() => setMontoContadoDebounced(montoContado), 400)
    return () => clearTimeout(t)
  }, [montoContado])

  // ── Handlers ──────────────────────────────────────────────────────────────

  async function abrirCaja() {
    if (abriendoRef.current) return
    if (!cajaSeleccionada) { toast.error('Seleccioná una caja'); return }
    abriendoRef.current = true
    setAbriendo(true)
    try {
      await api.post('/contabilidad/cierres-caja/', {
        caja: Number(cajaSeleccionada),
        monto_inicial: Number(montoInicial) || 0,
      }, { timeout: 10000 })
      toast.success('Caja abierta')
      setAbrirModal(false)
      setMontoInicial('')
      await Promise.all([loadCierres(), loadMiCierre()])
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      abriendoRef.current = false
      setAbriendo(false)
    }
  }

  async function openCerrarModal(cierre: CierreCaja) {
    setCerrarModal(cierre)
    setMontoContado('')
    setArqueoModal(null)
    setLoadingArqueoModal(true)
    try {
      const { data } = await api.get(`/contabilidad/cierres-caja/${cierre.id}/arqueo/`, { timeout: 8000 })
      setArqueoModal(data)
    } catch {
      // modal se abre igual, sin desglose
    } finally {
      setLoadingArqueoModal(false)
    }
  }

  async function confirmarCierre() {
    if (cerrandoRef.current || !cerrarModal) return
    cerrandoRef.current = true
    setCerrando(true)
    try {
      await api.post(`/contabilidad/cierres-caja/${cerrarModal.id}/cerrar/`, {
        monto_contado_fisico: Number(montoContado) || 0,
      }, { timeout: 10000 })
      // Cargar datos ANTES de cerrar el modal para evitar unmounts concurrentes
      // que causan removeChild en la reconciliación de React
      await Promise.all([loadCierres(), loadMiCierre()])
      setCerrarModal(null)
      setArqueoModal(null)
      toast.success('Caja cerrada')
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      cerrandoRef.current = false
      setCerrando(false)
    }
  }

  async function confirmarConciliar() {
    if (conciliandoRef.current || !conciliarModal) return
    conciliandoRef.current = true
    setConciliando(true)
    try {
      await api.post(`/contabilidad/cierres-caja/${conciliarModal.id}/conciliar/`, {
        observaciones: obsConc,
      }, { timeout: 10000 })
      await loadCierres()
      setConciliarModal(null)
      toast.success('Cierre conciliado')
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      conciliandoRef.current = false
      setConciliando(false)
    }
  }

  async function confirmarMovimiento() {
    if (movSavingRef.current || !miCierre) return
    if (!movMonto || Number(movMonto) <= 0) { toast.error('Ingresá un monto válido'); return }
    movSavingRef.current = true
    setMovSaving(true)
    try {
      await api.post(`/contabilidad/cierres-caja/${miCierre.id}/registrar-movimiento/`, {
        tipo: movTipo,
        monto: Number(movMonto),
        medio_pago: movMedioPago ? Number(movMedioPago) : null,
        descripcion: movDesc,
      }, { timeout: 10000 })
      toast.success(`${movTipo === 'INGRESO' ? 'Ingreso' : 'Egreso'} registrado`)
      setMovModal(false)
      setMovMonto('')
      setMovDesc('')
      loadArqueo(miCierre.id)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      movSavingRef.current = false
      setMovSaving(false)
    }
  }

  function abrirMovModal(tipo: 'INGRESO' | 'EGRESO') {
    setMovTipo(tipo)
    setMovMonto('')
    setMovMedioPago(mediosPago[0] ? String(mediosPago[0].id) : '')
    setMovDesc('')
    setMovModal(true)
  }

  function imprimirCierre(cierre: CierreCaja) {
    const base = api.defaults.baseURL?.replace(/\/api\/v1\/?$/, '') ?? ''
    window.open(`${base}/api/v1/contabilidad/cierres-caja/${cierre.id}/pdf/`, '_blank')
  }

  // ── Diferencia en vivo ────────────────────────────────────────────────────

  const diferenciaViva = useMemo(() => {
    if (!arqueoModal || !montoContadoDebounced) return null
    return Number(montoContadoDebounced) - arqueoModal.efectivo_esperado
  }, [arqueoModal, montoContadoDebounced])

  // ── Columns ───────────────────────────────────────────────────────────────

  const columns = useMemo<Column<CierreCaja>[]>(() => [
    {
      title: 'Caja / Cajero',
      key: 'caja',
      render: (_, r) => (
        <div>
          <p className="text-base font-semibold text-slate-800">{r.caja_nombre}</p>
          <p className="text-sm text-slate-400 mt-0.5">{r.empleado_nombre}</p>
        </div>
      ),
    },
    {
      title: 'Apertura',
      key: 'apertura',
      render: (_, r) => <span className="text-base text-slate-600">{formatDatetime(r.fecha_apertura)}</span>,
    },
    {
      title: 'Cierre',
      key: 'cierre',
      render: (_, r) => <span className="text-base text-slate-600">{formatDatetime(r.fecha_cierre)}</span>,
    },
    {
      title: 'Monto Inicial',
      key: 'inicial',
      render: (_, r) => <span className="tabular-nums text-base text-slate-700">{formatGs(r.monto_inicial)}</span>,
    },
    {
      title: 'Diferencia',
      key: 'diferencia',
      render: (_, r) => {
        if (r.diferencia_efectivo === null) return <span className="text-slate-300">—</span>
        const n = Number(r.diferencia_efectivo) || 0
        return (
          <span className={['tabular-nums text-base font-semibold', n === 0 ? 'text-emerald-700' : 'text-red-600'].join(' ')}>
            {n > 0 ? '+' : ''}{formatGs(n)}
          </span>
        )
      },
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => <Badge color={ESTADO_COLOR[r.estado] ?? 'default'}>{ESTADO_LABEL[r.estado] ?? r.estado}</Badge>,
    },
    {
      title: '',
      key: 'acciones',
      width: 180,
      render: (_, r) => (
        <div className="flex items-center gap-1 justify-end">
          {r.estado === 'ABIERTO' && (
            <button
              onClick={() => openCerrarModal(r)}
              className="flex items-center gap-1 px-2.5 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              <Lock className="w-3 h-3" />
              Cerrar
            </button>
          )}
          {r.estado === 'CERRADO' && (
            <button
              onClick={() => { setConciliarModal(r); setObsConc('') }}
              className="flex items-center gap-1 px-2.5 py-1.5 text-sm font-medium text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
            >
              <CheckCircle className="w-3 h-3" />
              Conciliar
            </button>
          )}
          <button
            onClick={() => imprimirCierre(r)}
            className="flex items-center gap-1 px-2.5 py-1.5 text-sm font-medium text-slate-500 hover:bg-slate-100 rounded-lg transition-colors"
            title="Imprimir cierre"
          >
            <Printer className="w-3.5 h-3.5" />
          </button>
        </div>
      ),
    },
  ], [])

  // ── Stats rápidas ─────────────────────────────────────────────────────────

  const stats = useMemo(() => ({
    abiertas: cierres.filter(c => c.estado === 'ABIERTO').length,
    cerradas: cierres.filter(c => c.estado === 'CERRADO').length,
    conciliadas: cierres.filter(c => c.estado === 'CONCILIADO').length,
  }), [cierres])

  const selectClass = 'border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const cajaActiva = cajas.find(c => String(c.id) === cajaSeleccionada && c.activo)

  return (
    <div className="p-4 md:p-6 space-y-5">

      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('cajas.title')}</h1>
          <p className="text-base text-slate-500 mt-0.5">{t('cajas.subtitle')}</p>
        </div>
        <Button variant="primary" onClick={() => { setAbrirModal(true); setMontoInicial('') }}>
          <Plus className="w-4 h-4" />
          {t('cajas.abrirCaja')}
        </Button>
      </div>

      {/* ── Turno activo ─────────────────────────────────────────────────────── */}
      {miCierre && (
        <div className="bg-white border border-green-200 rounded-2xl overflow-hidden shadow-sm">
          {/* Header del turno */}
          <div className="bg-green-50 border-b border-green-200 px-5 py-3 flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-2.5">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <p className="text-green-800 text-base font-semibold">
                Turno activo — {miCierre.caja_nombre}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5 text-green-600 text-sm tabular-nums">
                <Clock className="w-4 h-4" />
                {elapsedLabel(miCierre.fecha_apertura)}
              </span>
              <button
                onClick={() => loadArqueo(miCierre.id)}
                className="flex items-center gap-1 px-2.5 py-1.5 text-sm font-medium text-green-700 hover:bg-green-100 rounded-lg transition-colors"
                title="Actualizar arqueo"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Actualizar
              </button>
              <button
                onClick={() => abrirMovModal('INGRESO')}
                className="flex items-center gap-1 px-2.5 py-1.5 text-sm font-medium text-blue-700 hover:bg-blue-50 border border-blue-200 rounded-lg transition-colors"
              >
                <ArrowUpCircle className="w-3.5 h-3.5" />
                Ingreso
              </button>
              <button
                onClick={() => abrirMovModal('EGRESO')}
                className="flex items-center gap-1 px-2.5 py-1.5 text-sm font-medium text-orange-700 hover:bg-orange-50 border border-orange-200 rounded-lg transition-colors"
              >
                <ArrowDownCircle className="w-3.5 h-3.5" />
                Egreso
              </button>
            </div>
          </div>

          {/* Arqueo en vivo — 4 columnas */}
          <div className="px-5 py-4">
            {loadingArqueo ? (
              <p className="text-slate-400 text-sm">Cargando arqueo…</p>
            ) : arqueo ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">

                {/* Efectivo en cajón */}
                <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Banknote className="w-3.5 h-3.5 text-green-600" />
                    <p className="text-green-700 text-xs font-semibold uppercase tracking-wide">Efectivo cajón</p>
                  </div>
                  <p className="text-green-800 font-bold text-lg tabular-nums leading-tight">
                    {formatGs(arqueo.efectivo_esperado)}
                  </p>
                  <p className="text-green-500 text-xs mt-0.5">
                    inicial + {formatGs(arqueo.efectivo_ingresos)} − {formatGs(arqueo.efectivo_egresos)}
                  </p>
                  <p className="text-green-700 text-xs font-medium mt-1.5 bg-green-100 rounded px-1.5 py-0.5 inline-block">
                    Contar billetes
                  </p>
                </div>

                {/* POS / Terminal */}
                <div className="bg-blue-50 border border-blue-200 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <CreditCard className="w-3.5 h-3.5 text-blue-600" />
                    <p className="text-blue-700 text-xs font-semibold uppercase tracking-wide">POS / Transferencia</p>
                  </div>
                  <p className="text-blue-800 font-bold text-lg tabular-nums leading-tight">
                    {formatGs(arqueo.pos_total)}
                  </p>
                  <p className="text-blue-500 text-xs mt-0.5">ventas con terminal</p>
                  <p className="text-blue-700 text-xs font-medium mt-1.5 bg-blue-100 rounded px-1.5 py-0.5 inline-block">
                    Cotejar con POS
                  </p>
                </div>

                {/* Tarjeta prepago */}
                <div className="bg-purple-50 border border-purple-200 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <ShoppingCart className="w-3.5 h-3.5 text-purple-600" />
                    <p className="text-purple-700 text-xs font-semibold uppercase tracking-wide">Prepago RFID</p>
                  </div>
                  <p className="text-purple-800 font-bold text-lg tabular-nums leading-tight">
                    {formatGs(arqueo.prepago_total)}
                  </p>
                  <p className="text-purple-500 text-xs mt-0.5">ventas con tarjeta</p>
                  <p className="text-purple-700 text-xs font-medium mt-1.5 bg-purple-100 rounded px-1.5 py-0.5 inline-block">
                    Sin efectivo físico
                  </p>
                </div>

                {/* Egresos manuales */}
                <div className="bg-orange-50 border border-orange-200 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <ArrowDownCircle className="w-3.5 h-3.5 text-orange-600" />
                    <p className="text-orange-700 text-xs font-semibold uppercase tracking-wide">Egresos</p>
                  </div>
                  <p className="text-orange-800 font-bold text-lg tabular-nums leading-tight">
                    {formatGs(arqueo.egresos_total)}
                  </p>
                  {arqueo.egresos_por_medio.length > 0 ? (
                    <div className="mt-1.5 space-y-0.5">
                      {arqueo.egresos_por_medio.map(m => (
                        <p key={m.medio} className="text-orange-600 text-xs tabular-nums">
                          {m.medio}: {m.total.toLocaleString('es-PY')} Gs.
                        </p>
                      ))}
                    </div>
                  ) : (
                    <p className="text-orange-400 text-xs mt-0.5">sin egresos</p>
                  )}
                </div>

              </div>
            ) : (
              <p className="text-slate-400 text-sm">Sin movimientos registrados aún.</p>
            )}
          </div>
        </div>
      )}

      {/* Stats rápidas */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Abiertas', value: stats.abiertas, color: 'text-green-600', icon: Banknote },
          { label: 'Cerradas', value: stats.cerradas, color: 'text-blue-600', icon: Lock },
          { label: 'Conciliadas', value: stats.conciliadas, color: 'text-purple-600', icon: CheckCircle },
        ].map(({ label, value, color, icon: Icon }) => (
          <div key={label} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3 flex items-start justify-between gap-2">
            <div>
              <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
              <p className={`text-2xl font-bold mt-0.5 tabular-nums ${color}`}>{value}</p>
            </div>
            <Icon className={`w-5 h-5 mt-1 ${color} opacity-40`} />
          </div>
        ))}
      </div>

      {/* Filtros */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3 flex flex-wrap gap-3 items-center">
        <LayoutGrid className="w-4 h-4 text-slate-400" />
        <select value={filterEstado} onChange={e => { setFilterEstado(e.target.value); setPage(1) }} className={selectClass}>
          <option value="">Todos los estados</option>
          <option value="ABIERTO">Abiertas</option>
          <option value="CERRADO">Cerradas</option>
          <option value="CONCILIADO">Conciliadas</option>
        </select>
        <select value={filterCaja} onChange={e => { setFilterCaja(e.target.value); setPage(1) }} className={selectClass}>
          <option value="">Todas las cajas</option>
          {cajas.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}
        </select>
      </div>

      {/* Tabla */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden p-1">
        <Table
          columns={columns}
          dataSource={cierres}
          rowKey="id"
          loading={loading}
          pageSize={15}
          page={page}
          onPageChange={setPage}
          total={total}
        />
      </div>

      {/* ── Modal Abrir Caja ───────────────────────────────────────────────── */}
      <Modal
        open={abrirModal}
        title="Abrir Caja"
        onCancel={() => { setAbrirModal(false); setMontoInicial('') }}
        onOk={abrirCaja}
        okText="Abrir Caja"
        confirmLoading={abriendo}
        width={420}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
              Caja
            </label>
            <select
              value={cajaSeleccionada}
              onChange={e => setCajaSeleccionada(e.target.value)}
              className="w-full border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors"
            >
              <option value="">Seleccionar caja...</option>
              {cajas.filter(c => c.activo).map(c => (
                <option key={c.id} value={c.id}>{c.nombre}{c.ubicacion ? ` — ${c.ubicacion}` : ''}</option>
              ))}
            </select>
          </div>
          {cajaActiva && (
            <div className="bg-green-50 border border-green-100 rounded-xl px-4 py-2.5">
              <p className="text-sm text-green-700 font-medium">{cajaActiva.nombre}</p>
              {cajaActiva.ubicacion && <p className="text-sm text-green-600 mt-0.5">{cajaActiva.ubicacion}</p>}
            </div>
          )}
          <Input
            label="Monto Inicial (Gs.)"
            type="number"
            placeholder="0"
            value={montoInicial}
            onChange={e => setMontoInicial(e.target.value)}
            min={0}
            step={10000}
          />
        </div>
      </Modal>

      {/* ── Modal Cerrar Caja ──────────────────────────────────────────────── */}
      <Modal
        open={!!cerrarModal}
        title={`Cerrar Caja — ${cerrarModal?.caja_nombre ?? ''}`}
        onCancel={() => setCerrarModal(null)}
        onOk={confirmarCierre}
        okText="Confirmar Cierre"
        confirmLoading={cerrando}
        width={500}
      >
        <div className="space-y-4">
          {/* Info básica */}
          <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-1.5 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Apertura:</span>
              <span className="font-medium text-slate-700">{formatDatetime(cerrarModal?.fecha_apertura)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Monto inicial:</span>
              <span className="font-semibold text-slate-800 tabular-nums">{formatGs(cerrarModal?.monto_inicial)}</span>
            </div>
          </div>

          {/* Arqueo detallado */}
          {loadingArqueoModal ? (
            <div className="flex items-center gap-2 text-slate-400 text-sm py-2">
              <ShoppingCart className="w-4 h-4 animate-pulse" />
              Cargando arqueo…
            </div>
          ) : arqueoModal ? (
            <div className="border border-slate-200 rounded-xl overflow-hidden text-sm">
              <div className="bg-slate-50 px-4 py-2 font-semibold text-slate-600 text-xs uppercase tracking-wide">
                Desglose de movimientos
              </div>
              <div className="divide-y divide-slate-100">
                {/* Ingresos */}
                {arqueoModal.ingresos_por_medio.map(m => (
                  <div key={m.medio} className="flex justify-between px-4 py-2">
                    <span className="text-slate-600 flex items-center gap-1.5">
                      <ArrowUpCircle className="w-3.5 h-3.5 text-green-500" />
                      {m.medio}
                    </span>
                    <span className="font-medium text-green-700 tabular-nums">+{formatGs(m.total)}</span>
                  </div>
                ))}
                {/* Egresos */}
                {arqueoModal.egresos_por_medio.map(m => (
                  <div key={m.medio} className="flex justify-between px-4 py-2">
                    <span className="text-slate-600 flex items-center gap-1.5">
                      <ArrowDownCircle className="w-3.5 h-3.5 text-orange-500" />
                      {m.medio}
                    </span>
                    <span className="font-medium text-orange-700 tabular-nums">-{formatGs(m.total)}</span>
                  </div>
                ))}
                {/* Total esperado */}
                <div className="flex justify-between px-4 py-2.5 bg-blue-50">
                  <span className="font-semibold text-blue-800">Efectivo esperado</span>
                  <span className="font-bold text-blue-800 tabular-nums">{formatGs(arqueoModal.efectivo_esperado)}</span>
                </div>
              </div>
            </div>
          ) : null}

          {/* Input monto contado */}
          <Input
            label="Monto Contado en Efectivo (Gs.)"
            type="number"
            placeholder="0"
            value={montoContado}
            onChange={e => setMontoContado(e.target.value)}
            min={0}
          />

          {/* Diferencia en vivo */}
          {diferenciaViva !== null && (
            <div className={[
              'flex justify-between px-4 py-2.5 rounded-xl text-sm font-semibold',
              diferenciaViva === 0
                ? 'bg-emerald-50 text-emerald-700'
                : diferenciaViva > 0
                ? 'bg-green-50 text-green-700'
                : 'bg-red-50 text-red-700',
            ].join(' ')}>
              <span>Diferencia</span>
              <span className="tabular-nums">
                {diferenciaViva > 0 ? '+' : ''}{formatGs(diferenciaViva)}
              </span>
            </div>
          )}
        </div>
      </Modal>

      {/* ── Modal Conciliar ────────────────────────────────────────────────── */}
      <Modal
        open={!!conciliarModal}
        title={`Conciliar Cierre — ${conciliarModal?.caja_nombre ?? ''}`}
        onCancel={() => setConciliarModal(null)}
        onOk={confirmarConciliar}
        okText="Conciliar"
        confirmLoading={conciliando}
        width={440}
      >
        <div className="space-y-4">
          {conciliarModal && (
            <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-1.5 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Monto contado:</span>
                <span className="font-semibold tabular-nums text-slate-800">
                  {formatGs(conciliarModal.monto_contado_fisico)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Diferencia:</span>
                <span className={['font-semibold tabular-nums', Number(conciliarModal.diferencia_efectivo) === 0 ? 'text-emerald-700' : 'text-red-600'].join(' ')}>
                  {formatGs(conciliarModal.diferencia_efectivo)}
                </span>
              </div>
            </div>
          )}
          <div>
            <label className="block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
              Observaciones del Contador
            </label>
            <textarea
              value={obsConc}
              onChange={e => setObsConc(e.target.value)}
              rows={3}
              placeholder="Notas de conciliación (opcional)..."
              className="w-full border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors resize-none"
            />
          </div>
        </div>
      </Modal>

      {/* ── Modal Movimiento Manual ─────────────────────────────────────────── */}
      <Modal
        open={movModal}
        title={movTipo === 'INGRESO' ? 'Registrar Ingreso' : 'Registrar Egreso'}
        onCancel={() => setMovModal(false)}
        onOk={confirmarMovimiento}
        okText={movTipo === 'INGRESO' ? 'Registrar Ingreso' : 'Registrar Egreso'}
        confirmLoading={movSaving}
        width={420}
      >
        <div className="space-y-4">
          {/* Tipo toggle */}
          <div className="flex gap-2">
            {(['INGRESO', 'EGRESO'] as const).map(t => (
              <button
                key={t}
                onClick={() => setMovTipo(t)}
                className={[
                  'flex-1 flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-sm font-semibold border transition-colors',
                  movTipo === t
                    ? t === 'INGRESO'
                      ? 'bg-green-50 border-green-300 text-green-700'
                      : 'bg-orange-50 border-orange-300 text-orange-700'
                    : 'bg-white border-slate-200 text-slate-500 hover:bg-slate-50',
                ].join(' ')}
              >
                {t === 'INGRESO'
                  ? <ArrowUpCircle className="w-4 h-4" />
                  : <ArrowDownCircle className="w-4 h-4" />}
                {t === 'INGRESO' ? 'Ingreso' : 'Egreso'}
              </button>
            ))}
          </div>

          <Input
            label="Monto (Gs.)"
            type="number"
            placeholder="0"
            value={movMonto}
            onChange={e => setMovMonto(e.target.value)}
            min={1}
            step={10000}
          />

          <div>
            <label className="block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
              Medio de Pago
            </label>
            <select
              value={movMedioPago}
              onChange={e => setMovMedioPago(e.target.value)}
              className="w-full border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors"
            >
              <option value="">Sin especificar</option>
              {mediosPago.map(m => <option key={m.id} value={m.id}>{m.descripcion}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
              Descripción
            </label>
            <input
              type="text"
              value={movDesc}
              onChange={e => setMovDesc(e.target.value)}
              placeholder={movTipo === 'INGRESO' ? 'Ej: Fondo de cambio adicional' : 'Ej: Compra de insumos'}
              className="w-full border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors"
            />
          </div>
        </div>
      </Modal>

    </div>
  )
}
