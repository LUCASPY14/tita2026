import api from './api';
import {
  recargasService,
  RecargaCajaData,
  RecargaTransferenciaData,
  ValidarTransferenciaData,
  HijoParams,
  TarjetaParams,
  RecargaParams
} from './recargas.service';
import { Hijo, Tarjeta, CargaSaldo, PaginatedResponse } from '../types';

jest.mock('./api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('Recargas Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('buscarHijos', () => {
    const mockHijos: Hijo[] = [
      {
        id_hijo: 1,
        nombre: 'Juan',
        apellido: 'Pérez',
        grado: '5to Grado',
        activo: true,
        id_cliente_responsable: 10
      },
      {
        id_hijo: 2,
        nombre: 'María',
        apellido: 'López',
        grado: '3er Grado',
        activo: true,
        id_cliente_responsable: 11
      }
    ];

    const mockResponse: PaginatedResponse<Hijo> = {
      count: 2,
      next: null,
      previous: null,
      results: mockHijos
    };

    test('debe buscar hijos sin parámetros', async () => {
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      const result = await recargasService.buscarHijos();

      expect(mockedApi.get).toHaveBeenCalledWith('/hijos/', { params: undefined });
      expect(result).toEqual(mockResponse);
      expect(result.results).toHaveLength(2);
    });

    test('debe buscar hijos con parámetros de búsqueda', async () => {
      const params: HijoParams = { search: 'Juan' };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await recargasService.buscarHijos(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/hijos/', { params });
    });

    test('debe filtrar hijos por cliente responsable', async () => {
      const params: HijoParams = { id_cliente_responsable: 10 };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await recargasService.buscarHijos(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/hijos/', { params });
    });

    test('debe filtrar hijos activos', async () => {
      const params: HijoParams = { activo: true };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await recargasService.buscarHijos(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/hijos/', { params });
    });

    test('debe manejar respuesta vacía', async () => {
      const emptyResponse: PaginatedResponse<Hijo> = {
        count: 0,
        next: null,
        previous: null,
        results: []
      };
      mockedApi.get.mockResolvedValue({ data: emptyResponse });

      const result = await recargasService.buscarHijos();

      expect(result.results).toHaveLength(0);
    });
  });

  describe('getHijoById', () => {
    const mockHijo: Hijo = {
      id_hijo: 1,
      nombre: 'Juan',
      apellido: 'Pérez',
      grado: '5to Grado',
      activo: true,
      id_cliente_responsable: 10
    };

    test('debe obtener hijo por ID', async () => {
      mockedApi.get.mockResolvedValue({ data: mockHijo });

      const result = await recargasService.getHijoById(1);

      expect(mockedApi.get).toHaveBeenCalledWith('/hijos/1/');
      expect(result).toEqual(mockHijo);
    });

    test('debe manejar hijo no encontrado', async () => {
      mockedApi.get.mockRejectedValue(new Error('Not Found'));

      await expect(recargasService.getHijoById(999)).rejects.toThrow('Not Found');
    });
  });

  describe('buscarTarjetas', () => {
    const mockTarjetas: Tarjeta[] = [
      {
        nro_tarjeta: '1234567890',
        saldo_actual: 100.00,
        estado: 'Activa',
        fecha_creacion: '2024-01-01',
        permite_saldo_negativo: false,
        limite_credito: 0,
        notificar_saldo_bajo: true,
        id_hijo: 1
      }
    ];

    const mockResponse: PaginatedResponse<Tarjeta> = {
      count: 1,
      next: null,
      previous: null,
      results: mockTarjetas
    };

    test('debe buscar tarjetas sin parámetros', async () => {
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      const result = await recargasService.buscarTarjetas();

      expect(mockedApi.get).toHaveBeenCalledWith('/tarjetas/', { params: undefined });
      expect(result).toEqual(mockResponse);
    });

    test('debe buscar tarjetas por estado', async () => {
      const params: TarjetaParams = { estado: 'ACTIVA' };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await recargasService.buscarTarjetas(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/tarjetas/', { params });
    });

    test('debe buscar tarjetas por hijo', async () => {
      const params: TarjetaParams = { id_hijo: 1 };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await recargasService.buscarTarjetas(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/tarjetas/', { params });
    });
  });

  describe('getTarjetaByHijo', () => {
    const mockTarjeta: Tarjeta = {
      nro_tarjeta: '1234567890',
      saldo_actual: 100.00,
      estado: 'Activa',
      fecha_creacion: '2024-01-01',
      permite_saldo_negativo: false,
      limite_credito: 0,
      notificar_saldo_bajo: true,
      id_hijo: 1
    };

    test('debe obtener tarjeta por hijo ID', async () => {
      const mockResponse: PaginatedResponse<Tarjeta> = {
        count: 1,
        next: null,
        previous: null,
        results: [mockTarjeta]
      };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      const result = await recargasService.getTarjetaByHijo(1);

      expect(mockedApi.get).toHaveBeenCalledWith('/tarjetas/', {
        params: { id_hijo: 1 }
      });
      expect(result).toEqual(mockTarjeta);
    });

    test('debe lanzar error si no se encuentra tarjeta para el hijo', async () => {
      const emptyResponse: PaginatedResponse<Tarjeta> = {
        count: 0,
        next: null,
        previous: null,
        results: []
      };
      mockedApi.get.mockResolvedValue({ data: emptyResponse });

      await expect(recargasService.getTarjetaByHijo(1)).rejects.toThrow(
        'No se encontró tarjeta para este hijo'
      );
    });
  });

  describe('getRecargas', () => {
    const mockRecargas: CargaSaldo[] = [
      {
        id_carga: 1,
        nro_tarjeta: '1234567890',
        monto_cargado: 50.00,
        fecha_carga: '2024-01-15',
        estado: 'Confirmada',
        metodo_pago: 'efectivo'
      }
    ];

    const mockResponse: PaginatedResponse<CargaSaldo> = {
      count: 1,
      next: null,
      previous: null,
      results: mockRecargas
    };

    test('debe obtener historial de recargas', async () => {
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      const result = await recargasService.getRecargas();

      expect(mockedApi.get).toHaveBeenCalledWith('/cargas-saldo/', { params: undefined });
      expect(result).toEqual(mockResponse);
    });

    test('debe filtrar recargas por estado', async () => {
      const params: RecargaParams = { estado: 'APROBADA' };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await recargasService.getRecargas(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/cargas-saldo/', { params });
    });

    test('debe filtrar recargas por tarjeta', async () => {
      const params: RecargaParams = { nro_tarjeta: '1234567890' };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await recargasService.getRecargas(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/cargas-saldo/', { params });
    });

    test('debe filtrar recargas por rango de fechas', async () => {
      const params: RecargaParams = {
        fecha_desde: '2024-01-01',
        fecha_hasta: '2024-01-31'
      };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await recargasService.getRecargas(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/cargas-saldo/', { params });
    });
  });

  describe('getRecargaById', () => {
    const mockRecarga: CargaSaldo = {
      id_carga: 1,
      nro_tarjeta: '1234567890',
      monto_cargado: 50.00,
      fecha_carga: '2024-01-15',
      estado: 'Confirmada',
      metodo_pago: 'efectivo'
    };

    test('debe obtener recarga por ID', async () => {
      mockedApi.get.mockResolvedValue({ data: mockRecarga });

      const result = await recargasService.getRecargaById(1);

      expect(mockedApi.get).toHaveBeenCalledWith('/cargas-saldo/1/');
      expect(result).toEqual(mockRecarga);
    });
  });

  describe('procesarRecargaCaja', () => {
    const mockRecargaData: RecargaCajaData = {
      hijo_id: 1,
      monto: 50.00,
      metodo_pago: 'efectivo',
      referencia: 'REF-001'
    };

    const mockRecarga: CargaSaldo = {
      id: 1,
      nro_tarjeta: '1234567890',
      monto: 50.00,
      fecha: '2024-01-15',
      estado: 'APROBADA',
      metodo_pago: 'efectivo'
    };

    test('debe procesar recarga en caja', async () => {
      mockedApi.post.mockResolvedValue({ data: mockRecarga });

      const result = await recargasService.procesarRecargaCaja(mockRecargaData);

      expect(mockedApi.post).toHaveBeenCalledWith('/cargas-saldo/caja/', mockRecargaData);
      expect(result).toEqual(mockRecarga);
    });

    test('debe procesar recarga con tarjeta POS', async () => {
      const posData: RecargaCajaData = {
        ...mockRecargaData,
        metodo_pago: 'tarjeta_pos'
      };
      mockedApi.post.mockResolvedValue({ data: { ...mockRecarga, metodo_pago: 'tarjeta_pos' } });

      const result = await recargasService.procesarRecargaCaja(posData);

      expect(result.metodo_pago).toBe('tarjeta_pos');
    });

    test('debe manejar error de saldo insuficiente', async () => {
      mockedApi.post.mockRejectedValue(new Error('Monto inválido'));

      await expect(recargasService.procesarRecargaCaja(mockRecargaData)).rejects.toThrow(
        'Monto inválido'
      );
    });
  });

  describe('generarReferenciaTransferencia', () => {
    const mockTransferenciaData: RecargaTransferenciaData = {
      hijo_id: 1,
      monto: 100.00
    };

    const mockReferencia = {
      codigo_referencia: 'TRANS-12345',
      monto_transferir: 103.00,
      datos_bancarios: {
        banco: 'Banco Test',
        cuenta: '1234567890'
      },
      instrucciones: 'Realizar transferencia y enviar comprobante'
    };

    test('debe generar código de referencia para transferencia', async () => {
      mockedApi.post.mockResolvedValue({ data: mockReferencia });

      const result = await recargasService.generarReferenciaTransferencia(mockTransferenciaData);

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/cargas-saldo/transferencia/referencia/',
        mockTransferenciaData
      );
      expect(result).toEqual(mockReferencia);
      expect(result.codigo_referencia).toBe('TRANS-12345');
    });

    test('debe incluir comisión en monto a transferir', async () => {
      mockedApi.post.mockResolvedValue({ data: mockReferencia });

      const result = await recargasService.generarReferenciaTransferencia(mockTransferenciaData);

      expect(result.monto_transferir).toBeGreaterThan(mockTransferenciaData.monto);
    });
  });

  describe('validarTransferencia', () => {
    const mockValidarData: ValidarTransferenciaData = {
      codigo_referencia: 'TRANS-12345',
      numero_comprobante: 'COMP-98765',
      empleado_id: 5
    };

    const mockRecarga: CargaSaldo = {
      id_carga: 1,
      nro_tarjeta: '1234567890',
      monto_cargado: 100.00,
      fecha_carga: '2024-01-15',
      estado: 'Pendiente',
      metodo_pago: 'transferencia'
    };

    test('debe validar transferencia bancaria', async () => {
      mockedApi.post.mockResolvedValue({ data: mockRecarga });

      const result = await recargasService.validarTransferencia(mockValidarData);

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/cargas-saldo/transferencia/validar/',
        mockValidarData
      );
      expect(result).toEqual(mockRecarga);
    });

    test('debe manejar error de código inválido', async () => {
      mockedApi.post.mockRejectedValue(new Error('Código de referencia inválido'));

      await expect(recargasService.validarTransferencia(mockValidarData)).rejects.toThrow(
        'Código de referencia inválido'
      );
    });
  });

  describe('aprobarRecarga', () => {
    const mockRecarga: CargaSaldo = {
      id_carga: 1,
      nro_tarjeta: '1234567890',
      monto_cargado: 50.00,
      fecha_carga: '2024-01-15',
      estado: 'Confirmada',
      metodo_pago: 'transferencia'
    };

    test('debe aprobar recarga como supervisor', async () => {
      mockedApi.post.mockResolvedValue({ data: mockRecarga });

      const result = await recargasService.aprobarRecarga(1, 10);

      expect(mockedApi.post).toHaveBeenCalledWith('/cargas-saldo/1/aprobar/', {
        supervisor_id: 10
      });
      expect(result).toEqual(mockRecarga);
      expect(result.estado).toBe('Confirmada');
    });

    test('debe aprobar recarga sin ID de supervisor', async () => {
      mockedApi.post.mockResolvedValue({ data: mockRecarga });

      await recargasService.aprobarRecarga(1);

      expect(mockedApi.post).toHaveBeenCalledWith('/cargas-saldo/1/aprobar/', {
        supervisor_id: undefined
      });
    });

    test('debe manejar error de permisos', async () => {
      mockedApi.post.mockRejectedValue(new Error('Forbidden'));

      await expect(recargasService.aprobarRecarga(1, 10)).rejects.toThrow('Forbidden');
    });
  });

  describe('Integration scenarios', () => {
    test('flujo completo: buscar hijo -> obtener tarjeta -> procesar recarga', async () => {
      const hijo: Hijo = {
        id_hijo: 1,
        nombre: 'Juan',
        apellido: 'Pérez',
        grado: '5to',
        activo: true,
        id_cliente_responsable: 10
      };

      const tarjeta: Tarjeta = {
        nro_tarjeta: '1234567890',
        saldo_actual: 50.00,
        estado: 'Activa',
        fecha_creacion: '2024-01-01',
        permite_saldo_negativo: false,
        limite_credito: 0,
        notificar_saldo_bajo: true,
        id_hijo: 1
      };

      const recarga: CargaSaldo = {
        id_carga: 1,
        nro_tarjeta: '1234567890',
        monto_cargado: 50.00,
        fecha_carga: '2024-01-15',
        estado: 'Confirmada',
        metodo_pago: 'efectivo'
      };

      // Buscar hijo
      mockedApi.get.mockResolvedValueOnce({
        data: { count: 1, next: null, previous: null, results: [hijo] }
      });
      const hijosResult = await recargasService.buscarHijos({ search: 'Juan' });
      expect(hijosResult.results[0].id_hijo).toBe(1);

      // Obtener tarjeta
      mockedApi.get.mockResolvedValueOnce({
        data: { count: 1, next: null, previous: null, results: [tarjeta] }
      });
      const tarjetaResult = await recargasService.getTarjetaByHijo(1);
      expect(tarjetaResult.nro_tarjeta).toBe('1234567890');

      // Procesar recarga
      mockedApi.post.mockResolvedValueOnce({ data: recarga });
      const recargaResult = await recargasService.procesarRecargaCaja({
        hijo_id: 1,
        monto: 50.00,
        metodo_pago: 'efectivo'
      });
      expect(recargaResult.estado).toBe('Confirmada');
    });
  });
});
