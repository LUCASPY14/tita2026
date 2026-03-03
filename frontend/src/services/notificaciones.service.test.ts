/**
 * Tests para notificaciones.service.ts
 */
import axios from 'axios';
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

// Mock de axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('Notificaciones Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('API Functions', () => {
    test('getNotificaciones obtiene lista de notificaciones', async () => {
      const mockResponse = {
        data: {
          results: [
            {
              id_notificacion: 1,
              tipo: 'info',
              titulo: 'Test',
              mensaje: 'Mensaje test',
              leida: false
            }
          ],
          count: 1,
          next: null,
          previous: null
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await getNotificaciones({ leida: false });

      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/notificaciones/portal/',
        expect.objectContaining({
          params: { leida: false }
        })
      );
      expect(result.results).toHaveLength(1);
      expect(result.results[0].titulo).toBe('Test');
    });

    test('getNotificacionById obtiene notificación específica', async () => {
      const mockNotificacion = {
        id_notificacion: 1,
        tipo: 'info',
        titulo: 'Notificación Test',
        mensaje: 'Mensaje de prueba'
      };

      mockedAxios.get.mockResolvedValue({ data: mockNotificacion });

      const result = await getNotificacionById(1);

      expect(mockedAxios.get).toHaveBeenCalledWith('/notificaciones/portal/1/');
      expect(result.titulo).toBe('Notificación Test');
    });

    test('marcarNotificacionLeida marca como leída', async () => {
      const mockResponse = {
        data: {
          id_notificacion: 1,
          leida: true,
          fecha_lectura: '2026-03-03T10:00:00Z'
        }
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await marcarNotificacionLeida(1);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/notificaciones/portal/1/marcar_leida/'
      );
      expect(result.leida).toBe(true);
    });

    test('marcarTodasLeidas marca todas como leídas', async () => {
      const mockResponse = {
        data: {
          mensaje: 'Todas las notificaciones fueron marcadas como leídas',
          actualizadas: 5
        }
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await marcarTodasLeidas();

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/notificaciones/portal/marcar_todas_leidas/'
      );
      expect(result.actualizadas).toBe(5);
    });

    test('getResumenNotificaciones obtiene resumen', async () => {
      const mockResumen = {
        total: 10,
        no_leidas: 3,
        por_tipo: {
          info: 5,
          warning: 3,
          error: 1,
          success: 1
        }
      };

      mockedAxios.get.mockResolvedValue({ data: mockResumen });

      const result = await getResumenNotificaciones();

      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/notificaciones/portal/resumen/'
      );
      expect(result.total).toBe(10);
      expect(result.no_leidas).toBe(3);
    });
  });

  describe('Helper Functions', () => {
    test('formatearFecha formatea fecha correctamente', () => {
      const fecha = '2026-03-03T10:30:00Z';
      const resultado = formatearFecha(fecha);
      
      // El formato exacto puede variar según la configuración local
      expect(resultado).toContain('03/03/2026');
    });

    test('calcularTiempoTranscurrido devuelve "Hace unos momentos" para fecha reciente', () => {
      const ahora = new Date();
      const resultado = calcularTiempoTranscurrido(ahora.toISOString());
      
      expect(resultado).toBe('Hace unos momentos');
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
      expect(getIconoTipo('info')).toBe('Info');
      expect(getIconoTipo('warning')).toBe('AlertTriangle');
      expect(getIconoTipo('error')).toBe('AlertCircle');
      expect(getIconoTipo('success')).toBe('CheckCircle');
    });

    test('getColorTipo devuelve color correcto para cada tipo', () => {
      expect(getColorTipo('info')).toBe('blue');
      expect(getColorTipo('warning')).toBe('yellow');
      expect(getColorTipo('error')).toBe('red');
      expect(getColorTipo('success')).toBe('green');
    });

    test('getColorCriticidad devuelve color correcto para cada nivel', () => {
      expect(getColorCriticidad('baja')).toBe('blue');
      expect(getColorCriticidad('media')).toBe('yellow');
      expect(getColorCriticidad('alta')).toBe('orange');
      expect(getColorCriticidad('critica')).toBe('red');
    });
  });

  describe('Error Handling', () => {
    test('getNotificaciones maneja errores correctamente', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Network Error'));

      await expect(getNotificaciones()).rejects.toThrow('Network Error');
    });

    test('marcarNotificacionLeida maneja errores 404', async () => {
      mockedAxios.post.mockRejectedValue({
        response: { status: 404, data: { detail: 'Not found' } }
      });

      await expect(marcarNotificacionLeida(999)).rejects.toThrow();
    });
  });
});
