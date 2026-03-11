/**
 * Contexto de Autenticación
 * 
 * Proporciona estado global de autenticación para toda la aplicación
 * - Usuario actual autenticado
 * - Estado de carga de autenticación
 * - Funciones de login/logout
 * - Intercepción automática de renovación de tokens
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService, User, LoginCredentials } from '../services/auth.service';
import toast from 'react-hot-toast';
import api from '../services/api';
import { AxiosError } from 'axios';

export interface LoginResult {
  requires2FA: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<LoginResult>;
  logout: () => void;
  refreshUserData: () => void;
  completeLogin: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    // Verificar si hay un usuario logueado al cargar la aplicación
    const checkAuthStatus = async () => {
      try {
        const currentUser = authService.getCurrentUser();
        const isAuth = authService.isAuthenticated();
        
        if (isAuth && currentUser) {
          setUser(currentUser);
        }
      } catch (error) {
        console.error('Error verificando estado de autenticación:', error);
        // Si hay error, limpiar datos posiblemente corruptos
        authService.logout();
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  // Configurar interceptor de respuesta para manejar refresh de tokens
  useEffect(() => {
    const responseInterceptor = api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        // Si es error 401 y no es de login/refresh, intentar renovar token
        if (
          error.response?.status === 401 &&
          !originalRequest._retry &&
          !originalRequest.url?.includes('/auth/login') &&
          !originalRequest.url?.includes('/auth/refresh')
        ) {
          if (isRefreshing) {
            // Si ya se está renovando, esperar
            return Promise.reject(error);
          }

          originalRequest._retry = true;
          setIsRefreshing(true);

          try {
            // Intentar renovar el token
            await authService.refreshToken();
            
            // Actualizar el header de autorización de la petición original
            const newToken = authService.getToken();
            if (originalRequest.headers && newToken) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
            }

            // Reintentar la petición original
            return api(originalRequest);
          } catch (refreshError) {
            // Si el refresh falló, cerrar sesión
            console.error('Error renovando token:', refreshError);
            authService.logout();
            setUser(null);
            toast.error('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.');
            window.location.href = '/login';
            return Promise.reject(refreshError);
          } finally {
            setIsRefreshing(false);
          }
        }

        return Promise.reject(error);
      }
    );

    // Limpiar interceptor al desmontar
    return () => {
      api.interceptors.response.eject(responseInterceptor);
    };
  }, [isRefreshing]);

  const login = async (credentials: LoginCredentials): Promise<LoginResult> => {
    try {
      setIsLoading(true);
      const outcome = await authService.login(credentials);
      if (!outcome.requires2FA) {
        setUser(outcome.user);
        toast.success(`Bienvenido, ${outcome.user.username}!`);
      }
      return { requires2FA: outcome.requires2FA };
    } catch (error) {
      console.error('Error en login:', error);
      toast.error('Error de autenticación');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  /** Llamado tras completar verificación 2FA para actualizar estado global. */
  const completeLogin = (user: User): void => {
    setUser(user);
    toast.success(`Bienvenido, ${user.username}!`);
  };

  const logout = (): void => {
    authService.logout();
    setUser(null);
    toast.success('Sesión cerrada exitosamente');
  };

  const refreshUserData = (): void => {
    const currentUser = authService.getCurrentUser();
    setUser(currentUser);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshUserData,
    completeLogin,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Hook personalizado para usar el contexto de autenticación
 */
export const useAuthContext = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthContext debe usarse dentro de un AuthProvider');
  }
  return context;
};

// Exportar el contexto para casos avanzados
export { AuthContext };