import api from './api';
import type { 
  Producto, 
  Categoria,
  Venta,
  VentaData,
  MedioPago,
  PaginatedResponse 
} from '../types';

export interface ProductoParams {
  page?: number;
  page_size?: number;
  search?: string;
  activo?: boolean;
  id_categoria?: number;
}

export interface CategoriaParams {
  page?: number;
  page_size?: number;
  activo?: boolean;
}

export interface VentaParams {
  page?: number;
  page_size?: number;
  estado_pago?: string;
  estado?: string;
  tipo_venta?: string;
  fecha?: string;
}

export const posService = {
  // Productos
  getProductos: async (params?: ProductoParams): Promise<PaginatedResponse<Producto>> => {
    const response = await api.get<PaginatedResponse<Producto>>('/productos/', { params });
    return response.data;
  },

  getProductoById: async (id: number): Promise<Producto> => {
    const response = await api.get<Producto>(`/productos/${id}/`);
    return response.data;
  },

  buscarProductoPorCodigo: async (codigo: string): Promise<Producto> => {
    const response = await api.get<PaginatedResponse<Producto>>('/productos/', {
      params: { search: codigo, activo: true }
    });
    const productos = response.data.results || [];
    if (productos.length === 0) {
      throw new Error('Producto no encontrado');
    }
    return productos[0];
  },

  // Categorías
  getCategorias: async (params?: CategoriaParams): Promise<PaginatedResponse<Categoria>> => {
    const response = await api.get<PaginatedResponse<Categoria>>('/categorias/', { params });
    return response.data;
  },

  // Medios de Pago
  getMediosPago: async (): Promise<MedioPago[]> => {
    const response = await api.get<PaginatedResponse<MedioPago>>('/medios-pago/', {
      params: { activo: true, page_size: 100 }
    });
    return response.data.results || [];
  },

  // Ventas
  crearVenta: async (data: VentaData): Promise<Venta> => {
    const response = await api.post<Venta>('/ventas/', data);
    return response.data;
  },

  getVentas: async (params?: VentaParams): Promise<PaginatedResponse<Venta>> => {
    const response = await api.get<PaginatedResponse<Venta>>('/ventas/', { params });
    return response.data;
  },

  getVentaById: async (id: number): Promise<Venta> => {
    const response = await api.get<Venta>(`/ventas/${id}/`);
    return response.data;
  },
};
