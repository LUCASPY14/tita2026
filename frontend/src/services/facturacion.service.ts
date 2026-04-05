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
  condicion_venta: 'CONTADO' | 'CREDITO';
  condicion_venta_display: string;
  plazo_dias: number | null;
}

export interface EmitirFacturaDto {
  id_cliente: number;
  nro_preimpreso: number;
  ventas_ids: number[];
  almuerzos_ids: number[];
  condicion_venta: 'CONTADO' | 'CREDITO';
  plazo_dias?: number | null;
}

// ─── API calls ────────────────────────────────────────────────────────────────

const facturacionService = {
  /** Cola: items pagados sin facturar, agrupados por cliente. */
  getCola: (): Promise<ClienteConPendientes[]> =>
    api.get('/facturacion/cola/').then((r) => r.data),

  /** Emite una factura física vinculando ventas y/o almuerzos. */
  emitir: (dto: EmitirFacturaDto): Promise<DocumentoEmitido> =>
    api.post('/facturacion/emitir/', dto).then((r) => r.data),

  /** Obtiene el texto de impresión (80 col) con autenticación y lo abre como Blob. */
  fetchTextoImpresion: (idDocumento: number): Promise<string> =>
    api
      .get(`/facturacion/${idDocumento}/imprimir/`, { responseType: 'text' })
      .then((r) => r.data as string),

  /** Anula una factura y devuelve los items a la cola. */
  anular: (idDocumento: number): Promise<void> =>
    api.post(`/facturacion/${idDocumento}/anular/`).then(() => undefined),

  /** Historial de facturas emitidas con filtros opcionales. */
  getHistorial: (params?: {
    fecha_desde?: string;
    fecha_hasta?: string;
    id_cliente?: number;
    condicion_venta?: 'CONTADO' | 'CREDITO';
    page?: number;
  }): Promise<{ count: number; next: string | null; previous: string | null; results: DocumentoEmitido[] }> =>
    api.get('/documentos-tributarios/', { params }).then((r) => r.data),
};

export default facturacionService;
