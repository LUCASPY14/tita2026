import { useRef, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, formatGs, type CierreCaja } from './shared'

interface Props {
  cierre: CierreCaja | null
  onClose: () => void
  onSaved: () => void
}

export default function ModalConciliar({ cierre, onClose, onSaved }: Props) {
  const [obsConc, setObsConc] = useState('')
  const [conciliando, setConciliando] = useState(false)
  const conciliandoRef = useRef(false)

  const handleConciliar = async () => {
    if (conciliandoRef.current || !cierre) return
    conciliandoRef.current = true
    setConciliando(true)
    try {
      await api.post(`/contabilidad/cierres-caja/${cierre.id}/conciliar/`, {
        observaciones: obsConc,
      }, { timeout: 10000 })
      toast.success('Cierre conciliado')
      onSaved()
      onClose()
      setObsConc('')
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      conciliandoRef.current = false
      setConciliando(false)
    }
  }

  return (
    <Modal
      open={!!cierre}
      title={`Conciliar Cierre — ${cierre?.caja_nombre ?? ''}`}
      onCancel={() => { onClose(); setObsConc('') }}
      onOk={handleConciliar}
      okText="Conciliar"
      confirmLoading={conciliando}
      width={440}
    >
      <div className="space-y-4">
        {cierre && (
          <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-1.5 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Monto contado:</span>
              <span className="font-semibold tabular-nums text-slate-800">
                {formatGs(cierre.monto_contado_fisico)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Diferencia:</span>
              <span className={['font-semibold tabular-nums', Number(cierre.diferencia_efectivo) === 0 ? 'text-emerald-700' : 'text-red-600'].join(' ')}>
                {formatGs(cierre.diferencia_efectivo)}
              </span>
            </div>
          </div>
        )}
        <div>
          <label className="block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
            Observaciones del Contador
          </label>
          <textarea
            value={obsConc}
            onChange={e => setObsConc(e.target.value)}
            rows={3}
            placeholder="Notas de conciliación (opcional)..."
            className="w-full border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors resize-none"
          />
        </div>
      </div>
    </Modal>
  )
}
