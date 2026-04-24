import api from '../api';
import {
  generarQRCargaSaldo,
  consultarEstadoPago,
  esperarConfirmacion,
} from '../sipap.service';

jest.mock('../api');

describe('SIPAP Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('generarQRCargaSaldo', () => {
    it('should generate QR code successfully', async () => {
      const mockResponse = {
        data: {
          txn_id: 'TXN123',
          qr_image: 'data:image/png;base64,...',
          monto: 50000,
          estado: 'pendiente',
        },
      };
      api.post.mockResolvedValue(mockResponse);

      const result = await generarQRCargaSaldo(1, 50000, 'Carga de saldo');

      expect(api.post).toHaveBeenCalledWith('/cobros/generar_qr_sipap/', {
        id_cliente: 1,
        monto: 50000,
        descripcion: 'Carga de saldo',
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('should throw error with API error message', async () => {
      const mockError = {
        response: {
          data: {
            detail: 'Monto inválido',
          },
        },
      };
      api.post.mockRejectedValue(mockError);

      await expect(generarQRCargaSaldo(1, -100, 'Invalid')).rejects.toThrow(
        'Monto inválido'
      );
    });

    it('should throw generic error when no detail available', async () => {
      api.post.mockRejectedValue(new Error('Network error'));

      await expect(generarQRCargaSaldo(1, 50000, 'Test')).rejects.toThrow(
        'Error al generar QR SIPAP'
      );
    });
  });

  describe('consultarEstadoPago', () => {
    it('should fetch payment status successfully', async () => {
      const mockResponse = {
        data: {
          txn_id: 'TXN123',
          estado: 'aprobado',
          fecha_confirmacion: '2026-04-21T10:30:00Z',
        },
      };
      api.get.mockResolvedValue(mockResponse);

      const result = await consultarEstadoPago('TXN123');

      expect(api.get).toHaveBeenCalledWith('/cobros/estado_pago_sipap/TXN123/');
      expect(result).toEqual(mockResponse.data);
    });

    it('should throw error on API failure', async () => {
      api.get.mockRejectedValue(new Error('Not found'));

      await expect(consultarEstadoPago('INVALID')).rejects.toThrow(
        'Error al consultar estado del pago'
      );
    });
  });

  describe('esperarConfirmacion', () => {
    it('should resolve when payment is approved', async () => {
      const mockEstado = { txn_id: 'TXN123', estado: 'aprobado' };
      api.get.mockResolvedValue({ data: mockEstado });

      const onUpdate = jest.fn();
      const promise = esperarConfirmacion('TXN123', onUpdate, 100, 10);

      // Esperar a que se resuelva
      const result = await promise;

      expect(result).toEqual(mockEstado);
      expect(onUpdate).toHaveBeenCalledWith(mockEstado);
    });

    it('should reject when payment is rejected', async () => {
      const mockEstado = { txn_id: 'TXN123', estado: 'rechazado' };
      api.get.mockResolvedValue({ data: mockEstado });

      const promise = esperarConfirmacion('TXN123', null, 100, 10);

      await expect(promise).rejects.toThrow('Pago rechazado');
    });

    it('should reject when QR is expired', async () => {
      const mockEstado = { txn_id: 'TXN123', estado: 'expirado' };
      api.get.mockResolvedValue({ data: mockEstado });

      const promise = esperarConfirmacion('TXN123', null, 100, 10);

      await expect(promise).rejects.toThrow('QR expirado');
    });

    it('should call onUpdate callback on each check', async () => {
      const mockEstado = { txn_id: 'TXN123', estado: 'pendiente' };
      api.get
        .mockResolvedValueOnce({ data: mockEstado })
        .mockResolvedValueOnce({ data: { ...mockEstado, estado: 'aprobado' } });

      const onUpdate = jest.fn();
      await esperarConfirmacion('TXN123', onUpdate, 50, 10);

      expect(onUpdate).toHaveBeenCalled();
    });

    it('should handle API errors gracefully', async () => {
      let callCount = 0;
      api.get.mockImplementation(() => {
        callCount++;
        if (callCount === 1) {
          return Promise.reject(new Error('Network error'));
        }
        return Promise.resolve({ data: { estado: 'aprobado' } });
      });

      const result = await esperarConfirmacion('TXN123', null, 50, 10);

      expect(result.estado).toBe('aprobado');
    });
  });
});
