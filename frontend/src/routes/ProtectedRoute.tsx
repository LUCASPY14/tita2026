import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthContext } from '../contexts/AuthContext';
import { useHasRole } from '../hooks/usePermissions';
import { UserRole } from '../services/auth.service';
import LoadingSpinner from '../components/common/LoadingSpinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: UserRole[];
  fallback?: React.ReactNode;
}

/**
 * Componente que protege rutas basándose en autenticación y roles
 */
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRoles,
  fallback
}) => {
  const { isAuthenticated, isLoading, user } = useAuthContext();
  const location = useLocation();
  const hasRequiredRole = useHasRole(requiredRoles || []);

  // Mostrar loading mientras se verifica la autenticación
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // Si no está autenticado, redirigir a login
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  // Si requiere roles específicos y no los tiene, mostrar acceso denegado
  if (requiredRoles && requiredRoles.length > 0 && !hasRequiredRole) {
    if (fallback) {
      return <>{fallback}</>;
    }
    
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">403</h1>
          <h2 className="text-2xl font-semibold text-gray-700 mb-2">Acceso Denegado</h2>
          <p className="text-gray-600 mb-4">
            No tienes permisos suficientes para acceder a esta página.
          </p>
          <p className="text-sm text-gray-500">
            Tu rol: <span className="font-semibold">{user?.role}</span>
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Roles requeridos: <span className="font-semibold">{requiredRoles.join(', ')}</span>
          </p>
          <button
            onClick={() => window.history.back()}
            className="mt-6 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Volver atrás
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute;
