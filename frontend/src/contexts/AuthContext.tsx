/**
 * Contexto de Autenticación
 * 
 * Proporciona estado global de autenticación para toda la aplicación
 * - Usuario actual autenticado
 * - Estado de carga de autenticación
 * - Funciones de login/logout
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService, User, LoginCredentials } from '../services/auth.service';
import toast from 'react-hot-toast';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

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

  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      setIsLoading(true);
      const data = await authService.login(credentials);
      setUser(data.user);
      toast.success(`Bienvenido, ${data.user.username}!`);
    } catch (error) {
      console.error('Error en login:', error);
      toast.error('Error de autenticación');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = (): void => {
    authService.logout();
    setUser(null);
    toast.success('Sesión cerrada exitosamente');
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
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