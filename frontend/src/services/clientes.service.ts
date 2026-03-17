import api from './api';
import type { Cliente, TipoCliente, CuentaCorriente, PaginatedResponse } from '../types';

export interface ClienteParams {
  page?: number;
  page_size?: number;
  search?: string;
  estado?: boolean;
  id_tipo_cliente?: number;
  ordering?: string;
}

export interface ClienteData {
  nombres: string;
  apellidos: string;
  razon_social?: string;
  ruc_ci: string;
  direccion?: string;
  ciudad?: string;
  telefono?: string;
  email?: string;
  limite_credito?: number;
  estado?: boolean;
  id_lista: number;
  id_tipo_cliente: number;
}

export const clientesService = {
  /**
   * Obtiene lista paginada de clientes
   */
  getClientes: async (params?: ClienteParams): Promise<PaginatedResponse<Cliente>> => {
    const response = await api.get<PaginatedResponse<Cliente>>('/clientes/', { params });
    return response.data;
  },

  /**
   * Obtiene un cliente por ID
   */
  getClienteById: async (id: number): Promise<Cliente> => {
    const response = await api.get<Cliente>(`/clientes/${id}/`);
    return response.data;
  },

  /**
   * Busca clientes por RUC/CI
   */
  buscarPorRucCi: async (rucCi: string): Promise<Cliente[]> => {
    const response = await api.get<PaginatedResponse<Cliente>>('/clientes/', {
      params: { search: rucCi }
    });
    return response.data.results || [];
  },

  /**
   * Crea un nuevo cliente
   */
  crearCliente: async (data: ClienteData): Promise<Cliente> => {
    const response = await api.post<Cliente>('/clientes/', data);
    return response.data;
  },

  /**
   * Actualiza un cliente existente
   */
  actualizarCliente: async (id: number, data: Partial<ClienteData>): Promise<Cliente> => {
    const response = await api.patch<Cliente>(`/clientes/${id}/`, data);
    return response.data;
  },

  /**
   * Elimina un cliente (soft delete - marca como inactivo)
   */
  eliminarCliente: async (id: number): Promise<void> => {
    await api.delete(`/clientes/${id}/`);
  },

  /**
   * Activa o desactiva un cliente
   */
  toggleEstadoCliente: async (id: number, estado: boolean): Promise<Cliente> => {
    const response = await api.patch<Cliente>(`/clientes/${id}/`, { estado });
    return response.data;
  },

  /**
   * Obtiene la cuenta corriente de un cliente
   */
  getCuentaCorriente: async (id: number): Promise<CuentaCorriente> => {
    const response = await api.get<CuentaCorriente>(`/clientes/${id}/cuenta_corriente/`);
    return response.data;
  },

  /**
   * Obtiene tipos de cliente disponibles
   */
  getTiposCliente: async (): Promise<TipoCliente[]> => {
    const response = await api.get<PaginatedResponse<TipoCliente>>('/tipos-cliente/', {
      params: { estado: true, page_size: 100 }
    });
    return response.data.results || [];
  },

  /**
   * Obtiene estadísticas de clientes
   */
  getEstadisticas: async (): Promise<{
    total: number;
    activos: number;
    inactivos: number;
    con_credito: number;
    sin_credito: number;
  }> => {
    const response = await api.get('/clientes/estadisticas/');
    return response.data;
  },
};
