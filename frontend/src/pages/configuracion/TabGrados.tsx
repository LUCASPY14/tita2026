import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Edit2, Trash2, Plus } from 'lucide-react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, inputClass, labelClass, toggleSwitch, type Grado, type DeleteTarget } from './helpers'

export default function TabGrados({ onDelete }: { onDelete: (t: DeleteTarget) => void }) {
  const [items, setItems] = useState<Grado[]>([])
  const [loading, setLoading] = useState(false)
  const [modal, setModal] = useState(false)
  const [editing, setEditing] = useState<Grado | null>(null)
  const [form, setForm] = useState({ nombre: '', nivel: 1, orden: 1, es_ultimo: false, activo: true })
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/clientes/grados/', { params: { page_size: 100 } })
      setItems(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar grados') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const open = useCallback((g?: Grado) => {
    setEditing(g ?? null)
    setForm(g ? { nombre: g.nombre, nivel: g.nivel, orden: g.orden, es_ultimo: g.es_ultimo, activo: g.activo } : { nombre: '', nivel: 1, orden: 1, es_ultimo: false, activo: true })
    setModal(true)
  }, [])

  const save = useCallback(async () => {
    if (!form.nombre) { toast.error('Ingresá el nombre'); return }
    setSaving(true)
    try {
      if (editing) {
        await api.put(`/clientes/grados/${editing.id}/`, form)
        toast.success('Grado actualizado')
      } else {
        await api.post('/clientes/grados/', form)
        toast.success('Grado creado')
      }
      setModal(false); load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSaving(false) }
  }, [form, editing, load])

  const columns: Column<Grado>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Nivel', key: 'nivel', width: 70, render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{r.nivel}</span> },
    { title: 'Orden', key: 'orden', width: 70, render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{r.orden}</span> },
    { title: 'Último', key: 'ultimo', width: 80, render: (_, r) => <Badge color={r.es_ultimo ? 'purple' : 'default'}>{r.es_ultimo ? 'Sí' : 'No'}</Badge> },
    { title: 'Estado', key: 'activo', width: 90, render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge> },
    {
      title: '', key: 'acc', width: 100,
      render: (_, r) => (
        <div className="flex items-center gap-1">
          <Button size="sm" variant="secondary" onClick={() => open(r)}><Edit2 className="w-3.5 h-3.5" /></Button>
          <Button size="sm" variant="danger" onClick={() => onDelete({ url: `/clientes/grados/${r.id}/`, label: r.nombre, reloadFn: load })}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <>
      <div className="flex justify-end mb-3">
        <Button variant="primary" onClick={() => open()}><Plus className="w-4 h-4" /> Nuevo grado</Button>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table columns={columns} dataSource={items} rowKey="id" loading={loading} pageSize={20} />
        </div>
      </div>
      <Modal open={modal} title={editing ? 'Editar Grado' : 'Nuevo Grado'} onOk={save} onCancel={() => setModal(false)} okText={editing ? 'Guardar' : 'Crear'} confirmLoading={saving} width={420}>
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} placeholder="1° Grado" className={inputClass} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Nivel (1-12)</label>
              <input type="number" min={1} max={12} value={form.nivel} onChange={e => setForm(f => ({ ...f, nivel: Number(e.target.value) }))} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Orden de visualización</label>
              <input type="number" min={1} value={form.orden} onChange={e => setForm(f => ({ ...f, orden: Number(e.target.value) }))} className={inputClass} />
            </div>
          </div>
          <div className="flex flex-col gap-3">
            {toggleSwitch(form.es_ultimo, v => setForm(f => ({ ...f, es_ultimo: v })), 'Es el último grado')}
            {toggleSwitch(form.activo, v => setForm(f => ({ ...f, activo: v })), 'Activo')}
          </div>
        </div>
      </Modal>
    </>
  )
}
