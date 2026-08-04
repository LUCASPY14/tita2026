import { useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, formatGs, type OrdenCompra } from './shared'

interface Props {
  oc: OrdenCompra | null
  onClose: () => void
  onSaved: () => void
}

export default function ModalRechazarOC({ oc, onClose, onSaved }: Props) {
  const [motivo, setMotivo] = useState('')
  const [saving, setSaving] = useState(false)

  const [prevOc, setPrevOc] = useState(oc)
  if (oc !== prevOc) {
    setPrevOc(oc)
    if (oc) setMotivo('')
  }

  async function handleRechazar() {
    const m = motivo.trim()
    if (!m) { toast.error('Ingresá el motivo del rechazo'); return }
    setSaving(true)
    try {
      await api.post(`/compras/ordenes/${oc!.id}/rechazar/`, { motivo: m })
      toast.success('OC rechazada')
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
      open={!!oc}
      title={`Rechazar OC #${oc?.id}`}
      onOk={handleRechazar}
      onCancel={onClose}
      okText="Confirmar Rechazo"
      confirmLoading={saving}
      width={440}
    >
      <div className="space-y-3">
        <p className="text-sm text-slate-600">
          Vas a rechazar la OC de <strong>{oc?.proveedor_nombre}</strong> por{' '}
          <strong>{formatGs(oc?.monto_total)}</strong>.
        </p>
        <div>
          <label className={labelClass}>Motivo del rechazo *</label>
          <textarea
            value={motivo}
            onChange={e => setMotivo(e.target.value)}
            rows={3}
            placeholder="Explicá el motivo del rechazo..."
            className={`${inputClass} resize-none`}
            autoFocus
          />
        </div>
      </div>
    </Modal>
  )
}
