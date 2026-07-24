import { useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, formatGs, todayISO, type Hijo, type PlanAlmuerzo } from './shared'

interface Props {
  open: boolean
  hijos: Hijo[]
  planes: PlanAlmuerzo[]
  onClose: () => void
  onSaved: () => void
}

export default function ModalSuscripcion({ open, hijos, planes, onClose, onSaved }: Props) {
  const [form, setForm] = useState({ hijo: '', plan: '', tipo_cobro: 'CUENTA', fecha_inicio: todayISO() })
  const [saving, setSaving] = useState(false)

  async function handleSave() {
    if (!form.hijo || !form.plan) { toast.error('Completá todos los campos'); return }
    setSaving(true)
    try {
      await api.post('/almuerzos/suscripciones/', {
        hijo: Number(form.hijo),
        plan: Number(form.plan),
        tipo_cobro: form.tipo_cobro,
        fecha_inicio: form.fecha_inicio,
      })
      toast.success('Suscripción creada')
      setForm({ hijo: '', plan: '', tipo_cobro: 'CUENTA', fecha_inicio: todayISO() })
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
            value={form.plan}
            onChange={e => {
              const planId = e.target.value
              const plan = planes.find(p => String(p.id) === planId)
              const tipoCobro = plan?.tipo === 'CANTIDAD' ? 'MENSUAL' : 'CUENTA'
              setForm(f => ({ ...f, plan: planId, tipo_cobro: tipoCobro }))
            }}
            className={inputClass}
          >
            <option value="">Seleccionar...</option>
            {planes.filter(p => p.activo).map(p => (
              <option key={p.id} value={p.id}>{p.nombre} — {formatGs(p.precio_mensual)}/mes</option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelClass}>Tipo de Cobro *</label>
          <select
            value={form.tipo_cobro}
            onChange={e => setForm(f => ({ ...f, tipo_cobro: e.target.value }))}
            className={inputClass}
          >
            <option value="CUENTA">Por consumo — padre paga al final del mes según lo que comió</option>
            <option value="MENSUAL">Cuota mensual fija — padre paga por adelantado</option>
          </select>
          {form.plan && (
            <p className="text-xs text-slate-400 mt-1">
              {form.tipo_cobro === 'MENSUAL'
                ? `El padre paga ${formatGs(planes.find(p => String(p.id) === form.plan)?.precio_mensual ?? 0)} al inicio de cada mes.`
                : 'La cuenta acumula Gs. por cada almuerzo registrado y el cajero cobra al mes siguiente.'}
            </p>
          )}
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
