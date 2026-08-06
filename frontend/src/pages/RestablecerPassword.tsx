import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Eye, EyeOff, CheckCircle } from 'lucide-react'
import api from '../services/api'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import AuthShell from '../components/AuthShell'

export default function RestablecerPassword() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const uid = searchParams.get('uid') ?? ''
  const token = searchParams.get('token') ?? ''

  const [password, setPassword] = useState('')
  const [confirmar, setConfirmar] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<{ password?: string; confirmar?: string }>({})
  const [completado, setCompletado] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined)

  useEffect(() => () => { clearTimeout(timerRef.current) }, [])

  const validate = (): boolean => {
    const e: { password?: string; confirmar?: string } = {}
    if (!password) {
      e.password = 'La contraseña es obligatoria'
    } else if (password.length < 6) {
      e.password = 'La contraseña debe tener al menos 6 caracteres'
    }
    if (!confirmar) {
      e.confirmar = 'Confirmá tu contraseña'
    } else if (password && password !== confirmar) {
      e.confirmar = 'Las contraseñas no coinciden'
    }
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const handleSubmit = async () => {
    if (!validate()) return
    setLoading(true)
    try {
      await api.post('/usuarios/recuperar-password/confirmar/', {
        uid,
        token,
        password_nuevo: password,
      })
      setCompletado(true)
      toast.success('Contraseña restablecida correctamente')
      timerRef.current = setTimeout(() => navigate('/login'), 3000)
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: string } } }
      setErrors({ password: e?.response?.data?.error ?? 'El enlace expiró o es inválido' })
    } finally {
      setLoading(false)
    }
  }

  if (!uid || !token) {
    return (
      <AuthShell>
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm text-center">
          <p className="text-4xl mb-4">⚠️</p>
          <h2 className="text-lg font-bold text-slate-800 mb-2">Enlace inválido</h2>
          <p className="text-sm text-slate-500 mb-6">
            El enlace de recuperación no es válido. Solicitá uno nuevo.
          </p>
          <Link to="/recuperar-password" className="text-sm text-green-600 hover:text-green-700 font-medium transition-colors">
            Solicitar nuevo enlace
          </Link>
        </div>
      </AuthShell>
    )
  }

  if (completado) {
    return (
      <AuthShell>
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm text-center">
          <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-7 h-7 text-green-600" />
          </div>
          <h2 className="text-lg font-bold text-slate-800 mb-2">¡Contraseña restablecida!</h2>
          <p className="text-sm text-slate-500 mb-4">Serás redirigido al inicio de sesión...</p>
          <Link to="/login" className="text-sm text-green-600 hover:text-green-700 font-medium transition-colors">
            Ir al inicio de sesión
          </Link>
        </div>
      </AuthShell>
    )
  }

  return (
    <AuthShell>
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-xl font-bold text-slate-800">Nueva Contraseña</h1>
          <p className="text-sm text-slate-500 mt-1">Ingresá tu nueva contraseña</p>
        </div>

        <div className="space-y-4">
          <div className="relative">
            <Input
              type={showPassword ? 'text' : 'password'}
              label="Nueva contraseña"
              placeholder="••••••••"
              value={password}
              onChange={e => {
                setPassword(e.target.value)
                if (errors.password) setErrors(prev => ({ ...prev, password: undefined }))
              }}
              error={errors.password}
              onKeyDown={e => e.key === 'Enter' && handleSubmit()}
              autoFocus
              autoComplete="new-password"
            />
            <button
              type="button"
              onClick={() => setShowPassword(v => !v)}
              className="absolute right-3 top-[34px] text-slate-400 hover:text-slate-600 transition-colors"
              tabIndex={-1}
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>

          <Input
            type={showPassword ? 'text' : 'password'}
            label="Confirmar contraseña"
            placeholder="••••••••"
            value={confirmar}
            onChange={e => {
              setConfirmar(e.target.value)
              if (errors.confirmar) setErrors(prev => ({ ...prev, confirmar: undefined }))
            }}
            error={errors.confirmar}
            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
            autoComplete="new-password"
          />

          <Button variant="primary" block size="lg" loading={loading} onClick={handleSubmit}>
            Restablecer contraseña
          </Button>
        </div>
      </div>
    </AuthShell>
  )
}
