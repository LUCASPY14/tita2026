/**
 * Servicio de autenticación del portal para clientes.
 * Instancia axios separada de la del sistema de empleados.
 */
import axios, { AxiosInstance } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const PORTAL_TOKEN_KEY = 'portal_token';
const PORTAL_USER_KEY = 'portal_user';

export interface PortalUser {
  id_usuario_portal: number;
  email: string;
  email_verificado: boolean;
  id_cliente: number;
  nombre_completo: string;
  ruc_ci: string;
}

export interface Consumo {
  id_consumo: number;
  fecha_consumo: string;
  monto_consumido: string;
  detalle: string | null;
  saldo_posterior: string;
}

export interface TarjetaPortal {
  nro_tarjeta: string;
  saldo_actual: string;
  estado: string;
  esta_en_alerta: boolean;
  ultimos_consumos: Consumo[];
}

export interface HijoPortal {
  id_hijo: number;
  nombre: string;
  apellido: string;
  nombre_completo: string;
  grado: string | null;
  tarjeta: TarjetaPortal | null;
}

export interface FacturaPendientePortal {
  id_venta: number;
  nro_factura_venta: string;
  fecha: string;
  total_venta: string;
  saldo_pendiente: string;
}

export interface CuentaCorriente {
  total_deuda: string;
  cantidad_facturas_pendientes: number;
  facturas_recientes: FacturaPendientePortal[];
}

export interface DashboardData {
  cliente: {
    nombre_completo: string;
    ruc_ci: string;
    email: string | null;
    limite_credito: string;
    credito_disponible: string;
  };
  hijos: HijoPortal[];
  cuenta_corriente: CuentaCorriente;
}

// Interfaces SIPAP para el portal
export interface QRSIPAPData {
  qr_image: string;
  qr_string: string;
  txn_id: string;
  expira_en: number;
  expira_at: string;
  banco: string;
  ambiente: string;
}

export interface GenerarQRSIPAPRequest {
  id_cliente: number;
  monto?: number;
  descripcion?: string;
}

export interface GenerarQRSIPAPResponse {
  success: boolean;
  qr_data: QRSIPAPData;
  cliente: {
    id_cliente: number;
    nombre_completo: string;
    ruc_ci: string;
    total_deuda: number;
    cantidad_facturas: number;
    monto_a_pagar: number;
  };
  id_pago_pendiente: number;
}

export interface EstadoPagoSIPAP {
  txn_id: string;
  estado: 'pendiente' | 'aprobado' | 'rechazado' | 'expirado';
  monto: number;
  fecha_pago?: string;
}

// Axios instance exclusiva del portal
const portalApi: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

portalApi.interceptors.request.use((config) => {
  const token = localStorage.getItem(PORTAL_TOKEN_KEY);
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const portalAuthService = {
  login: async (email: string, password: string): Promise<PortalUser> => {
    const response = await portalApi.post('/portal-auth/login/', { email, password });
    const { token, usuario } = response.data;
    localStorage.setItem(PORTAL_TOKEN_KEY, token);
    localStorage.setItem(PORTAL_USER_KEY, JSON.stringify(usuario));
    return usuario as PortalUser;
  },

  logout: () => {
    localStorage.removeItem(PORTAL_TOKEN_KEY);
    localStorage.removeItem(PORTAL_USER_KEY);
  },

  getToken: (): string | null => localStorage.getItem(PORTAL_TOKEN_KEY),

  getCurrentUser: (): PortalUser | null => {
    const raw = localStorage.getItem(PORTAL_USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },

  isAuthenticated: (): boolean => !!localStorage.getItem(PORTAL_TOKEN_KEY),

  getPerfil: async (): Promise<PortalUser> => {
    const response = await portalApi.get('/portal-auth/perfil/');
    return response.data;
  },

  getDashboard: async (): Promise<DashboardData> => {
    const response = await portalApi.get('/portal-auth/dashboard/');
    return response.data;
  },

  cambiarPassword: async (
    password_actual: string,
    password_nuevo: string
  ): Promise<void> => {
    await portalApi.post('/portal-auth/cambiar_password/', {
      password_actual,
      password_nuevo,
    });
  },

  // Métodos SIPAP para el portal
  generarQRSIPAP: async (request: GenerarQRSIPAPRequest): Promise<GenerarQRSIPAPResponse> => {
    const response = await portalApi.post('/cobros/generar_qr_sipap/', request);
    return response.data;
  },

  consultarEstadoSIPAP: async (txnId: string): Promise<EstadoPagoSIPAP> => {
    const response = await portalApi.get(`/cobros/estado_pago_sipap/${txnId}/`);
    return response.data;
  },

  esperarConfirmacionSIPAP: async (
    txnId: string,
    onUpdate?: (estado: EstadoPagoSIPAP) => void,
    intervalo: number = 3000,
    maxIntentos: number = 300
  ): Promise<EstadoPagoSIPAP> => {
    let intentos = 0;

    while (intentos < maxIntentos) {
      try {
        const estado = await portalAuthService.consultarEstadoSIPAP(txnId);
        onUpdate?.(estado);

        if (estado.estado === 'aprobado') {
          return estado;
        }

        if (estado.estado === 'rechazado') {
          throw new Error('El pago fue rechazado');
        }

        if (estado.estado === 'expirado') {
          throw new Error('El QR ha expirado');
        }

        await new Promise(resolve => setTimeout(resolve, intervalo));
        intentos++;
      } catch (error: any) {
        if (error.message.includes('rechazado') || error.message.includes('expirado')) {
          throw error;
        }
        throw new Error(`Error consultando estado: ${error.message}`);
      }
    }

    throw new Error('Tiempo de espera agotado');
  },
};

// Utilidades SIPAP
export const sipapUtils = {
  formatearMonto(monto: number): string {
    return `Gs. ${monto.toLocaleString('es-PY')}`;
  },

  calcularTiempoRestante(expiraAt: string): number {
    const ahora = new Date().getTime();
    const expiracion = new Date(expiraAt).getTime();
    const diferencia = Math.floor((expiracion - ahora) / 1000);
    return Math.max(0, diferencia);
  },

  formatearTiempo(segundos: number): string {
    const minutos = Math.floor(segundos / 60);
    const segs = segundos % 60;
    return `${minutos.toString().padStart(2, '0')}:${segs.toString().padStart(2, '0')}`;
  },
};
