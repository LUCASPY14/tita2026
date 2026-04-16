import api from './api';

export interface MedioPago {
  id_medio_pago: number;
  nombre: string;
  activo?: boolean;
}

class MediosPagoService {
  private readonly basePath = '/medios-pago';

  /**
   * Obtiene todos los medios de pago
   */
  async getAll(): Promise<MedioPago[]> {
    const response = await api.get(this.basePath);
    return response.data;
  }

  /**
   * Obtiene un medio de pago por ID
   */
  async getById(id: number): Promise<MedioPago> {
    const response = await api.get(`${this.basePath}/${id}/`);
    return response.data;
  }
}

export default new MediosPagoService();
