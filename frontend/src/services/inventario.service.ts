import api from './api';
import type { PaginatedResponse } from '../types';

export interface StockItem {
  id_stock: number;
  id_producto: number;
  cantidad: number;
  fecha_ultima_actualizacion: string;
  producto_nombre: string;
  producto_categoria: string;
}

export interface MovimientoStock {
  id_movimiento_stock: number;
  fecha_hora: string;
  tipo_movimiento: 'Ingreso' | 'Egreso';
  motivo: string;
  cantidad: number;
  stock_resultante: number;
  id_producto: number;
  producto_nombre: string;
  referencia_documento?: string;
}

export interface StockParams {
  page?: number;
  page_size?: number;
  id_producto?: number;
  search?: string;
}

export interface MovimientoParams {
  page?: number;
  page_size?: number;
  id_producto?: number;
  tipo_movimiento?: 'Ingreso' | 'Egreso';
}

export const inventarioService = {
  getStock: async (params?: StockParams): Promise<PaginatedResponse<StockItem>> => {
    const response = await api.get<PaginatedResponse<StockItem>>('/stock/', { params });
    return response.data;
  },

  getStockByProducto: async (idProducto: number): Promise<StockItem> => {
    const response = await api.get<PaginatedResponse<StockItem>>('/stock/', {
      params: { id_producto: idProducto, page_size: 1 },
    });
    const results = response.data.results || [];
    if (results.length === 0) throw new Error('Sin registro de stock para este producto');
    return results[0];
  },

  getMovimientos: async (params?: MovimientoParams): Promise<PaginatedResponse<MovimientoStock>> => {
    const response = await api.get<PaginatedResponse<MovimientoStock>>('/movimientos-stock/', { params });
    return response.data;
  },
};
