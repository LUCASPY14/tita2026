import { useState, useRef, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuthStore } from '../store/authStore'
import LanguageSwitcher from './ui/LanguageSwitcher'
import {
  LayoutDashboard,
  UtensilsCrossed,
  Utensils,
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
  Zap,
  PanelLeftClose,
  PanelLeftOpen,
  ChevronDown,
  LogOut,
  Wallet,
  ChefHat,
  Leaf,
  type LucideIcon,
} from 'lucide-react'

// Todos los roles internos del sistema
const ALL_STAFF = ['ADMIN', 'CAJERO', 'SUPERVISOR', 'COBRADOR', 'COCINA']
const ADMIN_ONLY = ['ADMIN']
const POS_ROLES = ['ADMIN', 'CAJERO']
const REPORTING = ['ADMIN', 'SUPERVISOR', 'COBRADOR']
const OPS_ROLES = ['ADMIN', 'CAJERO', 'SUPERVISOR', 'COCINA']
const BILLING   = ['ADMIN', 'CAJERO', 'COBRADOR']
const TARJETAS  = ['ADMIN', 'CAJERO', 'SUPERVISOR', 'COBRADOR']
const CLIENTES  = ['ADMIN', 'CAJERO', 'SUPERVISOR', 'COBRADOR']

interface NavItem {
  path: string
  labelKey: string
  icon: LucideIcon
  roles: string[]
}

const navItems: NavItem[] = [
  { path: '/dashboard',    labelKey: 'nav.dashboard',    icon: LayoutDashboard, roles: ALL_STAFF },
  { path: '/modo-recreo',  labelKey: 'nav.modoRecreo',   icon: Zap,             roles: POS_ROLES },
  { path: '/almuerzos',    labelKey: 'nav.almuerzos',    icon: UtensilsCrossed, roles: OPS_ROLES },
  { path: '/comedor',      labelKey: 'nav.comedor',      icon: Utensils,        roles: OPS_ROLES },
  { path: '/menu-diario',  labelKey: 'nav.menuDiario',   icon: ChefHat,         roles: OPS_ROLES },
  { path: '/tarjetas',     labelKey: 'nav.tarjetas',     icon: CreditCard,      roles: TARJETAS },
  { path: '/carga-saldo',  labelKey: 'nav.cargaSaldo',   icon: Wallet,          roles: BILLING },
  { path: '/clientes',     labelKey: 'nav.clientes',     icon: Users,           roles: CLIENTES },
  { path: '/productos',    labelKey: 'nav.productos',    icon: Package,         roles: OPS_ROLES },
  { path: '/compras',      labelKey: 'nav.compras',      icon: Truck,           roles: ['ADMIN', 'CAJERO', 'SUPERVISOR'] },
  { path: '/caja',         labelKey: 'nav.caja',         icon: Banknote,        roles: ['ADMIN', 'CAJERO', 'SUPERVISOR'] },
  { path: '/facturacion',  labelKey: 'nav.facturacion',  icon: FileText,        roles: BILLING },
  { path: '/reportes',     labelKey: 'nav.reportes',     icon: BarChart2,       roles: REPORTING },
  { path: '/inventario',   labelKey: 'nav.inventario',   icon: Warehouse,       roles: ['ADMIN', 'SUPERVISOR'] },
  { path: '/alergenos',    labelKey: 'nav.alergenos',    icon: Leaf,            roles: OPS_ROLES },
  { path: '/usuarios',     labelKey: 'nav.usuarios',     icon: UserCog,         roles: ADMIN_ONLY },
  { path: '/configuracion',labelKey: 'nav.configuracion',icon: Settings,        roles: ADMIN_ONLY },
]

