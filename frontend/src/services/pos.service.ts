import api from './api';
import type { 
  Producto, 
  Categoria,
  Venta,
  VentaData,
  MedioPago,
  PaginatedResponse 
} from '../types';

export interface NotaCredito {
  id_nota: number;
  nro_nota_credito: number;
  fecha_emision: string;
  motivo: string;
  monto_total: string;
  estado: string;
  id_cliente: number;
  id_empleado_autoriza: number;
  id_venta_origen: number | null;
}

export interface DevolucionData {
  id_venta: number;
  productos: Array<{ id_producto: number; cantidad: number; motivo_item?: string }>;
  motivo: string;
  tipo_devolucion: 'total' | 'parcial';
}

export interface NotaCreditoParams {
  page?: number;
  page_size?: number;
  estado?: string;
  id_cliente?: number;
}

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

  // Notas de crédito / Devoluciones
  getNotasCredito: async (params?: NotaCreditoParams): Promise<PaginatedResponse<NotaCredito>> => {
    const response = await api.get<PaginatedResponse<NotaCredito>>('/notas-credito-cliente/', { params });
    return response.data;
  },

  crearDevolucion: async (data: DevolucionData): Promise<{ exito: boolean; nota_credito: NotaCredito; monto_devuelto: string; mensaje: string }> => {
    const response = await api.post('/notas-credito-cliente/crear_devolucion/', data);
    return response.data;
  },

  anularNotaCredito: async (id: number, motivo: string): Promise<{ exito: boolean; mensaje: string }> => {
    const response = await api.post(`/notas-credito-cliente/${id}/anular/`, { motivo_anulacion: motivo });
    return response.data;
  },
};
