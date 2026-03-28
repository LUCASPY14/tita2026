import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Menu, 
  Bell, 
  User, 
  LogOut, 
  Settings, 
  ChevronDown,
  Search,
  Shield,
  AlertTriangle
} from 'lucide-react';
import { useAuthContext } from '../contexts/AuthContext';
import { useUIStore } from '../store/uiStore';
import { useNotificationsByRole } from '../hooks/useNotificationsByRole';
import clsx from 'clsx';
import { Avatar, Badge, SearchBar } from '../components/common';
import NotificationStreamIndicator from '../components/common/NotificationStreamIndicator';
import PWAStatus from '../components/common/PWAStatus';

const Header: React.FC = () => {
  const { user, logout } = useAuthContext();
  const { toggleSidebar } = useUIStore();
  const navigate = useNavigate();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  
  // Hook para notificaciones filtradas por rol
  const { 
    notificaciones, 
    alertas, 
    resumen, 
    resumenCriticidad,
    marcarComoLeida 
  } = useNotificationsByRole();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Calcular notificaciones no leídas (solo notificaciones normales + alertas pendientes)
  const unreadCount = (resumen?.no_leidas || 0) + (resumenCriticidad.criticas + resumenCriticidad.altas);

  // Combinar notificaciones y alertas críticas para el dropdown
  const notificacionesCombinadas = [
    ...alertas.slice(0, 3).map(alerta => ({
      id: `alerta-${alerta.id_alerta}`,
      title: alerta.tipo,
      message: alerta.mensaje,
      time: new Date(alerta.fecha_creacion).toLocaleDateString('es-PY'),
      read: alerta.estado !== 'Pendiente',
      type: alerta.criticidad === 'critico' ? 'error' as const : 
            alerta.criticidad === 'alto' ? 'warning' as const : 'info' as const,
      isAlert: true,
    })),
    ...notificaciones.slice(0, 5).map(notif => ({
      id: `notif-${notif.id_notificacion}`,
      title: notif.tipo,
      message: notif.mensaje,
      time: new Date(notif.fecha_envio).toLocaleDateString('es-PY'),
      read: notif.leida,
      type: 'info' as const,
      isAlert: false,
      notifId: notif.id_notificacion,
    }))
  ];

  const handleNotificationClick = async (item: any) => {
    if (!item.isAlert && !item.read) {
      try {
        await marcarComoLeida(item.notifId);
      } catch (error) {
        console.error('Error marcando notificación:', error);
      }
    }
  };

  // Mapeo de roles a colores y etiquetas
  const roleConfig: Record<import('../services/auth.service').UserRole, { label: string; color: string }> = {
    admin: { label: 'Administrador', color: 'bg-purple-100 text-purple-700' },
    gerente: { label: 'Gerente', color: 'bg-blue-100 text-blue-700' },
    supervisor: { label: 'Supervisor', color: 'bg-indigo-100 text-indigo-700' },
    cajero: { label: 'Cajero', color: 'bg-green-100 text-green-700' },
    cobrador: { label: 'Cobrador', color: 'bg-orange-100 text-orange-700' },
    empleado: { label: 'Empleado', color: 'bg-gray-100 text-gray-700' },
  };

  const currentRole = user?.role ? roleConfig[user.role] : null;

  const notificationColors = {
    info: 'bg-blue-100 text-blue-600',
    success: 'bg-green-100 text-green-600',
    warning: 'bg-yellow-100 text-yellow-600',
    error: 'bg-red-100 text-red-600',
  };

  return (
    <header className="sticky top-0 z-10 bg-white border-b border-gray-200 shadow-sm">
      <div className="flex h-16 items-center justify-between gap-4 px-4 lg:px-6">
        {/* Left Section */}
        <div className="flex items-center gap-4">
          {/* Menu button - visible always, controls sidebar */}
          <button
            onClick={toggleSidebar}
            className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700"
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* Search Bar - Hidden on mobile */}
          <div className="hidden md:block md:w-64 lg:w-96">
            <SearchBar
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              placeholder="Buscar productos, clientes..."
              searchSize="sm"
            />
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-2">
          {/* Search icon for mobile */}
          <button className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 md:hidden">
            <Search className="h-5 w-5" />
          </button>

          {/* PWA Status - desktop only */}
          <PWAStatus className="hidden lg:flex" />

          {/* Stream Connection Status */}
          <NotificationStreamIndicator className="hidden md:flex" />

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700"
            >
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-xs font-semibold text-white">
                  {unreadCount}
                </span>
              )}
            </button>

            {/* Notifications Dropdown */}
            {showNotifications && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowNotifications(false)}
                />
                <div className="absolute right-0 top-full z-20 mt-2 w-80 rounded-lg border border-gray-200 bg-white shadow-lg">
                  <div className="border-b border-gray-200 px-4 py-3">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-gray-900">Notificaciones</h3>
                      {unreadCount > 0 && (
                        <Badge variant="danger" size="sm">
                          {unreadCount} nuevas
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    {notificacionesCombinadas.length === 0 ? (
                      <div className="px-4 py-8 text-center text-sm text-gray-500">
                        No hay notificaciones para tu rol
                      </div>
                    ) : (
                      notificacionesCombinadas.map((notification) => (
                        <div
                          key={notification.id}
                          onClick={() => handleNotificationClick(notification)}
                          className={clsx(
                            'border-b border-gray-100 px-4 py-3 transition-colors hover:bg-gray-50 cursor-pointer',
                            !notification.read && 'bg-blue-50/50'
                          )}
                        >
                          <div className="flex items-start gap-3">
                            <div className={clsx(
                              'mt-1 rounded-full p-1.5',
                              notificationColors[notification.type]
                            )}>
                              {notification.isAlert ? (
                                <AlertTriangle className="h-3 w-3" />
                              ) : (
                                <Bell className="h-3 w-3" />
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <p className="text-sm font-medium text-gray-900">
                                  {notification.title}
                                </p>
                                {notification.isAlert && (
                                  <Badge variant="danger" size="sm">Alerta</Badge>
                                )}
                              </div>
                              <p className="mt-0.5 text-sm text-gray-600 line-clamp-2">
                                {notification.message}
                              </p>
                              <p className="mt-1 text-xs text-gray-500">
                                {notification.time}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                  <div className="border-t border-gray-200 px-4 py-2">
                    <button 
                      onClick={() => {
                        navigate('/notificaciones');
                        setShowNotifications(false);
                      }}
                      className="w-full text-center text-sm font-medium text-amber-600 hover:text-amber-700"
                    >
                      Ver todas las notificaciones
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 rounded-lg px-3 py-2 transition-colors hover:bg-gray-100"
            >
              <Avatar
                name={user?.username || 'Usuario'}
                size="sm"
                status="online"
              />
              <div className="hidden text-left lg:block">
                <p className="text-sm font-medium text-gray-900 flex items-center gap-1">
                  {user?.username || 'Usuario'}
                  {user?.role === 'admin' && (
                    <Shield className="h-3 w-3 text-purple-600" />
                  )}
                </p>
                <p className="text-xs text-gray-500">
                  {currentRole?.label || 'Sin rol'}
                </p>
              </div>
              <ChevronDown className="hidden h-4 w-4 text-gray-500 lg:block" />
            </button>

            {/* User Menu Dropdown */}
            {showUserMenu && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowUserMenu(false)}
                />
                <div className="absolute right-0 top-full z-20 mt-2 w-64 rounded-lg border border-gray-200 bg-white shadow-lg">
                  <div className="border-b border-gray-200 px-4 py-3">
                    <p className="text-sm font-medium text-gray-900 flex items-center gap-2">
                      {user?.username || 'Usuario'}
                      {user?.role === 'admin' && (
                        <Shield className="h-4 w-4 text-purple-600" />
                      )}
                    </p>
                    <p className="mt-0.5 text-xs text-gray-500">
                      {user?.email || 'usuario@cantina.com'}
                    </p>
                    {currentRole && (
                      <div className="mt-2">
                        <span className={clsx(
                          'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
                          currentRole.color
                        )}>
                          {currentRole.label}
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="py-2">
                    <button
                      onClick={() => {
                        navigate('/perfil');
                        setShowUserMenu(false);
                      }}
                      className="flex w-full items-center gap-2 px-4 py-2 text-sm text-gray-700 transition-colors hover:bg-gray-50"
                    >
                      <User className="h-4 w-4" />
                      Mi Perfil
                    </button>
                    <button
                      onClick={() => {
                        navigate('/configuracion');
                        setShowUserMenu(false);
                      }}
                      className="flex w-full items-center gap-2 px-4 py-2 text-sm text-gray-700 transition-colors hover:bg-gray-50"
                    >
                      <Settings className="h-4 w-4" />
                      Configuración
                    </button>
                  </div>
                  <div className="border-t border-gray-200 py-2">
                    <button
                      onClick={handleLogout}
                      className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 transition-colors hover:bg-red-50"
                    >
                      <LogOut className="h-4 w-4" />
                      Cerrar Sesión
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
