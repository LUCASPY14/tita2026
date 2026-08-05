import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Edit2, Trash2, Plus } from 'lucide-react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, inputClass, labelClass, toggleSwitch, type TipoAlmuerzo, type DeleteTarget } from './helpers'

export default function TabTiposAlmuerzo({ onDelete }: { onDelete: (t: DeleteTarget) => void }) {
  const [items, setItems] = useState<TipoAlmuerzo[]>([])
  const [loading, setLoading] = useState(false)
  const [modal, setModal] = useState(false)
  const [editing, setEditing] = useState<TipoAlmuerzo | null>(null)
  const [form, setForm] = useState({ nombre: '', descripcion: '', precio_unitario: '', incluye_plato_principal: true, incluye_postre: false, incluye_bebida: false, activo: true, es_predeterminado: false })
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/almuerzos/tipos-almuerzo/', { params: { page_size: 100 } })
      setItems(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar tipos de almuerzo') }
    finally { setLoading(false) }
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load() }, [load])

  const open = useCallback((t?: TipoAlmuerzo) => {
    setEditing(t ?? null)
    setForm(t
      ? { nombre: t.nombre, descripcion: t.descripcion, precio_unitario: String(t.precio_unitario), incluye_plato_principal: t.incluye_plato_principal, incluye_postre: t.incluye_postre, incluye_bebida: t.incluye_bebida, activo: t.activo, es_predeterminado: t.es_predeterminado }
      : { nombre: '', descripcion: '', precio_unitario: '', incluye_plato_principal: true, incluye_postre: false, incluye_bebida: false, activo: true, es_predeterminado: false })
    setModal(true)
  }, [])

  const save = useCallback(async () => {
    if (!form.nombre) { toast.error('Ingresá el nombre'); return }
    setSaving(true)
    try {
      const payload = { ...form, precio_unitario: Number(form.precio_unitario) || 0 }
      if (editing) {
        await api.put(`/almuerzos/tipos-almuerzo/${editing.id}/`, payload)
        toast.success('Tipo de almuerzo actualizado')
      } else {
        await api.post('/almuerzos/tipos-almuerzo/', payload)
        toast.success('Tipo de almuerzo creado')
      }
      setModal(false); load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSaving(false) }
  }, [form, editing, load])

  const columns: Column<TipoAlmuerzo>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Precio unit.', key: 'precio', width: 130, render: (_, r) => <span className="tabular-nums text-sm text-slate-700">Gs. {(Number(r.precio_unitario) || 0).toLocaleString('es-PY')}</span> },
    { title: 'Plato Ppal', key: 'pp', width: 100, render: (_, r) => <Badge color={r.incluye_plato_principal ? 'green' : 'default'}>{r.incluye_plato_principal ? 'Sí' : 'No'}</Badge> },
    { title: 'Postre', key: 'pos', width: 80, render: (_, r) => <Badge color={r.incluye_postre ? 'green' : 'default'}>{r.incluye_postre ? 'Sí' : 'No'}</Badge> },
    { title: 'Bebida', key: 'beb', width: 80, render: (_, r) => <Badge color={r.incluye_bebida ? 'green' : 'default'}>{r.incluye_bebida ? 'Sí' : 'No'}</Badge> },
    { title: 'Estado', key: 'activo', width: 90, render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge> },
    { title: 'Predeterminado', key: 'predeterminado', width: 120, render: (_, r) => r.es_predeterminado ? <Badge color="blue">Predeterminado</Badge> : null },
    {
      title: '', key: 'acc', width: 100,
      render: (_, r) => (
        <div className="flex items-center gap-1">
          <Button size="sm" variant="secondary" onClick={() => open(r)}><Edit2 className="w-3.5 h-3.5" /></Button>
          <Button size="sm" variant="danger" onClick={() => onDelete({ url: `/almuerzos/tipos-almuerzo/${r.id}/`, label: r.nombre, reloadFn: load })}>
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
      <Modal open={modal} title={editing ? 'Editar Tipo de Almuerzo' : 'Nuevo Tipo de Almuerzo'} onOk={save} onCancel={() => setModal(false)} okText={editing ? 'Guardar' : 'Crear'} confirmLoading={saving} width={440}>
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
            <label className={labelClass}>Precio unitario (Gs.)</label>
            <input type="number" min={0} step={1000} value={form.precio_unitario} onChange={e => setForm(f => ({ ...f, precio_unitario: e.target.value }))} className={inputClass} />
          </div>
          <div className="flex flex-col gap-3">
            {toggleSwitch(form.incluye_plato_principal, v => setForm(f => ({ ...f, incluye_plato_principal: v })), 'Incluye plato principal')}
            {toggleSwitch(form.incluye_postre, v => setForm(f => ({ ...f, incluye_postre: v })), 'Incluye postre')}
            {toggleSwitch(form.incluye_bebida, v => setForm(f => ({ ...f, incluye_bebida: v })), 'Incluye bebida')}
            {toggleSwitch(form.activo, v => setForm(f => ({ ...f, activo: v })), 'Activo')}
            {toggleSwitch(form.es_predeterminado, v => setForm(f => ({ ...f, es_predeterminado: v })), 'Predeterminado (preseleccionado al registrar un consumo)')}
          </div>
        </div>
      </Modal>
    </>
  )
}
