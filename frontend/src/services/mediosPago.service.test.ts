import api from './api';
import mediosPagoService, { MedioPago } from './mediosPago.service';

vi.mock('./api');
const mockedApi = api as vi.Mocked<typeof api>;

const mockMedios: MedioPago[] = [
  { id_medio_pago: 1, nombre: 'Efectivo', activo: true },
  { id_medio_pago: 2, nombre: 'Tarjeta de Debito', activo: true },
  { id_medio_pago: 3, nombre: 'Transferencia Bancaria', activo: true },
  { id_medio_pago: 4, nombre: 'QR (SIPAP)', activo: true },
  { id_medio_pago: 5, nombre: 'Cheque', activo: false },
];

describe('MediosPago Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getAll', () => {
    it('retorna todos los medios de pago', async () => {
      mockedApi.get.mockResolvedValue({ data: mockMedios });

      const result = await mediosPagoService.getAll();

      expect(mockedApi.get).toHaveBeenCalledWith('/medios-pago');
      expect(result).toHaveLength(5);
      expect(result[0].nombre).toBe('Efectivo');
    });

    it('retorna lista vacia cuando no hay medios', async () => {
      mockedApi.get.mockResolvedValue({ data: [] });

      const result = await mediosPagoService.getAll();

      expect(result).toHaveLength(0);
    });

    it('maneja error de autenticacion', async () => {
      mockedApi.get.mockRejectedValue({ response: { status: 401 } });

      await expect(mediosPagoService.getAll()).rejects.toMatchObject({
        response: { status: 401 },
      });
    });

    it('incluye medios inactivos', async () => {
      mockedApi.get.mockResolvedValue({ data: mockMedios });

      const result = await mediosPagoService.getAll();

      const inactivo = result.find(m => !m.activo);
      expect(inactivo).toBeDefined();
      expect(inactivo?.nombre).toBe('Cheque');
    });
  });

  describe('getById', () => {
    it('retorna medio de pago por ID', async () => {
      mockedApi.get.mockResolvedValue({ data: mockMedios[0] });

      const result = await mediosPagoService.getById(1);

      expect(mockedApi.get).toHaveBeenCalledWith('/medios-pago/1/');
      expect(result.id_medio_pago).toBe(1);
      expect(result.nombre).toBe('Efectivo');
    });

    it('lanza error para ID inexistente', async () => {
      mockedApi.get.mockRejectedValue({ response: { status: 404 } });

      await expect(mediosPagoService.getById(999)).rejects.toMatchObject({
        response: { status: 404 },
      });
    });
  });
});
