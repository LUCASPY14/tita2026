import { useState } from 'react'
import toast from 'react-hot-toast'
import tarjetasService from '../../services/tarjetas'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage } from './shared'

interface Props {
  cargaId: number | null
  onClose: () => void
  onSaved: () => void
}

const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

export default function ModalConfirmarCarga({ cargaId, onClose, onSaved }: Props) {
  const [confirmFactura, setConfirmFactura] = useState({ emitir: false, nro: '' })
  const [confirmando, setConfirmando] = useState(false)

  const handleConfirmar = async () => {
    if (!cargaId) return
    if (confirmFactura.emitir && !confirmFactura.nro.trim()) {
      toast.error('Ingresá el número de factura')
      return
    }
    setConfirmando(true)
    try {
      await tarjetasService.confirmarCarga(
        cargaId,
        confirmFactura.emitir ? confirmFactura.nro.trim() : undefined,
      )
      toast.success('Carga confirmada')
      setConfirmFactura({ emitir: false, nro: '' })
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setConfirmando(false)
    }
  }

  return (
    <Modal
      open={cargaId !== null}
      title="Confirmar Carga de Saldo"
      onOk={handleConfirmar}
      onCancel={() => { onClose(); setConfirmFactura({ emitir: false, nro: '' }) }}
      okText="Confirmar"
      confirmLoading={confirmando}
      width={400}
    >
      <div className="space-y-4">
        <p className="text-sm text-slate-600">¿Confirmás esta carga de saldo?</p>
        <div className="pt-1">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={confirmFactura.emitir}
              onChange={e => setConfirmFactura(f => ({ ...f, emitir: e.target.checked, nro: '' }))}
              className="w-4 h-4 rounded accent-green-600"
            />
            <span className="text-sm font-semibold text-slate-700">Emitir factura ahora</span>
          </label>
          {confirmFactura.emitir && (
            <div className="mt-2">
              <label className={labelClass}>Nro. Factura *</label>
              <input
                value={confirmFactura.nro}
                onChange={e => setConfirmFactura(f => ({ ...f, nro: e.target.value }))}
                placeholder="001-001-0001234"
                className={inputClass}
                autoFocus
              />
            </div>
          )}
        </div>
      </div>
    </Modal>
  )
}
