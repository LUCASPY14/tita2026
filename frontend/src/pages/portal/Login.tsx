import { useState, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ShieldCheck, ArrowLeft } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import AuthShell from '../../components/AuthShell'

export default function PortalLogin() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [codigo, setCodigo] = useState('')
  const [codigoError, setCodigoError] = useState('')
  const codigoRef = useRef<HTMLInputElement>(null)
  const { login, verify2FA, cancelPending2FA, pending2FA } = useAuthStore()
  const navigate = useNavigate()

  const [olvideModo, setOlvideModo] = useState(false)
  const [emailRecuperar, setEmailRecuperar] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [enviado, setEnviado] = useState(false)

  const irLuegoDeLogin = () => {
    const { user } = useAuthStore.getState()
    if (user?.debe_cambiar_contrasena) {
      navigate('/portal/cambiar-contrasena', { replace: true })
    } else if (!user?.tiene_2fa_activo) {
      navigate('/portal/configurar-2fa', { replace: true })
    } else {
      toast.success('Bienvenido al portal')
      navigate('/portal')
    }
  }

  const handleSubmit = async (e: { preventDefault(): void }) => {
    e.preventDefault()
    setLoading(true)
    try {
      const done = await login(email, password)
      if (done) {
        irLuegoDeLogin()
      } else {
        // 2FA requerido: el store guardó pending2FA, se muestra el paso 2
        setLoading(false)
        queueMicrotask(() => codigoRef.current?.focus())
      }
    } catch (err) {
      const e = err as { response?: { status?: number } }
      if (e?.response?.status === 401) {
        toast.error('Credenciales incorrectas')
      } else {
        toast.error('Error de conexión. Intentalo de nuevo.')
      }
      setLoading(false)
    }
  }

  const handle2FASubmit = async (e: { preventDefault(): void }) => {
    e.preventDefault()
    const trimmed = codigo.replace(/\s/g, '')
    if (!trimmed) {
      setCodigoError('Ingresá el código de 6 dígitos')
      return
    }
    setLoading(true)
    try {
      await verify2FA(trimmed)
      irLuegoDeLogin()
    } catch {
      setCodigoError('Código inválido o expirado')
      setCodigo('')
      setLoading(false)
      queueMicrotask(() => codigoRef.current?.focus())
    }
  }

  const handleCancel2FA = () => {
    cancelPending2FA()
    setCodigo('')
    setCodigoError('')
  }

  const handleRecuperar = async (e: { preventDefault(): void }) => {
    e.preventDefault()
    if (!emailRecuperar.trim()) return
    setEnviando(true)
    try {
      await api.post('/usuarios/recuperar-password/', { email: emailRecuperar.trim() })
    } catch {
      // Never reveal whether the email exists in the system
    } finally {
      setEnviando(false)
      setEnviado(true)
    }
  }

  if (pending2FA) {
    return (
      <AuthShell caption="Portal de Padres">
        <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-green-100 mb-3">
              <ShieldCheck className="w-7 h-7 text-green-600" />
            </div>
            <h2 className="text-lg font-semibold text-slate-800">Verificación en dos pasos</h2>
            <p className="text-sm text-slate-500 mt-1">
              Ingresá el código de 6 dígitos de tu aplicación autenticadora
            </p>
          </div>

          <form onSubmit={handle2FASubmit} className="space-y-4">
            <Input
              ref={codigoRef}
              label="Código TOTP"
              type="text"
              inputMode="numeric"
              pattern="[0-9 ]*"
              maxLength={7}
              placeholder="000000"
              value={codigo}
              onChange={e => {
                setCodigo(e.target.value.replace(/[^0-9 ]/g, ''))
                if (codigoError) setCodigoError('')
              }}
              error={codigoError}
              autoFocus
              autoComplete="one-time-code"
              className="text-center text-2xl font-mono tracking-widest"
            />
            <Button variant="primary" block size="lg" loading={loading} type="submit">
              Verificar
            </Button>
          </form>

          <div className="mt-5 text-center">
            <button
              type="button"
              onClick={handleCancel2FA}
              className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Volver al inicio de sesión
            </button>
            <p className="text-xs text-slate-400 mt-3">
              ¿Perdiste el acceso a tu app de autenticación? Contactá a la cantina para restablecer tu verificación.
            </p>
          </div>
        </div>
      </AuthShell>
    )
  }

  if (olvideModo) {
    return (
      <AuthShell>
        <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-green-800">Recuperar contraseña</h1>
            <p className="text-gray-500 mt-2 text-sm">Te enviaremos un enlace a tu email</p>
          </div>

          {enviado ? (
            <div className="text-center space-y-4">
              <p className="text-4xl">📬</p>
              <p className="text-gray-700 font-medium">Revisá tu correo</p>
              <p className="text-gray-500 text-sm">
                Si existe una cuenta con ese email, recibirás un enlace para restablecer tu contraseña.
              </p>
              <button
                type="button"
                onClick={() => { setOlvideModo(false); setEnviado(false); setEmailRecuperar('') }}
                className="text-sm text-green-600 hover:underline cursor-pointer"
              >
                Volver al login
              </button>
            </div>
          ) : (
            <form onSubmit={handleRecuperar} className="space-y-4">
              <Input
                label="Email"
                type="email"
                placeholder="tucorreo@email.com"
                value={emailRecuperar}
                onChange={(e) => setEmailRecuperar(e.target.value)}
                required
              />
              <Button variant="primary" block size="lg" loading={enviando} type="submit">
                Enviar enlace
              </Button>
              <p className="text-center">
                <button
                  type="button"
                  onClick={() => setOlvideModo(false)}
                  className="text-sm text-green-600 hover:underline cursor-pointer"
                >
                  Volver al login
                </button>
              </p>
            </form>
          )}
        </div>
      </AuthShell>
    )
  }

  return (
    <AuthShell caption="Portal de Padres">
      <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8 w-full max-w-md">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="CI/RUC"
            type="text"
            placeholder="Ej: 3331234-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="username"
            required
          />
          <Input
            label="Contraseña"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
          <Button variant="primary" block size="lg" loading={loading} type="submit">
            Ingresar
          </Button>
        </form>
        <div className="mt-4 text-center space-y-2">
          <button
            type="button"
            onClick={() => setOlvideModo(true)}
            className="text-sm text-green-600 hover:underline cursor-pointer"
          >
            Olvidé mi contraseña
          </button>
          <p className="text-sm text-gray-400">
            ¿Trabajás en la cantina?{' '}
            <Link to="/login" className="text-green-600 hover:underline">Acceso empleados</Link>
          </p>
        </div>
      </div>
    </AuthShell>
  )
}
