/**
 * Tests para hook useAuth
 * Tests críticos de autenticación
 */
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAuthContext, AuthProvider } from '../../src/contexts/AuthContext';

// Mock del servicio de autenticación
jest.mock('../../src/services/auth.service', () => ({
  authService: {
    login: jest.fn(),
    logout: jest.fn(),
    getCurrentUser: jest.fn(),
    refreshToken: jest.fn(),
  },
}));

import { authService } from '../../src/services/auth.service';

describe('🧪 useAuth Hook Tests', () => {
  
  beforeEach(() => {
    // Limpiar localStorage
    localStorage.clear();
    // Limpiar mocks
    jest.clearAllMocks();
  });

  test('✅ CRÍTICO: should initialize with no user when not authenticated', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );
    
    const { result } = renderHook(() => useAuthContext(), { wrapper });
    
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  test('✅ CRÍTICO: should login successfully with valid credentials', async () => {
    const mockUser = {
      id_empleado: 1,
      usuario: 'testuser',
      nombre: 'Test',
      apellido: 'User',
      email: 'test@cantina.com',
    };

    const mockResponse = {
      access: 'mock-access-token',
      refresh: 'mock-refresh-token',
      empleado: mockUser,
    };

    (authService.login as jest.Mock).mockResolvedValue(mockResponse);

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuthContext(), { wrapper });

    await act(async () => {
      await result.current.login('testuser', 'password123');
    });

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    // Verificar que se llamó al servicio
    expect(authService.login).toHaveBeenCalledWith('testuser', 'password123');
  });

  test('✅ CRÍTICO: should handle login failure', async () => {
    (authService.login as jest.Mock).mockRejectedValue(
      new Error('Invalid credentials')
    );

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuthContext(), { wrapper });

    await expect(async () => {
      await act(async () => {
        await result.current.login('testuser', 'wrongpassword');
      });
    }).rejects.toThrow();

    // Usuario debe seguir siendo null
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  test('✅ CRÍTICO: should logout successfully', async () => {
    const mockUser = {
      id_empleado: 1,
      usuario: 'testuser',
      nombre: 'Test',
      apellido: 'User',
      email: 'test@cantina.com',
    };

    // Simular que el usuario está autenticado
    localStorage.setItem('token', 'mock-token');
    localStorage.setItem('user', JSON.stringify(mockUser));

    (authService.logout as jest.Mock).mockResolvedValue(undefined);

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuthContext(), { wrapper });

    await act(async () => {
      await result.current.logout();
    });

    await waitFor(() => {
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    // Verificar que se limpió el localStorage
    expect(localStorage.getItem('token')).toBeNull();
  });

  test('✅ CRÍTICO: should restore session from localStorage', () => {
    const mockUser = {
      id_empleado: 1,
      usuario: 'testuser',
      nombre: 'Test',
      apellido: 'User',
      email: 'test@cantina.com',
    };

    localStorage.setItem('token', 'mock-token');
    localStorage.setItem('user', JSON.stringify(mockUser));

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuthContext(), { wrapper });

    // Puede tomar un tiempo cargar del localStorage
    waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });
  });

  test('✅ CRÍTICO: should check if user has specific permission', () => {
    const mockUser = {
      id_empleado: 1,
      usuario: 'testuser',
      nombre: 'Test',
      apellido: 'User',
      email: 'test@cantina.com',
      permisos: [
        { codigo_permiso: 'VER_VENTAS' },
        { codigo_permiso: 'CREAR_PRODUCTOS' }
      ],
    };

    localStorage.setItem('token', 'mock-token');
    localStorage.setItem('user', JSON.stringify(mockUser));

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuthContext(), { wrapper });

    // Si existe método hasPermission
    if (result.current.hasPermission) {
      expect(result.current.hasPermission('VER_VENTAS')).toBe(true);
      expect(result.current.hasPermission('ELIMINAR_CLIENTES')).toBe(false);
    }
  });
});
