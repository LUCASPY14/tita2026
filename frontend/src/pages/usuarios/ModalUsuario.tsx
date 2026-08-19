import { useState } from 'react'
import toast from 'react-hot-toast'
import { Eye, EyeOff } from 'lucide-react'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, type Usuario, type UsuarioForm, FORM_INITIAL, ROLES_SISTEMA } from './shared'

interface Props {
  open: boolean
  editingUser: Usuario | null
  onClose: () => void
  onSaved: () => void
}

const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

export default function ModalUsuario({ open, editingUser, onClose, onSaved }: Props) {
  const [form, setForm] = useState<UsuarioForm>(FORM_INITIAL)
  const [showPassword, setShowPassword] = useState(false)
  const [saving, setSaving] = useState(false)

  // Reinicia el formulario cada vez que el modal se abre (patrón "adjusting
  // state during render" de React: https://react.dev/learn/you-might-not-need-an-effect).
  const [wasOpen, setWasOpen] = useState(open)
  if (open !== wasOpen) {
    setWasOpen(open)
    if (open) {
      setForm(editingUser
        ? {
            email: editingUser.email,
            ci_ruc: editingUser.ci_ruc ?? '',
            nombre: editingUser.nombre,
            apellido: editingUser.apellido,
            rol: editingUser.rol,
            password: '',
            is_active: editingUser.is_active,
          }
        : FORM_INITIAL)
      setShowPassword(false)
    }
  }

  const handleSave = async () => {
    if (!form.email || !form.nombre) { toast.error('Completá email y nombre'); return }
    if (form.rol !== 'CLIENTE_WEB' && !form.ci_ruc.trim()) {
      toast.error('El CI/RUC es obligatorio: es lo que se usa para iniciar sesión en Administración, POS y Cobranzas')
      return
    }
    if (!editingUser && form.password.length < 6) { toast.error('La contraseña debe tener mínimo 6 caracteres'); return }
    if (editingUser && form.password && form.password.length < 6) { toast.error('La nueva contraseña debe tener mínimo 6 caracteres'); return }
    setSaving(true)
    try {
      const payload: Record<string, unknown> = {
        email: form.email,
        ci_ruc: form.ci_ruc.trim() || null,
        nombre: form.nombre,
        apellido: form.apellido,
        rol: form.rol,
        is_active: form.is_active,
      }
      if (form.password) payload.password = form.password

      if (editingUser) {
        await api.patch(`/usuarios/usuarios/${editingUser.id}/`, payload)
        toast.success('Usuario actualizado')
      } else {
        await api.post('/usuarios/usuarios/', payload)
        toast.success('Usuario creado')
      }
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
      title={editingUser ? 'Editar Usuario' : 'Nuevo Usuario'}
      onOk={handleSave}
      onCancel={onClose}
      okText={editingUser ? 'Guardar' : 'Crear'}
      confirmLoading={saving}
      width={500}
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input
              value={form.nombre}
              onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))}
              placeholder="Juan"
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>Apellido</label>
            <input
              value={form.apellido}
              onChange={e => setForm(f => ({ ...f, apellido: e.target.value }))}
              placeholder="García"
              className={inputClass}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
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
            <label className={labelClass}>
              CI/RUC {form.rol !== 'CLIENTE_WEB' && '*'}
            </label>
            <input
              value={form.ci_ruc}
              onChange={e => setForm(f => ({ ...f, ci_ruc: e.target.value }))}
              placeholder="Ej: 2447330"
              className={inputClass}
            />
          </div>
        </div>

        <div>
          <label className={labelClass}>Rol</label>
          <select value={form.rol} onChange={e => setForm(f => ({ ...f, rol: e.target.value }))} className={inputClass}>
            {ROLES_SISTEMA.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
          </select>
        </div>

        <div>
          <label className={labelClass}>
            {editingUser ? 'Nueva Contraseña (dejar vacío para no cambiar)' : 'Contraseña *'}
          </label>
          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              placeholder={editingUser ? 'Nueva contraseña...' : 'Mínimo 6 caracteres'}
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
          <span className="text-sm text-slate-700">Usuario activo</span>
        </label>
      </div>
    </Modal>
  )
}
