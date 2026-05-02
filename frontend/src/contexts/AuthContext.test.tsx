/**
 * Tests para AuthContext
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuthContext } from './AuthContext';
import { authService, UserRole } from '../services/auth.service';
import toast from 'react-hot-toast';

// Mock del servicio de autenticación
vi.mock('../services/auth.service', () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn(),
    getCurrentUser: vi.fn(),
    isAuthenticated: vi.fn(),
    refreshToken: vi.fn(),
    getToken: vi.fn(),
  },
}));

// Mock de react-hot-toast
vi.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockedAuthService = authService as vi.Mocked<typeof authService>;
const mockedToast = toast as vi.Mocked<typeof toast>;

// Componente de prueba para testing
const TestComponent = () => {
  const { user, isAuthenticated, isLoading, login, logout, refreshUserData } = useAuthContext();

  const handleLogin = async () => {
    try {
      await login({ username: 'test', password: 'test' });
    } catch (error) {
      // Error manejado por AuthContext (toast), solo silenciamos aquí para los tests
    }
  };

  if (isLoading) {
    return <div>Cargando...</div>;
  }

  return (
    <div>
      <div data-testid="auth-status">
        {isAuthenticated ? `Usuario: ${user?.username}` : 'No autenticado'}
      </div>
      <div data-testid="user-id">{user?.id || 'Sin ID'}</div>
      <button onClick={handleLogin}>Login</button>
      <button onClick={logout}>Logout</button>
      <button onClick={refreshUserData}>Refresh User Data</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('inicializa con estado no autenticado cuando no hay usuario', async () => {
    mockedAuthService.getCurrentUser.mockReturnValue(null);
    mockedAuthService.isAuthenticated.mockReturnValue(false);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('No autenticado')).toBeInTheDocument();
      expect(screen.getByText('Sin ID')).toBeInTheDocument();
    });
  });

  test('inicializa con usuario autenticado cuando hay datos válidos', async () => {
    const mockUser = {
      id: 1,
      username: 'testuser',
      email: 'test@test.com',
      role: 'admin' as UserRole,
    };

    mockedAuthService.getCurrentUser.mockReturnValue(mockUser);
    mockedAuthService.isAuthenticated.mockReturnValue(true);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Usuario: testuser')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
    });
  });

  test('realiza login exitosamente', async () => {
    const user = userEvent.setup();
    const mockUser = {
      id: 1,
      username: 'testuser',
      email: 'test@test.com',
      role: 'admin' as UserRole,
    };

    mockedAuthService.getCurrentUser.mockReturnValue(null);
    mockedAuthService.isAuthenticated.mockReturnValue(false);
    mockedAuthService.login.mockResolvedValue({
      requires2FA: false,
      token: 'test-token',
      user: mockUser,
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Esperar a que cargue el estado inicial
    await waitFor(() => {
      expect(screen.getByText('No autenticado')).toBeInTheDocument();
    });

    // Hacer login
    await user.click(screen.getByText('Login'));

    await waitFor(() => {
      expect(mockedAuthService.login).toHaveBeenCalledWith({
        username: 'test',
        password: 'test',
      });
      expect(screen.getByText('Usuario: testuser')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
    });
  });

  test('realiza logout correctamente', async () => {
    const user = userEvent.setup();
    const mockUser = {
      id: 1,
      username: 'testuser',
      email: 'test@test.com',
      role: 'admin' as UserRole,
    };

    mockedAuthService.getCurrentUser.mockReturnValue(mockUser);
    mockedAuthService.isAuthenticated.mockReturnValue(true);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Verificar estado inicial autenticado
    await waitFor(() => {
      expect(screen.getByText('Usuario: testuser')).toBeInTheDocument();
    });

    // Hacer logout
    await user.click(screen.getByText('Logout'));

    await waitFor(() => {
      expect(mockedAuthService.logout).toHaveBeenCalled();
      expect(screen.getByText('No autenticado')).toBeInTheDocument();
      expect(screen.getByText('Sin ID')).toBeInTheDocument();
    });
  });

  test('maneja error de login', async () => {
    const user = userEvent.setup();
    
    mockedAuthService.getCurrentUser.mockReturnValue(null);
    mockedAuthService.isAuthenticated.mockReturnValue(false);
    mockedAuthService.login.mockRejectedValue(new Error('Login failed'));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('No autenticado')).toBeInTheDocument();
    });

    // Intento de login fallido
    await user.click(screen.getByText('Login'));

    await waitFor(() => {
      expect(mockedAuthService.login).toHaveBeenCalled();
      // Debe mantenerse no autenticado después del error
      expect(screen.getByText('No autenticado')).toBeInTheDocument();
    });

    // Verificamos que se mostró el toast de error
    expect(mockedToast.error).toHaveBeenCalledWith('Error de autenticación');
  });

  test('lanza error cuando se usa fuera del provider', () => {
    // Capturar error de consola
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useAuthContext debe usarse dentro de un AuthProvider');

    consoleSpy.mockRestore();
  });
});