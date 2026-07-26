import { useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, todayISO } from './shared'

interface Props {
  open: boolean
  onClose: () => void
  onSaved: () => void
}

export default function ModalMenu({ open, onClose, onSaved }: Props) {
  const [form, setForm] = useState({ fecha: todayISO(), plato_principal: '', guarnicion: '', postre: '', bebida: '', descripcion: '' })
  const [saving, setSaving] = useState(false)

  async function handleSave() {
    if (!form.fecha || !form.plato_principal) { toast.error('Ingresá la fecha y el plato principal'); return }
    setSaving(true)
    try {
      await api.post('/almuerzos/menu/', {
        fecha: form.fecha,
        plato_principal: form.plato_principal,
        guarnicion: form.guarnicion,
        postre: form.postre,
        bebida: form.bebida,
        descripcion: form.descripcion,
      })
      toast.success('Menú registrado')
      setForm({ fecha: todayISO(), plato_principal: '', guarnicion: '', postre: '', bebida: '', descripcion: '' })
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
      title="Agregar al Menú"
      onOk={handleSave}
      onCancel={onClose}
      okText="Guardar"
      confirmLoading={saving}
      width={560}
    >
      <div className="space-y-4">
        <div>
          <label className={labelClass}>Fecha *</label>
          <input type="date" value={form.fecha} onChange={e => setForm(f => ({ ...f, fecha: e.target.value }))} className={inputClass} />
        </div>
        <div>
          <label className={labelClass}>Plato principal *</label>
          <input
            value={form.plato_principal}
            onChange={e => setForm(f => ({ ...f, plato_principal: e.target.value }))}
            placeholder="Ej: Milanesa con papas"
            className={inputClass}
          />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className={labelClass}>Guarnición</label>
            <input value={form.guarnicion} onChange={e => setForm(f => ({ ...f, guarnicion: e.target.value }))} placeholder="Ej: Ensalada" className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Postre</label>
            <input value={form.postre} onChange={e => setForm(f => ({ ...f, postre: e.target.value }))} placeholder="Ej: Fruta" className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Bebida</label>
            <input value={form.bebida} onChange={e => setForm(f => ({ ...f, bebida: e.target.value }))} placeholder="Ej: Jugo" className={inputClass} />
          </div>
        </div>
        <div>
          <label className={labelClass}>Notas</label>
          <textarea
            value={form.descripcion}
            onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))}
            rows={2}
            placeholder="Información adicional..."
            className={`${inputClass} resize-none`}
          />
        </div>
      </div>
    </Modal>
  )
}
