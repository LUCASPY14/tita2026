import { useState, useEffect, useCallback } from 'react';
import { useAuthContext } from '../contexts/AuthContext';
import notificacionesService from '../services/notificaciones.service';
import type { AlertaSistema, NotificacionPortal, ResumenNotificaciones } from '../types';
import {
  filtrarAlertasPorRol,
  filtrarNotificacionesPorRol,
  enriquecerAlertas,
  ordenarAlertasPorCriticidad,
  obtenerResumenCriticidad,
  type ResumenCriticidad,
} from '../utils/notificationFilters';

interface UseNotificationsByRoleReturn {
  notificaciones: NotificacionPortal[];
  alertas: AlertaSistema[];
  resumen: ResumenNotificaciones | null;
  resumenCriticidad: ResumenCriticidad;
  cargando: boolean;
  error: string | null;
  refrescar: () => Promise<void>;
  marcarComoLeida: (id: number) => Promise<void>;
  marcarTodasComoLeidas: () => Promise<void>;
}

/**
 * Hook para gestionar notificaciones filtradas por rol del usuario
 * 
 * Este hook:
 * - Filtra notificaciones según el rol del usuario autenticado
 * - Enriquece alertas con información de criticidad
 * - Ordena alertas por criticidad
 * - Proporciona funciones para marcar como leídas
 * - Mantiene un resumen actualizado
 * 
 * @example
 * ```tsx
 * const { notificaciones, alertas, refrescar } = useNotificationsByRole();
 * ```
 */
export const useNotificationsByRole = (): UseNotificationsByRoleReturn => {
  const { user } = useAuthContext();
  const [notificaciones, setNotificaciones] = useState<NotificacionPortal[]>([]);
  const [alertas, setAlertas] = useState<AlertaSistema[]>([]);
  const [resumen, setResumen] = useState<ResumenNotificaciones | null>(null);
  const [resumenCriticidad, setResumenCriticidad] = useState<ResumenCriticidad>({
    criticas: 0,
    altas: 0,
    medias: 0,
    bajas: 0,
  });
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Obtener el rol del usuario del contexto
  const userRole = user?.role || 'empleado';

  /**
   * Carga notificaciones del servidor y las filtra por rol
   */
  const cargarNotificaciones = useCallback(async () => {
    if (!user) return;

    try {
      setError(null);

      // Cargar notificaciones
      const notifs = await notificacionesService.getNotificaciones({
        page_size: 50,
      });

      // Filtrar por rol
      const notifsFiltradas = filtrarNotificacionesPorRol(notifs, userRole);
      setNotificaciones(notifsFiltradas);
    } catch (err) {
      console.error('Error cargando notificaciones:', err);
      setError('Error al cargar notificaciones');
      setNotificaciones([]);
    }
  }, [user, userRole]);

  /**
   * Carga alertas del servidor y las filtra por rol
   */
  const cargarAlertas = useCallback(async () => {
    if (!user) return;

    try {
      setError(null);
      const alertasRaw = await notificacionesService.getAlertas({
        page_size: 50,
      });

      // Enriquecer con criticidad
      const alertasEnriquecidas = enriquecerAlertas(alertasRaw);

      // Filtrar por rol
      const alertasFiltradas = filtrarAlertasPorRol(alertasEnriquecidas, userRole);

      // Ordenar por criticidad
      const alertasOrdenadas = ordenarAlertasPorCriticidad(alertasFiltradas);

      setAlertas(alertasOrdenadas);

      // Calcular resumen de criticidad
      const resumenCrit = obtenerResumenCriticidad(alertasOrdenadas);
      setResumenCriticidad(resumenCrit);
    } catch (err) {
      console.error('Error cargando alertas:', err);
      setError('Error al cargar alertas');
      setAlertas([]);
    }
  }, [user, userRole]);

  /**
   * Carga el resumen de notificaciones
   */
  const cargarResumen = useCallback(async () => {
    if (!user) return;

    try {
      const idUsuario = user.id || 1;
      const resumenData = await notificacionesService.getResumenNotificaciones(idUsuario);
      setResumen(resumenData);
    } catch (err) {
      console.error('Error cargando resumen:', err);
      // No setear error aquí para no bloquear la UI
    }
  }, [user]);

  /**
   * Carga todas las notificaciones y alertas
   */
  const refrescar = useCallback(async () => {
    setCargando(true);
    try {
      await Promise.all([
        cargarNotificaciones(),
        cargarAlertas(),
        cargarResumen(),
      ]);
    } finally {
      setCargando(false);
    }
  }, [cargarNotificaciones, cargarAlertas, cargarResumen]);

  /**
   * Marca una notificación como leída
   */
  const marcarComoLeida = useCallback(async (id: number) => {
    try {
      await notificacionesService.marcarNotificacionLeida(id);
      // Actualizar localmente
      setNotificaciones(prev =>
        prev.map(n => n.id_notificacion === id ? { ...n, leida: true } : n)
      );
      // Refrescar resumen
      await cargarResumen();
    } catch (err) {
      console.error('Error marcando notificación como leída:', err);
      throw err;
    }
  }, [cargarResumen]);

  /**
   * Marca todas las notificaciones como leídas
   */
  const marcarTodasComoLeidas = useCallback(async () => {
    if (!user) return;

    try {
      const idUsuario = user.id || 1;
      await notificacionesService.marcarTodasLeidas(idUsuario);
      // Actualizar localmente
      setNotificaciones(prev =>
        prev.map(n => ({ ...n, leida: true }))
      );
      // Refrescar resumen
      await cargarResumen();
    } catch (err) {
      console.error('Error marcando todas como leídas:', err);
      throw err;
    }
  }, [user, cargarResumen]);

  // Cargar datos inicialmente
  useEffect(() => {
    refrescar();
  }, [refrescar]);

  return {
    notificaciones,
    alertas,
    resumen,
    resumenCriticidad,
    cargando,
    error,
    refrescar,
    marcarComoLeida,
    marcarTodasComoLeidas,
  };
};

export default useNotificationsByRole;
