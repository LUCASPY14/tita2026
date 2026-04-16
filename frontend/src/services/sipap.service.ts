/**
 * Servicio para integración con SIPAP QR
 * Sistema de Pagos QR Nativo de Paraguay - Banco Central
 */

import apiClient from './api.service';

/**
 * Datos del QR SIPAP generado
 */
export interface QRSIPAPData {
  qr_image: string;           // Base64 data URL de la imagen QR
  qr_string: string;          // String EMVCo para apps
  txn_id: string;             // ID único de transacción (ej: COB-123-1713308400)
  expira_en: number;          // Segundos hasta expiración
  expira_at: string;          // Timestamp ISO de expiración
  banco: string;              // Banco agregador (continental, atlas, etc.)
  ambiente: string;           // sandbox o produccion
}

/**
 * Datos del cliente para el QR
 */
export interface ClienteQRData {
  id_cliente: number;
  nombre_completo: string;
  ruc_ci: string;
  total_deuda: number;
  cantidad_facturas: number;
  monto_a_pagar: number;
}

/**
 * Request para generar QR SIPAP
 */
export interface GenerarQRSIPAPRequest {
  id_cliente: number;
  monto?: number;             // Opcional - si no se envía usa total deuda
  descripcion?: string;       // Opcional - descripción del pago
}

/**
 * Response de generar QR SIPAP
 */
export interface GenerarQRSIPAPResponse {
  success: boolean;
  qr_data: QRSIPAPData;
  cliente: ClienteQRData;
  id_pago_pendiente: number;
}

/**
 * Estado de un pago SIPAP
 */
export interface EstadoPagoSIPAP {
  txn_id: string;
  estado: 'pendiente' | 'aprobado' | 'rechazado' | 'expirado';
  monto?: number;
  fecha_pago?: string;
  referencia_bancaria?: string;
  banco_origen?: string;
}

class SIPAPService {
  /**
   * Genera un QR SIPAP para pago de deuda
   * 
   * @param request - Datos para generar el QR
   * @returns Promise con datos del QR generado
   * 
   * @example
   * ```ts
   * const qr = await sipapService.generarQR({
   *   id_cliente: 1,
   *   monto: 14402000,
   *   descripcion: 'Pago de 92 facturas'
   * });
   * 
   * // Mostrar QR
   * <img src={qr.qr_data.qr_image} alt="QR SIPAP" />
   * ```
   */
  async generarQR(request: GenerarQRSIPAPRequest): Promise<GenerarQRSIPAPResponse> {
    const response = await apiClient.post('/cobros/generar_qr_sipap/', request);
    return response.data;
  }

  /**
   * Consulta el estado de un pago SIPAP por txn_id
   * 
   * @param txnId - ID de transacción SIPAP
   * @returns Promise con estado del pago
   * 
   * @example
   * ```ts
   * const estado = await sipapService.consultarEstado('COB-123-1713308400');
   * 
   * if (estado.estado === 'aprobado') {
   *   console.log('Pago confirmado!');
   * }
   * ```
   */
  async consultarEstado(txnId: string): Promise<EstadoPagoSIPAP> {
    const response = await apiClient.get(`/cobros/estado_pago_sipap/${txnId}/`);
    return response.data;
  }

  /**
   * Polling para verificar si el pago fue confirmado
   * 
   * @param txnId - ID de transacción SIPAP
   * @param onEstadoCambiado - Callback cuando el estado cambia
   * @param intervaloMs - Intervalo de polling en milisegundos (default: 3000)
   * @param maxIntentos - Máximo de intentos (default: 300 = 15 min si intervalo es 3s)
   * @returns Promise que resuelve cuando el pago es confirmado o rechazado
   * 
   * @example
   * ```ts
   * await sipapService.esperarConfirmacion(
   *   'COB-123-1713308400',
   *   (estado) => {
   *     console.log('Estado actual:', estado);
   *     setEstadoPago(estado);
   *   },
   *   3000, // Verificar cada 3 segundos
   *   300   // Máximo 15 minutos
   * );
   * ```
   */
  async esperarConfirmacion(
    txnId: string,
    onEstadoCambiado: (estado: EstadoPagoSIPAP) => void,
    intervaloMs: number = 3000,
    maxIntentos: number = 300
  ): Promise<EstadoPagoSIPAP> {
    return new Promise((resolve, reject) => {
      let intentos = 0;

      const verificar = async () => {
        try {
          const estado = await this.consultarEstado(txnId);
          
          // Notificar cambio de estado
          onEstadoCambiado(estado);

          // Verificar si ya terminó
          if (estado.estado === 'aprobado') {
            clearInterval(intervalo);
            resolve(estado);
          } else if (estado.estado === 'rechazado' || estado.estado === 'expirado') {
            clearInterval(intervalo);
            reject(new Error(`Pago ${estado.estado}`));
          }

          // Verificar límite de intentos
          intentos++;
          if (intentos >= maxIntentos) {
            clearInterval(intervalo);
            reject(new Error('Timeout: Se agotó el tiempo de espera'));
          }
        } catch (error) {
          console.error('Error al verificar estado:', error);
          // Continuar polling aunque falle una verificación
        }
      };

      // Iniciar polling
      const intervalo = setInterval(verificar, intervaloMs);
      
      // Primera verificación inmediata
      verificar();
    });
  }

  /**
   * Formatea un monto en Guaraníes
   * 
   * @param monto - Monto numérico
   * @returns String formateado (ej: "Gs. 14.402.000")
   */
  formatearMonto(monto: number): string {
    return `Gs. ${monto.toLocaleString('es-PY')}`;
  }

  /**
   * Calcula tiempo restante hasta expiración
   * 
   * @param expiraAt - Timestamp ISO de expiración
   * @returns Segundos restantes (0 si ya expiró)
   */
  calcularTiempoRestante(expiraAt: string): number {
    const ahora = new Date().getTime();
    const expiracion = new Date(expiraAt).getTime();
    const diferencia = Math.floor((expiracion - ahora) / 1000);
    return Math.max(0, diferencia);
  }

  /**
   * Formatea tiempo en formato MM:SS
   * 
   * @param segundos - Cantidad de segundos
   * @returns String formateado (ej: "14:35")
   */
  formatearTiempo(segundos: number): string {
    const minutos = Math.floor(segundos / 60);
    const segs = segundos % 60;
    return `${minutos.toString().padStart(2, '0')}:${segs.toString().padStart(2, '0')}`;
  }
}

export const sipapService = new SIPAPService();
export default sipapService;
