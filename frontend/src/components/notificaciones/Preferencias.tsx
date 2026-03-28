/**
 * Componente de Preferencias de Notificación
 * Permite configurar preferencias de notificaciones por tipo
 */

import React, { useState, useEffect } from 'react';
import { Mail, Bell } from 'lucide-react';
import { PreferenciasNotificacion } from '../../types';
import notificacionesService from '../../services/notificaciones.service';
import toast from 'react-hot-toast';

interface PreferenciasProps {
  idUsuario: number;
}

const Preferencias: React.FC<PreferenciasProps> = ({ idUsuario }) => {
  const [preferencias, setPreferencias] = useState<PreferenciasNotificacion[]>([]);
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState<string | null>(null);

  // Tipos de notificaciones disponibles
  const tiposNotificacion = [
    { codigo: 'saldo_bajo', nombre: 'Saldo Bajo', descripcion: 'Alertas cuando el saldo de una tarjeta está bajo' },
    { codigo: 'recarga_exitosa', nombre: 'Recarga Exitosa', descripcion: 'Confirmación de recargas de saldo' },
    { codigo: 'consumo', nombre: 'Consumo', descripcion: 'Notificaciones de consumos realizados' },
    { codigo: 'almuerzo', nombre: 'Almuerzo', descripcion: 'Información sobre planes de almuerzo' },
    { codigo: 'sistema', nombre: 'Sistema', descripcion: 'Notificaciones importantes del sistema' },
    { codigo: 'seguridad', nombre: 'Seguridad', descripcion: 'Alertas de seguridad y accesos' },
  ];

  useEffect(() => {
    cargarPreferencias();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cargarPreferencias = async () => {
    try {
      setCargando(true);
      const data = await notificacionesService.getPreferencias(idUsuario);
      setPreferencias(data);
    } catch (error) {
      console.error('Error cargando preferencias:', error);
      toast.error('Error al cargar las preferencias');
    } finally {
      setCargando(false);
    }
  };

  const obtenerPreferencia = (tipoNotificacion: string) => {
    return preferencias.find((p) => p.tipo_notificacion === tipoNotificacion) || {
      tipo_notificacion: tipoNotificacion,
      email_activo: true,
      push_activo: true,
    };
  };

  const actualizarPreferencia = async (
    tipoNotificacion: string,
    campo: 'email_activo' | 'push_activo',
    valor: boolean
  ) => {
    try {
      setGuardando(tipoNotificacion);
      
      const preferenciaActual = obtenerPreferencia(tipoNotificacion);
      const datosActualizados = {
        ...preferenciaActual,
        [campo]: valor,
      };

      await notificacionesService.actualizarPreferencias(idUsuario, {
        tipo_notificacion: tipoNotificacion,
        email_activo: datosActualizados.email_activo,
        push_activo: datosActualizados.push_activo,
      });

      toast.success('Preferencias actualizadas');
      cargarPreferencias();
    } catch (error) {
      console.error('Error actualizando preferencia:', error);
      toast.error('Error al actualizar las preferencias');
    } finally {
      setGuardando(null);
    }
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
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900">
          Configuración de Notificaciones
        </h3>
        <p className="mt-1 text-sm text-gray-500">
          Elige cómo quieres recibir cada tipo de notificación
        </p>
      </div>

      <div className="space-y-3">
        {tiposNotificacion.map((tipo) => {
          const preferencia = obtenerPreferencia(tipo.codigo);
          const estaGuardando = guardando === tipo.codigo;

          return (
            <div
              key={tipo.codigo}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="space-y-3">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">
                    {tipo.nombre}
                  </h4>
                  <p className="text-sm text-gray-500">{tipo.descripcion}</p>
                </div>

                <div className="flex items-center gap-6">
                  {/* Email */}
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={preferencia.email_activo}
                      onChange={(e) =>
                        actualizarPreferencia(
                          tipo.codigo,
                          'email_activo',
                          e.target.checked
                        )
                      }
                      disabled={estaGuardando}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded cursor-pointer"
                    />
                    <Mail className="h-4 w-4 text-gray-500" />
                    <span className="text-sm text-gray-700">Email</span>
                  </label>

                  {/* Push */}
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={preferencia.push_activo}
                      onChange={(e) =>
                        actualizarPreferencia(
                          tipo.codigo,
                          'push_activo',
                          e.target.checked
                        )
                      }
                      disabled={estaGuardando}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded cursor-pointer"
                    />
                    <Bell className="h-4 w-4 text-gray-500" />
                    <span className="text-sm text-gray-700">Portal</span>
                  </label>

                  {estaGuardando && (
                    <div className="ml-auto">
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        Guardando...
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <div className="flex">
          <div className="flex-shrink-0">
            <Bell className="h-5 w-5 text-blue-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">
              Información sobre las preferencias
            </h3>
            <div className="mt-2 text-sm text-blue-700">
              <ul className="list-disc list-inside space-y-1">
                <li>Los cambios se guardan automáticamente</li>
                <li>Email: Recibirás notificaciones en tu correo electrónico</li>
                <li>Portal: Verás las notificaciones en el sistema</li>
                <li>Puedes activar ambas opciones para cada tipo</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Preferencias;
