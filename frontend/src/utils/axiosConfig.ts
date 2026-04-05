/**
 * Configuración de Axios con interceptores para auditoría automática
 * Registra automáticamente operaciones importantes del sistema
 */

import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Operaciones a trackear automáticamente (métodos HTTP que modifican datos)
const OPERACIONES_TRACKEADAS = ['POST', 'PUT', 'PATCH', 'DELETE'];

// Endpoints que NO deben ser trackeados (para evitar recursión infinita)
const ENDPOINTS_EXCLUIDOS = [
  '/usuarios/auditoria',
  '/usuarios/auth/login',
  '/usuarios/auth/logout',
  '/usuarios/2fa',
];

/**
 * Determina si un endpoint debe ser trackeado
 */
const debeTrackear = (url: string | undefined, method: string | undefined): boolean => {
  if (!url || !method) return false;
  
  // Solo trackear métodos que modifican datos
  if (!OPERACIONES_TRACKEADAS.includes(method.toUpperCase())) {
    return false;
  }
  
  // Excluir endpoints específicos
  for (const endpoint of ENDPOINTS_EXCLUIDOS) {
    if (url.includes(endpoint)) {
      return false;
    }
  }
  
  return true;
};

/**
 * Extrae el nombre de la operación desde el método HTTP
 */
const extraerOperacion = (method: string): string => {
  const operaciones: Record<string, string> = {
    POST: 'CREATE',
    PUT: 'UPDATE',
    PATCH: 'UPDATE',
    DELETE: 'DELETE',
  };
  
  return operaciones[method.toUpperCase()] || method.toUpperCase();
};

/**
 * Extrae la tabla afectada desde la URL
 */
const extraerTabla = (url: string): string | null => {
  // Eliminar API_URL base si existe
  const cleanUrl = url.replace(API_URL, '');
  
  // Extrar el primer segmento después de /api/v1/
  const match = cleanUrl.match(/\/([^/]+)/);
  return match ? match[1] : null;
};

/**
 * Envía log de auditoría al backend
 */
const enviarLogAuditoria = async (
  operacion: string,
  tabla: string | null,
  url: string,
  datos: any,
  resultado: 'EXITO' | 'ERROR',
  mensajeError?: string
): Promise<void> => {
  try {
    // Obtener usuario del localStorage
    const userStr = localStorage.getItem('user');
    const user = userStr ? JSON.parse(userStr) : null;
    
    if (!user) return; // No trackear si no hay usuario autenticado
    
    const logData = {
      usuario: user.username || 'Desconocido',
      tipo_usuario: 'Usuario Web',
      id_usuario: user.id,
      operacion,
      tabla_afectada: tabla,
      descripcion: `${operacion} en ${tabla || url}`,
      datos_nuevos: datos,
      ip_address: null, // Se captura en backend
      fecha_operacion: new Date().toISOString(),
      resultado,
      mensaje_error: mensajeError || null,
    };
    
    // Enviar sin await para no bloquear la operación principal
    axios.post(`${API_URL}/usuarios/auditoria/`, logData).catch(err => {
      console.warn('Error enviando log de auditoría:', err);
    });
  } catch (error) {
    console.warn('Error preparando log de auditoría:', error);
  }
};

/**
 * Interceptor de request para agregar token de autenticación
 */
axios.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Agregar token si existe (corregido: usar 'token' en vez de 'access_token')
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Guardar timestamp para medir duración
    (config as any).startTime = Date.now();
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

/**
 * Interceptor de response para auditoría automática
 */
axios.interceptors.response.use(
  async (response: AxiosResponse) => {
    const config = response.config;
    const duration = Date.now() - ((config as any).startTime || 0);
    
    // Trackear solo si es necesario
    if (debeTrackear(config.url, config.method)) {
      const operacion = extraerOperacion(config.method || '');
      const tabla = extraerTabla(config.url || '');
      
      // Enviar log de auditoría (no bloqueante)
      enviarLogAuditoria(
        operacion,
        tabla,
        config.url || '',
        config.data ? JSON.parse(config.data) : null,
        'EXITO'
      );
      
      console.debug(`[Auditoría] ${operacion} en ${tabla} - ${duration}ms - EXITO`);
    }
    
    return response;
  },
  async (error: AxiosError) => {
    const config = error.config;
    
    if (config && debeTrackear(config.url, config.method)) {
      const operacion = extraerOperacion(config.method || '');
      const tabla = extraerTabla(config.url || '');
      const errorData = error.response?.data as any;
      const mensajeError = errorData?.message || (error as any).message || 'Error desconocido';
      
      // Enviar log de auditoría con error
      enviarLogAuditoria(
        operacion,
        tabla,
        config.url || '',
        config.data ? JSON.parse(config.data) : null,
        'ERROR',
        mensajeError
      );
      
      console.debug(`[Auditoría] ${operacion} en ${tabla} - ERROR:`, mensajeError);
    }
    
    return Promise.reject(error);
  }
);

// Exportar instancia configurada de axios
export default axios;
