import api from './api';

// Interfaces
export interface PagoCliente {
  id_pago_cliente: number;
  id_cliente: number;
  monto_total: number;
  fecha_pago: string;
  id_medio_pago: number;
  referencia: string;
  banco_emisor: string;
  observaciones: string;
  id_empleado_cajero: number;
  estado: string;
  monto_aplicado: number;
  monto_pendiente_aplicar: number;
  aplicaciones?: AplicacionPago[];
}

export interface AplicacionPago {
  id_aplicacion: number;
  id_pago_cliente: number;
  id_venta: number;
  monto_aplicado: number;
  fecha_aplicacion: string;
}

export interface FacturaPendiente {
  id_venta: number;
  nro_factura_venta: string;
  fecha: string;
  total_venta: number;
  saldo_pendiente: number;
  dias_vencido: number;
}

export interface ResumenCobros {
  cliente: {
    id_cliente: number;
    nombre_completo: string;
    ruc_ci: string;
    limite_credito: number;
    credito_disponible: number;
  };
  facturas: FacturaPendiente[];
  resumen: {
    cantidad_facturas: number;
    total_pendiente: number;
  };
}

export interface RegistrarPagoRequest {
  id_cliente: number;
  monto_total: number;
  id_medio_pago: number;
  referencia?: string;
  banco_emisor?: string;
  observaciones?: string;
  aplicaciones?: Array<{
    id_venta: number;
    monto_aplicado: number;
  }>;
}

// Service
class CobrosService {
  private readonly basePath = '/cobros';

  /**
   * Obtiene la lista de pagos
   */
  async getPagos(params?: {
    id_cliente?: number;
    estado?: string;
    id_medio_pago?: number;
  }): Promise<PagoCliente[]> {
    const response = await api.get(this.basePath, { params });
    return response.data;
  }

  /**
   * Obtiene un pago por ID
   */
  async getPagoById(id: number): Promise<PagoCliente> {
    const response = await api.get(`${this.basePath}/${id}/`);
    return response.data;
  }

  /**
   * Obtiene las facturas pendientes de un cliente
   */
  async getFacturasPendientes(idCliente: number): Promise<ResumenCobros> {
    const response = await api.get(`${this.basePath}/facturas_pendientes/`, {
      params: { id_cliente: idCliente },
    });
    return response.data;
  }

  /**
   * Registra un nuevo pago
   */
  async registrarPago(data: RegistrarPagoRequest): Promise<PagoCliente> {
    const response = await api.post(`${this.basePath}/registrar_pago/`, data);
    return response.data;
  }
}

export default new CobrosService();
