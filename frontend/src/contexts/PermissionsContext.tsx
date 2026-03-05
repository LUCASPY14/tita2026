/**
 * Contexto de Permisos
 * 
 * Proporciona estado global de permisos para toda la aplicación
 * - Permisos del usuario actual
 * - Funciones de verificación de permisos
 * - Carga automática al autenticarse
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuthContext } from './AuthContext';
import axios from '../utils/axiosConfig';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

interface PermissionsContextType {
  permisos: string[];
  isLoading: boolean;
  hasPermission: (permiso: string) => boolean;
  hasAnyPermission: (permisos: string[]) => boolean;
  hasAllPermissions: (permisos: string[]) => boolean;
  hasAdminAccess: () => boolean;
  recargarPermisos: () => Promise<void>;
}

const PermissionsContext = createContext<PermissionsContextType | undefined>(undefined);

export interface PermissionsProviderProps {
  children: React.ReactNode;
}

export const PermissionsProvider: React.FC<PermissionsProviderProps> = ({ children }) => {
  const { user, isAuthenticated } = useAuthContext();
  const [permisos, setPermisos] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const cargarPermisos = useCallback(async () => {
    if (!isAuthenticated) {
      setPermisos([]);
      return;
    }

    try {
      setIsLoading(true);
      const response = await axios.get(`${API_URL}/auth/perfil/`);
      const permisosData = response.data.permisos || [];
      setPermisos(permisosData);
    } catch (error) {
      console.error('Error cargando permisos:', error);
      setPermisos([]);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  // Cargar permisos cuando el usuario se autentique
  useEffect(() => {
    if (isAuthenticated && user) {
      cargarPermisos();
    } else {
      setPermisos([]);
    }
  }, [isAuthenticated, user, cargarPermisos]);

  /**
   * Verifica si el usuario tiene un permiso específico
   */
  const hasPermission = useCallback(
    (permiso: string): boolean => {
      // Si tiene acceso total admin, tiene todos los permisos
      if (permisos.includes('admin.acceso_total')) {
        return true;
      }
      return permisos.includes(permiso);
    },
    [permisos]
  );

  /**
   * Verifica si el usuario tiene AL MENOS UNO de los permisos especificados
   */
  const hasAnyPermission = useCallback(
    (permisosRequeridos: string[]): boolean => {
      if (permisos.includes('admin.acceso_total')) {
        return true;
      }
      return permisosRequeridos.some((p) => permisos.includes(p));
    },
    [permisos]
  );

  /**
   * Verifica si el usuario tiene TODOS los permisos especificados
   */
  const hasAllPermissions = useCallback(
    (permisosRequeridos: string[]): boolean => {
      if (permisos.includes('admin.acceso_total')) {
        return true;
      }
      return permisosRequeridos.every((p) => permisos.includes(p));
    },
    [permisos]
  );

  /**
   * Verifica si el usuario tiene acceso de administrador total
   */
  const hasAdminAccess = useCallback((): boolean => {
    return permisos.includes('admin.acceso_total');
  }, [permisos]);

  /**
   * Recarga los permisos del usuario
   */
  const recargarPermisos = useCallback(async () => {
    await cargarPermisos();
  }, [cargarPermisos]);

  const value: PermissionsContextType = {
    permisos,
    isLoading,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasAdminAccess,
    recargarPermisos,
  };

  return <PermissionsContext.Provider value={value}>{children}</PermissionsContext.Provider>;
};

/**
 * Hook personalizado para usar el contexto de permisos
 */
export const usePermissions = (): PermissionsContextType => {
  const context = useContext(PermissionsContext);
  if (context === undefined) {
    throw new Error('usePermissions debe usarse dentro de un PermissionsProvider');
  }
  return context;
};

// Exportar el contexto para casos avanzados
export { PermissionsContext };
