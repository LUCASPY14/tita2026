import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuthStore } from '../store/authStore'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async () => {
    if (!email || !password) {
      toast.error('Ingrese email y contrasena')
      return
    }
    setLoading(true)
    try {
      await login(email, password)
      toast.success('Bienvenido a La Cantina de Tita')
      navigate('/dashboard')
    } catch {
      toast.error('Email o contrasena incorrectos')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-green-50">
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-sm">
        <div className="text-center mb-6">
          <img src="/logo_tita.png" alt="La Cantina de Tita" className="h-28 w-auto mx-auto mb-3" />
          <p className="text-sm text-slate-500">Sistema de Gestión</p>
        </div>
        <div className="space-y-4">
          <Input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            autoFocus
          />
          <Input
            type="password"
            placeholder="Contrasena"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
          />
          <Button
            variant="primary"
            block
            size="lg"
            loading={loading}
            onClick={handleSubmit}
          >
            Iniciar Sesion
          </Button>
        </div>
      </div>
    </div>
  )
}
