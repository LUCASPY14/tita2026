import api from './api';
import { ventasService, VentaCreateData, VentaParams, CancelarVentaResponse } from './ventas.service';
import { Venta, PaginatedResponse } from '../types';

jest.mock('./api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('Ventas Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getAll', () => {
    const mockVentas: Venta[] = [
      {
        id_venta: 1,
        nro_factura_venta: 1,
        fecha: '2024-01-15',
        id_cliente: 10,
        cliente_nombre: 'Juan Pérez',
        monto_total: 150.00,
        saldo_pendiente: 0,
        estado_pago: 'Pagado',
        estado: 'COMPLETADA',
        tipo_venta: 'Contado'
      },
      {
        id_venta: 2,
        nro_factura_venta: 2,
        fecha: '2024-01-16',
        id_cliente: 11,
        cliente_nombre: 'María López',
        monto_total: 250.00,
        saldo_pendiente: 0,
        estado_pago: 'Pagado',
        estado: 'COMPLETADA',
        tipo_venta: 'Contado'
      }
    ];

    const mockResponse: PaginatedResponse<Venta> = {
      count: 2,
      next: null,
      previous: null,
      results: mockVentas
    };

    test('debe obtener todas las ventas sin parámetros', async () => {
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      const result = await ventasService.getAll();

      expect(mockedApi.get).toHaveBeenCalledWith('/ventas/', { params: undefined });
      expect(result).toEqual(mockResponse);
      expect(result.results).toHaveLength(2);
    });

    test('debe obtener ventas con parámetros de paginación', async () => {
      const params: VentaParams = { page: 2, page_size: 10 };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await ventasService.getAll(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/ventas/', { params });
    });

    test('debe filtrar ventas por fecha', async () => {
      const params: VentaParams = {
        fecha_desde: '2024-01-01',
        fecha_hasta: '2024-01-31'
      };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await ventasService.getAll(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/ventas/', { params });
    });

    test('debe filtrar ventas por estado', async () => {
      const params: VentaParams = { estado: 'COMPLETADA' };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await ventasService.getAll(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/ventas/', { params });
    });

    test('debe filtrar ventas por cliente', async () => {
      const params: VentaParams = { cliente_id: 10 };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await ventasService.getAll(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/ventas/', { params });
    });

    test('debe manejar respuesta vacía', async () => {
      const emptyResponse: PaginatedResponse<Venta> = {
        count: 0,
        next: null,
        previous: null,
        results: []
      };
      mockedApi.get.mockResolvedValue({ data: emptyResponse });

      const result = await ventasService.getAll();

      expect(result.results).toHaveLength(0);
      expect(result.count).toBe(0);
    });

    test('debe manejar error de red', async () => {
      mockedApi.get.mockRejectedValue(new Error('Network Error'));

      await expect(ventasService.getAll()).rejects.toThrow('Network Error');
    });
  });

  describe('getById', () => {
    const mockVenta: Venta = {
      id_venta: 1,
      nro_factura_venta: 1,
      fecha: '2024-01-15',
      id_cliente: 10,
      cliente_nombre: 'Juan Pérez',
      monto_total: 150.00,
      saldo_pendiente: 0,
      estado_pago: 'Pagado',
      estado: 'COMPLETADA',
      tipo_venta: 'Contado'
    };

    test('debe obtener venta por ID', async () => {
      mockedApi.get.mockResolvedValue({ data: mockVenta });

      const result = await ventasService.getById(1);

      expect(mockedApi.get).toHaveBeenCalledWith('/ventas/1/');
      expect(result).toEqual(mockVenta);
      expect(result.id_venta).toBe(1);
    });

    test('debe obtener venta con datos completos', async () => {
      mockedApi.get.mockResolvedValue({ data: mockVenta });

      const result = await ventasService.getById(1);

      expect(result.cliente_nombre).toBe('Juan Pérez');
      expect(result.monto_total).toBe(150.00);
    });

    test('debe manejar venta no encontrada', async () => {
      mockedApi.get.mockRejectedValue(new Error('Not Found'));

      await expect(ventasService.getById(999)).rejects.toThrow('Not Found');
    });
  });

  describe('create', () => {
    const mockVentaData: VentaCreateData = {
      cliente_id: 10,
      metodo_pago: 'EFECTIVO',
      items: [
        {
          producto_id: 5,
          cantidad: 2,
          precio_unitario: 75.00
        }
      ]
    };

    const mockCreatedVenta: Venta = {
      id_venta: 1,
      nro_factura_venta: 1,
      fecha: '2024-01-15',
      id_cliente: 10,
      cliente_nombre: 'Juan Pérez',
      monto_total: 150.00,
      saldo_pendiente: 0,
      estado_pago: 'Pagado',
      estado: 'COMPLETADA',
      tipo_venta: 'Contado'
    };

    test('debe crear venta nueva', async () => {
      mockedApi.post.mockResolvedValue({ data: mockCreatedVenta });

      const result = await ventasService.create(mockVentaData);

      expect(mockedApi.post).toHaveBeenCalledWith('/ventas/', mockVentaData);
      expect(result).toEqual(mockCreatedVenta);
      expect(result.id_venta).toBe(1);
    });

    test('debe crear venta con método de pago TARJETA', async () => {
      const tarjetaData: VentaCreateData = {
        ...mockVentaData,
        metodo_pago: 'TARJETA'
      };
      mockedApi.post.mockResolvedValue({ 
        data: { ...mockCreatedVenta, tipo_venta: 'Contado' } 
      });

      const result = await ventasService.create(tarjetaData);

      expect(result.tipo_venta).toBe('Contado');
    });

    test('debe crear venta con múltiples items', async () => {
      const multiItemData: VentaCreateData = {
        cliente_id: 10,
        metodo_pago: 'EFECTIVO',
        items: [
          { producto_id: 1, cantidad: 2, precio_unitario: 50.00 },
          { producto_id: 2, cantidad: 3, precio_unitario: 30.00 },
          { producto_id: 3, cantidad: 1, precio_unitario: 100.00 }
        ]
      };
      mockedApi.post.mockResolvedValue({ data: mockCreatedVenta });

      await ventasService.create(multiItemData);

      expect(mockedApi.post).toHaveBeenCalledWith('/ventas/', multiItemData);
    });

    test('debe manejar error de validación', async () => {
      mockedApi.post.mockRejectedValue(new Error('Validation Error'));

      await expect(ventasService.create(mockVentaData)).rejects.toThrow('Validation Error');
    });
  });

  describe('update', () => {
    const mockUpdatedVenta: Venta = {
      id_venta: 1,
      nro_factura_venta: 1,
      fecha: '2024-01-15',
      id_cliente: 11,
      cliente_nombre: 'María López',
      monto_total: 200.00,
      saldo_pendiente: 0,
      estado_pago: 'Pagado',
      estado: 'COMPLETADA',
      tipo_venta: 'Credito'
    };

    test('debe actualizar venta existente', async () => {
      const updateData: Partial<VentaCreateData> = {
        cliente_id: 11,
        metodo_pago: 'TARJETA'
      };
      mockedApi.put.mockResolvedValue({ data: mockUpdatedVenta });

      const result = await ventasService.update(1, updateData);

      expect(mockedApi.put).toHaveBeenCalledWith('/ventas/1/', updateData);
      expect(result).toEqual(mockUpdatedVenta);
    });

    test('debe actualizar tipo de venta', async () => {
      const updateData = { metodo_pago: 'TRANSFERENCIA' as const };
      mockedApi.put.mockResolvedValue({ 
        data: { ...mockUpdatedVenta, tipo_venta: 'Contado' } 
      });

      const result = await ventasService.update(1, updateData);

      expect(result.tipo_venta).toBe('Contado');
    });

    test('debe manejar venta no encontrada en update', async () => {
      mockedApi.put.mockRejectedValue(new Error('Not Found'));

      await expect(ventasService.update(999, {})).rejects.toThrow('Not Found');
    });
  });

  describe('cancel', () => {
    const mockCancelResponse: CancelarVentaResponse = {
      id: 1,
      estado: 'CANCELADA',
      mensaje: 'Venta cancelada exitosamente'
    };

    test('debe cancelar venta', async () => {
      mockedApi.post.mockResolvedValue({ data: mockCancelResponse });

      const result = await ventasService.cancel(1);

      expect(mockedApi.post).toHaveBeenCalledWith('/ventas/1/cancelar/');
      expect(result).toEqual(mockCancelResponse);
      expect(result.estado).toBe('CANCELADA');
    });

    test('debe retornar mensaje de confirmación al cancelar', async () => {
      mockedApi.post.mockResolvedValue({ data: mockCancelResponse });

      const result = await ventasService.cancel(1);

      expect(result.mensaje).toBe('Venta cancelada exitosamente');
    });

    test('debe manejar error al cancelar venta ya cancelada', async () => {
      mockedApi.post.mockRejectedValue(new Error('Venta ya está cancelada'));

      await expect(ventasService.cancel(1)).rejects.toThrow('Venta ya está cancelada');
    });

    test('debe manejar error de permisos al cancelar', async () => {
      mockedApi.post.mockRejectedValue(new Error('Forbidden'));

      await expect(ventasService.cancel(1)).rejects.toThrow('Forbidden');
    });
  });

  describe('Integration scenarios', () => {
    test('flujo completo: crear venta -> obtener por ID -> cancelar', async () => {
      const ventaData: VentaCreateData = {
        cliente_id: 10,
        metodo_pago: 'EFECTIVO',
        items: [{ producto_id: 5, cantidad: 2, precio_unitario: 75.00 }]
      };

      const ventaCreada: Venta = {
        id_venta: 1,
        nro_factura_venta: 1,
        fecha: '2024-01-15',
        id_cliente: 10,
        cliente_nombre: 'Juan Pérez',
        monto_total: 150.00,
        saldo_pendiente: 0,
        estado_pago: 'Pagado',
        estado: 'COMPLETADA',
        tipo_venta: 'Contado'
      };

      const cancelResponse: CancelarVentaResponse = {
        id: 1,
        estado: 'CANCELADA',
        mensaje: 'Venta cancelada'
      };

      // Crear
      mockedApi.post.mockResolvedValueOnce({ data: ventaCreada });
      const created = await ventasService.create(ventaData);
      expect(created.id_venta).toBe(1);

      // Obtener
      mockedApi.get.mockResolvedValueOnce({ data: ventaCreada });
      const fetched = await ventasService.getById(1);
      expect(fetched.estado).toBe('COMPLETADA');

      // Cancelar
      mockedApi.post.mockResolvedValueOnce({ data: cancelResponse });
      const cancelled = await ventasService.cancel(1);
      expect(cancelled.estado).toBe('CANCELADA');
    });
  });
});
