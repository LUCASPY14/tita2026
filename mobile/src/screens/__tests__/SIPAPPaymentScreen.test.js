import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert } from 'react-native';
import SIPAPPaymentScreen from '../SIPAPPaymentScreen';
import sipapService from '../../services/sipap.service';

jest.mock('../../services/sipap.service', () => ({
  __esModule: true,
  default: {
    generarQRCargaSaldo: jest.fn(),
    esperarConfirmacion: jest.fn(),
    formatearTiempo: jest.fn((segundos) => `${Math.floor(segundos / 60)}:${(segundos % 60).toString().padStart(2, '0')}`),
    formatearMonto: jest.fn((monto) => `Gs. ${monto.toLocaleString('es-PY')}`),
  },
}));

describe('SIPAPPaymentScreen', () => {
  const mockNavigation = {
    navigate: jest.fn(),
    goBack: jest.fn(),
    setOptions: jest.fn(),
  };

  const mockRoute = {
    params: {
      idCliente: 1,
      tipo: 'carga',
      montoInicial: 50000,
      descripcionInicial: 'Carga de saldo',
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(Alert, 'alert').mockImplementation(() => {});
  });

  afterEach(() => {
    Alert.alert.mockRestore();
  });

  it('should render payment screen', () => {
    const { getByText } = render(
      <SIPAPPaymentScreen navigation={mockNavigation} route={mockRoute} />
    );

    expect(getByText(/Cargar Saldo con QR/i)).toBeTruthy();
    expect(getByText(/Generar QR/i)).toBeTruthy();
  });

  it('should set navigation title based on tipo', () => {
    render(<SIPAPPaymentScreen navigation={mockNavigation} route={mockRoute} />);

    expect(mockNavigation.setOptions).toHaveBeenCalledWith(
      expect.objectContaining({ title: 'Cargar Saldo' })
    );
  });

  it('should initialize with monto from params', () => {
    const { getByDisplayValue } = render(
      <SIPAPPaymentScreen navigation={mockNavigation} route={mockRoute} />
    );

    // El componente muestra el valor sin formato en el input
    expect(getByDisplayValue('50000')).toBeTruthy();
  });

  it('should show error for empty monto on generate', async () => {
    const emptyRoute = {
      params: { idCliente: 1, tipo: 'carga' },
    };

    const { getByText } = render(
      <SIPAPPaymentScreen navigation={mockNavigation} route={emptyRoute} />
    );

    const generateButton = getByText(/Generar QR/i);
    fireEvent.press(generateButton);

    expect(Alert.alert).toHaveBeenCalledWith('Error', 'Ingresa un monto válido');
  });

  it('should show error for monto below minimum', async () => {
    const lowAmountRoute = {
      params: { idCliente: 1, tipo: 'carga', montoInicial: 5000 },
    };

    const { getByText } = render(
      <SIPAPPaymentScreen navigation={mockNavigation} route={lowAmountRoute} />
    );

    const generateButton = getByText(/Generar QR/i);
    fireEvent.press(generateButton);

    expect(Alert.alert).toHaveBeenCalledWith(
      'Error',
      'El monto mínimo es Gs. 10.000'
    );
  });

  it('should call generarQRCargaSaldo when pressing generate with valid monto', async () => {
    const mockQRData = {
      qr_data: {
        txn_id: 'TXN123',
        qr_image_base64: 'data:image/png;base64,test',
        expira_en: 300,
      },
    };

    sipapService.generarQRCargaSaldo.mockResolvedValue(mockQRData);
    sipapService.esperarConfirmacion.mockImplementation(() => new Promise(() => {}));

    const { getByText } = render(
      <SIPAPPaymentScreen navigation={mockNavigation} route={mockRoute} />
    );

    const generateButton = getByText(/Generar QR/i);
    fireEvent.press(generateButton);

    await waitFor(() => {
      expect(sipapService.generarQRCargaSaldo).toHaveBeenCalledWith(
        1,
        50000,
        'Carga de saldo'
      );
    });
  });

  it('should handle QR generation error', async () => {
    sipapService.generarQRCargaSaldo.mockRejectedValue(
      new Error('Error al generar QR')
    );

    const { getByText } = render(
      <SIPAPPaymentScreen navigation={mockNavigation} route={mockRoute} />
    );

    const generateButton = getByText(/Generar QR/i);
    fireEvent.press(generateButton);

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        'Error',
        'Error al generar QR'
      );
    });
  });

  it('should show monto from params', () => {
    const largeAmountRoute = {
      params: {
        idCliente: 1,
        tipo: 'carga',
        montoInicial: 1500000,
      },
    };

    const { getByDisplayValue } = render(
      <SIPAPPaymentScreen navigation={mockNavigation} route={largeAmountRoute} />
    );

    // El componente muestra el valor sin formato en el input
    expect(getByDisplayValue('1500000')).toBeTruthy();
  });
});
