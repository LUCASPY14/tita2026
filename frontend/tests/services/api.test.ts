/**
 * Tests para servicios API
 * Tests críticos de servicios de inventario y ventas
 */
import { inventarioService } from '../../src/services/inventario.service';
import { ventasService } from '../../src/services/ventas.service';

// Mock de fetch global
global.fetch = jest.fn();

describe('🧪 Inventory Service Tests', () => {
  
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('✅ CRÍTICO: should fetch stock list successfully', async () => {
    const mockStockData = {
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id_stock: 1,
          id_producto: 1,
          cantidad: 50,
          fecha_ultima_actualizacion: '2024-01-15T10:00:00Z',
          producto_nombre: 'Coca Cola 500ml',
          producto_categoria: 'Bebidas'
        },
        {
          id_stock: 2,
          id_producto: 2,
          cantidad: 10,
          fecha_ultima_actualizacion: '2024-01-15T10:00:00Z',
          producto_nombre: 'Arroz Blanco',
          producto_categoria: 'Granos'
        }
      ]
    };

    jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockStockData,
    } as Response);

    const result = await inventarioService.getStock();

    expect(result.count).toBe(2);
    expect(result.results).toHaveLength(2);
  });

  test('✅ CRÍTICO: should get stock by product ID', async () => {
    const mockStockData = {
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id_stock: 1,
          id_producto: 1,
          cantidad: 50,
          fecha_ultima_actualizacion: '2024-01-15T10:00:00Z',
          producto_nombre: 'Coca Cola 500ml',
          producto_categoria: 'Bebidas'
        }
      ]
    };

    jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockStockData,
    } as Response);

    const result = await inventarioService.getStockByProducto(1);

    expect(result.id_producto).toBe(1);
    expect(result.cantidad).toBe(50);
  });

  test('✅ CRÍTICO: should fetch stock movements', async () => {
    const mockMovimientos = {
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id_movimiento_stock: 1,
          fecha_hora: '2024-01-15T10:00:00Z',
          tipo_movimiento: 'Ingreso' as const,
          motivo: 'compra',
          cantidad: 50,
          stock_resultante: 100,
          id_producto: 1,
          producto_nombre: 'Coca Cola'
        }
      ]
    };

    jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockMovimientos,
    } as Response);

    const result = await inventarioService.getMovimientos({ id_producto: 1 });

    expect(result.count).toBe(2);
    expect(result.results[0].tipo_movimiento).toBe('Ingreso');
  });
});

