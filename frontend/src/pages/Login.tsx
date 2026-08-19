import { useState, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Eye, EyeOff, ShieldCheck, ArrowLeft } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import AuthShell from '../components/AuthShell'

type LoginVariant = 'admin' | 'pos' | 'cobranzas'

const VARIANTES: Record<LoginVariant, { text: string; className: string }> = {
  admin:     { text: 'Administración', className: 'bg-orange-100 text-orange-700' },
  pos:       { text: 'Caja / POS',     className: 'bg-amber-100 text-amber-700' },
  cobranzas: { text: 'Cobranzas',      className: 'bg-blue-100 text-blue-700' },
}

interface Props {
  variant?: LoginVariant
}

export default function Login({ variant = 'admin' }: Props) {
  const badge = VARIANTES[variant]
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<{ email?: string; password?: string; codigo?: string }>({})
  const [showPassword, setShowPassword] = useState(false)
  // 2FA step 2
  const [codigo, setCodigo] = useState('')
  const codigoRef = useRef<HTMLInputElement>(null)

  const { login, verify2FA, cancelPending2FA, pending2FA } = useAuthStore()
  const navigate = useNavigate()

  const validate = (): boolean => {
    const newErrors: { email?: string; password?: string } = {}
    const identificador = email.trim()
    if (!identificador) {
      newErrors.email = 'El CI/RUC es obligatorio'
    } else if (identificador.includes('@')) {
      newErrors.email = 'Ingresá tu CI o RUC, no un email'
    }
    if (!password) newErrors.password = 'La contraseña es obligatoria'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async () => {
    if (!validate()) return
    setLoading(true)
    try {
      const done = await login(email, password)
      if (done) {
        navigate('/dashboard')
        queueMicrotask(() => toast.success('¡Bienvenido a La Cantina de Tita!'))
        // component unmounts — don't call setLoading(false)
      } else {
        // 2FA required: store set pending2FA, component re-renders showing step 2
        setLoading(false)
        queueMicrotask(() => codigoRef.current?.focus())
      }
    } catch {
      setErrors({ password: 'CI/RUC o contraseña incorrectos' })
      setLoading(false)
    }
  }

  const handle2FASubmit = async () => {
    const trimmed = codigo.replace(/\s/g, '')
    if (!trimmed) {
      setErrors({ codigo: 'Ingresá el código de 6 dígitos' })
      return
    }
    setLoading(true)
    try {
      await verify2FA(trimmed)
      navigate('/dashboard')
      queueMicrotask(() => toast.success('¡Bienvenido a La Cantina de Tita!'))
    } catch {
      setErrors({ codigo: 'Código inválido o expirado' })
      setCodigo('')
      setLoading(false)
      queueMicrotask(() => codigoRef.current?.focus())
    }
  }

  const handleCancel2FA = () => {
    cancelPending2FA()
    setCodigo('')
    setErrors({})
  }

  // ── Step 2: 2FA code entry ────────────────────────────────────────────────
  if (pending2FA) {
    return (
      <AuthShell badge={badge}>
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-green-100 mb-3">
              <ShieldCheck className="w-7 h-7 text-green-600" />
            </div>
            <h2 className="text-lg font-semibold text-slate-800">Verificación en dos pasos</h2>
            <p className="text-sm text-slate-500 mt-1">
              Ingresá el código de 6 dígitos de tu aplicación autenticadora
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Código TOTP
              </label>
              <input
                ref={codigoRef}
                type="text"
                inputMode="numeric"
                pattern="[0-9 ]*"
                maxLength={7}
                placeholder="000000"
                value={codigo}
                onChange={e => {
                  setCodigo(e.target.value.replace(/[^0-9 ]/g, ''))
                  if (errors.codigo) setErrors({})
                }}
                onKeyDown={e => e.key === 'Enter' && handle2FASubmit()}
                autoFocus
                autoComplete="one-time-code"
                className={[
                  'w-full px-4 py-3 text-center text-2xl font-mono tracking-widest rounded-xl border',
                  'focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent',
                  'transition-colors duration-150',
                  errors.codigo
                    ? 'border-red-400 bg-red-50'
                    : 'border-slate-300 bg-white hover:border-slate-400',
                ].join(' ')}
              />
              {errors.codigo && (
                <p className="mt-1 text-xs text-red-500">{errors.codigo}</p>
              )}
            </div>

            <Button
              variant="primary"
              block
              size="lg"
              loading={loading}
              onClick={handle2FASubmit}
            >
              Verificar
            </Button>
          </div>

          <div className="mt-5 text-center">
            <button
              type="button"
              onClick={handleCancel2FA}
              className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-600 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Volver al inicio de sesión
            </button>
          </div>
        </div>
      </AuthShell>
    )
  }

  // ── Step 1: email + password ──────────────────────────────────────────────
  return (
    <AuthShell badge={badge}>
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm">
        <div className="space-y-4">
          <Input
            type="text"
            label="CI/RUC"
            placeholder="Tu CI o RUC"
            value={email}
            onChange={e => {
              setEmail(e.target.value)
              if (errors.email) setErrors(prev => ({ ...prev, email: undefined }))
            }}
            error={errors.email}
            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
            autoFocus
            autoComplete="username"
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
    </AuthShell>
  )
}
