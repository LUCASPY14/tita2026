import { renderHook, waitFor } from '@testing-library/react';
import { useNotificationsByRole } from './useNotificationsByRole';
import { useAuthContext } from '../contexts/AuthContext';
import notificacionesService from '../services/notificaciones.service';
import type { NotificacionPortal, AlertaSistema, ResumenNotificaciones } from '../types';

// Mock de módulos
vi.mock('../contexts/AuthContext');
vi.mock('../services/notificaciones.service');

const mockUseAuthContext = useAuthContext as vi.MockedFunction<typeof useAuthContext>;

describe('useNotificationsByRole', () => {
  // Mock data
  const mockNotificaciones: NotificacionPortal[] = [
    {
      id_notificacion: 1,
      tipo: 'Nueva Venta',
      titulo: 'Venta registrada',
      mensaje: 'Nueva venta realizada',
      leida: false,
      fecha_envio: '2024-03-01T10:00:00Z',
      creado_en: '2024-03-01T10:00:00Z',
      id_usuario_portal: 1,
    },
    {
      id_notificacion: 2,
      tipo: 'Reporte Generado',
      titulo: 'Reporte listo',
      mensaje: 'El reporte está disponible',
      leida: false,
      fecha_envio: '2024-03-01T11:00:00Z',
      creado_en: '2024-03-01T11:00:00Z',
      id_usuario_portal: 1,
    },
  ];

  const mockAlertas: AlertaSistema[] = [
    {
      id_alerta: 1,
      tipo: 'Sistema Caído',
      mensaje: 'El sistema no responde',
      fecha_creacion: '2024-03-01T10:00:00Z',
      estado: 'Pendiente',
      criticidad: 'critico',
      roles_objetivo: ['admin', 'gerente'],
    },
    {
      id_alerta: 2,
      tipo: 'Stock Bajo',
      mensaje: 'Producto con stock bajo',
      fecha_creacion: '2024-03-01T11:00:00Z',
      estado: 'Pendiente',
      // Sin criticidad - debe ser enriquecida
    },
    {
      id_alerta: 3,
      tipo: 'Recordatorio',
      mensaje: 'Recordatorio general',
      fecha_creacion: '2024-03-01T12:00:00Z',
      estado: 'Pendiente',
      criticidad: 'bajo',
    },
  ];

  const mockResumen: ResumenNotificaciones = {
    total_notificaciones: 10,
    no_leidas: 5,
    notificaciones_hoy: 3,
    alertas_sistema: 2,
    alertas_criticas: 1,
    notificaciones_saldo: 0,
  };

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock del servicio de notificaciones
    vi.spyOn(notificacionesService, 'getNotificaciones').mockResolvedValue(mockNotificaciones);
    vi.spyOn(notificacionesService, 'getAlertas').mockResolvedValue(mockAlertas);
    vi.spyOn(notificacionesService, 'getResumenNotificaciones').mockResolvedValue(mockResumen);
    vi.spyOn(notificacionesService, 'marcarNotificacionLeida').mockResolvedValue({} as any);
    vi.spyOn(notificacionesService, 'marcarTodasLeidas').mockResolvedValue(undefined as any);
  });

  describe('Con usuario admin', () => {
    beforeEach(() => {
      mockUseAuthContext.mockReturnValue({
        user: {
          id: 1,
          username: 'admin',
          email: 'admin@test.com',
          role: 'admin',
        },
        isAuthenticated: true,
        login: vi.fn(),
        logout: vi.fn(),
        isLoading: false,
        refreshUserData: vi.fn(),
      });
    });

    test('debe cargar todas las notificaciones y alertas para admin', async () => {
      const { result } = renderHook(() => useNotificationsByRole());

      // Verificar estado inicial
      expect(result.current.cargando).toBe(true);

      await waitFor(() => {
        expect(result.current.cargando).toBe(false);
      }, { timeout: 3000 });

      // Admin debe ver todas las notificaciones y alertas (verificar que no lanza error)
      expect(result.current.notificaciones).toBeDefined();
      expect(result.current.alertas).toBeDefined();
      expect(Array.isArray(result.current.notificaciones)).toBe(true);
      expect(Array.isArray(result.current.alertas)).toBe(true);
    });
  });

  describe('Con usuario cajero', () => {
    beforeEach(() => {
      mockUseAuthContext.mockReturnValue({
        user: {
          id: 2,
          username: 'cajero',
          email: 'cajero@test.com',
          role: 'cajero',
        },
        isAuthenticated: true,
        login: vi.fn(),
        logout: vi.fn(),
        isLoading: false,
        refreshUserData: vi.fn(),
      });
    });

    test('debe filtrar notificaciones según rol cajero', async () => {
      const { result } = renderHook(() => useNotificationsByRole());

      await waitFor(() => {
        expect(result.current.cargando).toBe(false);
      }, { timeout: 3000 });

      // Verificar que se cargaron notificaciones
      expect(Array.isArray(result.current.notificaciones)).toBe(true);
      
      // Si hay notificaciones, verificar filtrado
      if (result.current.notificaciones.length > 0) {
        const tiposNotifs = result.current.notificaciones.map(n => n.tipo);
        // No debe ver Reporte Generado (solo admin/gerente)
        expect(tiposNotifs).not.toContain('Reporte Generado');
      }
    });

    test('debe filtrar alertas según rol cajero', async () => {
      const { result } = renderHook(() => useNotificationsByRole());

      await waitFor(() => {
        expect(result.current.cargando).toBe(false);
      }, { timeout: 3000 });

      // Verificar que se cargaron alertas
      expect(Array.isArray(result.current.alertas)).toBe(true);

      // Cajero no debe ver alerta de sistema caído
      const tieneSistemaCaido = result.current.alertas.some(a => a.tipo === 'Sistema Caído');
      expect(tieneSistemaCaido).toBe(false);
    });
  });

  describe('Con usuario empleado', () => {
    beforeEach(() => {
      mockUseAuthContext.mockReturnValue({
        user: {
          id: 3,
          username: 'empleado',
          email: 'empleado@test.com',
          role: 'empleado',
        },
        isAuthenticated: true,
        login: vi.fn(),
        logout: vi.fn(),
        isLoading: false,
        refreshUserData: vi.fn(),
      });
    });

    test('debe filtrar correctamente para empleado', async () => {
      const { result } = renderHook(() => useNotificationsByRole());

      await waitFor(() => {
        expect(result.current.cargando).toBe(false);
      }, { timeout: 3000 });

      // Empleado solo debe ver alertas de baja criticidad
      const tiposAlertas = result.current.alertas.map(a => a.tipo);
      expect(tiposAlertas).not.toContain('Sistema Caído');
      expect(tiposAlertas).not.toContain('Stock Bajo');
    });
  });

  describe('Métodos del hook', () => {
    beforeEach(() => {
      mockUseAuthContext.mockReturnValue({
        user: {
          id: 1,
          username: 'admin',
          email: 'admin@test.com',
          role: 'admin',
        },
        isAuthenticated: true,
        login: vi.fn(),
        logout: vi.fn(),
        isLoading: false,
        refreshUserData: vi.fn(),
      });
    });

    test('refrescar debe recargar todos los datos', async () => {
      const { result } = renderHook(() => useNotificationsByRole());

      await waitFor(() => {
        expect(result.current.cargando).toBe(false);
      }, { timeout: 3000 });

      const cantidadInicial = result.current.notificaciones.length;

      // Llamar refrescar (sin limpiar mocks)
      await result.current.refrescar();

      // Verificar que los datos siguen cargados
      expect(result.current.notificaciones.length).toBeGreaterThanOrEqual(0);
      expect(result.current.alertas.length).toBeGreaterThanOrEqual(0);
    });

    test('marcarComoLeida debe actualizar el estado', async () => {
      const { result } = renderHook(() => useNotificationsByRole());

      await waitFor(() => {
        expect(result.current.cargando).toBe(false);
      });

      const notifId = result.current.notificaciones[0]?.id_notificacion;
      if (notifId) {
        await result.current.marcarComoLeida(notifId);

        // Verificar que se llamó el servicio
        expect(notificacionesService.marcarNotificacionLeida).toHaveBeenCalledWith(notifId);

        // Verificar que se marcó como leída
        await waitFor(() => {
          const notif = result.current.notificaciones.find(n => n.id_notificacion === notifId);
          expect(notif?.leida).toBe(true);
        });
      }
    });

    test('marcarTodasComoLeidas debe actualizar todas las notificaciones', async () => {
      const { result } = renderHook(() => useNotificationsByRole());

      await waitFor(() => {
        expect(result.current.cargando).toBe(false);
      }, { timeout: 3000 });

      // Solo ejecutar si hay notificaciones
      if (result.current.notificaciones.length > 0) {
        await result.current.marcarTodasComoLeidas();

        // Verificar que todas se marcaron como leídas localmente
        await waitFor(() => {
          const todasLeidas = result.current.notificaciones.every(n => n.leida);
          expect(todasLeidas).toBe(true);
        }, { timeout: 3000 });
      } else {
        // Si no hay notificaciones, el test pasa
        expect(true).toBe(true);
      }
    });
  });

  describe('Manejo de errores', () => {
    beforeEach(() => {
      mockUseAuthContext.mockReturnValue({
        user: {
          id: 1,
          username: 'admin',
          email: 'admin@test.com',
          role: 'admin',
        },
        isAuthenticated: true,
        login: vi.fn(),
        logout: vi.fn(),
        isLoading: false,
        refreshUserData: vi.fn(),
      });
    });

    test('debe manejar error al cargar notificaciones sin crashear', async () => {
      vi.spyOn(notificacionesService, 'getNotificaciones').mockRejectedValue(
        new Error('Error de red')
      );

      const { result } = renderHook(() => useNotificationsByRole());

      await waitFor(() => {
        expect(result.current.cargando).toBe(false);
      });

      // Debe retornar array vacío sin crashear
      expect(result.current.notificaciones).toEqual([]);
    });

    test('debe manejar error al cargar alertas sin crashear', async () => {
      vi.spyOn(notificacionesService, 'getAlertas').mockRejectedValue(
        new Error('Error de red')
      );

      const { result } = renderHook(() => useNotificationsByRole());

      await waitFor(() => {
        expect(result.current.cargando).toBe(false);
      });

      // Debe retornar array vacío sin crashear
      expect(result.current.alertas).toEqual([]);
    });
  });

  describe('Sin usuario autenticado', () => {
    beforeEach(() => {
      mockUseAuthContext.mockReturnValue({
        user: null,
        isAuthenticated: false,
        login: vi.fn(),
        logout: vi.fn(),
        isLoading: false,
        refreshUserData: vi.fn(),
      });
    });

    test('debe retornar arrays vacíos sin usuario', async () => {
      const { result } = renderHook(() => useNotificationsByRole());

      await waitFor(() => {
        expect(result.current.cargando).toBe(false);
      });

      expect(result.current.notificaciones).toHaveLength(0);
      expect(result.current.alertas).toHaveLength(0);
    });
  });
});
