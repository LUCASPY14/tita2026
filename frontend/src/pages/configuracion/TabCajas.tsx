import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Edit2, Trash2, Plus } from 'lucide-react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, inputClass, labelClass, toggleSwitch, type Caja, type DeleteTarget } from './helpers'

export default function TabCajas({ onDelete }: { onDelete: (t: DeleteTarget) => void }) {
  const [items, setItems] = useState<Caja[]>([])
  const [loading, setLoading] = useState(false)
  const [modal, setModal] = useState(false)
  const [editing, setEditing] = useState<Caja | null>(null)
  const [form, setForm] = useState({ nombre: '', ubicacion: '', activo: true })
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/contabilidad/cajas/', { params: { page_size: 100 } })
      setItems(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar cajas') }
    finally { setLoading(false) }
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load() }, [load])

  const open = useCallback((c?: Caja) => {
    setEditing(c ?? null)
    setForm(c ? { nombre: c.nombre, ubicacion: c.ubicacion ?? '', activo: c.activo } : { nombre: '', ubicacion: '', activo: true })
    setModal(true)
  }, [])

  const save = useCallback(async () => {
    if (!form.nombre) { toast.error('Ingresá el nombre'); return }
    setSaving(true)
    try {
      const payload = { ...form, ubicacion: form.ubicacion || null }
      if (editing) {
        await api.put(`/contabilidad/cajas/${editing.id_caja}/`, payload)
        toast.success('Caja actualizada')
      } else {
        await api.post('/contabilidad/cajas/', payload)
        toast.success('Caja creada')
      }
      setModal(false); load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSaving(false) }
  }, [form, editing, load])

  const columns: Column<Caja>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Ubicación', key: 'ubicacion', render: (_, r) => <span className="text-sm text-slate-600">{r.ubicacion || '—'}</span> },
    { title: 'Estado', key: 'activo', render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activa' : 'Inactiva'}</Badge> },
    {
      title: '', key: 'acc', width: 100,
      render: (_, r) => (
        <div className="flex items-center gap-1">
          <Button size="sm" variant="secondary" onClick={() => open(r)}><Edit2 className="w-3.5 h-3.5" /></Button>
          <Button size="sm" variant="danger" onClick={() => onDelete({ url: `/contabilidad/cajas/${r.id_caja}/`, label: r.nombre, reloadFn: load })}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <>
      <div className="flex justify-end mb-3">
        <Button variant="primary" onClick={() => open()}><Plus className="w-4 h-4" /> Nueva caja</Button>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table columns={columns} dataSource={items} rowKey="id_caja" loading={loading} pageSize={20} />
        </div>
      </div>
      <Modal open={modal} title={editing ? 'Editar Caja' : 'Nueva Caja'} onOk={save} onCancel={() => setModal(false)} okText={editing ? 'Guardar' : 'Crear'} confirmLoading={saving} width={420}>
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Ubicación</label>
            <input value={form.ubicacion} onChange={e => setForm(f => ({ ...f, ubicacion: e.target.value }))} className={inputClass} />
          </div>
          {toggleSwitch(form.activo, v => setForm(f => ({ ...f, activo: v })), 'Activa')}
        </div>
      </Modal>
    </>
  )
}
