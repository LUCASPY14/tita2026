import api from './api';
import { 
  Proveedor, 
  Compra, 
  CompraData,
  PaginatedResponse,
  CuentaCorrienteProveedor 
} from '../types';

export interface ProveedorParams {
  page?: number;
  page_size?: number;
  search?: string;
  activo?: boolean;
  ciudad?: string;
  ordering?: string;
}

export interface CompraParams {
  page?: number;
  page_size?: number;
  search?: string;
  estado_pago?: 'Pendiente' | 'Parcial' | 'Pagado';
  id_proveedor?: number;
  ordering?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
}

export interface ProveedorData {
  ruc: string;
  razon_social: string;
  telefono?: string;
  email?: string;
  direccion?: string;
  ciudad?: string;
  activo: boolean;
}

export const comprasService = {
  // === PROVEEDORES ===
  
  getProveedores: async (params?: ProveedorParams): Promise<PaginatedResponse<Proveedor>> => {
    const response = await api.get<PaginatedResponse<Proveedor>>('/proveedores/', { params });
    return response.data;
  },

  getProveedorById: async (id: number): Promise<Proveedor> => {
    const response = await api.get<Proveedor>(`/proveedores/${id}/`);
    return response.data;
  },

  buscarPorRuc: async (ruc: string): Promise<PaginatedResponse<Proveedor>> => {
    const response = await api.get<PaginatedResponse<Proveedor>>('/proveedores/', {
      params: { search: ruc }
    });
    return response.data;
  },

  crearProveedor: async (data: ProveedorData): Promise<Proveedor> => {
    const response = await api.post<Proveedor>('/proveedores/', data);
    return response.data;
  },

  actualizarProveedor: async (id: number, data: Partial<ProveedorData>): Promise<Proveedor> => {
    const response = await api.patch<Proveedor>(`/proveedores/${id}/`, data);
    return response.data;
  },

  eliminarProveedor: async (id: number): Promise<void> => {
    await api.delete(`/proveedores/${id}/`);
  },

  toggleEstadoProveedor: async (id: number, activo: boolean): Promise<Proveedor> => {
    const response = await api.patch<Proveedor>(`/proveedores/${id}/`, { activo });
    return response.data;
  },

  getCuentaCorrienteProveedor: async (id: number): Promise<CuentaCorrienteProveedor> => {
    const response = await api.get<CuentaCorrienteProveedor>(`/proveedores/${id}/cuenta_corriente/`);
    return response.data;
  },

  // === COMPRAS ===
  
  getCompras: async (params?: CompraParams): Promise<PaginatedResponse<Compra>> => {
    const response = await api.get<PaginatedResponse<Compra>>('/compras/', { params });
    return response.data;
  },

  getCompraById: async (id: number): Promise<Compra> => {
    const response = await api.get<Compra>(`/compras/${id}/`);
    return response.data;
  },

  crearCompra: async (data: CompraData): Promise<Compra> => {
    const response = await api.post<Compra>('/compras/', data);
    return response.data;
  },

  actualizarCompra: async (id: number, data: Partial<CompraData>): Promise<Compra> => {
    const response = await api.patch<Compra>(`/compras/${id}/`, data);
    return response.data;
  },

  eliminarCompra: async (id: number): Promise<void> => {
    await api.delete(`/compras/${id}/`);
  },

  confirmarCompra: async (id: number): Promise<Compra> => {
    const response = await api.post<{ compra: Compra; mensaje: string }>(`/compras/${id}/confirmar/`);
    return response.data.compra;
  },

  getComprasPendientes: async (): Promise<Compra[]> => {
    const response = await api.get<Compra[]>('/compras/pendientes/');
    return response.data;
  },

  // === ESTADÍSTICAS ===
  
  getEstadisticasCompras: async (): Promise<{
    total_compras: number;
    compras_pendientes: number;
    monto_total: number;
    saldo_pendiente: number;
  }> => {
    const response = await api.get('/compras/estadisticas/');
    return response.data;
  },
};
