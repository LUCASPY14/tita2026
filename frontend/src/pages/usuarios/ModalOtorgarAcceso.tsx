import { useState } from 'react'
import toast from 'react-hot-toast'
import { Eye, EyeOff } from 'lucide-react'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import {
  extractErrorMessage, type Empleado, type OtorgarAccesoForm,
  OTORGAR_ACCESO_INITIAL, ROLES_PERSONAL,
} from './shared'

interface Props {
  open: boolean
  empleado: Empleado | null
  onClose: () => void
  onSaved: () => void
}

const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

export default function ModalOtorgarAcceso({ open, empleado, onClose, onSaved }: Props) {
  const [form, setForm] = useState<OtorgarAccesoForm>(OTORGAR_ACCESO_INITIAL)
  const [showPassword, setShowPassword] = useState(false)
  const [saving, setSaving] = useState(false)

  const [wasOpen, setWasOpen] = useState(open)
  if (open !== wasOpen) {
    setWasOpen(open)
    if (open) {
      setForm({ ...OTORGAR_ACCESO_INITIAL, email: empleado?.email ?? '' })
      setShowPassword(false)
    }
  }

  const handleSave = async () => {
    if (!empleado) return
    if (!form.email) { toast.error('Completá el email'); return }
    if (!form.ci_ruc.trim()) { toast.error('El CI/RUC es obligatorio: es lo que usa para iniciar sesión'); return }
    if (form.password.length < 6) { toast.error('La contraseña debe tener mínimo 6 caracteres'); return }
    setSaving(true)
    try {
      await api.post('/usuarios/usuarios/', {
        empleado: empleado.id_empleado,
        email: form.email,
        ci_ruc: form.ci_ruc.trim(),
        rol: form.rol,
        password: form.password,
        is_active: form.is_active,
      })
      toast.success(`Acceso creado para ${empleado.nombre} ${empleado.apellido}`)
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
      open={open}
      title={empleado ? `Otorgar acceso — ${empleado.nombre} ${empleado.apellido}` : 'Otorgar acceso'}
      onOk={handleSave}
      onCancel={onClose}
      okText="Crear acceso"
      confirmLoading={saving}
      width={460}
    >
      <div className="space-y-4">
        <div className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-600">
          Nombre y apellido se toman del empleado — no hace falta repetirlos acá.
        </div>

        <div>
          <label className={labelClass}>Email *</label>
          <input
            type="email"
            value={form.email}
            onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
            placeholder="usuario@cantina.com"
            className={inputClass}
          />
        </div>

        <div>
          <label className={labelClass}>CI/RUC *</label>
          <input
            value={form.ci_ruc}
            onChange={e => setForm(f => ({ ...f, ci_ruc: e.target.value }))}
            placeholder="Ej: 2447330"
            className={inputClass}
          />
        </div>

        <div>
          <label className={labelClass}>Rol</label>
          <select value={form.rol} onChange={e => setForm(f => ({ ...f, rol: e.target.value }))} className={inputClass}>
            {ROLES_PERSONAL.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
          </select>
        </div>

        <div>
          <label className={labelClass}>Contraseña *</label>
          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              placeholder="Mínimo 6 caracteres"
              className={`${inputClass} pr-10`}
            />
            <button
              type="button"
              onClick={() => setShowPassword(s => !s)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        <label className="flex items-center gap-3 cursor-pointer">
          <div className="relative shrink-0">
            <input type="checkbox" className="sr-only peer" checked={form.is_active} onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))} />
            <div className="w-9 h-5 bg-slate-200 rounded-full peer-checked:bg-green-500 transition-colors" />
            <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
          </div>
          <span className="text-sm text-slate-700">Acceso activo</span>
        </label>
      </div>
    </Modal>
  )
}
