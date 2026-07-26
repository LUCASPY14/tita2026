import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, formatFecha, type AlertaVencimiento } from './shared'

interface Props {
  alerta: AlertaVencimiento | null
  onClose: () => void
  onSaved: () => void
}

const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

export default function ModalAccionVencimiento({ alerta, onClose, onSaved }: Props) {
  const [accion, setAccion] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (alerta) setAccion(alerta.accion_tomada ?? '')
  }, [alerta])

  const handleSave = async () => {
    if (!alerta || !accion) { toast.error('Seleccioná una acción'); return }
    setSaving(true)
    try {
      await api.post(`/inventario/alertas-vencimiento/${alerta.id}/registrar-accion/`, {
        accion_tomada: accion,
      })
      toast.success('Acción registrada correctamente')
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
      open={!!alerta}
      title="Registrar Acción sobre Lote"
      onOk={handleSave}
      onCancel={onClose}
      okText="Guardar"
      confirmLoading={saving}
      width={440}
    >
      {alerta && (
        <div className="space-y-4 py-1">
          <div className="bg-slate-50 rounded-xl px-4 py-3 text-sm text-slate-700 space-y-1">
            <p><span className="font-semibold">Producto:</span> {alerta.producto_nombre}</p>
            <p><span className="font-semibold">Lote:</span> {alerta.lote_numero}</p>
            <p><span className="font-semibold">Vencimiento:</span> {formatFecha(alerta.fecha_vencimiento)}</p>
            <p><span className="font-semibold">Cantidad:</span> {Number(alerta.cantidad_lote)}</p>
          </div>
          <div>
            <label className={labelClass}>Acción tomada *</label>
            <select value={accion} onChange={e => setAccion(e.target.value)} className={inputClass}>
              <option value="">Seleccioná una acción...</option>
              <option value="DESCUENTO">Descuento aplicado</option>
              <option value="DEVUELTO">Devuelto a proveedor</option>
              <option value="DONADO">Donado</option>
              <option value="DESCARTADO">Descartado</option>
              <option value="VENDIDO">Vendido a tiempo</option>
            </select>
          </div>
        </div>
      )}
    </Modal>
  )
}
