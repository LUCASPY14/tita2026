import api from './api';
import { 
  Producto, 
  PaginatedResponse, 
  Categoria, 
  UnidadMedida, 
  ListaPrecio, 
  PrecioPorLista 
} from '../types';

export interface ProductoParams {
  page?: number;
  page_size?: number;
  search?: string;
  activo?: boolean;
  id_categoria?: number;
  ordering?: string;
}

export interface ProductoData {
  codigo_barra?: string;
  descripcion: string;
  stock_minimo: number;
  permite_stock_negativo: boolean;
  activo: boolean;
  id_categoria: number;
  id_impuesto: number;
  id_unidad_medida?: number;
}

export interface CategoriaData {
  nombre: string;
  activo: boolean;
  id_categoria_padre?: number;
}

export interface PrecioPorListaData {
  precio_unitario: number;
  id_lista: number;
  id_producto: number;
}

export const productosService = {
  // === PRODUCTOS ===
  
  getProductos: async (params?: ProductoParams): Promise<PaginatedResponse<Producto>> => {
    const response = await api.get<PaginatedResponse<Producto>>('/productos/', { params });
    return response.data;
  },

  getProductoById: async (id: number): Promise<Producto> => {
    const response = await api.get<Producto>(`/productos/${id}/`);
    return response.data;
  },

  buscarPorCodigoBarra: async (codigoBarra: string): Promise<PaginatedResponse<Producto>> => {
    const response = await api.get<PaginatedResponse<Producto>>('/productos/', {
      params: { search: codigoBarra }
    });
    return response.data;
  },

  crearProducto: async (data: ProductoData): Promise<Producto> => {
    const response = await api.post<Producto>('/productos/', data);
    return response.data;
  },

  actualizarProducto: async (id: number, data: Partial<ProductoData>): Promise<Producto> => {
    const response = await api.patch<Producto>(`/productos/${id}/`, data);
    return response.data;
  },

  eliminarProducto: async (id: number): Promise<void> => {
    await api.delete(`/productos/${id}/`);
  },

  toggleEstadoProducto: async (id: number, activo: boolean): Promise<Producto> => {
    const response = await api.patch<Producto>(`/productos/${id}/`, { activo });
    return response.data;
  },

  // === CATEGORÍAS ===
  
  getCategorias: async (params?: { activo?: boolean }): Promise<PaginatedResponse<Categoria>> => {
    const response = await api.get<PaginatedResponse<Categoria>>('/categorias/', { params });
    return response.data;
  },

  getCategoriaById: async (id: number): Promise<Categoria> => {
    const response = await api.get<Categoria>(`/categorias/${id}/`);
    return response.data;
  },

  crearCategoria: async (data: CategoriaData): Promise<Categoria> => {
    const response = await api.post<Categoria>('/categorias/', data);
    return response.data;
  },

  actualizarCategoria: async (id: number, data: Partial<CategoriaData>): Promise<Categoria> => {
    const response = await api.patch<Categoria>(`/categorias/${id}/`, data);
    return response.data;
  },

  eliminarCategoria: async (id: number): Promise<void> => {
    await api.delete(`/categorias/${id}/`);
  },

  // === UNIDADES DE MEDIDA ===
  
  getUnidadesMedida: async (): Promise<UnidadMedida[]> => {
    const response = await api.get<UnidadMedida[]>('/unidades-medida/');
    return response.data;
  },

  // === LISTAS DE PRECIOS ===
  
  getListasPrecios: async (): Promise<ListaPrecio[]> => {
    const response = await api.get<ListaPrecio[]>('/listas-precios/');
    return response.data;
  },

  // === PRECIOS POR LISTA ===
  
  getPreciosPorProducto: async (idProducto: number): Promise<PrecioPorLista[]> => {
    const response = await api.get<PrecioPorLista[]>('/precios-por-lista/', {
      params: { id_producto: idProducto }
    });
    return response.data;
  },

  actualizarPrecio: async (idPrecio: number, precioUnitario: number): Promise<PrecioPorLista> => {
    const response = await api.patch<PrecioPorLista>(`/precios-por-lista/${idPrecio}/`, {
      precio_unitario: precioUnitario
    });
    return response.data;
  },

  crearPrecio: async (data: PrecioPorListaData): Promise<PrecioPorLista> => {
    const response = await api.post<PrecioPorLista>('/precios-por-lista/', data);
    return response.data;
  },
};

