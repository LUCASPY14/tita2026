import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Edit2, Trash2, Plus } from 'lucide-react'
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
  const [form, setForm] = useState({ nombre: '', descripcion: '', es_precio_base: false })
  const [saving, setSaving] = useState(false)

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
    setForm(l ? { nombre: l.nombre, descripcion: l.descripcion, es_precio_base: l.es_precio_base } : { nombre: '', descripcion: '', es_precio_base: false })
    setModal(true)
  }, [])

  const save = useCallback(async () => {
    if (!form.nombre) { toast.error('Ingresá el nombre'); return }
    setSaving(true)
    try {
      if (editing) {
        await api.put(`/productos/listas-precio/${editing.id}/`, form)
        toast.success('Lista de precio actualizada')
      } else {
        await api.post('/productos/listas-precio/', form)
        toast.success('Lista de precio creada')
      }
      setModal(false); load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSaving(false) }
  }, [form, editing, load])

  const columns: Column<ListaPrecio>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Descripción', key: 'desc', render: (_, r) => <span className="text-sm text-slate-500">{r.descripcion || '—'}</span> },
    { title: 'Precio Base', key: 'base', render: (_, r) => <Badge color={r.es_precio_base ? 'green' : 'default'}>{r.es_precio_base ? 'Sí' : 'No'}</Badge> },
    {
      title: '', key: 'acc', width: 100,
      render: (_, r) => (
        <div className="flex items-center gap-1">
          <Button size="sm" variant="secondary" onClick={() => open(r)}><Edit2 className="w-3.5 h-3.5" /></Button>
          <Button size="sm" variant="danger" onClick={() => onDelete({ url: `/productos/listas-precio/${r.id}/`, label: r.nombre, reloadFn: load })}>
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
          <Table columns={columns} dataSource={items} rowKey="id" loading={loading} pageSize={20} />
        </div>
      </div>
      <Modal open={modal} title={editing ? 'Editar Lista de Precio' : 'Nueva Lista de Precio'} onOk={save} onCancel={() => setModal(false)} okText={editing ? 'Guardar' : 'Crear'} confirmLoading={saving} width={420}>
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Descripción</label>
            <textarea value={form.descripcion} onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))} rows={2} className={`${inputClass} resize-none`} />
          </div>
          {toggleSwitch(form.es_precio_base, v => setForm(f => ({ ...f, es_precio_base: v })), 'Es precio base')}
        </div>
      </Modal>
    </>
  )
}
