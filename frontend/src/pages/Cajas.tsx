import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import {
  Plus, Lock, CheckCircle, Banknote, LayoutGrid,
  Clock, ShoppingCart, CreditCard,
  Printer, ArrowUpCircle, ArrowDownCircle, RefreshCw,
} from 'lucide-react'
import api from '../services/api'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'
import {
  formatGs, formatDatetime, elapsedLabel,
  type Caja, type CierreCaja, type ArqueoData, type MedioPago,
  ESTADO_COLOR, ESTADO_LABEL,
} from './cajas/shared'
import ModalAbrir from './cajas/ModalAbrir'
import ModalCerrar from './cajas/ModalCerrar'
import ModalConciliar from './cajas/ModalConciliar'
import ModalMovimiento from './cajas/ModalMovimiento'

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

  const [miCierre, setMiCierre] = useState<CierreCaja | null | undefined>(undefined)
  const [arqueo, setArqueo] = useState<ArqueoData | null>(null)
  const [loadingArqueo, setLoadingArqueo] = useState(false)

  const [abrirModal, setAbrirModal] = useState(false)
  const [cerrarModal, setCerrarModal] = useState<CierreCaja | null>(null)
  const [conciliarModal, setConciliarModal] = useState<CierreCaja | null>(null)
  const [movTipo, setMovTipo] = useState<'INGRESO' | 'EGRESO' | null>(null)

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

  // eslint-disable-next-line react-hooks/set-state-in-effect
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

  // eslint-disable-next-line react-hooks/set-state-in-effect
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
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (miCierre?.id) loadArqueo(miCierre.id)
    else setArqueo(null)
  }, [miCierre, loadArqueo])

  // ── Datos auxiliares ──────────────────────────────────────────────────────

  useEffect(() => {
    api.get('/contabilidad/cajas/')
      .then(({ data }) => {
        const lista: Caja[] = data.results ?? data
        setCajas(lista)
      })
      .catch(() => toast.error('Error al cargar cajas'))

    api.get('/core/medios-pago/', { params: { activo: true } })
      .then(({ data }) => setMediosPago(data.results ?? data))
      .catch(() => toast.error('Error al cargar medios de pago'))
  }, [])

  // ── Actions ───────────────────────────────────────────────────────────────

  function imprimirCierre(cierre: CierreCaja) {
    const base = api.defaults.baseURL?.replace(/\/api\/v1\/?$/, '') ?? ''
    window.open(`${base}/api/v1/contabilidad/cierres-caja/${cierre.id}/pdf/`, '_blank')
  }

  // ── Columns ───────────────────────────────────────────────────────────────

  const columns = useMemo<Column<CierreCaja>[]>(() => [
    {
      title: 'Caja / Cajero', key: 'caja',
      render: (_, r) => (
        <div>
          <p className="text-base font-semibold text-slate-800">{r.caja_nombre}</p>
          <p className="text-sm text-slate-400 mt-0.5">{r.empleado_nombre}</p>
        </div>
      ),
    },
    {
      title: 'Apertura', key: 'apertura',
      render: (_, r) => <span className="text-base text-slate-600">{formatDatetime(r.fecha_apertura)}</span>,
    },
    {
      title: 'Cierre', key: 'cierre',
      render: (_, r) => <span className="text-base text-slate-600">{formatDatetime(r.fecha_cierre)}</span>,
    },
    {
      title: 'Monto Inicial', key: 'inicial',
      render: (_, r) => <span className="tabular-nums text-base text-slate-700">{formatGs(r.monto_inicial)}</span>,
    },
    {
      title: 'Diferencia', key: 'diferencia',
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
      title: 'Estado', key: 'estado',
      render: (_, r) => <Badge color={ESTADO_COLOR[r.estado] ?? 'default'}>{ESTADO_LABEL[r.estado] ?? r.estado}</Badge>,
    },
    {
      title: '', key: 'acciones', width: 180,
      render: (_, r) => (
        <div className="flex items-center gap-1 justify-end">
          {r.estado === 'ABIERTO' && (
            <button
              onClick={() => setCerrarModal(r)}
              className="flex items-center gap-1 px-2.5 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              <Lock className="w-3 h-3" />
              Cerrar
            </button>
          )}
          {r.estado === 'CERRADO' && (
            <button
              onClick={() => setConciliarModal(r)}
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
    abiertas: cierres.filter(c => c.caja_activo && c.estado === 'ABIERTO').length,
    cerradas: cierres.filter(c => c.caja_activo && c.estado === 'CERRADO').length,
    conciliadas: cierres.filter(c => c.caja_activo && c.estado === 'CONCILIADO').length,
  }), [cierres])

  const selectClass = 'border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'

  return (
    <div className="p-4 md:p-6 space-y-5">

      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('cajas.title')}</h1>
          <p className="text-base text-slate-500 mt-0.5">{t('cajas.subtitle')}</p>
        </div>
        <Button variant="primary" onClick={() => setAbrirModal(true)}>
          <Plus className="w-4 h-4" />
          {t('cajas.abrirCaja')}
        </Button>
      </div>

      {/* ── Turno activo ─────────────────────────────────────────────────────── */}
      {miCierre && (
        <div className="bg-white border border-green-200 rounded-2xl overflow-hidden shadow-sm">
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
                onClick={() => setMovTipo('INGRESO')}
                className="flex items-center gap-1 px-2.5 py-1.5 text-sm font-medium text-blue-700 hover:bg-blue-50 border border-blue-200 rounded-lg transition-colors"
              >
                <ArrowUpCircle className="w-3.5 h-3.5" />
                Ingreso
              </button>
              <button
                onClick={() => setMovTipo('EGRESO')}
                className="flex items-center gap-1 px-2.5 py-1.5 text-sm font-medium text-orange-700 hover:bg-orange-50 border border-orange-200 rounded-lg transition-colors"
              >
                <ArrowDownCircle className="w-3.5 h-3.5" />
                Egreso
              </button>
            </div>
          </div>

          <div className="px-5 py-4">
            {loadingArqueo ? (
              <p className="text-slate-400 text-sm">Cargando arqueo…</p>
            ) : arqueo ? (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Banknote className="w-3.5 h-3.5 text-green-600" />
                    <p className="text-green-700 text-xs font-semibold uppercase tracking-wide">Efectivo Caja</p>
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

                {arqueo.medios_pago_totales.map(m => (
                  <div key={m.medio} className="bg-blue-50 border border-blue-200 rounded-xl px-4 py-3">
                    <div className="flex items-center gap-1.5 mb-1">
                      <CreditCard className="w-3.5 h-3.5 text-blue-600" />
                      <p className="text-blue-700 text-xs font-semibold uppercase tracking-wide">{m.medio}</p>
                    </div>
                    <p className="text-blue-800 font-bold text-lg tabular-nums leading-tight">
                      {formatGs(m.total)}
                    </p>
                    <p className="text-blue-500 text-xs mt-0.5">ventas con este medio</p>
                  </div>
                ))}

                <div className="bg-purple-50 border border-purple-200 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <ShoppingCart className="w-3.5 h-3.5 text-purple-600" />
                    <p className="text-purple-700 text-xs font-semibold uppercase tracking-wide">Prepago</p>
                  </div>
                  <p className="text-purple-800 font-bold text-lg tabular-nums leading-tight">
                    {formatGs(arqueo.prepago_total)}
                  </p>
                  <p className="text-purple-500 text-xs mt-0.5">ventas con saldo de tarjeta</p>
                  <p className="text-purple-700 text-xs font-medium mt-1.5 bg-purple-100 rounded px-1.5 py-0.5 inline-block">
                    Ya cobrado al cargar saldo
                  </p>
                </div>

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

      <ModalAbrir
        open={abrirModal}
        cajas={cajas}
        onClose={() => setAbrirModal(false)}
        onSaved={async () => { await Promise.all([loadCierres(), loadMiCierre()]) }}
      />
      <ModalCerrar
        cierre={cerrarModal}
        onClose={() => setCerrarModal(null)}
        onSaved={async () => { await Promise.all([loadCierres(), loadMiCierre()]) }}
      />
      <ModalConciliar
        cierre={conciliarModal}
        onClose={() => setConciliarModal(null)}
        onSaved={() => loadCierres()}
      />
      <ModalMovimiento
        tipo={movTipo}
        miCierre={miCierre ?? null}
        mediosPago={mediosPago}
        onClose={() => setMovTipo(null)}
        onSaved={() => { if (miCierre) loadArqueo(miCierre.id) }}
      />
    </div>
  )
}
