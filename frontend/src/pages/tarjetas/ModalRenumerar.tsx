import { useState } from 'react'
import toast from 'react-hot-toast'
import tarjetasService from '../../services/tarjetas'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, MOTIVOS_RENUMERACION, type Tarjeta } from './shared'

interface Props {
  tarjeta: Tarjeta | null
  onClose: () => void
  onSaved: () => void
}

const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

export default function ModalRenumerar({ tarjeta, onClose, onSaved }: Props) {
  const [nroNuevo, setNroNuevo] = useState('')
  const [motivo, setMotivo] = useState('')
  const [motivoDetalle, setMotivoDetalle] = useState('')
  const [saving, setSaving] = useState(false)

  const [prevTarjeta, setPrevTarjeta] = useState(tarjeta)
  if (tarjeta !== prevTarjeta) {
    setPrevTarjeta(tarjeta)
    setNroNuevo('')
    setMotivo('')
    setMotivoDetalle('')
  }

  if (!tarjeta) return null

  const handleSave = async () => {
    if (!nroNuevo.trim()) { toast.error('Ingresá el número nuevo'); return }
    if (!motivo) { toast.error('Seleccioná un motivo'); return }
    if (motivo === 'OTRO' && !motivoDetalle.trim()) { toast.error('Aclará el motivo en el detalle'); return }

    setSaving(true)
    try {
      await tarjetasService.renumerar(tarjeta.nro_tarjeta, nroNuevo.trim(), motivo, motivoDetalle.trim())
      toast.success('Tarjeta renumerada')
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={!!tarjeta}
      title={`Renumerar tarjeta — ${tarjeta.nro_tarjeta}`}
      onOk={handleSave}
      onCancel={onClose}
      okText="Renumerar"
      confirmLoading={saving}
      width={480}
    >
      <div className="space-y-4">
        <div className="bg-slate-50 rounded-xl px-4 py-3 text-sm text-slate-500">
          {tarjeta.es_alumno ? 'Estudiante' : 'Docente / Funcionario'}:{' '}
          <span className="font-semibold text-slate-800">{tarjeta.hijo_nombre ?? '—'}</span>
        </div>

        <p className="text-xs text-slate-400">
          El saldo y todo el historial (movimientos, cargas, ventas, pagos, almuerzos) se conservan
          intactos bajo el número nuevo.
        </p>

        <div>
          <label className={labelClass}>Número actual</label>
          <input value={tarjeta.nro_tarjeta} disabled className={`${inputClass} bg-slate-50 text-slate-400`} />
        </div>

        <div>
          <label className={labelClass}>Número nuevo</label>
          <input
            value={nroNuevo}
            onChange={e => setNroNuevo(e.target.value)}
            placeholder="Nro. de la tarjeta física"
            className={inputClass}
          />
        </div>

        <div>
          <label className={labelClass}>Motivo</label>
          <select value={motivo} onChange={e => setMotivo(e.target.value)} className={inputClass}>
            <option value="">Seleccioná un motivo…</option>
            {MOTIVOS_RENUMERACION.map(m => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>
        </div>

        {motivo === 'OTRO' && (
          <div>
            <label className={labelClass}>Detalle (obligatorio)</label>
            <textarea
              value={motivoDetalle}
              onChange={e => setMotivoDetalle(e.target.value)}
              placeholder="Describí el motivo"
              rows={3}
              className={inputClass}
            />
          </div>
        )}
      </div>
    </Modal>
  )
}
