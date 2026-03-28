/**
 * Hook personalizado para gestión de auditoría
 * Proporciona acceso a logs, estadísticas y filtros avanzados
 */

import { useState, useCallback, useEffect } from 'react';
import auditoriaService from '../services/auditoria.service';
import type {
  AuditoriaOperacion,
  FiltrosAuditoria,
  EstadisticasAuditoria,
  TimelineAuditoria,
  ActividadUsuario,
} from '../types';

export interface UseAuditoriaReturn {
  // Estados
  logs: AuditoriaOperacion[];
  logSeleccionado: AuditoriaOperacion | null;
  estadisticas: EstadisticasAuditoria | null;
  timeline: TimelineAuditoria[];
  actividadUsuario: ActividadUsuario | null;
  cargando: boolean;
  error: string | null;
  
  // Paginación
  totalRegistros: number;
  paginaActual: number;
  totalPaginas: number;
  
  // Filtros
  filtros: FiltrosAuditoria;
  
  // Métodos
  cargarLogs: (filtros?: FiltrosAuditoria) => Promise<void>;
  cargarLogPorId: (id: number) => Promise<void>;
  cargarEstadisticas: (filtros?: FiltrosAuditoria) => Promise<void>;
  cargarTimeline: (filtros?: FiltrosAuditoria) => Promise<void>;
  cargarActividadUsuario: (idUsuario: number, filtros?: FiltrosAuditoria) => Promise<void>;
  aplicarFiltros: (nuevosFiltros: FiltrosAuditoria) => void;
  cambiarPagina: (pagina: number) => void;
  limpiarFiltros: () => void;
  refrescar: () => Promise<void>;
}

const FILTROS_INICIALES: FiltrosAuditoria = {
  page: 1,
  page_size: 20,
  ordering: '-fecha_operacion',
};

/**
 * Hook para gestión de auditoría del sistema
 * 
 * @example
 * ```tsx
 * const { logs, estadisticas, cargarLogs, aplicarFiltros } = useAuditoria();
 * ```
 */
