import { useEffect, useState } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useNotificaciones } from '../hooks/useNotificaciones'
import { useDatosEmpresaPublico } from '../hooks/useDatosEmpresaPublico'
import { formatTelefonoPy } from '../utils/formatTelefonoPy'
import { Home, Bell, LogOut, FileText, Wallet, Download, Mail, Phone } from 'lucide-react'
import LogoSinFondo from './LogoSinFondo'

const navItems = [
  { path: '/portal',                 label: 'Inicio',    icon: Home,    exact: true  },
  { path: '/portal/carga-saldo',    label: 'Recargar',  icon: Wallet,  exact: false },
  { path: '/portal/facturas',       label: 'Facturas',  icon: FileText,exact: false },
  { path: '/portal/notificaciones', label: 'Alertas',   icon: Bell,    exact: false },
]

export default function PortalLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const { unreadCount, clearUnread } = useNotificaciones()
  const empresa = useDatosEmpresaPublico()
  const [installPrompt, setInstallPrompt] = useState<Event | null>(
    () => (window as unknown as Record<string, unknown>).__pwaPrompt as Event ?? null
  )

  // Apuntar al manifest del portal mientras el usuario está en /portal
  useEffect(() => {
    const link = document.querySelector<HTMLLinkElement>('link[rel="manifest"]')
    const prev = link?.getAttribute('href') ?? '/manifest.webmanifest'
    link?.setAttribute('href', '/portal-manifest.webmanifest')
    return () => { link?.setAttribute('href', prev) }
  }, [])

  // Escuchar el prompt si llegó después del montaje
  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault()
      setInstallPrompt(e)
      ;(window as unknown as Record<string, unknown>).__pwaPrompt = e
    }
    window.addEventListener('beforeinstallprompt', handler)
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  const handleInstall = async () => {
    if (!installPrompt) return
    const prompt = installPrompt as Event & { prompt(): void; userChoice: Promise<{ outcome: string }> }
    prompt.prompt()
    const { outcome } = await prompt.userChoice
    if (outcome === 'accepted') {
      setInstallPrompt(null)
      ;(window as unknown as Record<string, unknown>).__pwaPrompt = null
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <LogoSinFondo
              src="/logo-cantina.png"
              alt="Cantina Tita"
              className="h-12 w-auto mix-blend-multiply"
            />
            <p className="text-xs text-slate-400 hidden sm:block">Portal de Padres</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-600 hidden sm:block">{user?.nombre}</span>
            {installPrompt && (
              <button
                type="button"
                onClick={handleInstall}
                title="Instalar app en este dispositivo"
                className="flex items-center gap-1.5 text-xs text-orange-500 hover:text-orange-700 border border-orange-200 rounded-lg px-3 py-1.5 hover:bg-orange-50 transition-colors cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Instalar</span>
              </button>
            )}
            <button
              type="button"
              onClick={handleLogout}
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

        {/* Footer — Términos y contacto, visible en todas las páginas del portal */}
        <footer className="mt-10 pt-4 border-t border-slate-200 flex flex-col items-center gap-2 text-xs text-slate-400">
          <Link to="/portal/terminos" className="hover:text-slate-600 hover:underline">
            Términos y Condiciones
          </Link>
          {(empresa?.email || empresa?.telefono) && (
            <div className="flex items-center gap-4">
              {empresa.email && (
                <a href={`mailto:${empresa.email}`} className="flex items-center gap-1 hover:text-slate-600">
                  <Mail className="w-3 h-3" /> {empresa.email}
                </a>
              )}
              {empresa.telefono && (
                <a href={`tel:${empresa.telefono}`} className="flex items-center gap-1 hover:text-slate-600">
                  <Phone className="w-3 h-3" /> {formatTelefonoPy(empresa.telefono)}
                </a>
              )}
            </div>
          )}
        </footer>
      </main>

      {/* Bottom nav */}
      <nav className="bg-white border-t border-slate-200 fixed bottom-0 left-0 right-0 z-10">
        <div className="max-w-2xl mx-auto flex">
          {navItems.map(({ path, label, icon: Icon, exact }) => {
            const active = exact
              ? location.pathname === path
              : location.pathname.startsWith(path)
            const isBell = path === '/portal/notificaciones'
            return (
              <button
                type="button"
                key={path}
                onClick={() => {
                  if (isBell) clearUnread()
                  navigate(path)
                }}
                aria-current={active ? 'page' : undefined}
                className={[
                  'flex-1 flex flex-col items-center gap-1 py-3 text-xs font-medium',
                  'transition-colors cursor-pointer relative',
                  active ? 'text-green-600' : 'text-slate-400 hover:text-slate-600',
                ].join(' ')}
              >
                <span className="relative">
                  <Icon className="w-5 h-5" />
                  {isBell && unreadCount > 0 && (
                    <span className="absolute -top-1.5 -right-2 min-w-[16px] h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center px-0.5 leading-none">
                      {unreadCount > 99 ? '99+' : unreadCount}
                    </span>
                  )}
                </span>
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
