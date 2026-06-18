import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Edit2, Trash2, Plus } from 'lucide-react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, inputClass, labelClass, toggleSwitch, type PlanAlmuerzo, type DeleteTarget } from './helpers'

const DIAS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

export default function TabPlanesAlmuerzo({ onDelete }: { onDelete: (t: DeleteTarget) => void }) {
  const [items, setItems] = useState<PlanAlmuerzo[]>([])
  const [loading, setLoading] = useState(false)
  const [modal, setModal] = useState(false)
  const [editing, setEditing] = useState<PlanAlmuerzo | null>(null)
  const [form, setForm] = useState({ nombre: '', tipo: 'CANTIDAD' as 'CANTIDAD' | 'SIN_LIMITE', precio_mensual: '', cantidad_almuerzos_mes: '', dias_semana_incluidos: [] as number[], activo: true })
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/almuerzos/planes-almuerzo/', { params: { page_size: 100 } })
      setItems(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar planes de almuerzo') }
    finally { setLoading(false) }
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load() }, [load])

  const open = useCallback((p?: PlanAlmuerzo) => {
    setEditing(p ?? null)
    setForm(p
      ? { nombre: p.nombre, tipo: p.tipo, precio_mensual: String(p.precio_mensual), cantidad_almuerzos_mes: p.cantidad_almuerzos_mes != null ? String(p.cantidad_almuerzos_mes) : '', dias_semana_incluidos: p.dias_semana_incluidos ?? [], activo: p.activo }
      : { nombre: '', tipo: 'CANTIDAD', precio_mensual: '', cantidad_almuerzos_mes: '', dias_semana_incluidos: [], activo: true })
    setModal(true)
  }, [])

  const toggleDia = (i: number) => {
    setForm(f => ({
      ...f,
      dias_semana_incluidos: f.dias_semana_incluidos.includes(i)
        ? f.dias_semana_incluidos.filter(d => d !== i)
        : [...f.dias_semana_incluidos, i],
    }))
  }

  const save = useCallback(async () => {
    if (!form.nombre) { toast.error('Ingresá el nombre'); return }
    setSaving(true)
    try {
      const payload = {
        ...form,
        precio_mensual: Number(form.precio_mensual) || 0,
        cantidad_almuerzos_mes: form.tipo === 'CANTIDAD' && form.cantidad_almuerzos_mes ? Number(form.cantidad_almuerzos_mes) : null,
      }
      if (editing) {
        await api.put(`/almuerzos/planes-almuerzo/${editing.id}/`, payload)
        toast.success('Plan actualizado')
      } else {
        await api.post('/almuerzos/planes-almuerzo/', payload)
        toast.success('Plan creado')
      }
      setModal(false); load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSaving(false) }
  }, [form, editing, load])

  const columns: Column<PlanAlmuerzo>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Tipo', key: 'tipo', width: 120, render: (_, r) => <Badge color={r.tipo === 'SIN_LIMITE' ? 'blue' : 'orange'}>{r.tipo === 'SIN_LIMITE' ? 'Sin límite' : 'Por cantidad'}</Badge> },
    { title: 'Precio mensual', key: 'precio', width: 150, render: (_, r) => <span className="tabular-nums text-sm text-slate-700">Gs. {(Number(r.precio_mensual) || 0).toLocaleString('es-PY')}</span> },
    { title: 'Cant./mes', key: 'cant', width: 100, render: (_, r) => <span className="tabular-nums text-sm text-slate-500">{r.cantidad_almuerzos_mes ?? '—'}</span> },
    { title: 'Estado', key: 'activo', width: 90, render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge> },
    {
      title: '', key: 'acc', width: 100,
      render: (_, r) => (
        <div className="flex items-center gap-1">
          <Button size="sm" variant="secondary" onClick={() => open(r)}><Edit2 className="w-3.5 h-3.5" /></Button>
          <Button size="sm" variant="danger" onClick={() => onDelete({ url: `/almuerzos/planes-almuerzo/${r.id}/`, label: r.nombre, reloadFn: load })}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <>
      <div className="flex justify-end mb-3">
        <Button variant="primary" onClick={() => open()}><Plus className="w-4 h-4" /> Nuevo plan</Button>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table columns={columns} dataSource={items} rowKey="id" loading={loading} pageSize={20} />
        </div>
      </div>
      <Modal open={modal} title={editing ? 'Editar Plan de Almuerzo' : 'Nuevo Plan de Almuerzo'} onOk={save} onCancel={() => setModal(false)} okText={editing ? 'Guardar' : 'Crear'} confirmLoading={saving} width={480}>
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} className={inputClass} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Tipo</label>
              <select value={form.tipo} onChange={e => setForm(f => ({ ...f, tipo: e.target.value as 'CANTIDAD' | 'SIN_LIMITE' }))} className={inputClass}>
                <option value="CANTIDAD">Por cantidad</option>
                <option value="SIN_LIMITE">Sin límite</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Precio mensual (Gs.)</label>
              <input type="number" min={0} step={1000} value={form.precio_mensual} onChange={e => setForm(f => ({ ...f, precio_mensual: e.target.value }))} className={inputClass} />
            </div>
          </div>
          {form.tipo === 'CANTIDAD' && (
            <div>
              <label className={labelClass}>Cantidad almuerzos/mes</label>
              <input type="number" min={1} value={form.cantidad_almuerzos_mes} onChange={e => setForm(f => ({ ...f, cantidad_almuerzos_mes: e.target.value }))} className={inputClass} />
            </div>
          )}
          <div>
            <label className={labelClass}>Días de semana incluidos</label>
            <div className="flex flex-wrap gap-2 mt-1">
              {DIAS.map((dia, i) => {
                const checked = form.dias_semana_incluidos.includes(i)
                return (
                  <button key={i} type="button" onClick={() => toggleDia(i)}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-colors cursor-pointer ${checked ? 'bg-green-500 text-white border-green-500' : 'bg-white text-slate-600 border-slate-200 hover:border-green-400'}`}>
                    {dia}
                  </button>
                )
              })}
            </div>
          </div>
          {toggleSwitch(form.activo, v => setForm(f => ({ ...f, activo: v })), 'Activo')}
        </div>
      </Modal>
    </>
  )
}
