/**
 * Componente de Lista de Notificaciones
 * Muestra y gestiona las notificaciones del portal
 */

import React, { useState, useEffect } from 'react';
import {
  Bell,
  CheckCircle,
  AlertTriangle,
  ShoppingCart,
  Utensils,
  Shield,
  Check,
  CheckCheck,
} from 'lucide-react';
import { NotificacionPortal } from '../../types';
import notificacionesService from '../../services/notificaciones.service';
import toast from 'react-hot-toast';
import Button from '../common/Button';

interface ListaNotificacionesProps {
  idUsuario: number;
  onNotificacionLeida?: () => void;
}

const ListaNotificaciones: React.FC<ListaNotificacionesProps> = ({
  idUsuario,
  onNotificacionLeida,
}) => {
  const [notificaciones, setNotificaciones] = useState<NotificacionPortal[]>([]);
  const [cargando, setCargando] = useState(true);
  const [filtroLeida, setFiltroLeida] = useState<'todas' | 'leidas' | 'no_leidas'>('todas');

  useEffect(() => {
    cargarNotificaciones();
  }, [filtroLeida]);

  const cargarNotificaciones = async () => {
    try {
      setCargando(true);
      const params: any = {};
      
      if (filtroLeida === 'leidas') {
        params.leida = true;
      } else if (filtroLeida === 'no_leidas') {
        params.leida = false;
      }

      const data = await notificacionesService.getNotificaciones(params);
      setNotificaciones(data);
    } catch (error) {
      console.error('Error cargando notificaciones:', error);
      toast.error('Error al cargar las notificaciones');
    } finally {
      setCargando(false);
    }
  };

  const marcarComoLeida = async (id: number) => {
    try {
      await notificacionesService.marcarNotificacionLeida(id);
      toast.success('Notificación marcada como leída');
      cargarNotificaciones();
      if (onNotificacionLeida) {
        onNotificacionLeida();
      }
    } catch (error) {
      console.error('Error marcando notificación:', error);
      toast.error('Error al marcar como leída');
    }
  };

  const marcarTodasComoLeidas = async () => {
    try {
      await notificacionesService.marcarTodasLeidas(idUsuario);
      toast.success('Todas las notificaciones marcadas como leídas');
      cargarNotificaciones();
      if (onNotificacionLeida) {
        onNotificacionLeida();
      }
    } catch (error) {
      console.error('Error marcando todas:', error);
      toast.error('Error al marcar todas como leídas');
    }
  };

  const getIcono = (tipo: string) => {
    const iconos: Record<string, React.ComponentType<any>> = {
      saldo_bajo: AlertTriangle,
      recarga_exitosa: CheckCircle,
      consumo: ShoppingCart,
      almuerzo: Utensils,
      sistema: Bell,
      seguridad: Shield,
    };
    return iconos[tipo] || Bell;
  };

  const getColorIcono = (tipo: string) => {
    const colores: Record<string, string> = {
      saldo_bajo: 'text-yellow-600 bg-yellow-50',
      recarga_exitosa: 'text-green-600 bg-green-50',
      consumo: 'text-blue-600 bg-blue-50',
      almuerzo: 'text-orange-600 bg-orange-50',
      sistema: 'text-gray-600 bg-gray-50',
      seguridad: 'text-red-600 bg-red-50',
    };
    return colores[tipo] || 'text-gray-600 bg-gray-50';
  };

  if (cargando) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filtros y Acciones */}
      <div className="flex flex-wrap gap-4 items-center justify-between">
        <div className="flex gap-2">
          <button
            onClick={() => setFiltroLeida('todas')}
            className={`
              px-3 py-1 rounded-md text-sm font-medium
              ${
                filtroLeida === 'todas'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
          >
            Todas
          </button>
          <button
            onClick={() => setFiltroLeida('no_leidas')}
            className={`
              px-3 py-1 rounded-md text-sm font-medium
              ${
                filtroLeida === 'no_leidas'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
          >
            No Leídas
          </button>
          <button
            onClick={() => setFiltroLeida('leidas')}
            className={`
              px-3 py-1 rounded-md text-sm font-medium
              ${
                filtroLeida === 'leidas'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
          >
            Leídas
          </button>
        </div>

        <Button
          onClick={marcarTodasComoLeidas}
          variant="outline"
          size="sm"
        >
          <CheckCheck className="h-4 w-4 mr-2" />
          Marcar todas como leídas
        </Button>
      </div>

      {/* Lista de Notificaciones */}
      {notificaciones.length === 0 ? (
        <div className="text-center py-12">
          <Bell className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            No hay notificaciones
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            No tienes notificaciones en este momento
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {notificaciones.map((notificacion) => {
            const Icono = getIcono(notificacion.tipo);
            const colorIcono = getColorIcono(notificacion.tipo);

            return (
              <div
                key={notificacion.id_notificacion}
                className={`
                  p-4 rounded-lg border transition-all hover:shadow-md
                  ${
                    notificacion.leida
                      ? 'bg-white border-gray-200'
                      : 'bg-blue-50 border-blue-200'
                  }
                `}
              >
                <div className="flex items-start gap-4">
                  <div className={`p-2 rounded-lg ${colorIcono}`}>
                    <Icono className="h-5 w-5" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-gray-900">
                          {notificacion.titulo}
                          {!notificacion.leida && (
                            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              Nueva
                            </span>
                          )}
                        </h4>
                        <p className="mt-1 text-sm text-gray-600">
                          {notificacion.mensaje}
                        </p>
                        <p className="mt-1 text-xs text-gray-500">
                          {notificacionesService.calcularTiempoTranscurrido(
                            notificacion.fecha_envio
                          )}
                        </p>
                      </div>

                      {!notificacion.leida && (
                        <button
                          onClick={() => marcarComoLeida(notificacion.id_notificacion)}
                          className="p-1 rounded hover:bg-blue-100 text-blue-600"
                          title="Marcar como leída"
                        >
                          <Check className="h-5 w-5" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ListaNotificaciones;
