import api from './api';
import { Producto, PaginatedResponse, Categoria } from '@/types';

export interface ProductoCreateData {
  codigo: string;
  nombre: string;
  descripcion?: string;
  precio: number;
  stock: number;
  stock_minimo: number;
  categoria_id?: number;
}

export interface ProductoParams {
  page?: number;
  page_size?: number;
  search?: string;
  categoria?: number;
  en_stock?: boolean;
}

export const productosService = {
  getAll: async (params?: ProductoParams): Promise<PaginatedResponse<Producto>> => {
    const response = await api.get<PaginatedResponse<Producto>>('/productos/', { params });
    return response.data;
  },

  getById: async (id: number): Promise<Producto> => {
    const response = await api.get<Producto>(`/productos/${id}/`);
    return response.data;
  },

  create: async (data: ProductoCreateData): Promise<Producto> => {
    const response = await api.post<Producto>('/productos/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<ProductoCreateData>): Promise<Producto> => {
    const response = await api.put<Producto>(`/productos/${id}/`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/productos/${id}/`);
  },

  getCategorias: async (): Promise<Categoria[]> => {
    const response = await api.get<Categoria[]>('/productos/categorias/');
    return response.data;
  },
};
