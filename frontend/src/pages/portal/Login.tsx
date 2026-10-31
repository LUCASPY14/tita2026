import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ShieldCheck, ArrowLeft, Fingerprint, MessageCircle, PlayCircle } from 'lucide-react'
import { browserSupportsWebAuthn, platformAuthenticatorIsAvailable, startAuthentication } from '@simplewebauthn/browser'
import { useAuthStore } from '../../store/authStore'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import AuthShell from '../../components/AuthShell'

// TODO: reemplazar por el link real una vez grabado y subido el video tutorial.
const TUTORIAL_VIDEO_URL = 'https://www.youtube.com/@CantinaTita'

export default function PortalLogin() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [codigo, setCodigo] = useState('')
  const [codigoError, setCodigoError] = useState('')
  const codigoRef = useRef<HTMLInputElement>(null)
  const {
    login, verify2FA, verifyWebAuthn, enviarCodigoWhatsapp2FA,
    cancelPending2FA, pending2FA, pendingTieneWebauthn, pendingMetodo2FA,
  } = useAuthStore()
  const navigate = useNavigate()

  const [huellaDisponible, setHuellaDisponible] = useState<boolean | null>(null)
  const [mostrarCodigo, setMostrarCodigo] = useState(false)
  const [verificandoHuella, setVerificandoHuella] = useState(false)

  const [waEnviando, setWaEnviando] = useState(false)
  const [waEnviado, setWaEnviado] = useState(false)
  const [waTelefono, setWaTelefono] = useState('')

  const [olvideModo, setOlvideModo] = useState(false)
  const [emailRecuperar, setEmailRecuperar] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [enviado, setEnviado] = useState(false)

  // Apuntar al manifest del portal acá también: es la pantalla donde el padre
  // instala la app (antes de loguearse) — si solo se hiciera en PortalLayout
  // (rutas ya autenticadas), "Agregar a pantalla de inicio" desde el login
  // instalaría el manifest por defecto (el del POS interno, apunta a
  // /modo-recreo, al que el padre no tiene acceso).
  useEffect(() => {
    const link = document.querySelector<HTMLLinkElement>('link[rel="manifest"]')
    const prev = link?.getAttribute('href') ?? '/manifest.webmanifest'
    link?.setAttribute('href', '/portal-manifest.webmanifest')
    return () => { link?.setAttribute('href', prev) }
  }, [])

  const irLuegoDeLogin = () => {
    const { user } = useAuthStore.getState()
    if (user?.debe_cambiar_contrasena) {
      navigate('/portal/cambiar-contrasena', { replace: true })
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

  useEffect(() => {
    if (!pending2FA || !pendingTieneWebauthn) return
    let cancelado = false
    ;(async () => {
      const disponible = browserSupportsWebAuthn() && await platformAuthenticatorIsAvailable()
      if (!cancelado) setHuellaDisponible(disponible)
    })()
    return () => { cancelado = true }
  }, [pending2FA, pendingTieneWebauthn])

  const handleWebAuthn = async () => {
    setVerificandoHuella(true)
    try {
      const { data: optionsJSON } = await api.post('/usuarios/webauthn/login-opciones/', {
        pre_auth_token: pending2FA,
      })
      const credential = await startAuthentication({ optionsJSON })
      await verifyWebAuthn(credential)
      irLuegoDeLogin()
    } catch (err) {
      if ((err as { name?: string })?.name !== 'NotAllowedError') {
        toast.error('No se pudo verificar la huella')
      }
      setVerificandoHuella(false)
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
    setMostrarCodigo(false)
    setHuellaDisponible(null)
    setWaEnviado(false)
    setWaTelefono('')
  }

  const handleEnviarWhatsapp2FA = async () => {
    setWaEnviando(true)
    try {
      const telefono = await enviarCodigoWhatsapp2FA()
      setWaTelefono(telefono)
      setWaEnviado(true)
      queueMicrotask(() => codigoRef.current?.focus())
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })
        ?.response?.data?.error ?? 'No se pudo enviar el código por WhatsApp.'
      toast.error(msg)
    } finally {
      setWaEnviando(false)
    }
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
    const puedeHuella = pendingTieneWebauthn && huellaDisponible === true && !mostrarCodigo
    const verificandoDisponibilidad = pendingTieneWebauthn && huellaDisponible === null && !mostrarCodigo
    const usaWhatsapp = !puedeHuella && !verificandoDisponibilidad && pendingMetodo2FA === 'WHATSAPP'

    return (
      <AuthShell caption="Portal de Padres">
        <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-green-100 mb-3">
              {puedeHuella
                ? <Fingerprint className="w-7 h-7 text-green-600" />
                : usaWhatsapp
                ? <MessageCircle className="w-7 h-7 text-green-600" />
                : <ShieldCheck className="w-7 h-7 text-green-600" />}
            </div>
            <h2 className="text-lg font-semibold text-slate-800">Verificación en dos pasos</h2>
            <p className="text-sm text-slate-500 mt-1">
              {puedeHuella
                ? 'Confirmá con tu huella o Face ID'
                : usaWhatsapp
                ? (waEnviado ? 'Ingresá el código que te enviamos por WhatsApp' : 'Te enviamos un código por WhatsApp para confirmar tu identidad')
                : 'Ingresá el código de 6 dígitos de tu aplicación autenticadora'}
            </p>
          </div>

          {verificandoDisponibilidad ? (
            <div className="text-center py-4 text-slate-400 text-sm">Un momento…</div>
          ) : puedeHuella ? (
            <div className="space-y-4">
              <Button variant="primary" block size="lg" loading={verificandoHuella} onClick={handleWebAuthn}>
                <Fingerprint className="w-5 h-5" /> Continuar con tu huella
              </Button>
              <button
                type="button"
                onClick={() => setMostrarCodigo(true)}
                className="w-full text-sm text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
              >
                {pendingMetodo2FA === 'WHATSAPP' ? 'Usar el código de WhatsApp en su lugar' : 'Usar el código de mi app en su lugar'}
              </button>
            </div>
          ) : usaWhatsapp ? (
            !waEnviado ? (
              <div className="space-y-4">
                <Button variant="primary" block size="lg" loading={waEnviando} onClick={handleEnviarWhatsapp2FA}>
                  <MessageCircle className="w-5 h-5" /> Enviar código por WhatsApp
                </Button>
              </div>
            ) : (
              <form onSubmit={handle2FASubmit} className="space-y-4">
                {waTelefono && (
                  <p className="text-xs text-slate-400 text-center">Enviado al {waTelefono}</p>
                )}
                <Input
                  ref={codigoRef}
                  label="Código de WhatsApp"
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
                <button
                  type="button"
                  onClick={handleEnviarWhatsapp2FA}
                  disabled={waEnviando}
                  className="w-full text-sm text-slate-400 hover:text-slate-600 transition-colors cursor-pointer disabled:opacity-50"
                >
                  Reenviar código
                </button>
              </form>
            )
          ) : (
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
          )}

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
              {usaWhatsapp
                ? '¿Ya no tenés ese número de WhatsApp? Contactá a la cantina para restablecer tu verificación.'
                : '¿Perdiste el acceso a tu app de autenticación? Contactá a la cantina para restablecer tu verificación.'}
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
          <p>
            <a
              href={TUTORIAL_VIDEO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-green-600 hover:underline"
            >
              <PlayCircle className="w-4 h-4" />
              ¿Cómo uso esto?
            </a>
          </p>
          <p className="text-sm text-gray-400">
            ¿Trabajás en la cantina?{' '}
            <Link to="/login" className="text-green-600 hover:underline">Acceso empleados</Link>
          </p>
          <p className="text-xs text-gray-300">
            <Link to="/portal/terminos" className="hover:underline">Términos y Condiciones</Link>
          </p>
        </div>
      </div>
    </AuthShell>
  )
}
