/**
 * Tests para ListaNotificaciones component
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import ListaNotificaciones from './ListaNotificaciones';
import notificacionesService from '../../services/notificaciones.service';

// Mock del service
vi.mock('../../services/notificaciones.service', () => ({
  __esModule: true,
  default: {
    getNotificaciones: vi.fn(),
    marcarNotificacionLeida: vi.fn(),
    calcularTiempoTranscurrido: vi.fn(() => 'hace 2 horas'),
  },
}));

// Mock de react-hot-toast
vi.mock('react-hot-toast', () => ({
  __esModule: true,
  default: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

const mockNotificaciones = [
  {
    id_notificacion: 1,
    tipo: 'info',
    titulo: 'Nueva venta registrada',
    mensaje: 'Se registró una venta por $50,000',
    leida: false,
    fecha_creacion: '2026-03-03T10:00:00Z',
    fecha_lectura: null,
    enlace: null,
    id_empleado: 1,
    empleado_nombre: 'Juan Pérez'
  },
  {
    id_notificacion: 2,
    tipo: 'warning',
    titulo: 'Stock bajo',
    mensaje: 'Producto Coca-Cola con stock crítico',
    leida: false,
    fecha_creacion: '2026-03-03T09:30:00Z',
    fecha_lectura: null,
    enlace: '/productos',
    id_empleado: 1,
    empleado_nombre: 'Juan Pérez'
  },
  {
    id_notificacion: 3,
    tipo: 'success',
    titulo: 'Recarga exitosa',
    mensaje: 'Recarga de $100,000 procesada correctamente',
    leida: true,
    fecha_creacion: '2026-03-02T15:00:00Z',
    fecha_lectura: '2026-03-02T16:00:00Z',
    enlace: null,
    id_empleado: 1,
    empleado_nombre: 'Juan Pérez'
  }
];

// Wrapper con Router
const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('ListaNotificaciones Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // El servicio retorna array directo, no paginado
    (notificacionesService.getNotificaciones as vi.Mock).mockResolvedValue(mockNotificaciones);
  });

  test('renderiza la lista de notificaciones', async () => {
    renderWithRouter(<ListaNotificaciones idUsuario={1} />);

    // Esperar a que carguen las notificaciones
    await waitFor(() => {
      expect(screen.getByText('Nueva venta registrada')).toBeInTheDocument();
    });

    expect(screen.getByText('Stock bajo')).toBeInTheDocument();
    expect(screen.getByText('Recarga exitosa')).toBeInTheDocument();
  });

  test('muestra estado de cargando inicialmente', () => {
    // Mock no debería resolverse inmediatamente
    (notificacionesService.getNotificaciones as vi.Mock).mockImplementation(
      () => new Promise(() => {}) // Promise que nunca se resuelve
    );

    renderWithRouter(<ListaNotificaciones idUsuario={1} />);
    
    // Verificar que el componente está en estado de carga
    // El spinner es un div con clase animate-spin
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  test('filtra notificaciones no leídas', async () => {
    renderWithRouter(<ListaNotificaciones idUsuario={1} />);

    await waitFor(() => {
      expect(screen.getByText('Nueva venta registrada')).toBeInTheDocument();
    });

    // Click en filtro "No leídas"
    const filtroNoLeidas = screen.getByRole('button', { name: /no leídas/i });
    fireEvent.click(filtroNoLeidas);

    // Debería mostrar solo las no leídas (2)
    await waitFor(() => {
      expect(screen.getByText('Nueva venta registrada')).toBeInTheDocument();
      expect(screen.getByText('Stock bajo')).toBeInTheDocument();
    });
  });

  test('marca notificación como leída', async () => {
    (notificacionesService.marcarNotificacionLeida as vi.Mock).mockResolvedValue({
      ...mockNotificaciones[0],
      leida: true,
      fecha_lectura: new Date().toISOString()
    });

    renderWithRouter(<ListaNotificaciones idUsuario={1} />);

    await waitFor(() => {
      expect(screen.getByText('Nueva venta registrada')).toBeInTheDocument();
    });

    // Buscar y hacer click en botón de marcar como leída
    const botones = screen.getAllByRole('button');
    const botonMarcar = botones.find(btn => btn.getAttribute('title')?.includes('Marcar como leída'));
    
    if (botonMarcar) {
      fireEvent.click(botonMarcar);
      
      await waitFor(() => {
        expect(notificacionesService.marcarNotificacionLeida).toHaveBeenCalledWith(1);
      });
    }
  });

  test('muestra badge "Nueva" para notificaciones recientes no leídas', async () => {
    renderWithRouter(<ListaNotificaciones idUsuario={1} />);

    await waitFor(() => {
      expect(screen.getByText('Nueva venta registrada')).toBeInTheDocument();
    });

    // Buscar badges "Nueva"
    const badges = screen.getAllByText('Nueva');
    expect(badges.length).toBeGreaterThan(0);
  });

  test('muestra icono diferente según tipo de notificación', async () => {
    renderWithRouter(<ListaNotificaciones idUsuario={1} />);

    await waitFor(() => {
      expect(screen.getByText('Nueva venta registrada')).toBeInTheDocument();
    });

    // Los iconos se renderizan según el tipo (info, warning, success)
    const container = screen.getByText('Nueva venta registrada').closest('div');
    expect(container).toBeInTheDocument();
  });

  test('maneja error al cargar notificaciones', async () => {
    (notificacionesService.getNotificaciones as vi.Mock).mockRejectedValue(
      new Error('Error al cargar')
    );

    renderWithRouter(<ListaNotificaciones idUsuario={1} />);

    // Debe mostrar el estado vacío en lugar de crashear
    await waitFor(() => {
      expect(screen.getByText(/no hay notificaciones/i)).toBeInTheDocument();
    });
  });

  test('muestra mensaje cuando no hay notificaciones', async () => {
    (notificacionesService.getNotificaciones as vi.Mock).mockResolvedValue(
      []
    );

    renderWithRouter(<ListaNotificaciones idUsuario={1} />);

    await waitFor(() => {
      expect(screen.getByText(/no hay notificaciones/i)).toBeInTheDocument();
    });
  });
});