describe('🧪 Sales Service Tests', () => {
  
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('✅ CRÍTICO: should create sale successfully', async () => {
    const saleData = {
      cliente_id: 1,
      metodo_pago: 'EFECTIVO' as const,
      items: [
        {
          producto_id: 1,
          cantidad: 2,
          precio_unitario: 3.50
        },
        {
          producto_id: 2,
          cantidad: 1,
          precio_unitario: 12.00
        }
      ]
    };

    const mockResponse = {
      id_venta: 1,
      fecha: '2024-01-15T10:00:00Z',
      monto_total: 19.00,
      saldo_pendiente: 0,
      estado_pago: 'Pagada',
      estado: 'Completada',
      tipo_venta: 'Contado',
      id_cliente: 1,
      id_empleado_cajero: 1,
      detalles: saleData.items
    };

    jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    const result = await ventasService.create(saleData);

    expect(result.monto_total).toBe(19.00);
    expect(result.estado_pago).toBe('Pagada');
  });

  test('✅ CRÍTICO: should create credit sale successfully', async () => {
    const creditSaleData = {
      cliente_id: 1,
      metodo_pago: 'CREDITO' as const,
      items: [
        {
          producto_id: 1,
          cantidad: 5,
          precio_unitario: 10.00
        }
      ]
    };

    const mockResponse = {
      id_venta: 2,
      fecha: '2024-01-15T10:00:00Z',
      monto_total: 50.00,
      saldo_pendiente: 50.00,
      estado_pago: 'Pendiente',
      estado: 'Completada',
      tipo_venta: 'Credito',
      id_cliente: 1,
      id_empleado_cajero: 1,
      detalles: creditSaleData.items
    };

    jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    const result = await ventasService.create(creditSaleData);

    expect(result.estado_pago).toBe('Pendiente');
    expect(result.monto_total).toBe(50.00);
  });

  test('✅ CRÍTICO: should get all sales with filters', async () => {
    const mockSales = {
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id_venta: 1,
          fecha: '2024-01-15T10:00:00Z',
          monto_total: 25.00,
          estado_pago: 'Pagada',
          estado: 'Completada',
          tipo_venta: 'Contado',
          id_cliente: 1,
          id_empleado_cajero: 1
        },
        {
          id_venta: 2,
          fecha: '2024-01-14T15:30:00Z',
          monto_total: 50.00,
          estado_pago: 'Pendiente',
          estado: 'Completada',
          tipo_venta: 'Credito',
          id_cliente: 1,
          id_empleado_cajero: 1
        }
      ]
    };

    jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockSales,
    } as Response);

    const filters = {
      fecha_desde: '2024-01-01',
      fecha_hasta: '2024-01-31',
      estado: 'COMPLETADA' as const
    };

    const result = await ventasService.getAll(filters);

    expect(result.count).toBe(2);
    expect(result.results).toHaveLength(2);
  });

  test('✅ CRÍTICO: should get sale by ID', async () => {
    const mockSale = {
      id_venta: 1,
      fecha: '2024-01-15T10:00:00Z',
      monto_total: 25.00,
      estado_pago: 'Pagada',
      estado: 'Completada',
      tipo_venta: 'Contado',
      id_cliente: 1,
      id_empleado_cajero: 1
    };

    jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockSale,
    } as Response);

    const result = await ventasService.getById(1);

    expect(result.id_venta).toBe(1);
    expect(result.estado_pago).toBe('Pagada');
  });

  test('✅ CRÍTICO: should cancel sale successfully', async () => {
    const mockResponse = {
      id: 1,
      estado: 'CANCELADA',
      mensaje: 'Venta cancelada exitosamente'
    };

    jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    const result = await ventasService.cancel(1);

    expect(result.estado).toBe('CANCELADA');
    expect(result.mensaje).toContain('cancelada');
  });

  test('✅ CRÍTICO: should update sale successfully', async () => {
    const updateData = {
      cliente_id: 2,
      items: [
        {
          producto_id: 1,
          cantidad: 3,
          precio_unitario: 5.00
        }
      ]
    };

    const mockResponse = {
      id_venta: 1,
      fecha: '2024-01-15T10:00:00Z',
      monto_total: 15.00,
      estado_pago: 'Pagada',
      estado: 'Completada',
      tipo_venta: 'Contado',
      id_cliente: 2,
      id_empleado_cajero: 1
    };

    jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    const result = await ventasService.update(1, updateData);

    expect(result.id_cliente).toBe(2);
    expect(result.monto_total).toBe(15.00);
  });

  test('✅ CRÍTICO: should validate sale data', async () => {
    const invalidSaleData = {
      cliente_id: 1,
      metodo_pago: 'EFECTIVO' as const,
      items: [] // Sin productos
    };

    jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ 
        error: 'La venta debe tener al menos un producto' 
      }),
    } as Response);

    await expect(
      ventasService.create(invalidSaleData)
    ).rejects.toThrow();
  });

  test('✅ CRÍTICO: should calculate total correctly', async () => {
    const saleData = {
      cliente_id: 1,
      metodo_pago: 'EFECTIVO' as const,
      items: [
        { producto_id: 1, cantidad: 3, precio_unitario: 5.00 },
        { producto_id: 2, cantidad: 2, precio_unitario: 7.50 },
        { producto_id: 3, cantidad: 1, precio_unitario: 10.00 }
      ]
    };

    const expectedTotal = (3 * 5.00) + (2 * 7.50) + (1 * 10.00); // 40.00

    const mockResponse = {
      id_venta: 1,
      fecha: '2024-01-15T10:00:00Z',
      monto_total: expectedTotal,
      saldo_pendiente: 0,
      estado_pago: 'Pagada',
      estado: 'Completada',
      tipo_venta: 'Contado',
      id_cliente: 1,
      id_empleado_cajero: 1,
      detalles: saleData.items
    };

    jest.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    const result = await ventasService.create(saleData);

    expect(result.monto_total).toBe(40.00);
  });
});
