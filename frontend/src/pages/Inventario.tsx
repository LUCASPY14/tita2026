import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import {
  Package, Plus, CheckCircle, XCircle,
  TrendingUp, TrendingDown, AlertTriangle, Bell, Clock,
} from 'lucide-react'
import api from '../services/api'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'
import {
  formatFecha,
  type Producto, type AjusteInventario, type MovimientoStock, type Lote,
  type AlertaStock, type AlertaVencimiento, type TabKey,
  ESTADO_COLOR, TIPO_AJUSTE_COLOR, TIPO_MOV_COLOR,
  ALERTA_COLOR, VENC_COLOR, VENC_LABEL, ACCION_COLOR,
} from './inventario/shared'
import ModalAjuste from './inventario/ModalAjuste'
import ModalAprobar from './inventario/ModalAprobar'
import ModalRechazar from './inventario/ModalRechazar'
import ModalAccionVencimiento from './inventario/ModalAccionVencimiento'

export default function Inventario() {
  const { t } = useTranslation()
  const [tab, setTab] = useState<TabKey>('ajustes')

  const [productos, setProductos] = useState<Producto[]>([])

  // ── Ajustes ───────────────────────────────────────────────────────
  const [ajustes, setAjustes] = useState<AjusteInventario[]>([])
  const [loadingAjustes, setLoadingAjustes] = useState(false)
  const [filterEstado, setFilterEstado] = useState('')
  const [filterTipoAjuste, setFilterTipoAjuste] = useState('')
  const [pageAjustes, setPageAjustes] = useState(1)
  const [totalAjustes, setTotalAjustes] = useState(0)

  const [ajusteOpen, setAjusteOpen] = useState(false)
  const [aprobar, setAprobar] = useState<number | null>(null)
  const [rechazar, setRechazar] = useState<number | null>(null)

  // ── Movimientos ───────────────────────────────────────────────────
  const [movimientos, setMovimientos] = useState<MovimientoStock[]>([])
  const [loadingMov, setLoadingMov] = useState(false)
  const [filterProductoMov, setFilterProductoMov] = useState('')
  const [filterTipoMov, setFilterTipoMov] = useState('')
  const [pageMov, setPageMov] = useState(1)
  const [totalMov, setTotalMov] = useState(0)
  const [sortMovKey, setSortMovKey] = useState('fecha')
  const [sortMovDir, setSortMovDir] = useState<'asc' | 'desc'>('desc')
  const searchTimerMov = useRef<ReturnType<typeof setTimeout>>(undefined)
  const requestIdAjustesRef = useRef(0)
  const requestIdMovRef = useRef(0)
  const requestIdLotesRef = useRef(0)

  // ── Lotes ─────────────────────────────────────────────────────────
  const [lotes, setLotes] = useState<Lote[]>([])
  const [loadingLotes, setLoadingLotes] = useState(false)
  const [filterVencido, setFilterVencido] = useState('')
  const [filterProductoLote, setFilterProductoLote] = useState('')
  const [pageLotes, setPageLotes] = useState(1)
  const [totalLotes, setTotalLotes] = useState(0)
  const [sortLotesKey, setSortLotesKey] = useState('fecha_vencimiento')
  const [sortLotesDir, setSortLotesDir] = useState<'asc' | 'desc'>('asc')

  // ── Load catalogs ─────────────────────────────────────────────────
  useEffect(() => {
    api.get('/productos/productos/', { params: { page_size: 500 } })
      .then(({ data }) => setProductos(data.results ?? []))
      .catch(() => toast.error('Error al cargar productos'))
  }, [])

  // ── Load ajustes ──────────────────────────────────────────────────
  const loadAjustes = useCallback(async (estado: string, tipo: string, p: number) => {
    const requestId = ++requestIdAjustesRef.current
    setLoadingAjustes(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: 15, ordering: '-fecha' }
      if (estado) params.estado = estado
      if (tipo) params.tipo = tipo
      const { data } = await api.get('/inventario/ajustes/', { params })
      if (requestId !== requestIdAjustesRef.current) return
      setAjustes(data.results ?? [])
      setTotalAjustes(data.count ?? 0)
    } catch {
      if (requestId !== requestIdAjustesRef.current) return
      toast.error('Error al cargar ajustes')
    } finally {
      if (requestId === requestIdAjustesRef.current) setLoadingAjustes(false)
    }
  }, [])

  useEffect(() => {
    if (tab === 'ajustes') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPageAjustes(1)
      loadAjustes(filterEstado, filterTipoAjuste, 1)
    }
  }, [tab, filterEstado, filterTipoAjuste, loadAjustes])

  // ── Load movimientos ──────────────────────────────────────────────
  const loadMovimientos = useCallback(async (prod: string, tipo: string, p: number) => {
    const requestId = ++requestIdMovRef.current
    setLoadingMov(true)
    try {
      const ordering = sortMovDir === 'asc' ? sortMovKey : `-${sortMovKey}`
      const params: Record<string, unknown> = { page: p, page_size: 15, ordering }
      if (prod) params.producto = prod
      if (tipo) params.tipo = tipo
      const { data } = await api.get('/inventario/movimientos/', { params })
      if (requestId !== requestIdMovRef.current) return
      setMovimientos(data.results ?? [])
      setTotalMov(data.count ?? 0)
    } catch {
      if (requestId !== requestIdMovRef.current) return
      toast.error('Error al cargar movimientos')
    } finally {
      if (requestId === requestIdMovRef.current) setLoadingMov(false)
    }
  }, [sortMovKey, sortMovDir])

  useEffect(() => {
    if (tab !== 'movimientos') return
    clearTimeout(searchTimerMov.current)
    searchTimerMov.current = setTimeout(() => {
      setPageMov(1)
      loadMovimientos(filterProductoMov, filterTipoMov, 1)
    }, 300)
    return () => clearTimeout(searchTimerMov.current)
  }, [tab, filterProductoMov, filterTipoMov, loadMovimientos])

  // ── Load lotes ────────────────────────────────────────────────────
  const loadLotes = useCallback(async (prod: string, vencido: string, p: number) => {
    const requestId = ++requestIdLotesRef.current
    setLoadingLotes(true)
    try {
      const ordering = sortLotesDir === 'asc' ? sortLotesKey : `-${sortLotesKey}`
      const params: Record<string, unknown> = { page: p, page_size: 15, ordering }
      if (prod) params.producto = prod
      if (vencido !== '') params.bloqueado = vencido
      const { data } = await api.get('/inventario/lotes/', { params })
      if (requestId !== requestIdLotesRef.current) return
      setLotes(data.results ?? [])
      setTotalLotes(data.count ?? 0)
    } catch {
      if (requestId !== requestIdLotesRef.current) return
      toast.error('Error al cargar lotes')
    } finally {
      if (requestId === requestIdLotesRef.current) setLoadingLotes(false)
    }
  }, [sortLotesKey, sortLotesDir])

  useEffect(() => {
    if (tab === 'lotes') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPageLotes(1)
      loadLotes(filterProductoLote, filterVencido, 1)
    }
  }, [tab, filterProductoLote, filterVencido, loadLotes])

  // ── Alertas de stock ──────────────────────────────────────────────
  const [alertas, setAlertas] = useState<AlertaStock[]>([])
  const [loadingAlertas, setLoadingAlertas] = useState(false)
  const [totalAlertas, setTotalAlertas] = useState(0)
  const [pageAlertas, setPageAlertas] = useState(1)

  const loadAlertas = useCallback(async (p: number) => {
    setLoadingAlertas(true)
    try {
      const { data } = await api.get('/inventario/alertas-stock/', {
        params: { activa: true, page: p, page_size: 15 },
      })
      setAlertas(data.results ?? [])
      setTotalAlertas(data.count ?? 0)
    } catch {
      toast.error('Error al cargar alertas de stock')
    } finally {
      setLoadingAlertas(false)
    }
  }, [])

  useEffect(() => {
    if (tab === 'alertas') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPageAlertas(1)
      loadAlertas(1)
    }
  }, [tab, loadAlertas])

  // ── Alertas de vencimiento ────────────────────────────────────────
  const [alertasVenc, setAlertasVenc] = useState<AlertaVencimiento[]>([])
  const [loadingAlertasVenc, setLoadingAlertasVenc] = useState(false)
  const [totalAlertasVenc, setTotalAlertasVenc] = useState(0)
  const [pageAlertasVenc, setPageAlertasVenc] = useState(1)
  const [accionModal, setAccionModal] = useState<AlertaVencimiento | null>(null)

  const loadAlertasVenc = useCallback(async (p: number) => {
    setLoadingAlertasVenc(true)
    try {
      const { data } = await api.get('/inventario/alertas-vencimiento/', {
        params: { page: p, page_size: 15 },
      })
      setAlertasVenc(data.results ?? [])
      setTotalAlertasVenc(data.count ?? 0)
    } catch {
      toast.error('Error al cargar alertas de vencimiento')
    } finally {
      setLoadingAlertasVenc(false)
    }
  }, [])

  useEffect(() => {
    if (tab === 'alertas') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPageAlertasVenc(1)
      loadAlertasVenc(1)
    }
  }, [tab, loadAlertasVenc])

  // ── Columns ──────────────────────────────────────────────────────

  const colsAjustes: Column<AjusteInventario>[] = [
    {
      title: 'ID', key: 'id', dataIndex: 'id', width: 60,
      render: v => <span className="font-mono text-sm text-slate-500">#{v as number}</span>,
    },
    {
      title: 'Tipo', key: 'tipo',
      render: (_, r) => <Badge color={TIPO_AJUSTE_COLOR[r.tipo] ?? 'default'}>{r.tipo}</Badge>,
    },
    {
      title: 'Estado', key: 'estado',
      render: (_, r) => <Badge color={ESTADO_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge>,
    },
    {
      title: 'Motivo', key: 'motivo',
      render: (_, r) => <span className="text-sm text-slate-700">{r.motivo}</span>,
    },
    {
      title: 'Productos', key: 'productos',
      render: (_, r) => (
        <span className="text-sm text-slate-500">{r.detalles?.length ?? 0} ítem(s)</span>
      ),
    },
    {
      title: 'Fecha', key: 'fecha',
      render: (_, r) => <span className="text-sm text-slate-500">{formatFecha(r.fecha)}</span>,
    },
    {
      title: '', key: 'acciones', width: 170,
      render: (_, r) => r.estado === 'PENDIENTE' ? (
        <div className="flex gap-1.5">
          <Button size="sm" variant="primary" onClick={() => setAprobar(r.id)}>
            <CheckCircle className="w-3.5 h-3.5" />
            Aprobar
          </Button>
          <Button size="sm" variant="danger" onClick={() => setRechazar(r.id)}>
            <XCircle className="w-3.5 h-3.5" />
          </Button>
        </div>
      ) : null,
    },
  ]

  const colsMov: Column<MovimientoStock>[] = [
    {
      title: 'Fecha', key: 'fecha', sortable: true,
      render: (_, r) => <span className="text-sm text-slate-500">{formatFecha(r.fecha)}</span>,
    },
    {
      title: 'Producto', key: 'prod',
      render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.producto_nombre}</span>,
    },
    {
      title: 'Tipo', key: 'tipo',
      render: (_, r) => <Badge color={TIPO_MOV_COLOR[r.tipo] ?? 'default'}>{r.tipo}</Badge>,
    },
    {
      title: 'Cantidad', key: 'cantidad', sortable: true,
      render: (_, r) => {
        const isEntry = r.tipo === 'ENTRADA'
        return (
          <span className={`tabular-nums font-semibold text-sm flex items-center gap-0.5 ${isEntry ? 'text-emerald-700' : 'text-slate-700'}`}>
            {isEntry ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {r.cantidad}
          </span>
        )
      },
    },
    {
      title: 'Motivo', key: 'motivo',
      render: (_, r) => <span className="text-sm text-slate-500">{r.motivo || '—'}</span>,
    },
  ]

  const colsLotes: Column<Lote>[] = [
    {
      title: 'Producto', key: 'prod',
      render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.producto_nombre}</span>,
    },
    {
      title: 'Nro. Lote', key: 'lote',
      render: (_, r) => <span className="font-mono text-sm text-slate-700">{r.numero_lote}</span>,
    },
    {
      title: 'Vencimiento', key: 'fecha_vencimiento', sortable: true,
      render: (_, r) => (
        <span className={`text-sm font-medium ${r.esta_vencido ? 'text-red-600' : r.dias_hasta_vencimiento <= 30 ? 'text-orange-600' : 'text-slate-700'}`}>
          {formatFecha(r.fecha_vencimiento)}
        </span>
      ),
    },
    {
      title: 'Días', key: 'dias',
      render: (_, r) => (
        <span className={`tabular-nums font-semibold text-sm ${r.esta_vencido ? 'text-red-600' : r.dias_hasta_vencimiento <= 30 ? 'text-orange-600' : 'text-emerald-700'}`}>
          {r.esta_vencido ? 'VENCIDO' : `${r.dias_hasta_vencimiento}d`}
        </span>
      ),
    },
    {
      title: 'Cantidad', key: 'cantidad', sortable: true,
      render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{r.cantidad}</span>,
    },
    {
      title: 'Estado', key: 'estado',
      render: (_, r) => (
        <div className="flex gap-1">
          {r.esta_vencido && <Badge color="red">Vencido</Badge>}
          {r.bloqueado && <Badge color="orange">Bloqueado</Badge>}
          {!r.esta_vencido && !r.bloqueado && <Badge color="green">OK</Badge>}
        </div>
      ),
    },
  ]

  const lotesConAlerta = useMemo(
    () => lotes.filter(l => l.esta_vencido || l.dias_hasta_vencimiento <= 30).length,
    [lotes],
  )

  const colsAlertasVenc: Column<AlertaVencimiento>[] = [
    {
      title: 'Producto', key: 'producto',
      render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.producto_nombre}</span>,
    },
    {
      title: 'Lote', key: 'lote',
      render: (_, r) => <span className="font-mono text-sm text-slate-500">{r.lote_numero}</span>,
    },
    {
      title: 'Urgencia', key: 'tipo',
      render: (_, r) => (
        <Badge color={VENC_COLOR[r.tipo] ?? 'default'}>{VENC_LABEL[r.tipo] ?? r.tipo}</Badge>
      ),
    },
    {
      title: 'Días', key: 'dias',
      render: (_, r) => (
        <span className={`tabular-nums font-bold text-sm ${r.dias_restantes < 0 ? 'text-red-600' : r.dias_restantes <= 7 ? 'text-orange-600' : 'text-slate-700'}`}>
          {r.dias_restantes < 0 ? `${Math.abs(r.dias_restantes)}d vencido` : `${r.dias_restantes}d`}
        </span>
      ),
    },
    {
      title: 'Vence', key: 'fecha_vencimiento',
      render: (_, r) => <span className="text-sm text-slate-500">{formatFecha(r.fecha_vencimiento)}</span>,
    },
    {
      title: 'Cant. lote', key: 'cantidad',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{Number(r.cantidad_lote)}</span>,
    },
    {
      title: 'Acción', key: 'accion',
      render: (_, r) => (
        <Badge color={ACCION_COLOR[r.accion_tomada ?? 'PENDIENTE'] ?? 'default'}>
          {r.accion_tomada ?? 'PENDIENTE'}
        </Badge>
      ),
    },
    {
      title: '', key: 'btn', width: 130,
      render: (_, r) => (
        <Button size="sm" variant="ghost" onClick={() => setAccionModal(r)}>
          Registrar acción
        </Button>
      ),
    },
  ]

  const colsAlertas: Column<AlertaStock>[] = [
    {
      title: 'Producto', key: 'producto',
      render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.producto_nombre}</span>,
    },
    {
      title: 'Tipo', key: 'tipo',
      render: (_, r) => (
        <Badge color={ALERTA_COLOR[r.tipo] ?? 'default'}>{r.tipo.replace(/_/g, ' ')}</Badge>
      ),
    },
    {
      title: 'Stock Actual', key: 'stock_actual',
      render: (_, r) => (
        <span className="tabular-nums text-sm font-bold text-red-600">{Number(r.stock_actual)}</span>
      ),
    },
    {
      title: 'Stock Mínimo', key: 'stock_minimo',
      render: (_, r) => (
        <span className="tabular-nums text-sm text-slate-500">{Number(r.stock_minimo)}</span>
      ),
    },
    {
      title: 'Generada', key: 'fecha_generada',
      render: (_, r) => <span className="text-sm text-slate-400">{formatFecha(r.fecha_generada)}</span>,
    },
  ]

  const TABS: { key: TabKey; label: string; icon: typeof Package }[] = [
    { key: 'ajustes', label: 'Ajustes', icon: Package },
    { key: 'movimientos', label: 'Movimientos', icon: TrendingUp },
    { key: 'lotes', label: 'Lotes y Vencimientos', icon: AlertTriangle },
    { key: 'alertas', label: 'Alertas de Stock', icon: Bell },
  ]

  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('inventario.title')}</h1>
          <p className="text-base text-slate-500 mt-0.5">{t('inventario.subtitle')}</p>
        </div>
        {tab === 'ajustes' && (
          <Button variant="primary" onClick={() => setAjusteOpen(true)}>
            <Plus className="w-4 h-4" />
            {t('inventario.nuevoAjuste')}
          </Button>
        )}
      </div>

      <div className="border-b border-slate-200">
        <div className="flex gap-0">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                tab === key ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
              {key === 'lotes' && lotesConAlerta > 0 && (
                <span className="bg-orange-100 text-orange-700 text-xs px-1.5 py-0.5 rounded-full font-semibold">
                  {lotesConAlerta}
                </span>
              )}
              {key === 'alertas' && (totalAlertas + totalAlertasVenc) > 0 && (
                <span className="bg-red-100 text-red-700 text-xs px-1.5 py-0.5 rounded-full font-semibold">
                  {totalAlertas + totalAlertasVenc}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* ── Ajustes tab ──────────────────────────────────────────── */}
      {tab === 'ajustes' && (
        <>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap items-end gap-4">
            <div>
              <label className={labelClass}>Estado</label>
              <select value={filterEstado} onChange={e => { setFilterEstado(e.target.value); setPageAjustes(1) }} className={`${inputClass} w-auto`}>
                <option value="">Todos</option>
                <option value="PENDIENTE">Pendiente</option>
                <option value="APROBADO">Aprobado</option>
                <option value="RECHAZADO">Rechazado</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Tipo</label>
              <select value={filterTipoAjuste} onChange={e => { setFilterTipoAjuste(e.target.value); setPageAjustes(1) }} className={`${inputClass} w-auto`}>
                <option value="">Todos</option>
                <option value="AUMENTO">Aumento</option>
                <option value="MERMA">Merma</option>
              </select>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table columns={colsAjustes} dataSource={ajustes} rowKey="id" loading={loadingAjustes}
                pageSize={15} page={pageAjustes} onPageChange={p => { setPageAjustes(p); loadAjustes(filterEstado, filterTipoAjuste, p) }} total={totalAjustes} />
            </div>
          </div>
        </>
      )}

      {/* ── Movimientos tab ──────────────────────────────────────── */}
      {tab === 'movimientos' && (
        <>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap items-end gap-4">
            <div className="w-64">
              <label className={labelClass}>Producto</label>
              <select value={filterProductoMov} onChange={e => setFilterProductoMov(e.target.value)} className={inputClass}>
                <option value="">Todos</option>
                {productos.map(p => <option key={p.id} value={p.id}>{p.descripcion}</option>)}
              </select>
            </div>
            <div>
              <label className={labelClass}>Tipo</label>
              <select value={filterTipoMov} onChange={e => setFilterTipoMov(e.target.value)} className={`${inputClass} w-auto`}>
                <option value="">Todos</option>
                <option value="INGRESO">Ingreso</option>
                <option value="EGRESO">Egreso</option>
              </select>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table
                columns={colsMov} dataSource={movimientos} rowKey="id" loading={loadingMov}
                pageSize={15} page={pageMov} onPageChange={p => { setPageMov(p); loadMovimientos(filterProductoMov, filterTipoMov, p) }} total={totalMov}
                sortKey={sortMovKey} sortDir={sortMovDir}
                onSort={(key, dir) => { setSortMovKey(key); setSortMovDir(dir) }}
              />
            </div>
          </div>
        </>
      )}

      {/* ── Lotes tab ────────────────────────────────────────────── */}
      {tab === 'lotes' && (
        <>
          {lotesConAlerta > 0 && (
            <div className="flex items-center gap-3 bg-orange-50 border border-orange-200 rounded-2xl px-5 py-3">
              <AlertTriangle className="w-4 h-4 text-orange-500 shrink-0" />
              <p className="text-sm text-orange-700 font-medium">
                {lotesConAlerta} lote(s) vencidos o próximos a vencer.
              </p>
            </div>
          )}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap items-end gap-4">
            <div className="w-64">
              <label className={labelClass}>Producto</label>
              <select value={filterProductoLote} onChange={e => setFilterProductoLote(e.target.value)} className={inputClass}>
                <option value="">Todos</option>
                {productos.map(p => <option key={p.id} value={p.id}>{p.descripcion}</option>)}
              </select>
            </div>
            <div>
              <label className={labelClass}>Estado</label>
              <select value={filterVencido} onChange={e => setFilterVencido(e.target.value)} className={`${inputClass} w-auto`}>
                <option value="">Todos</option>
                <option value="false">Disponibles</option>
                <option value="true">Bloqueados</option>
              </select>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table
                columns={colsLotes} dataSource={lotes} rowKey="id" loading={loadingLotes}
                pageSize={15} page={pageLotes} onPageChange={p => { setPageLotes(p); loadLotes(filterProductoLote, filterVencido, p) }} total={totalLotes}
                sortKey={sortLotesKey} sortDir={sortLotesDir}
                onSort={(key, dir) => { setSortLotesKey(key); setSortLotesDir(dir) }}
              />
            </div>
          </div>
        </>
      )}

      {/* ── Alertas tab ──────────────────────────────────────────── */}
      {tab === 'alertas' && (
        <>
          <div className="flex items-center gap-2 mb-1">
            <Bell className="w-4 h-4 text-red-500" />
            <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">Alertas de Stock</h2>
            {totalAlertas > 0 && (
              <span className="bg-red-100 text-red-700 text-xs px-1.5 py-0.5 rounded-full font-semibold">{totalAlertas}</span>
            )}
          </div>
          {totalAlertas > 0 && (
            <div className="flex items-center gap-3 bg-red-50 border border-red-200 rounded-2xl px-5 py-3">
              <Bell className="w-4 h-4 text-red-500 shrink-0" />
              <p className="text-sm text-red-700 font-medium">
                {totalAlertas} producto(s) con stock bajo el mínimo configurado.
              </p>
            </div>
          )}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table columns={colsAlertas} dataSource={alertas} rowKey="id" loading={loadingAlertas}
                pageSize={15} page={pageAlertas} total={totalAlertas}
                onPageChange={p => { setPageAlertas(p); loadAlertas(p) }} />
            </div>
          </div>

          <div className="flex items-center gap-2 mt-4 mb-1">
            <Clock className="w-4 h-4 text-orange-500" />
            <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">Alertas de Vencimiento</h2>
            {totalAlertasVenc > 0 && (
              <span className="bg-orange-100 text-orange-700 text-xs px-1.5 py-0.5 rounded-full font-semibold">{totalAlertasVenc}</span>
            )}
          </div>
          {totalAlertasVenc > 0 && (
            <div className="flex items-center gap-3 bg-orange-50 border border-orange-200 rounded-2xl px-5 py-3">
              <Clock className="w-4 h-4 text-orange-500 shrink-0" />
              <p className="text-sm text-orange-700 font-medium">
                {totalAlertasVenc} lote(s) vencidos o próximos a vencer. Registrá la acción tomada para cada uno.
              </p>
            </div>
          )}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table columns={colsAlertasVenc} dataSource={alertasVenc} rowKey="id" loading={loadingAlertasVenc}
                pageSize={15} page={pageAlertasVenc} total={totalAlertasVenc}
                onPageChange={p => { setPageAlertasVenc(p); loadAlertasVenc(p) }} />
            </div>
          </div>
        </>
      )}

      <ModalAjuste
        open={ajusteOpen}
        productos={productos}
        onClose={() => setAjusteOpen(false)}
        onSaved={() => { setPageAjustes(1); loadAjustes(filterEstado, filterTipoAjuste, 1) }}
      />
      <ModalAprobar
        ajusteId={aprobar}
        onClose={() => setAprobar(null)}
        onSaved={() => loadAjustes(filterEstado, filterTipoAjuste, pageAjustes)}
      />
      <ModalRechazar
        ajusteId={rechazar}
        onClose={() => setRechazar(null)}
        onSaved={() => loadAjustes(filterEstado, filterTipoAjuste, pageAjustes)}
      />
      <ModalAccionVencimiento
        alerta={accionModal}
        onClose={() => setAccionModal(null)}
        onSaved={() => { setAccionModal(null); loadAlertasVenc(pageAlertasVenc) }}
      />
    </div>
  )
}
