import { useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, formatGs, formatFecha, type RecargaPendiente } from './shared'

interface Props {
  recarga: RecargaPendiente | null
  onClose: () => void
  onSaved: () => void
}

export default function ModalConfirmarRecarga({ recarga, onClose, onSaved }: Props) {
  const [emitirFactura, setEmitirFactura] = useState(false)
  const [nroFactura, setNroFactura] = useState('')
  const [saving, setSaving] = useState(false)

  const [prevRecarga, setPrevRecarga] = useState(recarga)
  if (recarga !== prevRecarga) {
    setPrevRecarga(recarga)
    setEmitirFactura(false)
    setNroFactura('')
  }

  async function handleConfirmar() {
    if (!recarga) return
    if (emitirFactura && !nroFactura.trim()) { toast.error('Ingresá el número de factura'); return }
    setSaving(true)
    try {
      const { data } = await api.post(
        `/almuerzos/recargas-saldo/${recarga.id_recarga_almuerzo}/confirmar/`,
        emitirFactura ? { nro_factura: nroFactura.trim() } : {},
      )
      toast.success(`Recarga de ${formatGs(recarga.monto_cargado)} confirmada`)
      if (data.advertencia) toast(data.advertencia, { duration: 9000 })
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
      open={!!recarga}
      title="Confirmar Recarga de Almuerzo"
      onOk={handleConfirmar}
      onCancel={onClose}
      okText="Confirmar y acreditar"
      confirmLoading={saving}
      width={440}
    >
      {recarga && (
        <div className="space-y-4">
          <div className="bg-slate-50 rounded-xl p-4 space-y-1">
            <p className="text-sm font-semibold text-slate-800">{recarga.hijo_nombre}</p>
            <p className="text-2xl font-black tabular-nums text-slate-800">{formatGs(recarga.monto_cargado)}</p>
            <p className="text-xs text-slate-500">
              {recarga.metodo_pago} · registrada el {formatFecha(recarga.fecha_carga.slice(0, 10))}
              {recarga.registrado_por_nombre ? ` por ${recarga.registrado_por_nombre}` : ''}
            </p>
            {recarga.referencia && (
              <p className="text-xs text-slate-500">Referencia: <span className="font-mono">{recarga.referencia}</span></p>
            )}
          </div>
          <p className="text-xs text-slate-400">
            Verificá que el dinero ya ingresó (transferencia, depósito) antes de confirmar. Al confirmar se
            acredita al saldo de almuerzo del alumno y se avisa al responsable por WhatsApp.
          </p>
          <div>
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={emitirFactura}
                onChange={e => { setEmitirFactura(e.target.checked); setNroFactura('') }}
                className="w-4 h-4 rounded accent-green-600"
              />
              <span className="text-sm font-semibold text-slate-700">Emitir factura ahora</span>
            </label>
            {emitirFactura && (
              <div className="mt-2">
                <label className={labelClass}>Nro. Factura *</label>
                <input
                  value={nroFactura}
                  onChange={e => setNroFactura(e.target.value)}
                  placeholder="001-001-0001234"
                  className={inputClass}
                  autoFocus
                />
              </div>
            )}
          </div>
        </div>
      )}
    </Modal>
  )
}
