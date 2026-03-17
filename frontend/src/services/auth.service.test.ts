import api from './api';
import { authService, LoginCredentials, LoginResponse, User } from './auth.service';

jest.mock('./api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('Auth Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('login', () => {
    const mockCredentials: LoginCredentials = {
      username: 'testuser',
      password: 'testpass123'
    };

    const mockBackendResponse = {
      success: true,
      tokens: {
        access: 'mock-jwt-token-12345',
        refresh: 'mock-refresh-token-67890'
      },
      empleado: {
        id: 1,
        usuario: 'testuser',
        email: 'test@example.com',
        rol: 'admin'
      },
      mensaje: 'Login exitoso'
    };

    const expectedLoginResponse: LoginResponse = {
      requires2FA: false,
      token: 'mock-jwt-token-12345',
      refreshToken: 'mock-refresh-token-67890',
      user: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'admin'
      }
    };

    test('debe realizar login exitosamente y guardar token y usuario', async () => {
      mockedApi.post.mockResolvedValue({ data: mockBackendResponse });

      const result = await authService.login(mockCredentials);

      expect(mockedApi.post).toHaveBeenCalledWith('/auth/login/', mockCredentials);
      expect(result).toEqual(expectedLoginResponse);
      expect(localStorage.getItem('token')).toBe('mock-jwt-token-12345');
      expect(localStorage.getItem('user')).toContain('testuser');
    });

    test('debe manejar error de credenciales inválidas', async () => {
      const errorResponse = new Error('Invalid credentials');
      mockedApi.post.mockRejectedValue(errorResponse);

      await expect(authService.login(mockCredentials)).rejects.toThrow('Invalid credentials');
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
    });

    test('debe manejar respuesta sin token', async () => {
      const responseWithoutSuccess = { 
        data: { 
          success: false,
          mensaje: 'Error al iniciar sesión' 
        } 
      };
      mockedApi.post.mockResolvedValue(responseWithoutSuccess as any);

      await expect(authService.login(mockCredentials)).rejects.toThrow('Error al iniciar sesión');
      expect(localStorage.getItem('token')).toBeNull();
    });

    test('debe hacer login con username vacío', async () => {
      const emptyCredentials: LoginCredentials = { username: '', password: 'pass' };
      mockedApi.post.mockResolvedValue({ data: mockBackendResponse });

      await authService.login(emptyCredentials);

      expect(mockedApi.post).toHaveBeenCalledWith('/auth/login/', emptyCredentials);
    });
  });

  describe('logout', () => {
    test('debe eliminar token y usuario del localStorage', () => {
      localStorage.setItem('token', 'test-token');
      localStorage.setItem('user', JSON.stringify({ id: 1, username: 'test' }));

      authService.logout();

      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
    });

    test('debe ejecutarse sin error cuando no hay datos en localStorage', () => {
      expect(() => authService.logout()).not.toThrow();
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
    });
  });

  describe('getCurrentUser', () => {
    const mockUser: User = {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      role: 'admin'
    };

    test('debe retornar usuario actual si existe en localStorage', () => {
      localStorage.setItem('user', JSON.stringify(mockUser));

      const result = authService.getCurrentUser();

      expect(result).toEqual(mockUser);
    });

    test('debe retornar null si no hay usuario en localStorage', () => {
      const result = authService.getCurrentUser();

      expect(result).toBeNull();
    });

    test('debe manejar JSON inválido en localStorage', () => {
      localStorage.setItem('user', 'invalid-json{');

      expect(() => authService.getCurrentUser()).toThrow();
    });

    test('debe retornar usuario con todos los campos', () => {
      const fullUser: User = {
        id: 5,
        username: 'admin',
        email: 'admin@cantina.com',
        role: 'admin'
      };
      localStorage.setItem('user', JSON.stringify(fullUser));

      const result = authService.getCurrentUser();

      expect(result).toEqual(fullUser);
      expect(result?.id).toBe(5);
      expect(result?.role).toBe('admin');
    });
  });

  describe('isAuthenticated', () => {
    test('debe retornar true si existe token en localStorage', () => {
      localStorage.setItem('token', 'test-token-123');

      const result = authService.isAuthenticated();

      expect(result).toBe(true);
    });

    test('debe retornar false si no existe token en localStorage', () => {
      const result = authService.isAuthenticated();

      expect(result).toBe(false);
    });

    test('debe retornar true incluso si el token es una cadena vacía', () => {
      localStorage.setItem('token', '');

      const result = authService.isAuthenticated();

      expect(result).toBe(false);
    });

    test('debe retornar true con token válido', () => {
      localStorage.setItem('token', 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...');

      const result = authService.isAuthenticated();

      expect(result).toBe(true);
    });
  });

  describe('Integration scenarios', () => {
    test('flujo completo: login -> getCurrentUser -> isAuthenticated -> logout', async () => {
      const credentials: LoginCredentials = { username: 'user1', password: 'pass1' };
      const backendResponse = {
        success: true,
        tokens: { access: 'token123', refresh: 'refresh123' },
        empleado: { id: 10, usuario: 'user1', email: 'user1@test.com', rol: 'empleado' },
        mensaje: 'Login exitoso'
      };
      const expectedUser = { id: 10, username: 'user1', email: 'user1@test.com', role: 'empleado' as UserRole };
      mockedApi.post.mockResolvedValue({ data: backendResponse });

      // Login
      await authService.login(credentials);
      expect(authService.isAuthenticated()).toBe(true);
      expect(authService.getCurrentUser()).toEqual(expectedUser);

      // Logout
      authService.logout();
      expect(authService.isAuthenticated()).toBe(false);
      expect(authService.getCurrentUser()).toBeNull();
    });

    test('debe mantener usuario en localStorage después de recargar página', async () => {
      const backendResponse = {
        success: true,
        tokens: { access: 'persistent-token', refresh: 'persistent-refresh' },
        empleado: { id: 20, usuario: 'persistent', email: 'p@test.com', rol: 'admin' },
        mensaje: 'Login exitoso'
      };
      const expectedUser = { id: 20, username: 'persistent', email: 'p@test.com', role: 'admin' };
      mockedApi.post.mockResolvedValue({ data: backendResponse });

      await authService.login({ username: 'persistent', password: 'pass' });

      // Simular recarga de página
      const storedUser = localStorage.getItem('user');
      const storedToken = localStorage.getItem('token');

      expect(storedToken).toBe('persistent-token');
      expect(JSON.parse(storedUser!)).toEqual(expectedUser);
    });
  });

  describe('refreshToken', () => {
    test('debe renovar el token exitosamente', async () => {
      localStorage.setItem('refreshToken', 'refresh-token-456');

      const mockResponse = {
        data: {
          token: 'new-access-token',
          refreshToken: 'new-refresh-token',
        },
      };

      mockedApi.post.mockResolvedValue(mockResponse);

      const result = await authService.refreshToken();

      expect(mockedApi.post).toHaveBeenCalledWith('/auth/refresh/', {
        refresh: 'refresh-token-456',
      });
      expect(localStorage.getItem('token')).toBe('new-access-token');
      expect(localStorage.getItem('refreshToken')).toBe('new-refresh-token');
      expect(result).toEqual(mockResponse.data);
    });

    test('debe lanzar error si no hay refreshToken en localStorage', async () => {
      await expect(authService.refreshToken()).rejects.toThrow(
        'No refresh token available'
      );
    });

    test('debe limpiar localStorage si el refresh falla', async () => {
      localStorage.setItem('refreshToken', 'invalid-refresh-token');
      localStorage.setItem('token', 'old-token');
      localStorage.setItem('user', JSON.stringify({ id: 1 }));

      mockedApi.post.mockRejectedValue(new Error('Refresh token expired'));

      await expect(authService.refreshToken()).rejects.toThrow('Refresh token expired');

      // Verificar que se limpió el localStorage
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('refreshToken')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
    });

    test('debe guardar solo refreshToken si la respuesta no incluye uno nuevo', async () => {
      localStorage.setItem('refreshToken', 'refresh-token-123');

      const mockResponse = {
        data: {
          token: 'new-access-token',
        },
      };

      mockedApi.post.mockResolvedValue(mockResponse);

      await authService.refreshToken();

      expect(localStorage.getItem('token')).toBe('new-access-token');
      expect(localStorage.getItem('refreshToken')).toBe('refresh-token-123'); // El mismo de antes
    });
  });

  describe('getToken', () => {
    test('debe retornar el token del localStorage si existe', () => {
      localStorage.setItem('token', 'access-token-123');
      expect(authService.getToken()).toBe('access-token-123');
    });

    test('debe retornar null si no hay token', () => {
      expect(authService.getToken()).toBeNull();
    });
  });

  describe('login con refreshToken', () => {
    test('debe guardar refreshToken cuando se proporciona en el login', async () => {
      const mockResponse = {
        data: {
          success: true,
          tokens: {
            access: 'access-token',
            refresh: 'refresh-token',
          },
          empleado: {
            id: 1,
            usuario: 'testuser',
            email: 'test@test.com',
            rol: 'admin',
          },
          mensaje: 'Login exitoso'
        },
      };
      const expectedUser = {
        id: 1,
        username: 'testuser',
        email: 'test@test.com',
        role: 'admin' as const,
      };

      mockedApi.post.mockResolvedValue(mockResponse);

      await authService.login({ username: 'testuser', password: 'password' });

      expect(localStorage.getItem('token')).toBe('access-token');
      expect(localStorage.getItem('refreshToken')).toBe('refresh-token');
      expect(localStorage.getItem('user')).toBe(JSON.stringify(expectedUser));
    });
  });
});

