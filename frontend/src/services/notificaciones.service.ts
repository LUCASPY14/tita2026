/**
 * Servicio de Notificaciones
 * Gestión de notificaciones, alertas y preferencias del sistema
 */

import api from './api';
import {
  NotificacionPortal,
  NotificacionSaldo,
  AlertaSistema,
  PreferenciasNotificacion,
  ResumenNotificaciones,
  NotificacionesParams,
  AlertasParams,
  ActualizarPreferenciasData,
} from '../types';

// ==================== Notificaciones Portal ====================

/**
 * Obtiene notificaciones del portal con filtros opcionales
 */
export const getNotificaciones = async (params?: NotificacionesParams): Promise<NotificacionPortal[]> => {
  const response = await api.get('/notificaciones-portal/', { params });
  const items = response.data.results ?? response.data;
  // Convertir IntegerField a boolean
  return items.map((n: any) => ({
    ...n,
    leida: n.leida === 1,
  }));
};

/**
 * Obtiene una notificación por ID
 */
export const getNotificacionById = async (id: number): Promise<NotificacionPortal> => {
  const response = await api.get(`/notificaciones-portal/${id}/`);
  return {
    ...response.data,
    leida: response.data.leida === 1,
  };
};

/**
 * Marca una notificación como leída
 */
export const marcarNotificacionLeida = async (id: number): Promise<NotificacionPortal> => {
  const response = await api.post(`/notificaciones-portal/${id}/marcar_leida/`);
  return {
    ...response.data,
    leida: response.data.leida === 1,
  };
};

/**
 * Marca todas las notificaciones como leídas
 */
export const marcarTodasLeidas = async (idUsuario: number): Promise<void> => {
  await api.post('/notificaciones-portal/marcar_todas_leidas/', {
    id_usuario_portal: idUsuario,
  });
};

/**
 * Obtiene el resumen de notificaciones
 */
export const getResumenNotificaciones = async (idUsuario: number): Promise<ResumenNotificaciones> => {
  const response = await api.get('/notificaciones-portal/resumen/', {
    params: { id_usuario_portal: idUsuario },
  });
  return response.data;
};

// ==================== Notificaciones de Saldo ====================

/**
 * Obtiene notificaciones de saldo con filtros opcionales
 */
export const getNotificacionesSaldo = async (params?: NotificacionesParams): Promise<NotificacionSaldo[]> => {
  const response = await api.get('/notificaciones-saldo/', { params });
  const items = response.data.results ?? response.data;
  // Convertir IntegerFields a boolean
  return items.map((n: any) => ({
    ...n,
    enviada_email: n.enviada_email === 1,
    enviada_sms: n.enviada_sms === 1,
    leida: n.leida === 1,
  }));
};

/**
 * Obtiene una notificación de saldo por ID
 */
export const getNotificacionSaldoById = async (id: number): Promise<NotificacionSaldo> => {
  const response = await api.get(`/notificaciones-saldo/${id}/`);
  return {
    ...response.data,
    enviada_email: response.data.enviada_email === 1,
    enviada_sms: response.data.enviada_sms === 1,
    leida: response.data.leida === 1,
  };
};

// ==================== Alertas del Sistema ====================

/**
 * Obtiene alertas del sistema con filtros opcionales
 */
export const getAlertas = async (params?: AlertasParams): Promise<AlertaSistema[]> => {
  const response = await api.get('/alertas-sistema/', { params });
  return response.data.results ?? response.data;
};

/**
 * Obtiene una alerta por ID
 */
export const getAlertaById = async (id: number): Promise<AlertaSistema> => {
  const response = await api.get(`/alertas-sistema/${id}/`);
  return response.data;
};

/**
 * Resuelve una alerta del sistema
 */
export const resolverAlerta = async (
  id: number,
  observaciones: string,
  idEmpleado?: number
): Promise<AlertaSistema> => {
  const response = await api.post(`/alertas-sistema/${id}/resolver/`, {
    observaciones,
    id_empleado_resuelve: idEmpleado,
  });
  return response.data;
};

// ==================== Preferencias de Notificación ====================

/**
 * Obtiene las preferencias de notificación de un usuario
 */
