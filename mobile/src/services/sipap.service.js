/**
 * Servicio SIPAP para pagos QR en la app móvil
 * Sistema de Pagos del Paraguay - BCP
 */
import api from './api';

/**
 * Genera QR SIPAP para carga de saldo de tarjeta
 * 
 * @param {number} idCliente - ID del cliente
 * @param {number} monto - Monto en Guaraníes
 * @param {string} descripcion - Descripción del pago
 * @returns {Promise} Datos del QR generado
 */
export const generarQRCargaSaldo = async (idCliente, monto, descripcion) => {
  try {
    const response = await api.post('/cobros/generar_qr_sipap/', {
      id_cliente: idCliente,
      monto,
      descripcion
    });
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 
      error.response?.data?.message || 
      'Error al generar QR SIPAP'
    );
  }
};

/**
 * Consulta el estado de un pago SIPAP
 * 
 * @param {string} txnId - ID de transacción SIPAP
 * @returns {Promise} Estado del pago
 */
export const consultarEstadoPago = async (txnId) => {
  try {
    const response = await api.get(`/cobros/estado_pago_sipap/${txnId}/`);
    return response.data;
  } catch (error) {
    throw new Error('Error al consultar estado del pago');
  }
};

/**
 * Polling para verificar confirmación de pago
 * 
 * @param {string} txnId - ID de transacción
 * @param {function} onUpdate - Callback con actualizaciones de estado
 * @param {number} intervaloMs - Intervalo entre verificaciones (default: 3000ms)
 * @param {number} maxIntentos - Máximo de intentos (default: 300 = 15min)
 * @returns {Promise} Estado final del pago
 */
export const esperarConfirmacion = async (
  txnId, 
  onUpdate, 
  intervaloMs = 3000, 
  maxIntentos = 300
) => {
  let intentos = 0;

  return new Promise((resolve, reject) => {
    const verificar = async () => {
      try {
        const estado = await consultarEstadoPago(txnId);
        
        if (onUpdate) {
          onUpdate(estado);
        }

        if (estado.estado === 'aprobado') {
          clearInterval(intervalo);
          resolve(estado);
        } else if (estado.estado === 'rechazado') {
          clearInterval(intervalo);
          reject(new Error('Pago rechazado'));
        } else if (estado.estado === 'expirado') {
          clearInterval(intervalo);
          reject(new Error('QR expirado'));
        }

        intentos++;
        if (intentos >= maxIntentos) {
          clearInterval(intervalo);
          reject(new Error('Tiempo de espera agotado'));
        }
      } catch (error) {
        console.error('Error verificando estado:', error);
      }
    };

    const intervalo = setInterval(verificar, intervaloMs);
    verificar(); // Primera verificación inmediata
  });
};

/**
 * Formatea monto en Guaraníes
 */
export const formatearMonto = (monto) => {
  return `Gs. ${Number(monto).toLocaleString('es-PY')}`;
};

/**
 * Calcula tiempo restante hasta expiración
 */
export const calcularTiempoRestante = (expiraAt) => {
  const ahora = new Date().getTime();
  const expiracion = new Date(expiraAt).getTime();
  const diferencia = Math.floor((expiracion - ahora) / 1000);
  return Math.max(0, diferencia);
};

/**
 * Formatea tiempo en MM:SS
 */
export const formatearTiempo = (segundos) => {
  const minutos = Math.floor(segundos / 60);
  const segs = segundos % 60;
  return `${String(minutos).padStart(2, '0')}:${String(segs).padStart(2, '0')}`;
};

export default {
  generarQRCargaSaldo,
  consultarEstadoPago,
  esperarConfirmacion,
  formatearMonto,
  calcularTiempoRestante,
  formatearTiempo
};
