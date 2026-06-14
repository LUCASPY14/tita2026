import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Edit2, Trash2, Plus } from 'lucide-react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, inputClass, labelClass, toggleSwitch, type Alergeno, type DeleteTarget } from './helpers'

const SEVERIDAD_COLOR: Record<string, 'blue' | 'orange' | 'red' | 'purple'> = { BAJA: 'blue', MEDIA: 'orange', ALTA: 'red', CRITICA: 'purple' }

export default function TabAlergenos({ onDelete }: { onDelete: (t: DeleteTarget) => void }) {
  const [items, setItems] = useState<Alergeno[]>([])
  const [loading, setLoading] = useState(false)
  const [modal, setModal] = useState(false)
  const [editing, setEditing] = useState<Alergeno | null>(null)
  const [form, setForm] = useState({ nombre: '', descripcion: '', palabras_clave: '', severidad: 'MEDIA' as 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA', icono: '', activo: true })
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/almuerzos/alergenos/', { params: { page_size: 100 } })
      setItems(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar alérgenos') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const open = useCallback((a?: Alergeno) => {
    setEditing(a ?? null)
    setForm(a
      ? { nombre: a.nombre, descripcion: a.descripcion, palabras_clave: (a.palabras_clave ?? []).join(', '), severidad: a.severidad, icono: a.icono ?? '', activo: a.activo }
      : { nombre: '', descripcion: '', palabras_clave: '', severidad: 'MEDIA', icono: '', activo: true })
    setModal(true)
  }, [])

  const save = useCallback(async () => {
    if (!form.nombre) { toast.error('Ingresá el nombre'); return }
    setSaving(true)
    try {
      const palabras = form.palabras_clave ? form.palabras_clave.split(',').map(s => s.trim()).filter(Boolean) : []
      const payload = { ...form, palabras_clave: palabras }
      if (editing) {
        await api.put(`/almuerzos/alergenos/${editing.id}/`, payload)
        toast.success('Alérgeno actualizado')
      } else {
        await api.post('/almuerzos/alergenos/', payload)
        toast.success('Alérgeno creado')
      }
      setModal(false); load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSaving(false) }
  }, [form, editing, load])

  const columns: Column<Alergeno>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Severidad', key: 'sev', width: 110, render: (_, r) => <Badge color={SEVERIDAD_COLOR[r.severidad] ?? 'default'}>{r.severidad}</Badge> },
    { title: 'Icono', key: 'icono', width: 70, render: (_, r) => <span className="text-lg">{r.icono || '—'}</span> },
    { title: 'Estado', key: 'activo', width: 90, render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge> },
    {
      title: '', key: 'acc', width: 100,
      render: (_, r) => (
        <div className="flex items-center gap-1">
          <Button size="sm" variant="secondary" onClick={() => open(r)}><Edit2 className="w-3.5 h-3.5" /></Button>
          <Button size="sm" variant="danger" onClick={() => onDelete({ url: `/almuerzos/alergenos/${r.id}/`, label: r.nombre, reloadFn: load })}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <>
      <div className="flex justify-end mb-3">
        <Button variant="primary" onClick={() => open()}><Plus className="w-4 h-4" /> Nuevo alérgeno</Button>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table columns={columns} dataSource={items} rowKey="id" loading={loading} pageSize={20} />
        </div>
      </div>
      <Modal open={modal} title={editing ? 'Editar Alérgeno' : 'Nuevo Alérgeno'} onOk={save} onCancel={() => setModal(false)} okText={editing ? 'Guardar' : 'Crear'} confirmLoading={saving} width={460}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Nombre *</label>
              <input value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} placeholder="Gluten" className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Icono (emoji)</label>
              <input value={form.icono} onChange={e => setForm(f => ({ ...f, icono: e.target.value }))} placeholder="🌾" className={inputClass} />
            </div>
          </div>
          <div>
            <label className={labelClass}>Descripción</label>
            <textarea value={form.descripcion} onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))} rows={2} className={`${inputClass} resize-none`} />
          </div>
          <div>
            <label className={labelClass}>Severidad</label>
            <select value={form.severidad} onChange={e => setForm(f => ({ ...f, severidad: e.target.value as 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA' }))} className={inputClass}>
              <option value="BAJA">Baja</option>
              <option value="MEDIA">Media</option>
              <option value="ALTA">Alta</option>
              <option value="CRITICA">Crítica</option>
            </select>
          </div>
          <div>
            <label className={labelClass}>Palabras clave (separadas por coma)</label>
            <input value={form.palabras_clave} onChange={e => setForm(f => ({ ...f, palabras_clave: e.target.value }))} placeholder="trigo, harina, cebada" className={inputClass} />
          </div>
          {toggleSwitch(form.activo, v => setForm(f => ({ ...f, activo: v })), 'Activo')}
        </div>
      </Modal>
    </>
  )
}
