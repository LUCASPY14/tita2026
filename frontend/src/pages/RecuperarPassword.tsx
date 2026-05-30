import { useState } from 'react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ArrowLeft, Mail } from 'lucide-react'
import api from '../services/api'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'

export default function RecuperarPassword() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [enviado, setEnviado] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    if (loading) return
    if (!email.trim()) { setError('Ingresá tu email'); return }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setError('Ingresá un email válido'); return }

    setLoading(true)
    setError('')
    try {
      await api.post('/usuarios/recuperar-password/', { email })
      setEnviado(true)
      toast.success('Revisá tu bandeja de entrada')
    } catch (err: unknown) {
      const e = err as { response?: unknown }
      if (e?.response) {
        // El servidor respondió (incluso 400/404) — no revelar si el email existe
        setEnviado(true)
      } else {
        // Error de red o servidor caído — informar sin mostrar pantalla de éxito falso
        toast.error('No se pudo conectar con el servidor. Intentá de nuevo.')
        setError('Error de conexión')
      }
    } finally {
      setLoading(false)
    }
  }

  if (enviado) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-100 p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm text-center">
          <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Mail className="w-7 h-7 text-green-600" />
          </div>
          <h2 className="text-lg font-bold text-slate-800 mb-2">¡Revisá tu email!</h2>
          <p className="text-sm text-slate-500 mb-6">
            Si el email existe en nuestro sistema, recibirás un enlace para restablecer tu contraseña.
          </p>
          <Link to="/login" className="text-sm text-green-600 hover:text-green-700 font-medium transition-colors">
            Volver al inicio de sesión
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-100 p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm">
        <div className="text-center mb-8">
          <img src="/logo_tita.png" alt="La Cantina de Tita" className="h-24 w-auto mx-auto mb-3 drop-shadow-sm" />
          <h1 className="text-xl font-bold text-slate-800">Recuperar Contraseña</h1>
          <p className="text-sm text-slate-500 mt-1">Ingresá tu email y te enviaremos un enlace</p>
        </div>

        <div className="space-y-4">
          <Input
            type="email"
            label="Email"
            placeholder="tu@email.com"
            value={email}
            onChange={e => {
              setEmail(e.target.value)
              if (error) setError('')
            }}
            error={error}
            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
            autoFocus
            autoComplete="email"
          />

          <Button variant="primary" block size="lg" loading={loading} onClick={handleSubmit}>
            Enviar enlace
          </Button>

          <Link
            to="/login"
            className="flex items-center justify-center gap-1.5 text-sm text-slate-400 hover:text-green-600 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Volver al inicio de sesión
          </Link>
        </div>
      </div>
    </div>
  )
}
