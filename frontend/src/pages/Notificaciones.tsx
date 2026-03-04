/**
 * Página de Notificaciones
 * Centro de notificaciones multicanal del sistema con filtrado por rol
 */

import React, { useState } from 'react';
import { Bell, AlertTriangle, Settings, Shield, Info } from 'lucide-react';
import {
  ListaNotificaciones,
  AlertasSistema,
  Preferencias,
} from '../components/notificaciones';
import { useAuthContext } from '../contexts/AuthContext';
import { useNotificationsByRole } from '../hooks/useNotificationsByRole';

type TabType = 'notificaciones' | 'alertas' | 'preferencias';

const Notificaciones: React.FC = () => {
  const { user } = useAuthContext();
  const [tabActiva, setTabActiva] = useState<TabType>('notificaciones');
  
  // Hook para notificaciones filtradas por rol
  const { 
    resumen, 
    resumenCriticidad, 
    cargando, 
    refrescar 
  } = useNotificationsByRole();

  // Obtener id_usuario del contexto de autenticación
  const idUsuario = user?.id || 1;

  const tabs = [
    {
      id: 'notificaciones' as const,
      nombre: 'Notificaciones',
      icon: Bell,
      badge: resumen?.no_leidas || 0,
    },
    {
      id: 'alertas' as const,
      nombre: 'Alertas del Sistema',
      icon: AlertTriangle,
      badge: (resumenCriticidad.criticas + resumenCriticidad.altas) || 0,
    },
    {
      id: 'preferencias' as const,
      nombre: 'Preferencias',
      icon: Settings,
      badge: 0,
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Centro de Notificaciones
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Gestiona tus notificaciones, alertas y preferencias del sistema
        </p>
      </div>

      {/* Info de filtrado por rol */}
      {user && (
        <div className="mb-4 rounded-lg bg-blue-50 border border-blue-200 p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-blue-900 flex items-center gap-2">
                <span>Vista personalizada para tu rol</span>
                {user.role === 'admin' && <Shield className="h-4 w-4" />}
              </h3>
              <p className="mt-1 text-sm text-blue-700">
                {user.role === 'admin' && 
                  'Como administrador, ves todas las notificaciones y alertas del sistema.'}
                {user.role === 'gerente' && 
                  'Como gerente, ves notificaciones operativas y alertas de gestión.'}
                {user.role === 'cajero' && 
                  'Como cajero, ves notificaciones de ventas y transacciones.'}
                {user.role === 'empleado' && 
                  'Como empleado, ves notificaciones generales del sistema.'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Panel de Resumen */}
      {!cargando && resumen && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Total</p>
                <p className="text-2xl font-bold text-gray-900">
                  {resumen.total_notificaciones}
                </p>
              </div>
              <Bell className="h-6 w-6 text-blue-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">No Leídas</p>
                <p className="text-2xl font-bold text-orange-600">
                  {resumen.no_leidas}
                </p>
              </div>
              <Bell className="h-6 w-6 text-orange-600" />
            </div>
          </div>

          {/* Resumen de criticidad */}
          <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-lg shadow p-4 border border-red-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-red-700 font-medium">Críticas</p>
                <p className="text-2xl font-bold text-red-900">
                  {resumenCriticidad.criticas}
                </p>
              </div>
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg shadow p-4 border border-orange-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-orange-700 font-medium">Altas</p>
                <p className="text-2xl font-bold text-orange-900">
                  {resumenCriticidad.altas}
                </p>
              </div>
              <AlertTriangle className="h-6 w-6 text-orange-600" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg shadow p-4 border border-yellow-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-yellow-700 font-medium">Medias</p>
                <p className="text-2xl font-bold text-yellow-900">
                  {resumenCriticidad.medias}
                </p>
              </div>
              <AlertTriangle className="h-6 w-6 text-yellow-600" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg shadow p-4 border border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-blue-700 font-medium">Bajas</p>
                <p className="text-2xl font-bold text-blue-900">
                  {resumenCriticidad.bajas}
                </p>
              </div>
              <Info className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = tabActiva === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setTabActiva(tab.id)}
                  className={`
                    group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm
                    ${
                      isActive
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon
                    className={`
                      -ml-0.5 mr-2 h-5 w-5
                      ${isActive ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'}
                    `}
                  />
                  {tab.nombre}
                  {tab.badge > 0 && (
                    <span
                      className={`
                        ml-2 py-0.5 px-2 rounded-full text-xs font-medium
                        ${
                          isActive
                            ? 'bg-blue-100 text-blue-600'
                            : 'bg-gray-100 text-gray-600'
                        }
                      `}
                    >
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Contenido de Tabs */}
        <div className="p-6">
          {tabActiva === 'notificaciones' && (
            <ListaNotificaciones
              idUsuario={idUsuario}
              onNotificacionLeida={refrescar}
            />
          )}
          {tabActiva === 'alertas' && (
            <AlertasSistema onAlertaResuelta={refrescar} />
          )}
          {tabActiva === 'preferencias' && (
            <Preferencias idUsuario={idUsuario} />
          )}
        </div>
      </div>
    </div>
  );
};

export default Notificaciones;
