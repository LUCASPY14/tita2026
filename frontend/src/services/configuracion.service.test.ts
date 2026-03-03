/**
 * Tests para configuracion.service.ts
 */
import axios from 'axios';
import {
  getConfiguraciones,
  getConfiguracionesPorCategoria,
  getConfiguracionById,
  actualizarConfiguracion,
  resetearConfiguracion,
  formatearValorConfig,
  validarValorConfig,
  getIconoCategoria,
  getColorCategoria
} from './configuracion.service';

// Mock de axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('Configuracion Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('API Functions', () => {
    test('getConfiguraciones obtiene lista de configuraciones', async () => {
      const mockResponse = {
        data: {
          results: [
            {
              id_configuracion: 1,
              clave: 'TIMEOUT_SESSION',
              valor: '30',
              tipo: 'int',
              categoria: 'seguridad'
            }
          ],
          count: 1
        }
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await getConfiguraciones({ categoria: 'seguridad' });

      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/configuracion/',
        expect.objectContaining({
          params: { categoria: 'seguridad' }
        })
      );
      expect(result.results).toHaveLength(1);
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

      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await getConfiguracionesPorCategoria();

      expect(mockedAxios.get).toHaveBeenCalledWith('/configuracion/por_categoria/');
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

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await actualizarConfiguracion(1, '60');

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/configuracion/1/actualizar_valor/',
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

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await resetearConfiguracion(1);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/configuracion/1/resetear_default/'
      );
      expect(result.valor).toBe(result.valor_defecto);
    });
  });

  describe('Helper Functions', () => {
    test('formatearValorConfig formatea boolean', () => {
      expect(formatearValorConfig('true', 'boolean')).toBe('Sí');
      expect(formatearValorConfig('false', 'boolean')).toBe('No');
    });

    test('formatearValorConfig formatea int', () => {
      expect(formatearValorConfig('100', 'int')).toBe('100');
    });

    test('formatearValorConfig formatea decimal', () => {
      expect(formatearValorConfig('10.50', 'decimal')).toBe('10.50');
    });

    test('formatearValorConfig formatea password', () => {
      expect(formatearValorConfig('secreto123', 'password')).toBe('********');
    });

    test('formatearValorConfig formatea json', () => {
      const jsonStr = '{"key": "value"}';
      const result = formatearValorConfig(jsonStr, 'json');
      expect(result).toContain('key');
      expect(result).toContain('value');
    });

    test('validarValorConfig valida boolean', () => {
      expect(validarValorConfig('true', 'boolean', {})).toBe(true);
      expect(validarValorConfig('false', 'boolean', {})).toBe(true);
      expect(validarValorConfig('invalid', 'boolean', {})).toBe(false);
    });

    test('validarValorConfig valida int', () => {
      expect(validarValorConfig('100', 'int', {})).toBe(true);
      expect(validarValorConfig('abc', 'int', {})).toBe(false);
    });

    test('validarValorConfig valida decimal', () => {
      expect(validarValorConfig('10.50', 'decimal', {})).toBe(true);
      expect(validarValorConfig('10.5.0', 'decimal', {})).toBe(false);
    });

    test('validarValorConfig valida rango int', () => {
      const config = { valor_min: 1, valor_max: 100 };
      expect(validarValorConfig('50', 'int', config)).toBe(true);
      expect(validarValorConfig('0', 'int', config)).toBe(false);
      expect(validarValorConfig('101', 'int', config)).toBe(false);
    });

    test('validarValorConfig valida valores permitidos', () => {
      const config = { valores_permitidos: ['DEBUG', 'INFO', 'ERROR'] };
      expect(validarValorConfig('INFO', 'string', config)).toBe(true);
      expect(validarValorConfig('WARNING', 'string', config)).toBe(false);
    });

    test('validarValorConfig valida email', () => {
      expect(validarValorConfig('test@example.com', 'email', {})).toBe(true);
      expect(validarValorConfig('invalid-email', 'email', {})).toBe(false);
    });

    test('validarValorConfig valida url', () => {
      expect(validarValorConfig('https://example.com', 'url', {})).toBe(true);
      expect(validarValorConfig('http://localhost', 'url', {})).toBe(true);
      expect(validarValorConfig('not-a-url', 'url', {})).toBe(false);
    });

    test('validarValorConfig valida json', () => {
      expect(validarValorConfig('{"key": "value"}', 'json', {})).toBe(true);
      expect(validarValorConfig('{invalid json}', 'json', {})).toBe(false);
    });

    test('getIconoCategoria devuelve icono correcto', () => {
      expect(getIconoCategoria('seguridad')).toBe('Shield');
      expect(getIconoCategoria('email')).toBe('Mail');
      expect(getIconoCategoria('sistema')).toBe('Settings');
      expect(getIconoCategoria('notificaciones')).toBe('Bell');
      expect(getIconoCategoria('pagos')).toBe('CreditCard');
      expect(getIconoCategoria('integraciones')).toBe('Link');
      expect(getIconoCategoria('servidor')).toBe('Server');
      expect(getIconoCategoria('interfaz')).toBe('Palette');
    });

    test('getColorCategoria devuelve color correcto', () => {
      expect(getColorCategoria('seguridad')).toBe('red');
      expect(getColorCategoria('email')).toBe('blue');
      expect(getColorCategoria('sistema')).toBe('gray');
      expect(getColorCategoria('notificaciones')).toBe('yellow');
    });
  });

  describe('Edge Cases', () => {
    test('maneja valores vacíos', () => {
      expect(formatearValorConfig('', 'string')).toBe('');
      expect(validarValorConfig('', 'string', { requerido: false })).toBe(true);
    });

    test('maneja valores null', () => {
      expect(formatearValorConfig(null as any, 'string')).toBe('');
    });

    test('maneja json mal formado', () => {
      const resultado = formatearValorConfig('{not valid json', 'json');
      expect(resultado).toBe('{not valid json');
    });
  });
});
