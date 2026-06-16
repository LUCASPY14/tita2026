import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import {
  Plus, Search, Package, Edit2, AlertTriangle, Tag, TrendingDown,
} from 'lucide-react'
import api from '../services/api'
import { useCatalogoStore } from '../store/catalogoStore'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Modal from '../components/ui/Modal'
import Table, { type Column } from '../components/ui/Table'

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface Categoria { id: number; nombre: string; activo: boolean }
interface UnidadMedida { id: number; nombre: string; abreviatura: string; activo: boolean }

interface Producto {
  id: number
  codigo_barra: string | null
  codigo: string | null
  descripcion: string
  categoria: number
  categoria_nombre: string
  unidad_medida: number | null
  stock_minimo: string
  permite_stock_negativo: boolean
  es_servicio: boolean
  requiere_stock: boolean
  activo: boolean
  precio_actual: string
}

interface ProductoForm {
  descripcion: string
  codigo_barra: string
  codigo: string
  categoria: string
  unidad_medida: string
  stock_minimo: string
  permite_stock_negativo: boolean
  es_servicio: boolean
  requiere_stock: boolean
  activo: boolean
}

interface StockRecord {
  id: number
  producto: number
  cantidad: string
  producto_nombre: string
  costo_promedio: string
  valor_inventario: string
  requiere_reposicion: boolean
  dias_stock_disponible: number
  fecha_actualizacion: string
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function extractErrorMessage(err: unknown): string {
  const e = err as { response?: { data?: unknown } }
  const data = e?.response?.data
  if (!data) return 'Error inesperado'
  if (typeof data === 'string') return data
  if (typeof data === 'object') {
    const d = data as Record<string, unknown>
    if (d.detail) return String(d.detail)
    const first = Object.values(d)[0]
    if (Array.isArray(first)) return String(first[0])
    return JSON.stringify(data)
  }
  return 'Error inesperado'
}

function formatGs(value: string | number | null | undefined): string {
  return (Number(value) || 0).toLocaleString('es-PY') + ' Gs.'
}

// ─── ProductoModal ────────────────────────────────────────────────────────────

const BLANK_FORM: ProductoForm = {
  descripcion: '', codigo_barra: '', codigo: '',
  categoria: '', unidad_medida: '',
  stock_minimo: '0',
  permite_stock_negativo: false,
  es_servicio: false,
  requiere_stock: true,
  activo: true,
}

interface ProductoModalProps {
  open: boolean
  producto: Producto | null
  categorias: Categoria[]
  unidades: UnidadMedida[]
  onClose: () => void
  onSaved: () => void
}

function ProductoModal({ open, producto, categorias, unidades, onClose, onSaved }: ProductoModalProps) {
  const [form, setForm] = useState<ProductoForm>(BLANK_FORM)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    setForm(producto
      ? {
          descripcion: producto.descripcion,
          codigo_barra: producto.codigo_barra ?? '',
          codigo: producto.codigo ?? '',
          categoria: String(producto.categoria),
          unidad_medida: producto.unidad_medida ? String(producto.unidad_medida) : '',
          stock_minimo: producto.stock_minimo,
          permite_stock_negativo: producto.permite_stock_negativo,
          es_servicio: producto.es_servicio,
          requiere_stock: producto.requiere_stock,
          activo: producto.activo,
        }
      : BLANK_FORM
    )
  }, [open, producto])

  useEffect(() => {
    if (form.es_servicio) {
      setForm(prev => ({ ...prev, requiere_stock: false, stock_minimo: '0' }))
    }
  }, [form.es_servicio])

  function setText(field: keyof ProductoForm) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm(prev => ({ ...prev, [field]: e.target.value }))
  }

  function toggleBool(field: keyof ProductoForm) {
    setForm(prev => ({ ...prev, [field]: !prev[field] }))
  }

  async function handleSave() {
    if (!form.descripcion || !form.categoria) {
      toast.error('Descripción y categoría son obligatorias')
      return
    }
    setSaving(true)
    const payload = {
      ...form,
      codigo_barra: form.codigo_barra || null,
      codigo: form.codigo || null,
      categoria: Number(form.categoria),
      unidad_medida: form.unidad_medida ? Number(form.unidad_medida) : null,
      stock_minimo: Number(form.stock_minimo) || 0,
    }
    try {
      if (producto) {
        await api.patch(`/productos/productos/${producto.id}/`, payload)
        toast.success('Producto actualizado')
      } else {
        await api.post('/productos/productos/', payload)
        toast.success('Producto creado')
      }
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const selectClass = 'w-full border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  function Toggle({ label, field }: { label: string; field: keyof ProductoForm }) {
    const checked = form[field] as boolean
    return (
      <div className="flex items-center justify-between py-2.5 border-b border-slate-50 last:border-0">
        <span className="text-sm text-slate-700">{label}</span>
        <button
          type="button"
          role="switch"
          aria-checked={checked}
          aria-label={label}
          onClick={() => toggleBool(field)}
          className={[
            'relative w-10 h-5 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500/30 shrink-0',
            checked ? 'bg-green-500' : 'bg-slate-200',
          ].join(' ')}
        >
          <span
            className={[
              'absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow-sm transition-transform duration-200',
              checked ? 'translate-x-5' : 'translate-x-0',
            ].join(' ')}
          />
        </button>
      </div>
    )
  }

  return (
    <Modal
      open={open}
      title={producto ? `Editar — ${producto.descripcion}` : 'Nuevo Producto'}
      onCancel={onClose}
      onOk={handleSave}
      okText={producto ? 'Guardar Cambios' : 'Crear Producto'}
      confirmLoading={saving}
      width={620}
    >
      <div className="space-y-5">
        {/* Identificación */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="sm:col-span-3">
            <Input
              label="Descripción *"
              value={form.descripcion}
              onChange={setText('descripcion')}
              placeholder="Ej: Sándwich de pollo"
            />
          </div>
          <Input
            label="Código de Barra"
            value={form.codigo_barra}
            onChange={setText('codigo_barra')}
            placeholder="7890..."
          />
          <Input
            label="Código Interno"
            value={form.codigo}
            onChange={setText('codigo')}
            placeholder="PRD-001"
          />
          <div>
            <label className={labelClass}>Categoría *</label>
            <select value={form.categoria} onChange={setText('categoria')} className={selectClass}>
              <option value="">Seleccionar...</option>
              {categorias.map(c => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Stock */}
        <div className="border-t border-slate-100 pt-4 grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Unidad de Medida</label>
            <select value={form.unidad_medida} onChange={setText('unidad_medida')} className={selectClass}>
              <option value="">Sin especificar</option>
              {unidades.map(u => (
                <option key={u.id} value={u.id}>{u.nombre} ({u.abreviatura})</option>
              ))}
            </select>
          </div>
          <Input
            label="Stock Mínimo"
            type="number"
            min="0"
            step="1"
            value={form.stock_minimo}
            onChange={e => setForm(prev => ({ ...prev, stock_minimo: String(Math.max(0, Number(e.target.value) || 0)) }))}
            placeholder="0"
          />
        </div>

        {/* Toggles */}
        <div className="border-t border-slate-100 pt-4 bg-slate-50/50 rounded-xl p-4">
          <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">Comportamiento</p>
          <Toggle label="Activo" field="activo" />
          <Toggle label="Controla stock" field="requiere_stock" />
          <Toggle label="Es servicio (sin stock físico)" field="es_servicio" />
          <Toggle label="Permite stock negativo" field="permite_stock_negativo" />
        </div>
      </div>
    </Modal>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────

const PAGE_SIZE = 25

export default function Produtos() {
  const { t } = useTranslation()
  const invalidateCatalogo = useCatalogoStore(state => state.invalidate)
  const [productos, setProductos] = useState<Producto[]>([])
  const [stockMap, setStockMap] = useState<Record<number, StockRecord>>({})
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [unidades, setUnidades] = useState<UnidadMedida[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)

  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [filterActivo, setFilterActivo] = useState('')
  const [filterCategoria, setFilterCategoria] = useState('')
  const [filterServicio, setFilterServicio] = useState('')

  const [modal, setModal] = useState<{ open: boolean; producto: Producto | null }>({
    open: false, producto: null,
  })

  const [stockCritico, setStockCritico] = useState(0)
  const [loadingCritico, setLoadingCritico] = useState(false)

  const searchTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined)

  // Load catalogs once
  useEffect(() => {
    api.get('/productos/categorias/', { params: { activo: true } })
      .then(({ data }) => setCategorias(data.results ?? data)).catch(() => {})
    api.get('/productos/unidades-medida/')
      .then(({ data }) => setUnidades(data.results ?? data)).catch(() => {})
    // Load stock crítico count
    setLoadingCritico(true)
    api.get('/inventario/stock-critico/')
      .then(({ data }) => setStockCritico(data.total ?? 0))
      .catch(() => {})
      .finally(() => setLoadingCritico(false))
  }, [])

  // Load stock map (all stock records) once and on refresh
  const loadStock = useCallback(async () => {
    try {
      const { data } = await api.get('/inventario/stock/', { params: { page_size: 500 } })
      const records: StockRecord[] = data.results ?? data
      const map: Record<number, StockRecord> = {}
      records.forEach(s => { map[s.producto] = s })
      setStockMap(map)
    } catch {
      // stock not critical for page load
    }
  }, [])

  const loadProductos = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = { page, page_size: PAGE_SIZE }
      if (search) params.search = search
      if (filterActivo) params.activo = filterActivo
      if (filterCategoria) params.categoria = filterCategoria
      if (filterServicio) params.es_servicio = filterServicio
      const { data } = await api.get('/productos/productos/', { params })
      setProductos(data.results ?? [])
      setTotal(data.count ?? 0)
    } catch {
      toast.error('Error al cargar productos')
    } finally {
      setLoading(false)
    }
  }, [page, search, filterActivo, filterCategoria, filterServicio])

  useEffect(() => {
    loadProductos()
  }, [loadProductos])

  useEffect(() => {
    loadStock()
  }, [loadStock])

  function handleSearchChange(value: string) {
    setSearchInput(value)
    clearTimeout(searchTimerRef.current)
    searchTimerRef.current = setTimeout(() => {
      setPage(1)
      setSearch(value)
    }, 350)
  }

  function handleFilter(setter: (v: string) => void) {
    return (e: React.ChangeEvent<HTMLSelectElement>) => {
      setter(e.target.value)
      setPage(1)
    }
  }

  function handleSaved() {
    loadProductos()
    loadStock()
    invalidateCatalogo()
  }

  const columns = useMemo<Column<Producto>[]>(() => [
    {
      title: 'Código',
      key: 'codigo',
      render: (_, r) => (
        <div className="space-y-0.5">
          {r.codigo_barra && (
            <span className="font-mono text-sm bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded block w-fit">
              {r.codigo_barra}
            </span>
          )}
          {r.codigo && (
            <span className="text-sm text-slate-400">{r.codigo}</span>
          )}
          {!r.codigo_barra && !r.codigo && (
            <span className="text-slate-300 text-sm">—</span>
          )}
        </div>
      ),
    },
    {
      title: 'Descripción',
      key: 'descripcion',
      render: (_, r) => (
        <div>
          <p className="text-sm font-semibold text-slate-800">{r.descripcion}</p>
          <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
            <span className="text-sm text-slate-400 flex items-center gap-0.5">
              <Tag className="w-2.5 h-2.5" />
              {r.categoria_nombre}
            </span>
            {r.es_servicio && (
              <Badge color="purple">Servicio</Badge>
            )}
          </div>
        </div>
      ),
    },
    {
      title: 'Stock',
      key: 'stock',
      render: (_, r) => {
        if (!r.requiere_stock || r.es_servicio) {
          return <span className="text-sm text-slate-400">N/A</span>
        }
        const s = stockMap[r.id]
        if (!s) return <span className="text-sm text-slate-400">—</span>
        const qty = Number(s.cantidad) || 0
        const min = Number(r.stock_minimo) || 0
        const isCritical = qty <= min && min > 0
        const isZero = qty <= 0
        return (
          <div className="flex items-center gap-1.5">
            <span className={[
              'tabular-nums text-sm font-semibold',
              isZero ? 'text-red-600' : isCritical ? 'text-orange-600' : 'text-emerald-700',
            ].join(' ')}>
              {qty.toLocaleString('es-PY')}
            </span>
            {isCritical && !isZero && (
              <AlertTriangle className="w-3.5 h-3.5 text-orange-500 shrink-0" />
            )}
            {isZero && (
              <AlertTriangle className="w-3.5 h-3.5 text-red-500 shrink-0" />
            )}
          </div>
        )
      },
    },
    {
      title: 'Precio',
      key: 'precio',
      render: (_, r) => (
        <span className="tabular-nums text-sm font-semibold text-emerald-700">
          {formatGs(r.precio_actual)}
        </span>
      ),
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => (
        <Badge color={r.activo ? 'green' : 'red'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge>
      ),
    },
    {
      title: '',
      key: 'acciones',
      render: (_, r) => (
        <div className="flex justify-end">
          <button
            onClick={() => setModal({ open: true, producto: r })}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
            title="Editar"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
        </div>
      ),
    },
  ], [stockMap])

  const stats = useMemo(() => ({
    activos: productos.filter(p => p.activo).length,
    sinStock: productos.filter(p => {
      if (!p.requiere_stock || p.es_servicio) return false
      const cantidad = stockMap[p.id] ? Number(stockMap[p.id].cantidad) : 0
      return cantidad <= 0
    }).length,
  }), [productos, stockMap])

  const selectClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'

  return (
    <div className="p-4 md:p-6 space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('productos.title')}</h1>
          <p className="text-base text-slate-500 mt-0.5">{t('productos.subtitle')}</p>
        </div>
        <Button variant="primary" onClick={() => setModal({ open: true, producto: null })}>
          <Plus className="w-4 h-4" />
          {t('productos.newProducto')}
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Total', value: total, color: 'text-slate-900', icon: Package },
          { label: 'Activos', value: stats.activos, color: 'text-green-600', icon: Package },
          { label: 'Sin Stock', value: stats.sinStock, color: 'text-red-600', icon: TrendingDown },
          {
            label: 'Stock Crítico',
            value: loadingCritico ? '...' : stockCritico,
            color: stockCritico > 0 ? 'text-orange-600' : 'text-slate-900',
            icon: AlertTriangle,
          },
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

      {/* Filters */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3 flex flex-wrap gap-3 items-center">
        <div className="flex-1 min-w-48 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          <input
            className="w-full border border-slate-200 rounded-xl pl-9 pr-3 py-2 text-sm text-slate-900 bg-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors"
            placeholder="Buscar por descripción o código..."
            value={searchInput}
            onChange={e => handleSearchChange(e.target.value)}
          />
        </div>
        <select value={filterCategoria} onChange={handleFilter(setFilterCategoria)} className={selectClass}>
          <option value="">Todas las categorías</option>
          {categorias.map(c => (
            <option key={c.id} value={c.id}>{c.nombre}</option>
          ))}
        </select>
        <select value={filterActivo} onChange={handleFilter(setFilterActivo)} className={selectClass}>
          <option value="">Todos los estados</option>
          <option value="true">Activos</option>
          <option value="false">Inactivos</option>
        </select>
        <select value={filterServicio} onChange={handleFilter(setFilterServicio)} className={selectClass}>
          <option value="">Todos los tipos</option>
          <option value="false">Productos físicos</option>
          <option value="true">Servicios</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden p-1">
        <Table
          columns={columns}
          dataSource={productos}
          rowKey="id"
          loading={loading}
          pageSize={PAGE_SIZE}
          page={page}
          onPageChange={setPage}
          total={total}
        />
      </div>

      {/* Stock crítico banner */}
      {!loadingCritico && stockCritico > 0 && (
        <div className="flex items-center gap-3 bg-orange-50 border border-orange-200 rounded-2xl px-5 py-3">
          <AlertTriangle className="w-5 h-5 text-orange-500 shrink-0" />
          <p className="text-sm text-orange-800">
            <span className="font-semibold">{stockCritico} producto{stockCritico !== 1 ? 's' : ''}</span>
            {' '}con stock por debajo del mínimo. Revisá el módulo de Compras para reabastecer.
          </p>
        </div>
      )}

      <ProductoModal
        open={modal.open}
        producto={modal.producto}
        categorias={categorias}
        unidades={unidades}
        onClose={() => setModal({ open: false, producto: null })}
        onSaved={handleSaved}
      />
    </div>
  )
}
