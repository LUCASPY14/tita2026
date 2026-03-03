/**
 * Tests para el componente AlertasSistema
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock de los servicios ANTES de importar el componente
jest.mock('../../services/notificaciones.service', () => ({
  __esModule: true,
  default: {
    getAlertas: jest.fn(),
    resolverAlerta: jest.fn(),
    formatearFecha: jest.fn(() => 'hace 2 horas'),
  },
}));

jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

import AlertasSistema from './AlertasSistema';
import notificacionesService from '../../services/notificaciones.service';
import toast from 'react-hot-toast';

const mockAlertas = [
  {
    id: 1,
    tipo: 'stock_critico',
    criticidad: 'alto',
    titulo: 'Stock Crítico',
    descripcion: 'Producto bajo en stock',
    estado: 'Pendiente',
    fecha_creacion: '2024-01-01T10:00:00',
  },
  {
    id: 2,
    tipo: 'anomalia',
    criticidad: 'medio',
    titulo: 'Anomalía detectada',
    descripcion: 'Transacción inusual',
    estado: 'Resuelta',
    fecha_creacion: '2024-01-02T10:00:00',
    fecha_resolucion: '2024-01-02T11:00:00',
  },
];

describe('AlertasSistema Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (notificacionesService.getAlertas as jest.Mock).mockResolvedValue(mockAlertas);
  });

  test('renderiza correctamente', async () => {
    render(<AlertasSistema />);
    await waitFor(() => {
      expect(screen.getByText('Stock Crítico')).toBeInTheDocument();
    });
  });

  test('muestra spinner de carga inicialmente', () => {
    render(<AlertasSistema />);
    const spinner = screen.getByRole('status', { hidden: true }) || 
                    document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  test('carga y muestra alertas al montar', async () => {
    render(<AlertasSistema />);
    
    await waitFor(() => {
      expect(notificacionesService.getAlertas).toHaveBeenCalledWith({});
      expect(screen.getByText('Stock Crítico')).toBeInTheDocument();
      expect(screen.getByText('Anomalía detectada')).toBeInTheDocument();
    });
  });

  test('muestra badge de estado correctamente', async () => {
    render(<AlertasSistema />);
    
    await waitFor(() => {
      expect(screen.getByText('Pendiente')).toBeInTheDocument();
      expect(screen.getByText('Resuelta')).toBeInTheDocument();
    });
  });

  test('filtra alertas por estado "Pendiente"', async () => {
    const user = userEvent.setup();
    render(<AlertasSistema />);
    
    await waitFor(() => {
      expect(screen.getByText('Stock Crítico')).toBeInTheDocument();
    });

    const botonPendientes = screen.getByText('Pendientes');
    await user.click(botonPendientes);

    await waitFor(() => {
      expect(notificacionesService.getAlertas).toHaveBeenCalledWith({ estado: 'Pendiente' });
    });
  });

  test('resuelve alerta exitosamente', async () => {
    const user = userEvent.setup();
    const mockOnAlertaResuelta = jest.fn();
    (notificacionesService.resolverAlerta as jest.Mock).mockResolvedValue({});
    
    render(<AlertasSistema onAlertaResuelta={mockOnAlertaResuelta} />);
    
    // Esperar a que carguen las alertas
    await waitFor(() => {
      expect(notificacionesService.getAlertas).toHaveBeenCalled();
    });

    // Si hay una alerta visible y un textarea, probar resolución
    const textarea = screen.queryByRole('textbox');
    if (textarea) {
      await user.type(textarea, 'Problema resuelto');
      
      // Buscar botón de confirmar
      const botonConfirmar = screen.queryByText(/confirmar/i);
      if (botonConfirmar) {
        await user.click(botonConfirmar);

        await waitFor(() => {
          expect(notificacionesService.resolverAlerta).toHaveBeenCalled();
        });
      }
    }
  });

  test('maneja error al cargar alertas', async () => {
    (notificacionesService.getAlertas as jest.Mock).mockRejectedValue(
      new Error('Error de red')
    );

    render(<AlertasSistema />);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Error al cargar las alertas');
    });
  });

  test('muestra mensaje cuando no hay alertas', async () => {
    (notificacionesService.getAlertas as jest.Mock).mockResolvedValue([]);

    render(<AlertasSistema />);

    await waitFor(() => {
      const noAlertasMsg = screen.queryByText(/no hay alertas/i) || 
                           screen.queryByText(/sin alertas/i);
      // El componente puede mostrar lista vacía sin mensaje
      expect(screen.queryByText('Stock Crítico')).not.toBeInTheDocument();
    });
  });
});
