import { useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, type Proveedor } from './shared'

interface Props {
  open: boolean
  editingProv: Proveedor | null
  onClose: () => void
  onSaved: () => void
}

const BLANK = { ruc: '', razon_social: '', telefono: '', email: '', direccion: '', ciudad: '', activo: true }

export default function ModalProveedor({ open, editingProv, onClose, onSaved }: Props) {
  const [form, setForm] = useState(BLANK)
  const [saving, setSaving] = useState(false)

  const [wasOpen, setWasOpen] = useState(open)
  if (open !== wasOpen) {
    setWasOpen(open)
    if (open) {
      setForm(editingProv
        ? { ruc: editingProv.ruc, razon_social: editingProv.razon_social, telefono: editingProv.telefono ?? '', email: editingProv.email ?? '', direccion: editingProv.direccion ?? '', ciudad: editingProv.ciudad ?? '', activo: editingProv.activo }
        : BLANK
      )
    }
  }

  async function handleSave() {
    if (!form.ruc.trim()) { toast.error('El RUC es obligatorio'); return }
    if (!form.razon_social.trim()) { toast.error('La razón social es obligatoria'); return }
    setSaving(true)
    try {
      const payload = {
        ruc: form.ruc.trim(),
        razon_social: form.razon_social.trim(),
        telefono: form.telefono.trim() || null,
        email: form.email.trim() || null,
        direccion: form.direccion.trim() || null,
        ciudad: form.ciudad.trim() || null,
        activo: form.activo,
      }
      if (editingProv) {
        await api.patch(`/compras/proveedores/${editingProv.id_proveedor}/`, payload)
        toast.success('Proveedor actualizado')
      } else {
        await api.post('/compras/proveedores/', payload)
        toast.success('Proveedor registrado')
      }
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
  const f = (field: keyof typeof BLANK) => (e: React.ChangeEvent<HTMLInputElement>) => setForm(p => ({ ...p, [field]: e.target.value }))

  return (
    <Modal
      open={open}
      title={editingProv ? `Editar Proveedor — ${editingProv.razon_social}` : 'Nuevo Proveedor'}
      onOk={handleSave}
      onCancel={onClose}
      okText={editingProv ? 'Guardar Cambios' : 'Registrar'}
      confirmLoading={saving}
      width={560}
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>RUC *</label>
            <input className={inputClass} placeholder="80012345-6" value={form.ruc} onChange={f('ruc')} />
          </div>
          <div>
            <label className={labelClass}>Razón Social *</label>
            <input className={inputClass} placeholder="Empresa S.A." value={form.razon_social} onChange={f('razon_social')} />
          </div>
          <div>
            <label className={labelClass}>Teléfono</label>
            <input className={inputClass} placeholder="021-123456" value={form.telefono} onChange={f('telefono')} />
          </div>
          <div>
            <label className={labelClass}>Email</label>
            <input type="email" className={inputClass} placeholder="contacto@empresa.com" value={form.email} onChange={f('email')} />
          </div>
          <div>
            <label className={labelClass}>Dirección</label>
            <input className={inputClass} placeholder="Av. Principal 123" value={form.direccion} onChange={f('direccion')} />
          </div>
          <div>
            <label className={labelClass}>Ciudad</label>
            <input className={inputClass} placeholder="Asunción" value={form.ciudad} onChange={f('ciudad')} />
          </div>
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <button
            type="button"
            role="switch"
            aria-checked={form.activo}
            onClick={() => setForm(p => ({ ...p, activo: !p.activo }))}
            className={`relative w-9 h-5 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-green-500/30 ${form.activo ? 'bg-green-500' : 'bg-slate-200'}`}
          >
            <span className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow-sm transition-transform ${form.activo ? 'translate-x-4' : 'translate-x-0'}`} />
          </button>
          <span className="text-sm text-slate-700">Proveedor activo</span>
        </label>
      </div>
    </Modal>
  )
}
