/**
 * Servicio de Permisos
 * Gestión de permisos del sistema y asignación a roles
 */

import axios from '../utils/axiosConfig';
import type {
  Permiso,
  PermisosResponse,
  RolConPermisos,
  AsignarPermisoRequest,
  RemoverPermisoRequest,
  PermisosResult,
} from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// ==================== Permisos ====================

/**
 * Obtiene todos los permisos del sistema agrupados por módulo
 */
export const listarPermisos = async (): Promise<PermisosResponse> => {
  const response = await axios.get(`${API_URL}/permisos/listar/`);
  return response.data;
};

/**
 * Inicializa todos los permisos del sistema
 * Solo debe ejecutarse en configuración inicial
 */
export const inicializarPermisos = async (): Promise<PermisosResult> => {
  const response = await axios.post(`${API_URL}/permisos/inicializar/`);
  return response.data;
};

/**
 * Asigna un permiso a un rol
 */
export const asignarPermisoARol = async (
  data: AsignarPermisoRequest
): Promise<PermisosResult> => {
  const response = await axios.post(`${API_URL}/permisos/asignar_a_rol/`, data);
  return response.data;
};

/**
 * Remueve un permiso de un rol
 */
export const removerPermisoDeRol = async (
  data: RemoverPermisoRequest
): Promise<PermisosResult> => {
  const response = await axios.post(`${API_URL}/permisos/remover_de_rol/`, data);
  return response.data;
};

// ==================== Permisos de Rol ====================

/**
 * Obtiene todos los permisos asignados a un rol específico
 */
export const obtenerPermisosDeRol = async (idRol: number): Promise<RolConPermisos> => {
  const response = await axios.get(`${API_URL}/roles/${idRol}/permisos/`);
  return response.data;
};

/**
 * Asigna múltiples permisos a un rol
 */
export const asignarPermisosMultiples = async (
  idRol: number,
  codigosPermisos: string[]
): Promise<{ success: boolean; resultados: PermisosResult[] }> => {
  const resultados: PermisosResult[] = [];
  
  for (const codigoPermiso of codigosPermisos) {
    try {
      const resultado = await asignarPermisoARol({ id_rol: idRol, codigo_permiso: codigoPermiso });
      resultados.push(resultado);
    } catch (error: any) {
      resultados.push({
        success: false,
        mensaje: error.response?.data?.mensaje || `Error al asignar ${codigoPermiso}`,
      });
    }
  }
  
  const success = resultados.every((r) => r.success);
  return { success, resultados };
};

/**
 * Remueve múltiples permisos de un rol
 */
export const removerPermisosMultiples = async (
  idRol: number,
  codigosPermisos: string[]
): Promise<{ success: boolean; resultados: PermisosResult[] }> => {
  const resultados: PermisosResult[] = [];
  
  for (const codigoPermiso of codigosPermisos) {
    try {
      const resultado = await removerPermisoDeRol({ id_rol: idRol, codigo_permiso: codigoPermiso });
      resultados.push(resultado);
    } catch (error: any) {
      resultados.push({
        success: false,
        mensaje: error.response?.data?.mensaje || `Error al remover ${codigoPermiso}`,
      });
    }
  }
  
  const success = resultados.every((r) => r.success);
  return { success, resultados };
};

// ==================== Helpers ====================

/**
 * Agrupa permisos por módulo
 */
export const agruparPermisosPorModulo = (permisos: Permiso[]): { [modulo: string]: Permiso[] } => {
  return permisos.reduce((acc, permiso) => {
    const modulo = permiso.modulo;
    if (!acc[modulo]) {
      acc[modulo] = [];
    }
    acc[modulo].push(permiso);
    return acc;
  }, {} as { [modulo: string]: Permiso[] });
};

/**
 * Verifica si un rol tiene un permiso específico
 */
export const rolTienePermiso = (
  permisosRol: RolConPermisos['permisos'],
  codigoPermiso: string
): boolean => {
  return permisosRol.some((p) => p.id_permiso__codigo_permiso === codigoPermiso);
};

export default {
  listarPermisos,
  inicializarPermisos,
  asignarPermisoARol,
  removerPermisoDeRol,
  obtenerPermisosDeRol,
  asignarPermisosMultiples,
  removerPermisosMultiples,
  agruparPermisosPorModulo,
  rolTienePermiso,
};
