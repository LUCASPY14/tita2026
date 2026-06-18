import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Shield, XCircle, CheckCircle2, Eye, EyeOff, Copy } from 'lucide-react'
import { QRCodeSVG } from 'qrcode.react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import { extractErrorMessage, inputClass, type Estado2FA } from './helpers'

type Step = 'idle' | 'setup' | 'disable'

export default function TabSeguridad() {
  const [estado2fa, setEstado2fa] = useState<Estado2FA | null>(null)
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState<Step>('idle')
  const [otpUri, setOtpUri] = useState('')
  const [otpSecret, setOtpSecret] = useState('')
  const [backupCodes, setBackupCodes] = useState<string[]>([])
  const [otpCode, setOtpCode] = useState('')
  const [showSecret, setShowSecret] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/usuarios/2fa/estado/')
      setEstado2fa(data)
    } catch { toast.error('Error al cargar estado 2FA') }
    finally { setLoading(false) }
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load(); setStep('idle') }, [load])

  const iniciarSetup = async () => {
    try {
      const { data } = await api.post('/usuarios/2fa/configurar/')
      setOtpUri(data.otp_uri)
      setOtpSecret(data.secret)
      setBackupCodes(data.backup_codes ?? [])
      setOtpCode('')
      setStep('setup')
    } catch (err) { toast.error(extractErrorMessage(err)) }
  }

  const activar = async () => {
    if (otpCode.length !== 6) { toast.error('Ingresá el código de 6 dígitos'); return }
    try {
      await api.post('/usuarios/2fa/activar/', { codigo: otpCode })
      toast.success('2FA activado correctamente')
      setStep('idle'); setOtpCode(''); load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
  }

  const desactivar = async () => {
    if (otpCode.length < 6) { toast.error('Ingresá tu código TOTP actual para confirmar'); return }
    try {
      await api.post('/usuarios/2fa/desactivar/', { codigo: otpCode })
      toast.success('2FA desactivado')
      setStep('idle'); setOtpCode(''); load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
  }

  return (
    <div className="max-w-lg space-y-5">
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${estado2fa?.habilitado ? 'bg-green-50' : 'bg-slate-100'}`}>
            <Shield className={`w-5 h-5 ${estado2fa?.habilitado ? 'text-green-600' : 'text-slate-400'}`} />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-800">Autenticación de dos factores</p>
            <p className="text-xs text-slate-500">TOTP — compatible con Google Authenticator, Authy, etc.</p>
          </div>
          {!loading && (
            <Badge color={estado2fa?.habilitado ? 'green' : 'default'}>
              {estado2fa?.habilitado ? 'Activo' : 'Inactivo'}
            </Badge>
          )}
        </div>

        {step === 'idle' && !loading && (
          <div className="space-y-3">
            {estado2fa?.fecha_activacion && (
              <p className="text-xs text-slate-400">
                Activado el {new Date(estado2fa.fecha_activacion).toLocaleDateString('es-PY')}
              </p>
            )}
            {estado2fa?.habilitado ? (
              <Button variant="danger" onClick={() => { setOtpCode(''); setStep('disable') }}>
                <XCircle className="w-4 h-4" /> Desactivar 2FA
              </Button>
            ) : (
              <Button variant="primary" onClick={iniciarSetup}>
                <Shield className="w-4 h-4" /> Configurar 2FA
              </Button>
            )}
          </div>
        )}

        {step === 'setup' && (
          <div className="space-y-4">
            <p className="text-sm text-slate-600">
              1. Escaneá este código con tu app de autenticación, o copiá el secret manualmente.
            </p>
            <div className="bg-slate-50 rounded-xl p-4 flex flex-col items-center gap-3">
              <QRCodeSVG value={otpUri} size={180} level="H" className="rounded-lg border border-slate-200 p-2 bg-white" />
              <div className="flex items-center gap-2 text-xs bg-white border border-slate-200 rounded-lg px-3 py-2 w-full">
                <code className="flex-1 break-all text-slate-700 select-all">
                  {showSecret ? otpSecret : '•'.repeat(otpSecret.length)}
                </code>
                <button onClick={() => setShowSecret(s => !s)} className="text-slate-400 hover:text-slate-600 cursor-pointer shrink-0">
                  {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
                <button onClick={() => { navigator.clipboard.writeText(otpSecret); toast.success('Copiado') }} className="text-slate-400 hover:text-slate-600 cursor-pointer shrink-0">
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            </div>
            <p className="text-sm text-slate-600">2. Ingresá el código de 6 dígitos para confirmar.</p>
            <div className="flex gap-2">
              <input
                value={otpCode}
                onChange={e => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="123456"
                className={`${inputClass} text-center tracking-widest text-lg font-mono`}
                maxLength={6}
              />
              <Button variant="primary" onClick={activar} disabled={otpCode.length !== 6}>
                <CheckCircle2 className="w-4 h-4" /> Activar
              </Button>
            </div>
            {backupCodes.length > 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                <p className="text-xs font-semibold text-amber-800 mb-2">Guardá estos códigos de respaldo (úsalos si perdés acceso a tu app)</p>
                <div className="grid grid-cols-4 gap-1">
                  {backupCodes.map(c => (
                    <code key={c} className="text-xs bg-white border border-amber-200 rounded px-2 py-1 text-center">{c}</code>
                  ))}
                </div>
              </div>
            )}
            <Button variant="secondary" onClick={() => setStep('idle')}>Cancelar</Button>
          </div>
        )}

        {step === 'disable' && (
          <div className="space-y-3">
            <p className="text-sm text-slate-600">Ingresá tu código TOTP actual para desactivar el 2FA.</p>
            <div className="flex gap-2">
              <input
                value={otpCode}
                onChange={e => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="123456"
                className={`${inputClass} text-center tracking-widest text-lg font-mono`}
                maxLength={6}
              />
              <Button variant="danger" onClick={desactivar} disabled={otpCode.length !== 6}>
                Confirmar
              </Button>
            </div>
            <Button variant="secondary" onClick={() => setStep('idle')}>Cancelar</Button>
          </div>
        )}
      </div>
    </div>
  )
}
