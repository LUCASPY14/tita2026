import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import Badge from '../../components/ui/Badge'
import { extractErrorMessage, formatGs, type PendienteItem, TIPO_COLOR, TIPO_LABEL } from './shared'

interface Props {
  item: PendienteItem | null
  onClose: () => void
  onSaved: () => void
}

const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

export default function ModalEmitir({ item, onClose, onSaved }: Props) {
  const [nroFactura, setNroFactura] = useState('')
  const [emitiendo, setEmitiendo] = useState(false)

  useEffect(() => { if (item) setNroFactura('') }, [item])

  const handleEmitir = async () => {
    if (!item) return
    if (!nroFactura.trim()) { toast.error('Ingresá el número de factura'); return }
    setEmitiendo(true)
    try {
      await api.post('/contabilidad/facturas/emitir/', {
        tipo: item.tipo,
        origen_id: item.id,
        nro_factura: nroFactura.trim(),
      })
      toast.success(`Factura ${nroFactura} emitida`)
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setEmitiendo(false)
    }
  }

  return (
    <Modal
      open={!!item}
      title="Emitir Factura"
      onOk={handleEmitir}
      onCancel={onClose}
      confirmLoading={emitiendo}
      okText="Emitir"
      width={460}
    >
      {item && (
        <div className="space-y-4">
          <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500 font-medium">Cliente</span>
              <span className="text-slate-800 font-semibold">{item.cliente_nombre}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-medium">Concepto</span>
              <span className="text-slate-700">{item.descripcion}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-medium">Monto</span>
              <span className="text-emerald-700 font-bold tabular-nums">{formatGs(item.monto)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-medium">Tipo</span>
              <Badge color={TIPO_COLOR[item.tipo] ?? 'default'}>{TIPO_LABEL[item.tipo] ?? item.tipo}</Badge>
            </div>
          </div>

          <div>
            <label className={labelClass}>Número de Factura *</label>
            <input
              value={nroFactura}
              onChange={e => setNroFactura(e.target.value)}
              placeholder="001-001-0000001"
              className={inputClass}
              autoFocus
            />
            <p className="text-sm text-slate-400 mt-1">Formato: 001-001-0000001</p>
          </div>
        </div>
      )}
    </Modal>
  )
}
