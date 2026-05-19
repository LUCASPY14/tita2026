import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { UtensilsCrossed, Home, Bell, LogOut } from 'lucide-react'

const navItems = [
  { path: '/portal', label: 'Inicio', icon: Home, exact: true },
  { path: '/portal/notificaciones', label: 'Notificaciones', icon: Bell, exact: false },
]

export default function PortalLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 bg-green-500 rounded-lg flex items-center justify-center shrink-0">
              <UtensilsCrossed className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-800 leading-none">Cantina Tita</p>
              <p className="text-xs text-slate-400 leading-none mt-0.5 hidden sm:block">Portal de Padres</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-600 hidden sm:block">{user?.nombre}</span>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 text-xs text-red-500 hover:text-red-700 border border-red-200 rounded-lg px-3 py-1.5 hover:bg-red-50 transition-colors cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              Salir
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 max-w-2xl mx-auto w-full px-4 py-6 pb-24">
        <Outlet />
      </main>

      {/* Bottom nav */}
      <nav className="bg-white border-t border-slate-200 fixed bottom-0 left-0 right-0 z-10">
        <div className="max-w-2xl mx-auto flex">
          {navItems.map(({ path, label, icon: Icon, exact }) => {
            const active = exact
              ? location.pathname === path
              : location.pathname.startsWith(path)
            return (
              <button
                key={path}
                onClick={() => navigate(path)}
                className={[
                  'flex-1 flex flex-col items-center gap-1 py-3 text-xs font-medium',
                  'transition-colors cursor-pointer relative',
                  active ? 'text-green-600' : 'text-slate-400 hover:text-slate-600',
                ].join(' ')}
              >
                <Icon className="w-5 h-5" />
                <span>{label}</span>
                {active && (
                  <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-green-500 rounded-t" />
                )}
              </button>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
