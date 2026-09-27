import { useState } from 'react'
import toast from 'react-hot-toast'
import tarjetasService from '../../services/tarjetas'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, formatGs, type Tarjeta } from './shared'

interface Props {
  tarjeta: Tarjeta | null
  onClose: () => void
  onSaved: (updates: Partial<Tarjeta>) => void
}

type TipoSaldo = 'CANTINA' | 'ALMUERZO'

const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

export default function ModalAjustarSaldo({ tarjeta, onClose, onSaved }: Props) {
  const [tipo, setTipo] = useState<TipoSaldo>('CANTINA')
  const [monto, setMonto] = useState('')
  const [motivo, setMotivo] = useState('')
  const [saving, setSaving] = useState(false)

  const [prevTarjeta, setPrevTarjeta] = useState(tarjeta)
  if (tarjeta !== prevTarjeta) {
    setPrevTarjeta(tarjeta)
    setTipo('CANTINA')
    setMonto('')
    setMotivo('')
  }

  if (!tarjeta) return null

  const saldoActual = tipo === 'CANTINA'
    ? Number(tarjeta.saldo_actual) || 0
    : Number(tarjeta.saldo_almuerzo) || 0
  const montoNum = Number(monto.replace(',', '.')) || 0
  const saldoResultante = saldoActual + montoNum

  const handleSave = async () => {
    if (!montoNum) { toast.error('Ingresá un monto distinto de cero'); return }
    if (!motivo.trim()) { toast.error('El motivo es obligatorio'); return }

    setSaving(true)
    try {
      if (tipo === 'CANTINA') {
        const { data } = await tarjetasService.ajustarSaldo(tarjeta.nro_tarjeta, montoNum, motivo.trim())
        onSaved({ saldo_actual: data.saldo_actual })
      } else {
        const { data } = await api.post<{ saldo_actual: number }>('/almuerzos/saldos/ajustar/', {
          hijo_id: tarjeta.hijo, monto: montoNum, motivo: motivo.trim(),
        })
        onSaved({ saldo_almuerzo: data.saldo_actual })
      }
      toast.success('Saldo ajustado')
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
      title={`Ajustar saldo — ${tarjeta.nro_tarjeta}`}
      onOk={handleSave}
      onCancel={onClose}
      okText="Aplicar ajuste"
      confirmLoading={saving}
      width={480}
    >
      <div className="space-y-4">
        <div className="bg-slate-50 rounded-xl px-4 py-3 text-sm text-slate-500">
          {tarjeta.es_alumno ? 'Estudiante' : 'Docente / Funcionario'}:{' '}
          <span className="font-semibold text-slate-800">{tarjeta.hijo_nombre ?? '—'}</span>
        </div>

        <div>
          <label className={labelClass}>Saldo a ajustar</label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setTipo('CANTINA')}
              className={`py-2 rounded-xl border-2 text-sm font-semibold transition-colors cursor-pointer ${
                tipo === 'CANTINA' ? 'bg-slate-800 text-white border-slate-800' : 'bg-white text-slate-600 border-slate-200'
              }`}
            >
              Saldo de cantina
            </button>
            <button
              type="button"
              onClick={() => tarjeta.es_alumno && setTipo('ALMUERZO')}
              disabled={!tarjeta.es_alumno}
              title={tarjeta.es_alumno ? undefined : 'Solo disponible para tarjetas de alumnos'}
              className={`py-2 rounded-xl border-2 text-sm font-semibold transition-colors ${
                !tarjeta.es_alumno ? 'bg-slate-50 text-slate-300 border-slate-100 cursor-not-allowed' :
                tipo === 'ALMUERZO' ? 'bg-slate-800 text-white border-slate-800 cursor-pointer' : 'bg-white text-slate-600 border-slate-200 cursor-pointer'
              }`}
            >
              Saldo de almuerzo
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between bg-slate-50 rounded-xl px-4 py-3">
          <span className="text-sm text-slate-500">Saldo actual</span>
          <span className="text-base font-semibold text-slate-800 tabular-nums">{formatGs(saldoActual)}</span>
        </div>

        <div>
          <label className={labelClass}>Monto del ajuste</label>
          <p className="text-xs text-slate-400 mb-1.5">Positivo suma, negativo resta. Ej: -5000 o 5000.</p>
          <input
            type="number"
            value={monto}
            onChange={e => setMonto(e.target.value)}
            placeholder="0"
            step={1000}
            className={inputClass}
          />
        </div>

        {montoNum !== 0 && (
          <div className="flex items-center justify-between bg-blue-50 border border-blue-200 rounded-xl px-4 py-3">
            <span className="text-sm text-blue-700">Saldo resultante</span>
            <span className="text-base font-bold text-blue-800 tabular-nums">{formatGs(saldoResultante)}</span>
          </div>
        )}

        <div>
          <label className={labelClass}>Motivo (obligatorio)</label>
          <textarea
            value={motivo}
            onChange={e => setMotivo(e.target.value)}
            placeholder="Ej: corrección por reclamo del padre, cobro duplicado, etc."
            rows={3}
            className={inputClass}
          />
        </div>
      </div>
    </Modal>
  )
}
