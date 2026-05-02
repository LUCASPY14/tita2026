import api from './api';
import { posService } from './pos.service';
import type { Producto, Categoria, MedioPago, Venta, VentaData, PaginatedResponse } from '../types';

vi.mock('./api');
const mockedApi = api as vi.Mocked<typeof api>;

describe('POS Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ============================================================
  // PRODUCTOS
  // ============================================================

  describe('Productos', () => {
    const mockProducto: Producto = {
      id_producto: 1,
      descripcion: 'Hamburguesa completa',
      codigo_barra: '12345',
      precio: 5000,
      stock_actual: 50,
      stock_minimo: 10,
      id_categoria: 1,
      categoria_nombre: 'Comidas',
      id_impuesto: 1,
      permite_stock_negativo: false,
      estado: true,
    };

    describe('getProductos', () => {
      it('debería obtener productos sin parámetros', async () => {
        const mockResponse: PaginatedResponse<Producto> = {
          count: 1,
          next: null,
          previous: null,
          results: [mockProducto],
        };

        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await posService.getProductos();

        expect(mockedApi.get).toHaveBeenCalledWith('/productos/', { params: undefined });
        expect(result).toEqual(mockResponse);
      });

      it('debería obtener productos con parámetros de búsqueda', async () => {
        const mockResponse: PaginatedResponse<Producto> = {
          count: 1,
          next: null,
          previous: null,
          results: [mockProducto],
        };

        const params = {
          search: 'hamburguesa',
          categoria: 1,
          estado: true,
        };

        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await posService.getProductos(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/productos/', { params });
        expect(result).toEqual(mockResponse);
      });

      it('debería manejar errores al obtener productos', async () => {
        mockedApi.get.mockRejectedValue(new Error('Network error'));

        await expect(posService.getProductos()).rejects.toThrow('Network error');
      });

      it('debería obtener productos solo activos', async () => {
        const mockResponse: PaginatedResponse<Producto> = {
          count: 1,
          next: null,
          previous: null,
          results: [mockProducto],
        };

        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await posService.getProductos({ estado: true });

        expect(mockedApi.get).toHaveBeenCalledWith('/productos/', { 
          params: { estado: true } 
        });
      });

      it('debería obtener productos por categoría', async () => {
        const mockResponse: PaginatedResponse<Producto> = {
          count: 1,
          next: null,
          previous: null,
          results: [mockProducto],
        };

        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await posService.getProductos({ id_categoria: 1 });

        expect(mockedApi.get).toHaveBeenCalledWith('/productos/', { 
          params: { id_categoria: 1 } 
        });
      });
    });

    describe('getProductoById', () => {
      it('debería obtener un producto por ID', async () => {
        mockedApi.get.mockResolvedValue({ data: mockProducto });

        const result = await posService.getProductoById(1);

        expect(mockedApi.get).toHaveBeenCalledWith('/productos/1/');
        expect(result).toEqual(mockProducto);
      });

      it('debería manejar errores al obtener producto por ID', async () => {
        mockedApi.get.mockRejectedValue(new Error('Not found'));

        await expect(posService.getProductoById(999)).rejects.toThrow('Not found');
      });
    });

    describe('buscarProductoPorCodigo', () => {
      it('debería buscar producto por código de barras', async () => {
        const mockResponse: PaginatedResponse<Producto> = {
          count: 1,
          next: null,
          previous: null,
          results: [mockProducto],
        };

        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await posService.buscarProductoPorCodigo('12345');

        expect(mockedApi.get).toHaveBeenCalledWith('/productos/', {
          params: { search: '12345', estado: true },
        });
        expect(result).toEqual(mockProducto);
      });

      it('debería manejar errores al buscar por código', async () => {
        mockedApi.get.mockRejectedValue(new Error('Producto no encontrado'));

        await expect(posService.buscarProductoPorCodigo('99999')).rejects.toThrow('Producto no encontrado');
      });

      it('debería buscar producto con código vacío', async () => {
        const mockResponse: PaginatedResponse<Producto> = {
          count: 0,
          next: null,
          previous: null,
          results: [],
        };

        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await expect(posService.buscarProductoPorCodigo('')).rejects.toThrow('Producto no encontrado');

        expect(mockedApi.get).toHaveBeenCalledWith('/productos/', {
          params: { search: '', estado: true },
        });
      });
    });
  });

  // ============================================================
  // CATEGORÍAS
  // ============================================================

  describe('Categorías', () => {
    const mockCategoria: Categoria = {
      id_categoria: 1,
      nombre: 'Comidas',
      estado: true,
    };

    describe('getCategorias', () => {
      it('debería obtener categorías sin parámetros', async () => {
        const mockResponse: PaginatedResponse<Categoria> = {
          count: 1,
          next: null,
          previous: null,
          results: [mockCategoria],
        };

        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await posService.getCategorias();

        expect(mockedApi.get).toHaveBeenCalledWith('/categorias/', { params: undefined });
        expect(result).toEqual(mockResponse);
      });

      it('debería obtener categorías con parámetros', async () => {
        const mockResponse: PaginatedResponse<Categoria> = {
          count: 1,
          next: null,
          previous: null,
          results: [mockCategoria],
        };

        const params = {
          search: 'comida',
          estado: true,
        };

        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await posService.getCategorias(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/categorias/', { params });
        expect(result).toEqual(mockResponse);
      });

      it('debería manejar errores al obtener categorías', async () => {
        mockedApi.get.mockRejectedValue(new Error('Network error'));

        await expect(posService.getCategorias()).rejects.toThrow('Network error');
      });

      it('debería obtener solo categorías activas', async () => {
        const mockResponse: PaginatedResponse<Categoria> = {
          count: 1,
          next: null,
          previous: null,
          results: [mockCategoria],
        };

        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await posService.getCategorias({ estado: true });

        expect(mockedApi.get).toHaveBeenCalledWith('/categorias/', { 
          params: { estado: true } 
        });
      });
    });
  });

  // ============================================================
  // MEDIOS DE PAGO
  // ============================================================

  describe('Medios de Pago', () => {
    const mockMedioPago: MedioPago = {
      id_medio_pago: 1,
      nombre: 'Efectivo',
      genera_comision: false,
      estado: true,
    };

    describe('getMediosPago', () => {
      it('debería obtener medios de pago activos', async () => {
        const mockResponse: PaginatedResponse<MedioPago> = {
          count: 1,
          next: null,
          previous: null,
          results: [mockMedioPago],
        };

        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await posService.getMediosPago();

        expect(mockedApi.get).toHaveBeenCalledWith('/medios-pago/', {
          params: { estado: true, page_size: 100 },
        });
        expect(result).toEqual([mockMedioPago]);
      });

      it('debería manejar errores al obtener medios de pago', async () => {
        mockedApi.get.mockRejectedValue(new Error('Network error'));

        await expect(posService.getMediosPago()).rejects.toThrow('Network error');
      });

      it('debería devolver array vacío si no hay medios de pago', async () => {
        const mockResponse: PaginatedResponse<MedioPago> = {
          count: 0,
          next: null,
          previous: null,
          results: [],
        };

        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await posService.getMediosPago();

        expect(result).toEqual([]);
      });
    });
  });

  // ============================================================
  // VENTAS
  // ============================================================

  describe('Ventas', () => {
    const mockVenta: Venta = {
      id_venta: 1,
      nro_factura_venta: 1,
      fecha: '2024-01-15T10:30:00Z',
      id_cliente: 1,
      cliente_nombre: 'Juan Pérez',
      monto_total: 15000,
      saldo_pendiente: 0,
      estado_pago: 'Pagado',
      estado: 'Completada',
      tipo_venta: 'Contado',
    };

    describe('crearVenta', () => {
      it('debería crear una venta exitosamente', async () => {
        const ventaData: VentaData = {
          id_cliente: 1,
          tipo_venta: 'Contado',
          id_medio_pago: 1,
          detalles: [
            { id_producto: 1, cantidad: 2, precio_unitario: 5000 },
            { id_producto: 2, cantidad: 1, precio_unitario: 5000 },
          ],
        };

        mockedApi.post.mockResolvedValue({ data: mockVenta });

        const result = await posService.crearVenta(ventaData);

        expect(mockedApi.post).toHaveBeenCalledWith('/ventas/', ventaData);
        expect(result).toEqual(mockVenta);
      });

      it('debería manejar errores al crear venta', async () => {
        const ventaData: VentaData = {
          id_cliente: 1,
          tipo_venta: 'Contado',
          detalles: [],
        };

        mockedApi.post.mockRejectedValue(new Error('Validation error'));

        await expect(posService.crearVenta(ventaData)).rejects.toThrow('Validation error');
      });

      it('debería crear venta a crédito', async () => {
        const ventaData: VentaData = {
          id_cliente: 1,
          tipo_venta: 'Credito',
          detalles: [{ id_producto: 1, cantidad: 1, precio_unitario: 10000 }],
        };

        const ventaCredito = { ...mockVenta, tipo_venta: 'Credito', saldo_pendiente: 10000 };
        mockedApi.post.mockResolvedValue({ data: ventaCredito });

        const result = await posService.crearVenta(ventaData);

        expect(result.tipo_venta).toBe('Credito');
        expect(result.saldo_pendiente).toBe(10000);
      });

      it('debería crear venta con número de comprobante', async () => {
        const ventaData: VentaData = {
          id_cliente: 1,
          tipo_venta: 'Contado',
          id_medio_pago: 1,
          numero_comprobante: 'COMP-001',
          detalles: [{ id_producto: 1, cantidad: 1, precio_unitario: 5000 }],
        };

        const ventaConComprobante = mockVenta;
        mockedApi.post.mockResolvedValue({ data: ventaConComprobante });

        const result = await posService.crearVenta(ventaData);

        expect(result.id_venta).toBe(1);
      });
    });

    describe('getVentas', () => {
      it('debería obtener ventas sin parámetros', async () => {
        const mockResponse: PaginatedResponse<Venta> = {
          count: 1,
          next: null,
          previous: null,
          results: [mockVenta],
        };

        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await posService.getVentas();

        expect(mockedApi.get).toHaveBeenCalledWith('/ventas/', { params: undefined });
        expect(result).toEqual(mockResponse);
      });

      it('debería obtener ventas con filtros', async () => {
        const mockResponse: PaginatedResponse<Venta> = {
          count: 1,
          next: null,
          previous: null,
          results: [mockVenta],
        };

        const params = {
          fecha: '2024-01-15',
          estado: 'Completada',
          tipo_venta: 'Contado',
        };

        mockedApi.get.mockResolvedValue({ data: mockResponse });

        const result = await posService.getVentas(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/ventas/', { params });
        expect(result).toEqual(mockResponse);
      });

      it('debería manejar errores al obtener ventas', async () => {
        mockedApi.get.mockRejectedValue(new Error('Network error'));

        await expect(posService.getVentas()).rejects.toThrow('Network error');
      });

      it('debería obtener ventas por tipo de venta', async () => {
        const mockResponse: PaginatedResponse<Venta> = {
          count: 1,
          next: null,
          previous: null,
          results: [mockVenta],
        };

        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await posService.getVentas({ tipo_venta: 'Contado' });

        expect(mockedApi.get).toHaveBeenCalledWith('/ventas/', { 
          params: { tipo_venta: 'Contado' } 
        });
      });

      it('debería obtener ventas por fecha', async () => {
        const mockResponse: PaginatedResponse<Venta> = {
          count: 1,
          next: null,
          previous: null,
          results: [mockVenta],
        };

        const params = {
          fecha: '2024-01-15',
        };

        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await posService.getVentas(params);

        expect(mockedApi.get).toHaveBeenCalledWith('/ventas/', { params });
      });

      it('debería obtener ventas por estado', async () => {
        const mockResponse: PaginatedResponse<Venta> = {
          count: 1,
          next: null,
          previous: null,
          results: [mockVenta],
        };

        mockedApi.get.mockResolvedValue({ data: mockResponse });

        await posService.getVentas({ estado: 'Completada' });

        expect(mockedApi.get).toHaveBeenCalledWith('/ventas/', { 
          params: { estado: 'Completada' } 
        });
      });
    });

    describe('getVentaById', () => {
      it('debería obtener una venta por ID', async () => {
        mockedApi.get.mockResolvedValue({ data: mockVenta });

        const result = await posService.getVentaById(1);

        expect(mockedApi.get).toHaveBeenCalledWith('/ventas/1/');
        expect(result).toEqual(mockVenta);
      });

      it('debería manejar errores al obtener venta por ID', async () => {
        mockedApi.get.mockRejectedValue(new Error('Not found'));

        await expect(posService.getVentaById(999)).rejects.toThrow('Not found');
      });
    });
  });

  // ============================================================
  // INTEGRATION TESTS
  // ============================================================

  describe('Integration Scenarios', () => {
    it('debería simular flujo completo de venta: buscar producto → crear venta', async () => {
      const mockProducto: Producto = {
        id_producto: 1,
        descripcion: 'Hamburguesa completa',
        codigo_barra: '12345',
        precio: 5000,
        stock_actual: 50,
        stock_minimo: 10,
        id_categoria: 1,
        categoria_nombre: 'Comidas',
        id_impuesto: 1,
        permite_stock_negativo: false,
        estado: true,
      };

      const mockVenta: Venta = {
        id_venta: 1,
        nro_factura_venta: 1,
        fecha: '2024-01-15T10:30:00Z',
        id_cliente: 1,
        cliente_nombre: 'Juan Pérez',
        monto_total: 5000,
        saldo_pendiente: 0,
        estado_pago: 'Pagado',
        estado: 'Completada',
        tipo_venta: 'Contado',
      };

      // Buscar producto
      mockedApi.get.mockResolvedValueOnce({ 
        data: { 
          count: 1, 
          next: null, 
          previous: null, 
          results: [mockProducto] 
        } 
      });
      const producto = await posService.buscarProductoPorCodigo('12345');
      expect(producto.id_producto).toBe(1);

      // Crear venta
      mockedApi.post.mockResolvedValueOnce({ data: mockVenta });
      const venta = await posService.crearVenta({
        id_cliente: 1,
        tipo_venta: 'Contado',
        id_medio_pago: 1,
        detalles: [{ id_producto: producto.id_producto, cantidad: 1, precio_unitario: producto.precio || 0 }],
      });

      expect(venta.id_venta).toBe(1);
      expect(venta.monto_total).toBe(5000);
    });

    it('debería simular flujo: obtener categorías → filtrar productos por categoría', async () => {
      const mockCategoria: Categoria = {
        id_categoria: 1,
        nombre: 'Comidas',
        estado: true,
      };

      const mockProductos: PaginatedResponse<Producto> = {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id_producto: 1,
            descripcion: 'Hamburguesa completa',
            codigo_barra: '12345',
            precio: 5000,
            stock_actual: 50,
            stock_minimo: 10,
            id_categoria: 1,
            categoria_nombre: 'Comidas',
            id_impuesto: 1,
            permite_stock_negativo: false,
            estado: true,
          },
        ],
      };

      // Obtener categorías
      mockedApi.get.mockResolvedValueOnce({
        data: { count: 1, next: null, previous: null, results: [mockCategoria] },
      });
      const categorias = await posService.getCategorias();
      const categoria = categorias.results[0];

      // Filtrar productos por categoría
      mockedApi.get.mockResolvedValueOnce({ data: mockProductos });
      const productos = await posService.getProductos({ id_categoria: categoria.id_categoria });

      expect(productos.results.length).toBe(1);
      expect(productos.results[0].id_categoria).toBe(categoria.id_categoria);
    });
  });
});
