/**
 * Tests E2E de página de Login
 * Smoke tests del flujo de autenticación
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Login from '../../src/pages/auth/Login';
import { AuthProvider } from '../../src/contexts/AuthContext';

// Mock del servicio de autenticación
jest.mock('../../src/services/auth.service');
import { authService } from '../../src/services/auth.service';

// Mock de useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

const renderLoginPage = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <Login />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('🧪 Login Page E2E Tests', () => {
  
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('✅ CRÍTICO: should render login form with all elements', () => {
    renderLoginPage();
    
    // Verificar título
    expect(screen.getByText(/Cantina Tita/i)).toBeInTheDocument();
    expect(screen.getByText(/Iniciar Sesión/i)).toBeInTheDocument();
    
    // Verificar campos de entrada
    expect(screen.getByLabelText(/Usuario/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Contraseña/i)).toBeInTheDocument();
    
    // Verificar botón de login
    expect(screen.getByRole('button', { name: /Ingresar/i })).toBeInTheDocument();
  });

  test('✅ CRÍTICO: should show validation errors for empty fields', async () => {
    renderLoginPage();
    
    const submitButton = screen.getByRole('button', { name: /Ingresar/i });
    
    // Intentar enviar sin llenar campos
    fireEvent.click(submitButton);
    
    // Esperar mensajes de validación
    await waitFor(() => {
      const errorMessages = screen.getAllByText(/requerido|obligatorio/i);
      expect(errorMessages.length).toBeGreaterThan(0);
    });
  });

  test('✅ CRÍTICO: should handle successful login', async () => {
    const mockUser = {
      id_empleado: 1,
      usuario: 'admin',
      nombre: 'Administrador',
      apellido: 'Sistema',
      email: 'admin@cantina.com',
    };

    (authService.login as jest.Mock).mockResolvedValue({
      access: 'mock-token',
      refresh: 'mock-refresh-token',
      empleado: mockUser,
    });

    renderLoginPage();
    
    // Llenar formulario
    const usernameInput = screen.getByLabelText(/Usuario/i);
    const passwordInput = screen.getByLabelText(/Contraseña/i);
    const submitButton = screen.getByRole('button', { name: /Ingresar/i });
    
    fireEvent.change(usernameInput, { target: { value: 'admin' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    
    // Enviar formulario
    fireEvent.click(submitButton);
    
    // Verificar que se llamó al servicio de login
    await waitFor(() => {
      expect(authService.login).toHaveBeenCalledWith('admin', 'password123');
    });
    
    // Verificar navegación al dashboard
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  test('✅ CRÍTICO: should show error message on invalid credentials', async () => {
    (authService.login as jest.Mock).mockRejectedValue(
      new Error('Credenciales inválidas')
    );

    renderLoginPage();
    
    // Llenar y enviar formulario
    fireEvent.change(screen.getByLabelText(/Usuario/i), { 
      target: { value: 'wronguser' } 
    });
    fireEvent.change(screen.getByLabelText(/Contraseña/i), { 
      target: { value: 'wrongpass' } 
    });
    fireEvent.click(screen.getByRole('button', { name: /Ingresar/i }));
    
    // Verificar mensaje de error
    await waitFor(() => {
      expect(screen.getByText(/Credenciales inválidas|Usuario o contraseña incorrectos/i))
        .toBeInTheDocument();
    });
    
    // No debe navegar
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  test('✅ CRÍTICO: should show error for inactive user', async () => {
    (authService.login as jest.Mock).mockRejectedValue(
      new Error('Usuario inactivo')
    );

    renderLoginPage();
    
    fireEvent.change(screen.getByLabelText(/Usuario/i), { 
      target: { value: 'inactiveuser' } 
    });
    fireEvent.change(screen.getByLabelText(/Contraseña/i), { 
      target: { value: 'password' } 
    });
    fireEvent.click(screen.getByRole('button', { name: /Ingresar/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/Usuario inactivo|cuenta desactivada/i))
        .toBeInTheDocument();
    });
  });

  test('✅ CRÍTICO: should toggle password visibility', () => {
    renderLoginPage();
    
    const passwordInput = screen.getByLabelText(/Contraseña/i);
    
    // Inicialmente debe ser tipo password
    expect(passwordInput).toHaveAttribute('type', 'password');
    
    // Buscar botón de toggle (ícono de ojo)
    const toggleButton = screen.getByRole('button', { name: /mostrar|ver contraseña/i });
    
    // Click para mostrar
    fireEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'text');
    
    // Click para ocultar
    fireEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('✅ CRÍTICO: should disable submit button while loading', async () => {
    // Simular login lento
    (authService.login as jest.Mock).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 1000))
    );

    renderLoginPage();
    
    const submitButton = screen.getByRole('button', { name: /Ingresar/i });
    
    fireEvent.change(screen.getByLabelText(/Usuario/i), { 
      target: { value: 'admin' } 
    });
    fireEvent.change(screen.getByLabelText(/Contraseña/i), { 
      target: { value: 'password' } 
    });
    
    // Enviar formulario
    fireEvent.click(submitButton);
    
    // Botón debe estar deshabilitado durante carga
    await waitFor(() => {
      expect(submitButton).toBeDisabled();
    });
  });

  test('✅ CRÍTICO: should persist session after successful login', async () => {
    const mockUser = {
      id_empleado: 1,
      usuario: 'admin',
      nombre: 'Admin',
      apellido: 'User',
    };

    (authService.login as jest.Mock).mockResolvedValue({
      access: 'test-token',
      refresh: 'refresh-token',
      empleado: mockUser,
    });

    renderLoginPage();
    
    fireEvent.change(screen.getByLabelText(/Usuario/i), { 
      target: { value: 'admin' } 
    });
    fireEvent.change(screen.getByLabelText(/Contraseña/i), { 
      target: { value: 'password' } 
    });
    fireEvent.click(screen.getByRole('button', { name: /Ingresar/i }));
    
    await waitFor(() => {
      expect(localStorage.getItem('token')).toBe('test-token');
      expect(localStorage.getItem('user')).toContain('admin');
    });
  });
});
