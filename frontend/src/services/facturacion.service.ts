import api from './api';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ItemPendiente {
  id: number;
  tipo: 'venta' | 'almuerzo';
  fecha: string;
  descripcion: string;
  monto: number;
}

export interface ClienteConPendientes {
  id_cliente: number;
  nombres: string;
  apellidos: string;
  nombre_completo: string;
  ruc_ci: string;
  ventas: ItemPendiente[];
  almuerzos: ItemPendiente[];
  total_pendiente: number;
}

export interface DocumentoEmitido {
  id_documento: number;
  nro_secuencial: number;
  nro_preimpreso_interno: string;
  fecha_emision: string;
  monto_total: string;
  tipo_documento: string;
  nro_timbrado: number;
  id_cliente: number;
  cliente_nombre: string;
  cliente_ruc: string;
}

export interface EmitirFacturaDto {
  id_cliente: number;
  nro_preimpreso: number;
  ventas_ids: number[];
  almuerzos_ids: number[];
}

// ─── API calls ────────────────────────────────────────────────────────────────

const facturacionService = {
  /** Cola: items pagados sin facturar, agrupados por cliente. */
  getCola: (): Promise<ClienteConPendientes[]> =>
    api.get('/facturacion/cola/').then((r) => r.data),

  /** Emite una factura física vinculando ventas y/o almuerzos. */
  emitir: (dto: EmitirFacturaDto): Promise<DocumentoEmitido> =>
    api.post('/facturacion/emitir/', dto).then((r) => r.data),

  /** URL del endpoint de impresión para abrir en nueva pestaña. */
  getImprimirUrl: (idDocumento: number): string =>
    `${api.defaults.baseURL}/facturacion/${idDocumento}/imprimir/`,

  /** Anula una factura y devuelve los items a la cola. */
  anular: (idDocumento: number): Promise<void> =>
    api.post(`/facturacion/${idDocumento}/anular/`).then(() => undefined),
};

export default facturacionService;
