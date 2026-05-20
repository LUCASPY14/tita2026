import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'

export default function PortalResetPassword() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const uid = searchParams.get('uid') || ''
  const token = searchParams.get('token') || ''

  const [password, setPassword] = useState('')
  const [confirmar, setConfirmar] = useState('')
  const [loading, setLoading] = useState(false)
  const [exito, setExito] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (password.length < 6) {
      toast.error('La contraseña debe tener al menos 6 caracteres')
      return
    }
    if (password !== confirmar) {
      toast.error('Las contraseñas no coinciden')
      return
    }
    setLoading(true)
    try {
      await api.post('/usuarios/recuperar-password/confirmar/', {
        uid,
        token,
        password_nuevo: password,
      })
      setExito(true)
      toast.success('Contraseña restablecida correctamente')
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } }
      toast.error(err?.response?.data?.error || 'Enlace inválido o expirado')
    } finally {
      setLoading(false)
    }
  }

  if (!uid || !token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-green-50 to-green-100">
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md text-center">
          <p className="text-4xl mb-4">⚠</p>
          <p className="text-gray-700 font-semibold">Enlace inválido</p>
          <p className="text-gray-500 text-sm mt-2">
            El enlace de recuperación no es válido. Solicitá uno nuevo desde el login.
          </p>
          <button
            onClick={() => navigate('/portal/login')}
            className="mt-4 text-sm text-green-600 hover:underline"
          >
            Volver al login
          </button>
        </div>
      </div>
    )
  }

  if (exito) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-green-50 to-green-100">
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md text-center">
          <p className="text-5xl mb-4">✅</p>
          <h2 className="text-xl font-bold text-gray-800 mb-2">Contraseña restablecida</h2>
          <p className="text-gray-500 text-sm mb-6">Ya podés iniciar sesión con tu nueva contraseña.</p>
          <Button variant="primary" block onClick={() => navigate('/portal/login')}>
            Ir al login
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-green-50 to-green-100">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <img src="/logo_tita.png" alt="Cantina Tita" className="h-16 w-auto mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-green-800">Nueva contraseña</h1>
          <p className="text-gray-500 mt-2 text-sm">Ingresá tu nueva contraseña</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Nueva contraseña"
            type="password"
            placeholder="Mínimo 6 caracteres"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <Input
            label="Confirmar contraseña"
            type="password"
            placeholder="Repetí la contraseña"
            value={confirmar}
            onChange={(e) => setConfirmar(e.target.value)}
            required
          />
          <Button variant="primary" block size="lg" loading={loading} type="submit">
            Restablecer contraseña
          </Button>
        </form>
        <p className="text-center text-sm text-gray-400 mt-6">
          <button
            onClick={() => navigate('/portal/login')}
            className="text-green-600 hover:underline"
          >
            Volver al login
          </button>
        </p>
      </div>
    </div>
  )
}
