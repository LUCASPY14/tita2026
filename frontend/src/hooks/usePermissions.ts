/**
 * Hook para manejar permisos basados en roles de usuario
 */
import { useAuthContext } from '../contexts/AuthContext';
import { UserRole } from '../services/auth.service';

export interface Permissions {
  // Permisos generales
  canViewReports: boolean;
  canManageUsers: boolean;
  canManageConfiguration: boolean;
  
  // Permisos de ventas
  canProcessSales: boolean;
  canProcessReturns: boolean;
  canViewSalesHistory: boolean;
  
  // Permisos de inventario
  canManageInventory: boolean;
  canViewInventory: boolean;
  canManageProducts: boolean;
  
  // Permisos de compras
  canManagePurchases: boolean;
  canViewPurchases: boolean;
  
  // Permisos de clientes
  canManageClients: boolean;
  canViewClients: boolean;
  canManageAccountBalance: boolean;
  
  // Permisos de almuerzos
  canManageLunchSubscriptions: boolean;
  canRegisterLunchConsumption: boolean;
  
  // Permisos financieros
  canViewFinancialReports: boolean;
  canManageRecharges: boolean;
}

/**
 * Hook que retorna los permisos del usuario actual basado en su rol
 */
export const usePermissions = (): Permissions => {
  const { user } = useAuthContext();
  const role: UserRole | undefined = user?.role;

  // Si no hay usuario, no tiene permisos
  if (!role) {
    return {
      canViewReports: false,
      canManageUsers: false,
      canManageConfiguration: false,
      canProcessSales: false,
      canProcessReturns: false,
      canViewSalesHistory: false,
      canManageInventory: false,
      canViewInventory: false,
      canManageProducts: false,
      canManagePurchases: false,
      canViewPurchases: false,
      canManageClients: false,
      canViewClients: false,
      canManageAccountBalance: false,
      canManageLunchSubscriptions: false,
      canRegisterLunchConsumption: false,
      canViewFinancialReports: false,
      canManageRecharges: false,
    };
  }

  // Define permisos por rol
  const rolePermissions: Record<UserRole, Permissions> = {
    admin: {
      // Admin tiene todos los permisos
      canViewReports: true,
      canManageUsers: true,
      canManageConfiguration: true,
      canProcessSales: true,
      canProcessReturns: true,
      canViewSalesHistory: true,
      canManageInventory: true,
      canViewInventory: true,
      canManageProducts: true,
      canManagePurchases: true,
      canViewPurchases: true,
      canManageClients: true,
      canViewClients: true,
      canManageAccountBalance: true,
      canManageLunchSubscriptions: true,
      canRegisterLunchConsumption: true,
      canViewFinancialReports: true,
      canManageRecharges: true,
    },
    gerente: {
      // Gerente tiene casi todos los permisos excepto gestión de usuarios
      canViewReports: true,
      canManageUsers: false,
      canManageConfiguration: true,
      canProcessSales: true,
      canProcessReturns: true,
      canViewSalesHistory: true,
      canManageInventory: true,
      canViewInventory: true,
      canManageProducts: true,
      canManagePurchases: true,
      canViewPurchases: true,
      canManageClients: true,
      canViewClients: true,
      canManageAccountBalance: true,
      canManageLunchSubscriptions: true,
      canRegisterLunchConsumption: true,
      canViewFinancialReports: true,
      canManageRecharges: true,
    },
    supervisor: {
      // Supervisor puede ver reportes y supervisar operaciones
      canViewReports: true,
      canManageUsers: false,
      canManageConfiguration: false,
      canProcessSales: true,
      canProcessReturns: true,
      canViewSalesHistory: true,
      canManageInventory: false,
      canViewInventory: true,
      canManageProducts: false,
      canManagePurchases: false,
      canViewPurchases: true,
      canManageClients: false,
      canViewClients: true,
      canManageAccountBalance: false,
      canManageLunchSubscriptions: false,
      canRegisterLunchConsumption: true,
      canViewFinancialReports: false,
      canManageRecharges: true,
    },
    cajero: {
      // Cajero puede hacer operaciones de venta y recargas
      canViewReports: false,
      canManageUsers: false,
      canManageConfiguration: false,
      canProcessSales: true,
      canProcessReturns: true,
      canViewSalesHistory: true,
      canManageInventory: false,
      canViewInventory: true,
      canManageProducts: false,
      canManagePurchases: false,
      canViewPurchases: false,
      canManageClients: false,
      canViewClients: true,
      canManageAccountBalance: false,
      canManageLunchSubscriptions: false,
      canRegisterLunchConsumption: true,
      canViewFinancialReports: false,
      canManageRecharges: true,
    },
    cobrador: {
      // Cobrador gestiona pagos y cuentas corrientes de clientes
      canViewReports: false,
      canManageUsers: false,
      canManageConfiguration: false,
      canProcessSales: false,
      canProcessReturns: false,
      canViewSalesHistory: true,
      canManageInventory: false,
      canViewInventory: false,
      canManageProducts: false,
      canManagePurchases: false,
      canViewPurchases: false,
      canManageClients: true,
      canViewClients: true,
      canManageAccountBalance: true,
      canManageLunchSubscriptions: false,
      canRegisterLunchConsumption: false,
      canViewFinancialReports: false,
      canManageRecharges: true,
    },
    compras: {
      // Compras gestiona productos, inventario, compras y proveedores
      canViewReports: true,
      canManageUsers: false,
      canManageConfiguration: false,
      canProcessSales: false,
      canProcessReturns: false,
      canViewSalesHistory: false,
      canManageInventory: true,
      canViewInventory: true,
      canManageProducts: true,
      canManagePurchases: true,
      canViewPurchases: true,
      canManageClients: false,
      canViewClients: false,
      canManageAccountBalance: false,
      canManageLunchSubscriptions: false,
      canRegisterLunchConsumption: false,
      canViewFinancialReports: false,
      canManageRecharges: false,
    },
    empleado: {
      // Empleado tiene permisos muy limitados
      canViewReports: false,
      canManageUsers: false,
      canManageConfiguration: false,
      canProcessSales: false,
      canProcessReturns: false,
      canViewSalesHistory: false,
      canManageInventory: false,
      canViewInventory: true,
      canManageProducts: false,
      canManagePurchases: false,
      canViewPurchases: false,
      canManageClients: false,
      canViewClients: true,
      canManageAccountBalance: false,
      canManageLunchSubscriptions: false,
      canRegisterLunchConsumption: true,
      canViewFinancialReports: false,
      canManageRecharges: false,
    },
  };

  return rolePermissions[role];
};

/**
 * Hook para verificar si el usuario tiene un rol específico
 */
export const useHasRole = (allowedRoles: UserRole[]): boolean => {
  const { user } = useAuthContext();
  
  if (!user?.role) {
    return false;
  }
  
  return allowedRoles.includes(user.role);
};

/**
 * Hook para verificar si el usuario tiene al menos uno de los permisos especificados
 */
export const useHasPermission = (requiredPermissions: (keyof Permissions)[]): boolean => {
  const permissions = usePermissions();
  
  return requiredPermissions.some((permission) => permissions[permission]);
};
