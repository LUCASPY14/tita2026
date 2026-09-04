import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Edit2, Trash2, Plus } from 'lucide-react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, inputClass, labelClass, toggleSwitch, type Impuesto, type DeleteTarget } from './helpers'

export default function TabImpuestos({ onDelete }: { onDelete: (t: DeleteTarget) => void }) {
  const [items, setItems] = useState<Impuesto[]>([])
  const [loading, setLoading] = useState(false)
  const [modal, setModal] = useState(false)
  const [editing, setEditing] = useState<Impuesto | null>(null)
  const [form, setForm] = useState({ nombre: '', porcentaje: '', vigente_desde: '', vigente_hasta: '', activo: true })
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/productos/impuestos/', { params: { page_size: 100 } })
      setItems(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar impuestos') }
    finally { setLoading(false) }
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load() }, [load])

  const open = useCallback((i?: Impuesto) => {
    setEditing(i ?? null)
    setForm(i
      ? { nombre: i.nombre, porcentaje: String(i.porcentaje), vigente_desde: i.vigente_desde ?? '', vigente_hasta: i.vigente_hasta ?? '', activo: i.activo }
      : { nombre: '', porcentaje: '', vigente_desde: '', vigente_hasta: '', activo: true })
    setModal(true)
  }, [])

  const save = useCallback(async () => {
    if (!form.nombre) { toast.error('Ingresá el nombre'); return }
    setSaving(true)
    try {
      const payload = { nombre: form.nombre, porcentaje: Number(form.porcentaje) || 0, vigente_desde: form.vigente_desde || null, vigente_hasta: form.vigente_hasta || null, activo: form.activo }
      if (editing) {
        await api.put(`/productos/impuestos/${editing.id_impuesto}/`, payload)
        toast.success('Impuesto actualizado')
      } else {
        await api.post('/productos/impuestos/', payload)
        toast.success('Impuesto creado')
      }
      setModal(false); load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSaving(false) }
  }, [form, editing, load])

  const columns: Column<Impuesto>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Porcentaje', key: 'pct', width: 110, render: (_, r) => <span className="tabular-nums text-sm font-semibold text-slate-700">{Number(r.porcentaje) || 0}%</span> },
    { title: 'Desde', key: 'desde', width: 120, render: (_, r) => <span className="text-xs text-slate-500">{r.vigente_desde ? new Date(r.vigente_desde).toLocaleDateString('es-PY') : '—'}</span> },
    { title: 'Hasta', key: 'hasta', width: 120, render: (_, r) => <span className="text-xs text-slate-500">{r.vigente_hasta ? new Date(r.vigente_hasta).toLocaleDateString('es-PY') : '—'}</span> },
    { title: 'Estado', key: 'activo', width: 90, render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge> },
    {
      title: '', key: 'acc', width: 100,
      render: (_, r) => (
        <div className="flex items-center gap-1">
          <Button size="sm" variant="secondary" onClick={() => open(r)}><Edit2 className="w-3.5 h-3.5" /></Button>
          <Button size="sm" variant="danger" onClick={() => onDelete({ url: `/productos/impuestos/${r.id_impuesto}/`, label: r.nombre, reloadFn: load })}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <>
      <div className="flex justify-end mb-3">
        <Button variant="primary" onClick={() => open()}><Plus className="w-4 h-4" /> Nuevo impuesto</Button>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table columns={columns} dataSource={items} rowKey="id_impuesto" loading={loading} pageSize={20} />
        </div>
      </div>
      <Modal open={modal} title={editing ? 'Editar Impuesto' : 'Nuevo Impuesto'} onOk={save} onCancel={() => setModal(false)} okText={editing ? 'Guardar' : 'Crear'} confirmLoading={saving} width={440}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Nombre *</label>
              <input value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} placeholder="IVA 10%" className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Porcentaje (%)</label>
              <input type="number" min={0} max={100} step={0.5} value={form.porcentaje} onChange={e => setForm(f => ({ ...f, porcentaje: e.target.value }))} className={inputClass} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Vigente desde</label>
              <input type="date" value={form.vigente_desde} onChange={e => setForm(f => ({ ...f, vigente_desde: e.target.value }))} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Vigente hasta</label>
              <input type="date" value={form.vigente_hasta} onChange={e => setForm(f => ({ ...f, vigente_hasta: e.target.value }))} className={inputClass} />
            </div>
          </div>
          {toggleSwitch(form.activo, v => setForm(f => ({ ...f, activo: v })), 'Activo')}
        </div>
      </Modal>
    </>
  )
}
