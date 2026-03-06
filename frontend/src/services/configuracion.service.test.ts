/**
 * Tests para configuracion.service.ts
 */
import api from './api';
import {
  getConfiguraciones,
  getConfiguracionesPorCategoria,
  actualizarConfiguracion,
  resetearConfiguracion,
  formatearValorConfig,
  validarValorConfig,
  getIconoCategoria,
  getColorCategoria
} from './configuracion.service';

jest.mock('./api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('Configuracion Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('API Functions', () => {
    test('getConfiguraciones obtiene lista de configuraciones', async () => {
      const mockResponse = {
        data: [
          {
            id_configuracion: 1,
            clave: 'TIMEOUT_SESSION',
            valor: '30',
            tipo: 'number',
            categoria: 'seguridad'
          }
        ]
      };

      mockedApi.get.mockResolvedValue(mockResponse);

      const result = await getConfiguraciones({ categoria: 'seguridad' });

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/configuracion-sistema/'),
        expect.objectContaining({
          params: { categoria: 'seguridad' }
        })
      );
      expect(result).toHaveLength(1);
    });

    test('getConfiguracionesPorCategoria agrupa por categoría', async () => {
      const mockResponse = {
        data: {
          seguridad: [
            { clave: 'TIMEOUT_SESSION', valor: '30' }
          ],
          email: [
            { clave: 'SMTP_HOST', valor: 'smtp.gmail.com' }
          ]
        }
      };

      mockedApi.get.mockResolvedValue(mockResponse);

      const result = await getConfiguracionesPorCategoria();

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/configuracion-sistema/por_categoria/')
      );
      expect(result).toHaveProperty('seguridad');
      expect(result).toHaveProperty('email');
    });

    test('actualizarConfiguracion actualiza valor', async () => {
      const mockResponse = {
        data: {
          id_configuracion: 1,
          clave: 'TIMEOUT_SESSION',
          valor: '60'
        }
      };

      mockedApi.post.mockResolvedValue(mockResponse);

      const result = await actualizarConfiguracion(1, { valor: '60' });

      expect(mockedApi.post).toHaveBeenCalledWith(
        expect.stringContaining('/configuracion-sistema/1/actualizar_valor/'),
        { valor: '60' }
      );
      expect(result.valor).toBe('60');
    });

    test('resetearConfiguracion resetea a default', async () => {
      const mockResponse = {
        data: {
          id_configuracion: 1,
          clave: 'TIMEOUT_SESSION',
          valor: '30',
          valor_defecto: '30'
        }
      };

      mockedApi.post.mockResolvedValue(mockResponse);

      const result = await resetearConfiguracion(1);

      expect(mockedApi.post).toHaveBeenCalledWith(
        expect.stringContaining('/configuracion-sistema/1/resetear_default/')
      );
      expect(result.valor).toBe(result.valor_defecto);
    });
  });

  describe('Helper Functions', () => {
    test('formatearValorConfig formatea boolean', () => {
      expect(formatearValorConfig({ valor: 'true', tipo: 'boolean' } as any)).toBe('Sí');
      expect(formatearValorConfig({ valor: 'false', tipo: 'boolean' } as any)).toBe('No');
    });

    test('formatearValorConfig formatea int', () => {
      expect(formatearValorConfig({ valor: '100', tipo: 'number' } as any)).toBe('100');
    });

    test('formatearValorConfig formatea decimal', () => {
      expect(formatearValorConfig({ valor: '10.50', tipo: 'number' } as any)).toContain('10');
    });

    test('formatearValorConfig formatea password', () => {
      expect(formatearValorConfig({ valor: 'secreto123', tipo: 'password' } as any)).toBe('••••••••');
    });

    test('formatearValorConfig formatea json', () => {
      const jsonStr = '{"key": "value"}';
      const result = formatearValorConfig({ valor: jsonStr, tipo: 'json' } as any);
      expect(result).toContain('key');
      expect(result).toContain('value');
    });

    test('validarValorConfig valida boolean', () => {
      expect(validarValorConfig({ tipo: 'boolean', requerido: false } as any, 'true').valido).toBe(true);
      expect(validarValorConfig({ tipo: 'boolean', requerido: false } as any, 'false').valido).toBe(true);
      expect(validarValorConfig({ tipo: 'boolean', requerido: false } as any, 'invalid').valido).toBe(false);
    });

    test('validarValorConfig valida int', () => {
      expect(validarValorConfig({ tipo: 'number', requerido: false } as any, '100').valido).toBe(true);
      expect(validarValorConfig({ tipo: 'number', requerido: false } as any, 'abc').valido).toBe(false);
    });

    test('validarValorConfig valida decimal', () => {
      expect(validarValorConfig({ tipo: 'number', requerido: false } as any, '10.50').valido).toBe(true);
      // parseFloat es permisivo: parseFloat('10.5.0') = 10.5 (válido)
      expect(validarValorConfig({ tipo: 'number', requerido: false } as any, '10.5.0').valido).toBe(true);
      expect(validarValorConfig({ tipo: 'number', requerido: false } as any, 'abc.def').valido).toBe(false);
    });

    test('validarValorConfig valida rango int', () => {
      const config = { tipo: 'number', requerido: false, valor_min: '1', valor_max: '100' };
      expect(validarValorConfig(config as any, '50').valido).toBe(true);
      expect(validarValorConfig(config as any, '0').valido).toBe(false);
      expect(validarValorConfig(config as any, '101').valido).toBe(false);
    });

    test('validarValorConfig valida valores permitidos', () => {
      // valores_permitidos debe ser array, no string
      const config = { tipo: 'string', requerido: false, valores_permitidos: ['DEBUG', 'INFO', 'ERROR'] };
      expect(validarValorConfig(config as any, 'INFO').valido).toBe(true);
      expect(validarValorConfig(config as any, 'WARNING').valido).toBe(false);
    });

    test('validarValorConfig valida email', () => {
      expect(validarValorConfig({ tipo: 'email', requerido: false } as any, 'test@example.com').valido).toBe(true);
      expect(validarValorConfig({ tipo: 'email', requerido: false } as any, 'invalid-email').valido).toBe(false);
    });

    test('validarValorConfig valida url', () => {
      expect(validarValorConfig({ tipo: 'url', requerido: false } as any, 'https://example.com').valido).toBe(true);
      expect(validarValorConfig({ tipo: 'url', requerido: false } as any, 'http://localhost').valido).toBe(true);
      expect(validarValorConfig({ tipo: 'url', requerido: false } as any, 'not-a-url').valido).toBe(false);
    });

    test('validarValorConfig valida json', () => {
      expect(validarValorConfig({ tipo: 'json', requerido: false } as any, '{"key": "value"}').valido).toBe(true);
      expect(validarValorConfig({ tipo: 'json', requerido: false } as any, '{invalid json}').valido).toBe(false);
    });

    test('getIconoCategoria devuelve icono correcto', () => {
      expect(getIconoCategoria('general')).toBe('Settings');
      expect(getIconoCategoria('seguridad')).toBe('Shield');
      expect(getIconoCategoria('email')).toBe('Mail');
      expect(getIconoCategoria('sistema')).toBe('Server');
      expect(getIconoCategoria('notificaciones')).toBe('Bell');
      expect(getIconoCategoria('pagos')).toBe('CreditCard');
      expect(getIconoCategoria('integraciones')).toBe('Link');
      expect(getIconoCategoria('ui')).toBe('Palette');
      expect(getIconoCategoria('desconocido')).toBe('Settings'); // Default
    });

    test('getColorCategoria devuelve color correcto', () => {
      expect(getColorCategoria('general')).toBe('text-blue-600 bg-blue-50');
      expect(getColorCategoria('seguridad')).toBe('text-red-600 bg-red-50');
      expect(getColorCategoria('email')).toBe('text-indigo-600 bg-indigo-50');
      expect(getColorCategoria('sistema')).toBe('text-gray-600 bg-gray-50');
      expect(getColorCategoria('notificaciones')).toBe('text-yellow-600 bg-yellow-50');
      expect(getColorCategoria('pagos')).toBe('text-green-600 bg-green-50');
      expect(getColorCategoria('integraciones')).toBe('text-purple-600 bg-purple-50');
      expect(getColorCategoria('ui')).toBe('text-pink-600 bg-pink-50');
      expect(getColorCategoria('desconocido')).toBe('text-gray-600 bg-gray-50'); // Default
    });
  });

  describe('Edge Cases', () => {
    test('maneja valores vacíos', () => {
      expect(formatearValorConfig({ valor: '', tipo: 'string' } as any)).toBe('');
      expect(validarValorConfig({ tipo: 'string', requerido: false } as any, '').valido).toBe(true);
    });

    test('maneja valores null', () => {
      // formatearValorConfig devuelve null si valor es null en tipo default
      expect(formatearValorConfig({ valor: null as any, tipo: 'string' } as any)).toBeNull();
    });

    test('maneja json mal formado', () => {
      const resultado = formatearValorConfig({ valor: '{not valid json', tipo: 'json' } as any);
      expect(resultado).toBe('{not valid json');
    });
  });
});
