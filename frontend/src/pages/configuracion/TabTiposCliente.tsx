import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Edit2, Trash2, Plus } from 'lucide-react'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, inputClass, labelClass, type TipoCliente, type DeleteTarget } from './helpers'

export default function TabTiposCliente({ onDelete }: { onDelete: (t: DeleteTarget) => void }) {
  const [items, setItems] = useState<TipoCliente[]>([])
  const [loading, setLoading] = useState(false)
  const [modal, setModal] = useState(false)
  const [editing, setEditing] = useState<TipoCliente | null>(null)
  const [form, setForm] = useState({ nombre: '', descripcion: '', descuento_porcentaje: '0' })
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/clientes/tipos-cliente/', { params: { page_size: 100 } })
      setItems(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar tipos de cliente') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const open = useCallback((t?: TipoCliente) => {
    setEditing(t ?? null)
    setForm(t ? { nombre: t.nombre, descripcion: t.descripcion, descuento_porcentaje: String(Number(t.descuento_porcentaje) || 0) } : { nombre: '', descripcion: '', descuento_porcentaje: '0' })
    setModal(true)
  }, [])

  const save = useCallback(async () => {
    if (!form.nombre) { toast.error('Ingresá el nombre'); return }
    setSaving(true)
    try {
      const payload = { ...form, descuento_porcentaje: Number(form.descuento_porcentaje) || 0 }
      if (editing) {
        await api.put(`/clientes/tipos-cliente/${editing.id}/`, payload)
        toast.success('Tipo de cliente actualizado')
      } else {
        await api.post('/clientes/tipos-cliente/', payload)
        toast.success('Tipo de cliente creado')
      }
      setModal(false); load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSaving(false) }
  }, [form, editing, load])

  const columns: Column<TipoCliente>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Descripción', key: 'desc', render: (_, r) => <span className="text-sm text-slate-500">{r.descripcion || '—'}</span> },
    { title: 'Descuento', key: 'desc_pct', render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{Number(r.descuento_porcentaje) || 0}%</span> },
    {
      title: '', key: 'acc', width: 100,
      render: (_, r) => (
        <div className="flex items-center gap-1">
          <Button size="sm" variant="secondary" onClick={() => open(r)}><Edit2 className="w-3.5 h-3.5" /></Button>
          <Button size="sm" variant="danger" onClick={() => onDelete({ url: `/clientes/tipos-cliente/${r.id}/`, label: r.nombre, reloadFn: load })}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <>
      <div className="flex justify-end mb-3">
        <Button variant="primary" onClick={() => open()}><Plus className="w-4 h-4" /> Nuevo tipo</Button>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table columns={columns} dataSource={items} rowKey="id" loading={loading} pageSize={20} />
        </div>
      </div>
      <Modal open={modal} title={editing ? 'Editar Tipo de Cliente' : 'Nuevo Tipo de Cliente'} onOk={save} onCancel={() => setModal(false)} okText={editing ? 'Guardar' : 'Crear'} confirmLoading={saving} width={420}>
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Descripción</label>
            <textarea value={form.descripcion} onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))} rows={2} className={`${inputClass} resize-none`} />
          </div>
          <div>
            <label className={labelClass}>Descuento (%)</label>
            <input type="number" min={0} max={100} step={0.5} value={form.descuento_porcentaje} onChange={e => setForm(f => ({ ...f, descuento_porcentaje: e.target.value }))} className={inputClass} />
          </div>
        </div>
      </Modal>
    </>
  )
}
