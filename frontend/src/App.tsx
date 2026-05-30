import { Component, useEffect, type ReactNode } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Login from './pages/Login'
import RecuperarPassword from './pages/RecuperarPassword'
import RestablecerPassword from './pages/RestablecerPassword'
import AppLayout from './components/Layout'
import PortalLayout from './components/PortalLayout'
import Productos from './pages/Productos'
import Clientes from './pages/Clientes'
import Tarjetas from './pages/Tarjetas'
// Ventas eliminado — se usa ModoRecreo como POS principal
import Caja from './pages/Cajas'
import Compras from './pages/Compras'
import Dashboard from './pages/Dashboard'
import Almuerzos from './pages/Almuerzos'
import Facturacion from './pages/Facturacion'
import Reportes from './pages/Reportes'
import Inventario from './pages/Inventario'
import Usuarios from './pages/Usuarios'
import Configuracion from './pages/Configuracion'
import CargaSaldo from './pages/CargaSaldo'
import Comedor from './pages/Comedor'
import ModoRecreo from './pages/ModoRecreo'
import PortalDashboard from './pages/portal/Dashboard'
import PortalLogin from './pages/portal/Login'
import PortalNotificaciones from './pages/portal/Notificaciones'
import PortalResetPassword from './pages/portal/ResetPassword'
import { useAuthStore } from './store/authStore'

class ErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean; message: string }> {
  state = { hasError: false, message: '' }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, message: error.message }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 p-8 text-center">
          <div className="bg-white rounded-2xl border border-red-100 shadow-sm px-8 py-10 max-w-md">
            <p className="text-4xl mb-4">⚠️</p>
            <h1 className="text-xl font-bold text-slate-900 mb-2">Algo salió mal</h1>
            <p className="text-sm text-slate-500 mb-6">{this.state.message || 'Error inesperado en la aplicación.'}</p>
            <button
              onClick={() => { this.setState({ hasError: false, message: '' }); window.location.href = '/' }}
              className="px-5 py-2 bg-green-600 text-white text-sm font-semibold rounded-xl hover:bg-green-700 transition-colors"
            >
              Volver al inicio
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

function PrivateRoute({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { isAuthenticated, user } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" />
  if (roles && user && !roles.includes(user.rol)) return <Navigate to="/login" />
  return <>{children}</>
}

function AuthMonitor() {
  const navigate = useNavigate()
  const { logout, user } = useAuthStore()

  useEffect(() => {
    const handle = () => {
      const isPortal = user?.rol === 'CLIENTE_WEB'
      logout()
      navigate(isPortal ? '/portal/login' : '/login', { replace: true })
    }
    window.addEventListener('auth:logout', handle)
    return () => window.removeEventListener('auth:logout', handle)
  }, [logout, navigate, user])

  return null
}

export default function App() {
  const { loadUser } = useAuthStore()

  useEffect(() => {
    loadUser()
  }, [])

  return (
    <ErrorBoundary>
    <BrowserRouter>
      <AuthMonitor />
      <Toaster position="top-right" toastOptions={{ duration: 3000 }} />
      <Routes>
        {/* Portal padres (separado) */}
        <Route path="/portal/login" element={<PortalLogin />} />
        <Route path="/portal/reset-password" element={<PortalResetPassword />} />
        <Route path="/portal" element={
          <PrivateRoute roles={['CLIENTE_WEB']}>
            <PortalLayout />
          </PrivateRoute>
        }>
          <Route index element={<PortalDashboard />} />
          <Route path="notificaciones" element={<PortalNotificaciones />} />
        </Route>

        {/* Sistema de gestión */}
        <Route path="/login" element={<Login />} />
        <Route path="/recuperar-password" element={<RecuperarPassword />} />
        <Route path="/reset-password" element={<RestablecerPassword />} />
        <Route element={
          <PrivateRoute roles={['ADMIN', 'CAJERO', 'COCINA']}>
            <AppLayout />
          </PrivateRoute>
        }>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/ventas" element={<Navigate to="/modo-recreo" />} />
          <Route path="/compras" element={<Compras />} />
          <Route path="/clientes" element={<Clientes />} />
          <Route path="/productos" element={<Productos />} />
          <Route path="/tarjetas" element={<Tarjetas />} />
          <Route path="/carga-saldo" element={<CargaSaldo />} />
          <Route path="/caja" element={<Caja />} />
          <Route path="/almuerzos" element={<Almuerzos />} />
          <Route path="/comedor" element={<Comedor />} />
          <Route path="/facturacion" element={<Facturacion />} />
          <Route path="/reportes" element={<Reportes />} />
          <Route path="/inventario" element={<Inventario />} />
          <Route path="/usuarios" element={<Usuarios />} />
          <Route path="/configuracion" element={<Configuracion />} />
        </Route>

        {/* Modo Recreo — overlay full-screen, fuera del AppLayout */}
        <Route path="/modo-recreo" element={
          <PrivateRoute roles={['ADMIN', 'CAJERO']}>
            <ModoRecreo />
          </PrivateRoute>
        } />

        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
    </ErrorBoundary>
  )
}