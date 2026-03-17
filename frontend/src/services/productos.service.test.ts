import api from './api';
import {
  productosService,
  ProductoParams,
  ProductoData,
  CategoriaData,
  PrecioPorListaData
} from './productos.service';
import {
  Producto,
  Categoria,
  UnidadMedida,
  ListaPrecio,
  PrecioPorLista,
  PaginatedResponse
} from '../types';

jest.mock('./api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('Productos Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getProductos', () => {
    const mockProductos: Producto[] = [
      {
        id_producto: 1,
        codigo_barra: '1234567890123',
        descripcion: 'Producto Test 1',
        stock_actual: 100,
        stock_minimo: 10,
        permite_stock_negativo: false,
        estado: true,
        id_categoria: 1,
        id_impuesto: 1
      },
      {
        id_producto: 2,
        codigo_barra: '9876543210987',
        descripcion: 'Producto Test 2',
        stock_actual: 50,
        stock_minimo: 5,
        permite_stock_negativo: true,
        estado: true,
        id_categoria: 2,
        id_impuesto: 1
      }
    ];

    const mockResponse: PaginatedResponse<Producto> = {
      count: 2,
      next: null,
      previous: null,
      results: mockProductos
    };

    test('debe obtener productos sin parámetros', async () => {
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      const result = await productosService.getProductos();

      expect(mockedApi.get).toHaveBeenCalledWith('/productos/', { params: undefined });
      expect(result).toEqual(mockResponse);
      expect(result.results).toHaveLength(2);
    });

    test('debe obtener productos con paginación', async () => {
      const params: ProductoParams = { page: 1, page_size: 10 };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await productosService.getProductos(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/productos/', { params });
    });

    test('debe buscar productos por término', async () => {
      const params: ProductoParams = { search: 'Test' };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await productosService.getProductos(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/productos/', { params });
    });

    test('debe filtrar productos activos', async () => {
      const params: ProductoParams = { estado: true };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await productosService.getProductos(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/productos/', { params });
    });

    test('debe filtrar productos por categoría', async () => {
      const params: ProductoParams = { id_categoria: 1 };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await productosService.getProductos(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/productos/', { params });
    });

    test('debe ordenar productos', async () => {
      const params: ProductoParams = { ordering: '-descripcion' };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await productosService.getProductos(params);

      expect(mockedApi.get).toHaveBeenCalledWith('/productos/', { params });
    });

    test('debe manejar respuesta vacía', async () => {
      const emptyResponse: PaginatedResponse<Producto> = {
        count: 0,
        next: null,
        previous: null,
        results: []
      };
      mockedApi.get.mockResolvedValue({ data: emptyResponse });

      const result = await productosService.getProductos();

      expect(result.results).toHaveLength(0);
    });
  });

  describe('getProductoById', () => {
    const mockProducto: Producto = {
      id_producto: 1,
      codigo_barra: '1234567890123',
      descripcion: 'Producto Detallado',
      stock_actual: 100,
      stock_minimo: 10,
      permite_stock_negativo: false,
      estado: true,
      id_categoria: 1,
      id_impuesto: 1,
      id_unidad_medida: 1
    };

    test('debe obtener producto por ID', async () => {
      mockedApi.get.mockResolvedValue({ data: mockProducto });

      const result = await productosService.getProductoById(1);

      expect(mockedApi.get).toHaveBeenCalledWith('/productos/1/');
      expect(result).toEqual(mockProducto);
      expect(result.id_producto).toBe(1);
    });

    test('debe manejar producto no encontrado', async () => {
      mockedApi.get.mockRejectedValue(new Error('Not Found'));

      await expect(productosService.getProductoById(999)).rejects.toThrow('Not Found');
    });
  });

  describe('buscarPorCodigoBarra', () => {
    const mockProducto: Producto = {
      id_producto: 1,
      codigo_barra: '1234567890123',
      descripcion: 'Producto Buscado',
      stock_actual: 100,
      stock_minimo: 10,
      permite_stock_negativo: false,
      estado: true,
      id_categoria: 1,
      id_impuesto: 1
    };

    test('debe buscar producto por código de barra', async () => {
      const mockResponse: PaginatedResponse<Producto> = {
        count: 1,
        next: null,
        previous: null,
        results: [mockProducto]
      };
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      const result = await productosService.buscarPorCodigoBarra('1234567890123');

      expect(mockedApi.get).toHaveBeenCalledWith('/productos/', {
        params: { search: '1234567890123' }
      });
      expect(result).toEqual(mockResponse);
    });

    test('debe retornar lista vacía si no encuentra producto', async () => {
      const emptyResponse: PaginatedResponse<Producto> = {
        count: 0,
        next: null,
        previous: null,
        results: []
      };
      mockedApi.get.mockResolvedValue({ data: emptyResponse });

      const result = await productosService.buscarPorCodigoBarra('9999999999999');

      expect(result.results).toHaveLength(0);
    });
  });

  describe('crearProducto', () => {
    const mockProductoData: ProductoData = {
      codigo_barra: '1111111111111',
      descripcion: 'Producto Nuevo',
      stock_minimo: 5,
      permite_stock_negativo: false,
      estado: true,
      id_categoria: 1,
      id_impuesto: 1
    };

    const mockProductoCreado: Producto = {
      id_producto: 3,
      ...mockProductoData,
      stock_actual: 0
    };

    test('debe crear producto nuevo', async () => {
      mockedApi.post.mockResolvedValue({ data: mockProductoCreado });

      const result = await productosService.crearProducto(mockProductoData);

      expect(mockedApi.post).toHaveBeenCalledWith('/productos/', mockProductoData);
      expect(result).toEqual(mockProductoCreado);
      expect(result.id_producto).toBe(3);
    });

    test('debe crear producto con unidad de medida', async () => {
      const dataConUnidad = { ...mockProductoData, id_unidad_medida: 1 };
      mockedApi.post.mockResolvedValue({
        data: { ...mockProductoCreado, id_unidad_medida: 1 }
      });

      const result = await productosService.crearProducto(dataConUnidad);

      expect(result.id_unidad_medida).toBe(1);
    });

    test('debe manejar error de validación', async () => {
      mockedApi.post.mockRejectedValue(new Error('Validation Error'));

      await expect(productosService.crearProducto(mockProductoData)).rejects.toThrow(
        'Validation Error'
      );
    });

    test('debe manejar error de código de barra duplicado', async () => {
      mockedApi.post.mockRejectedValue(new Error('Código de barra ya existe'));

      await expect(productosService.crearProducto(mockProductoData)).rejects.toThrow(
        'Código de barra ya existe'
      );
    });
  });

  describe('actualizarProducto', () => {
    const mockProductoActualizado: Producto = {
      id_producto: 1,
      codigo_barra: '1234567890123',
      descripcion: 'Producto Actualizado',
      stock_actual: 150,
      stock_minimo: 15,
      permite_stock_negativo: true,
      estado: true,
      id_categoria: 1,
      id_impuesto: 1
    };

    test('debe actualizar producto', async () => {
      const updateData: Partial<ProductoData> = {
        descripcion: 'Producto Actualizado',
        stock_minimo: 15
      };
      mockedApi.patch.mockResolvedValue({ data: mockProductoActualizado });

      const result = await productosService.actualizarProducto(1, updateData);

      expect(mockedApi.patch).toHaveBeenCalledWith('/productos/1/', updateData);
      expect(result).toEqual(mockProductoActualizado);
    });

    test('debe actualizar solo el stock mínimo', async () => {
      const updateData = { stock_minimo: 20 };
      mockedApi.patch.mockResolvedValue({
        data: { ...mockProductoActualizado, stock_minimo: 20 }
      });

      const result = await productosService.actualizarProducto(1, updateData);

      expect(result.stock_minimo).toBe(20);
    });

    test('debe manejar producto no encontrado', async () => {
      mockedApi.patch.mockRejectedValue(new Error('Not Found'));

      await expect(productosService.actualizarProducto(999, {})).rejects.toThrow('Not Found');
    });
  });

  describe('eliminarProducto', () => {
    test('debe eliminar producto', async () => {
      mockedApi.delete.mockResolvedValue({ data: null });

      await productosService.eliminarProducto(1);

      expect(mockedApi.delete).toHaveBeenCalledWith('/productos/1/');
    });

    test('debe manejar error al eliminar producto con ventas', async () => {
      mockedApi.delete.mockRejectedValue(new Error('Cannot delete product with sales'));

      await expect(productosService.eliminarProducto(1)).rejects.toThrow(
        'Cannot delete product with sales'
      );
    });
  });

  describe('toggleEstadoProducto', () => {
    const mockProducto: Producto = {
      id_producto: 1,
      codigo_barra: '1234567890123',
      descripcion: 'Producto Test',
      stock_actual: 100,
      stock_minimo: 10,
      permite_stock_negativo: false,
      estado: false,
      id_categoria: 1,
      id_impuesto: 1
    };

    test('debe activar producto', async () => {
      mockedApi.patch.mockResolvedValue({ data: { ...mockProducto, estado: true } });

      const result = await productosService.toggleEstadoProducto(1, true);

      expect(mockedApi.patch).toHaveBeenCalledWith('/productos/1/', { estado: true });
      expect(result.estado).toBe(true);
    });

    test('debe desactivar producto', async () => {
      mockedApi.patch.mockResolvedValue({ data: mockProducto });

      const result = await productosService.toggleEstadoProducto(1, false);

      expect(mockedApi.patch).toHaveBeenCalledWith('/productos/1/', { estado: false });
      expect(result.estado).toBe(false);
    });
  });

  describe('getCategorias', () => {
    const mockCategorias: Categoria[] = [
      { id_categoria: 1, nombre: 'Bebidas', estado: true },
      { id_categoria: 2, nombre: 'Alimentos', estado: true }
    ];

    const mockResponse: PaginatedResponse<Categoria> = {
      count: 2,
      next: null,
      previous: null,
      results: mockCategorias
    };

    test('debe obtener categorías sin filtros', async () => {
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      const result = await productosService.getCategorias();

      expect(mockedApi.get).toHaveBeenCalledWith('/categorias/', { params: undefined });
      expect(result).toEqual(mockResponse);
    });

    test('debe filtrar categorías activas', async () => {
      mockedApi.get.mockResolvedValue({ data: mockResponse });

      await productosService.getCategorias({ estado: true });

      expect(mockedApi.get).toHaveBeenCalledWith('/categorias/', { params: { estado: true } });
    });
  });

  describe('getCategoriaById', () => {
    const mockCategoria: Categoria = {
      id_categoria: 1,
      nombre: 'Bebidas',
      estado: true
    };

    test('debe obtener categoría por ID', async () => {
      mockedApi.get.mockResolvedValue({ data: mockCategoria });

      const result = await productosService.getCategoriaById(1);

      expect(mockedApi.get).toHaveBeenCalledWith('/categorias/1/');
      expect(result).toEqual(mockCategoria);
    });
  });

  describe('crearCategoria', () => {
    const mockCategoriaData: CategoriaData = {
      nombre: 'Nueva Categoría',
      estado: true
    };

    const mockCategoriaCreada: Categoria = {
      id_categoria: 3,
      ...mockCategoriaData
    };

    test('debe crear categoría', async () => {
      mockedApi.post.mockResolvedValue({ data: mockCategoriaCreada });

      const result = await productosService.crearCategoria(mockCategoriaData);

      expect(mockedApi.post).toHaveBeenCalledWith('/categorias/', mockCategoriaData);
      expect(result).toEqual(mockCategoriaCreada);
    });

    test('debe crear subcategoría', async () => {
      const subcategoriaData: CategoriaData = {
        ...mockCategoriaData,
        id_categoria_padre: 1
      };
      mockedApi.post.mockResolvedValue({
        data: { ...mockCategoriaCreada, id_categoria_padre: 1 }
      });

      const result = await productosService.crearCategoria(subcategoriaData);

      expect(result.id_categoria_padre).toBe(1);
    });
  });

  describe('actualizarCategoria', () => {
    const mockCategoriaActualizada: Categoria = {
      id_categoria: 1,
      nombre: 'Bebidas Actualizadas',
      estado: true
    };

    test('debe actualizar categoría', async () => {
      const updateData: Partial<CategoriaData> = { nombre: 'Bebidas Actualizadas' };
      mockedApi.patch.mockResolvedValue({ data: mockCategoriaActualizada });

      const result = await productosService.actualizarCategoria(1, updateData);

      expect(mockedApi.patch).toHaveBeenCalledWith('/categorias/1/', updateData);
      expect(result).toEqual(mockCategoriaActualizada);
    });
  });

  describe('eliminarCategoria', () => {
    test('debe eliminar categoría', async () => {
      mockedApi.delete.mockResolvedValue({ data: null });

      await productosService.eliminarCategoria(1);

      expect(mockedApi.delete).toHaveBeenCalledWith('/categorias/1/');
    });

    test('debe manejar error al eliminar categoría con productos', async () => {
      mockedApi.delete.mockRejectedValue(new Error('Category has products'));

      await expect(productosService.eliminarCategoria(1)).rejects.toThrow('Category has products');
    });
  });

  describe('getUnidadesMedida', () => {
    const mockUnidades: UnidadMedida[] = [
      { id_unidad_medida: 1, nombre: 'Unidad', abreviatura: 'UN', estado: true },
      { id_unidad_medida: 2, nombre: 'Kilo', abreviatura: 'KG', estado: true }
    ];

    test('debe obtener unidades de medida', async () => {
      mockedApi.get.mockResolvedValue({ data: mockUnidades });

      const result = await productosService.getUnidadesMedida();

      expect(mockedApi.get).toHaveBeenCalledWith('/unidades-medida/');
      expect(result).toEqual(mockUnidades);
    });
  });

  describe('getListasPrecios', () => {
    const mockListas: ListaPrecio[] = [
      { id_lista: 1, nombre_lista: 'Precio Público', moneda: 'PYG', estado: true },
      { id_lista: 2, nombre_lista: 'Precio Mayorista', moneda: 'PYG', estado: true }
    ];

    test('debe obtener listas de precios', async () => {
      mockedApi.get.mockResolvedValue({ data: mockListas });

      const result = await productosService.getListasPrecios();

      expect(mockedApi.get).toHaveBeenCalledWith('/listas-precios/');
      expect(result).toEqual(mockListas);
    });
  });

  describe('getPreciosPorProducto', () => {
    const mockPrecios: PrecioPorLista[] = [
      { id_precio: 1, precio_unitario: 10.00, fecha_vigencia: '2024-01-01', id_lista: 1, id_producto: 1 },
      { id_precio: 2, precio_unitario: 8.00, fecha_vigencia: '2024-01-01', id_lista: 2, id_producto: 1 }
    ];

    test('debe obtener precios por producto', async () => {
      mockedApi.get.mockResolvedValue({ data: mockPrecios });

      const result = await productosService.getPreciosPorProducto(1);

      expect(mockedApi.get).toHaveBeenCalledWith('/precios-por-lista/', {
        params: { id_producto: 1 }
      });
      expect(result).toEqual(mockPrecios);
    });
  });

  describe('actualizarPrecio', () => {
    const mockPrecio: PrecioPorLista = {
      id_precio: 1,
      precio_unitario: 15.00,
      fecha_vigencia: '2024-01-01',
      id_lista: 1,
      id_producto: 1
    };

    test('debe actualizar precio', async () => {
      mockedApi.patch.mockResolvedValue({ data: mockPrecio });

      const result = await productosService.actualizarPrecio(1, 15.00);

      expect(mockedApi.patch).toHaveBeenCalledWith('/precios-por-lista/1/', {
        precio_unitario: 15.00
      });
      expect(result).toEqual(mockPrecio);
    });
  });

  describe('crearPrecio', () => {
    const mockPrecioData: PrecioPorListaData = {
      precio_unitario: 12.00,
      id_lista: 1,
      id_producto: 1
    };

    const mockPrecio: PrecioPorLista = {
      id_precio: 3,
      ...mockPrecioData,
      fecha_vigencia: '2024-01-01'
    };

    test('debe crear precio nuevo', async () => {
      mockedApi.post.mockResolvedValue({ data: mockPrecio });

      const result = await productosService.crearPrecio(mockPrecioData);

      expect(mockedApi.post).toHaveBeenCalledWith('/precios-por-lista/', mockPrecioData);
      expect(result).toEqual(mockPrecio);
    });
  });

  describe('Integration scenarios', () => {
    test('flujo completo: crear producto -> agregar precio -> actualizar', async () => {
      const productoData: ProductoData = {
        codigo_barra: '7777777777777',
        descripcion: 'Producto Integración',
        stock_minimo: 10,
        permite_stock_negativo: false,
        estado: true,
        id_categoria: 1,
        id_impuesto: 1
      };

      const productoCreado: Producto = {
        id_producto: 10,
        ...productoData,
        stock_actual: 0
      };

      const precioData: PrecioPorListaData = {
        precio_unitario: 25.00,
        id_lista: 1,
        id_producto: 10
      };

      const precioCreado: PrecioPorLista = {
        id_precio: 5,
        ...precioData,
        fecha_vigencia: '2024-01-01'
      };

      // Crear producto
      mockedApi.post.mockResolvedValueOnce({ data: productoCreado });
      const created = await productosService.crearProducto(productoData);
      expect(created.id_producto).toBe(10);

      // Agregar precio
      mockedApi.post.mockResolvedValueOnce({ data: precioCreado });
      const precio = await productosService.crearPrecio(precioData);
      expect(precio.id_producto).toBe(10);

      // Actualizar producto
      mockedApi.patch.mockResolvedValueOnce({
        data: { ...productoCreado, descripcion: 'Actualizado' }
      });
      const updated = await productosService.actualizarProducto(10, {
        descripcion: 'Actualizado'
      });
      expect(updated.descripcion).toBe('Actualizado');
    });
  });
});
