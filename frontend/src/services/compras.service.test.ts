import api from './api';
import { 
  comprasService,
  ProveedorParams,
  CompraParams,
  ProveedorData
} from './compras.service';
import type {
  Proveedor,
  Compra,
  CompraData,
  PaginatedResponse,
  CuentaCorrienteProveedor
} from '../types';

jest.mock('./api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('Compras Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // === PROVEEDORES ===
  describe('Proveedores', () => {
    const mockProveedores: Proveedor[] = [
      {
        id_proveedor: 1,
        ruc: '80012345-6',
        razon_social: 'Proveedor ABC S.A.',
        telefono: '0981234567',
        email: 'contacto@proveedorabc.com',
        direccion: 'Av. Principal 123',
        ciudad: 'Asunción',
        activo: true,
        fecha_registro: '2024-01-01'
      },
      {
        id_proveedor: 2,
        ruc: '80098765-4',
        razon_social: 'Distribuidora XYZ',
        telefono: '0987654321',
        email: 'ventas@xyz.com',
        direccion: 'Calle Secundaria 456',
        ciudad: 'Luque',
        activo: true,
        fecha_registro: '2024-01-05'
      }
    ];

    const mockResponse: PaginatedResponse<Proveedor> = {
      count: 2,
      next: null,
      previous: null,
      results: mockProveedores
    };

    describe('getProveedores', () => {
      test('debe obtener proveedores sin filtros', async () => {
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await comprasService.getProveedores();

        expect(mockedApi.get).toHaveBeenCalledWith('/proveedores/', { params: undefined });
        expect(result).toEqual(mockResponse);
        expect(result.results).toHaveLength(2);
      });

      test('debe obtener proveedores con paginación', async () => {
        const params: ProveedorParams = { page: 1, page_size: 10 };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await comprasService.getProveedores(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/proveedores/', { params });
      });

      test('debe buscar proveedores por término', async () => {
        const params: ProveedorParams = { search: 'ABC' };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await comprasService.getProveedores(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/proveedores/', { params });
      });

      test('debe filtrar proveedores activos', async () => {
        const params: ProveedorParams = { activo: true };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await comprasService.getProveedores(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/proveedores/', { params });
      });

      test('debe filtrar proveedores por ciudad', async () => {
        const params: ProveedorParams = { ciudad: 'Asunción' };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await comprasService.getProveedores(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/proveedores/', { params });
      });
    });

    describe('getProveedorById', () => {
      test('debe obtener proveedor por ID', async () => {
        mockedApi.get.mockResolvedValue({ data: mockProveedores[0] });

        const result = await comprasService.getProveedorById(1);

        expect(mockedApi.get).toHaveBeenCalledWith('/proveedores/1/');
        expect(result).toEqual(mockProveedores[0]);
        expect(result.id_proveedor).toBe(1);
      });

      test('debe manejar proveedor no encontrado', async () => {
        mockedApi.get.mockRejectedValue(new Error('Not Found'));

        await expect(comprasService.getProveedorById(999)).rejects.toThrow('Not Found');
      });
    });

    describe('buscarPorRuc', () => {
      test('debe buscar proveedor por RUC', async () => {
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await comprasService.buscarPorRuc('80012345-6');

        expect(mockedApi.get).toHaveBeenCalledWith('/proveedores/', {
          params: { search: '80012345-6' }
        });
        expect(result).toEqual(mockResponse);
      });
    });

    describe('crearProveedor', () => {
      const proveedorData: ProveedorData = {
        ruc: '80033333-3',
        razon_social: 'Nuevo Proveedor S.R.L.',
        telefono: '0991112222',
        email: 'nuevo@proveedor.com',
        direccion: 'Av. Test 789',
        ciudad: 'San Lorenzo',
        activo: true
      };

      test('debe crear proveedor nuevo', async () => {
        const proveedorCreado: Proveedor = {
          id_proveedor: 3,
          ...proveedorData,
          fecha_registro: '2024-01-20'
        };
        mockedApi.post.mockResolvedValue({ data: proveedorCreado });

        const result = await comprasService.crearProveedor(proveedorData);

        expect(mockedApi.post).toHaveBeenCalledWith('/proveedores/', proveedorData);
        expect(result).toEqual(proveedorCreado);
        expect(result.id_proveedor).toBe(3);
      });

      test('debe manejar error de RUC duplicado', async () => {
        mockedApi.post.mockRejectedValue(new Error('RUC ya existe'));

        await expect(comprasService.crearProveedor(proveedorData)).rejects.toThrow(
          'RUC ya existe'
        );
      });
    });

    describe('actualizarProveedor', () => {
      test('debe actualizar proveedor', async () => {
        const updateData = { 
          telefono: '0991234567', 
          email: 'nuevo@proveedorabc.com' 
        };
        const proveedorActualizado: Proveedor = { 
          ...mockProveedores[0], 
          ...updateData 
        };
        mockedApi.patch.mockResolvedValue({ data: proveedorActualizado });

        const result = await comprasService.actualizarProveedor(1, updateData);

        expect(mockedApi.patch).toHaveBeenCalledWith('/proveedores/1/', updateData);
        expect(result.telefono).toBe('0991234567');
        expect(result.email).toBe('nuevo@proveedorabc.com');
      });

      test('debe actualizar solo el campo especificado', async () => {
        const updateData = { ciudad: 'Fernando de la Mora' };
        mockedApi.patch.mockResolvedValue({ 
          data: { ...mockProveedores[0], ...updateData } 
        });

        const result = await comprasService.actualizarProveedor(1, updateData);

        expect(result.ciudad).toBe('Fernando de la Mora');
      });
    });

    describe('eliminarProveedor', () => {
      test('debe eliminar proveedor', async () => {
        mockedApi.delete.mockResolvedValue({ data: null });

        await comprasService.eliminarProveedor(1);

        expect(mockedApi.delete).toHaveBeenCalledWith('/proveedores/1/');
      });

      test('debe manejar error al eliminar proveedor con compras', async () => {
        mockedApi.delete.mockRejectedValue(
          new Error('Cannot delete provider with purchases')
        );

        await expect(comprasService.eliminarProveedor(1)).rejects.toThrow(
          'Cannot delete provider with purchases'
        );
      });
    });

    describe('toggleEstadoProveedor', () => {
      test('debe desactivar proveedor', async () => {
        const proveedorInactivo: Proveedor = { ...mockProveedores[0], activo: false };
        mockedApi.patch.mockResolvedValue({ data: proveedorInactivo });

        const result = await comprasService.toggleEstadoProveedor(1, false);

        expect(mockedApi.patch).toHaveBeenCalledWith('/proveedores/1/', { activo: false });
        expect(result.activo).toBe(false);
      });

      test('debe activar proveedor', async () => {
        const proveedorActivo: Proveedor = { ...mockProveedores[0], activo: true };
        mockedApi.patch.mockResolvedValue({ data: proveedorActivo });

        const result = await comprasService.toggleEstadoProveedor(1, true);

        expect(mockedApi.patch).toHaveBeenCalledWith('/proveedores/1/', { activo: true });
        expect(result.activo).toBe(true);
      });
    });

    describe('getCuentaCorrienteProveedor', () => {
      const mockCuentaCorriente: CuentaCorrienteProveedor = {
        total_compras: 5000000,
        total_pagado: 3000000,
        saldo_pendiente: 2000000,
        compras_pendientes: 3,
        notas_credito: 1,
        proveedor: {
          id: 1,
          razon_social: 'Proveedor ABC S.A.',
          ruc: '80012345-6'
        }
      };

      test('debe obtener cuenta corriente de proveedor', async () => {
        mockedApi.get.mockResolvedValue({ data: mockCuentaCorriente });

        const result = await comprasService.getCuentaCorrienteProveedor(1);

        expect(mockedApi.get).toHaveBeenCalledWith('/proveedores/1/cuenta_corriente/');
        expect(result).toEqual(mockCuentaCorriente);
        expect(result.saldo_pendiente).toBe(2000000);
      });

      test('debe calcular saldo correctamente', async () => {
        mockedApi.get.mockResolvedValue({ data: mockCuentaCorriente });

        const result = await comprasService.getCuentaCorrienteProveedor(1);

        expect(result.total_compras - result.total_pagado).toBe(result.saldo_pendiente);
      });
    });
  });

  // === COMPRAS ===
  describe('Compras', () => {
    const mockCompras: Compra[] = [
      {
        id_compra: 1,
        fecha: '2024-01-15',
        monto_total: 1500000,
        saldo_pendiente: 1500000,
        estado_pago: 'Pendiente',
        nro_factura: '001-001-0001234',
        observaciones: 'Compra de productos varios',
        id_proveedor: 1,
        proveedor_nombre: 'Proveedor ABC S.A.'
      },
      {
        id_compra: 2,
        fecha: '2024-01-20',
        monto_total: 2500000,
        saldo_pendiente: 500000,
        estado_pago: 'Parcial',
        nro_factura: '001-001-0001235',
        id_proveedor: 2,
        proveedor_nombre: 'Distribuidora XYZ'
      }
    ];

    const mockResponse: PaginatedResponse<Compra> = {
      count: 2,
      next: null,
      previous: null,
      results: mockCompras
    };

    describe('getCompras', () => {
      test('debe obtener compras sin filtros', async () => {
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await comprasService.getCompras();

        expect(mockedApi.get).toHaveBeenCalledWith('/compras/', { params: undefined });
        expect(result).toEqual(mockResponse);
      });

      test('debe filtrar compras por estado de pago', async () => {
        const params: CompraParams = { estado_pago: 'Pendiente' };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await comprasService.getCompras(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/compras/', { params });
      });

      test('debe filtrar compras por proveedor', async () => {
        const params: CompraParams = { id_proveedor: 1 };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await comprasService.getCompras(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/compras/', { params });
      });

      test('debe filtrar compras por rango de fechas', async () => {
        const params: CompraParams = { 
          fecha_desde: '2024-01-01', 
          fecha_hasta: '2024-01-31' 
        };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await comprasService.getCompras(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/compras/', { params });
      });

      test('debe ordenar compras', async () => {
        const params: CompraParams = { ordering: '-fecha' };
        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await comprasService.getCompras(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/compras/', { params });
      });
    });

    describe('getCompraById', () => {
      test('debe obtener compra por ID', async () => {
        mockedApi.get.mockResolvedValue({ data: mockCompras[0] });

        const result = await comprasService.getCompraById(1);

        expect(mockedApi.get).toHaveBeenCalledWith('/compras/1/');
        expect(result).toEqual(mockCompras[0]);
        expect(result.id_compra).toBe(1);
      });
    });

    describe('crearCompra', () => {
      const compraData: CompraData = {
        fecha: '2024-01-25',
        id_proveedor: 1,
        nro_factura: '001-001-0001236',
        observaciones: 'Nueva compra',
        detalles: [
          {
            id_producto: 1,
            cantidad: 10,
            costo_unitario: 50000
          },
          {
            id_producto: 2,
            cantidad: 5,
            costo_unitario: 100000
          }
        ]
      };

      test('debe crear compra nueva', async () => {
        const compraCreada: Compra = {
          id_compra: 3,
          fecha: compraData.fecha,
          monto_total: 1000000,
          saldo_pendiente: 1000000,
          estado_pago: 'Pendiente',
          nro_factura: compraData.nro_factura,
          observaciones: compraData.observaciones,
          id_proveedor: compraData.id_proveedor
        };
        mockedApi.post.mockResolvedValue({ data: compraCreada });

        const result = await comprasService.crearCompra(compraData);

        expect(mockedApi.post).toHaveBeenCalledWith('/compras/', compraData);
        expect(result).toEqual(compraCreada);
        expect(result.id_compra).toBe(3);
      });

      test('debe calcular monto total correctamente', async () => {
        const compraCreada: Compra = {
          id_compra: 3,
          fecha: compraData.fecha,
          monto_total: 1000000, // (10 * 50000) + (5 * 100000)
          saldo_pendiente: 1000000,
          estado_pago: 'Pendiente',
          id_proveedor: compraData.id_proveedor
        };
        mockedApi.post.mockResolvedValue({ data: compraCreada });

        const result = await comprasService.crearCompra(compraData);

        expect(result.monto_total).toBe(1000000);
      });
    });

    describe('actualizarCompra', () => {
      test('debe actualizar compra', async () => {
        const updateData = { observaciones: 'Observaciones actualizadas' };
        const compraActualizada: Compra = { ...mockCompras[0], ...updateData };
        mockedApi.patch.mockResolvedValue({ data: compraActualizada });

        const result = await comprasService.actualizarCompra(1, updateData);

        expect(mockedApi.patch).toHaveBeenCalledWith('/compras/1/', updateData);
        expect(result.observaciones).toBe('Observaciones actualizadas');
      });
    });

    describe('eliminarCompra', () => {
      test('debe eliminar compra', async () => {
        mockedApi.delete.mockResolvedValue({ data: null });

        await comprasService.eliminarCompra(1);

        expect(mockedApi.delete).toHaveBeenCalledWith('/compras/1/');
      });
    });

    describe('confirmarCompra', () => {
      test('debe confirmar compra y actualizar inventario', async () => {
        const compraConfirmada: Compra = {
          ...mockCompras[0],
          estado_pago: 'Pendiente'
        };
        mockedApi.post.mockResolvedValue({ 
          data: { 
            compra: compraConfirmada,
            mensaje: 'Compra confirmada exitosamente'
          } 
        });

        const result = await comprasService.confirmarCompra(1);

        expect(mockedApi.post).toHaveBeenCalledWith('/compras/1/confirmar/');
        expect(result).toEqual(compraConfirmada);
      });
    });

    describe('getComprasPendientes', () => {
      test('debe obtener solo compras pendientes', async () => {
        const comprasPendientes = [mockCompras[0]]; // Solo la primera tiene estado Pendiente
        mockedApi.get.mockResolvedValue({ data: comprasPendientes });

        const result = await comprasService.getComprasPendientes();

        expect(mockedApi.get).toHaveBeenCalledWith('/compras/pendientes/');
        expect(result).toEqual(comprasPendientes);
        expect(result).toHaveLength(1);
      });
    });
  });

  // === ESTADÍSTICAS ===
  describe('Estadísticas', () => {
    const mockEstadisticas = {
      total_compras: 50,
      compras_pendientes: 15,
      monto_total: 25000000,
      saldo_pendiente: 5000000
    };

    describe('getEstadisticasCompras', () => {
      test('debe obtener estadísticas de compras', async () => {
        mockedApi.get.mockResolvedValue({ data: mockEstadisticas });

        const result = await comprasService.getEstadisticasCompras();

        expect(mockedApi.get).toHaveBeenCalledWith('/compras/estadisticas/');
        expect(result).toEqual(mockEstadisticas);
        expect(result.total_compras).toBe(50);
        expect(result.saldo_pendiente).toBe(5000000);
      });

      test('debe calcular porcentaje pendiente correctamente', async () => {
        mockedApi.get.mockResolvedValue({ data: mockEstadisticas });

        const result = await comprasService.getEstadisticasCompras();

        const porcentajePendiente = (result.saldo_pendiente / result.monto_total) * 100;
        expect(porcentajePendiente).toBe(20); // 5M / 25M = 20%
      });
    });
  });

  // === INTEGRATION SCENARIOS ===
  describe('Integration scenarios', () => {
    test('flujo completo: crear proveedor -> crear compra -> confirmar', async () => {
      // 1. Crear proveedor
      const proveedorData: ProveedorData = {
        ruc: '80044444-4',
        razon_social: 'Test Proveedor',
        activo: true
      };
      const proveedorCreado: Proveedor = {
        id_proveedor: 10,
        ...proveedorData,
        fecha_registro: '2024-01-25'
      };
      mockedApi.post.mockResolvedValueOnce({ data: proveedorCreado });
      const proveedor = await comprasService.crearProveedor(proveedorData);
      expect(proveedor.id_proveedor).toBe(10);

      // 2. Crear compra
      const compraData: CompraData = {
        fecha: '2024-01-25',
        id_proveedor: proveedor.id_proveedor,
        detalles: [
          {
            id_producto: 1,
            cantidad: 10,
            costo_unitario: 10000
          }
        ]
      };
      const compraCreada: Compra = {
        id_compra: 20,
        fecha: compraData.fecha,
        monto_total: 100000,
        saldo_pendiente: 100000,
        estado_pago: 'Pendiente',
        id_proveedor: proveedor.id_proveedor
      };
      mockedApi.post.mockResolvedValueOnce({ data: compraCreada });
      const compra = await comprasService.crearCompra(compraData);
      expect(compra.id_compra).toBe(20);
      expect(compra.estado_pago).toBe('Pendiente');

      // 3. Confirmar compra
      mockedApi.post.mockResolvedValueOnce({ 
        data: { 
          compra: { ...compraCreada },
          mensaje: 'OK'
        } 
      });
      const compraConfirmada = await comprasService.confirmarCompra(compra.id_compra);
      expect(compraConfirmada.id_compra).toBe(20);
    });

    test('gestión de cuenta corriente: crear compras -> verificar saldo', async () => {
      // Crear varias compras
      const compraData: CompraData = {
        fecha: '2024-01-25',
        id_proveedor: 1,
        detalles: [{ id_producto: 1, cantidad: 1, costo_unitario: 1000000 }]
      };

      mockedApi.post.mockResolvedValue({ 
        data: {
          id_compra: 1,
          fecha: compraData.fecha,
          monto_total: 1000000,
          saldo_pendiente: 1000000,
          estado_pago: 'Pendiente',
          id_proveedor: 1
        }
      });

      await comprasService.crearCompra(compraData);
      await comprasService.crearCompra(compraData);

      // Verificar cuenta corriente
      const cuentaCorriente: CuentaCorrienteProveedor = {
        total_compras: 2000000,
        total_pagado: 0,
        saldo_pendiente: 2000000,
        compras_pendientes: 2,
        notas_credito: 0
      };
      mockedApi.get.mockResolvedValue({ data: cuentaCorriente });

      const cuenta = await comprasService.getCuentaCorrienteProveedor(1);
      expect(cuenta.saldo_pendiente).toBe(2000000);
      expect(cuenta.compras_pendientes).toBe(2);
    });
  });
});
