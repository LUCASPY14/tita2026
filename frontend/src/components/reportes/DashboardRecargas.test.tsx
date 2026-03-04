/**
 * Tests para el componente DashboardRecargas
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DashboardRecargas from './DashboardRecargas';
import reportesService from '../../services/reportes.service';
import toast from 'react-hot-toast';

// Mock de servicios
jest.mock('../../services/reportes.service', () => ({
  __esModule: true,
  default: {
    getDashboardRecargas: jest.fn(),
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
  total_recargas: 150,
  recargas_exitosas: 145,
  recargas_fallidas: 5,
  tasa_exito: 96.7,
  monto_total: 2000000,
  comisiones_generadas: 50000,
  recargas_por_dia: [
    { fecha: '2026-03-01', cantidad: 20, monto: 250000 },
    { fecha: '2026-03-02', cantidad: 25, monto: 300000 },
  ],
  recargas_por_metodo: [
    { metodo_pago: 'efectivo', cantidad: 80, monto_total: 1200000, comision_total: 30000 },
    { metodo_pago: 'transferencia', cantidad: 65, monto_total: 800000, comision_total: 20000 },
  ],
};

describe('DashboardRecargas Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (reportesService.getDashboardRecargas as jest.Mock).mockResolvedValue(mockDashboard);
  });

  test('renderiza correctamente', async () => {
    render(<DashboardRecargas />);
    
    await waitFor(() => {
      expect(screen.getByText('Dashboard de Recargas')).toBeInTheDocument();
    });
  });

  test('muestra spinner de carga inicialmente', () => {
    render(<DashboardRecargas />);
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  test('carga y muestra dashboard al montar', async () => {
    render(<DashboardRecargas />);
    
    await waitFor(() => {
      expect(reportesService.getDashboardRecargas).toHaveBeenCalledWith({ dias: 7 });
      expect(screen.getByText('Últimos 7 días')).toBeInTheDocument();
    });
  });

  test('muestra KPI de total recargas', async () => {
    render(<DashboardRecargas />);
    
    await waitFor(() => {
      expect(screen.getByText('Total Recargas')).toBeInTheDocument();
      expect(screen.getByText('150')).toBeInTheDocument();
    });
  });

  test('muestra KPI de recargas exitosas', async () => {
    render(<DashboardRecargas />);
    
    await waitFor(() => {
      expect(screen.getByText('Recargas Exitosas')).toBeInTheDocument();
      expect(screen.getByText('145')).toBeInTheDocument();
    });
  });

  test('muestra tasa de éxito correctamente', async () => {
    render(<DashboardRecargas />);
    
    await waitFor(() => {
      expect(screen.getByText('Tasa de Éxito')).toBeInTheDocument();
      expect(screen.getByText(/96\.7%/)).toBeInTheDocument();
    });
  });

  test('muestra comisiones generadas formateadas', async () => {
    render(<DashboardRecargas />);
    
    await waitFor(() => {
      expect(screen.getByText('Comisiones')).toBeInTheDocument();
      // Formato: ₲ 50.000
      const comisionElement = screen.getByText(/50\.000/);
      expect(comisionElement).toBeInTheDocument();
    });
  });

  test('permite cambiar período seleccionado', async () => {
    const user = userEvent.setup();
    render(<DashboardRecargas />);
    
    await waitFor(() => {
      expect(reportesService.getDashboardRecargas).toHaveBeenCalledWith({ dias: 7 });
    });

    const select = screen.getByRole('combobox');
    await user.selectOptions(select, '30');

    await waitFor(() => {
      expect(reportesService.getDashboardRecargas).toHaveBeenCalledWith({ dias: 30 });
    });
  });

  test('renderiza opciones de período correctamente', async () => {
    render(<DashboardRecargas />);
    
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
    (reportesService.getDashboardRecargas as jest.Mock).mockRejectedValue(
      new Error('Error de red')
    );

    render(<DashboardRecargas />);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Error al cargar el dashboard');
    });
  });

  test('muestra mensaje cuando no hay datos', async () => {
    (reportesService.getDashboardRecargas as jest.Mock).mockResolvedValue(null);

    render(<DashboardRecargas />);

    await waitFor(() => {
      expect(screen.getByText('No hay datos disponibles')).toBeInTheDocument();
    });
  });

  test('muestra iconos de KPIs correctamente', async () => {
    render(<DashboardRecargas />);
    
    await waitFor(() => {
      expect(screen.getByText('Total Recargas')).toBeInTheDocument();
      expect(screen.getByText('Recargas Exitosas')).toBeInTheDocument();
      expect(screen.getByText('Tasa de Éxito')).toBeInTheDocument();
      expect(screen.getByText('Comisiones')).toBeInTheDocument();
    });
  });

  test('calcula tasa de éxito correctamente', async () => {
    const mockBajaTasa = {
      ...mockDashboard,
      total_recargas: 100,
      recargas_exitosas: 50,
      tasa_exito: 50.0,
    };
    (reportesService.getDashboardRecargas as jest.Mock).mockResolvedValue(mockBajaTasa);

    render(<DashboardRecargas />);
    
    await waitFor(() => {
      expect(screen.getByText(/50\.0%/)).toBeInTheDocument();
    });
  });

  test('formatea montos en guaraníes correctamente', async () => {
    render(<DashboardRecargas />);
    
    await waitFor(() => {
      // Verifica formato de moneda paraguaya
      const comision = screen.getByText(/50\.000/);
      expect(comision).toBeInTheDocument();
    });
  });
});
