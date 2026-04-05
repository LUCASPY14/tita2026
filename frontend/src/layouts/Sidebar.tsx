import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import clsx from 'clsx';
import { 
  LayoutDashboard, 
  TrendingUp,
  CreditCard, 
  ShoppingCart, 
  Users, 
  Package, 
  Utensils,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  Bell,
  FileText,
  UserCog,
  Shield,
  KeyRound,
  Warehouse,
  Tag,
  Truck,
  DollarSign,
  Stamp,
  Percent,
  Mail,
  Clock,
  Building2
} from 'lucide-react';
import { useUIStore } from '../store/uiStore';
import { useHasRole } from '../hooks/usePermissions';
import { useAuthContext } from '../contexts/AuthContext';
import { useNotificationsByRole } from '../hooks/useNotificationsByRole';

interface NavItem {
  name: string;
  path: string;
  icon: React.ElementType;
  badge?: number;
  adminOnly?: boolean;
  roles?: import('../services/auth.service').UserRole[];
  end?: boolean;
}

const BASE_NAVIGATION: NavItem[] = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard, end: true },
  { name: 'Recargas', path: '/recargas', icon: CreditCard, roles: ['admin', 'gerente', 'cajero', 'cobrador'] },
  { name: 'Punto de Venta', path: '/ventas', icon: ShoppingCart, end: true, roles: ['admin', 'gerente', 'cajero'] },
  { name: 'Gestión Ventas', path: '/ventas/gestion', icon: TrendingUp, roles: ['admin', 'gerente', 'cobrador'] },
  { name: 'Clientes', path: '/clientes', icon: Users, roles: ['admin', 'gerente', 'cobrador'] },
  { name: 'Productos', path: '/productos', icon: Package, roles: ['admin', 'gerente', 'supervisor'] },
  { name: 'Categorías', path: '/categorias', icon: Tag, roles: ['admin', 'gerente', 'supervisor'] },
  { name: 'Inventario', path: '/inventario', icon: Warehouse, roles: ['admin', 'gerente', 'supervisor'] },
  { name: 'Almuerzos', path: '/almuerzos', icon: Utensils },
  { name: 'Reportes', path: '/reportes', icon: BarChart3, roles: ['admin', 'gerente'] },
  { name: 'Notificaciones', path: '/notificaciones', icon: Bell },
  { name: 'Compras', path: '/compras', icon: FileText, roles: ['admin', 'gerente'] },
  { name: 'Proveedores', path: '/proveedores', icon: Truck, roles: ['admin', 'gerente'] },
  { name: 'Caja', path: '/caja', icon: DollarSign, roles: ['admin', 'gerente', 'cajero'] },
  { name: 'Facturación', path: '/facturacion', icon: FileText, roles: ['admin', 'cajero'] },
  { name: 'Timbrado', path: '/timbrado', icon: Stamp, adminOnly: true },
  { name: 'Datos de Empresa', path: '/configuracion/datos-empresa', icon: Building2, adminOnly: true },
  { name: 'Medios de Pago', path: '/configuracion/medios-pago', icon: CreditCard, adminOnly: true },
  { name: 'Impuestos', path: '/configuracion/impuestos', icon: Percent, adminOnly: true },
  { name: 'Plantillas Email', path: '/configuracion/plantillas-email', icon: Mail, adminOnly: true },
  { name: 'Tareas Programadas', path: '/configuracion/tareas-programadas', icon: Clock, adminOnly: true },
  { name: 'Configuración', path: '/configuracion', icon: Settings },
  { name: 'Usuarios', path: '/admin/usuarios', icon: UserCog, adminOnly: true },
  { name: 'Permisos', path: '/admin/permisos', icon: KeyRound, adminOnly: true },
  { name: 'Auditoría', path: '/admin/auditoria', icon: Shield, adminOnly: true },
];

const Sidebar: React.FC = () => {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const location = useLocation();
  const isAdmin = useHasRole(['admin']);
  const { user } = useAuthContext();
  const { resumen, resumenCriticidad } = useNotificationsByRole();

  const notifBadge = (resumen?.no_leidas || 0) + (resumenCriticidad.criticas + resumenCriticidad.altas);

  const navigation = BASE_NAVIGATION.map(item =>
    item.path === '/notificaciones' ? { ...item, badge: notifBadge } : item
  );

  // Filtrar navegación según permisos
  const filteredNavigation = navigation.filter(item => {
    if (item.adminOnly) {
      return isAdmin;
    }
    if (item.roles && item.roles.length > 0) {
      return user?.role ? (item.roles as string[]).includes(user.role) : false;
    }
    return true;
  });

  return (
    <>
      {/* Overlay para móviles */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/50 backdrop-blur-sm lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed left-0 top-0 z-30 h-screen bg-white border-r border-gray-200 transition-all duration-300 ease-in-out',
          'lg:z-10',
          sidebarOpen ? 'w-64' : 'w-16',
          'lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        {/* Header del Sidebar */}
        <div className={clsx(
          'flex items-center gap-3 border-b border-gray-200 px-4 transition-all',
          sidebarOpen ? 'h-16 justify-between' : 'h-16 justify-center'
        )}>
          {sidebarOpen && (
            <div className="flex items-center gap-3">
              <img 
                src="/assets/images/logo_tita.png" 
                alt="Cantina Tita" 
                className="h-10 w-10 object-contain"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
              <div className="flex flex-col">
                <h1 className="text-lg font-bold text-amber-600">Cantina Tita</h1>
                <p className="text-xs text-gray-500">Sistema de Gestión</p>
              </div>
            </div>
          )}
          
          <button
            onClick={toggleSidebar}
            className={clsx(
              'rounded-lg p-1.5 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700',
              !sidebarOpen && 'mx-auto'
            )}
          >
            {sidebarOpen ? (
              <ChevronLeft className="h-5 w-5" />
            ) : (
              <ChevronRight className="h-5 w-5" />
            )}
          </button>
        </div>

        {/* Navegación */}
        <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-4">
          {filteredNavigation.map((item) => {
            const isActive = item.end
              ? location.pathname === item.path
              : location.pathname === item.path || location.pathname.startsWith(item.path + '/');
            const Icon = item.icon;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.end}
                className={({ isActive: active }) =>
                  clsx(
                    'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
                    active || isActive
                      ? 'bg-amber-50 text-amber-600 shadow-sm'
                      : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900',
                    !sidebarOpen && 'justify-center'
                  )
                }
                title={!sidebarOpen ? item.name : undefined}
              >
                <Icon className={clsx(
                  'h-5 w-5 flex-shrink-0',
                  isActive ? 'text-amber-600' : 'text-gray-500 group-hover:text-gray-700'
                )} />
                
                {sidebarOpen && (
                  <>
                    <span className="flex-1">{item.name}</span>
                    {item.badge !== undefined && item.badge > 0 && (
                      <span className="rounded-full bg-red-500 px-2 py-0.5 text-xs font-semibold text-white">
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Footer del Sidebar */}
        {sidebarOpen && (
          <div className="border-t border-gray-200 p-4">
            <div className="rounded-lg bg-gradient-to-br from-amber-50 to-orange-50 p-3">
              <p className="text-xs font-semibold text-amber-900">Cantina Tita v1.0</p>
              <p className="mt-1 text-xs text-amber-700">© 2026 Todos los derechos reservados</p>
            </div>
          </div>
        )}
      </aside>
    </>
  );
};

export default Sidebar;
