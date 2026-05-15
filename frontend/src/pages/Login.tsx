import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Card, Input, message } from 'antd'
import { useAuthStore } from '../store/authStore'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async () => {
    if (!email || !password) {
      message.warning('Ingrese email y contraseña')
      return
    }
    setLoading(true)
    try {
      await login(email, password)
      message.success('Bienvenido a La Cantina de Tita')
      navigate('/dashboard')
    } catch {
      message.error('Email o contraseña incorrectos')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-green-50">
      <Card className="w-96 shadow-lg" title={
        <div className="text-center text-xl">La Cantina de Tita</div>
      }>
        <Input
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mb-3"
          size="large"
          onPressEnter={handleSubmit}
        />
        <Input.Password
          placeholder="Contrasena"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mb-4"
          size="large"
          onPressEnter={handleSubmit}
        />
        <Button
          type="primary"
          block
          size="large"
          loading={loading}
          onClick={handleSubmit}
        >
          Iniciar Sesion
        </Button>
      </Card>
    </div>
  )
}