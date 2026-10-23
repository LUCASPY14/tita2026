import { useState } from 'react'
import toast from 'react-hot-toast'
import { AlertTriangle } from 'lucide-react'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import Button from '../../components/ui/Button'
import { extractErrorMessage, formatGs, type RecargaAlmuerzoReciente } from './shared'

interface Props {
  recarga: RecargaAlmuerzoReciente | null
  onClose: () => void
  onSaved: () => void
}

export default function ModalAnularRecargaAlmuerzo({ recarga, onClose, onSaved }: Props) {
  const [anulando, setAnulando] = useState(false)

  const handleAnular = async () => {
    if (!recarga) return
    setAnulando(true)
    try {
      await api.post(`/almuerzos/recargas-saldo/${recarga.id_recarga_almuerzo}/anular/`)
      toast.success(`Recarga #${recarga.id_recarga_almuerzo} anulada`)
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
      open={recarga !== null}
      title="Anular Recarga de Almuerzo"
      onCancel={() => !anulando && onClose()}
      footer={null}
      width={400}
    >
      {recarga && (
        <div className="space-y-4">
          <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
            <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
            <div className="text-sm text-red-800 space-y-1">
              <p className="font-semibold">Esta acción es irreversible</p>
              <p>Se descontará el monto del saldo de almuerzo.</p>
            </div>
          </div>
          <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-1 text-sm">
            <p className="text-slate-500">Recarga <span className="font-semibold text-slate-800">#{recarga.id_recarga_almuerzo}</span></p>
            <p className="text-slate-500">Monto: <span className="font-semibold text-slate-800">{formatGs(recarga.monto_cargado)}</span></p>
          </div>
          <div className="flex gap-3 justify-end pt-1">
            <Button variant="secondary" onClick={onClose} disabled={anulando}>
              Cancelar
            </Button>
            <Button variant="danger" loading={anulando} onClick={handleAnular}>
              Confirmar anulación
            </Button>
          </div>
        </div>
      )}
    </Modal>
  )
}
