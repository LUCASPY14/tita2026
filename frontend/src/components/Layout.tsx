import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import {
  LayoutDashboard,
  ShoppingCart,
  UtensilsCrossed,
  CreditCard,
  Users,
  Package,
  Truck,
  Banknote,
  FileText,
  BarChart2,
  Warehouse,
  UserCog,
  Settings,
  PanelLeftClose,
  PanelLeftOpen,
  ChevronDown,
  LogOut,
  type LucideIcon,
} from 'lucide-react'

interface NavItem {
  path: string
  label: string
  icon: LucideIcon
}

const navItems: NavItem[] = [
  { path: '/dashboard',   label: 'Dashboard',   icon: LayoutDashboard },
  { path: '/ventas',      label: 'Ventas',       icon: ShoppingCart },
  { path: '/almuerzos',   label: 'Almuerzos',    icon: UtensilsCrossed },
  { path: '/tarjetas',    label: 'Tarjetas',     icon: CreditCard },
  { path: '/clientes',    label: 'Clientes',     icon: Users },
  { path: '/productos',   label: 'Productos',    icon: Package },
  { path: '/compras',     label: 'Compras',      icon: Truck },
  { path: '/caja',        label: 'Caja',         icon: Banknote },
  { path: '/facturacion',  label: 'Facturación',  icon: FileText },
  { path: '/reportes',     label: 'Reportes',     icon: BarChart2 },
  { path: '/inventario',   label: 'Inventario',   icon: Warehouse },
  { path: '/usuarios',     label: 'Usuarios',     icon: UserCog },
  { path: '/configuracion',label: 'Configuración',icon: Settings },
]

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const initials = (user?.nombre?.[0] ?? 'U').toUpperCase()

  return (
    <div className="flex min-h-screen bg-slate-50">

      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <aside
        className={[
          'bg-slate-950 text-white flex flex-col shrink-0',
          'transition-all duration-200 ease-in-out',
          collapsed ? 'w-16' : 'w-60',
        ].join(' ')}
      >
        {/* Logo */}
        <div
          className={[
            'flex items-center h-14 border-b border-white/5 shrink-0',
            collapsed ? 'justify-center px-3' : 'px-5 gap-2.5',
          ].join(' ')}
        >
          <div className="w-7 h-7 bg-green-500 rounded-lg flex items-center justify-center shrink-0">
            <span className="text-white font-black text-xs leading-none">CT</span>
          </div>
          {!collapsed && (
            <span className="text-white/90 font-semibold text-sm tracking-tight truncate">
              Cantina Tita
            </span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
          {navItems.map(({ path, label, icon: Icon }) => {
            const active = location.pathname === path
            return (
              <button
                key={path}
                onClick={() => navigate(path)}
                title={collapsed ? label : undefined}
                className={[
                  'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium',
                  'transition-all duration-150 cursor-pointer group',
                  collapsed ? 'justify-center' : '',
                  active
                    ? 'bg-green-500/15 text-green-400'
                    : 'text-slate-400 hover:bg-white/5 hover:text-slate-200',
                ].join(' ')}
              >
                <Icon
                  className={[
                    'w-[18px] h-[18px] shrink-0 transition-colors',
                    active
                      ? 'text-green-400'
                      : 'text-slate-500 group-hover:text-slate-300',
                  ].join(' ')}
                />
                {!collapsed && (
                  <>
                    <span className="truncate flex-1 text-left">{label}</span>
                    {active && (
                      <span className="w-1.5 h-1.5 rounded-full bg-green-400 shrink-0" />
                    )}
                  </>
                )}
              </button>
            )
          })}
        </nav>

        {/* Collapse toggle */}
        <div className="p-2 border-t border-white/5 shrink-0">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className={[
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm',
              'text-slate-500 hover:bg-white/5 hover:text-slate-300',
              'transition-colors duration-150 cursor-pointer',
              collapsed ? 'justify-center' : '',
            ].join(' ')}
            title={collapsed ? 'Expandir menú' : 'Colapsar menú'}
          >
            {collapsed ? (
              <PanelLeftOpen className="w-[18px] h-[18px]" />
            ) : (
              <>
                <PanelLeftClose className="w-[18px] h-[18px]" />
                <span className="text-xs">Colapsar</span>
              </>
            )}
          </button>
        </div>
      </aside>

      {/* ── Main column ─────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Header */}
        <header className="h-14 bg-white border-b border-slate-200/80 px-4 flex items-center justify-end shrink-0">
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer"
            >
              <span className="w-7 h-7 bg-green-100 text-green-700 rounded-full flex items-center justify-center text-xs font-bold shrink-0">
                {initials}
              </span>
              <div className="hidden sm:block text-left">
                <p className="text-sm font-medium text-slate-700 leading-none">
                  {user?.nombre || 'Usuario'}
                </p>
                <p className="text-xs text-slate-400 mt-0.5 leading-none">
                  {user?.rol || ''}
                </p>
              </div>
              <ChevronDown
                className={[
                  'w-3.5 h-3.5 text-slate-400 transition-transform duration-150',
                  userMenuOpen ? 'rotate-180' : '',
                ].join(' ')}
              />
            </button>

            {userMenuOpen && (
              <div className="absolute right-0 mt-1.5 w-48 bg-white border border-slate-200 rounded-xl shadow-lg shadow-slate-200/60 z-50 overflow-hidden">
                <div className="px-4 py-3 border-b border-slate-100">
                  <p className="text-sm font-semibold text-slate-800 truncate">
                    {user?.nombre} {user?.apellido}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5 truncate">{user?.email}</p>
                </div>
                <button
                  onClick={() => { setUserMenuOpen(false); logout() }}
                  className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  Cerrar sesión
                </button>
              </div>
            )}
          </div>
        </header>

        {/* Content — cada página maneja su propio padding */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
