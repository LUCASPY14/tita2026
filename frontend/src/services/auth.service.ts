import api from './api';

/**
 * Roles disponibles en el sistema
 */
export type UserRole = 'admin' | 'gerente' | 'cajero' | 'empleado';

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  refreshToken?: string;
  user: User;
}

export interface RefreshTokenResponse {
  token: string;
  refreshToken: string;
}

export const authService = {
  login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
    const response = await api.post<LoginResponse>('/auth/login/', credentials);
    if (response.data.token) {
      localStorage.setItem('token', response.data.token);
      if (response.data.refreshToken) {
        localStorage.setItem('refreshToken', response.data.refreshToken);
      }
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  logout: (): void => {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
  },

  getCurrentUser: (): User | null => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('token');
  },

  /**
   * Renueva el token de acceso usando el refresh token
   */
  refreshToken: async (): Promise<RefreshTokenResponse> => {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await api.post<RefreshTokenResponse>('/auth/refresh/', {
        refresh: refreshToken,
      });

      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
        if (response.data.refreshToken) {
          localStorage.setItem('refreshToken', response.data.refreshToken);
        }
      }

      return response.data;
    } catch (error) {
      // Si el refresh token falló, limpiar todo y forzar logout
      authService.logout();
      throw error;
    }
  },

  /**
   * Obtiene el token actual
   */
  getToken: (): string | null => {
    return localStorage.getItem('token');
  },
};