export const getPreferencias = async (idUsuario: number): Promise<PreferenciasNotificacion[]> => {
  const response = await api.get('/preferencias-notificacion/obtener_preferencias/', {
    params: { id_usuario_portal: idUsuario },
  });
  const items = response.data.results ?? response.data;
  // Convertir IntegerFields a boolean
  return items.map((p: any) => ({
    ...p,
    email_activo: p.email_activo === 1,
    push_activo: p.push_activo === 1,
  }));
};

/**
 * Actualiza o crea preferencias de notificación
 */
export const actualizarPreferencias = async (
  idUsuario: number,
  data: ActualizarPreferenciasData
): Promise<PreferenciasNotificacion> => {
  const response = await api.post('/preferencias-notificacion/actualizar_preferencias/', {
    id_usuario_portal: idUsuario,
    tipo_notificacion: data.tipo_notificacion,
    email_activo: data.email_activo ? 1 : 0,
    push_activo: data.push_activo ? 1 : 0,
  });
  return {
    ...response.data,
    email_activo: response.data.email_activo === 1,
    push_activo: response.data.push_activo === 1,
  };
};

// ==================== Funciones Helper ====================

/**
 * Formatea una fecha a string legible
 */
export const formatearFecha = (fecha: string): string => {
  const date = new Date(fecha);
  return date.toLocaleDateString('es-PY', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Calcula el tiempo transcurrido desde una fecha
 */
export const calcularTiempoTranscurrido = (fecha: string): string => {
  const ahora = new Date();
  const fechaObj = new Date(fecha);
  const diffMs = ahora.getTime() - fechaObj.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHoras = Math.floor(diffMins / 60);
  const diffDias = Math.floor(diffHoras / 24);

  if (diffMins < 1) return 'Justo ahora';
  if (diffMins < 60) return `Hace ${diffMins} minuto${diffMins > 1 ? 's' : ''}`;
  if (diffHoras < 24) return `Hace ${diffHoras} hora${diffHoras > 1 ? 's' : ''}`;
  if (diffDias < 7) return `Hace ${diffDias} día${diffDias > 1 ? 's' : ''}`;
  return formatearFecha(fecha);
};

/**
 * Obtiene el ícono según el tipo de notificación
 */
export const getIconoTipo = (tipo: string): string => {
  const iconos: Record<string, string> = {
    saldo_bajo: 'AlertTriangle',
    recarga_exitosa: 'CheckCircle',
    consumo: 'ShoppingCart',
    almuerzo: 'Utensils',
    sistema: 'Bell',
    seguridad: 'Shield',
  };
  return iconos[tipo] || 'Bell';
};

/**
 * Obtiene el color según el tipo de notificación
 */
export const getColorTipo = (tipo: string): string => {
  const colores: Record<string, string> = {
    saldo_bajo: 'text-yellow-600',
    recarga_exitosa: 'text-green-600',
    consumo: 'text-blue-600',
    almuerzo: 'text-orange-600',
    sistema: 'text-gray-600',
    seguridad: 'text-red-600',
  };
  return colores[tipo] || 'text-gray-600';
};

/**
 * Obtiene el color según la criticidad de alerta
 */
export const getColorCriticidad = (tipo: string): string => {
  const colores: Record<string, string> = {
    critico: 'text-red-600 bg-red-50',
    alto: 'text-orange-600 bg-orange-50',
    medio: 'text-yellow-600 bg-yellow-50',
    bajo: 'text-blue-600 bg-blue-50',
  };
  return colores[tipo] || 'text-gray-600 bg-gray-50';
};

const notificacionesService = {
  getNotificaciones,
  getNotificacionById,
  marcarNotificacionLeida,
  marcarTodasLeidas,
  getResumenNotificaciones,
  getNotificacionesSaldo,
  getNotificacionSaldoById,
  getAlertas,
  getAlertaById,
  resolverAlerta,
  getPreferencias,
  actualizarPreferencias,
  formatearFecha,
  calcularTiempoTranscurrido,
  getIconoTipo,
  getColorTipo,
  getColorCriticidad,
};

export default notificacionesService;
