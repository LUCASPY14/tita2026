import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Edit2, Trash2, Plus } from 'lucide-react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, inputClass, labelClass, toggleSwitch, type MedioPago, type DeleteTarget } from './helpers'

export default function TabMediosPago({ onDelete }: { onDelete: (t: DeleteTarget) => void }) {
  const [items, setItems] = useState<MedioPago[]>([])
  const [loading, setLoading] = useState(false)
  const [modal, setModal] = useState(false)
  const [editing, setEditing] = useState<MedioPago | null>(null)
  const [form, setForm] = useState({ descripcion: '', requiere_validacion: false, activo: true })
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/core/medios-pago/', { params: { page_size: 100 } })
      setItems(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar medios de pago') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const open = useCallback((m?: MedioPago) => {
    setEditing(m ?? null)
    setForm(m ? { descripcion: m.descripcion, requiere_validacion: m.requiere_validacion, activo: m.activo } : { descripcion: '', requiere_validacion: false, activo: true })
    setModal(true)
  }, [])

  const save = useCallback(async () => {
    if (!form.descripcion) { toast.error('Ingresá la descripción'); return }
    setSaving(true)
    try {
      if (editing) {
        await api.put(`/core/medios-pago/${editing.id}/`, form)
        toast.success('Medio de pago actualizado')
      } else {
        await api.post('/core/medios-pago/', form)
        toast.success('Medio de pago creado')
      }
      setModal(false); load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSaving(false) }
  }, [form, editing, load])

  const columns: Column<MedioPago>[] = [
    { title: 'Descripción', key: 'descripcion', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.descripcion}</span> },
    { title: 'Requiere validación', key: 'req_val', width: 160, render: (_, r) => <Badge color={r.requiere_validacion ? 'blue' : 'default'}>{r.requiere_validacion ? 'Sí' : 'No'}</Badge> },
    { title: 'Estado', key: 'activo', render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge> },
    {
      title: '', key: 'acc', width: 100,
      render: (_, r) => (
        <div className="flex items-center gap-1">
          <Button size="sm" variant="secondary" onClick={() => open(r)}><Edit2 className="w-3.5 h-3.5" /></Button>
          <Button size="sm" variant="danger" onClick={() => onDelete({ url: `/core/medios-pago/${r.id}/`, label: r.descripcion, reloadFn: load })}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <>
      <div className="flex justify-end mb-3">
        <Button variant="primary" onClick={() => open()}><Plus className="w-4 h-4" /> Nuevo medio</Button>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table columns={columns} dataSource={items} rowKey="id" loading={loading} pageSize={20} />
        </div>
      </div>
      <Modal open={modal} title={editing ? 'Editar Medio de Pago' : 'Nuevo Medio de Pago'} onOk={save} onCancel={() => setModal(false)} okText={editing ? 'Guardar' : 'Crear'} confirmLoading={saving} width={420}>
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Descripción *</label>
            <input value={form.descripcion} onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))} className={inputClass} />
          </div>
          <div className="flex flex-col gap-3">
            {toggleSwitch(form.requiere_validacion, v => setForm(f => ({ ...f, requiere_validacion: v })), 'Requiere validación')}
            {toggleSwitch(form.activo, v => setForm(f => ({ ...f, activo: v })), 'Activo')}
          </div>
        </div>
      </Modal>
    </>
  )
}
