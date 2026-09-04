import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Edit2, Trash2, Plus } from 'lucide-react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, inputClass, labelClass, toggleSwitch, type UnidadMedida, type DeleteTarget } from './helpers'

export default function TabUnidadesMedida({ onDelete }: { onDelete: (t: DeleteTarget) => void }) {
  const [items, setItems] = useState<UnidadMedida[]>([])
  const [loading, setLoading] = useState(false)
  const [modal, setModal] = useState(false)
  const [editing, setEditing] = useState<UnidadMedida | null>(null)
  const [form, setForm] = useState({ nombre: '', abreviatura: '', activo: true })
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/productos/unidades-medida/', { params: { page_size: 100 } })
      setItems(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar unidades de medida') }
    finally { setLoading(false) }
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load() }, [load])

  const open = useCallback((u?: UnidadMedida) => {
    setEditing(u ?? null)
    setForm(u ? { nombre: u.nombre, abreviatura: u.abreviatura, activo: u.activo } : { nombre: '', abreviatura: '', activo: true })
    setModal(true)
  }, [])

  const save = useCallback(async () => {
    if (!form.nombre) { toast.error('Ingresá el nombre'); return }
    setSaving(true)
    try {
      if (editing) {
        await api.put(`/productos/unidades-medida/${editing.id_unidad_medida}/`, form)
        toast.success('Unidad actualizada')
      } else {
        await api.post('/productos/unidades-medida/', form)
        toast.success('Unidad creada')
      }
      setModal(false); load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSaving(false) }
  }, [form, editing, load])

  const columns: Column<UnidadMedida>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Abreviatura', key: 'abrev', width: 130, render: (_, r) => <code className="text-sm text-slate-600 bg-slate-100 rounded px-2 py-0.5">{r.abreviatura}</code> },
    { title: 'Estado', key: 'activo', width: 90, render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge> },
    {
      title: '', key: 'acc', width: 100,
      render: (_, r) => (
        <div className="flex items-center gap-1">
          <Button size="sm" variant="secondary" onClick={() => open(r)}><Edit2 className="w-3.5 h-3.5" /></Button>
          <Button size="sm" variant="danger" onClick={() => onDelete({ url: `/productos/unidades-medida/${r.id_unidad_medida}/`, label: r.nombre, reloadFn: load })}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <>
      <div className="flex justify-end mb-3">
        <Button variant="primary" onClick={() => open()}><Plus className="w-4 h-4" /> Nueva unidad</Button>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table columns={columns} dataSource={items} rowKey="id_unidad_medida" loading={loading} pageSize={20} />
        </div>
      </div>
      <Modal open={modal} title={editing ? 'Editar Unidad de Medida' : 'Nueva Unidad de Medida'} onOk={save} onCancel={() => setModal(false)} okText={editing ? 'Guardar' : 'Crear'} confirmLoading={saving} width={400}>
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} placeholder="Kilogramo" className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Abreviatura *</label>
            <input value={form.abreviatura} onChange={e => setForm(f => ({ ...f, abreviatura: e.target.value }))} placeholder="kg" className={inputClass} />
          </div>
          {toggleSwitch(form.activo, v => setForm(f => ({ ...f, activo: v })), 'Activo')}
        </div>
      </Modal>
    </>
  )
}