export const useAuditoria = (): UseAuditoriaReturn => {
  // Estados de datos
  const [logs, setLogs] = useState<AuditoriaOperacion[]>([]);
  const [logSeleccionado, setLogSeleccionado] = useState<AuditoriaOperacion | null>(null);
  const [estadisticas, setEstadisticas] = useState<EstadisticasAuditoria | null>(null);
  const [timeline, setTimeline] = useState<TimelineAuditoria[]>([]);
  const [actividadUsuario, setActividadUsuario] = useState<ActividadUsuario | null>(null);
  
  // Estados de UI
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Estados de paginación
  const [totalRegistros, setTotalRegistros] = useState(0);
  const [paginaActual, setPaginaActual] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(0);
  
  // Estado de filtros
  const [filtros, setFiltros] = useState<FiltrosAuditoria>(FILTROS_INICIALES);

  /**
   * Carga logs de auditoría con filtros
   */
  const cargarLogs = useCallback(async (filtrosAdicionales?: FiltrosAuditoria) => {
    try {
      setCargando(true);
      setError(null);
      
      const filtrosFinales = { ...filtros, ...filtrosAdicionales };
      const response = await auditoriaService.getLogsAuditoria(filtrosFinales);
      
      setLogs(response.results || []);
      setTotalRegistros(response.count || 0);
      
      const pageSize = filtrosFinales.page_size || 20;
      setTotalPaginas(Math.ceil((response.count || 0) / pageSize));
      
      if (filtrosFinales.page) {
        setPaginaActual(filtrosFinales.page);
      }
    } catch (err: any) {
      console.error('Error cargando logs de auditoría:', err);
      setError(err.response?.data?.message || 'Error al cargar logs de auditoría');
      setLogs([]);
    } finally {
      setCargando(false);
    }
  }, [filtros]);

  /**
   * Carga un log específico por ID
   */
  const cargarLogPorId = useCallback(async (id: number) => {
    try {
      setCargando(true);
      setError(null);
      
      const log = await auditoriaService.getLogAuditoriaById(id);
      setLogSeleccionado(log);
    } catch (err: any) {
      console.error('Error cargando log de auditoría:', err);
      setError(err.response?.data?.message || 'Error al cargar log de auditoría');
      setLogSeleccionado(null);
    } finally {
      setCargando(false);
    }
  }, []);

  /**
   * Carga estadísticas de auditoría
   */
  const cargarEstadisticas = useCallback(async (filtrosAdicionales?: FiltrosAuditoria) => {
    try {
      setCargando(true);
      setError(null);
      
      const filtrosFinales = { ...filtros, ...filtrosAdicionales };
      // Excluir parámetros de paginación para estadísticas
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { page: _page, page_size: _pageSize, ...filtrosStats } = filtrosFinales;
      
      const stats = await auditoriaService.getEstadisticasAuditoria(filtrosStats);
      setEstadisticas(stats);
    } catch (err: any) {
      console.error('Error cargando estadísticas:', err);
      setError(err.response?.data?.message || 'Error al cargar estadísticas');
      setEstadisticas(null);
    } finally {
      setCargando(false);
    }
  }, [filtros]);

  /**
   * Carga timeline de operaciones
   */
  const cargarTimeline = useCallback(async (filtrosAdicionales?: FiltrosAuditoria) => {
    try {
      setCargando(true);
      setError(null);
      
      const filtrosFinales = { ...filtros, ...filtrosAdicionales };
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { page: _page, page_size: _pageSize, ...filtrosTimeline } = filtrosFinales;
      
      const timelineData = await auditoriaService.getTimelineAuditoria(filtrosTimeline);
      setTimeline(timelineData);
    } catch (err: any) {
      console.error('Error cargando timeline:', err);
      setError(err.response?.data?.message || 'Error al cargar timeline');
      setTimeline([]);
    } finally {
      setCargando(false);
    }
  }, [filtros]);

  /**
   * Carga actividad de un usuario específico
   */
  const cargarActividadUsuario = useCallback(async (
    idUsuario: number,
    filtrosAdicionales?: FiltrosAuditoria
  ) => {
    try {
      setCargando(true);
      setError(null);
      
      const filtrosFinales = { ...filtrosAdicionales };
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { page: _page, page_size: _pageSize, ...filtrosActividad } = filtrosFinales;
      
      const actividad = await auditoriaService.getActividadUsuario(idUsuario, filtrosActividad);
      setActividadUsuario(actividad);
    } catch (err: any) {
      console.error('Error cargando actividad de usuario:', err);
      setError(err.response?.data?.message || 'Error al cargar actividad de usuario');
      setActividadUsuario(null);
    } finally {
      setCargando(false);
    }
  }, []);

  /**
   * Aplica nuevos filtros y recarga logs
   */
  const aplicarFiltros = useCallback((nuevosFiltros: FiltrosAuditoria) => {
    const filtrosActualizados = {
      ...filtros,
      ...nuevosFiltros,
      page: 1, // Resetear a primera página al filtrar
    };
    setFiltros(filtrosActualizados);
  }, [filtros]);

  /**
   * Cambia la página actual
   */
  const cambiarPagina = useCallback((pagina: number) => {
    if (pagina >= 1 && pagina <= totalPaginas) {
      setFiltros(prev => ({ ...prev, page: pagina }));
    }
  }, [totalPaginas]);

  /**
   * Limpia todos los filtros
   */
  const limpiarFiltros = useCallback(() => {
    setFiltros(FILTROS_INICIALES);
  }, []);

  /**
   * Refresca todos los datos
   */
  const refrescar = useCallback(async () => {
    await Promise.all([
      cargarLogs(),
      cargarEstadisticas(),
      cargarTimeline(),
    ]);
  }, [cargarLogs, cargarEstadisticas, cargarTimeline]);

  // Cargar logs cuando cambian los filtros
  useEffect(() => {
    cargarLogs(filtros);
  }, [filtros, cargarLogs]);

  return {
    // Estados
    logs,
    logSeleccionado,
    estadisticas,
    timeline,
    actividadUsuario,
    cargando,
    error,
    
    // Paginación
    totalRegistros,
    paginaActual,
    totalPaginas,
    
    // Filtros
    filtros,
    
    // Métodos
    cargarLogs,
    cargarLogPorId,
    cargarEstadisticas,
    cargarTimeline,
    cargarActividadUsuario,
    aplicarFiltros,
    cambiarPagina,
    limpiarFiltros,
    refrescar,
  };
};

export default useAuditoria;
