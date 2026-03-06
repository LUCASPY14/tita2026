/**
 * Tests para notificaciones.service.ts
 */
import api from './api';
import {
  getNotificaciones,
  getNotificacionById,
  marcarNotificacionLeida,
  marcarTodasLeidas,
  getResumenNotificaciones,
  formatearFecha,
  calcularTiempoTranscurrido,
  getIconoTipo,
  getColorTipo,
  getColorCriticidad
} from './notificaciones.service';

jest.mock('./api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('Notificaciones Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('API Functions', () => {
    test('getNotificaciones obtiene lista de notificaciones', async () => {
      const mockResponse = {
        data: [
          {
            id_notificacion: 1,
            tipo: 'info',
            titulo: 'Test',
            mensaje: 'Mensaje test',
            leida: 0
          }
        ]
      };

      mockedApi.get.mockResolvedValue(mockResponse);

      const result = await getNotificaciones({ leida: false });

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/notificaciones-portal/'),
        expect.objectContaining({
          params: { leida: false }
        })
      );
      expect(result).toHaveLength(1);
      expect(result[0].titulo).toBe('Test');
      expect(result[0].leida).toBe(false);
    });

    test('getNotificacionById obtiene notificación específica', async () => {
      const mockNotificacion = {
        id_notificacion: 1,
        tipo: 'info',
        titulo: 'Notificación Test',
        mensaje: 'Mensaje de prueba'
      };

      mockedApi.get.mockResolvedValue({ data: mockNotificacion });

      const result = await getNotificacionById(1);

      expect(mockedApi.get).toHaveBeenCalledWith('/notificaciones-portal/1/');
      expect(result.titulo).toBe('Notificación Test');
    });

    test('marcarNotificacionLeida marca como leída', async () => {
      const mockResponse = {
        data: {
          id_notificacion: 1,
          leida: 1,
          fecha_lectura: '2026-03-03T10:00:00Z'
        }
      };

      mockedApi.post.mockResolvedValue(mockResponse);

      const result = await marcarNotificacionLeida(1);

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/notificaciones-portal/1/marcar_leida/'
      );
      expect(result.leida).toBe(true);
    });

    test('marcarTodasLeidas marca todas como leídas', async () => {
      mockedApi.post.mockResolvedValue({ data: undefined });

      await marcarTodasLeidas(1);

      expect(mockedApi.post).toHaveBeenCalledWith(
        expect.stringContaining('/notificaciones-portal/marcar_todas_leidas/'),
        { id_usuario_portal: 1 }
      );
    });

    test('getResumenNotificaciones obtiene resumen', async () => {
      const mockResumen = {
        total_notificaciones: 10,
        no_leidas: 3,
        notificaciones_hoy: 5,
        alertas_criticas: 1,
        notificaciones_saldo: 2,
        alertas_sistema: 4
      };

      mockedApi.get.mockResolvedValue({ data: mockResumen });

      const result = await getResumenNotificaciones(1);

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/notificaciones-portal/resumen/'),
        expect.objectContaining({
          params: { id_usuario_portal: 1 }
        })
      );
      expect(result.total_notificaciones).toBe(10);
      expect(result.no_leidas).toBe(3);
    });
  });

  describe('Helper Functions', () => {
    test('formatearFecha formatea fecha correctamente', () => {
      const fecha = '2026-03-03T10:30:00Z';
      const resultado = formatearFecha(fecha);
      
      // El formato exacto puede variar según la configuración local
      expect(resultado).toBeTruthy();
      expect(typeof resultado).toBe('string');
      expect(resultado.length).toBeGreaterThan(0);
    });

    test('calcularTiempoTranscurrido devuelve "Justo ahora" para fecha reciente', () => {
      const ahora = new Date();
      const resultado = calcularTiempoTranscurrido(ahora.toISOString());
      
      expect(resultado).toBe('Justo ahora');
    });

    test('calcularTiempoTranscurrido devuelve minutos para fechas recientes', () => {
      const hace5min = new Date(Date.now() - 5 * 60 * 1000);
      const resultado = calcularTiempoTranscurrido(hace5min.toISOString());
      
      expect(resultado).toBe('Hace 5 minutos');
    });

    test('calcularTiempoTranscurrido devuelve horas', () => {
      const hace3horas = new Date(Date.now() - 3 * 60 * 60 * 1000);
      const resultado = calcularTiempoTranscurrido(hace3horas.toISOString());
      
      expect(resultado).toBe('Hace 3 horas');
    });

    test('calcularTiempoTranscurrido devuelve días', () => {
      const hace2dias = new Date(Date.now() - 2 * 24 * 60 * 60 * 1000);
      const resultado = calcularTiempoTranscurrido(hace2dias.toISOString());
      
      expect(resultado).toBe('Hace 2 días');
    });

    test('getIconoTipo devuelve icono correcto para cada tipo', () => {
      expect(getIconoTipo('saldo_bajo')).toBe('AlertTriangle');
      expect(getIconoTipo('recarga_exitosa')).toBe('CheckCircle');
      expect(getIconoTipo('consumo')).toBe('ShoppingCart');
      expect(getIconoTipo('almuerzo')).toBe('Utensils');
      expect(getIconoTipo('sistema')).toBe('Bell');
      expect(getIconoTipo('seguridad')).toBe('Shield');
      expect(getIconoTipo('desconocido')).toBe('Bell'); // Default
    });

    test('getColorTipo devuelve color correcto para cada tipo', () => {
      expect(getColorTipo('saldo_bajo')).toBe('text-yellow-600');
      expect(getColorTipo('recarga_exitosa')).toBe('text-green-600');
      expect(getColorTipo('consumo')).toBe('text-blue-600');
      expect(getColorTipo('almuerzo')).toBe('text-orange-600');
      expect(getColorTipo('sistema')).toBe('text-gray-600');
      expect(getColorTipo('seguridad')).toBe('text-red-600');
      expect(getColorTipo('desconocido')).toBe('text-gray-600'); // Default
    });

    test('getColorCriticidad devuelve color correcto para cada nivel', () => {
      expect(getColorCriticidad('bajo')).toBe('text-blue-600 bg-blue-50');
      expect(getColorCriticidad('medio')).toBe('text-yellow-600 bg-yellow-50');
      expect(getColorCriticidad('alto')).toBe('text-orange-600 bg-orange-50');
      expect(getColorCriticidad('critico')).toBe('text-red-600 bg-red-50');
      expect(getColorCriticidad('desconocido')).toBe('text-gray-600 bg-gray-50'); // Default
    });
  });

  describe('Error Handling', () => {
    test('getNotificaciones maneja errores correctamente', async () => {
      mockedApi.get.mockRejectedValue(new Error('Network Error'));

      await expect(getNotificaciones()).rejects.toThrow('Network Error');
    });

    test('marcarNotificacionLeida maneja errores 404', async () => {
      const error = {
        response: { status: 404, data: { detail: 'Not found' } }
      };
      mockedApi.post.mockRejectedValue(error);

      await expect(marcarNotificacionLeida(999)).rejects.toEqual(error);
    });
  });
});
