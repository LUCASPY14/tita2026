import { useState } from 'react'
import toast from 'react-hot-toast'
import { CheckCircle } from 'lucide-react'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage } from './shared'

interface Props {
  ajusteId: number | null
  onClose: () => void
  onSaved: () => void
}

export default function ModalAprobar({ ajusteId, onClose, onSaved }: Props) {
  const [saving, setSaving] = useState(false)

  const handleAprobar = async () => {
    if (!ajusteId) return
    setSaving(true)
    try {
      await api.post(`/inventario/ajustes/${ajusteId}/aprobar/`)
      toast.success('Ajuste aprobado')
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={!!ajusteId}
      title="Aprobar Ajuste"
      onOk={handleAprobar}
      onCancel={onClose}
      okText="Aprobar"
      confirmLoading={saving}
      width={380}
    >
      <div className="flex items-start gap-3 py-2">
        <CheckCircle className="w-5 h-5 text-green-500 shrink-0 mt-0.5" />
        <p className="text-sm text-slate-700">
          ¿Aprobar el ajuste <span className="font-semibold">#{ajusteId}</span>? Esto modificará el stock de los productos.
        </p>
      </div>
    </Modal>
  )
}
