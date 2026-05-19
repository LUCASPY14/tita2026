import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Login from './pages/Login'
import AppLayout from './components/Layout'
import PortalLayout from './components/PortalLayout'
import Productos from './pages/Productos'
import Clientes from './pages/Clientes'
import Tarjetas from './pages/Tarjetas'
import Ventas from './pages/Ventas'
import Caja from './pages/Cajas'
import Compras from './pages/Compras'
import Dashboard from './pages/Dashboard'
import Almuerzos from './pages/Almuerzos'
import Facturacion from './pages/Facturacion'
import Reportes from './pages/Reportes'
import Inventario from './pages/Inventario'
import Usuarios from './pages/Usuarios'
import Configuracion from './pages/Configuracion'
import PortalDashboard from './pages/portal/Dashboard'
import PortalLogin from './pages/portal/Login'
import PortalNotificaciones from './pages/portal/Notificaciones'
import PortalResetPassword from './pages/portal/ResetPassword'
import { useAuthStore } from './store/authStore'

function PrivateRoute({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const { isAuthenticated, user } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" />
  if (roles && user && !roles.includes(user.rol)) return <Navigate to="/login" />
  return <>{children}</>
}

export default function App() {
  const { loadUser } = useAuthStore()

  useEffect(() => {
    loadUser()
  }, [])

  return (
    <BrowserRouter>
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
        <Route element={
          <PrivateRoute roles={['ADMIN', 'CAJERO', 'COCINA']}>
            <AppLayout />
          </PrivateRoute>
        }>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/ventas" element={<Ventas />} />
          <Route path="/compras" element={<Compras />} />
          <Route path="/clientes" element={<Clientes />} />
          <Route path="/productos" element={<Productos />} />
          <Route path="/tarjetas" element={<Tarjetas />} />
          <Route path="/caja" element={<Caja />} />
          <Route path="/almuerzos" element={<Almuerzos />} />
          <Route path="/facturacion" element={<Facturacion />} />
          <Route path="/reportes" element={<Reportes />} />
          <Route path="/inventario" element={<Inventario />} />
          <Route path="/usuarios" element={<Usuarios />} />
          <Route path="/configuracion" element={<Configuracion />} />
        </Route>

        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
  )
}