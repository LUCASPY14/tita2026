import api from './api';
import { inventarioService, StockItem, MovimientoStock } from './inventario.service';
import type { PaginatedResponse } from '../types';

vi.mock('./api');
const mockedApi = api as vi.Mocked<typeof api>;

const mockStockItem: StockItem = {
  id_stock: 1,
  id_producto: 5,
  cantidad: 100,
  fecha_ultima_actualizacion: '2026-05-12T10:00:00Z',
  producto_nombre: 'Gaseosa 500ml',
  producto_categoria: 'Bebidas',
};

const mockMovimiento: MovimientoStock = {
  id_movimiento_stock: 1,
  fecha_hora: '2026-05-12T09:00:00Z',
  tipo_movimiento: 'Ingreso',
  motivo: 'Compra proveedor',
  cantidad: 50,
  stock_resultante: 100,
  id_producto: 5,
  producto_nombre: 'Gaseosa 500ml',
  referencia_documento: 'COMP-001',
};

const mockPagedStock: PaginatedResponse<StockItem> = {
  count: 1,
  next: null,
  previous: null,
  results: [mockStockItem],
};

const mockPagedMovimientos: PaginatedResponse<MovimientoStock> = {
  count: 1,
  next: null,
  previous: null,
  results: [mockMovimiento],
};

describe('Inventario Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getStock', () => {
    it('retorna stock paginado sin parametros', async () => {
      mockedApi.get.mockResolvedValue({ data: mockPagedStock });

      const result = await inventarioService.getStock();

      expect(mockedApi.get).toHaveBeenCalledWith('/stock/', { params: undefined });
      expect(result.count).toBe(1);
      expect(result.results[0].cantidad).toBe(100);
    });

    it('filtra por id_producto', async () => {
      mockedApi.get.mockResolvedValue({ data: mockPagedStock });

      await inventarioService.getStock({ id_producto: 5 });

      expect(mockedApi.get).toHaveBeenCalledWith('/stock/', {
        params: { id_producto: 5 },
      });
    });

    it('soporta busqueda por nombre', async () => {
      mockedApi.get.mockResolvedValue({ data: mockPagedStock });

      await inventarioService.getStock({ search: 'Gaseosa' });

      expect(mockedApi.get).toHaveBeenCalledWith('/stock/', {
        params: { search: 'Gaseosa' },
      });
    });

    it('maneja error de red', async () => {
      mockedApi.get.mockRejectedValue(new Error('Network Error'));

      await expect(inventarioService.getStock()).rejects.toThrow('Network Error');
    });
  });

  describe('getStockByProducto', () => {
    it('retorna stock de un producto especifico', async () => {
      mockedApi.get.mockResolvedValue({ data: { ...mockPagedStock } });

      const result = await inventarioService.getStockByProducto(5);

      expect(mockedApi.get).toHaveBeenCalledWith('/stock/', {
        params: { id_producto: 5, page_size: 1 },
      });
      expect(result.id_producto).toBe(5);
      expect(result.cantidad).toBe(100);
    });

    it('lanza error cuando no hay stock para el producto', async () => {
      mockedApi.get.mockResolvedValue({
        data: { count: 0, results: [], next: null, previous: null },
      });

      await expect(inventarioService.getStockByProducto(999)).rejects.toThrow(
        'Sin registro de stock para este producto'
      );
    });
  });

  describe('getMovimientos', () => {
    it('retorna movimientos de stock sin parametros', async () => {
      mockedApi.get.mockResolvedValue({ data: mockPagedMovimientos });

      const result = await inventarioService.getMovimientos();

      expect(mockedApi.get).toHaveBeenCalledWith('/movimientos-stock/', {
        params: undefined,
      });
      expect(result.results[0].tipo_movimiento).toBe('Ingreso');
    });

    it('filtra por tipo de movimiento', async () => {
      mockedApi.get.mockResolvedValue({ data: mockPagedMovimientos });

      await inventarioService.getMovimientos({ tipo_movimiento: 'Egreso' });

      expect(mockedApi.get).toHaveBeenCalledWith('/movimientos-stock/', {
        params: { tipo_movimiento: 'Egreso' },
      });
    });

    it('filtra por producto', async () => {
      mockedApi.get.mockResolvedValue({ data: mockPagedMovimientos });

      await inventarioService.getMovimientos({ id_producto: 5, page: 1, page_size: 20 });

      expect(mockedApi.get).toHaveBeenCalledWith('/movimientos-stock/', {
        params: { id_producto: 5, page: 1, page_size: 20 },
      });
    });
  });
});
