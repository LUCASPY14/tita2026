import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Lock, ShieldCheck } from 'lucide-react'
import api from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'

export default function PortalCambiarContrasena() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [passwordActual, setPasswordActual] = useState('')
  const [passwordNuevo, setPasswordNuevo] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (passwordNuevo.length < 6) {
      toast.error('La contraseña nueva debe tener al menos 6 caracteres')
      return
    }
    if (passwordNuevo !== passwordConfirm) {
      toast.error('Las contraseñas nuevas no coinciden')
      return
    }
    setLoading(true)
    try {
      await api.post('/usuarios/usuarios/cambiar-password/', {
        password_actual: passwordActual,
        password_nuevo: passwordNuevo,
      })
      // Actualizar el flag en el store localmente
      useAuthStore.setState(state => ({
        user: state.user ? { ...state.user, debe_cambiar_contrasena: false } : null,
      }))
      toast.success('Contraseña actualizada. ¡Bienvenido!')
      navigate('/portal', { replace: true })
    } catch (err) {
      const e = err as { response?: { data?: { detail?: string; password_actual?: string[] } } }
      const msg =
        e?.response?.data?.password_actual?.[0] ||
        e?.response?.data?.detail ||
        'Error al cambiar la contraseña'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-green-50 to-green-100">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
            <ShieldCheck className="w-8 h-8 text-green-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-800">Cambiar contraseña</h1>
          <p className="text-gray-500 mt-2 text-sm">
            Hola, <span className="font-medium">{user?.nombre}</span>. Por seguridad,
            debés elegir una contraseña personal antes de continuar.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Contraseña actual (tu CI/RUC)"
            type="password"
            placeholder="Ingresá tu CI o RUC"
            value={passwordActual}
            onChange={e => setPasswordActual(e.target.value)}
            autoComplete="current-password"
            required
          />
          <Input
            label="Nueva contraseña"
            type="password"
            placeholder="Mínimo 6 caracteres"
            value={passwordNuevo}
            onChange={e => setPasswordNuevo(e.target.value)}
            autoComplete="new-password"
            required
          />
          <Input
            label="Confirmar nueva contraseña"
            type="password"
            placeholder="Repetí la contraseña"
            value={passwordConfirm}
            onChange={e => setPasswordConfirm(e.target.value)}
            autoComplete="new-password"
            required
          />

          <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 text-xs text-amber-700 flex gap-2">
            <Lock className="w-4 h-4 shrink-0 mt-0.5" />
            <span>Tu contraseña debe tener al menos 6 caracteres y ser diferente a tu CI/RUC.</span>
          </div>

          <Button variant="primary" block size="lg" loading={loading} type="submit">
            Guardar contraseña
          </Button>
        </form>

        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={() => { logout(); navigate('/portal/login', { replace: true }) }}
            className="text-sm text-gray-400 hover:text-gray-600 cursor-pointer"
          >
            Cerrar sesión
          </button>
        </div>
      </div>
    </div>
  )
}
