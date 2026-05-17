import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: '▦' },
  { path: '/ventas', label: 'Ventas', icon: '🛒' },
  { path: '/almuerzos', label: 'Almuerzos', icon: '🍽' },
  { path: '/tarjetas', label: 'Tarjetas', icon: '💳' },
  { path: '/clientes', label: 'Clientes', icon: '👥' },
  { path: '/productos', label: 'Productos', icon: '📦' },
  { path: '/compras', label: 'Compras', icon: '🚚' },
  { path: '/caja', label: 'Caja', icon: '🏧' },
]

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  return (
    <div className="flex min-h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className={`bg-gray-900 text-white flex flex-col transition-all duration-200 ${collapsed ? 'w-16' : 'w-56'}`}>
        <div className={`p-4 border-b border-gray-700 font-bold text-center text-green-400 text-lg truncate ${collapsed ? 'px-2' : ''}`}>
          {collapsed ? 'CT' : 'Cantina Tita'}
        </div>
        <nav className="flex-1 py-2">
          {navItems.map((item) => {
            const active = location.pathname === item.path
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center gap-3 px-4 py-3 text-sm transition-colors cursor-pointer ${
                  active
                    ? 'bg-green-700 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                } ${collapsed ? 'justify-center px-2' : ''}`}
                title={collapsed ? item.label : undefined}
              >
                <span className="text-lg">{item.icon}</span>
                {!collapsed && <span>{item.label}</span>}
              </button>
            )
          })}
        </nav>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="text-gray-500 hover:text-gray-700 text-xl cursor-pointer"
          >
            {collapsed ? '☰' : '✕'}
          </button>
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900 cursor-pointer"
            >
              <span className="w-8 h-8 bg-green-100 text-green-700 rounded-full flex items-center justify-center font-bold">
                {(user?.nombre?.[0] || 'U').toUpperCase()}
              </span>
              <span>{user?.nombre || 'Usuario'}</span>
              <span className="text-gray-400">▾</span>
            </button>
            {userMenuOpen && (
              <div className="absolute right-0 mt-1 w-40 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                <button
                  onClick={() => { setUserMenuOpen(false); logout() }}
                  className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 cursor-pointer"
                >
                  Cerrar sesion
                </button>
              </div>
            )}
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-6 overflow-auto">
          <div className="bg-white rounded-lg p-6 min-h-full shadow-sm">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
