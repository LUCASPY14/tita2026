import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Edit2, Plus } from 'lucide-react'
import api from '../../services/api'
import { formatDateOnly } from '../../lib/format'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, inputClass, labelClass } from './helpers'

interface Calendario {
  id_calendario: number | null
  anio: number
  fecha_aviso_ultimo_curso: string
  fecha_cierre_lectivo: string
  baja_ultimo_curso_aplicada: boolean
  configurado: boolean
}

const anioActual = new Date().getFullYear()

function porDefecto(anio: number): Calendario {
  return {
    id_calendario: null, anio, configurado: false, baja_ultimo_curso_aplicada: false,
    fecha_aviso_ultimo_curso: `${anio}-10-01`, fecha_cierre_lectivo: `${anio}-12-31`,
  }
}

export default function TabAnioLectivo() {
  const [items, setItems] = useState<Calendario[]>([])
  const [loading, setLoading] = useState(false)
  const [modal, setModal] = useState(false)
  const [editing, setEditing] = useState<Calendario | null>(null)
  const [form, setForm] = useState({ anio: anioActual, aviso: '', cierre: '' })
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/clientes/calendarios-lectivos/', { params: { page_size: 50 } })
      const filas: Calendario[] = (data.results ?? data ?? []).map((c: Calendario) => ({ ...c, configurado: true }))
      // El año en curso siempre aparece, aunque use los valores por defecto.
      if (!filas.some(f => f.anio === anioActual)) filas.push(porDefecto(anioActual))
      setItems(filas.sort((a, b) => b.anio - a.anio))
    } catch {
      toast.error('Error al cargar el calendario lectivo')
    } finally {
      setLoading(false)
    }
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load() }, [load])

  const abrir = useCallback((c?: Calendario) => {
    setEditing(c ?? null)
    setForm(c
      ? { anio: c.anio, aviso: c.fecha_aviso_ultimo_curso, cierre: c.fecha_cierre_lectivo }
      : { anio: anioActual + 1, aviso: `${anioActual + 1}-10-01`, cierre: `${anioActual + 1}-12-31` })
    setModal(true)
  }, [])

  const guardar = useCallback(async () => {
    if (!form.aviso || !form.cierre) { toast.error('Completá las dos fechas'); return }
    setSaving(true)
    try {
      const payload = {
        anio: form.anio, fecha_aviso_ultimo_curso: form.aviso, fecha_cierre_lectivo: form.cierre,
      }
      if (editing?.id_calendario) {
        await api.patch(`/clientes/calendarios-lectivos/${editing.id_calendario}/`, payload)
      } else {
        await api.post('/clientes/calendarios-lectivos/', payload)
      }
      toast.success('Calendario guardado')
      setModal(false)
      load()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }, [form, editing, load])

  const columns: Column<Calendario>[] = [
    { title: 'Año', key: 'anio', width: 80, render: (_, r) => <span className="font-semibold tabular-nums text-slate-800">{r.anio}</span> },
    { title: 'Aviso desde', key: 'aviso', render: (_, r) => <span className="text-sm text-slate-700">{formatDateOnly(r.fecha_aviso_ultimo_curso)}</span> },
    { title: 'Cierre del año lectivo', key: 'cierre', render: (_, r) => <span className="text-sm text-slate-700">{formatDateOnly(r.fecha_cierre_lectivo)}</span> },
    {
      title: 'Estado', key: 'estado',
      render: (_, r) => (
        <div className="flex gap-1.5 flex-wrap">
          {!r.configurado && <Badge color="default">Por defecto</Badge>}
          {r.baja_ultimo_curso_aplicada && <Badge color="purple">Baja del último curso aplicada</Badge>}
        </div>
      ),
    },
    {
      title: '', key: 'acc', width: 100,
      render: (_, r) => (
        <Button size="sm" variant="secondary" onClick={() => abrir(r)}>
          <Edit2 className="w-3.5 h-3.5" />
          {r.configurado ? 'Editar' : 'Configurar'}
        </Button>
      ),
    },
  ]

  return (
    <>
      <div className="bg-blue-50 border border-blue-100 rounded-2xl px-5 py-4 mb-4 text-sm text-slate-700 space-y-1.5">
        <p><strong>Cursos normales:</strong> la tarjeta no vence. Sigue de un año al otro mientras el alumno esté activo.</p>
        <p>
          <strong>Último curso:</strong> desde la fecha de <em>aviso</em> se avisa a padres, caja y administración los saldos y
          deudas. El alumno sigue operando hasta el <em>cierre</em>; después se lo da de baja y su saldo se resuelve en el cierre de cuentas.
        </p>
        <p className="text-slate-500">Si un año no está configurado se usa 01/10 (aviso) y 31/12 (cierre).</p>
      </div>

      <div className="flex justify-end mb-3">
        <Button variant="primary" onClick={() => abrir()}><Plus className="w-4 h-4" /> Configurar otro año</Button>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table columns={columns} dataSource={items} rowKey="anio" loading={loading} pageSize={20} />
        </div>
      </div>

      <Modal
        open={modal}
        title={editing?.configurado ? `Año lectivo ${form.anio}` : 'Configurar año lectivo'}
        onOk={guardar}
        onCancel={() => setModal(false)}
        okText="Guardar"
        confirmLoading={saving}
        width={420}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Año *</label>
            <input
              type="number" min={2020} max={2100}
              value={form.anio}
              disabled={!!editing}
              onChange={e => setForm(f => ({ ...f, anio: Number(e.target.value) }))}
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>Aviso del cierre de cuentas (último curso) *</label>
            <input type="date" value={form.aviso} onChange={e => setForm(f => ({ ...f, aviso: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Cierre del año lectivo (último día que opera) *</label>
            <input type="date" value={form.cierre} onChange={e => setForm(f => ({ ...f, cierre: e.target.value }))} className={inputClass} />
          </div>
        </div>
      </Modal>
    </>
  )
}
