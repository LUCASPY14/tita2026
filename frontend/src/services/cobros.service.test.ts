import api from './api';
import cobrosService, {
  PagoCliente,
  FacturaPendiente,
  ResumenCobros,
  RegistrarPagoRequest,
} from './cobros.service';

vi.mock('./api');
const mockedApi = api as vi.Mocked<typeof api>;

const mockPago: PagoCliente = {
  id_pago_cliente: 1,
  id_cliente: 10,
  monto_total: 150000,
  fecha_pago: '2026-05-12',
  id_medio_pago: 1,
  referencia: 'REF-001',
  banco_emisor: 'Banco Continental',
  observaciones: '',
  id_empleado_cajero: 2,
  estado: 'Aplicado',
  monto_aplicado: 150000,
  monto_pendiente_aplicar: 0,
};

const mockResumen: ResumenCobros = {
  cliente: {
    id_cliente: 10,
    nombre_completo: 'Juan Perez',
    ruc_ci: '1234567-8',
    limite_credito: 500000,
    credito_disponible: 200000,
  },
  facturas: [
    {
      id_venta: 1,
      nro_factura_venta: '001-001-0000001',
      fecha: '2026-04-01',
      total_venta: 150000,
      saldo_pendiente: 150000,
      dias_vencido: 41,
    },
  ],
  resumen: {
    cantidad_facturas: 1,
    total_pendiente: 150000,
  },
};

describe('Cobros Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getPagos', () => {
    it('retorna lista de pagos sin parametros', async () => {
      mockedApi.get.mockResolvedValue({ data: [mockPago] });

      const result = await cobrosService.getPagos();

      expect(mockedApi.get).toHaveBeenCalledWith('/cobros', { params: undefined });
      expect(result).toHaveLength(1);
      expect(result[0].id_pago_cliente).toBe(1);
    });

    it('filtra por id_cliente', async () => {
      mockedApi.get.mockResolvedValue({ data: [mockPago] });

      await cobrosService.getPagos({ id_cliente: 10 });

      expect(mockedApi.get).toHaveBeenCalledWith('/cobros', {
        params: { id_cliente: 10 },
      });
    });

    it('filtra por estado', async () => {
      mockedApi.get.mockResolvedValue({ data: [] });

      await cobrosService.getPagos({ estado: 'Pendiente' });

      expect(mockedApi.get).toHaveBeenCalledWith('/cobros', {
        params: { estado: 'Pendiente' },
      });
    });

    it('maneja error de red', async () => {
      mockedApi.get.mockRejectedValue(new Error('Network Error'));

      await expect(cobrosService.getPagos()).rejects.toThrow('Network Error');
    });
  });

  describe('getPagoById', () => {
    it('retorna un pago por ID', async () => {
      mockedApi.get.mockResolvedValue({ data: mockPago });

      const result = await cobrosService.getPagoById(1);

      expect(mockedApi.get).toHaveBeenCalledWith('/cobros/1/');
      expect(result.id_pago_cliente).toBe(1);
    });

    it('maneja pago no encontrado', async () => {
      mockedApi.get.mockRejectedValue({ response: { status: 404 } });

      await expect(cobrosService.getPagoById(999)).rejects.toMatchObject({
        response: { status: 404 },
      });
    });
  });

  describe('getFacturasPendientes', () => {
    it('retorna resumen de facturas pendientes para un cliente', async () => {
      mockedApi.get.mockResolvedValue({ data: mockResumen });

      const result = await cobrosService.getFacturasPendientes(10);

      expect(mockedApi.get).toHaveBeenCalledWith('/cobros/facturas_pendientes/', {
        params: { id_cliente: 10 },
      });
      expect(result.cliente.id_cliente).toBe(10);
      expect(result.resumen.total_pendiente).toBe(150000);
      expect(result.facturas).toHaveLength(1);
    });

    it('retorna resumen vacio cuando cliente no tiene deudas', async () => {
      const resumenVacio: ResumenCobros = {
        ...mockResumen,
        facturas: [],
        resumen: { cantidad_facturas: 0, total_pendiente: 0 },
      };
      mockedApi.get.mockResolvedValue({ data: resumenVacio });

      const result = await cobrosService.getFacturasPendientes(10);

      expect(result.facturas).toHaveLength(0);
      expect(result.resumen.total_pendiente).toBe(0);
    });
  });

  describe('registrarPago', () => {
    const pagoRequest: RegistrarPagoRequest = {
      id_cliente: 10,
      monto_total: 150000,
      id_medio_pago: 1,
      referencia: 'REF-001',
      aplicaciones: [{ id_venta: 1, monto_aplicado: 150000 }],
    };

    it('registra un pago exitosamente', async () => {
      mockedApi.post.mockResolvedValue({ data: mockPago });

      const result = await cobrosService.registrarPago(pagoRequest);

      expect(mockedApi.post).toHaveBeenCalledWith(
        '/cobros/registrar_pago/',
        pagoRequest
      );
      expect(result.id_pago_cliente).toBe(1);
      expect(result.estado).toBe('Aplicado');
    });

    it('registra pago sin aplicaciones (pago anticipado)', async () => {
      const pagoSinAplicaciones: RegistrarPagoRequest = {
        id_cliente: 10,
        monto_total: 200000,
        id_medio_pago: 2,
      };
      const pagoPendiente = { ...mockPago, monto_pendiente_aplicar: 200000, estado: 'Pendiente' };
      mockedApi.post.mockResolvedValue({ data: pagoPendiente });

      const result = await cobrosService.registrarPago(pagoSinAplicaciones);

      expect(result.monto_pendiente_aplicar).toBe(200000);
    });

    it('maneja error de validacion', async () => {
      mockedApi.post.mockRejectedValue({
        response: { status: 400, data: { error: 'Monto supera la deuda' } },
      });

      await expect(cobrosService.registrarPago(pagoRequest)).rejects.toMatchObject({
        response: { status: 400 },
      });
    });

    it('maneja error de permisos', async () => {
      mockedApi.post.mockRejectedValue({ response: { status: 403 } });

      await expect(cobrosService.registrarPago(pagoRequest)).rejects.toMatchObject({
        response: { status: 403 },
      });
    });
  });
});
