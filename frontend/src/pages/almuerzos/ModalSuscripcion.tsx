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
  const [form, setForm] = useState({ hijo: '', fecha_inicio: todayISO() })
  const [saving, setSaving] = useState(false)

  const plan = planes.find(p => p.activo)

  async function handleSave() {
    if (!form.hijo || !plan) { toast.error('Completá todos los campos'); return }
    setSaving(true)
    try {
      await api.post('/almuerzos/suscripciones/', {
        hijo: Number(form.hijo),
        plan: plan.id,
        tipo_cobro: 'CUENTA',
        fecha_inicio: form.fecha_inicio,
      })
      toast.success('Suscripción creada')
      setForm({ hijo: '', fecha_inicio: todayISO() })
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
        <div className="bg-green-50 rounded-xl px-3 py-2.5">
          <p className="text-sm font-medium text-green-800">
            {plan ? plan.nombre : 'No hay un plan de almuerzo activo'}
          </p>
          <p className="text-xs text-green-700 mt-0.5">
            Por consumo: la cuenta acumula el costo de cada almuerzo registrado en el comedor
            y el cajero cobra el total al mes siguiente.
          </p>
        </div>
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
