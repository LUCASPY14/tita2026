import { useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, type PlanAlmuerzo, type Suscripcion } from './shared'

interface Props {
  susc: Suscripcion | null
  planes: PlanAlmuerzo[]
  onClose: () => void
  onSaved: () => void
}

export default function ModalPagoMensual({ susc, planes, onClose, onSaved }: Props) {
  const [form, setForm] = useState({ monto: '', mes_pagado: '' })
  const [saving, setSaving] = useState(false)

  const [prevSusc, setPrevSusc] = useState(susc)
  if (susc !== prevSusc) {
    setPrevSusc(susc)
    if (susc) {
      const plan = planes.find(p => p.id === susc.plan)
      const primerDiaMes = new Date()
      primerDiaMes.setDate(1)
      setForm({
        monto: plan ? String(plan.precio_mensual) : '',
        mes_pagado: primerDiaMes.toISOString().split('T')[0],
      })
    }
  }

  async function handlePago() {
    if (!susc) return
    if (!form.monto || Number(form.monto) <= 0) { toast.error('Ingresá el monto'); return }
    if (!form.mes_pagado) { toast.error('Seleccioná el mes'); return }
    setSaving(true)
    try {
      const [y, m] = form.mes_pagado.split('-')
      const mesPagado = `${y}-${m}-01`
      await api.post('/almuerzos/pagos-mensuales/', {
        suscripcion: susc.id,
        monto_pagado: Number(form.monto),
        mes_pagado: mesPagado,
      })
      toast.success('Cuota mensual registrada')
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
      open={!!susc}
      title="Registrar Cuota Mensual"
      onOk={handlePago}
      onCancel={onClose}
      okText="Registrar Cuota"
      confirmLoading={saving}
      width={440}
    >
      {susc && (
        <div className="space-y-4">
          <div className="bg-slate-50 rounded-xl p-4">
            <p className="text-sm font-semibold text-slate-800">{susc.hijo_nombre}</p>
            <p className="text-xs text-slate-500 mt-1">
              {planes.find(p => p.id === susc.plan)?.nombre ?? 'Plan'} — Cuota fija mensual
            </p>
          </div>
          <div>
            <label className={labelClass}>Mes *</label>
            <input
              type="month"
              value={form.mes_pagado.slice(0, 7)}
              onChange={e => setForm(f => ({ ...f, mes_pagado: `${e.target.value}-01` }))}
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>Monto (Gs.) *</label>
            <input
              type="number" min={1} step={1000}
              value={form.monto}
              onChange={e => setForm(f => ({ ...f, monto: e.target.value }))}
              className={inputClass}
            />
          </div>
        </div>
      )}
    </Modal>
  )
}
