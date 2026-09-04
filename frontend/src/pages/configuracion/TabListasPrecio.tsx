import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Edit2, Trash2, Plus, Copy } from 'lucide-react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, inputClass, labelClass, toggleSwitch, type ListaPrecio, type DeleteTarget } from './helpers'

export default function TabListasPrecio({ onDelete }: { onDelete: (t: DeleteTarget) => void }) {
  const [items, setItems] = useState<ListaPrecio[]>([])
  const [loading, setLoading] = useState(false)
  const [modal, setModal] = useState(false)
  const [editing, setEditing] = useState<ListaPrecio | null>(null)
  const [form, setForm] = useState({ nombre: '', fecha_vigencia: '', moneda: 'PYG', activo: true, es_por_defecto: false })
  const [saving, setSaving] = useState(false)

  const [copiarModal, setCopiarModal] = useState<ListaPrecio | null>(null)
  const [copiarForm, setCopiarForm] = useState({ desde_lista: '', ajuste_porcentual: '0' })
  const [copiando, setCopiando] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/productos/listas-precio/', { params: { page_size: 100 } })
      setItems(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar listas de precio') }
    finally { setLoading(false) }
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load() }, [load])

  const open = useCallback((l?: ListaPrecio) => {
    setEditing(l ?? null)
    setForm(l
      ? { nombre: l.nombre, fecha_vigencia: l.fecha_vigencia ?? '', moneda: l.moneda, activo: l.activo, es_por_defecto: l.es_por_defecto }
      : { nombre: '', fecha_vigencia: '', moneda: 'PYG', activo: true, es_por_defecto: false })
    setModal(true)
  }, [])

  const save = useCallback(async () => {
    if (!form.nombre) { toast.error('Ingresá el nombre'); return }
    setSaving(true)
    try {
      const payload = { ...form, fecha_vigencia: form.fecha_vigencia || null }
      if (editing) {
        await api.put(`/productos/listas-precio/${editing.id_lista_precio}/`, payload)
        toast.success('Lista de precio actualizada')
      } else {
        await api.post('/productos/listas-precio/', payload)
        toast.success('Lista de precio creada')
      }
      setModal(false); load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSaving(false) }
  }, [form, editing, load])

  const abrirCopiar = useCallback((l: ListaPrecio) => {
    setCopiarModal(l)
    setCopiarForm({ desde_lista: '', ajuste_porcentual: '0' })
  }, [])

  const copiarPrecios = useCallback(async () => {
    if (!copiarModal) return
    if (!copiarForm.desde_lista) { toast.error('Elegí de qué lista copiar'); return }
    setCopiando(true)
    try {
      const { data } = await api.post(`/productos/listas-precio/${copiarModal.id_lista_precio}/copiar-precios/`, {
        desde_lista: Number(copiarForm.desde_lista),
        ajuste_porcentual: Number(copiarForm.ajuste_porcentual) || 0,
      })
      toast.success(`Precios copiados: ${data.creados} nuevos, ${data.actualizados} actualizados`)
      setCopiarModal(null)
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setCopiando(false) }
  }, [copiarModal, copiarForm])

  const columns: Column<ListaPrecio>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Moneda', key: 'moneda', render: (_, r) => <span className="text-sm text-slate-500">{r.moneda}</span> },
    { title: 'Vigente desde', key: 'fecha_vigencia', render: (_, r) => <span className="text-sm text-slate-500">{r.fecha_vigencia || '—'}</span> },
    { title: 'Activa', key: 'activo', render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Sí' : 'No'}</Badge> },
    { title: 'Por defecto', key: 'default', render: (_, r) => <Badge color={r.es_por_defecto ? 'blue' : 'default'}>{r.es_por_defecto ? 'Sí' : 'No'}</Badge> },
    {
      title: '', key: 'acc', width: 140,
      render: (_, r) => (
        <div className="flex items-center gap-1">
          <Button size="sm" variant="secondary" onClick={() => abrirCopiar(r)} title="Copiar precios desde otra lista">
            <Copy className="w-3.5 h-3.5" />
          </Button>
          <Button size="sm" variant="secondary" onClick={() => open(r)}><Edit2 className="w-3.5 h-3.5" /></Button>
          <Button size="sm" variant="danger" onClick={() => onDelete({ url: `/productos/listas-precio/${r.id_lista_precio}/`, label: r.nombre, reloadFn: load })}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <>
      <div className="flex justify-end mb-3">
        <Button variant="primary" onClick={() => open()}><Plus className="w-4 h-4" /> Nueva lista</Button>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table columns={columns} dataSource={items} rowKey="id_lista_precio" loading={loading} pageSize={20} />
        </div>
      </div>
      <Modal open={modal} title={editing ? 'Editar Lista de Precio' : 'Nueva Lista de Precio'} onOk={save} onCancel={() => setModal(false)} okText={editing ? 'Guardar' : 'Crear'} confirmLoading={saving} width={420}>
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Moneda</label>
            <input value={form.moneda} onChange={e => setForm(f => ({ ...f, moneda: e.target.value.toUpperCase() }))} maxLength={3} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Vigente desde</label>
            <input type="date" value={form.fecha_vigencia} onChange={e => setForm(f => ({ ...f, fecha_vigencia: e.target.value }))} className={inputClass} />
          </div>
          {toggleSwitch(form.activo, v => setForm(f => ({ ...f, activo: v })), 'Lista activa')}
          {toggleSwitch(form.es_por_defecto, v => setForm(f => ({ ...f, es_por_defecto: v })), 'Usar como lista por defecto')}
          {form.es_por_defecto && (
            <p className="text-xs text-slate-400">Al guardar, se desmarca automáticamente la lista que hoy es la de por defecto.</p>
          )}
        </div>
      </Modal>
      <Modal
        open={!!copiarModal}
        title={`Copiar precios a "${copiarModal?.nombre ?? ''}"`}
        onOk={copiarPrecios}
        onCancel={() => setCopiarModal(null)}
        okText="Copiar"
        confirmLoading={copiando}
        width={420}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Desde qué lista *</label>
            <select
              value={copiarForm.desde_lista}
              onChange={e => setCopiarForm(f => ({ ...f, desde_lista: e.target.value }))}
              className={inputClass}
            >
              <option value="">Seleccionar...</option>
              {items.filter(l => l.id_lista_precio !== copiarModal?.id_lista_precio).map(l => (
                <option key={l.id_lista_precio} value={l.id_lista_precio}>{l.nombre}</option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass}>Ajuste (%)</label>
            <input
              type="number" step="1" value={copiarForm.ajuste_porcentual}
              onChange={e => setCopiarForm(f => ({ ...f, ajuste_porcentual: e.target.value }))}
              className={inputClass}
            />
            <p className="text-xs text-slate-400 mt-1">
              Ej: -10 para 10% menos, 20 para 20% más. 0 = mismo precio.
            </p>
          </div>
          <p className="text-xs text-slate-400">
            Sobrescribe los precios que ya tenga "{copiarModal?.nombre}" para los productos de la lista origen. No toca productos que no estén en la lista origen.
          </p>
        </div>
      </Modal>
    </>
  )
}
