/**
 * Servicio de Dashboard y KPIs
 * Gestión de dashboards personalizados y métricas en tiempo real
 */

import axios from '../utils/axiosConfig';
import {
  DashboardKPIs,
  DashboardVentas,
  DashboardRecargas,
  DashboardFinanciero,
} from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// ==================== KPIs Principales ====================

/**
 * Obtiene los KPIs principales del negocio
 * @param fecha Fecha para calcular (opcional, default: hoy)
 * @returns KPIs principales del día
 */
export const getKpisPrincipales = async (fecha?: string): Promise<DashboardKPIs> => {
  const response = await axios.get(`${API_URL}/reportes/kpis-principales/`, {
    params: { fecha },
  });
  return response.data;
};

// ==================== Dashboard de Ventas ====================

/**
 * Obtiene dashboard de ventas con análisis de últimos N días
 * @param dias Cantidad de días a analizar (default: 7)
 * @returns Dashboard completo de ventas
 */
export const getDashboardVentas = async (dias: number = 7): Promise<DashboardVentas> => {
  const response = await axios.get(`${API_URL}/reportes/dashboard-ventas/`, {
    params: { dias },
  });
  return response.data;
};

// ==================== Dashboard de Recargas ====================

/**
 * Obtiene dashboard de recargas con análisis de últimos N días
 * @param dias Cantidad de días a analizar (default: 7)
 * @returns Dashboard completo de recargas
 */
export const getDashboardRecargas = async (dias: number = 7): Promise<DashboardRecargas> => {
  const response = await axios.get(`${API_URL}/reportes/dashboard-recargas/`, {
    params: { dias },
  });
  return response.data;
};

// ==================== Dashboard Financiero ====================

/**
 * Obtiene dashboard financiero con estado del mes
 * @param mes Mes a analizar (1-12, opcional, default: mes actual)
 * @returns Dashboard completo financiero
 */
export const getDashboardFinanciero = async (mes?: number): Promise<DashboardFinanciero> => {
  const response = await axios.get(`${API_URL}/reportes/dashboard-financiero/`, {
    params: { mes },
  });
  return response.data;
};

// ==================== Utilidades ====================

/**
 * Formatea montos a moneda local
 */
export const formatearMoneda = (monto: number): string => {
  return new Intl.NumberFormat('es-PY', {
    style: 'currency',
    currency: 'PYG',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(monto);
};

/**
 * Formatea porcentaje
 */
export const formatearPorcentaje = (valor: number, decimales: number = 1): string => {
  return `${valor.toFixed(decimales)}%`;
};

/**
 * Obtiene color según tendencia
 */
export const getTendenciaColor = (tendencia: 'crecimiento' | 'decrecimiento' | 'estable'): string => {
  const colores: Record<string, string> = {
    crecimiento: 'text-green-600',
    decrecimiento: 'text-red-600',
    estable: 'text-gray-600',
  };
  return colores[tendencia] || 'text-gray-600';
};

/**
 * Obtiene icono según tendencia
 */
export const getTendenciaIcono = (tendencia: 'crecimiento' | 'decrecimiento' | 'estable'): string => {
  const iconos: Record<string, string> = {
    crecimiento: '↗',
    decrecimiento: '↘',
    estable: '→',
  };
  return iconos[tendencia] || '→';
};

/**
 * Calcula variación porcentual
 */
export const calcularVariacion = (actual: number, anterior: number): number => {
  if (anterior === 0) return actual > 0 ? 100 : 0;
  return ((actual - anterior) / anterior) * 100;
};

// Export default con todos los métodos
const dashboardService = {
  getKpisPrincipales,
  getDashboardVentas,
  getDashboardRecargas,
  getDashboardFinanciero,
  formatearMoneda,
  formatearPorcentaje,
  getTendenciaColor,
  getTendenciaIcono,
  calcularVariacion,
};

export default dashboardService;
