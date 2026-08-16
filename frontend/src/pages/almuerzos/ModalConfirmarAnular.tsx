import { useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage } from './shared'

interface Props {
  consumoId: number | null
  onClose: () => void
  onSaved: () => void
}

export default function ModalConfirmarAnular({ consumoId, onClose, onSaved }: Props) {
  const [anulando, setAnulando] = useState(false)

  async function handleAnular() {
    if (!consumoId) return
    setAnulando(true)
    try {
      await api.post(`/almuerzos/registros-consumo/${consumoId}/anular/`)
      toast.success('Consumo anulado')
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setAnulando(false)
    }
  }

  return (
    <Modal
      open={!!consumoId}
      title="Anular registro de consumo"
      onOk={handleAnular}
      onCancel={onClose}
      okText="Sí, anular"
      confirmLoading={anulando}
      width={420}
    >
      <div className="space-y-3">
        <p className="text-sm text-slate-700">
          ¿Confirmás anular este registro de consumo? Si el almuerzo ya estaba cobrado, se
          revierte el cargo de la cuenta mensual del alumno.
        </p>
        <p className="text-xs text-slate-400">
          El registro queda en estado ANULADO — solo un administrador puede eliminarlo
          definitivamente después.
        </p>
      </div>
    </Modal>
  )
}
