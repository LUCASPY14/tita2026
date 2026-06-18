import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Edit2, Trash2, Plus } from 'lucide-react'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, inputClass, labelClass, type Categoria, type DeleteTarget } from './helpers'

export default function TabCategorias({ onDelete }: { onDelete: (t: DeleteTarget) => void }) {
  const [items, setItems] = useState<Categoria[]>([])
  const [loading, setLoading] = useState(false)
  const [modal, setModal] = useState(false)
  const [editing, setEditing] = useState<Categoria | null>(null)
  const [form, setForm] = useState({ nombre: '', descripcion: '' })
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/productos/categorias/', { params: { page_size: 100 } })
      setItems(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar categorías') }
    finally { setLoading(false) }
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load() }, [load])

  const open = useCallback((c?: Categoria) => {
    setEditing(c ?? null)
    setForm(c ? { nombre: c.nombre, descripcion: c.descripcion } : { nombre: '', descripcion: '' })
    setModal(true)
  }, [])

  const save = useCallback(async () => {
    if (!form.nombre) { toast.error('Ingresá el nombre'); return }
    setSaving(true)
    try {
      if (editing) {
        await api.put(`/productos/categorias/${editing.id}/`, form)
        toast.success('Categoría actualizada')
      } else {
        await api.post('/productos/categorias/', form)
        toast.success('Categoría creada')
      }
      setModal(false); load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSaving(false) }
  }, [form, editing, load])

  const columns: Column<Categoria>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Descripción', key: 'desc', render: (_, r) => <span className="text-sm text-slate-500">{r.descripcion || '—'}</span> },
    {
      title: '', key: 'acc', width: 100,
      render: (_, r) => (
        <div className="flex items-center gap-1">
          <Button size="sm" variant="secondary" onClick={() => open(r)}><Edit2 className="w-3.5 h-3.5" /></Button>
          <Button size="sm" variant="danger" onClick={() => onDelete({ url: `/productos/categorias/${r.id}/`, label: r.nombre, reloadFn: load })}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <>
      <div className="flex justify-end mb-3">
        <Button variant="primary" onClick={() => open()}><Plus className="w-4 h-4" /> Nueva categoría</Button>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table columns={columns} dataSource={items} rowKey="id" loading={loading} pageSize={20} />
        </div>
      </div>
      <Modal open={modal} title={editing ? 'Editar Categoría' : 'Nueva Categoría'} onOk={save} onCancel={() => setModal(false)} okText={editing ? 'Guardar' : 'Crear'} confirmLoading={saving} width={420}>
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Descripción</label>
            <textarea value={form.descripcion} onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))} rows={2} className={`${inputClass} resize-none`} />
          </div>
        </div>
      </Modal>
    </>
  )
}
