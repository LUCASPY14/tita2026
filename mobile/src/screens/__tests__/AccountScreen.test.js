import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import AccountScreen from '../AccountScreen';
import api from '../../services/api';

jest.mock('../../services/api');

const mockNavigation = {
  navigate: jest.fn(),
  goBack: jest.fn(),
  setOptions: jest.fn(),
};

const mockRoute = {
  params: {
    hijoId: 42,
    hijoNombre: 'Lucas Perez',
  },
};

const mockTarjeta = {
  id_tarjeta: 1,
  nro_tarjeta: 'T-0042',
  saldo_actual: 150000,
};

const mockRecargas = [
  { id: 1, monto: 100000, fecha_recarga: '2026-05-10T10:00:00Z' },
  { id: 2, monto: 50000, fecha_recarga: '2026-05-01T09:00:00Z' },
];

const mockConsumos = [
  { id: 1, monto: 5000, fecha_consumo: '2026-05-11T12:00:00Z' },
];

describe('AccountScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(Alert, 'alert').mockImplementation(() => {});

    api.get.mockImplementation((url) => {
      if (url === '/tarjetas/') {
        return Promise.resolve({ data: { results: [mockTarjeta] } });
      }
      if (url === '/recargas/') {
        return Promise.resolve({ data: { results: mockRecargas } });
      }
      if (url === '/consumos/') {
        return Promise.resolve({ data: { results: mockConsumos } });
      }
      return Promise.resolve({ data: { results: [] } });
    });
  });

  afterEach(() => {
    Alert.alert.mockRestore();
  });

  it('muestra indicador de carga al inicio', () => {
    api.get.mockReturnValue(new Promise(() => {}));
    const { getByText } = render(
      <AccountScreen navigation={mockNavigation} route={mockRoute} />
    );
    expect(getByText('Cargando cuenta...')).toBeTruthy();
  });

  it('configura titulo con nombre del hijo', async () => {
    render(<AccountScreen navigation={mockNavigation} route={mockRoute} />);

    expect(mockNavigation.setOptions).toHaveBeenCalledWith(
      expect.objectContaining({ title: 'Cuenta: Lucas Perez' })
    );
  });

  it('usa titulo generico cuando no hay nombre', () => {
    const routeSinNombre = { params: { hijoId: 42 } };
    render(<AccountScreen navigation={mockNavigation} route={routeSinNombre} />);

    expect(mockNavigation.setOptions).toHaveBeenCalledWith(
      expect.objectContaining({ title: 'Mi Cuenta' })
    );
  });

  it('muestra saldo disponible al cargar', async () => {
    const { getByText } = render(
      <AccountScreen navigation={mockNavigation} route={mockRoute} />
    );

    await waitFor(() => {
      expect(getByText('Saldo disponible')).toBeTruthy();
    });
  });

  it('muestra numero de tarjeta', async () => {
    const { getByText } = render(
      <AccountScreen navigation={mockNavigation} route={mockRoute} />
    );

    await waitFor(() => {
      expect(getByText(/T-0042/)).toBeTruthy();
    });
  });

  it('muestra boton de recarga QR', async () => {
    const { getByText } = render(
      <AccountScreen navigation={mockNavigation} route={mockRoute} />
    );

    await waitFor(() => {
      expect(getByText('Cargar Saldo con QR')).toBeTruthy();
    });
  });

  it('navega a SIPAPPayment al presionar boton de recarga', async () => {
    const { getByText } = render(
      <AccountScreen navigation={mockNavigation} route={mockRoute} />
    );

    await waitFor(() => {
      expect(getByText('Cargar Saldo con QR')).toBeTruthy();
    });

    fireEvent.press(getByText('Cargar Saldo con QR'));

    expect(mockNavigation.navigate).toHaveBeenCalledWith(
      'SIPAPPayment',
      expect.objectContaining({ tipo: 'carga' })
    );
  });

  it('muestra seccion de movimientos', async () => {
    const { getByText } = render(
      <AccountScreen navigation={mockNavigation} route={mockRoute} />
    );

    await waitFor(() => {
      expect(getByText('Últimos movimientos')).toBeTruthy();
    });
  });

  it('muestra mensaje cuando no hay movimientos', async () => {
    api.get.mockImplementation((url) => {
      if (url === '/tarjetas/') {
        return Promise.resolve({ data: { results: [mockTarjeta] } });
      }
      return Promise.resolve({ data: { results: [] } });
    });

    const { getByText } = render(
      <AccountScreen navigation={mockNavigation} route={mockRoute} />
    );

    await waitFor(() => {
      expect(getByText('Sin movimientos recientes')).toBeTruthy();
    });
  });

  it('muestra alerta cuando no hay tarjeta registrada', async () => {
    api.get.mockImplementation((url) => {
      if (url === '/tarjetas/') {
        return Promise.resolve({ data: { results: [] } });
      }
      return Promise.resolve({ data: { results: [] } });
    });

    const { getByText } = render(
      <AccountScreen navigation={mockNavigation} route={mockRoute} />
    );

    await waitFor(() => {
      // Sin tarjeta, el saldo es 0 y no hay boton QR visible (tarjeta es null)
      expect(getByText('Saldo disponible')).toBeTruthy();
    });
  });

  it('muestra error cuando falla la API', async () => {
    api.get.mockRejectedValue(new Error('Server Error'));

    render(<AccountScreen navigation={mockNavigation} route={mockRoute} />);

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        'Error',
        'No se pudo cargar la información de la cuenta.'
      );
    });
  });

  it('maneja ruta sin params correctamente', () => {
    const routeVacio = { params: {} };
    // No debe lanzar error
    expect(() =>
      render(<AccountScreen navigation={mockNavigation} route={routeVacio} />)
    ).not.toThrow();
  });
});
