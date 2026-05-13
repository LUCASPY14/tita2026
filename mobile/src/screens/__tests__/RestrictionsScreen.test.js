import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Alert, TouchableOpacity } from 'react-native';
import RestrictionsScreen from '../RestrictionsScreen';
import api from '../../services/api';

jest.mock('../../services/api');

// @expo/vector-icons no siempre está disponible en CI
jest.mock('@expo/vector-icons', () => ({
  MaterialIcons: 'MaterialIcons',
  FontAwesome5: 'FontAwesome5',
}));

const mockNavigation = {
  navigate: jest.fn(),
  goBack: jest.fn(),
  setOptions: jest.fn(),
};

const mockRoute = {
  params: {
    hijoId: 10,
    hijoNombre: 'Tomas Garcia',
  },
};

const mockRestricciones = [
  {
    id_restriccion: 1,
    tipo: 'alergia',
    descripcion: 'Alergia al mani',
    severidad: 'alta',
    observaciones: 'Llevar epipen',
    fecha_registro: '2026-01-01',
    estado: true,
  },
  {
    id_restriccion: 2,
    tipo: 'intolerancia',
    descripcion: 'Intolerancia a la lactosa',
    severidad: 'media',
    observaciones: '',
    fecha_registro: '2026-03-01',
    estado: true,
  },
];

describe('RestrictionsScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(Alert, 'alert').mockImplementation(() => {});
    api.get.mockResolvedValue({
      data: { restricciones: mockRestricciones },
    });
  });

  afterEach(() => {
    Alert.alert.mockRestore();
  });

  it('muestra indicador de carga al inicio', () => {
    api.get.mockReturnValue(new Promise(() => {}));
    const { getByTestId, UNSAFE_getByType } = render(
      <RestrictionsScreen navigation={mockNavigation} route={mockRoute} />
    );
    // La pantalla carga inicialmente
    const { queryByText } = render(
      <RestrictionsScreen navigation={mockNavigation} route={mockRoute} />
    );
    // En estado loading no se muestran restricciones
    expect(queryByText('Alergia al mani')).toBeNull();
  });

  it('muestra restricciones cuando la API responde', async () => {
    const { getByText } = render(
      <RestrictionsScreen navigation={mockNavigation} route={mockRoute} />
    );

    await waitFor(() => {
      expect(getByText('Alergia al mani')).toBeTruthy();
      expect(getByText('Intolerancia a la lactosa')).toBeTruthy();
    });
  });

  it('muestra descripcion de cada restriccion', async () => {
    const { getByText } = render(
      <RestrictionsScreen navigation={mockNavigation} route={mockRoute} />
    );

    await waitFor(() => {
      expect(getByText('Alergia al mani')).toBeTruthy();
    });
  });

  it('muestra mensaje vacio cuando no hay restricciones', async () => {
    api.get.mockResolvedValue({ data: { restricciones: [] } });

    const { getByText } = render(
      <RestrictionsScreen navigation={mockNavigation} route={mockRoute} />
    );

    await waitFor(() => {
      expect(getByText('Sin restricciones registradas')).toBeTruthy();
    });
  });

  it('muestra error cuando falla la API', async () => {
    api.get.mockRejectedValue(new Error('Network Error'));

    render(<RestrictionsScreen navigation={mockNavigation} route={mockRoute} />);

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalledWith(
        'Error',
        'No se pudieron cargar las restricciones'
      );
    });
  });

  it('llama a api con el ID del hijo correcto', async () => {
    render(<RestrictionsScreen navigation={mockNavigation} route={mockRoute} />);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/hijos/10/');
    });
  });

  it('muestra dialogo de confirmacion al intentar eliminar', async () => {
    api.delete.mockResolvedValue({});

    const { getByText, UNSAFE_getAllByType } = render(
      <RestrictionsScreen navigation={mockNavigation} route={mockRoute} />
    );

    await waitFor(() => {
      expect(getByText('Alergia al mani')).toBeTruthy();
    });

    // Botones TouchableOpacity: 0=back, 1=addHeader, 2=edit1, 3=delete1, 4=edit2, 5=delete2, 6=FAB
    const touchables = UNSAFE_getAllByType(TouchableOpacity);
    fireEvent.press(touchables[3]);

    await waitFor(() => {
      expect(Alert.alert).toHaveBeenCalled();
    });
  });

  it('navega a AddRestriction al presionar boton agregar', async () => {
    api.get.mockResolvedValue({ data: { restricciones: [] } });

    const { getByText } = render(
      <RestrictionsScreen navigation={mockNavigation} route={mockRoute} />
    );

    await waitFor(() => {
      expect(getByText('Agregar primera restricción')).toBeTruthy();
    });

    fireEvent.press(getByText('Agregar primera restricción'));
    expect(mockNavigation.navigate).toHaveBeenCalledWith(
      'AddRestriction',
      expect.objectContaining({ hijoId: 10 })
    );
  });

  it('maneja restricciones sin observaciones', async () => {
    const sinObservaciones = [
      { ...mockRestricciones[0], observaciones: null },
    ];
    api.get.mockResolvedValue({ data: { restricciones: sinObservaciones } });

    const { getByText } = render(
      <RestrictionsScreen navigation={mockNavigation} route={mockRoute} />
    );

    await waitFor(() => {
      expect(getByText('Alergia al mani')).toBeTruthy();
    });
  });
});
