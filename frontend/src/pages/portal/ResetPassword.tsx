import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'

export default function PortalResetPassword() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const uid = searchParams.get('uid') ?? ''
  const token = searchParams.get('token') ?? ''

  const [password, setPassword] = useState('')
  const [confirmar, setConfirmar] = useState('')
  const [errors, setErrors] = useState<{ password?: string; confirmar?: string }>({})
  const [loading, setLoading] = useState(false)
  const [exito, setExito] = useState(false)

  const validate = (): boolean => {
    const e: { password?: string; confirmar?: string } = {}
    if (password.length < 6) e.password = 'Debe tener al menos 6 caracteres'
    if (!confirmar) e.confirmar = 'Confirmá tu contraseña'
    else if (password !== confirmar) e.confirmar = 'Las contraseñas no coinciden'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async (e: { preventDefault(): void }) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    try {
      await api.post('/usuarios/recuperar-password/confirmar/', {
        uid,
        token,
        password_nuevo: password,
      })
      setExito(true)
      toast.success('Contraseña restablecida correctamente')
    } catch {
      toast.error('El enlace es inválido o ya fue usado')
      navigate('/portal/login', { replace: true })
    } finally {
      setLoading(false)
    }
  }

  if (!uid || !token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-green-50 to-green-100">
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md text-center">
          <p className="text-4xl mb-4">⚠️</p>
          <p className="text-gray-700 font-semibold">Enlace inválido</p>
          <p className="text-gray-500 text-sm mt-2">
            El enlace de recuperación no es válido. Solicitá uno nuevo desde el login.
          </p>
          <button
            type="button"
            onClick={() => navigate('/portal/login', { replace: true })}
            className="mt-4 text-sm text-green-600 hover:underline cursor-pointer"
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
          <Button variant="primary" block onClick={() => navigate('/portal/login', { replace: true })}>
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
          <img src="/logo_tita.png" alt="Cantina Tita" className="h-28 w-auto mx-auto mb-3 drop-shadow-sm" />
          <h1 className="text-2xl font-bold text-green-800">Nueva contraseña</h1>
          <p className="text-gray-500 mt-2 text-sm">Ingresá tu nueva contraseña</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Nueva contraseña"
            type="password"
            placeholder="Mínimo 6 caracteres"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value)
              if (errors.password) setErrors(prev => ({ ...prev, password: undefined }))
            }}
            error={errors.password}
            autoComplete="new-password"
            required
          />
          <Input
            label="Confirmar contraseña"
            type="password"
            placeholder="Repetí la contraseña"
            value={confirmar}
            onChange={(e) => {
              setConfirmar(e.target.value)
              if (errors.confirmar) setErrors(prev => ({ ...prev, confirmar: undefined }))
            }}
            error={errors.confirmar}
            autoComplete="new-password"
            required
          />
          <Button variant="primary" block size="lg" loading={loading} type="submit">
            Restablecer contraseña
          </Button>
        </form>
        <p className="text-center text-sm text-gray-400 mt-6">
          <button
            type="button"
            onClick={() => navigate('/portal/login', { replace: true })}
            className="text-green-600 hover:underline cursor-pointer"
          >
            Volver al login
          </button>
        </p>
      </div>
    </div>
  )
}
