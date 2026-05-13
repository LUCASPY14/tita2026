import api from './api';
import {
  getKpisPrincipales,
  getDashboardVentas,
  getDashboardRecargas,
  getDashboardFinanciero,
  formatearMoneda,
  formatearPorcentaje,
  getTendenciaColor,
  getTendenciaIcono,
  calcularVariacion,
} from './dashboard.service';

vi.mock('./api');
const mockedApi = api as vi.Mocked<typeof api>;

describe('Dashboard Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ============================================================
  // API Calls
  // ============================================================

  describe('getKpisPrincipales', () => {
    const mockKpis = {
      ventas_hoy: 1500000,
      transacciones_hoy: 12,
      ticket_promedio: 125000,
      clientes_activos: 8,
      tendencia_ventas: 'crecimiento',
    };

    it('obtiene KPIs sin fecha (usa default del servidor)', async () => {
      mockedApi.get.mockResolvedValue({ data: mockKpis });

      const result = await getKpisPrincipales();

      expect(mockedApi.get).toHaveBeenCalledWith('/reportes/kpis-principales/', {
        params: { fecha: undefined },
      });
      expect(result.ventas_hoy).toBe(1500000);
    });

    it('obtiene KPIs con fecha especifica', async () => {
      mockedApi.get.mockResolvedValue({ data: mockKpis });

      await getKpisPrincipales('2026-05-01');

      expect(mockedApi.get).toHaveBeenCalledWith('/reportes/kpis-principales/', {
        params: { fecha: '2026-05-01' },
      });
    });

    it('maneja error de servidor', async () => {
      mockedApi.get.mockRejectedValue({ response: { status: 500 } });

      await expect(getKpisPrincipales()).rejects.toMatchObject({
        response: { status: 500 },
      });
    });
  });

  describe('getDashboardVentas', () => {
    it('usa 7 dias por defecto', async () => {
      mockedApi.get.mockResolvedValue({ data: {} });

      await getDashboardVentas();

      expect(mockedApi.get).toHaveBeenCalledWith('/reportes/dashboard-ventas/', {
        params: { dias: 7 },
      });
    });

    it('acepta dias personalizado', async () => {
      mockedApi.get.mockResolvedValue({ data: {} });

      await getDashboardVentas(30);

      expect(mockedApi.get).toHaveBeenCalledWith('/reportes/dashboard-ventas/', {
        params: { dias: 30 },
      });
    });
  });

  describe('getDashboardRecargas', () => {
    it('usa 7 dias por defecto', async () => {
      mockedApi.get.mockResolvedValue({ data: {} });

      await getDashboardRecargas();

      expect(mockedApi.get).toHaveBeenCalledWith('/reportes/dashboard-recargas/', {
        params: { dias: 7 },
      });
    });

    it('acepta periodo de 14 dias', async () => {
      mockedApi.get.mockResolvedValue({ data: {} });

      await getDashboardRecargas(14);

      expect(mockedApi.get).toHaveBeenCalledWith('/reportes/dashboard-recargas/', {
        params: { dias: 14 },
      });
    });
  });

  describe('getDashboardFinanciero', () => {
    it('obtiene dashboard sin mes especifico', async () => {
      mockedApi.get.mockResolvedValue({ data: {} });

      await getDashboardFinanciero();

      expect(mockedApi.get).toHaveBeenCalledWith('/reportes/dashboard-financiero/', {
        params: { mes: undefined },
      });
    });

    it('obtiene dashboard para mes especifico', async () => {
      mockedApi.get.mockResolvedValue({ data: {} });

      await getDashboardFinanciero(5);

      expect(mockedApi.get).toHaveBeenCalledWith('/reportes/dashboard-financiero/', {
        params: { mes: 5 },
      });
    });
  });

  // ============================================================
  // Utilidades puras (sin mocks)
  // ============================================================

  describe('formatearMoneda', () => {
    it('formatea guaranies correctamente', () => {
      const result = formatearMoneda(150000);
      expect(result).toContain('150');
      // El formato exacto depende del locale, pero debe contener el numero
      expect(result).toMatch(/\d/);
    });

    it('formatea cero', () => {
      const result = formatearMoneda(0);
      expect(result).toContain('0');
    });

    it('formatea monto grande', () => {
      const result = formatearMoneda(1500000);
      expect(result).toContain('1');
    });
  });

  describe('formatearPorcentaje', () => {
    it('formatea porcentaje con 1 decimal por defecto', () => {
      expect(formatearPorcentaje(12.5)).toBe('12.5%');
    });

    it('formatea con 2 decimales', () => {
      expect(formatearPorcentaje(12.567, 2)).toBe('12.57%');
    });

    it('formatea cero', () => {
      expect(formatearPorcentaje(0)).toBe('0.0%');
    });

    it('formatea 100%', () => {
      expect(formatearPorcentaje(100)).toBe('100.0%');
    });
  });

  describe('getTendenciaColor', () => {
    it('retorna verde para crecimiento', () => {
      expect(getTendenciaColor('crecimiento')).toBe('text-green-600');
    });

    it('retorna rojo para decrecimiento', () => {
      expect(getTendenciaColor('decrecimiento')).toBe('text-red-600');
    });

    it('retorna gris para estable', () => {
      expect(getTendenciaColor('estable')).toBe('text-gray-600');
    });
  });

  describe('getTendenciaIcono', () => {
    it('retorna flecha arriba-derecha para crecimiento', () => {
      expect(getTendenciaIcono('crecimiento')).toBe('↗');
    });

    it('retorna flecha abajo-derecha para decrecimiento', () => {
      expect(getTendenciaIcono('decrecimiento')).toBe('↘');
    });

    it('retorna flecha derecha para estable', () => {
      expect(getTendenciaIcono('estable')).toBe('→');
    });
  });

  describe('calcularVariacion', () => {
    it('calcula variacion positiva correctamente', () => {
      expect(calcularVariacion(120, 100)).toBe(20);
    });

    it('calcula variacion negativa correctamente', () => {
      expect(calcularVariacion(80, 100)).toBe(-20);
    });

    it('retorna 100 cuando anterior es 0 y actual es positivo', () => {
      expect(calcularVariacion(50, 0)).toBe(100);
    });

    it('retorna 0 cuando ambos son 0', () => {
      expect(calcularVariacion(0, 0)).toBe(0);
    });

    it('calcula variacion exacta', () => {
      expect(calcularVariacion(150, 100)).toBe(50);
    });
  });
});
