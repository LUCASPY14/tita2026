import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, App } from 'antd'
import esES from 'antd/locale/es_ES'
import Login from './pages/Login'
import AppLayout from './components/Layout'
import Productos from './pages/Productos'
import Clientes from './pages/Clientes'
import Tarjetas from './pages/Tarjetas'
import Ventas from './pages/Ventas'
import Caja from './pages/Cajas'
import Compras from './pages/Compras'
import { useAuthStore } from './store/authStore'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />
}

function Dashboard() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Panel de Control</h2>
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="text-lg font-bold text-blue-800">Ventas Hoy</h3>
          <p className="text-3xl font-bold">Gs. 0</p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg">
          <h3 className="text-lg font-bold text-green-800">Clientes</h3>
          <p className="text-3xl font-bold">10</p>
        </div>
        <div className="bg-orange-50 p-4 rounded-lg">
          <h3 className="text-lg font-bold text-orange-800">Productos</h3>
          <p className="text-3xl font-bold">12</p>
        </div>
      </div>
    </div>
  )
}

export default function AppWrapper() {
  return (
    <ConfigProvider locale={esES} theme={{ token: { colorPrimary: '#16a34a' } }}>
      <App>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route element={<PrivateRoute><AppLayout /></PrivateRoute>}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/ventas" element={<Ventas />} />
              <Route path="/compras" element={<Compras />} />
              <Route path="/clientes" element={<Clientes />} />
              <Route path="/productos" element={<Productos />} />
              <Route path="/tarjetas" element={<Tarjetas />} />
              <Route path="/caja" element={<Caja />} />
            </Route>
            <Route path="*" element={<Navigate to="/dashboard" />} />
          </Routes>
        </BrowserRouter>
      </App>
    </ConfigProvider>
  )
}