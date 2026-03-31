/**
 * Servicio de autenticación del portal para clientes.
 * Instancia axios separada de la del sistema de empleados.
 */
import axios, { AxiosInstance } from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
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

export interface DashboardData {
  cliente: {
    nombre_completo: string;
    ruc_ci: string;
    email: string | null;
    limite_credito: string;
    credito_disponible: string;
  };
  hijos: HijoPortal[];
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
};
