import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, formatGs, type Compra } from './shared'

interface Props {
  open: boolean
  compra: Compra | null
  mediosPago: { id: number; descripcion: string }[]
  onClose: () => void
  onSaved: () => void
}

export default function ModalPago({ open, compra, mediosPago, onClose, onSaved }: Props) {
  const [monto, setMonto] = useState('')
  const [medioPago, setMedioPago] = useState(0)
  const [obs, setObs] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open && compra) {
      setMonto(String(Number(compra.saldo_pendiente) || ''))
      const efectivo = mediosPago.find(m => m.descripcion.toLowerCase().includes('efectivo'))
      setMedioPago(efectivo?.id ?? mediosPago[0]?.id ?? 0)
      setObs('')
    }
  }, [open, compra, mediosPago])

  async function handleSave() {
    const montoNum = Number(monto) || 0
    if (montoNum <= 0) { toast.error('Ingresá un monto válido'); return }
    setSaving(true)
    try {
      await api.post('/compras/pagos/', {
        compra: compra!.id,
        monto: montoNum,
        medio_pago: medioPago,
        observaciones: obs,
      })
      toast.success('Pago registrado')
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  return (
    <Modal
      open={open}
      title={`Registrar Pago — Compra #${compra?.id}`}
      onOk={handleSave}
      onCancel={onClose}
      okText="Registrar Pago"
      confirmLoading={saving}
      width={440}
    >
      <div className="space-y-4">
        <div className="bg-slate-50 rounded-xl px-4 py-3 flex justify-between items-center">
          <div>
            <p className="text-sm text-slate-500 font-medium uppercase tracking-wide">Proveedor</p>
            <p className="text-base font-semibold text-slate-800">{compra?.proveedor_nombre}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-slate-500 font-medium uppercase tracking-wide">Saldo Pendiente</p>
            <p className="text-lg font-bold tabular-nums text-red-600">{formatGs(compra?.saldo_pendiente)}</p>
          </div>
        </div>

        <div>
          <label className={labelClass}>Monto a Pagar *</label>
          <input
            type="number" value={monto} onChange={e => setMonto(e.target.value)}
            placeholder="Guaraníes" min={1} step={1000} className={inputClass} autoFocus
          />
        </div>

        <div>
          <label className={labelClass}>Medio de Pago</label>
          <select value={medioPago} onChange={e => setMedioPago(Number(e.target.value))} className={inputClass}>
            {mediosPago.map(mp => <option key={mp.id} value={mp.id}>{mp.descripcion}</option>)}
          </select>
        </div>

        <div>
          <label className={labelClass}>Observaciones</label>
          <textarea value={obs} onChange={e => setObs(e.target.value)} rows={2} placeholder="Opcional..." className={`${inputClass} resize-none`} />
        </div>
      </div>
    </Modal>
  )
}
