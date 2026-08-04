import { useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, formatGs, type PendienteItem } from './shared'

interface Props {
  open: boolean
  items: PendienteItem[]
  onClose: () => void
  onSuccess: () => void
}

export default function LoteModal({ open, items, onClose, onSuccess }: Props) {
  const [nro, setNro] = useState('')
  const [saving, setSaving] = useState(false)

  const [wasOpen, setWasOpen] = useState(open)
  if (open !== wasOpen) {
    setWasOpen(open)
    if (open) setNro('')
  }

  const clienteNombre = items[0]?.cliente_nombre ?? ''
  const total = items.reduce((s, i) => s + i.monto, 0)

  const confirmar = async () => {
    if (!nro.trim()) { toast.error('Ingresá el número de factura'); return }
    if (items.length === 0) return
    setSaving(true)
    try {
      await api.post('/contabilidad/facturas/emitir-lote/', {
        tipo: items[0].tipo,
        ids: items.map(i => i.id),
        nro_factura: nro.trim(),
      })
      toast.success(`Factura ${nro} emitida por ${formatGs(total)}`)
      onSuccess()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      title="Emitir Factura Mensual"
      onOk={confirmar}
      onCancel={onClose}
      confirmLoading={saving}
      okText="Emitir Factura"
      width={500}
    >
      <div className="space-y-4">
        <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-500 font-medium">Cliente</span>
            <span className="text-slate-800 font-semibold">{clienteNombre}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500 font-medium">Ítems seleccionados</span>
            <span className="text-slate-700 font-semibold">{items.length}</span>
          </div>
          <div className="flex justify-between border-t border-blue-100 pt-2">
            <span className="text-slate-500 font-medium">Total a facturar</span>
            <span className="text-emerald-700 font-bold tabular-nums text-base">{formatGs(total)}</span>
          </div>
        </div>

        {items.length > 0 && (
          <div className="max-h-40 overflow-y-auto space-y-1">
            {items.map(item => (
              <div key={`${item.tipo}-${item.id}`} className="flex justify-between text-sm px-1 py-1 rounded hover:bg-slate-50">
                <span className="text-slate-600 truncate max-w-[280px]">{item.descripcion}</span>
                <span className="text-slate-800 font-semibold tabular-nums shrink-0 ml-2">{formatGs(item.monto)}</span>
              </div>
            ))}
          </div>
        )}

        <div>
          <label className="block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
            Número de Factura *
          </label>
          <input
            value={nro}
            onChange={e => setNro(e.target.value)}
            placeholder="001-001-0000001"
            className="w-full border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150"
            autoFocus
          />
          <p className="text-sm text-slate-400 mt-1">Formato: 001-001-0000001</p>
        </div>
      </div>
    </Modal>
  )
}
