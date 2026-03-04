/**
 * Tests para componente ProtectedRoute con role-based access
 */
import { render, screen } from '@testing-library/react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';
import { useAuthContext } from '../contexts/AuthContext';
import { useHasRole } from '../hooks/usePermissions';

// Mocks
jest.mock('../contexts/AuthContext');
jest.mock('../hooks/usePermissions');

const mockedUseAuthContext = useAuthContext as jest.MockedFunction<typeof useAuthContext>;
const mockedUseHasRole = useHasRole as jest.MockedFunction<typeof useHasRole>;

const TestComponent = () => <div>Protected Content</div>;

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Loading state', () => {
    it('debe mostrar loading spinner mientras se verifica la autenticación', () => {
      mockedUseAuthContext.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: true,
        login: jest.fn(),
        logout: jest.fn(),
        refreshUserData: jest.fn(),
      });

      render(
        <BrowserRouter>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </BrowserRouter>
      );

      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('Authentication', () => {
    it('debe redirigir a login si no está autenticado', () => {
      mockedUseAuthContext.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: jest.fn(),
        logout: jest.fn(),
        refreshUserData: jest.fn(),
      });

      render(
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<div>Login Page</div>} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <TestComponent />
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      );

      expect(screen.getByText('Login Page')).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('debe mostrar el contenido si está autenticado', () => {
      mockedUseAuthContext.mockReturnValue({
        user: { id: 1, username: 'test', email: 'test@test.com', role: 'admin' },
        isAuthenticated: true,
        isLoading: false,
        login: jest.fn(),
        logout: jest.fn(),
        refreshUserData: jest.fn(),
      });

      mockedUseHasRole.mockReturnValue(true);

      render(
        <BrowserRouter>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </BrowserRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  describe('Role-based access', () => {
    it('debe mostrar el contenido si el usuario tiene el rol requerido', () => {
      mockedUseAuthContext.mockReturnValue({
        user: { id: 1, username: 'admin', email: 'admin@test.com', role: 'admin' },
        isAuthenticated: true,
        isLoading: false,
        login: jest.fn(),
        logout: jest.fn(),
        refreshUserData: jest.fn(),
      });

      mockedUseHasRole.mockReturnValue(true);

      render(
        <BrowserRouter>
          <ProtectedRoute requiredRoles={['admin']}>
            <TestComponent />
          </ProtectedRoute>
        </BrowserRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('debe mostrar página de acceso denegado si no tiene el rol requerido', () => {
      mockedUseAuthContext.mockReturnValue({
        user: { id: 2, username: 'empleado', email: 'empleado@test.com', role: 'empleado' },
        isAuthenticated: true,
        isLoading: false,
        login: jest.fn(),
        logout: jest.fn(),
        refreshUserData: jest.fn(),
      });

      mockedUseHasRole.mockReturnValue(false);

      render(
        <BrowserRouter>
          <ProtectedRoute requiredRoles={['admin', 'gerente']}>
            <TestComponent />
          </ProtectedRoute>
        </BrowserRouter>
      );

      expect(screen.getByText('403')).toBeInTheDocument();
      expect(screen.getByText('Acceso Denegado')).toBeInTheDocument();
      expect(screen.getByText(/empleado/i)).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('debe mostrar fallback personalizado si se proporciona', () => {
      mockedUseAuthContext.mockReturnValue({
        user: { id: 2, username: 'cajero', email: 'cajero@test.com', role: 'cajero' },
        isAuthenticated: true,
        isLoading: false,
        login: jest.fn(),
        logout: jest.fn(),
        refreshUserData: jest.fn(),
      });

      mockedUseHasRole.mockReturnValue(false);

      const CustomFallback = () => <div>Custom Access Denied</div>;

      render(
        <BrowserRouter>
          <ProtectedRoute
            requiredRoles={['admin']}
            fallback={<CustomFallback />}
          >
            <TestComponent />
          </ProtectedRoute>
        </BrowserRouter>
      );

      expect(screen.getByText('Custom Access Denied')).toBeInTheDocument();
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('Multiple roles', () => {
    it('debe permitir acceso si el usuario tiene uno de varios roles requeridos', () => {
      mockedUseAuthContext.mockReturnValue({
        user: { id: 3, username: 'gerente', email: 'gerente@test.com', role: 'gerente' },
        isAuthenticated: true,
        isLoading: false,
        login: jest.fn(),
        logout: jest.fn(),
        refreshUserData: jest.fn(),
      });

      mockedUseHasRole.mockReturnValue(true);

      render(
        <BrowserRouter>
          <ProtectedRoute requiredRoles={['admin', 'gerente', 'cajero']}>
            <TestComponent />
          </ProtectedRoute>
        </BrowserRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });
});
