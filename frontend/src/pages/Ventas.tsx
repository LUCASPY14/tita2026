import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import {
  Search, ShoppingCart, ChevronDown, ChevronUp, XCircle, AlertTriangle,
  Receipt, Plus, Eye, RotateCcw,
} from 'lucide-react'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import Table, { type Column } from '../components/ui/Table'
import ModalNC from './ventas/ModalNC'
import ModalNCDetail from './ventas/ModalNCDetail'
import {
  NC_ESTADO_COLOR,
  type ClienteOption, type ProductoOption, type VentaOrigen, type NotaCredito,
} from './ventas/shared'

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface DetalleVenta {
  id_detalle_venta: number
  producto: number
  producto_nombre: string
  cantidad: string
  precio_unitario: string
  subtotal: string
}

interface Venta {
  id_venta: number
  fecha: string
  cliente: number | null
  cliente_nombre: string | null
  hijo_nombre: string | null
  hijo_grado: string | null
  cajero_nombre: string | null
  tarjeta: string | null
  tipo: string
  estado: string
  estado_pago: string
  monto_total: string
  saldo_pendiente: string
  detalles: DetalleVenta[]
}

interface CajeroOption {
  id_usuario: number
  nombre: string
  apellido: string
  email: string
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatGs(n: string | number | null | undefined): string {
  return (Number(n) || 0).toLocaleString('es-PY') + ' Gs.'
}

function formatFecha(iso: string): string {
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

const TIPO_LABEL: Record<string, string> = {
  VENTA_TARJETA:   'Tarjeta prepago',
  VENTA_EFECTIVO:  'Efectivo',
  CONSUMO_ALMUERZO:'Almuerzo',
  CARGA_SALDO:     'Carga de saldo',
  CONTADO:         'Contado',
  CREDITO:         'Crédito',
}

const TIPO_COLOR: Record<string, BadgeColor> = {
  VENTA_TARJETA:   'blue',
  VENTA_EFECTIVO:  'green',
  CONSUMO_ALMUERZO:'orange',
  CARGA_SALDO:     'purple',
  CONTADO:         'green',
  CREDITO:         'yellow',
}

const ESTADO_COLOR: Record<string, BadgeColor> = {
  ACTIVA:  'green',
  ANULADA: 'red',
}

const PAGE_SIZE = 20

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Ventas() {
  const today = new Date().toISOString().split('T')[0]
  const { user } = useAuthStore()
  const isAdmin = user?.rol === 'ADMIN'
  const isCajero = user?.rol === 'CAJERO'
  const canFilter = !isCajero  // CAJERO solo ve sus ventas — backend ya filtra

  const [tab, setTab] = useState<'ventas' | 'notas'>('ventas')

  // ── Filtros ──────────────────────────────────────────────────────────────────
  const [desde, setDesde] = useState(today)
  const [hasta, setHasta] = useState(today)
  const [estado, setEstado] = useState('')
  const [tipo, setTipo] = useState('')
  const [search, setSearch] = useState('')
  const [cajeroId, setCajeroId] = useState('')
  const [cajeros, setCajeros] = useState<CajeroOption[]>([])

  // ── Resultados ───────────────────────────────────────────────────────────────
  const [ventas, setVentas] = useState<Venta[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [expandedId, setExpandedId] = useState<number | null>(null)

  // ── Anulación ────────────────────────────────────────────────────────────────
  const [confirmAnular, setConfirmAnular] = useState<Venta | null>(null)
  const [anulando, setAnulando] = useState(false)

  // ── Notas de crédito ─────────────────────────────────────────────────────────
  const [clientesOpt, setClientesOpt] = useState<ClienteOption[]>([])
  const [productosOpt, setProductosOpt] = useState<ProductoOption[]>([])
  const [notas, setNotas] = useState<NotaCredito[]>([])
  const [totalNotas, setTotalNotas] = useState(0)
  const [pageNotas, setPageNotas] = useState(1)
  const [loadingNotas, setLoadingNotas] = useState(false)
  const [ncModalOpen, setNcModalOpen] = useState(false)
  const [ncInitialVenta, setNcInitialVenta] = useState<VentaOrigen | null>(null)
  const [detailNC, setDetailNC] = useState<NotaCredito | null>(null)

  const requestIdRef = useRef(0)
  const searchTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined)
  const reqNotasRef = useRef(0)

  // ── Cargar clientes + productos (para el formulario de Nota de Crédito) ─────
  useEffect(() => {
    api.get('/clientes/clientes/', { params: { page_size: 500, activo: true } })
      .then(({ data }) => setClientesOpt((data.results ?? []).map((c: { id_cliente: number; nombre_completo: string }) => ({ id_cliente: c.id_cliente, nombre_completo: c.nombre_completo }))))
      .catch(() => {})
    api.get('/productos/productos/', { params: { page_size: 500, activo: true } })
      .then(({ data }) => setProductosOpt((data.results ?? []).map((p: { id_producto: number; descripcion: string }) => ({ id_producto: p.id_producto, descripcion: p.descripcion }))))
      .catch(() => {})
  }, [])

  // ── Cargar notas de crédito ──────────────────────────────────────────────────
  const loadNotas = useCallback(async (p: number) => {
    const reqId = ++reqNotasRef.current
    setLoadingNotas(true)
    try {
      const { data } = await api.get('/ventas/notas-credito/', { params: { page: p, page_size: PAGE_SIZE, ordering: '-fecha_emision' } })
      if (reqId !== reqNotasRef.current) return
      setNotas(data.results ?? [])
      setTotalNotas(data.count ?? 0)
    } catch {
      if (reqId !== reqNotasRef.current) return
      toast.error('Error al cargar notas de crédito')
    } finally {
      if (reqId === reqNotasRef.current) setLoadingNotas(false)
    }
  }, [])

  // Carga de datos al cambiar de tab/página: el setLoadingNotas(true) inicial es intencional.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { if (tab === 'notas') loadNotas(pageNotas) }, [tab, pageNotas, loadNotas])

  function emitirNCDesdeVenta(v: Venta) {
    setNcInitialVenta({
      id_venta: v.id_venta,
      fecha: v.fecha,
      monto_total: v.monto_total,
      cliente: v.cliente ?? 0,
      detalles: v.detalles.map(d => ({
        producto: d.producto, producto_nombre: d.producto_nombre,
        cantidad: d.cantidad, precio_unitario: d.precio_unitario,
      })),
    })
    setNcModalOpen(true)
  }

  // ── Cargar cajeros + admins (solo visible para ADMIN) ───────────────────────
  useEffect(() => {
    if (!isAdmin) return
    Promise.all([
      api.get('/usuarios/usuarios/', { params: { rol: 'CAJERO', page_size: 100 } }),
      api.get('/usuarios/usuarios/', { params: { rol: 'ADMIN', page_size: 100 } }),
    ]).then(([cajRes, admRes]) => {
      const todos: CajeroOption[] = [
        ...(cajRes.data?.results ?? []),
        ...(admRes.data?.results ?? []),
      ]
      todos.sort((a, b) =>
        `${a.nombre} ${a.apellido}`.localeCompare(`${b.nombre} ${b.apellido}`)
      )
      setCajeros(todos)
    }).catch(() => toast.error('Error al cargar lista de usuarios'))
  }, [isAdmin])

  // ── Fetch ventas ─────────────────────────────────────────────────────────────
  const fetchVentas = useCallback(async (p: number) => {
    const requestId = ++requestIdRef.current
    setLoading(true)
    try {
      const params: Record<string, unknown> = {
        page: p,
        page_size: PAGE_SIZE,
        ordering: '-fecha',
      }
      if (desde)    params.fecha_desde = desde
      if (hasta)    params.fecha_hasta = hasta
      if (estado)   params.estado = estado
      if (tipo)     params.tipo = tipo
      if (search)   params.search = search
      if (cajeroId) params.cajero = cajeroId

      const { data } = await api.get('/ventas/ventas/', { params })
      if (requestId !== requestIdRef.current) return
      setVentas(data.results ?? [])
      setTotal(data.count ?? 0)
    } catch {
      if (requestId !== requestIdRef.current) return
      toast.error('Error al cargar ventas')
    } finally {
      if (requestId === requestIdRef.current) setLoading(false)
    }
  }, [desde, hasta, estado, tipo, search, cajeroId])

  // Carga inicial y al cambiar filtros (excepto search que tiene debounce).
  // El reset de página + fetch al cambiar filtros es intencional.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPage(1)
    setExpandedId(null)
    fetchVentas(1)
  }, [desde, hasta, estado, tipo, cajeroId, fetchVentas])

