/**
 * Tests para el componente DashboardVentas
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DashboardVentas from './DashboardVentas';
import reportesService from '../../services/reportes.service';
import toast from 'react-hot-toast';

// Mock de servicios
jest.mock('../../services/reportes.service', () => ({
  __esModule: true,
  default: {
    getDashboardVentas: jest.fn(),
  },
}));

jest.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    error: jest.fn(),
  },
}));

const mockDashboard = {
  periodo: 'Últimos 7 días',
  total_ventas: 1500000,
  comparacion_semana_anterior: {
    periodo_actual: 1500000,
    periodo_anterior: 1200000,
    variacion_porcentual: 25.0,
  },
  tendencia: 'crecimiento' as const,
  ventas_por_dia: [
    { fecha: '2026-03-01', total: 150000, cantidad: 20 },
    { fecha: '2026-03-02', total: 200000, cantidad: 25 },
  ],
  ventas_por_metodo_pago: [
    { metodo: 'Efectivo', total: 800000, porcentaje: 53.3 },
    { metodo: 'Tarjeta', total: 700000, porcentaje: 46.7 },
  ],
  productos_mas_vendidos: [
    { producto: 'Empanada', cantidad: 150, total: 75000 },
    { producto: 'Gaseosa', cantidad: 100, total: 50000 },
  ],
};

describe('DashboardVentas Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (reportesService.getDashboardVentas as jest.Mock).mockResolvedValue(mockDashboard);
  });

  test('renderiza correctamente', async () => {
    render(<DashboardVentas />);
    
    await waitFor(() => {
      expect(screen.getByText('Dashboard de Ventas')).toBeInTheDocument();
    });
  });

  test('muestra spinner de carga inicialmente', () => {
    render(<DashboardVentas />);
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  test('carga y muestra dashboard al montar', async () => {
    render(<DashboardVentas />);
    
    await waitFor(() => {
      expect(reportesService.getDashboardVentas).toHaveBeenCalledWith({ dias: 7 });
      expect(screen.getByText('Últimos 7 días')).toBeInTheDocument();
    });
  });

  test('muestra comparación con período anterior', async () => {
    render(<DashboardVentas />);
    
    await waitFor(() => {
      expect(screen.getByText('Período Actual')).toBeInTheDocument();
      expect(screen.getByText('Período Anterior')).toBeInTheDocument();
      expect(screen.getByText('Variación')).toBeInTheDocument();
    });
  });

  test('muestra variación porcentual correctamente', async () => {
    render(<DashboardVentas />);
    
    await waitFor(() => {
      const variacion = screen.getByText(/\+25\.0%/);
      expect(variacion).toBeInTheDocument();
    });
  });

  test('muestra icono de crecimiento para tendencia positiva', async () => {
    render(<DashboardVentas />);
    
    await waitFor(() => {
      const variacion = screen.getByText(/\+25\.0%/);
      const parent = variacion.closest('div');
      expect(parent).toHaveClass('text-green-600');
    });
  });

  test('muestra icono de decrecimiento para tendencia negativa', async () => {
    const mockDecrecimiento = {
      ...mockDashboard,
      tendencia: 'decrecimiento' as const,
      comparacion_semana_anterior: {
        periodo_actual: 1000000,
        periodo_anterior: 1500000,
        variacion_porcentual: -33.3,
      },
    };
    (reportesService.getDashboardVentas as jest.Mock).mockResolvedValue(mockDecrecimiento);

    render(<DashboardVentas />);
    
    await waitFor(() => {
      const variacion = screen.getByText(/-33\.3%/);
      const parent = variacion.closest('div');
      expect(parent).toHaveClass('text-red-600');
    });
  });

  test('permite cambiar período seleccionado', async () => {
    const user = userEvent.setup();
    render(<DashboardVentas />);
    
    await waitFor(() => {
      expect(reportesService.getDashboardVentas).toHaveBeenCalledWith({ dias: 7 });
    });

    const select = screen.getByRole('combobox');
    await user.selectOptions(select, '30');

    await waitFor(() => {
      expect(reportesService.getDashboardVentas).toHaveBeenCalledWith({ dias: 30 });
    });
  });

  test('renderiza opciones de período correctamente', async () => {
    render(<DashboardVentas />);
    
    await waitFor(() => {
      const select = screen.getByRole('combobox');
      expect(select).toBeInTheDocument();
    });

    expect(screen.getByRole('option', { name: 'Últimos 7 días' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Últimos 15 días' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Últimos 30 días' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Últimos 90 días' })).toBeInTheDocument();
  });

  test('maneja error al cargar dashboard', async () => {
    (reportesService.getDashboardVentas as jest.Mock).mockRejectedValue(
      new Error('Error de red')
    );

    render(<DashboardVentas />);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Error al cargar el dashboard');
    });
  });

  test('muestra mensaje cuando no hay datos', async () => {
    (reportesService.getDashboardVentas as jest.Mock).mockResolvedValue(null);

    render(<DashboardVentas />);

    await waitFor(() => {
      expect(screen.getByText('No hay datos disponibles')).toBeInTheDocument();
    });
  });

  test('muestra título de ventas por día', async () => {
    render(<DashboardVentas />);
    
    await waitFor(() => {
      expect(screen.getByText('Ventas por Día')).toBeInTheDocument();
    });
  });

  test('formatea montos en guaraníes correctamente', async () => {
    render(<DashboardVentas />);
    
    await waitFor(() => {
      // Verifica formato de moneda paraguaya (1.500.000 → ₲ 1.500.000)
      const montoActual = screen.getByText(/1\.500\.000/);
      expect(montoActual).toBeInTheDocument();
    });
  });
});
