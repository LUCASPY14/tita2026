import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { Edit2, Trash2, Plus, Search, Star } from 'lucide-react'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Table, { type Column } from '../../components/ui/Table'
import {
  extractErrorMessage, formatGs, formatFecha, calcularMargen, formatMargen, MARGEN_TEXT_COLOR,
  type Producto, type Proveedor, type ProductoProveedorRecord,
} from './shared'

const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'
const PAGE_SIZE = 15

export default function TabProductosProveedor({ proveedores, productos }: { proveedores: Proveedor[]; productos: Producto[] }) {
  const [items, setItems] = useState<ProductoProveedorRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [filterProveedor, setFilterProveedor] = useState('')
  const [search, setSearch] = useState('')
  const searchTimer = useRef<ReturnType<typeof setTimeout>>(undefined)

  const [modal, setModal] = useState(false)
  const [editing, setEditing] = useState<ProductoProveedorRecord | null>(null)
  const [form, setForm] = useState({ proveedor: '', producto: '', precio_compra: '', preferido: false })
  const [saving, setSaving] = useState(false)

  const [deleting, setDeleting] = useState<ProductoProveedorRecord | null>(null)
  const [removing, setRemoving] = useState(false)

  const [marcandoPreferido, setMarcandoPreferido] = useState<number | null>(null)

  const precioVentaPorProducto = useMemo(() => {
    const map: Record<number, number> = {}
    for (const p of productos) map[p.id_producto] = Number(p.precio_actual) || 0
    return map
  }, [productos])

  const load = useCallback(async (s: string, prov: string, p: number) => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = { page: p, page_size: PAGE_SIZE }
      if (prov) params.proveedor = prov
      if (s) params.search = s
      const { data } = await api.get('/compras/productos-proveedor/', { params })
      setItems(data.results ?? data ?? [])
      setTotal(data.count ?? 0)
    } catch { toast.error('Error al cargar los vínculos producto-proveedor') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => {
    clearTimeout(searchTimer.current)
    searchTimer.current = setTimeout(() => { setPage(1); load(search, filterProveedor, 1) }, 350)
    return () => clearTimeout(searchTimer.current)
  }, [search, filterProveedor, load])

  const open = useCallback((r?: ProductoProveedorRecord) => {
    setEditing(r ?? null)
    setForm(r
      ? { proveedor: String(r.proveedor), producto: String(r.producto), precio_compra: String(r.precio_compra), preferido: r.preferido }
      : { proveedor: filterProveedor || '', producto: '', precio_compra: '', preferido: false })
    setModal(true)
  }, [filterProveedor])

  const save = useCallback(async () => {
    if (!form.proveedor) { toast.error('Elegí el proveedor'); return }
    if (!form.producto) { toast.error('Elegí el producto'); return }
    setSaving(true)
    try {
      const payload = {
        proveedor: Number(form.proveedor),
        producto: Number(form.producto),
        precio_compra: Number(form.precio_compra) || 0,
        preferido: form.preferido,
      }
      if (editing) {
        await api.put(`/compras/productos-proveedor/${editing.id_producto_proveedor}/`, payload)
        toast.success('Vínculo actualizado')
      } else {
        await api.post('/compras/productos-proveedor/', payload)
        toast.success('Vínculo creado')
      }
      setModal(false)
      load(search, filterProveedor, page)
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSaving(false) }
  }, [form, editing, load, search, filterProveedor, page])

  const marcarPreferido = useCallback(async (r: ProductoProveedorRecord) => {
    setMarcandoPreferido(r.id_producto_proveedor)
    try {
      await api.patch(`/compras/productos-proveedor/${r.id_producto_proveedor}/`, { preferido: !r.preferido })
      load(search, filterProveedor, page)
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setMarcandoPreferido(null) }
  }, [load, search, filterProveedor, page])

  const remove = useCallback(async () => {
    if (!deleting) return
    setRemoving(true)
    try {
      await api.delete(`/compras/productos-proveedor/${deleting.id_producto_proveedor}/`)
      toast.success('Vínculo eliminado')
      setDeleting(null)
      load(search, filterProveedor, page)
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setRemoving(false) }
  }, [deleting, load, search, filterProveedor, page])

  const columns: Column<ProductoProveedorRecord>[] = [
    {
      title: 'Preferido', key: 'preferido', width: 90,
      render: (_, r) => (
        <button
          onClick={() => marcarPreferido(r)}
          disabled={marcandoPreferido === r.id_producto_proveedor}
          title={r.preferido ? 'Proveedor preferido para este producto — clic para quitar' : 'Marcar como proveedor preferido para este producto'}
          className="mx-auto flex items-center justify-center disabled:opacity-40 cursor-pointer"
        >
          <Star className={`w-4.5 h-4.5 ${r.preferido ? 'fill-amber-400 text-amber-400' : 'text-slate-300 hover:text-amber-300'}`} />
        </button>
      ),
    },
    { title: 'Proveedor', key: 'proveedor', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.proveedor_nombre}</span> },
    { title: 'Producto', key: 'producto', render: (_, r) => <span className="text-sm text-slate-700">{r.producto_nombre}</span> },
    { title: 'Precio de Compra', key: 'precio', render: (_, r) => <span className="tabular-nums text-sm font-medium text-slate-800">{formatGs(r.precio_compra)}</span> },
    {
      title: 'Margen', key: 'margen',
      render: (_, r) => {
        const margen = calcularMargen(Number(r.precio_compra) || 0, precioVentaPorProducto[r.producto] || 0)
        return <span className={`tabular-nums text-sm font-bold ${MARGEN_TEXT_COLOR[margen.color]}`}>{formatMargen(margen)}</span>
      },
    },
    { title: 'Última Compra', key: 'fecha', render: (_, r) => <span className="text-sm text-slate-500">{r.fecha_ultima_compra ? formatFecha(r.fecha_ultima_compra) : '— sin compras'}</span> },
    {
      title: '', key: 'acc', width: 100,
      render: (_, r) => (
        <div className="flex items-center gap-1">
          <Button size="sm" variant="secondary" onClick={() => open(r)}><Edit2 className="w-3.5 h-3.5" /></Button>
          <Button size="sm" variant="danger" onClick={() => setDeleting(r)}><Trash2 className="w-3.5 h-3.5" /></Button>
        </div>
      ),
    },
  ]

  return (
    <>
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4">
        <div className="flex items-center justify-between gap-4 mb-3">
          <label className={labelClass}>Buscar producto</label>
          <Button size="sm" variant="primary" onClick={() => open()}>
            <Plus className="w-3.5 h-3.5" /> Nuevo Vínculo
          </Button>
        </div>
        <div className="flex flex-wrap gap-3">
          <div className="relative max-w-sm flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            <input placeholder="Descripción del producto..." value={search} onChange={e => setSearch(e.target.value)} className={`${inputClass} pl-9`} />
          </div>
          <select value={filterProveedor} onChange={e => setFilterProveedor(e.target.value)} className={inputClass} style={{ maxWidth: 260 }}>
            <option value="">Todos los proveedores</option>
            {proveedores.map(p => <option key={p.id_proveedor} value={p.id_proveedor}>{p.razon_social}</option>)}
          </select>
        </div>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden mt-4">
        <div className="p-1">
          <Table columns={columns} dataSource={items} rowKey="id_producto_proveedor" loading={loading}
            pageSize={PAGE_SIZE} page={page}
            onPageChange={p => { setPage(p); load(search, filterProveedor, p) }}
            total={total} />
        </div>
      </div>

      <Modal open={modal} title={editing ? 'Editar Vínculo' : 'Nuevo Vínculo'} onOk={save} onCancel={() => setModal(false)} okText={editing ? 'Guardar' : 'Crear'} confirmLoading={saving} width={420}>
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Proveedor *</label>
            <select value={form.proveedor} onChange={e => setForm(f => ({ ...f, proveedor: e.target.value }))} className={inputClass}>
              <option value="">Seleccionar proveedor...</option>
              {proveedores.map(p => <option key={p.id_proveedor} value={p.id_proveedor}>{p.razon_social}</option>)}
            </select>
          </div>
          <div>
            <label className={labelClass}>Producto *</label>
            <select value={form.producto} onChange={e => setForm(f => ({ ...f, producto: e.target.value }))} className={inputClass}>
              <option value="">Seleccionar producto...</option>
              {productos.map(p => <option key={p.id_producto} value={p.id_producto}>{p.descripcion}</option>)}
            </select>
          </div>
          <div>
            <label className={labelClass}>Precio de Compra (Gs.)</label>
            <input type="number" min={0} step={100} value={form.precio_compra} onChange={e => setForm(f => ({ ...f, precio_compra: e.target.value }))} className={inputClass} />
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={form.preferido}
              onChange={e => setForm(f => ({ ...f, preferido: e.target.checked }))}
              className="w-4 h-4 rounded border-slate-300 text-amber-500 focus:ring-amber-400"
            />
            Proveedor preferido para este producto
          </label>
          {form.preferido && (
            <p className="text-xs text-slate-400">Al guardar, se desmarca automáticamente como preferido cualquier otro proveedor de este mismo producto.</p>
          )}
          {editing && (
            <p className="text-xs text-slate-400">La fecha de última compra se actualiza sola cuando se registra una Compra real — no se edita a mano.</p>
          )}
        </div>
      </Modal>

      <Modal
        open={!!deleting}
        title="Confirmar eliminación"
        onOk={remove}
        onCancel={() => setDeleting(null)}
        okText="Eliminar"
        confirmLoading={removing}
        width={400}
      >
        <div className="flex items-start gap-3 py-1">
          <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center shrink-0">
            <Trash2 className="w-5 h-5 text-red-500" />
          </div>
          <div>
            <p className="text-sm text-slate-700">
              ¿Eliminar el vínculo con <strong className="text-slate-900">"{deleting?.producto_nombre}"</strong>?
            </p>
            <p className="text-xs text-slate-400 mt-1">Esto no borra el historial de compras ya registradas, solo el precio de referencia guardado.</p>
          </div>
        </div>
      </Modal>
    </>
  )
}
