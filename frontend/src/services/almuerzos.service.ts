import api from './api';
import type { 
  RegistroConsumoData,
  Alergeno
} from '../types';

// Interfaces para parámetros
export interface PlanParams {
  estado?: boolean;
  search?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface TipoParams {
  estado?: boolean;
  search?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface SuscripcionParams {
  estado?: 'Activa' | 'Pendiente' | 'Finalizada' | 'Cancelada';
  id_hijo?: number;
  id_plan_almuerzo?: number;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface RegistroParams {
  estado?: string;
  id_hijo?: number;
  fecha_consumo?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  ya_cobrado?: boolean;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface PlanData {
  nombre_plan: string;
  descripcion?: string;
  precio_mensual: number;
  dias_semana_incluidos: string;
  estado?: boolean;
}

export interface TipoData {
  nombre: string;
  descripcion?: string;
  precio_unitario: number;
  incluye_plato_principal?: boolean;
  incluye_postre?: boolean;
  incluye_bebida?: boolean;
  estado?: boolean;
}

export interface SuscripcionData {
  fecha_inicio: string;
  fecha_fin?: string;
  estado?: string;
  id_hijo: number;
  id_plan_almuerzo: number;
}

export const almuerzosService = {
  // === PLANES DE ALMUERZO ===
  async getPlanes(params?: PlanParams) {
    const response = await api.get('/planes-almuerzo/', { params });
    return response.data;
  },

  async getPlanById(id: number) {
    const response = await api.get(`/planes-almuerzo/${id}/`);
    return response.data;
  },

  async crearPlan(data: PlanData) {
    const response = await api.post('/planes-almuerzo/', data);
    return response.data;
  },

  async actualizarPlan(id: number, data: Partial<PlanData>) {
    const response = await api.patch(`/planes-almuerzo/${id}/`, data);
    return response.data;
  },

  async eliminarPlan(id: number) {
    const response = await api.delete(`/planes-almuerzo/${id}/`);
    return response.data;
  },

  async toggleEstadoPlan(id: number, estado: boolean) {
    const response = await api.patch(`/planes-almuerzo/${id}/`, { estado });
    return response.data;
  },

  // === TIPOS DE ALMUERZO ===
  async getTipos(params?: TipoParams) {
    const response = await api.get('/tipos-almuerzo/', { params });
    return response.data;
  },

  async getTipoById(id: number) {
    const response = await api.get(`/tipos-almuerzo/${id}/`);
    return response.data;
  },

  async crearTipo(data: TipoData) {
    const response = await api.post('/tipos-almuerzo/', data);
    return response.data;
  },

  async actualizarTipo(id: number, data: Partial<TipoData>) {
    const response = await api.patch(`/tipos-almuerzo/${id}/`, data);
    return response.data;
  },

  async eliminarTipo(id: number) {
    const response = await api.delete(`/tipos-almuerzo/${id}/`);
    return response.data;
  },

  async toggleEstadoTipo(id: number, estado: boolean) {
    const response = await api.patch(`/tipos-almuerzo/${id}/`, { estado });
    return response.data;
  },

  // === SUSCRIPCIONES ===
  async getSuscripciones(params?: SuscripcionParams) {
    const response = await api.get('/suscripciones-almuerzo/', { params });
    return response.data;
  },

  async getSuscripcionById(id: number) {
    const response = await api.get(`/suscripciones-almuerzo/${id}/`);
    return response.data;
  },

  async crearSuscripcion(data: SuscripcionData) {
    const response = await api.post('/suscripciones-almuerzo/', data);
    return response.data;
  },

  async actualizarSuscripcion(id: number, data: Partial<SuscripcionData>) {
    const response = await api.patch(`/suscripciones-almuerzo/${id}/`, data);
    return response.data;
  },

  async eliminarSuscripcion(id: number) {
    const response = await api.delete(`/suscripciones-almuerzo/${id}/`);
    return response.data;
  },

  async getSuscripcionesPorHijo(idHijo: number) {
    const response = await api.get('/suscripciones-almuerzo/', {
      params: { id_hijo: idHijo }
    });
    return response.data;
  },

  async getSuscripcionesActivas() {
    const response = await api.get('/suscripciones-almuerzo/', {
      params: { estado: 'Activa' }
    });
    return response.data;
  },

  // === REGISTROS DE CONSUMO ===
  async getRegistros(params?: RegistroParams) {
    const response = await api.get('/registros-consumo-almuerzo/', { params });
    return response.data;
  },

  async getRegistroById(id: number) {
    const response = await api.get(`/registros-consumo-almuerzo/${id}/`);
    return response.data;
  },

  async registrarConsumo(data: RegistroConsumoData) {
    const response = await api.post('/registros-consumo-almuerzo/', data);
    return response.data;
  },

  async getRegistrosHoy(idHijo?: number) {
    const hoy = new Date().toISOString().split('T')[0];
    const params: RegistroParams = {
      fecha_consumo: hoy,
      ...(idHijo && { id_hijo: idHijo })
    };
    const response = await api.get('/registros-consumo-almuerzo/', { params });
    return response.data;
  },

  async getRegistrosPorHijo(idHijo: number, fechaDesde?: string, fechaHasta?: string) {
    const params: RegistroParams = {
      id_hijo: idHijo,
      ...(fechaDesde && { fecha_desde: fechaDesde }),
      ...(fechaHasta && { fecha_hasta: fechaHasta }),
      ordering: '-fecha_consumo,-hora_registro'
    };
    const response = await api.get('/registros-consumo-almuerzo/', { params });
    return response.data;
  },

  async getRegistrosDelDia(fecha: string) {
    const response = await api.get('/registros-consumo-almuerzo/', {
      params: { fecha_consumo: fecha, ordering: '-hora_registro' }
    });
    return response.data;
  },

  // === CUENTAS MENSUALES ===
  async getCuentasMensuales(params?: { id_hijo?: number; anio?: number; mes?: number; estado?: string }) {
    const response = await api.get('/cuentas-almuerzo-mensual/', { params });
    return response.data;
  },

  async getCuentaMensualById(id: number) {
    const response = await api.get(`/cuentas-almuerzo-mensual/${id}/`);
    return response.data;
  },

  // === ALÉRGENOS ===
  async getAlergenos(params?: { estado?: boolean; search?: string }) {
    const response = await api.get('/alergenos/', { params });
    return response.data;
  },

  async getAlergenoById(id: number) {
    const response = await api.get(`/alergenos/${id}/`);
    return response.data;
  },

  async crearAlergeno(data: Partial<Alergeno>) {
    const response = await api.post('/alergenos/', data);
    return response.data;
  },

  async actualizarAlergeno(id: number, data: Partial<Alergeno>) {
    const response = await api.patch(`/alergenos/${id}/`, data);
    return response.data;
  },

  async eliminarAlergeno(id: number) {
    const response = await api.delete(`/alergenos/${id}/`);
    return response.data;
  },

  // === ESTADÍSTICAS ===
  async getEstadisticasConsumos(idHijo?: number) {
    // Esta función podría requerir un endpoint personalizado en el backend
    // Por ahora retornamos datos calculados del frontend
    const params: RegistroParams = {
      ...(idHijo && { id_hijo: idHijo }),
      estado: 'Confirmado'
    };
    const response = await api.get('/registros-consumo-almuerzo/', { params });
    return response.data;
  }
};
