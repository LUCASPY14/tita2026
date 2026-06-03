import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Eye, EyeOff } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({})
  const [showPassword, setShowPassword] = useState(false)
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const validate = (): boolean => {
    const newErrors: { email?: string; password?: string } = {}
    if (!email.trim()) {
      newErrors.email = 'El email es obligatorio'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Ingresá un email válido'
    }
    if (!password) newErrors.password = 'La contraseña es obligatoria'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async () => {
    if (!validate()) return
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
      // Defer toast to a separate React batch: calling toast.success() in the same
      // synchronous frame as navigate() causes React 19 to batch both the Toaster
      // update and the route change together, resulting in an insertBefore DOM error
      // when it tries to insert the toast node while simultaneously unmounting Login.
      queueMicrotask(() => toast.success('¡Bienvenido a La Cantina de Tita!'))
    } catch {
      setErrors({ password: 'Email o contraseña incorrectos' })
      setLoading(false)
    }
    // No finally: on success the component unmounts immediately after navigate(),
    // so setLoading(false) would be a state update on an unmounting component.
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-100 p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm">
        <div className="text-center mb-8">
          <img src="/logo_tita.png" alt="La Cantina de Tita" className="h-28 w-auto mx-auto mb-3 drop-shadow-sm" />
          <p className="text-sm text-slate-500">Sistema de Gestión</p>
        </div>

        <div className="space-y-4">
          <Input
            type="email"
            label="Email"
            placeholder="tu@email.com"
            value={email}
            onChange={e => {
              setEmail(e.target.value)
              if (errors.email) setErrors(prev => ({ ...prev, email: undefined }))
            }}
            error={errors.email}
            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
            autoFocus
            autoComplete="email"
          />

          <div className="relative">
            <Input
              type={showPassword ? 'text' : 'password'}
              label="Contraseña"
              placeholder="••••••••"
              value={password}
              onChange={e => {
                setPassword(e.target.value)
                if (errors.password) setErrors(prev => ({ ...prev, password: undefined }))
              }}
              error={errors.password}
              onKeyDown={e => e.key === 'Enter' && handleSubmit()}
              autoComplete="current-password"
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

          <Button
            variant="primary"
            block
            size="lg"
            loading={loading}
            onClick={handleSubmit}
          >
            Iniciar Sesión
          </Button>
        </div>

        <div className="mt-6 text-center">
          <Link to="/recuperar-password" className="text-xs text-slate-400 hover:text-green-600 transition-colors">
            ¿Olvidaste tu contraseña?
          </Link>
        </div>
      </div>
    </div>
  )
}
