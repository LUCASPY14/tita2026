import api from './api';

/**
 * Roles disponibles en el sistema
 */
export type UserRole = 'admin' | 'gerente' | 'cajero' | 'empleado';

// Función para mapear roles del backend a UserRole
const mapRoleFromBackend = (backendRole: string): UserRole => {
  const roleMap: { [key: string]: UserRole } = {
    'administrador': 'admin',
    'admin': 'admin',
    'gerente': 'gerente',
    'cajero': 'cajero',
    'vendedor': 'cajero',
    'empleado': 'empleado'
  };
  
  const normalizedRole = backendRole.toLowerCase();
  return roleMap[normalizedRole] || 'empleado';
};

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
    const response = await api.post('/auth/login/', credentials);
    
    // El backend devuelve: { success, tokens: { access, refresh }, empleado, mensaje }
    const data = response.data;
    
    if (data.success && data.tokens) {
      const tokens = data.tokens;
      const empleado = data.empleado;
      
      // Guardar tokens
      localStorage.setItem('token', tokens.access);
      if (tokens.refresh) {
        localStorage.setItem('refreshToken', tokens.refresh);
      }
      
      // Adaptar estructura del usuario
      const user: User = {
        id: empleado.id,
        username: empleado.usuario,
        email: empleado.email || '',
        role: mapRoleFromBackend(empleado.rol || 'empleado')
      };
      
      localStorage.setItem('user', JSON.stringify(user));
      
      // Retornar en el formato esperado
      return {
        token: tokens.access,
        refreshToken: tokens.refresh,
        user: user
      };
    } else {
      throw new Error(data.mensaje || 'Error al iniciar sesión');
    }
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
