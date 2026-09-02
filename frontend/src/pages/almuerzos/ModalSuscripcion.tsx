import { useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, todayISO, type Hijo, type PlanAlmuerzo } from './shared'

interface Props {
  open: boolean
  hijos: Hijo[]
  planes: PlanAlmuerzo[]
  onClose: () => void
  onSaved: () => void
}

export default function ModalSuscripcion({ open, hijos, planes, onClose, onSaved }: Props) {
  const [form, setForm] = useState({ hijo: '', planId: '', fecha_inicio: todayISO() })
  const [saving, setSaving] = useState(false)

  const activos = planes.filter(p => p.activo)
  const predeterminado = activos.find(p => p.es_predeterminado) ?? activos[0]
  const planId = form.planId || (predeterminado ? String(predeterminado.id) : '')
  const plan = activos.find(p => String(p.id) === planId)

  async function handleSave() {
    if (!form.hijo || !plan) { toast.error('Completá todos los campos'); return }
    setSaving(true)
    try {
      await api.post('/almuerzos/suscripciones/', {
        hijo: Number(form.hijo),
        plan: plan.id,
        fecha_inicio: form.fecha_inicio,
      })
      toast.success('Suscripción creada')
      setForm({ hijo: '', planId: '', fecha_inicio: todayISO() })
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  return (
    <Modal
      open={open}
      title="Nueva Suscripción"
      onOk={handleSave}
      onCancel={onClose}
      okText="Suscribir"
      confirmLoading={saving}
      width={440}
    >
      <div className="space-y-4">
        <div>
          <label htmlFor="susc-estudiante" className={labelClass}>Estudiante *</label>
          <select
            id="susc-estudiante"
            value={form.hijo}
            onChange={e => setForm(f => ({ ...f, hijo: e.target.value }))}
            className={inputClass}
          >
            <option value="">Seleccionar...</option>
            {hijos.map(h => (
              <option key={h.id} value={h.id}>
                {h.nombre_completo ?? `${h.nombre} ${h.apellido}`} — {h.grado}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="susc-plan" className={labelClass}>Plan *</label>
          <select
            id="susc-plan"
            value={planId}
            onChange={e => setForm(f => ({ ...f, planId: e.target.value }))}
            className={inputClass}
          >
            <option value="">Seleccionar...</option>
            {activos.map(p => (
              <option key={p.id} value={p.id}>{p.nombre}{p.es_predeterminado ? ' (predeterminado)' : ''}</option>
            ))}
          </select>
        </div>
        {plan && (
          <div className="bg-green-50 rounded-xl px-3 py-2.5">
            <p className="text-xs text-green-700">
              Cada almuerzo registrado en el comedor descuenta el costo del saldo de almuerzo del alumno.
            </p>
          </div>
        )}
        <div>
          <label className={labelClass}>Fecha de Inicio</label>
          <input
            type="date"
            value={form.fecha_inicio}
            onChange={e => setForm(f => ({ ...f, fecha_inicio: e.target.value }))}
            className={inputClass}
          />
        </div>
      </div>
    </Modal>
  )
}
