/**
 * Tests para el componente DashboardKPIs
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DashboardKPIs from './DashboardKPIs';
import reportesService from '../../services/reportes.service';
import toast from 'react-hot-toast';

// Mock de servicios
jest.mock('../../services/reportes.service', () => ({
  __esModule: true,
  default: {
    getKPIsPrincipales: jest.fn(),
  },
}));

jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    error: jest.fn(),
  },
}));

const mockKPIs = {
  ventas_del_dia: 150000,
  cantidad_ventas: 25,
  ticket_promedio: 6000,
  recargas_del_dia: 200000,
  cantidad_recargas: 15,
  saldo_total_tarjetas: 500000,
  tarjetas_activas: 120,
  productos_stock_critico: 3,
};

describe('DashboardKPIs Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (reportesService.getKPIsPrincipales as jest.Mock).mockResolvedValue(mockKPIs);
  });

  test('renderiza correctamente', async () => {
    render(<DashboardKPIs />);
    
    await waitFor(() => {
      expect(screen.getByText('KPIs del Día')).toBeInTheDocument();
    });
  });

  test('muestra spinner de carga inicialmente', () => {
    render(<DashboardKPIs />);
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  test('carga y muestra KPIs al montar', async () => {
    render(<DashboardKPIs />);
    
    await waitFor(() => {
      expect(reportesService.getKPIsPrincipales).toHaveBeenCalled();
      expect(screen.getByText('Ventas del Día')).toBeInTheDocument();
      expect(screen.getByText('Recargas del Día')).toBeInTheDocument();
    });
  });

  test('formatea montos correctamente', async () => {
    render(<DashboardKPIs />);
    
    await waitFor(() => {
      // Verifica que el monto esté formateado (150000 → ₲ 150.000)
      const ventasElement = screen.getByText(/150\.000/);
      expect(ventasElement).toBeInTheDocument();
    });
  });

  test('muestra cantidad de ventas y recargas', async () => {
    render(<DashboardKPIs />);
    
    await waitFor(() => {
      expect(screen.getByText(/25 ventas/)).toBeInTheDocument();
      expect(screen.getByText(/15 recargas/)).toBeInTheDocument();
    });
  });

  test('muestra KPI de tarjetas activas', async () => {
    render(<DashboardKPIs />);
    
    await waitFor(() => {
      expect(screen.getByText('120')).toBeInTheDocument();
    });
  });

  test('muestra productos con stock crítico', async () => {
    render(<DashboardKPIs />);
    
    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument();
    });
  });

  test('permite cambiar fecha seleccionada', async () => {
    const user = userEvent.setup();
    render(<DashboardKPIs />);
    
    await waitFor(() => {
      expect(screen.getByText('Ventas del Día')).toBeInTheDocument();
    });

    const dateInput = screen.getByDisplayValue(/\d{4}-\d{2}-\d{2}/);
    await user.clear(dateInput);
    await user.type(dateInput, '2026-03-01');

    await waitFor(() => {
      expect(reportesService.getKPIsPrincipales).toHaveBeenCalledWith('2026-03-01');
    });
  });

  test('permite actualizar datos con botón refresh', async () => {
    const user = userEvent.setup();
    render(<DashboardKPIs />);
    
    await waitFor(() => {
      expect(reportesService.getKPIsPrincipales).toHaveBeenCalledTimes(1);
    });

    const refreshButton = screen.getByTitle('Actualizar');
    await user.click(refreshButton);

    await waitFor(() => {
      expect(reportesService.getKPIsPrincipales).toHaveBeenCalledTimes(2);
    });
  });

  test('maneja error al cargar KPIs', async () => {
    (reportesService.getKPIsPrincipales as jest.Mock).mockRejectedValue(
      new Error('Error de red')
    );

    render(<DashboardKPIs />);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Error al cargar los KPIs');
    });
  });

  test('muestra mensaje cuando no hay datos', async () => {
    (reportesService.getKPIsPrincipales as jest.Mock).mockResolvedValue(null);

    render(<DashboardKPIs />);

    await waitFor(() => {
      expect(screen.getByText('No hay datos disponibles')).toBeInTheDocument();
    });
  });

  test('formatea ticket promedio correctamente', async () => {
    render(<DashboardKPIs />);
    
    await waitFor(() => {
      expect(screen.getByText('Ticket Promedio')).toBeInTheDocument();
      const ticketElement = screen.getByText(/6\.000/);
      expect(ticketElement).toBeInTheDocument();
    });
  });

  test('muestra iconos de KPIs correctamente', async () => {
    render(<DashboardKPIs />);
    
    await waitFor(() => {
      const ventas = screen.getByText('Ventas del Día');
      expect(ventas).toBeInTheDocument();
      
      const recargas = screen.getByText('Recargas del Día');
      expect(recargas).toBeInTheDocument();
    });
  });
});
