/**
 * Servicio para gestión de Reportes y Estadísticas
 * 
 * Funcionalidades:
 * - Reportes de ventas
 * - Reportes de recargas
 * - Reportes de top productos
 * - Reportes de consumos por tarjeta
 * - Reportes financieros consolidados
 * - Dashboards (KPIs, ventas, recargas, financiero)
 */

import api from './api';
import type {
  ReporteVentas,
  ReporteVentasParams,
  ReporteRecargas,
  ReporteRecargasParams,
  ReporteTopProductos,
  ReporteTopProductosParams,
  ReporteConsumosTarjeta,
  ReporteConsumosTarjetaParams,
  ReporteFinanciero,
  ReporteFinancieroParams,
  DashboardKPIs,
  DashboardVentas,
  DashboardVentasParams,
  DashboardRecargas,
  DashboardRecargasParams,
  DashboardFinanciero,
  DashboardFinancieroParams,
} from '../types';

// ============================================================================
// Reportes
// ============================================================================

/**
 * Genera reporte de ventas con filtros
 */
export async function getReporteVentas(params: ReporteVentasParams): Promise<ReporteVentas> {
  const response = await api.get<ReporteVentas>(`/reportes/ventas/`, { params });
  return response.data;
}

/**
 * Genera reporte de recargas con filtros
 */
export async function getReporteRecargas(params: ReporteRecargasParams): Promise<ReporteRecargas> {
  const response = await api.get<ReporteRecargas>(`/reportes/recargas/`, { params });
  return response.data;
}

/**
 * Genera reporte de productos más vendidos
 */
export async function getReporteTopProductos(params: ReporteTopProductosParams): Promise<ReporteTopProductos> {
  const response = await api.get<ReporteTopProductos>(`/reportes/top-productos/`, { params });
  return response.data;
}

/**
 * Genera reporte de consumos de una tarjeta específica
 */
export async function getReporteConsumosTarjeta(params: ReporteConsumosTarjetaParams): Promise<ReporteConsumosTarjeta> {
  const response = await api.get<ReporteConsumosTarjeta>(`/reportes/consumos-tarjeta/`, { params });
  return response.data;
}

/**
 * Genera reporte financiero consolidado
 */
export async function getReporteFinanciero(params: ReporteFinancieroParams): Promise<ReporteFinanciero> {
  const response = await api.get<ReporteFinanciero>(`/reportes/financiero/`, { params });
  return response.data;
}

// ============================================================================
// Dashboards y KPIs
// ============================================================================

/**
 * Obtiene KPIs principales del día
 */
export async function getKPIsPrincipales(fecha?: string): Promise<DashboardKPIs> {
  const params = fecha ? { fecha } : {};
  const response = await api.get<DashboardKPIs>(`/reportes/kpis-principales/`, { params });
  return response.data;
}

/**
 * Obtiene dashboard de ventas (últimos N días)
 */
export async function getDashboardVentas(params: DashboardVentasParams = {}): Promise<DashboardVentas> {
  const response = await api.get<DashboardVentas>(`/reportes/dashboard-ventas/`, { params });
  return response.data;
}

/**
 * Obtiene dashboard de recargas (últimos N días)
 */
export async function getDashboardRecargas(params: DashboardRecargasParams = {}): Promise<DashboardRecargas> {
  const response = await api.get<DashboardRecargas>(`/reportes/dashboard-recargas/`, { params });
  return response.data;
}

/**
 * Obtiene dashboard financiero mensual
 */
export async function getDashboardFinanciero(params: DashboardFinancieroParams = {}): Promise<DashboardFinanciero> {
  const response = await api.get<DashboardFinanciero>(`/reportes/dashboard-financiero/`, { params });
  return response.data;
}

// ============================================================================
// Exportación de reportes
// ============================================================================

/**
 * Exporta reporte a PDF
 */
export async function exportarReportePDF(tipo: string, params: Record<string, any>): Promise<Blob> {
  const response = await api.get(`/reportes/exportar-pdf/`, {
    params: { tipo, ...params },
    responseType: 'blob'
  });
  return response.data;
}

/**
 * Exporta reporte a Excel
 */
export async function exportarReporteExcel(tipo: string, params: Record<string, any>): Promise<Blob> {
  const response = await api.get(`/reportes/exportar-excel/`, {
    params: { tipo, ...params },
    responseType: 'blob'
  });
  return response.data;
}

// ============================================================================
// Funciones auxiliares
// ============================================================================

/**
 * Helper: Descarga archivo blob con nombre específico
 */
export function descargarArchivo(blob: Blob, nombreArchivo: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = nombreArchivo;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Helper: Formatea número como moneda guaraníes
 */
export function formatearMoneda(valor: number): string {
  return new Intl.NumberFormat('es-PY', {
    style: 'currency',
    currency: 'PYG',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(valor);
}

/**
 * Helper: Formatea fecha a formato local
 */
export function formatearFecha(fecha: string): string {
  return new Date(fecha).toLocaleDateString('es-PY', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
}

/**
 * Helper: Formatea fecha con hora
 */
export function formatearFechaHora(fecha: string): string {
  return new Date(fecha).toLocaleString('es-PY', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * Helper: Calcula rango de fechas predefinido
 */
export function calcularRangoFechas(tipo: 'hoy' | 'ayer' | 'semana' | 'mes' | 'año'): { fecha_inicio: string; fecha_fin: string } {
  const hoy = new Date();
  const fecha_fin = hoy.toISOString().split('T')[0];
  let fecha_inicio: string;

  switch (tipo) {
    case 'hoy':
      fecha_inicio = fecha_fin;
      break;
    case 'ayer':
      const ayer = new Date(hoy);
      ayer.setDate(ayer.getDate() - 1);
      fecha_inicio = ayer.toISOString().split('T')[0];
      break;
    case 'semana':
      const semana = new Date(hoy);
      semana.setDate(semana.getDate() - 7);
      fecha_inicio = semana.toISOString().split('T')[0];
      break;
    case 'mes':
      const mes = new Date(hoy);
      mes.setMonth(mes.getMonth() - 1);
      fecha_inicio = mes.toISOString().split('T')[0];
      break;
    case 'año':
      const año = new Date(hoy);
      año.setFullYear(año.getFullYear() - 1);
      fecha_inicio = año.toISOString().split('T')[0];
      break;
    default:
      fecha_inicio = fecha_fin;
  }

  return { fecha_inicio, fecha_fin };
}

const reportesService = {
  // Reportes
  getReporteVentas,
  getReporteRecargas,
  getReporteTopProductos,
  getReporteConsumosTarjeta,
  getReporteFinanciero,
  
  // Dashboards
  getKPIsPrincipales,
  getDashboardVentas,
  getDashboardRecargas,
  getDashboardFinanciero,
  
  // Exportación
  exportarReportePDF,
  exportarReporteExcel,
  
  // Helpers
  descargarArchivo,
  formatearMoneda,
  formatearFecha,
  formatearFechaHora,
  calcularRangoFechas,
};

export default reportesService;
