import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Plus, Edit2, Trash2, CheckCircle } from 'lucide-react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, inputClass, labelClass, type DeleteTarget } from './helpers'

interface PrecioAlmuerzo {
  id: number
  precio_unitario: string | number
  fecha_inicio_vigencia: string
  fecha_fin_vigencia: string | null
  descripcion: string
  activo: boolean
}

function formatGs(n: string | number | null | undefined) {
  return 'Gs. ' + (Number(n) || 0).toLocaleString('es-PY')
}

function formatFecha(iso: string | null | undefined) {
  if (!iso) return '—'
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

const emptyForm = {
  precio_unitario: '',
  fecha_inicio_vigencia: new Date().toISOString().split('T')[0],
  fecha_fin_vigencia: '',
  descripcion: '',
  activo: true,
}

export default function TabPreciosAlmuerzo({ onDelete }: { onDelete: (t: DeleteTarget) => void }) {
  const [items, setItems] = useState<PrecioAlmuerzo[]>([])
  const [loading, setLoading] = useState(false)
  const [modal, setModal] = useState(false)
  const [editing, setEditing] = useState<PrecioAlmuerzo | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/almuerzos/precios-almuerzo/', { params: { page_size: 100 } })
      setItems(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar precios de almuerzo') }
    finally { setLoading(false) }
  }, [])

  // Carga de datos al montar: el setLoading(true) inicial en load() es intencional.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load() }, [load])

  const open = useCallback((p?: PrecioAlmuerzo) => {
    setEditing(p ?? null)
    setForm(p ? {
      precio_unitario: String(p.precio_unitario),
      fecha_inicio_vigencia: p.fecha_inicio_vigencia,
      fecha_fin_vigencia: p.fecha_fin_vigencia ?? '',
      descripcion: p.descripcion ?? '',
      activo: p.activo,
    } : emptyForm)
    setModal(true)
  }, [])

  const save = useCallback(async () => {
    if (!form.precio_unitario || Number(form.precio_unitario) <= 0) {
      toast.error('Ingresá el precio unitario')
      return
    }
    if (!form.fecha_inicio_vigencia) {
      toast.error('Ingresá la fecha de inicio')
      return
    }
    setSaving(true)
    try {
      const payload = {
        precio_unitario: Number(form.precio_unitario),
        fecha_inicio_vigencia: form.fecha_inicio_vigencia,
        fecha_fin_vigencia: form.fecha_fin_vigencia || null,
        descripcion: form.descripcion,
        activo: form.activo,
      }
      if (editing) {
        await api.put(`/almuerzos/precios-almuerzo/${editing.id}/`, payload)
        toast.success('Precio actualizado')
      } else {
        await api.post('/almuerzos/precios-almuerzo/', payload)
        toast.success('Precio creado')
      }
      setModal(false)
      load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSaving(false) }
  }, [form, editing, load])

  const columns: Column<PrecioAlmuerzo>[] = [
    {
      title: 'Precio unitario',
      key: 'precio',
      width: 160,
      render: (_, r) => (
        <span className="tabular-nums font-bold text-emerald-700 text-sm">
          {formatGs(r.precio_unitario)}
        </span>
      ),
    },
    {
      title: 'Vigencia desde',
      key: 'desde',
      width: 140,
      render: (_, r) => <span className="text-sm text-slate-700">{formatFecha(r.fecha_inicio_vigencia)}</span>,
    },
    {
      title: 'Vigencia hasta',
      key: 'hasta',
      width: 140,
      render: (_, r) => (
        <span className="text-sm text-slate-500">
          {r.fecha_fin_vigencia ? formatFecha(r.fecha_fin_vigencia) : <span className="italic text-slate-300">Sin vencimiento</span>}
        </span>
      ),
    },
    {
      title: 'Descripción',
      key: 'desc',
      render: (_, r) => <span className="text-sm text-slate-600">{r.descripcion || '—'}</span>,
    },
    {
      title: 'Estado',
      key: 'activo',
      width: 100,
      render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge>,
    },
    {
      title: '',
      key: 'acc',
      width: 90,
      render: (_, r) => (
        <div className="flex items-center gap-1">
          <Button size="sm" variant="secondary" onClick={() => open(r)}>
            <Edit2 className="w-3.5 h-3.5" />
          </Button>
          <Button size="sm" variant="danger" onClick={() => onDelete({
            url: `/almuerzos/precios-almuerzo/${r.id}/`,
            label: `Precio ${formatGs(r.precio_unitario)} (desde ${formatFecha(r.fecha_inicio_vigencia)})`,
            reloadFn: load,
          })}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  const vigente = items.find(p => p.activo && !p.fecha_fin_vigencia)
    ?? items.find(p => p.activo)

  return (
    <>
      {vigente && (
        <div className="mb-4 flex items-center gap-3 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3">
          <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-emerald-800">
              Precio vigente: {formatGs(vigente.precio_unitario)} por almuerzo
            </p>
            <p className="text-xs text-emerald-600 mt-0.5">
              Se aplica a todos los registros de consumo del comedor.
              Cambia hacia adelante — los consumos ya registrados mantienen su costo original.
            </p>
          </div>
        </div>
      )}

      <div className="flex justify-end mb-3">
        <Button variant="primary" onClick={() => open()}>
          <Plus className="w-4 h-4" />
          Nuevo precio
        </Button>
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table columns={columns} dataSource={items} rowKey="id" loading={loading} pageSize={20} />
        </div>
      </div>

      <Modal
        open={modal}
        title={editing ? 'Editar Precio de Almuerzo' : 'Nuevo Precio de Almuerzo'}
        onOk={save}
        onCancel={() => setModal(false)}
        okText={editing ? 'Guardar' : 'Crear'}
        confirmLoading={saving}
        width={460}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Precio por almuerzo (Gs.) *</label>
            <input
              type="number"
              min={1}
              step={1000}
              value={form.precio_unitario}
              onChange={e => setForm(f => ({ ...f, precio_unitario: e.target.value }))}
              placeholder="Ej: 15000"
              className={inputClass}
            />
            <p className="text-xs text-slate-400 mt-1">
              Se usa para calcular el costo de cada registro en el Comedor (plan por consumo).
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass}>Válido desde *</label>
              <input
                type="date"
                value={form.fecha_inicio_vigencia}
                onChange={e => setForm(f => ({ ...f, fecha_inicio_vigencia: e.target.value }))}
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Válido hasta (opcional)</label>
              <input
                type="date"
                value={form.fecha_fin_vigencia}
                onChange={e => setForm(f => ({ ...f, fecha_fin_vigencia: e.target.value }))}
                className={inputClass}
              />
            </div>
          </div>

          <div>
            <label className={labelClass}>Descripción</label>
            <input
              value={form.descripcion}
              onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))}
              placeholder="Ej: Ajuste por inflación julio 2026"
              className={inputClass}
            />
          </div>

          <label className="flex items-center gap-3 cursor-pointer">
            <div className="relative shrink-0">
              <input
                type="checkbox"
                className="sr-only peer"
                checked={form.activo}
                onChange={e => setForm(f => ({ ...f, activo: e.target.checked }))}
              />
              <div className="w-9 h-5 bg-slate-200 rounded-full peer-checked:bg-green-500 transition-colors" />
              <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
            </div>
            <span className="text-sm text-slate-700">Activo</span>
          </label>
        </div>
      </Modal>
    </>
  )
}
