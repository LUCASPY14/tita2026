/**
 * Servicio de Configuración del Sistema
 * Gestión de configuraciones, caché y límites del sistema
 */

import axios from '../utils/axiosConfig';
import {
  ConfiguracionSistema,
  ConfiguracionParams,
  ActualizarConfiguracionData,
} from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// ==================== Configuración del Sistema ====================

/**
 * Obtiene todas las configuraciones del sistema
 */
export const getConfiguraciones = async (params?: ConfiguracionParams): Promise<ConfiguracionSistema[]> => {
  const response = await axios.get(`${API_URL}/configuracion-sistema/`, { params });
  return response.data;
};

/**
 * Obtiene configuraciones agrupadas por categoría
 */
export const getConfiguracionesPorCategoria = async (): Promise<Record<string, ConfiguracionSistema[]>> => {
  const response = await axios.get(`${API_URL}/configuracion-sistema/por_categoria/`);
  return response.data;
};

/**
 * Obtiene una configuración por ID
 */
export const getConfiguracionById = async (id: number): Promise<ConfiguracionSistema> => {
  const response = await axios.get(`${API_URL}/configuracion-sistema/${id}/`);
  return response.data;
};

/**
 * Actualiza el valor de una configuración
 */
export const actualizarConfiguracion = async (
  id: number,
  data: ActualizarConfiguracionData
): Promise<ConfiguracionSistema> => {
  const response = await axios.post(`${API_URL}/configuracion-sistema/${id}/actualizar_valor/`, data);
  return response.data;
};

/**
 * Resetea una configuración a su valor por defecto
 */
export const resetearConfiguracion = async (id: number): Promise<ConfiguracionSistema> => {
  const response = await axios.post(`${API_URL}/configuracion-sistema/${id}/resetear_default/`);
  return response.data;
};

// ==================== Funciones Helper ====================

/**
 * Formatea el valor de configuración según su tipo
 */
export const formatearValorConfig = (config: ConfiguracionSistema): string => {
  switch (config.tipo) {
    case 'boolean':
      return config.valor === 'true' || config.valor === '1' ? 'Sí' : 'No';
    case 'number':
      return parseFloat(config.valor).toLocaleString('es-PY');
    case 'password':
      return '••••••••';
    case 'json':
      try {
        return JSON.stringify(JSON.parse(config.valor), null, 2);
      } catch {
        return config.valor;
      }
    default:
      return config.valor;
  }
};

/**
 * Valida el valor según el tipo de configuración
 */
export const validarValorConfig = (config: ConfiguracionSistema, valor: string): { valido: boolean; error?: string } => {
  // Validación requerido
  if (config.requerido && !valor.trim()) {
    return { valido: false, error: 'Este campo es requerido' };
  }

  // Validación por tipo
  switch (config.tipo) {
    case 'number':
      const numero = parseFloat(valor);
      if (isNaN(numero)) {
        return { valido: false, error: 'Debe ser un número válido' };
      }
      if (config.valor_min && numero < parseFloat(config.valor_min)) {
        return { valido: false, error: `El valor mínimo es ${config.valor_min}` };
      }
      if (config.valor_max && numero > parseFloat(config.valor_max)) {
        return { valido: false, error: `El valor máximo es ${config.valor_max}` };
      }
      break;

    case 'boolean':
      if (!['true', 'false', '1', '0'].includes(valor.toLowerCase())) {
        return { valido: false, error: 'Debe ser verdadero o falso' };
      }
      break;

    case 'email':
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(valor)) {
        return { valido: false, error: 'Email inválido' };
      }
      break;

    case 'url':
      try {
        new URL(valor);
      } catch {
        return { valido: false, error: 'URL inválida' };
      }
      break;

    case 'json':
      try {
        JSON.parse(valor);
      } catch {
        return { valido: false, error: 'JSON inválido' };
      }
      break;
  }

  // Validación de valores permitidos
  if (config.valores_permitidos && Array.isArray(config.valores_permitidos)) {
    if (!config.valores_permitidos.includes(valor)) {
      return {
        valido: false,
        error: `Valor debe ser uno de: ${config.valores_permitidos.join(', ')}`,
      };
    }
  }

  return { valido: true };
};

/**
 * Obtiene el icono según la categoría de configuración
 */
export const getIconoCategoria = (categoria: string): string => {
  const iconos: Record<string, string> = {
    general: 'Settings',
    notificaciones: 'Bell',
    seguridad: 'Shield',
    pagos: 'CreditCard',
    integraciones: 'Link',
    sistema: 'Server',
    ui: 'Palette',
    email: 'Mail',
  };
  return iconos[categoria.toLowerCase()] || 'Settings';
};

/**
 * Obtiene el color según la categoría
 */
export const getColorCategoria = (categoria: string): string => {
  const colores: Record<string, string> = {
    general: 'text-blue-600 bg-blue-50',
    notificaciones: 'text-yellow-600 bg-yellow-50',
    seguridad: 'text-red-600 bg-red-50',
    pagos: 'text-green-600 bg-green-50',
    integraciones: 'text-purple-600 bg-purple-50',
    sistema: 'text-gray-600 bg-gray-50',
    ui: 'text-pink-600 bg-pink-50',
    email: 'text-indigo-600 bg-indigo-50',
  };
  return colores[categoria.toLowerCase()] || 'text-gray-600 bg-gray-50';
};

/**
 * Formatea fecha a string legible
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

const configuracionService = {
  getConfiguraciones,
  getConfiguracionesPorCategoria,
  getConfiguracionById,
  actualizarConfiguracion,
  resetearConfiguracion,
  formatearValorConfig,
  validarValorConfig,
  getIconoCategoria,
  getColorCategoria,
  formatearFecha,
};

export default configuracionService;
