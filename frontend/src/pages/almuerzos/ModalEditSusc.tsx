import { useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, type Suscripcion } from './shared'

interface Props {
  susc: Suscripcion | null
  onClose: () => void
  onSaved: () => void
}

export default function ModalEditSusc({ susc, onClose, onSaved }: Props) {
  const [form, setForm] = useState({ fecha_fin: '' })
  const [saving, setSaving] = useState(false)

  const [prevSusc, setPrevSusc] = useState(susc)
  if (susc !== prevSusc) {
    setPrevSusc(susc)
    if (susc) setForm({ fecha_fin: susc.fecha_fin ?? '' })
  }

  async function handleSave() {
    if (!susc) return
    setSaving(true)
    try {
      await api.patch(`/almuerzos/suscripciones/${susc.id_suscripcion}/`, {
        fecha_fin: form.fecha_fin || null,
      })
      toast.success('Suscripción actualizada')
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
      title="Editar Suscripción"
      onOk={handleSave}
      onCancel={onClose}
      okText="Guardar"
      confirmLoading={saving}
      width={440}
    >
      <div className="space-y-4">
        <div>
          <label className={labelClass}>Fecha de Fin (opcional)</label>
          <input
            type="date"
            value={form.fecha_fin}
            onChange={e => setForm(f => ({ ...f, fecha_fin: e.target.value }))}
            className={inputClass}
          />
        </div>
      </div>
    </Modal>
  )
}