  // Debounce para search
  useEffect(() => {
    clearTimeout(searchTimerRef.current)
    searchTimerRef.current = setTimeout(() => {
      setPage(1)
      setExpandedId(null)
      fetchVentas(1)
    }, 350)
    return () => clearTimeout(searchTimerRef.current)
    // Solo debounce sobre `search`: `fetchVentas` cambia de identidad con cada
    // filtro y ya se dispara sin debounce en el efecto anterior al cambiar esos.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search])

  function changePage(p: number) {
    setPage(p)
    setExpandedId(null)
    fetchVentas(p)
  }

  // ── Anular ───────────────────────────────────────────────────────────────────
  async function anularVenta() {
    if (!confirmAnular) return
    setAnulando(true)
    try {
      await api.post(`/ventas/ventas/${confirmAnular.id_venta}/anular/`)
      toast.success(`Venta #${confirmAnular.id_venta} anulada`)
      setConfirmAnular(null)
      fetchVentas(page)
    } catch (err) {
      const e = err as { response?: { data?: { error?: string; detail?: string } } }
      const msg = e?.response?.data?.error ?? e?.response?.data?.detail ?? 'Error al anular la venta'
      toast.error(msg)
    } finally {
      setAnulando(false)
    }
  }

  // ── Estilos compartidos ──────────────────────────────────────────────────────
  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors'
  const labelClass = 'block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1'

  const totalPages = Math.ceil(total / PAGE_SIZE)

  const colsNotas: Column<NotaCredito>[] = [
    { title: 'NC #', key: 'nro', render: (_, r) => <span className="text-sm font-semibold text-slate-500">{r.nro_nota_credito}</span> },
    { title: 'Cliente', key: 'cliente', render: (_, r) => <span className="text-base font-medium text-slate-800">{r.cliente_nombre}</span> },
    { title: 'Monto', key: 'monto_total', render: (_, r) => <span className="text-base font-bold tabular-nums text-emerald-700">{formatGs(r.monto_total)}</span> },
    {
      title: 'Venta orig.', key: 'venta_origen',
      render: (_, r) => r.venta_origen
        ? <span className="text-sm text-blue-600 font-medium">#{r.venta_origen}</span>
        : <span className="text-sm text-slate-400">—</span>,
    },
    { title: 'Estado', key: 'estado', render: (_, r) => <Badge color={NC_ESTADO_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge> },
    { title: 'Fecha', key: 'fecha_emision', render: (_, r) => <span className="text-sm text-slate-500">{formatFecha(r.fecha_emision)}</span> },
    {
      title: '', key: 'acciones',
      render: (_, r) => (
        <div className="flex items-center gap-2 justify-end">
          <Button size="sm" variant="secondary" onClick={() => setDetailNC(r)}><Eye className="w-3.5 h-3.5" />Ver</Button>
        </div>
      ),
    },
  ]

  // ─── JSX ─────────────────────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Ventas</h1>
          <p className="text-sm text-slate-500 mt-0.5">Historial y gestión de ventas</p>
        </div>
        {tab === 'notas' && (
          <Button variant="primary" onClick={() => { setNcInitialVenta(null); setNcModalOpen(true) }}>
            <Plus className="w-4 h-4" />Nueva Nota de Crédito
          </Button>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <div className="flex gap-0">
          {([
            { key: 'ventas' as const, label: 'Ventas', icon: ShoppingCart },
            { key: 'notas' as const, label: 'Notas de Crédito', icon: Receipt },
          ]).map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                tab === key ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Icon className="w-4 h-4" />{label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'ventas' && (
      <>
      {/* Filtros */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className={labelClass}>Desde</label>
            <input type="date" value={desde} onChange={e => setDesde(e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Hasta</label>
            <input type="date" value={hasta} onChange={e => setHasta(e.target.value)} className={inputClass} />
          </div>

          {canFilter && (
            <>
              <div>
                <label className={labelClass}>Estado</label>
                <select value={estado} onChange={e => setEstado(e.target.value)} className={inputClass}>
                  <option value="">Todos</option>
                  <option value="ACTIVA">Activa</option>
                  <option value="ANULADA">Anulada</option>
                </select>
              </div>
              <div>
                <label className={labelClass}>Tipo</label>
                <select value={tipo} onChange={e => setTipo(e.target.value)} className={inputClass}>
                  <option value="">Todos</option>
                  <option value="CONTADO">Contado</option>
                  <option value="CREDITO">Crédito</option>
                </select>
              </div>
              {isAdmin && cajeros.length > 0 && (
                <div>
                  <label className={labelClass}>Cajero</label>
                  <select value={cajeroId} onChange={e => setCajeroId(e.target.value)} className={inputClass}>
                    <option value="">Todos</option>
                    {cajeros.map(c => (
                      <option key={c.id_usuario} value={c.id_usuario}>
                        {`${c.nombre} ${c.apellido}`.trim() || c.email}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </>
          )}

          <div className="flex-1 min-w-48">
            <label className={labelClass}>Buscar</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
              <input
                placeholder="Cliente, RUC/CI..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className={`${inputClass} pl-8 w-full`}
              />
            </div>
          </div>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Total registros</p>
          <p className="text-xl font-bold text-slate-800 tabular-nums mt-0.5">{total}</p>
        </div>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">En esta página</p>
          <p className="text-xl font-bold text-slate-800 tabular-nums mt-0.5">{ventas.length}</p>
        </div>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Monto (página)</p>
          <p className="text-xl font-bold text-emerald-700 tabular-nums mt-0.5">
            {formatGs(ventas.filter(v => v.estado === 'ACTIVA').reduce((s, v) => s + Number(v.monto_total), 0))}
          </p>
        </div>
      </div>

      {/* Lista */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        {loading && ventas.length === 0 ? (
          <div className="py-20 text-center text-slate-400 text-sm">Cargando...</div>
        ) : ventas.length === 0 ? (
          <div className="py-20 text-center">
            <ShoppingCart className="w-10 h-10 text-slate-200 mx-auto mb-3" />
            <p className="text-sm text-slate-400">Sin ventas en el período seleccionado</p>
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {ventas.map(v => {
              const isExp = expandedId === v.id_venta
              const persona = v.hijo_nombre ?? v.cliente_nombre ?? '—'
              const pendiente = (v.estado_pago === 'PENDIENTE' || v.estado_pago === 'PARCIAL') && Number(v.saldo_pendiente) > 0

              return (
                <li key={v.id_venta} className={v.estado === 'ANULADA' ? 'opacity-60' : ''}>
                  <div
                    role="button"
                    tabIndex={0}
                    onClick={() => setExpandedId(isExp ? null : v.id_venta)}
                    onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && setExpandedId(isExp ? null : v.id_venta)}
                    className="w-full flex items-center gap-3 px-5 py-3.5 text-left hover:bg-slate-50 transition-colors group cursor-pointer"
                  >
                    {/* Icono */}
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                      v.estado === 'ANULADA' ? 'bg-red-50' : 'bg-green-50'
                    }`}>
                      {v.estado === 'ANULADA'
                        ? <XCircle className="w-3.5 h-3.5 text-red-400" />
                        : <ShoppingCart className="w-3.5 h-3.5 text-green-600" />
                      }
                    </div>

                    {/* Info principal */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-semibold text-slate-800 truncate">{persona}</span>
                        {v.hijo_grado && <span className="text-xs text-slate-400">{v.hijo_grado}</span>}
                        <Badge color={TIPO_COLOR[v.tipo] ?? 'default'}>
                          {TIPO_LABEL[v.tipo] ?? v.tipo}
                        </Badge>
                        <Badge color={ESTADO_COLOR[v.estado] ?? 'default'}>{v.estado}</Badge>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {formatFecha(v.fecha)}
                        {v.cajero_nombre && ` · ${v.cajero_nombre}`}
                        {v.tarjeta && ` · ${v.tarjeta}`}
                      </p>
                    </div>

                    {/* Monto + acciones */}
                    <div className="flex items-center gap-3 shrink-0">
                      <div className="text-right">
                        <p className="text-sm font-bold tabular-nums text-slate-800">
                          {formatGs(v.monto_total)}
                        </p>
                        {pendiente && v.estado === 'ACTIVA' && (
                          <p className="text-xs text-amber-600 tabular-nums">
                            Pend: {formatGs(v.saldo_pendiente)}
                          </p>
                        )}
                      </div>
                      {isAdmin && v.estado === 'ACTIVA' && (
                        <button
                          type="button"
                          onClick={e => { e.stopPropagation(); setConfirmAnular(v) }}
                          className="text-xs font-medium text-red-500 hover:text-red-700 px-2 py-1 rounded-lg hover:bg-red-50 transition-colors shrink-0"
                          title="Anular venta"
                        >
                          Anular
                        </button>
                      )}
                      {isExp
                        ? <ChevronUp className="w-4 h-4 text-slate-400 shrink-0" />
                        : <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" />
                      }
                    </div>
                  </div>

                  {/* Detalles expandidos */}
                  {isExp && (
                    <div className="px-5 pb-4 ml-11">
                      {v.detalles.length === 0 ? (
                        <p className="text-xs text-slate-400 py-2">Sin detalle de productos</p>
                      ) : (
                        <ul className="space-y-1.5 mt-1">
                          {v.detalles.map(d => (
                            <li key={d.id_detalle_venta} className="flex items-center justify-between text-sm text-slate-600">
                              <span>
                                <span className="font-semibold text-slate-700 tabular-nums">{d.cantidad}×</span>
                                {' '}{d.producto_nombre}
                                <span className="text-slate-400 ml-1.5">{formatGs(d.precio_unitario)} c/u</span>
                              </span>
                              <span className="tabular-nums font-semibold text-slate-700 shrink-0 ml-4">
                                {formatGs(d.subtotal)}
                              </span>
                            </li>
                          ))}
                        </ul>
                      )}
                      {v.estado === 'ACTIVA' && v.cliente && (
                        <button
                          type="button"
                          onClick={e => { e.stopPropagation(); emitirNCDesdeVenta(v) }}
                          className="mt-3 text-xs font-medium text-blue-600 hover:text-blue-800 flex items-center gap-1.5"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                          Emitir Nota de Crédito
                        </button>
                      )}
                    </div>
                  )}
                </li>
              )
            })}
          </ul>
        )}

        {/* Paginación */}
        {totalPages > 1 && (
          <div className="px-5 py-3 border-t border-slate-100 flex items-center justify-between gap-4">
            <p className="text-xs text-slate-400 tabular-nums">
              {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, total)} de {total}
            </p>
            <div className="flex items-center gap-1">
              <Button
                variant="secondary"
                onClick={() => changePage(page - 1)}
                disabled={page === 1 || loading}
              >
                ‹ Anterior
              </Button>
              <span className="px-3 text-sm text-slate-600 tabular-nums">
                {page} / {totalPages}
              </span>
              <Button
                variant="secondary"
                onClick={() => changePage(page + 1)}
                disabled={page >= totalPages || loading}
              >
                Siguiente ›
              </Button>
            </div>
          </div>
        )}
      </div>
      </>
      )}

      {tab === 'notas' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-base font-semibold text-slate-800">Notas de Crédito</h2>
          </div>
          <div className="p-1">
            <Table columns={colsNotas} dataSource={notas} rowKey="id_nota_credito" loading={loadingNotas}
              pageSize={PAGE_SIZE} page={pageNotas} onPageChange={setPageNotas} total={totalNotas} />
          </div>
        </div>
      )}

      {/* Modal de confirmación anulación */}
      {confirmAnular && (
        <Modal
          open
          title="Anular venta"
          onCancel={() => !anulando && setConfirmAnular(null)}
          footer={null}
        >
          <div className="space-y-4">
            <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
              <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
              <div className="text-sm text-red-800 space-y-1">
                <p className="font-semibold">Esta acción es irreversible</p>
                <p>Se revertirá el stock, el saldo de tarjeta y la cuenta corriente del cliente.</p>
              </div>
            </div>
            <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-1 text-sm">
              <p className="text-slate-500">Venta <span className="font-semibold text-slate-800">#{confirmAnular.id_venta}</span></p>
              <p className="text-slate-500">Cliente: <span className="font-semibold text-slate-800">{confirmAnular.hijo_nombre ?? confirmAnular.cliente_nombre ?? '—'}</span></p>
              <p className="text-slate-500">Monto: <span className="font-semibold text-slate-800">{formatGs(confirmAnular.monto_total)}</span></p>
              <p className="text-slate-500">Fecha: <span className="font-semibold text-slate-800">{formatFecha(confirmAnular.fecha)}</span></p>
            </div>
            <div className="flex gap-3 justify-end pt-1">
              <Button variant="secondary" onClick={() => setConfirmAnular(null)} disabled={anulando}>
                Cancelar
              </Button>
              <Button variant="danger" loading={anulando} onClick={anularVenta}>
                Confirmar anulación
              </Button>
            </div>
          </div>
        </Modal>
      )}

      <ModalNC
        open={ncModalOpen}
        clientes={clientesOpt}
        productos={productosOpt}
        initialVenta={ncInitialVenta}
        onClose={() => { setNcModalOpen(false); setNcInitialVenta(null) }}
        onSaved={() => { setPageNotas(1); loadNotas(1) }}
      />
      <ModalNCDetail
        nc={detailNC}
        canAnular={isAdmin}
        onClose={() => setDetailNC(null)}
        onAnulada={() => loadNotas(pageNotas)}
      />
    </div>
  )
}
