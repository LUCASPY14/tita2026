import api from './api';
import { Venta, PaginatedResponse, CondicionVenta } from '../types';

export interface VentaCreateData {
  cliente_id: number;
  metodo_pago: 'EFECTIVO' | 'TARJETA' | 'TRANSFERENCIA' | 'CREDITO';
  items: {
    producto_id: number;
    cantidad: number;
    precio_unitario: number;
  }[];
}

export interface VentaParams {
  page?: number;
  page_size?: number;
  fecha_desde?: string;
  fecha_hasta?: string;
  estado?: 'PENDIENTE' | 'COMPLETADA' | 'CANCELADA';
  cliente_id?: number;
}

export interface CancelarVentaResponse {
  id: number;
  estado: string;
  mensaje: string;
}

export const ventasService = {
  getAll: async (params?: VentaParams): Promise<PaginatedResponse<Venta>> => {
    const response = await api.get<PaginatedResponse<Venta>>('/ventas/', { params });
    return response.data;
  },

  getById: async (id: number): Promise<Venta> => {
    const response = await api.get<Venta>(`/ventas/${id}/`);
    return response.data;
  },

  create: async (data: VentaCreateData): Promise<Venta> => {
    const response = await api.post<Venta>('/ventas/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<VentaCreateData>): Promise<Venta> => {
    const response = await api.put<Venta>(`/ventas/${id}/`, data);
    return response.data;
  },

  cancel: async (id: number): Promise<CancelarVentaResponse> => {
    const response = await api.post<CancelarVentaResponse>(`/ventas/${id}/cancelar/`);
    return response.data;
  },
};


export const condicionesVentaService = {
  getCondicionesVenta: async (): Promise<CondicionVenta[]> => {
    const response = await api.get<PaginatedResponse<CondicionVenta>>('/condiciones-venta/', { params: { page_size: 100 } });
    return response.data.results || [];
  },
  crear: async (nombre: string): Promise<CondicionVenta> => {
    const response = await api.post<CondicionVenta>('/condiciones-venta/', { nombre });
    return response.data;
  },
  actualizar: async (id: number, nombre: string): Promise<CondicionVenta> => {
    const response = await api.patch<CondicionVenta>(`/condiciones-venta/${id}/`, { nombre });
    return response.data;
  },
  eliminar: async (id: number): Promise<void> => {
    await api.delete(`/condiciones-venta/${id}/`);
  },
};
