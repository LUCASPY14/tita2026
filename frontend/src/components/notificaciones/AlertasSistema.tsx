/**
 * Componente de Alertas del Sistema
 * Muestra y gestiona las alertas del sistema para empleados
 */

import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  AlertCircle,
  Info,
} from 'lucide-react';
import { AlertaSistema } from '../../types';
import notificacionesService from '../../services/notificaciones.service';
import toast from 'react-hot-toast';
import Button from '../common/Button';
import { useAuthContext } from '../../contexts/AuthContext';

interface AlertasSistemaProps {
  onAlertaResuelta?: () => void;
}

const AlertasSistemaComponent: React.FC<AlertasSistemaProps> = ({
  onAlertaResuelta,
}) => {
  const { user } = useAuthContext();
  const [alertas, setAlertas] = useState<AlertaSistema[]>([]);
  const [cargando, setCargando] = useState(true);
  const [filtroEstado, setFiltroEstado] = useState<string>('');
  const [alertaSeleccionada, setAlertaSeleccionada] = useState<AlertaSistema | null>(null);
  const [observaciones, setObservaciones] = useState('');
  const [resolviendoId, setResolviendoId] = useState<number | null>(null);

  useEffect(() => {
    cargarAlertas();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtroEstado]);

  const cargarAlertas = async () => {
    try {
      setCargando(true);
      const params: any = {};
      
      if (filtroEstado) {
        params.estado = filtroEstado;
      }

      const data = await notificacionesService.getAlertas(params);
      setAlertas(data);
    } catch (error) {
      console.error('Error cargando alertas:', error);
      toast.error('Error al cargar las alertas');
    } finally {
      setCargando(false);
    }
  };

  const resolverAlerta = async (id: number) => {
    if (!observaciones.trim()) {
      toast.error('Por favor ingresa observaciones');
      return;
    }

    try {
      setResolviendoId(id);
      // Obtener id_empleado del contexto de autenticación
      const idEmpleado = user?.id || 1; // Fallback a 1 si no hay usuario
      await notificacionesService.resolverAlerta(id, observaciones, idEmpleado);
      toast.success('Alerta resuelta exitosamente');
      setObservaciones('');
      setAlertaSeleccionada(null);
      cargarAlertas();
      if (onAlertaResuelta) {
        onAlertaResuelta();
      }
    } catch (error) {
      console.error('Error resolviendo alerta:', error);
      toast.error('Error al resolver la alerta');
    } finally {
      setResolviendoId(null);
    }
  };

  const getIconoCriticidad = (tipo: string) => {
    const iconos: Record<string, React.ComponentType<any>> = {
      critico: XCircle,
      alto: AlertTriangle,
      medio: AlertCircle,
      bajo: Info,
    };
    return iconos[tipo] || AlertTriangle;
  };

  const getColorCriticidad = (tipo: string) => {
    const colores: Record<string, string> = {
      critico: 'text-red-600 bg-red-50 border-red-200',
      alto: 'text-orange-600 bg-orange-50 border-orange-200',
      medio: 'text-yellow-600 bg-yellow-50 border-yellow-200',
      bajo: 'text-blue-600 bg-blue-50 border-blue-200',
    };
    return colores[tipo] || 'text-gray-600 bg-gray-50 border-gray-200';
  };

  const getBadgeEstado = (estado?: string) => {
    if (!estado || estado === 'Pendiente') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
          Pendiente
        </span>
      );
    }
    if (estado === 'Leida') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
          Leída
        </span>
      );
    }
    if (estado === 'Resuelta') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
          Resuelta
        </span>
      );
    }
    return null;
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
      {/* Filtros */}
      <div className="flex gap-2">
        <button
          onClick={() => setFiltroEstado('')}
          className={`
            px-3 py-1 rounded-md text-sm font-medium
            ${
              filtroEstado === ''
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }
          `}
        >
          Todas
        </button>
        <button
          onClick={() => setFiltroEstado('Pendiente')}
          className={`
            px-3 py-1 rounded-md text-sm font-medium
            ${
              filtroEstado === 'Pendiente'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }
          `}
        >
          Pendientes
        </button>
        <button
          onClick={() => setFiltroEstado('Resuelta')}
          className={`
            px-3 py-1 rounded-md text-sm font-medium
            ${
              filtroEstado === 'Resuelta'
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }
          `}
        >
          Resueltas
        </button>
      </div>

      {/* Lista de Alertas */}
      {alertas.length === 0 ? (
        <div className="text-center py-12">
          <CheckCircle className="mx-auto h-12 w-12 text-green-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            No hay alertas
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            No hay alertas del sistema en este momento
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {alertas.map((alerta) => {
            const Icono = getIconoCriticidad(alerta.tipo);
            const colorClases = getColorCriticidad(alerta.tipo);
            const mostrandoDetalle = alertaSeleccionada?.id_alerta === alerta.id_alerta;

            return (
              <div
                key={alerta.id_alerta}
                className={`p-4 rounded-lg border ${colorClases}`}
              >
                <div className="flex items-start gap-4">
                  <div className="p-2 rounded-lg">
                    <Icono className="h-6 w-6" />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="text-sm font-medium text-gray-900">
                            {alerta.tipo.toUpperCase()}
                          </h4>
                          {getBadgeEstado(alerta.estado)}
                        </div>
                        <p className="mt-1 text-sm text-gray-700">
                          {alerta.mensaje}
                        </p>
                        <p className="mt-1 text-xs text-gray-500">
                          {notificacionesService.formatearFecha(alerta.fecha_creacion)}
                        </p>

                        {alerta.estado === 'Resuelta' && alerta.observaciones && (
                          <div className="mt-2 p-2 bg-white bg-opacity-50 rounded">
                            <p className="text-xs font-medium text-gray-700">
                              Observaciones:
                            </p>
                            <p className="text-xs text-gray-600">
                              {alerta.observaciones}
                            </p>
                          </div>
                        )}
                      </div>

                      {(!alerta.estado || alerta.estado === 'Pendiente') && (
                        <Button
                          onClick={() => {
                            if (mostrandoDetalle) {
                              setAlertaSeleccionada(null);
                              setObservaciones('');
                            } else {
                              setAlertaSeleccionada(alerta);
                            }
                          }}
                          variant="primary"
                          size="sm"
                        >
                          {mostrandoDetalle ? 'Cancelar' : 'Resolver'}
                        </Button>
                      )}
                    </div>

                    {/* Formulario de Resolución */}
                    {mostrandoDetalle && (
                      <div className="mt-4 space-y-3 bg-white bg-opacity-50 p-3 rounded">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Observaciones
                          </label>
                          <textarea
                            value={observaciones}
                            onChange={(e) => setObservaciones(e.target.value)}
                            rows={3}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Describe la solución aplicada..."
                          />
                        </div>
                        <div className="flex gap-2">
                          <Button
                            onClick={() => resolverAlerta(alerta.id_alerta)}
                            isLoading={resolviendoId === alerta.id_alerta}
                            variant="primary"
                            size="sm"
                          >
                            Confirmar Resolución
                          </Button>
                          <Button
                            onClick={() => {
                              setAlertaSeleccionada(null);
                              setObservaciones('');
                            }}
                            variant="outline"
                            size="sm"
                          >
                            Cancelar
                          </Button>
                        </div>
                      </div>
                    )}
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

export default AlertasSistemaComponent;
