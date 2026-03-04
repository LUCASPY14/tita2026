/**
 * Hook personalizado para gestión de dashboards y KPIs
 * Proporciona acceso a métricas en tiempo real y dashboards personalizados
 */

import { useState, useCallback, useEffect } from 'react';
import dashboardService from '../services/dashboard.service';
import type {
  DashboardKPIs,
  DashboardVentas,
  DashboardRecargas,
  DashboardFinanciero,
} from '../types';

export interface UseDashboardReturn {
  // Estados
  kpis: DashboardKPIs | null;
  dashboardVentas: DashboardVentas | null;
  dashboardRecargas: DashboardRecargas | null;
  dashboardFinanciero: DashboardFinanciero | null;
  cargando: boolean;
  error: string | null;
  
  // Configuración
  diasAnalisis: number;
  mesFinanciero: number | undefined;
  
  // Métodos
  cargarKpis: (fecha?: string) => Promise<void>;
  cargarDashboardVentas: (dias?: number) => Promise<void>;
  cargarDashboardRecargas: (dias?: number) => Promise<void>;
  cargarDashboardFinanciero: (mes?: number) => Promise<void>;
  cambiarDiasAnalisis: (dias: number) => void;
  cambiarMesFinanciero: (mes: number) => void;
  refrescarTodo: () => Promise<void>;
}

const DIAS_DEFAULT = 7;

/**
 * Hook para gestión de dashboards y KPIs
 * 
 * @example
 * ```tsx
 * const { kpis, dashboardVentas, cargarKpis, cargarDashboardVentas } = useDashboard();
 * ```
 */
export const useDashboard = (): UseDashboardReturn => {
  // Estados de datos
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [dashboardVentas, setDashboardVentas] = useState<DashboardVentas | null>(null);
  const [dashboardRecargas, setDashboardRecargas] = useState<DashboardRecargas | null>(null);
  const [dashboardFinanciero, setDashboardFinanciero] = useState<DashboardFinanciero | null>(null);
  
  // Estados de UI
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Estados de configuración
  const [diasAnalisis, setDiasAnalisis] = useState(DIAS_DEFAULT);
  const [mesFinanciero, setMesFinanciero] = useState<number | undefined>(undefined);

  /**
   * Carga KPIs principales
   */
  const cargarKpis = useCallback(async (fecha?: string) => {
    try {
      setCargando(true);
      setError(null);
      
      const data = await dashboardService.getKpisPrincipales(fecha);
      setKpis(data);
    } catch (err: any) {
      console.error('Error cargando KPIs:', err);
      setError(err.response?.data?.message || 'Error al cargar KPIs');
      setKpis(null);
    } finally {
      setCargando(false);
    }
  }, []);

  /**
   * Carga dashboard de ventas
   */
  const cargarDashboardVentas = useCallback(async (dias?: number) => {
    try {
      setCargando(true);
      setError(null);
      
      const diasFinal = dias || diasAnalisis;
      const data = await dashboardService.getDashboardVentas(diasFinal);
      setDashboardVentas(data);
    } catch (err: any) {
      console.error('Error cargando dashboard de ventas:', err);
      setError(err.response?.data?.message || 'Error al cargar dashboard de ventas');
      setDashboardVentas(null);
    } finally {
      setCargando(false);
    }
  }, [diasAnalisis]);

  /**
   * Carga dashboard de recargas
   */
  const cargarDashboardRecargas = useCallback(async (dias?: number) => {
    try {
      setCargando(true);
      setError(null);
      
      const diasFinal = dias || diasAnalisis;
      const data = await dashboardService.getDashboardRecargas(diasFinal);
      setDashboardRecargas(data);
    } catch (err: any) {
      console.error('Error cargando dashboard de recargas:', err);
      setError(err.response?.data?.message || 'Error al cargar dashboard de recargas');
      setDashboardRecargas(null);
    } finally {
      setCargando(false);
    }
  }, [diasAnalisis]);

  /**
   * Carga dashboard financiero
   */
  const cargarDashboardFinanciero = useCallback(async (mes?: number) => {
    try {
      setCargando(true);
      setError(null);
      
      const mesFinal = mes || mesFinanciero;
      const data = await dashboardService.getDashboardFinanciero(mesFinal);
      setDashboardFinanciero(data);
    } catch (err: any) {
      console.error('Error cargando dashboard financiero:', err);
      setError(err.response?.data?.message || 'Error al cargar dashboard financiero');
      setDashboardFinanciero(null);
    } finally {
      setCargando(false);
    }
  }, [mesFinanciero]);

  /**
   * Cambia el período de análisis en días
   */
  const cambiarDiasAnalisis = useCallback((dias: number) => {
    setDiasAnalisis(dias);
  }, []);

  /**
   * Cambia el mes del dashboard financiero
   */
  const cambiarMesFinanciero = useCallback((mes: number) => {
    setMesFinanciero(mes);
  }, []);

  /**
   * Refresca todos los dashboards
   */
  const refrescarTodo = useCallback(async () => {
    await Promise.all([
      cargarKpis(),
      cargarDashboardVentas(),
      cargarDashboardRecargas(),
      cargarDashboardFinanciero(),
    ]);
  }, [cargarKpis, cargarDashboardVentas, cargarDashboardRecargas, cargarDashboardFinanciero]);

  // Cargar KPIs automáticamente al montar
  useEffect(() => {
    cargarKpis();
  }, [cargarKpis]);

  return {
    // Estados
    kpis,
    dashboardVentas,
    dashboardRecargas,
    dashboardFinanciero,
    cargando,
    error,
    
    // Configuración
    diasAnalisis,
    mesFinanciero,
    
    // Métodos
    cargarKpis,
    cargarDashboardVentas,
    cargarDashboardRecargas,
    cargarDashboardFinanciero,
    cambiarDiasAnalisis,
    cambiarMesFinanciero,
    refrescarTodo,
  };
};

export default useDashboard;
