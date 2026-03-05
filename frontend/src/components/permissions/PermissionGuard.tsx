/**
 * Componente PermissionGuard
 * 
 * Protege componentes y rutas según permisos del usuario
 * Solo renderiza children si el usuario tiene los permisos requeridos
 */

import React from 'react';
import { usePermissions } from '../../contexts/PermissionsContext';
import { AlertTriangle } from 'lucide-react';

export interface PermissionGuardProps {
  children: React.ReactNode;
  /** Permiso único requerido */
  permission?: string;
  /** Lista de permisos, requiere AL MENOS UNO */
  anyPermission?: string[];
  /** Lista de permisos, requiere TODOS */
  allPermissions?: string[];
  /** Requiere ser administrador */
  requireAdmin?: boolean;
  /** Componente a renderizar si no tiene permisos */
  fallback?: React.ReactNode;
  /** Si true, renderiza null en lugar del fallback */
  hideOnDenied?: boolean;
}

/**
 * PermissionGuard - Protección visual de componentes
 * 
 * @example
 * // Requiere un permiso específico
 * <PermissionGuard permission="ventas.crear">
 *   <Button onClick={crearVenta}>Crear Venta</Button>
 * </PermissionGuard>
 * 
 * @example
 * // Requiere al menos uno de los permisos
 * <PermissionGuard anyPermission={['ventas.ver', 'ventas.crear']}>
 *   <VentasTable />
 * </PermissionGuard>
 * 
 * @example
 * // Requiere todos los permisos
 * <PermissionGuard allPermissions={['ventas.crear', 'ventas.aplicar_descuentos']}>
 *   <VentaConDescuento />
 * </PermissionGuard>
 * 
 * @example
 * // Solo administradores
 * <PermissionGuard requireAdmin>
 *   <ConfiguracionAvanzada />
 * </PermissionGuard>
 * 
 * @example
 * // Con componente fallback personalizado
 * <PermissionGuard 
 *   permission="usuarios.ver"
 *   fallback={<div>No tienes permisos para ver usuarios</div>}
 * >
 *   <UsersList />
 * </PermissionGuard>
 * 
 * @example
 * // Ocultar completamente si no tiene permisos
 * <PermissionGuard permission="admin.ver_logs" hideOnDenied>
 *   <LogsButton />
 * </PermissionGuard>
 */
export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  children,
  permission,
  anyPermission,
  allPermissions,
  requireAdmin,
  fallback,
  hideOnDenied = false,
}) => {
  const { hasPermission, hasAnyPermission, hasAllPermissions, hasAdminAccess, isLoading } = usePermissions();

  // Mientras carga permisos, no renderizar nada (evita flashes de contenido)
  if (isLoading) {
    return null;
  }

  let hasAccess = true;

  // Verificar acceso según los parámetros proporcionados
  if (requireAdmin) {
    hasAccess = hasAdminAccess();
  } else if (permission) {
    hasAccess = hasPermission(permission);
  } else if (anyPermission && anyPermission.length > 0) {
    hasAccess = hasAnyPermission(anyPermission);
  } else if (allPermissions && allPermissions.length > 0) {
    hasAccess = hasAllPermissions(allPermissions);
  }

  // Si tiene acceso, renderizar children
  if (hasAccess) {
    return <>{children}</>;
  }

  // Si no tiene acceso y hideOnDenied es true, no renderizar nada
  if (hideOnDenied) {
    return null;
  }

  // Si tiene fallback personalizado, renderizarlo
  if (fallback) {
    return <>{fallback}</>;
  }

  // Fallback por defecto
  return (
    <div className="flex items-center justify-center p-8 bg-gray-50 rounded-lg border border-gray-200">
      <div className="text-center">
        <AlertTriangle className="h-12 w-12 text-amber-500 mx-auto mb-3" />
        <h3 className="text-lg font-semibold text-gray-900 mb-1">Acceso Restringido</h3>
        <p className="text-sm text-gray-600">
          No tienes permisos para acceder a esta funcionalidad.
        </p>
        <p className="text-xs text-gray-500 mt-2">
          Contacta a un administrador si necesitas acceso.
        </p>
      </div>
    </div>
  );
};

export default PermissionGuard;
