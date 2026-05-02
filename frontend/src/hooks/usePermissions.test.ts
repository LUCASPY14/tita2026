/**
 * Tests para hook usePermissions
 */
import { renderHook } from '@testing-library/react';
import { usePermissions, useHasRole, useHasPermission } from './usePermissions';
import { useAuthContext } from '../contexts/AuthContext';

// Mock de AuthContext
vi.mock('../contexts/AuthContext', () => ({
  useAuthContext: vi.fn(),
}));

const mockedUseAuthContext = useAuthContext as vi.MockedFunction<typeof useAuthContext>;

describe('usePermissions', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Admin permissions', () => {
    it('debe tener todos los permisos cuando el rol es admin', () => {
      mockedUseAuthContext.mockReturnValue({
        user: { id: 1, username: 'admin', email: 'admin@test.com', role: 'admin' },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        logout: vi.fn(),
        refreshUserData: vi.fn(),
      });

      const { result } = renderHook(() => usePermissions());

      expect(result.current.canViewReports).toBe(true);
      expect(result.current.canManageUsers).toBe(true);
      expect(result.current.canManageConfiguration).toBe(true);
      expect(result.current.canProcessSales).toBe(true);
      expect(result.current.canManageInventory).toBe(true);
      expect(result.current.canViewFinancialReports).toBe(true);
    });
  });

  describe('Gerente permissions', () => {
    it('debe tener permisos de gerente sin gestión de usuarios', () => {
      mockedUseAuthContext.mockReturnValue({
        user: { id: 2, username: 'gerente', email: 'gerente@test.com', role: 'gerente' },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        logout: vi.fn(),
        refreshUserData: vi.fn(),
      });

      const { result } = renderHook(() => usePermissions());

      expect(result.current.canViewReports).toBe(true);
      expect(result.current.canManageUsers).toBe(false); // No puede gestionar usuarios
      expect(result.current.canManageConfiguration).toBe(true);
      expect(result.current.canProcessSales).toBe(true);
      expect(result.current.canManageInventory).toBe(true);
      expect(result.current.canViewFinancialReports).toBe(true);
    });
  });

  describe('Cajero permissions', () => {
    it('debe tener permisos limitados a operaciones de caja', () => {
      mockedUseAuthContext.mockReturnValue({
        user: { id: 3, username: 'cajero', email: 'cajero@test.com', role: 'cajero' },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        logout: vi.fn(),
        refreshUserData: vi.fn(),
      });

      const { result } = renderHook(() => usePermissions());

      expect(result.current.canProcessSales).toBe(true);
      expect(result.current.canProcessReturns).toBe(true);
      expect(result.current.canManageRecharges).toBe(true);
      expect(result.current.canViewInventory).toBe(true);
      
      // Permisos que NO debe tener
      expect(result.current.canViewReports).toBe(false);
      expect(result.current.canManageUsers).toBe(false);
      expect(result.current.canManageInventory).toBe(false);
      expect(result.current.canViewFinancialReports).toBe(false);
    });
  });

  describe('Empleado permissions', () => {
    it('debe tener permisos muy limitados', () => {
      mockedUseAuthContext.mockReturnValue({
        user: { id: 4, username: 'empleado', email: 'empleado@test.com', role: 'empleado' },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        logout: vi.fn(),
        refreshUserData: vi.fn(),
      });

      const { result } = renderHook(() => usePermissions());

      expect(result.current.canViewInventory).toBe(true);
      expect(result.current.canViewClients).toBe(true);
      expect(result.current.canRegisterLunchConsumption).toBe(true);
      
      // Permisos que NO debe tener
      expect(result.current.canProcessSales).toBe(false);
      expect(result.current.canViewReports).toBe(false);
      expect(result.current.canManageUsers).toBe(false);
      expect(result.current.canManageInventory).toBe(false);
    });
  });

  describe('Sin usuario autenticado', () => {
    it('debe no tener ningún permiso cuando no hay usuario', () => {
      mockedUseAuthContext.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        logout: vi.fn(),
        refreshUserData: vi.fn(),
      });

      const { result } = renderHook(() => usePermissions());

      expect(result.current.canViewReports).toBe(false);
      expect(result.current.canManageUsers).toBe(false);
      expect(result.current.canProcessSales).toBe(false);
      expect(result.current.canManageInventory).toBe(false);
    });
  });
});

describe('useHasRole', () => {
  it('debe retornar true si el usuario tiene uno de los roles permitidos', () => {
    mockedUseAuthContext.mockReturnValue({
      user: { id: 1, username: 'admin', email: 'admin@test.com', role: 'admin' },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshUserData: vi.fn(),
    });

    const { result } = renderHook(() => useHasRole(['admin', 'gerente']));
    expect(result.current).toBe(true);
  });

  it('debe retornar false si el usuario no tiene ninguno de los roles permitidos', () => {
    mockedUseAuthContext.mockReturnValue({
      user: { id: 2, username: 'empleado', email: 'empleado@test.com', role: 'empleado' },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshUserData: vi.fn(),
    });

    const { result } = renderHook(() => useHasRole(['admin', 'gerente']));
    expect(result.current).toBe(false);
  });

  it('debe retornar false si no hay usuario autenticado', () => {
    mockedUseAuthContext.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshUserData: vi.fn(),
    });

    const { result } = renderHook(() => useHasRole(['admin']));
    expect(result.current).toBe(false);
  });
});

describe('useHasPermission', () => {
  it('debe retornar true si el usuario tiene al menos uno de los permisos requeridos', () => {
    mockedUseAuthContext.mockReturnValue({
      user: { id: 1, username: 'cajero', email: 'cajero@test.com', role: 'cajero' },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshUserData: vi.fn(),
    });

    const { result } = renderHook(() => useHasPermission(['canProcessSales', 'canManageUsers']));
    expect(result.current).toBe(true); // Tiene canProcessSales
  });

  it('debe retornar false si el usuario no tiene ninguno de los permisos requeridos', () => {
    mockedUseAuthContext.mockReturnValue({
      user: { id: 1, username: 'empleado', email: 'empleado@test.com', role: 'empleado' },
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      logout: vi.fn(),
      refreshUserData: vi.fn(),
    });

    const { result } = renderHook(() => useHasPermission(['canManageUsers', 'canViewReports']));
    expect(result.current).toBe(false);
  });
});
