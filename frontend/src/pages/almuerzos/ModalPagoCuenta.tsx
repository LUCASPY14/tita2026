import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, formatGs, MESES, type CuentaMensual } from './shared'

interface Props {
  cuenta: CuentaMensual | null
  onClose: () => void
  onSaved: () => void
}

export default function ModalPagoCuenta({ cuenta, onClose, onSaved }: Props) {
  const [form, setForm] = useState({ monto: '', medio_pago: 'EFECTIVO', referencia: '', emitirFactura: false, nroFactura: '' })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!cuenta) return
    const pendiente = Number(cuenta.saldo_pendiente) || (Number(cuenta.monto_total) - Number(cuenta.monto_pagado))
    setForm({ monto: String(pendiente > 0 ? pendiente : ''), medio_pago: 'EFECTIVO', referencia: '', emitirFactura: false, nroFactura: '' })
  }, [cuenta])

  async function handlePagar() {
    if (!cuenta) return
    if (!form.monto || Number(form.monto) <= 0) { toast.error('Ingresá el monto'); return }
    if (form.emitirFactura && !form.nroFactura.trim()) { toast.error('Ingresá el número de factura'); return }
    setSaving(true)
    try {
      await api.post('/almuerzos/pagos-cuentas/', {
        cuenta: cuenta.id,
        monto: Number(form.monto),
        medio_pago: form.medio_pago,
        referencia: form.referencia || undefined,
        ...(form.emitirFactura && form.nroFactura.trim() ? { nro_factura: form.nroFactura.trim() } : {}),
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
      open={!!cuenta}
      title="Registrar Pago de Cuenta"
      onOk={handlePagar}
      onCancel={onClose}
      okText="Registrar Pago"
      confirmLoading={saving}
      width={440}
    >
      {cuenta && (
        <div className="space-y-4">
          <div className="bg-slate-50 rounded-xl p-4">
            <p className="text-sm font-semibold text-slate-800">{cuenta.hijo_nombre}</p>
            <p className="text-xs text-slate-500 mt-1">{MESES[cuenta.mes]} {cuenta.anio} — {cuenta.cantidad_almuerzos} almuerzos</p>
            <div className="flex gap-6 mt-3">
              <div>
                <p className="text-sm text-slate-400">Total</p>
                <p className="text-sm font-bold text-slate-800">{formatGs(cuenta.monto_total)}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400">Pagado</p>
                <p className="text-sm font-bold text-emerald-700">{formatGs(cuenta.monto_pagado)}</p>
              </div>
              <div>
                <p className="text-sm text-slate-400">Saldo</p>
                <p className="text-sm font-bold text-red-600">{formatGs(cuenta.saldo_pendiente)}</p>
              </div>
            </div>
          </div>
          <div>
            <label className={labelClass}>Monto (Gs.) *</label>
            <input
              type="number" min={1} step={1000}
              value={form.monto}
              onChange={e => setForm(f => ({ ...f, monto: e.target.value }))}
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>Medio de Pago</label>
            <select value={form.medio_pago} onChange={e => setForm(f => ({ ...f, medio_pago: e.target.value }))} className={inputClass}>
              <option value="EFECTIVO">Efectivo</option>
              <option value="TRANSFERENCIA">Transferencia</option>
              <option value="TARJETA">Tarjeta</option>
              <option value="CHEQUE">Cheque</option>
            </select>
          </div>
          {form.medio_pago !== 'EFECTIVO' && (
            <div>
              <label className={labelClass}>Referencia</label>
              <input
                value={form.referencia}
                onChange={e => setForm(f => ({ ...f, referencia: e.target.value }))}
                placeholder="Nro. de transferencia, cheque, etc."
                className={inputClass}
              />
            </div>
          )}
          <div className="pt-1">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={form.emitirFactura}
                onChange={e => setForm(f => ({ ...f, emitirFactura: e.target.checked, nroFactura: '' }))}
                className="w-4 h-4 rounded accent-green-600"
              />
              <span className="text-sm font-semibold text-slate-700">Emitir factura ahora</span>
            </label>
            {form.emitirFactura && (
              <div className="mt-2">
                <label className={labelClass}>Nro. Factura *</label>
                <input
                  value={form.nroFactura}
                  onChange={e => setForm(f => ({ ...f, nroFactura: e.target.value }))}
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
