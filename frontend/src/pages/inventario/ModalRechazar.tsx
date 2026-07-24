import { useState } from 'react'
import toast from 'react-hot-toast'
import { XCircle } from 'lucide-react'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage } from './shared'

interface Props {
  ajusteId: number | null
  onClose: () => void
  onSaved: () => void
}

export default function ModalRechazar({ ajusteId, onClose, onSaved }: Props) {
  const [saving, setSaving] = useState(false)

  const handleRechazar = async () => {
    if (!ajusteId) return
    setSaving(true)
    try {
      await api.post(`/inventario/ajustes/${ajusteId}/rechazar/`)
      toast.success('Ajuste rechazado')
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
      title="Rechazar Ajuste"
      onOk={handleRechazar}
      onCancel={onClose}
      okText="Rechazar"
      confirmLoading={saving}
      width={380}
    >
      <div className="flex items-start gap-3 py-2">
        <XCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
        <p className="text-sm text-slate-700">
          ¿Rechazar el ajuste <span className="font-semibold">#{ajusteId}</span>? No se realizará ningún cambio en el stock.
        </p>
      </div>
    </Modal>
  )
}
