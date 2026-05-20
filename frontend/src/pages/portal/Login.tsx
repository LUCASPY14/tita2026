import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuthStore } from '../../store/authStore'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'

export default function PortalLogin() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const [olvideModo, setOlvideModo] = useState(false)
  const [emailRecuperar, setEmailRecuperar] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [enviado, setEnviado] = useState(false)

  const handleSubmit = async (e: { preventDefault(): void }) => {
    e.preventDefault()
    setLoading(true)
    try {
      await login(email, password)
      toast.success('Bienvenido al portal')
      navigate('/portal')
    } catch {
      toast.error('Credenciales incorrectas')
    } finally {
      setLoading(false)
    }
  }

  const handleRecuperar = async (e: { preventDefault(): void }) => {
    e.preventDefault()
    if (!emailRecuperar.trim()) return
    setEnviando(true)
    try {
      await api.post('/usuarios/recuperar-password/', { email: emailRecuperar.trim() })
      setEnviado(true)
    } catch {
      toast.error('No se encontró una cuenta con ese email')
    } finally {
      setEnviando(false)
    }
  }

  if (olvideModo) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-green-50 to-green-100">
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <img src="/logo_tita.png" alt="Cantina Tita" className="h-16 w-auto mx-auto mb-4" />
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
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-green-50 to-green-100">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <img src="/logo_tita.png" alt="La Cantina de Tita" className="h-32 w-auto mx-auto mb-3" />
          <p className="text-gray-500">Portal de Padres</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email"
            type="email"
            placeholder="tucorreo@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            label="Contraseña"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <Button variant="primary" block size="lg" loading={loading} type="submit">
            Ingresar
          </Button>
        </form>
        <div className="mt-4 text-center space-y-2">
          <button
            onClick={() => setOlvideModo(true)}
            className="text-sm text-green-600 hover:underline cursor-pointer"
          >
            Olvidé mi contraseña
          </button>
          <p className="text-sm text-gray-400">
            ¿Trabajás en la cantina?{' '}
            <a href="/login" className="text-green-600 hover:underline">Acceso empleados</a>
          </p>
        </div>
      </div>
    </div>
  )
}