export default function AppLayout() {
  const { t } = useTranslation()
  const [collapsed, setCollapsed] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const userMenuRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const initials = (user?.nombre?.[0] ?? 'U').toUpperCase()
  const visibleNav = navItems.filter(item => item.roles.includes(user?.rol ?? ''))

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  useEffect(() => {
    if (!userMenuOpen) return
    const handleClickOutside = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [userMenuOpen])

  return (
    <div className="flex min-h-screen bg-slate-50">

      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <aside
        className={[
          'bg-white border-r border-slate-200 flex flex-col shrink-0',
          'transition-all duration-200 ease-in-out',
          collapsed ? 'w-16' : 'w-64',
        ].join(' ')}
      >
        {/* Logo */}
        <div
          className={[
            'flex items-center h-14 border-b border-slate-200 shrink-0',
            collapsed ? 'justify-center px-3' : 'px-4 gap-2.5',
          ].join(' ')}
        >
          <img
            src="/logo_tita.png"
            alt="Cantina Tita"
            className={collapsed ? 'h-7 w-auto' : 'h-9 w-auto'}
          />
          {!collapsed && (
            <span className="text-slate-700 font-semibold text-base tracking-tight truncate">
              {t('layout.systemName')}
            </span>
          )}
        </div>

        {/* Nav */}
        <nav role="navigation" aria-label={t('layout.mainMenu')} className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
          {visibleNav.map(({ path, labelKey, icon: Icon }) => {
            const label = t(labelKey)
            const active = location.pathname === path || location.pathname.startsWith(path + '/')
            return (
              <button
                type="button"
                key={path}
                onClick={() => navigate(path)}
                title={collapsed ? label : undefined}
                aria-label={collapsed ? label : undefined}
                aria-current={active ? 'page' : undefined}
                className={[
                  'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-base font-medium',
                  'transition-all duration-150 cursor-pointer group',
                  collapsed ? 'justify-center' : '',
                  active
                    ? 'bg-green-50 text-green-700'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-800',
                ].join(' ')}
              >
                <Icon
                  className={[
                    'w-[18px] h-[18px] shrink-0 transition-colors',
                    active
                      ? 'text-green-600'
                      : 'text-slate-400 group-hover:text-slate-600',
                  ].join(' ')}
                />
                {!collapsed && (
                  <>
                    <span className="truncate flex-1 text-left">{label}</span>
                    {active && (
                      <span className="w-1.5 h-1.5 rounded-full bg-green-500 shrink-0" />
                    )}
                  </>
                )}
              </button>
            )
          })}
        </nav>

        {/* Collapse toggle */}
        <div className="p-2 border-t border-slate-200 shrink-0">
          <button
            type="button"
            onClick={() => setCollapsed(!collapsed)}
            className={[
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-base',
              'text-slate-400 hover:bg-slate-100 hover:text-slate-600',
              'transition-colors duration-150 cursor-pointer',
              collapsed ? 'justify-center' : '',
            ].join(' ')}
            title={collapsed ? t('layout.expandMenu') : t('layout.collapseMenu')}
            aria-label={collapsed ? t('layout.expandMenu') : t('layout.collapseMenu')}
          >
            {collapsed ? (
              <PanelLeftOpen className="w-[18px] h-[18px]" />
            ) : (
              <>
                <PanelLeftClose className="w-[18px] h-[18px]" />
                <span className="text-base">{t('layout.collapse')}</span>
              </>
            )}
          </button>
        </div>
      </aside>

      {/* ── Main column ─────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Header */}
        <header className="h-16 bg-white border-b border-slate-200/80 px-4 flex items-center justify-end gap-3 shrink-0">
          <LanguageSwitcher />
          <div ref={userMenuRef} className="relative">
            <button
              type="button"
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              aria-expanded={userMenuOpen}
              aria-haspopup="menu"
              aria-label={t('layout.userMenu')}
              className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl hover:bg-slate-50 transition-colors cursor-pointer"
            >
              <span className="w-8 h-8 bg-green-100 text-green-700 rounded-full flex items-center justify-center text-sm font-bold shrink-0">
                {initials}
              </span>
              <div className="hidden sm:block text-left">
                <p className="text-base font-medium text-slate-700 leading-none">
                  {user?.nombre || t('layout.defaultUser')}
                </p>
                <p className="text-sm text-slate-500 mt-0.5 leading-none">
                  {t(`role.${user?.rol}`, { defaultValue: user?.rol ?? '' })}
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
              <div role="menu" className="absolute right-0 mt-1.5 w-48 bg-white border border-slate-200 rounded-xl shadow-lg shadow-slate-200/60 z-50 overflow-hidden">
                <div className="px-4 py-3 border-b border-slate-100">
                  <p className="text-base font-semibold text-slate-800 truncate">
                    {user?.nombre} {user?.apellido}
                  </p>
                  <p className="text-sm text-slate-500 mt-0.5 truncate">{user?.email}</p>
                </div>
                <button
                  type="button"
                  role="menuitem"
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2.5 px-4 py-2.5 text-base text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  {t('layout.logout')}
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
