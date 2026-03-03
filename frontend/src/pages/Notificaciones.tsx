/**
 * Página de Notificaciones
 * Centro de notificaciones multicanal del sistema
 */

import React, { useState, useEffect } from 'react';
import { Bell, AlertTriangle, Settings } from 'lucide-react';
import {
  ListaNotificaciones,
  AlertasSistema,
  Preferencias,
} from '../components/notificaciones';
import notificacionesService from '../services/notificaciones.service';
import { ResumenNotificaciones } from '../types';
import toast from 'react-hot-toast';

type TabType = 'notificaciones' | 'alertas' | 'preferencias';

const Notificaciones: React.FC = () => {
  const [tabActiva, setTabActiva] = useState<TabType>('notificaciones');
  const [resumen, setResumen] = useState<ResumenNotificaciones | null>(null);
  const [cargando, setCargando] = useState(true);

  // TODO: Obtener id_usuario del contexto de autenticación
  const idUsuario = 1;

  useEffect(() => {
    cargarResumen();
  }, []);

  const cargarResumen = async () => {
    try {
      setCargando(true);
      const data = await notificacionesService.getResumenNotificaciones(idUsuario);
      setResumen(data);
    } catch (error) {
      console.error('Error cargando resumen:', error);
      toast.error('Error al cargar el resumen de notificaciones');
    } finally {
      setCargando(false);
    }
  };

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
      badge: resumen?.alertas_sistema || 0,
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

      {/* Panel de Resumen */}
      {!cargando && resumen && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total</p>
                <p className="text-2xl font-bold text-gray-900">
                  {resumen.total_notificaciones}
                </p>
              </div>
              <Bell className="h-8 w-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">No Leídas</p>
                <p className="text-2xl font-bold text-orange-600">
                  {resumen.no_leidas}
                </p>
              </div>
              <Bell className="h-8 w-8 text-orange-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Hoy</p>
                <p className="text-2xl font-bold text-green-600">
                  {resumen.notificaciones_hoy}
                </p>
              </div>
              <Bell className="h-8 w-8 text-green-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Alertas Críticas</p>
                <p className="text-2xl font-bold text-red-600">
                  {resumen.alertas_criticas}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-600" />
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
              onNotificacionLeida={cargarResumen}
            />
          )}
          {tabActiva === 'alertas' && (
            <AlertasSistema onAlertaResuelta={cargarResumen} />
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
