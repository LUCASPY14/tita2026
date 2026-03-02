import api from './api';
import { Cliente, PaginatedResponse } from '../types';

export interface ClienteCreateData {
  nombre: string;
  ruc: string;
  telefono: string;
  email: string;
  direccion?: string;
}

export interface ClienteParams {
  page?: number;
  page_size?: number;
  search?: string;
}

export const clientesService = {
  getAll: async (params?: ClienteParams): Promise<PaginatedResponse<Cliente>> => {
    const response = await api.get<PaginatedResponse<Cliente>>('/clientes/', { params });
    return response.data;
  },

  getById: async (id: number): Promise<Cliente> => {
    const response = await api.get<Cliente>(`/clientes/${id}/`);
    return response.data;
  },

  create: async (data: ClienteCreateData): Promise<Cliente> => {
    const response = await api.post<Cliente>('/clientes/', data);
    return response.data;
  },

  update: async (id: number, data: Partial<ClienteCreateData>): Promise<Cliente> => {
    const response = await api.put<Cliente>(`/clientes/${id}/`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/clientes/${id}/`);
  },
};
