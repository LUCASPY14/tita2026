import { useState } from 'react'
import toast from 'react-hot-toast'
import { Banknote, Printer } from 'lucide-react'
import { METODOS_PAGO as METODOS } from '../../constants/mediosPago'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, formatGs, abrirReciboCC, type Cliente, type PagoCC } from './shared'

interface Props {
  open: boolean
  cliente: Cliente | null
  onClose: () => void
  onSaved: () => void
}

export default function ModalPagarCC({ open, cliente, onClose, onSaved }: Props) {
  const saldoActual = Number(cliente?.saldo_cuenta_corriente ?? 0)
  const deudaCantina = Number(cliente?.saldo_cc_cantina ?? 0)
  const deudaAlmuerzo = Number(cliente?.saldo_cc_almuerzo ?? 0)
  const requiereElegirOrigen = deudaCantina > 0 && deudaAlmuerzo > 0

  const [monto, setMonto] = useState('')
  const [origen, setOrigen] = useState<'CANTINA' | 'ALMUERZO' | ''>('')
  const [metodo, setMetodo] = useState('EFECTIVO')
  const [referencia, setReferencia] = useState('')
  const [nroFactura, setNroFactura] = useState('')
  const [saving, setSaving] = useState(false)
  const [ultimoPago, setUltimoPago] = useState<PagoCC | null>(null)

  const [wasOpen, setWasOpen] = useState(open)
  if (open !== wasOpen) {
    setWasOpen(open)
    if (open) {
      setMonto(saldoActual > 0 ? String(saldoActual) : '')
      setOrigen(deudaCantina > 0 && deudaAlmuerzo <= 0 ? 'CANTINA' : deudaAlmuerzo > 0 && deudaCantina <= 0 ? 'ALMUERZO' : '')
      setMetodo('EFECTIVO')
      setReferencia('')
      setNroFactura('')
      setUltimoPago(null)
    }
  }

  const metodoInfo = METODOS.find(m => m.value === metodo)
  const deudaOrigenSeleccionado = origen === 'CANTINA' ? deudaCantina : origen === 'ALMUERZO' ? deudaAlmuerzo : saldoActual

  async function handlePagar() {
    const montoNum = Number(monto)
    if (!montoNum || montoNum <= 0) { toast.error('Ingresá un monto válido'); return }
    if (requiereElegirOrigen && !origen) { toast.error('Elegí a qué deuda corresponde el pago'); return }
    if (metodoInfo?.requiere_referencia && !referencia.trim()) {
      toast.error('Ingresá el código de transacción'); return
    }
    setSaving(true)
    try {
      const desc = `Pago CC — ${metodo}${referencia ? ` (${referencia})` : ''}`
      const { data } = await api.post('/clientes/cuentas-corrientes/', {
        cliente: cliente!.id,
        monto: montoNum,
        descripcion: desc,
        medio_pago: metodo,
        genera_factura_legal: true,
        ...(origen ? { origen } : {}),
        ...(nroFactura.trim() ? { nro_factura: nroFactura.trim() } : {}),
      })
      setUltimoPago(data)
      toast.success(`Pago de ${montoNum.toLocaleString('es-PY')} Gs. registrado`)
      onSaved()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const inputClass = 'w-full border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors'

  return (
    <Modal
      open={open}
      title={`Cobrar Cuenta Corriente — ${cliente?.apellidos ?? ''}, ${cliente?.nombres ?? ''}`}
      onCancel={onClose}
      footer={null}
      width={480}
    >
      <div className="space-y-5">
        <div className={`rounded-xl px-4 py-3 border ${saldoActual > 0 ? 'bg-orange-50 border-orange-200' : 'bg-emerald-50 border-emerald-200'}`}>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-0.5">Deuda actual</p>
          <p className={`text-3xl font-black tabular-nums ${saldoActual > 0 ? 'text-orange-700' : 'text-emerald-700'}`}>
            {formatGs(saldoActual)}
          </p>
          {saldoActual === 0 && <p className="text-xs text-emerald-600 mt-0.5">Sin deuda pendiente</p>}
          {requiereElegirOrigen && (
            <p className="text-xs text-orange-600 mt-1">
              Cantina: {formatGs(deudaCantina)} · Almuerzo: {formatGs(deudaAlmuerzo)}
            </p>
          )}
        </div>

        {!ultimoPago ? (
          <>
            {requiereElegirOrigen && (
              <div>
                <label className="block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">¿A qué deuda corresponde? *</label>
                <div className="grid grid-cols-2 gap-2">
                  {(['CANTINA', 'ALMUERZO'] as const).map(op => (
                    <button key={op} type="button" onClick={() => setOrigen(op)}
                      className={`px-3 py-2.5 rounded-xl text-sm font-bold transition-colors cursor-pointer border-2 ${origen === op ? 'bg-orange-600 text-white border-orange-600' : 'bg-white text-slate-700 border-slate-200 hover:border-orange-400'}`}>
                      {op === 'CANTINA' ? 'Cantina' : 'Almuerzo'}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Monto a cobrar (Gs.) *</label>
              <input
                type="number" min={1} step={1000} value={monto}
                onChange={e => setMonto(e.target.value)} placeholder="0"
                className="w-full text-center text-3xl font-black tracking-wider py-4 border-2 rounded-2xl outline-none bg-white border-slate-200 focus:border-green-500 focus:ring-4 focus:ring-green-500/10 text-slate-900 placeholder:text-slate-300 transition-all"
              />
              {deudaOrigenSeleccionado > 0 && Number(monto) < deudaOrigenSeleccionado && (
                <p className="text-xs text-slate-400 mt-1 text-center">Pago parcial — quedará saldo pendiente</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">Método de pago</label>
              <div className="grid grid-cols-2 gap-2">
                {METODOS.map(m => (
                  <button key={m.value} type="button" onClick={() => { setMetodo(m.value); setReferencia('') }}
                    className={`px-3 py-2.5 rounded-xl text-sm font-bold text-left transition-colors cursor-pointer border-2 ${metodo === m.value ? 'bg-green-600 text-white border-green-600' : 'bg-white text-slate-700 border-slate-200 hover:border-green-400'}`}>
                    {m.label}
                  </button>
                ))}
              </div>
            </div>

            {metodoInfo?.requiere_referencia && (
              <div>
                <label className="block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Código de transacción *</label>
                <input value={referencia} onChange={e => setReferencia(e.target.value)}
                  placeholder={metodo === 'TRANSFERENCIA' ? 'Nro. de transferencia...' : 'Nro. de comprobante POS...'}
                  className={inputClass} />
              </div>
            )}

            <div>
              <label className="block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Nro. factura (opcional)</label>
              <input value={nroFactura} onChange={e => setNroFactura(e.target.value)}
                placeholder="001-001-0000001" className={inputClass} />
              <p className="text-xs text-slate-400 mt-1">
                {nroFactura.trim() ? 'Factura emitida al registrar el pago' : 'Sin número → queda pendiente en Facturación'}
              </p>
            </div>

            <div className="flex gap-3 pt-1">
              <button onClick={onClose}
                className="flex-1 py-3 border border-slate-200 rounded-xl text-slate-600 font-semibold text-sm hover:bg-slate-50 transition-colors cursor-pointer">
                Cancelar
              </button>
              <button onClick={handlePagar} disabled={saving}
                className="flex-1 py-3 bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white font-black text-base rounded-xl flex items-center justify-center gap-2 transition-colors cursor-pointer">
                <Banknote className="w-5 h-5" />
                {saving ? 'Registrando...' : 'Registrar pago'}
              </button>
            </div>
          </>
        ) : (
          <div className="space-y-4">
            <div className="bg-emerald-50 border-2 border-emerald-300 rounded-2xl p-5 text-center">
              <p className="text-emerald-700 font-bold text-lg mb-1">Pago registrado</p>
              <p className="text-4xl font-black tabular-nums text-slate-800">{formatGs(ultimoPago.monto)}</p>
              <p className="text-sm text-slate-500 mt-1">
                {METODOS.find(m => m.value === metodo)?.label}
                {ultimoPago.origen !== 'GENERAL' && ` — ${ultimoPago.origen === 'CANTINA' ? 'Cantina' : 'Almuerzo'}`}
              </p>
              <div className="mt-3 pt-3 border-t border-emerald-200 text-sm text-slate-600">
                <div className="flex justify-between">
                  <span>Saldo anterior:</span>
                  <span className="tabular-nums font-semibold">{formatGs(ultimoPago.saldo_anterior)}</span>
                </div>
                <div className="flex justify-between mt-1">
                  <span>Saldo restante:</span>
                  <span className={`tabular-nums font-semibold ${Number(ultimoPago.saldo_resultante) > 0 ? 'text-orange-600' : 'text-emerald-700'}`}>
                    {formatGs(ultimoPago.saldo_resultante)}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex gap-3">
              <button onClick={() => cliente && abrirReciboCC(cliente, ultimoPago, metodo)}
                className="flex-1 flex items-center justify-center gap-2 py-3 border border-slate-200 hover:border-slate-400 text-slate-700 font-semibold text-sm rounded-xl transition-colors cursor-pointer">
                <Printer className="w-4 h-4" />Imprimir recibo
              </button>
              <button onClick={onClose}
                className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 text-white font-semibold text-sm rounded-xl transition-colors cursor-pointer">
                Cerrar
              </button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  )
}
