import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ShieldCheck, Eye, EyeOff, Copy, CheckCircle2, Fingerprint } from 'lucide-react'
import { QRCodeSVG } from 'qrcode.react'
import { browserSupportsWebAuthn, platformAuthenticatorIsAvailable, startRegistration } from '@simplewebauthn/browser'
import api from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'

type Metodo = 'cargando' | 'huella' | 'totp'

export default function PortalConfigurar2FA() {
  const navigate = useNavigate()
  const { user, loadUser } = useAuthStore()
  const [metodo, setMetodo] = useState<Metodo>('cargando')
  const [registrandoHuella, setRegistrandoHuella] = useState(false)

  const [loading, setLoading] = useState(false)
  const [otpUri, setOtpUri] = useState('')
  const [otpSecret, setOtpSecret] = useState('')
  const [backupCodes, setBackupCodes] = useState<string[]>([])
  const [otpCode, setOtpCode] = useState('')
  const [showSecret, setShowSecret] = useState(false)
  const [error, setError] = useState('')

  const iniciarSetupTotp = useCallback(async () => {
    setMetodo('totp')
    setLoading(true)
    try {
      const { data } = await api.post('/usuarios/2fa/configurar/')
      setOtpUri(data.otp_uri)
      setOtpSecret(data.secret)
      setBackupCodes(data.backup_codes ?? [])
    } catch {
      toast.error('No se pudo generar el código de configuración. Recargá la página.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelado = false
    async function decidirMetodo() {
      // El chequeo de plataforma cubre TODOS los casos por igual (celular sin
      // huella habilitada, navegador viejo, navegador interno de WhatsApp con
      // soporte parcial) sin necesidad de detectar cada caso por separado.
      const disponible = browserSupportsWebAuthn() && await platformAuthenticatorIsAvailable()
      if (cancelado) return
      if (disponible) setMetodo('huella')
      else iniciarSetupTotp()
    }
    decidirMetodo()
    return () => { cancelado = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const registrarHuella = async () => {
    setRegistrandoHuella(true)
    try {
      const { data: optionsJSON } = await api.post('/usuarios/webauthn/registrar-opciones/')
      const credential = await startRegistration({ optionsJSON })
      await api.post('/usuarios/webauthn/registrar-verificar/', { credential })
      await loadUser()
      toast.success('Huella activada')
      navigate('/portal', { replace: true })
    } catch (err) {
      // El usuario canceló el prompt nativo (Face ID/huella) — no es un error real
      if ((err as { name?: string })?.name !== 'NotAllowedError') {
        toast.error('No se pudo activar la huella')
      }
    } finally {
      setRegistrandoHuella(false)
    }
  }

  const activar = async (e: { preventDefault(): void }) => {
    e.preventDefault()
    if (otpCode.length !== 6) {
      setError('Ingresá el código de 6 dígitos')
      return
    }
    setLoading(true)
    try {
      await api.post('/usuarios/2fa/activar/', { codigo: otpCode })
      await loadUser()
      toast.success('Verificación en dos pasos activada')
      navigate('/portal', { replace: true })
    } catch (err) {
      const e = err as { response?: { data?: { error?: string } } }
      setError(e?.response?.data?.error || 'Código inválido')
      setOtpCode('')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-green-50 to-green-100 p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
            {metodo === 'huella'
              ? <Fingerprint className="w-8 h-8 text-green-600" />
              : <ShieldCheck className="w-8 h-8 text-green-600" />}
          </div>
          <h1 className="text-2xl font-bold text-gray-800">Activá la verificación en dos pasos</h1>
          <p className="text-gray-500 mt-2 text-sm">
            Hola, <span className="font-medium">{user?.nombre}</span>. Es opcional, pero te ayuda a
            proteger el acceso a los datos y el saldo de tu hijo/a.
          </p>
        </div>

        {metodo === 'cargando' && (
          <div className="text-center py-8 text-slate-400 text-sm">Preparando…</div>
        )}

        {metodo === 'huella' && (
          <div className="space-y-4 text-center">
            <p className="text-sm text-slate-600">
              Usá la huella o Face ID de este dispositivo — es más rápido y no necesitás ninguna
              app extra.
            </p>
            <Button variant="primary" block size="lg" loading={registrandoHuella} onClick={registrarHuella}>
              <Fingerprint className="w-5 h-5" /> Activar con tu huella
            </Button>
            <button
              type="button"
              onClick={iniciarSetupTotp}
              className="text-sm text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
            >
              Prefiero usar una app de autenticación
            </button>
          </div>
        )}

        {metodo === 'totp' && (otpUri ? (
          <form onSubmit={activar} className="space-y-4">
            <p className="text-sm text-slate-600">
              1. Escaneá este código con una app de autenticación (Google Authenticator, Authy, etc.)
            </p>
            <div className="bg-slate-50 rounded-xl p-4 flex flex-col items-center gap-3">
              <QRCodeSVG value={otpUri} size={180} level="H" className="rounded-lg border border-slate-200 p-2 bg-white" />
              <div className="flex items-center gap-2 text-xs bg-white border border-slate-200 rounded-lg px-3 py-2 w-full">
                <code className="flex-1 break-all text-slate-700 select-all">
                  {showSecret ? otpSecret : '•'.repeat(otpSecret.length)}
                </code>
                <button
                  type="button"
                  onClick={() => setShowSecret(s => !s)}
                  className="text-slate-400 hover:text-slate-600 cursor-pointer shrink-0"
                >
                  {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
                <button
                  type="button"
                  onClick={() => { navigator.clipboard.writeText(otpSecret); toast.success('Copiado') }}
                  className="text-slate-400 hover:text-slate-600 cursor-pointer shrink-0"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            </div>

            <Input
              label="2. Ingresá el código de 6 dígitos para confirmar"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={6}
              placeholder="123456"
              value={otpCode}
              onChange={e => {
                setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))
                if (error) setError('')
              }}
              error={error}
              className="text-center text-2xl font-mono tracking-widest"
              autoFocus
              autoComplete="one-time-code"
            />

            {backupCodes.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                <p className="text-xs font-semibold text-amber-800 mb-2">
                  Guardá estos códigos de respaldo — te van a servir si perdés el celular
                </p>
                <div className="grid grid-cols-4 gap-1">
                  {backupCodes.map(c => (
                    <code key={c} className="text-xs bg-white border border-amber-200 rounded px-2 py-1 text-center">{c}</code>
                  ))}
                </div>
              </div>
            )}

            <Button variant="primary" block size="lg" loading={loading} type="submit" disabled={otpCode.length !== 6}>
              <CheckCircle2 className="w-4 h-4" /> Activar y continuar
            </Button>
          </form>
        ) : (
          <div className="text-center py-8 text-slate-400 text-sm">Generando código de configuración…</div>
        ))}

        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={() => navigate('/portal')}
            className="text-sm text-gray-400 hover:text-gray-600 cursor-pointer"
          >
            Ahora no
          </button>
        </div>
      </div>
    </div>
  )
}
