import api from './api';
import {
  clientesService,
  ClienteParams,
  ClienteData,
} from './clientes.service';
import {
  Cliente,
  TipoCliente,
  CuentaCorriente,
  PaginatedResponse,
} from '../types';
jest.mock('./api');
const mockedApi = api as jest.Mocked<typeof api>;
describe('Clientes Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getClientes', () => {
    const mockClientes: Cliente[] = [
      {
        id_cliente: 1,
        nombres: 'Juan',
        apellidos: 'Pérez',
        razon_social: 'Juan Pérez',
        ruc_ci: '1234567890',
        telefono: '0981234567',
        email: 'juan@example.com',
        estado: true,
        fecha_registro: '2024-01-01',
        id_tipo_cliente: 1,
        id_lista: 1,
      },
      {
        id_cliente: 2,
        nombres: 'María',
        apellidos: 'López',
        razon_social: 'María López',
        ruc_ci: '9876543210',
        telefono: '0987654321',
        email: 'maria@example.com',
        estado: true,
        fecha_registro: '2024-01-01',
        id_tipo_cliente: 2,
        id_lista: 1,
      },
    ];
    const mockResponse: PaginatedResponse<Cliente> = {
      count: 2,
      next: null,
      previous: null,
      results: mockClientes,
    };
    test('debe obtener clientes sin parámetros', async () => {
      mockedApi.get.mockResolvedValue({ data: mockResponse });
      const result = await clientesService.getClientes();
      expect(mockedApi.get).toHaveBeenCalledWith('/clientes/', {
        params: undefined,
      });
      expect(result).toEqual(mockResponse);
      expect(result.results).toHaveLength(2);
    });

    test('debe obtener clientes con paginación', async () => {
      const params: ClienteParams = { page: 1, page_size: 10 };
      mockedApi.get.mockResolvedValue({ data: mockResponse });
      await clientesService.getClientes(params);
      expect(mockedApi.get).toHaveBeenCalledWith('/clientes/', { params });
    });

    test('debe buscar clientes por término de búsqueda', async () => {
      const params: ClienteParams = { search: 'Juan' };
      mockedApi.get.mockResolvedValue({ data: mockResponse });
      await clientesService.getClientes(params);
      expect(mockedApi.get).toHaveBeenCalledWith('/clientes/', { params });
    });

    test('debe filtrar clientes activos', async () => {
      const params: ClienteParams = { estado: true };
      mockedApi.get.mockResolvedValue({ data: mockResponse });
      await clientesService.getClientes(params);
      expect(mockedApi.get).toHaveBeenCalledWith('/clientes/', { params });
    });

    test('debe filtrar clientes por tipo', async () => {
      const params: ClienteParams = { id_tipo_cliente: 1 };
      mockedApi.get.mockResolvedValue({ data: mockResponse });
      await clientesService.getClientes(params);
      expect(mockedApi.get).toHaveBeenCalledWith('/clientes/', { params });
    });

    test('debe ordenar clientes', async () => {
      const params: ClienteParams = { ordering: '-nombres' };
      mockedApi.get.mockResolvedValue({ data: mockResponse });
      await clientesService.getClientes(params);
      expect(mockedApi.get).toHaveBeenCalledWith('/clientes/', { params });
    });

    test('debe manejar respuesta vacía', async () => {
      const emptyResponse: PaginatedResponse<Cliente> = {
        count: 0,
        next: null,
        previous: null,
        results: [],
      };
      mockedApi.get.mockResolvedValue({ data: emptyResponse });
      const result = await clientesService.getClientes();
      expect(result.results).toHaveLength(0);
    });
  });

  describe('getClienteById', () => {
    const mockCliente: Cliente = {
      id_cliente: 1,
      nombres: 'Juan',
      apellidos: 'Pérez',
      razon_social: 'Juan Pérez',
      ruc_ci: '1234567890',
      direccion: 'Calle Test 123',
      ciudad: 'Asunción',
      telefono: '0981234567',
      email: 'juan@example.com',
      limite_credito: 1000.0,
      estado: true,
      fecha_registro: '2024-01-01',
      id_tipo_cliente: 1,
      id_lista: 1,
    };
    test('debe obtener cliente por ID', async () => {
      mockedApi.get.mockResolvedValue({ data: mockCliente });
      const result = await clientesService.getClienteById(1);
      expect(mockedApi.get).toHaveBeenCalledWith('/clientes/1/');
      expect(result).toEqual(mockCliente);
      expect(result.id_cliente).toBe(1);
    });

    test('debe manejar cliente no encontrado', async () => {
      mockedApi.get.mockRejectedValue(new Error('Not Found'));
      await expect(clientesService.getClienteById(999)).rejects.toThrow(
        'Not Found'
      );
    });
  });

  describe('buscarPorRucCi', () => {
    const mockClientes: Cliente[] = [
      {
        id_cliente: 1,
        nombres: 'Juan',
        apellidos: 'Pérez',
        razon_social: 'Juan Pérez',
        ruc_ci: '1234567890',
        estado: true,
        fecha_registro: '2024-01-01',
        id_tipo_cliente: 1,
        id_lista: 1,
      },
    ];
    test('debe buscar cliente por RUC/CI', async () => {
      const mockResponse: PaginatedResponse<Cliente> = {
        count: 1,
        next: null,
        previous: null,
        results: mockClientes,
      };
      mockedApi.get.mockResolvedValue({ data: mockResponse });
      const result = await clientesService.buscarPorRucCi('1234567890');
      expect(mockedApi.get).toHaveBeenCalledWith('/clientes/', {
        params: { search: '1234567890' },
      });
      expect(result).toEqual(mockClientes);
      expect(result).toHaveLength(1);
    });

    test('debe retornar array vacío si no encuentra cliente', async () => {
      const emptyResponse: PaginatedResponse<Cliente> = {
        count: 0,
        next: null,
        previous: null,
        results: [],
      };
      mockedApi.get.mockResolvedValue({ data: emptyResponse });
      const result = await clientesService.buscarPorRucCi('9999999999');
      expect(result).toEqual([]);
    });
  });

  describe('crearCliente', () => {
    const mockClienteData: ClienteData = {
      nombres: 'Pedro',
      apellidos: 'González',
      ruc_ci: '5555555555',
      telefono: '0985555555',
      email: 'pedro@example.com',
      estado: true,
      id_lista: 1,
      id_tipo_cliente: 1,
    };
    const mockClienteCreado: Cliente = {
      id_cliente: 3,
      nombres: 'Pedro',
      apellidos: 'González',
      razon_social: 'Pedro González',
      ruc_ci: '5555555555',
      telefono: '0985555555',
      email: 'pedro@example.com',
      estado: true,
      fecha_registro: '2024-01-15',
      id_lista: 1,
      id_tipo_cliente: 1,
    };
    test('debe crear cliente nuevo', async () => {
      mockedApi.post.mockResolvedValue({ data: mockClienteCreado });
      const result = await clientesService.crearCliente(mockClienteData);
      expect(mockedApi.post).toHaveBeenCalledWith(
        '/clientes/',
        mockClienteData
      );
      expect(result).toEqual(mockClienteCreado);
      expect(result.id_cliente).toBe(3);
    });

    test('debe crear cliente con todos los campos opcionales', async () => {
      const fullData: ClienteData = {
        ...mockClienteData,
        razon_social: 'Pedro González S.A.',
        direccion: 'Av. Principal 456',
        ciudad: 'Ciudad del Este',
        limite_credito: 5000.0,
      };
      mockedApi.post.mockResolvedValue({
        data: { id_cliente: 4, ...fullData, fecha_registro: '2024-01-15' },
      });
      const result = await clientesService.crearCliente(fullData);
      expect(result.razon_social).toBe('Pedro González S.A.');
      expect(result.limite_credito).toBe(5000.0);
    });

    test('debe manejar error de validación', async () => {
      mockedApi.post.mockRejectedValue(new Error('Validation Error'));
      await expect(
        clientesService.crearCliente(mockClienteData)
      ).rejects.toThrow('Validation Error');
    });

    test('debe manejar error de RUC/CI duplicado', async () => {
      mockedApi.post.mockRejectedValue(new Error('RUC/CI ya existe'));
      await expect(
        clientesService.crearCliente(mockClienteData)
      ).rejects.toThrow('RUC/CI ya existe');
    });
  });

  describe('actualizarCliente', () => {
    const mockClienteActualizado: Cliente = {
      id_cliente: 1,
      nombres: 'Juan Carlos',
      apellidos: 'Pérez',
      razon_social: 'Juan Carlos Pérez',
      ruc_ci: '1234567890',
      telefono: '0981111111',
      email: 'juancarlos@example.com',
      estado: true,
      fecha_registro: '2024-01-01',
      id_tipo_cliente: 1,
      id_lista: 1,
    };
    test('debe actualizar cliente', async () => {
      const updateData: Partial<ClienteData> = {
        nombres: 'Juan Carlos',
        telefono: '0981111111',
      };
      mockedApi.patch.mockResolvedValue({ data: mockClienteActualizado });
      const result = await clientesService.actualizarCliente(1, updateData);
      expect(mockedApi.patch).toHaveBeenCalledWith('/clientes/1/', updateData);
      expect(result).toEqual(mockClienteActualizado);
      expect(result.nombres).toBe('Juan Carlos');
    });

    test('debe actualizar solo el email', async () => {
      const updateData = { email: 'nuevo@example.com' };
      mockedApi.patch.mockResolvedValue({
        data: { ...mockClienteActualizado, email: 'nuevo@example.com' },
      });
      const result = await clientesService.actualizarCliente(1, updateData);
      expect(result.email).toBe('nuevo@example.com');
    });

    test('debe manejar cliente no encontrado', async () => {
      mockedApi.patch.mockRejectedValue(new Error('Not Found'));
      await expect(clientesService.actualizarCliente(999, {})).rejects.toThrow(
        'Not Found'
      );
    });
  });

  describe('eliminarCliente', () => {
    test('debe eliminar cliente', async () => {
      mockedApi.delete.mockResolvedValue({ data: null });
      await clientesService.eliminarCliente(1);
      expect(mockedApi.delete).toHaveBeenCalledWith('/clientes/1/');
    });

    test('debe manejar error al eliminar cliente con ventas asociadas', async () => {
      mockedApi.delete.mockRejectedValue(
        new Error('Cannot delete client with sales')
      );
      await expect(clientesService.eliminarCliente(1)).rejects.toThrow(
        'Cannot delete client with sales'
      );
    });
  });

  describe('toggleEstadoCliente', () => {
    const mockCliente: Cliente = {
      id_cliente: 1,
      nombres: 'Juan',
      apellidos: 'Pérez',
      razon_social: 'Juan Pérez',
      ruc_ci: '1234567890',
      estado: false,
      fecha_registro: '2024-01-01',
      id_tipo_cliente: 1,
      id_lista: 1,
    };
    test('debe activar cliente', async () => {
      mockedApi.patch.mockResolvedValue({
        data: { ...mockCliente, estado: true },
      });
      const result = await clientesService.toggleEstadoCliente(1, true);
      expect(mockedApi.patch).toHaveBeenCalledWith('/clientes/1/', {
        estado: true,
      });
      expect(result.estado).toBe(true);
    });

    test('debe desactivar cliente', async () => {
      mockedApi.patch.mockResolvedValue({ data: mockCliente });
      const result = await clientesService.toggleEstadoCliente(1, false);
      expect(mockedApi.patch).toHaveBeenCalledWith('/clientes/1/', {
        estado: false,
      });
      expect(result.estado).toBe(false);
    });
  });

  describe('getCuentaCorriente', () => {
    const mockCuentaCorriente: CuentaCorriente = {
      total_debe: 1500.0,
      total_haber: 1000.0,
      saldo_neto: 500.0,
      limite_credito: 1000.0,
      credito_disponible: 500.0,
      porcentaje_usado: 50,
      cantidad_facturas_pendientes: 3,
      cantidad_notas_credito: 1,
    };
    test('debe obtener cuenta corriente de cliente', async () => {
      mockedApi.get.mockResolvedValue({ data: mockCuentaCorriente });
      const result = await clientesService.getCuentaCorriente(1);
      expect(mockedApi.get).toHaveBeenCalledWith(
        '/clientes/1/cuenta_corriente/'
      );
      expect(result).toEqual(mockCuentaCorriente);
    });

    test('debe manejar cliente sin cuenta corriente', async () => {
      mockedApi.get.mockRejectedValue(new Error('No tiene cuenta corriente'));
      await expect(clientesService.getCuentaCorriente(1)).rejects.toThrow(
        'No tiene cuenta corriente'
      );
    });
  });

  describe('getTiposCliente', () => {
    const mockTipos: TipoCliente[] = [
      { id_tipo_cliente: 1, nombre: 'Mayorista', estado: true },
      { id_tipo_cliente: 2, nombre: 'Minorista', estado: true },
    ];
    test('debe obtener tipos de cliente', async () => {
      const mockResponse: PaginatedResponse<TipoCliente> = {
        count: 2,
        next: null,
        previous: null,
        results: mockTipos,
      };
      mockedApi.get.mockResolvedValue({ data: mockResponse });
      const result = await clientesService.getTiposCliente();
      expect(mockedApi.get).toHaveBeenCalledWith('/tipos-cliente/', {
        params: { estado: true, page_size: 100 },
      });
      expect(result).toEqual(mockTipos);
      expect(result).toHaveLength(2);
    });

    test('debe retornar array vacío si no hay tipos', async () => {
      const emptyResponse: PaginatedResponse<TipoCliente> = {
        count: 0,
        next: null,
        previous: null,
        results: [],
      };
      mockedApi.get.mockResolvedValue({ data: emptyResponse });
      const result = await clientesService.getTiposCliente();
      expect(result).toEqual([]);
    });
  });

  describe('getEstadisticas', () => {
    const mockEstadisticas = {
      total: 100,
      activos: 85,
      inactivos: 15,
      con_credito: 30,
      sin_credito: 70,
    };
    test('debe obtener estadísticas de clientes', async () => {
      mockedApi.get.mockResolvedValue({ data: mockEstadisticas });
      const result = await clientesService.getEstadisticas();
      expect(mockedApi.get).toHaveBeenCalledWith('/clientes/estadisticas/');
      expect(result).toEqual(mockEstadisticas);
      expect(result.total).toBe(100);
      expect(result.activos).toBe(85);
    });

    test('debe calcular porcentajes correctamente', async () => {
      mockedApi.get.mockResolvedValue({ data: mockEstadisticas });
      const result = await clientesService.getEstadisticas();
      expect(result.activos + result.inactivos).toBe(result.total);
      expect(result.con_credito + result.sin_credito).toBe(result.total);
    });
  });

  describe('Integration scenarios', () => {
    test('flujo completo: crear cliente -> actualizar -> obtener cuenta corriente', async () => {
      const clienteData: ClienteData = {
        nombres: 'Test',
        apellidos: 'Cliente',
        ruc_ci: '1111111111',
        estado: true,
        id_lista: 1,
        id_tipo_cliente: 1,
      };
      const clienteCreado: Cliente = {
        id_cliente: 10,
        nombres: 'Test',
        apellidos: 'Cliente',
        ruc_ci: '1111111111',
        estado: true,
        razon_social: 'Test Cliente',
        fecha_registro: '2024-01-15',
        id_lista: 1,
        id_tipo_cliente: 1,
      };
      const cuentaCorriente: CuentaCorriente = {
        total_debe: 0,
        total_haber: 0,
        saldo_neto: 0,
        limite_credito: 1000,
        credito_disponible: 1000,
        porcentaje_usado: 0,
        cantidad_facturas_pendientes: 0,
        cantidad_notas_credito: 0,
      };

      // Crear
      mockedApi.post.mockResolvedValueOnce({ data: clienteCreado });
      const created = await clientesService.crearCliente(clienteData);
      expect(created.id_cliente).toBe(10);

      // Actualizar
      mockedApi.patch.mockResolvedValueOnce({
        data: { ...clienteCreado, email: 'updated@test.com' },
      });
      const updated = await clientesService.actualizarCliente(10, {
        email: 'updated@test.com',
      });
      expect(updated.email).toBe('updated@test.com');

      // Obtener cuenta corriente
      mockedApi.get.mockResolvedValueOnce({ data: cuentaCorriente });
      const cuenta = await clientesService.getCuentaCorriente(10);
      expect(cuenta.saldo_neto).toBe(0);
    });
  });
});
