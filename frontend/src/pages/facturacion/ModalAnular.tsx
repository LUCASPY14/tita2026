import { useState } from 'react'
import toast from 'react-hot-toast'
import { AlertTriangle } from 'lucide-react'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, type Factura } from './shared'

interface Props {
  factura: Factura | null
  onClose: () => void
  onSaved: () => void
}

export default function ModalAnular({ factura, onClose, onSaved }: Props) {
  const [anulando, setAnulando] = useState(false)

  const handleAnular = async () => {
    if (!factura) return
    setAnulando(true)
    try {
      await api.post(`/contabilidad/facturas/${factura.id}/anular/`)
      toast.success('Factura anulada')
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
      open={!!factura}
      title="Anular Factura"
      onOk={handleAnular}
      onCancel={onClose}
      confirmLoading={anulando}
      okText="Anular"
      width={400}
    >
      {factura && (
        <div className="flex items-start gap-3 py-2">
          <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-slate-800">
              ¿Anular factura {factura.nro_factura}?
            </p>
            <p className="text-sm text-slate-500 mt-1">
              Esta acción no se puede deshacer. La factura quedará marcada como ANULADA.
            </p>
          </div>
        </div>
      )}
    </Modal>
  )
}
