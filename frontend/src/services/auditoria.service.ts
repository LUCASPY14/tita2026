/**
 * Servicio de Auditoría
 * Gestión de logs de auditoría y tracking de operaciones del sistema
 */

import axios from '../utils/axiosConfig';
import {
  AuditoriaOperacion,
  FiltrosAuditoria,
  EstadisticasAuditoria,
  TimelineAuditoria,
  ActividadUsuario,
  PaginatedResponse,
} from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// ==================== Logs de Auditoría ====================

/**
 * Obtiene logs de auditoría con filtros avanzados
 * @param filtros Filtros para la consulta de logs
 * @returns Paginación con logs de auditoría
 */
export const getLogsAuditoria = async (
  filtros?: FiltrosAuditoria
): Promise<PaginatedResponse<AuditoriaOperacion>> => {
  const response = await axios.get(`${API_URL}/usuarios/auditoria/`, {
    params: filtros,
  });
  return response.data;
};

/**
 * Obtiene un log de auditoría por ID
 * @param id ID del log de auditoría
 * @returns Detalle del log
 */
export const getLogAuditoriaById = async (id: number): Promise<AuditoriaOperacion> => {
  const response = await axios.get(`${API_URL}/usuarios/auditoria/${id}/`);
  return response.data;
};

/**
 * Obtiene estadísticas generales de auditoría
 * @param filtros Filtros opcionales para las estadísticas
 * @returns Estadísticas agregadas de auditoría
 */
export const getEstadisticasAuditoria = async (
  filtros?: FiltrosAuditoria
): Promise<EstadisticasAuditoria> => {
  const response = await axios.get(`${API_URL}/usuarios/auditoria/estadisticas/`, {
    params: filtros,
  });
  return response.data;
};

/**
 * Obtiene timeline de operaciones agrupadas por día
 * @param filtros Filtros de fecha
 * @returns Array con cantidad de operaciones por día
 */
export const getTimelineAuditoria = async (
  filtros?: FiltrosAuditoria
): Promise<TimelineAuditoria[]> => {
  const response = await axios.get(`${API_URL}/usuarios/auditoria/timeline/`, {
    params: filtros,
  });
  return response.data;
};

/**
 * Obtiene actividad detallada de un usuario específico
 * @param idUsuario ID del usuario
 * @param filtros Filtros adicionales opcionales
 * @returns Resumen de actividad del usuario
 */
export const getActividadUsuario = async (
  idUsuario: number,
  filtros?: FiltrosAuditoria
): Promise<ActividadUsuario> => {
  const response = await axios.get(`${API_URL}/usuarios/auditoria/actividad_usuario/`, {
    params: { id_usuario: idUsuario, ...filtros },
  });
  return response.data;
};

// ==================== Utilidades ====================

/**
 * Convierte código de operación a texto legible
 */
export const getTipoOperacionDisplay = (operacion: string): string => {
  const operaciones: Record<string, string> = {
    LOGIN: 'Inicio de sesión',
    LOGOUT: 'Cierre de sesión',
    CREATE: 'Creación',
    UPDATE: 'Modificación',
    DELETE: 'Eliminación',
    VIEW: 'Consulta',
    EXPORT: 'Exportación',
    IMPORT: 'Importación',
    '2FA_ENABLE': 'Activación 2FA',
    '2FA_DISABLE': 'Desactivación 2FA',
    PASSWORD_CHANGE: 'Cambio de contraseña',
    PASSWORD_RESET: 'Recuperación de contraseña',
  };
  return operaciones[operacion] || operacion;
};

/**
 * Convierte código de resultado a texto legible
 */
export const getResultadoDisplay = (resultado: string): string => {
  const resultados: Record<string, string> = {
    EXITO: 'Exitoso',
    ERROR: 'Error',
    BLOQUEADO: 'Bloqueado',
    DENEGADO: 'Denegado',
  };
  return resultados[resultado] || resultado;
};

/**
 * Obtiene color para badge según resultado
 */
export const getResultadoColor = (resultado: string): string => {
  const colores: Record<string, string> = {
    EXITO: 'bg-green-100 text-green-800',
    ERROR: 'bg-red-100 text-red-800',
    BLOQUEADO: 'bg-orange-100 text-orange-800',
    DENEGADO: 'bg-gray-100 text-gray-800',
  };
  return colores[resultado] || 'bg-gray-100 text-gray-800';
};

/**
 * Obtiene icono según tipo de operación
 */
export const getOperacionIcon = (operacion: string): string => {
  if (operacion.includes('LOGIN')) return 'LogIn';
  if (operacion.includes('LOGOUT')) return 'LogOut';
  if (operacion.includes('CREATE')) return 'Plus';
  if (operacion.includes('UPDATE')) return 'Edit';
  if (operacion.includes('DELETE')) return 'Trash2';
  if (operacion.includes('VIEW')) return 'Eye';
  if (operacion.includes('EXPORT')) return 'Download';
  if (operacion.includes('IMPORT')) return 'Upload';
  if (operacion.includes('2FA')) return 'Shield';
  if (operacion.includes('PASSWORD')) return 'Key';
  return 'Activity';
};

// Export default con todos los métodos
const auditoriaService = {
  getLogsAuditoria,
  getLogAuditoriaById,
  getEstadisticasAuditoria,
  getTimelineAuditoria,
  getActividadUsuario,
  getTipoOperacionDisplay,
  getResultadoDisplay,
  getResultadoColor,
  getOperacionIcon,
};

export default auditoriaService;
