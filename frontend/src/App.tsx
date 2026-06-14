import { Component, lazy, Suspense, useEffect, type ReactNode } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import AppLayout from './components/Layout'
import PortalLayout from './components/PortalLayout'
import Spinner from './components/ui/Spinner'
import { useAuthStore } from './store/authStore'

// ── Eager: rutas públicas y estructurales ─────────────────────────────────────
import Login from './pages/Login'
import RecuperarPassword from './pages/RecuperarPassword'
import RestablecerPassword from './pages/RestablecerPassword'
import PortalLogin from './pages/portal/Login'
import PortalResetPassword from './pages/portal/ResetPassword'

// ── Lazy: sección de gestión (cargadas al navegar) ────────────────────────────
const Dashboard         = lazy(() => import('./pages/Dashboard'))
const Productos         = lazy(() => import('./pages/Productos'))
const Clientes          = lazy(() => import('./pages/Clientes'))
const Tarjetas          = lazy(() => import('./pages/Tarjetas'))
const Caja              = lazy(() => import('./pages/Cajas'))
const Compras           = lazy(() => import('./pages/Compras'))
const Almuerzos         = lazy(() => import('./pages/Almuerzos'))
const Facturacion       = lazy(() => import('./pages/Facturacion'))
const Reportes          = lazy(() => import('./pages/Reportes'))
const Inventario        = lazy(() => import('./pages/Inventario'))
const Usuarios          = lazy(() => import('./pages/Usuarios'))
const Configuracion     = lazy(() => import('./pages/Configuracion'))
const CargaSaldo        = lazy(() => import('./pages/CargaSaldo'))
const Comedor           = lazy(() => import('./pages/Comedor'))
const ModoRecreo        = lazy(() => import('./pages/ModoRecreo'))
const MenuDiario        = lazy(() => import('./pages/MenuDiario'))
const Alergenos         = lazy(() => import('./pages/Alergenos'))
const Integraciones     = lazy(() => import('./pages/Integraciones'))

// ── Lazy: portal de padres ────────────────────────────────────────────────────
const PortalDashboard      = lazy(() => import('./pages/portal/Dashboard'))
const PortalNotificaciones = lazy(() => import('./pages/portal/Notificaciones'))
const PortalHistorial      = lazy(() => import('./pages/portal/Historial'))
const PortalFacturas       = lazy(() => import('./pages/portal/Facturas'))
const PortalCargaSaldo     = lazy(() => import('./pages/portal/CargaSaldo'))

// ── Fallback de carga ─────────────────────────────────────────────────────────
function PageLoader() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <Spinner />
    </div>
  )
}

// ── Error boundary ────────────────────────────────────────────────────────────
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

// ── Guards ────────────────────────────────────────────────────────────────────
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

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  const { loadUser } = useAuthStore()

  useEffect(() => { loadUser() }, [])

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthMonitor />
        <Toaster position="top-right" toastOptions={{ duration: 3000 }} />
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Portal padres */}
            <Route path="/portal/login"          element={<PortalLogin />} />
            <Route path="/portal/reset-password" element={<PortalResetPassword />} />
            <Route path="/portal" element={
              <PrivateRoute roles={['CLIENTE_WEB']}>
                <PortalLayout />
              </PrivateRoute>
            }>
              <Route index                        element={<PortalDashboard />} />
              <Route path="carga-saldo"           element={<PortalCargaSaldo />} />
              <Route path="notificaciones"        element={<PortalNotificaciones />} />
              <Route path="historial"             element={<PortalHistorial />} />
              <Route path="facturas"              element={<PortalFacturas />} />
            </Route>

            {/* Sistema de gestión */}
            <Route path="/login"              element={<Login />} />
            <Route path="/recuperar-password" element={<RecuperarPassword />} />
            <Route path="/reset-password"     element={<RestablecerPassword />} />
            <Route element={
              <PrivateRoute roles={['ADMIN', 'CAJERO', 'SUPERVISOR', 'COBRADOR', 'COCINA']}>
                <AppLayout />
              </PrivateRoute>
            }>
              <Route path="/dashboard"     element={<Dashboard />} />
              <Route path="/ventas"        element={<Navigate to="/modo-recreo" />} />
              <Route path="/almuerzos"     element={<Almuerzos />} />
              <Route path="/comedor"       element={<Comedor />} />
              <Route path="/menu-diario"   element={<MenuDiario />} />
              <Route path="/tarjetas"      element={<Tarjetas />} />
              <Route path="/carga-saldo"   element={<CargaSaldo />} />
              <Route path="/clientes"      element={<Clientes />} />
              <Route path="/productos"     element={<Productos />} />
              <Route path="/compras"       element={<Compras />} />
              <Route path="/caja"          element={<Caja />} />
              <Route path="/facturacion"   element={<Facturacion />} />
              <Route path="/alergenos"     element={<Alergenos />} />
              <Route path="/reportes" element={
                <PrivateRoute roles={['ADMIN', 'SUPERVISOR', 'COBRADOR']}>
                  <Reportes />
                </PrivateRoute>
              } />
              <Route path="/inventario" element={
                <PrivateRoute roles={['ADMIN', 'SUPERVISOR']}>
                  <Inventario />
                </PrivateRoute>
              } />
              <Route path="/usuarios" element={
                <PrivateRoute roles={['ADMIN']}>
                  <Usuarios />
                </PrivateRoute>
              } />
              <Route path="/configuracion" element={
                <PrivateRoute roles={['ADMIN']}>
                  <Configuracion />
                </PrivateRoute>
              } />
              <Route path="/integraciones" element={
                <PrivateRoute roles={['ADMIN']}>
                  <Integraciones />
                </PrivateRoute>
              } />
            </Route>

            {/* Modo Recreo — overlay full-screen, fuera del AppLayout */}
            <Route path="/modo-recreo" element={
              <PrivateRoute roles={['ADMIN', 'CAJERO']}>
                <ModoRecreo />
              </PrivateRoute>
            } />

            <Route path="*" element={<Navigate to="/login" />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
