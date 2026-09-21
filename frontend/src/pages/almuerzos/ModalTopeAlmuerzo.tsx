import { useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, type SaldoAlmuerzoItem } from './shared'

interface Props {
  saldo: SaldoAlmuerzoItem | null
  onClose: () => void
  onSaved: () => void
}

export default function ModalTopeAlmuerzo({ saldo, onClose, onSaved }: Props) {
  const [limite, setLimite] = useState(String(Number(saldo?.limite_credito) || 0))
  const [saving, setSaving] = useState(false)

  const [prevSaldo, setPrevSaldo] = useState(saldo)
  if (saldo !== prevSaldo) {
    setPrevSaldo(saldo)
    if (saldo) setLimite(String(Number(saldo.limite_credito) || 0))
  }

  async function handleSave() {
    if (!saldo) return
    setSaving(true)
    try {
      await api.patch(`/almuerzos/saldos/${saldo.id_saldo_almuerzo}/`, {
        limite_credito: Number(limite) || 0,
      })
      toast.success('Tope actualizado')
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
      open={!!saldo}
      title="Tope de deuda de almuerzo"
      onOk={handleSave}
      onCancel={onClose}
      okText="Guardar"
      confirmLoading={saving}
      width={440}
    >
      {saldo && (
        <div className="space-y-4">
          <div className="bg-slate-50 rounded-xl px-4 py-3 text-sm text-slate-500">
            Estudiante: <span className="font-semibold text-slate-800">{saldo.hijo_nombre}</span>
          </div>
          <div>
            <label className={labelClass}>Tope de deuda (Gs.)</label>
            <p className="text-xs text-slate-400 mb-1.5">
              El comedor nunca deja de registrar un almuerzo por deuda — al superar este tope solo se avisa a
              administración. 0 = sin tope.
            </p>
            <input
              type="number"
              value={limite}
              onChange={e => setLimite(e.target.value)}
              placeholder="0"
              min={0}
              step={1000}
              className={inputClass}
            />
          </div>
        </div>
      )}
    </Modal>
  )
}
