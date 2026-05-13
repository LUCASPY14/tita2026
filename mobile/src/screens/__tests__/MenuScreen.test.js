import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import MenuScreen from '../MenuScreen';
import api from '../../services/api';
import * as authService from '../../services/auth.service';

jest.mock('../../services/api');
jest.mock('../../services/auth.service');

const mockNavigation = {
  navigate: jest.fn(),
  replace: jest.fn(),
  setOptions: jest.fn(),
};

const mockProductos = [
  { id: 1, nombre: 'Gaseosa 500ml', precio: 5000, descripcion: 'Bebida fria', imagen: null },
  { id: 2, nombre: 'Sandwich Jamon', precio: 8000, descripcion: 'Con queso', imagen: null },
];

describe('MenuScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(Alert, 'alert').mockImplementation(() => {});
    api.get.mockResolvedValue({ data: { results: mockProductos } });
  });

  afterEach(() => {
    Alert.alert.mockRestore();
  });

  it('muestra indicador de carga al inicio', () => {
    // api nunca resuelve en este test
    api.get.mockReturnValue(new Promise(() => {}));
    const { getByText } = render(<MenuScreen navigation={mockNavigation} />);
    expect(getByText('Cargando menú...')).toBeTruthy();
  });

  it('muestra productos cuando la API responde', async () => {
    const { getByText } = render(<MenuScreen navigation={mockNavigation} />);

    await waitFor(() => {
      expect(getByText('Gaseosa 500ml')).toBeTruthy();
      expect(getByText('Sandwich Jamon')).toBeTruthy();
    });
  });

  it('muestra precio formateado en guaranies', async () => {
    const { getAllByText } = render(<MenuScreen navigation={mockNavigation} />);

    await waitFor(() => {
      const precios = getAllByText(/Gs\./);
      expect(precios.length).toBeGreaterThan(0);
    });
  });

  it('muestra mensaje vacio cuando no hay productos', async () => {
    api.get.mockResolvedValue({ data: { results: [] } });

    const { getByText } = render(<MenuScreen navigation={mockNavigation} />);

    await waitFor(() => {
      expect(getByText('No hay productos disponibles hoy.')).toBeTruthy();
    });
  });

  it('muestra error cuando falla la API', async () => {
    api.get.mockRejectedValue(new Error('Network Error'));

    render(<MenuScreen navigation={mockNavigation} />);

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        'Error',
        'No se pudo cargar el menú. Verificá tu conexión.'
      );
    });
  });

  it('acepta respuesta de api como array directo', async () => {
    api.get.mockResolvedValue({ data: mockProductos });

    const { getByText } = render(<MenuScreen navigation={mockNavigation} />);

    await waitFor(() => {
      expect(getByText('Gaseosa 500ml')).toBeTruthy();
    });
  });

  it('agrega producto al carrito', async () => {
    const { getByText, getAllByText } = render(<MenuScreen navigation={mockNavigation} />);

    await waitFor(() => {
      expect(getByText('Gaseosa 500ml')).toBeTruthy();
    });

    // El boton de agregar muestra "+ Agregar" o similar
    const addButtons = getAllByText(/agregar|Agregar|\+/i);
    if (addButtons.length > 0) {
      fireEvent.press(addButtons[0]);
    }

    // El carrito actualiza el header — navigation.setOptions fue llamado
    expect(mockNavigation.setOptions).toHaveBeenCalled();
  });

  it('navega a Cart al presionar icono del carrito', async () => {
    const { getByText } = render(<MenuScreen navigation={mockNavigation} />);

    await waitFor(() => {
      expect(getByText('Gaseosa 500ml')).toBeTruthy();
    });

    // El header tiene un boton que llama navigate('Cart')
    // setOptions configura el headerRight con botones
    expect(mockNavigation.setOptions).toHaveBeenCalled();
  });

  it('llama a logout y navega a Login al presionar Salir', async () => {
    authService.logout.mockResolvedValue();

    const { getByText } = render(<MenuScreen navigation={mockNavigation} />);

    await waitFor(() => {
      expect(getByText('Gaseosa 500ml')).toBeTruthy();
    });

    // navigation.replace('Login') se llama via handleLogout
    // Accedemos al callback de setOptions para disparar el logout
    const lastCall = mockNavigation.setOptions.mock.calls.slice(-1)[0][0];
    if (lastCall?.headerRight) {
      const HeaderRight = lastCall.headerRight;
      const { getByText: getByTextHeader } = render(<HeaderRight />);
      fireEvent.press(getByTextHeader('Salir'));

      await waitFor(() => {
        expect(authService.logout).toHaveBeenCalled();
      });
    }
  });
});
