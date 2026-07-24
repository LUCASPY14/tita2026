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

export default function ModalConfirmarEliminar({ consumoId, onClose, onSaved }: Props) {
  const [deleting, setDeleting] = useState(false)

  async function handleEliminar() {
    if (!consumoId) return
    setDeleting(true)
    try {
      await api.delete(`/almuerzos/registros-consumo/${consumoId}/`)
      toast.success('Registro eliminado')
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setDeleting(false)
    }
  }

  return (
    <Modal
      open={!!consumoId}
      title="Eliminar registro de consumo"
      onOk={handleEliminar}
      onCancel={onClose}
      okText="Eliminar definitivamente"
      confirmLoading={deleting}
      width={420}
    >
      <div className="space-y-3">
        <p className="text-sm text-slate-700">
          Esta acción <span className="font-semibold text-red-600">no se puede deshacer</span>.
          El registro será eliminado permanentemente de la base de datos.
        </p>
        <p className="text-xs text-slate-400">
          Solo se pueden eliminar registros en estado ANULADO. La cuenta mensual del alumno ya fue corregida al anular.
        </p>
      </div>
    </Modal>
  )
}
