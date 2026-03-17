import api from './api';
import type { 
  Hijo, 
  Tarjeta, 
  CargaSaldo, 
  PaginatedResponse 
} from '../types';

export interface RecargaCajaData {
  hijo_id: number;
  monto: number;
  metodo_pago: 'efectivo' | 'tarjeta_pos';
  referencia?: string;
  empleado_id?: number;
}

export interface RecargaTransferenciaData {
  hijo_id: number;
  monto: number;
}

export interface ValidarTransferenciaData {
  codigo_referencia?: string;
  numero_comprobante: string;
  empleado_id?: number;
  hijo_id?: number;
  monto?: number;
  imagen_comprobante?: string;
}

export interface HijoParams {
  page?: number;
  page_size?: number;
  search?: string;
  id_cliente_responsable?: number;
  estado?: boolean;
}

export interface TarjetaParams {
  page?: number;
  page_size?: number;
  search?: string;
  estado?: string;
  id_hijo?: number;
}

export interface RecargaParams {
  page?: number;
  page_size?: number;
  estado?: string;
  nro_tarjeta?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
}

export const recargasService = {
  // Búsqueda de hijos/estudiantes
  buscarHijos: async (params?: HijoParams): Promise<PaginatedResponse<Hijo>> => {
    const response = await api.get<PaginatedResponse<Hijo>>('/hijos/', { params });
    return response.data;
  },

  getHijoById: async (id: number): Promise<Hijo> => {
    const response = await api.get<Hijo>(`/hijos/${id}/`);
    return response.data;
  },

  // Búsqueda de tarjetas
  buscarTarjetas: async (params?: TarjetaParams): Promise<PaginatedResponse<Tarjeta>> => {
    const response = await api.get<PaginatedResponse<Tarjeta>>('/tarjetas/', { params });
    return response.data;
  },

  getTarjetaByHijo: async (hijoId: number): Promise<Tarjeta> => {
    const response = await api.get<PaginatedResponse<Tarjeta>>('/tarjetas/', { 
      params: { id_hijo: hijoId } 
    });
    // Asumiendo que devuelve un array, tomamos el primero
    const tarjetas = response.data.results || [];
    if (tarjetas.length === 0) {
      throw new Error('No se encontró tarjeta para este hijo');
    }
    return tarjetas[0];
  },

  // Historial de recargas
  getRecargas: async (params?: RecargaParams): Promise<PaginatedResponse<CargaSaldo>> => {
    const response = await api.get<PaginatedResponse<CargaSaldo>>('/cargas-saldo/', { params });
    return response.data;
  },

  getRecargaById: async (id: number): Promise<CargaSaldo> => {
    const response = await api.get<CargaSaldo>(`/cargas-saldo/${id}/`);
    return response.data;
  },

  // Procesar recarga en caja (efectivo/POS)
  procesarRecargaCaja: async (data: RecargaCajaData): Promise<CargaSaldo> => {
    const response = await api.post<CargaSaldo>('/cargas-saldo/caja/', data);
    return response.data;
  },

  // Generar código de referencia para transferencia
  generarReferenciaTransferencia: async (data: RecargaTransferenciaData): Promise<{
    codigo_referencia: string;
    monto_transferir: number;
    datos_bancarios: any;
    instrucciones: string;
  }> => {
    const response = await api.post('/cargas-saldo/transferencia/referencia/', data);
    return response.data;
  },

  // Validar transferencia bancaria
  validarTransferencia: async (data: ValidarTransferenciaData): Promise<CargaSaldo> => {
    const response = await api.post<CargaSaldo>('/cargas-saldo/transferencia/validar/', data);
    return response.data;
  },

  // Aprobar recarga (supervisor)
  aprobarRecarga: async (recargaId: number, supervisorId?: number): Promise<CargaSaldo> => {
    const response = await api.post<CargaSaldo>(
      `/cargas-saldo/${recargaId}/aprobar/`,
      { supervisor_id: supervisorId }
    );
    return response.data;
  },
};
