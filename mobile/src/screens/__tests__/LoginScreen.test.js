import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import LoginScreen from '../LoginScreen';
import * as authService from '../../services/auth.service';

jest.mock('../../services/auth.service');

describe('LoginScreen', () => {
  const mockNavigation = {
    replace: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(Alert, 'alert').mockImplementation(() => {});
  });

  afterEach(() => {
    Alert.alert.mockRestore();
  });

  it('should render login form', () => {
    const { getByPlaceholderText, getByText } = render(
      <LoginScreen navigation={mockNavigation} />
    );

    expect(getByText('🍽️ Cantina Tita')).toBeTruthy();
    expect(getByText('Iniciá sesión para continuar')).toBeTruthy();
    expect(getByPlaceholderText('Usuario')).toBeTruthy();
    expect(getByPlaceholderText('Contraseña')).toBeTruthy();
    expect(getByText('Ingresar')).toBeTruthy();
  });

  it('should show error when fields are empty', async () => {
    const { getByText } = render(<LoginScreen navigation={mockNavigation} />);

    const loginButton = getByText('Ingresar');
    fireEvent.press(loginButton);

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        'Error',
        'Por favor ingresá tu usuario y contraseña.'
      );
    });
  });

  it('should update username and password inputs', () => {
    const { getByPlaceholderText } = render(
      <LoginScreen navigation={mockNavigation} />
    );

    const usernameInput = getByPlaceholderText('Usuario');
    const passwordInput = getByPlaceholderText('Contraseña');

    fireEvent.changeText(usernameInput, 'testuser');
    fireEvent.changeText(passwordInput, 'password123');

    expect(usernameInput.props.value).toBe('testuser');
    expect(passwordInput.props.value).toBe('password123');
  });

  it('should login successfully and navigate to Menu', async () => {
    authService.login.mockResolvedValue({
      token: 'test-token',
      user: { id: 1, username: 'testuser' },
    });

    const { getByPlaceholderText, getByText } = render(
      <LoginScreen navigation={mockNavigation} />
    );

    const usernameInput = getByPlaceholderText('Usuario');
    const passwordInput = getByPlaceholderText('Contraseña');
    const loginButton = getByText('Ingresar');

    fireEvent.changeText(usernameInput, 'testuser');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.press(loginButton);

    await waitFor(() => {
      expect(authService.login).toHaveBeenCalledWith('testuser', 'password123');
      expect(mockNavigation.replace).toHaveBeenCalledWith('Menu');
    });
  });

  it('should show error message on login failure', async () => {
    const errorMessage = 'Credenciales inválidas';
    authService.login.mockRejectedValue({
      response: {
        data: {
          non_field_errors: [errorMessage],
        },
      },
    });

    const { getByPlaceholderText, getByText } = render(
      <LoginScreen navigation={mockNavigation} />
    );

    const usernameInput = getByPlaceholderText('Usuario');
    const passwordInput = getByPlaceholderText('Contraseña');
    const loginButton = getByText('Ingresar');

    fireEvent.changeText(usernameInput, 'baduser');
    fireEvent.changeText(passwordInput, 'badpass');
    fireEvent.press(loginButton);

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith('Error de acceso', errorMessage);
    });
  });

  it('should show generic error message on network failure', async () => {
    authService.login.mockRejectedValue(new Error('Network Error'));

    const { getByPlaceholderText, getByText } = render(
      <LoginScreen navigation={mockNavigation} />
    );

    const usernameInput = getByPlaceholderText('Usuario');
    const passwordInput = getByPlaceholderText('Contraseña');
    const loginButton = getByText('Ingresar');

    fireEvent.changeText(usernameInput, 'testuser');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.press(loginButton);

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        'Error de acceso',
        'No se pudo conectar con el servidor.'
      );
    });
  });

  it('should disable inputs and button while loading', async () => {
    authService.login.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 1000))
    );

    const { getByPlaceholderText, getByText } = render(
      <LoginScreen navigation={mockNavigation} />
    );

    const usernameInput = getByPlaceholderText('Usuario');
    const passwordInput = getByPlaceholderText('Contraseña');
    const loginButton = getByText('Ingresar');

    fireEvent.changeText(usernameInput, 'testuser');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.press(loginButton);

    // Check that inputs are disabled during loading
    await waitFor(() => {
      expect(usernameInput.props.editable).toBe(false);
      expect(passwordInput.props.editable).toBe(false);
    });
  });

  it('should trim username before submitting', async () => {
    authService.login.mockResolvedValue({
      token: 'test-token',
      user: { id: 1, username: 'testuser' },
    });

    const { getByPlaceholderText, getByText } = render(
      <LoginScreen navigation={mockNavigation} />
    );

    const usernameInput = getByPlaceholderText('Usuario');
    const passwordInput = getByPlaceholderText('Contraseña');
    const loginButton = getByText('Ingresar');

    fireEvent.changeText(usernameInput, '  testuser  ');
    fireEvent.changeText(passwordInput, 'password123');
    fireEvent.press(loginButton);

    await waitFor(() => {
      expect(authService.login).toHaveBeenCalledWith('testuser', 'password123');
    });
  });
});
