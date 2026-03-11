import api from './api';

/**
 * Roles disponibles en el sistema
 */
export type UserRole = 'admin' | 'gerente' | 'cajero' | 'empleado';

// Clave usada en sessionStorage para el token temporal de 2FA
const TEMP_2FA_TOKEN_KEY = 'cantina_2fa_temp_token';

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
  requires2FA: false;
}

export interface Login2FARequired {
  requires2FA: true;
  token_temporal: string;
}

export type LoginOutcome = LoginResponse | Login2FARequired;

export interface RefreshTokenResponse {
  token: string;
  refreshToken: string;
}

export const authService = {
  login: async (credentials: LoginCredentials): Promise<LoginOutcome> => {
    const response = await api.post('/auth/login/', credentials);
    
    // El backend devuelve: { success, tokens: { access, refresh }, empleado, mensaje }
    // O en caso de 2FA: { success, requiere_2fa: true, token_temporal }
    const data = response.data;
    
    if (!data.success) {
      throw new Error(data.mensaje || 'Error al iniciar sesión');
    }

    // Caso 2FA requerida
    if (data.requiere_2fa) {
      sessionStorage.setItem(TEMP_2FA_TOKEN_KEY, data.token_temporal);
      return { requires2FA: true, token_temporal: data.token_temporal };
    }

    // Login completo sin 2FA
    if (data.tokens) {
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
      
      return {
        requires2FA: false,
        token: tokens.access,
        refreshToken: tokens.refresh,
        user,
      };
    }

    throw new Error(data.mensaje || 'Error al iniciar sesión');
  },

  /**
   * Completa el login verificando el código TOTP usando el token temporal.
   */
  verify2FA: async (codigo: string): Promise<LoginResponse> => {
    const tempToken = sessionStorage.getItem(TEMP_2FA_TOKEN_KEY);
    if (!tempToken) {
      throw new Error('No hay sesión de 2FA activa. Por favor, vuelve a iniciar sesión.');
    }

    const response = await api.post(
      '/2fa/verificar/',
      { codigo },
      { headers: { Authorization: `Bearer ${tempToken}` } }
    );

    if (!response.data.success) {
      throw new Error(response.data.mensaje || 'Código inválido');
    }

    // Promover el token temporal a token de acceso definitivo
    localStorage.setItem('token', tempToken);
    sessionStorage.removeItem(TEMP_2FA_TOKEN_KEY);

    // Obtener datos del empleado autenticado
    const perfilRes = await api.get('/auth/perfil/');
    const emp = perfilRes.data.empleado;
    const user: User = {
      id: emp.id_empleado || emp.id,
      username: emp.usuario,
      email: emp.email || '',
      role: mapRoleFromBackend(emp.id_rol?.nombre_rol || emp.rol || 'empleado'),
    };
    localStorage.setItem('user', JSON.stringify(user));

    return { requires2FA: false, token: tempToken, user };
  },

  /**
   * Solicita el envío de email para recuperación de contraseña.
   */
  solicitarRecuperacion: async (email: string): Promise<void> => {
    await api.post('/password/solicitar/', { email });
  },

  /**
   * Valida si un token de recuperación es válido.
   */
  validarTokenRecuperacion: async (token: string): Promise<boolean> => {
    try {
      const response = await api.post('/password/validar_token/', { token });
      return response.data.valido === true;
    } catch {
      return false;
    }
  },

  /**
   * Restablece la contraseña usando el token recibido por email.
   */
  restablecerPassword: async (token: string, nueva_password: string): Promise<void> => {
    const response = await api.post('/password/restablecer/', { token, nueva_password });
    if (!response.data.success) {
      throw new Error(response.data.mensaje || 'Error al restablecer la contraseña');
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
