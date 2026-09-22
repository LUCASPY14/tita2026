import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  Package, Plus, CheckCircle, XCircle,
  TrendingUp, TrendingDown, Bell, ShoppingCart,
} from 'lucide-react'
import api from '../services/api'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'
import {
  formatFecha, formatGs,
  type Producto, type AjusteInventario, type MovimientoStock,
  type AlertaStock, type TabKey,
  ESTADO_COLOR, TIPO_AJUSTE_COLOR, TIPO_MOV_COLOR, ALERTA_COLOR,
} from './inventario/shared'
import ModalAjuste from './inventario/ModalAjuste'
import ModalAprobar from './inventario/ModalAprobar'
import ModalRechazar from './inventario/ModalRechazar'

// La API devuelve next/previous como URL absoluta (scheme+host que Django
// cree que tiene). La convertimos a ruta relativa a /api/v1 para que pase
// por la misma instancia de axios (interceptor de auth, baseURL) que el
// resto de los pedidos, en vez de depender de que el host que arma el
// backend coincida siempre con el origen real del frontend.
function toApiPath(absoluteUrl: string | null | undefined): string | null {
  if (!absoluteUrl) return null
  const u = new URL(absoluteUrl, window.location.origin)
  return u.pathname.replace(/^\/api\/v1/, '') + u.search
}

export default function Inventario() {
  const { t } = useTranslation()
  const navigate = useNavigate()
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
  const [movNextUrl, setMovNextUrl] = useState<string | null>(null)
  const [movPrevUrl, setMovPrevUrl] = useState<string | null>(null)
  const [sortMovKey, setSortMovKey] = useState('fecha')
  const [sortMovDir, setSortMovDir] = useState<'asc' | 'desc'>('desc')
  const searchTimerMov = useRef<ReturnType<typeof setTimeout>>(undefined)
  const requestIdAjustesRef = useRef(0)
  const requestIdMovRef = useRef(0)

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
  // Paginado por cursor (no por página): la tabla es de alto volumen y el
  // backend evita a propósito un COUNT() completo — no hay "total" ni
  // "saltar a la página N", solo Anterior/Siguiente sobre el cursor que
  // devuelve la API (ver common/pagination.py CursorResultsSetPagination).
  const loadMovimientos = useCallback(async (prod: string, tipo: string) => {
    const requestId = ++requestIdMovRef.current
    setLoadingMov(true)
    try {
      const ordering = sortMovDir === 'asc' ? sortMovKey : `-${sortMovKey}`
      const params: Record<string, unknown> = { page_size: 15, ordering }
      if (prod) params.producto = prod
      if (tipo) params.tipo = tipo
      const { data } = await api.get('/inventario/movimientos/', { params })
      if (requestId !== requestIdMovRef.current) return
      setMovimientos(data.results ?? [])
      setMovNextUrl(toApiPath(data.next))
      setMovPrevUrl(toApiPath(data.previous))
    } catch {
      if (requestId !== requestIdMovRef.current) return
      toast.error('Error al cargar movimientos')
    } finally {
      if (requestId === requestIdMovRef.current) setLoadingMov(false)
    }
  }, [sortMovKey, sortMovDir])

  const loadMovimientosCursor = useCallback(async (url: string) => {
    const requestId = ++requestIdMovRef.current
    setLoadingMov(true)
    try {
      const { data } = await api.get(url)
      if (requestId !== requestIdMovRef.current) return
      setMovimientos(data.results ?? [])
      setMovNextUrl(toApiPath(data.next))
      setMovPrevUrl(toApiPath(data.previous))
    } catch {
      if (requestId !== requestIdMovRef.current) return
      toast.error('Error al cargar movimientos')
    } finally {
      if (requestId === requestIdMovRef.current) setLoadingMov(false)
    }
  }, [])

  useEffect(() => {
    if (tab !== 'movimientos') return
    clearTimeout(searchTimerMov.current)
    searchTimerMov.current = setTimeout(() => {
      loadMovimientos(filterProductoMov, filterTipoMov)
    }, 300)
    return () => clearTimeout(searchTimerMov.current)
  }, [tab, filterProductoMov, filterTipoMov, loadMovimientos])

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

  // ── Columns ──────────────────────────────────────────────────────

  const colsAjustes: Column<AjusteInventario>[] = [
    {
      title: 'ID', key: 'id_ajuste', dataIndex: 'id_ajuste', width: 60,
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
          <Button size="sm" variant="primary" onClick={() => setAprobar(r.id_ajuste)}>
            <CheckCircle className="w-3.5 h-3.5" />
            Aprobar
          </Button>
          <Button size="sm" variant="danger" onClick={() => setRechazar(r.id_ajuste)}>
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
    {
      title: 'Proveedor sugerido', key: 'proveedor_preferido',
      render: (_, r) => r.proveedor_preferido_nombre
        ? (
          <div>
            <p className="text-sm text-slate-700">{r.proveedor_preferido_nombre}</p>
            <p className="text-xs text-slate-400">{formatGs(r.precio_compra_preferido)}</p>
          </div>
        )
        : <span className="text-xs text-slate-400">Sin proveedor preferido</span>,
    },
    {
      title: '', key: 'acc', width: 140,
      render: (_, r) => r.proveedor_preferido_id
        ? (
          <Button
            size="sm" variant="secondary"
            onClick={() => navigate(`/compras?nueva_compra=1&proveedor=${r.proveedor_preferido_id}&producto=${r.producto}`)}
          >
            <ShoppingCart className="w-3.5 h-3.5" /> Generar compra
          </Button>
        )
        : (
          <button
            onClick={() => navigate('/compras?tab=vinculos')}
            className="text-xs text-emerald-600 hover:underline cursor-pointer"
          >
            Configurar proveedor →
          </button>
        ),
    },
  ]

  const TABS: { key: TabKey; label: string; icon: typeof Package }[] = [
    { key: 'ajustes', label: 'Ajustes', icon: Package },
    { key: 'movimientos', label: 'Movimientos', icon: TrendingUp },
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
              {key === 'alertas' && totalAlertas > 0 && (
                <span className="bg-red-100 text-red-700 text-xs px-1.5 py-0.5 rounded-full font-semibold">
                  {totalAlertas}
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
              <Table columns={colsAjustes} dataSource={ajustes} rowKey="id_ajuste" loading={loadingAjustes}
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
                {productos.map(p => <option key={p.id_producto} value={p.id_producto}>{p.descripcion}</option>)}
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
                columns={colsMov} dataSource={movimientos} rowKey="id_movimiento_stock" loading={loadingMov}
                pageSize={15}
                sortKey={sortMovKey} sortDir={sortMovDir}
                onSort={(key, dir) => { setSortMovKey(key); setSortMovDir(dir) }}
              />
            </div>
            <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
              <span className="text-xs text-slate-400">
                Historial de alto volumen — se navega de a páginas, sin salto directo ni total.
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary" size="sm"
                  disabled={!movPrevUrl || loadingMov}
                  onClick={() => movPrevUrl && loadMovimientosCursor(movPrevUrl)}
                >
                  Anterior
                </Button>
                <Button
                  variant="secondary" size="sm"
                  disabled={!movNextUrl || loadingMov}
                  onClick={() => movNextUrl && loadMovimientosCursor(movNextUrl)}
                >
                  Siguiente
                </Button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* ── Alertas tab ──────────────────────────────────────────── */}
      {tab === 'alertas' && (
        <>
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
    </div>
  )
}
