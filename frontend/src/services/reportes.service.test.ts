import {
  getReporteVentas,
  getReporteRecargas,
  getReporteTopProductos,
  getReporteConsumosTarjeta,
  getReporteFinanciero,
  getKPIsPrincipales,
  getDashboardVentas,
  getDashboardRecargas,
  getDashboardFinanciero,
  exportarReportePDF,
  exportarReporteExcel,
  formatearMoneda,
  formatearFecha,
  formatearFechaHora,
  calcularRangoFechas,
} from './reportes.service';
import api from './api';

jest.mock('./api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('Reportes Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ============================================================
  // REPORTES
  // ============================================================

  describe('getReporteVentas', () => {
    it('debería obtener reporte de ventas con parámetros básicos', async () => {
      const mockReporte = {
        total_ventas: 150000,
        cantidad_ventas: 25,
        ticket_promedio: 6000,
        ventas_por_dia: [],
      };

      const params = {
        fecha_inicio: '2024-01-01',
        fecha_fin: '2024-01-31',
      };

      mockedApi.get.mockResolvedValue({ data: mockReporte });

      const result = await getReporteVentas(params);

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/ventas/'),
        { params }
      );
      expect(result).toEqual(mockReporte);
    });

    it('debería obtener reporte de ventas con rango de fechas', async () => {
      const mockReporte = {
        total_ventas: 150000,
        cantidad_ventas: 25,
        ticket_promedio: 6000,
        ventas_por_dia: [],
      };

      const params = {
        fecha_inicio: '2024-01-01',
        fecha_fin: '2024-01-31',
      };

      mockedApi.get.mockResolvedValue({ data: mockReporte });

      const result = await getReporteVentas(params);

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/ventas/'),
        { params }
      );
      expect(result).toEqual(mockReporte);
    });

    it('debería manejar errores al obtener reporte de ventas', async () => {
      mockedApi.get.mockRejectedValue(new Error('Error de red'));

      const params = {
        fecha_inicio: '2024-01-01',
        fecha_fin: '2024-01-31',
      };

      await expect(getReporteVentas(params)).rejects.toThrow('Error de red');
    });
  });

  describe('getReporteRecargas', () => {
    it('debería obtener reporte de recargas', async () => {
      const mockReporte = {
        total_recargas: 500000,
        cantidad_recargas: 100,
        recarga_promedio: 5000,
        recargas_por_dia: [],
      };

      mockedApi.get.mockResolvedValue({ data: mockReporte });

      const params = {
        fecha_inicio: '2024-01-01',
        fecha_fin: '2024-01-31',
      };

      const result = await getReporteRecargas(params);

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/recargas/'),
        { params }
      );
      expect(result).toEqual(mockReporte);
    });

    it('debería obtener reporte de recargas con filtros', async () => {
      const mockReporte = {
        total_recargas: 500000,
        cantidad_recargas: 100,
        recarga_promedio: 5000,
        recargas_por_dia: [],
      };

      const params = {
        fecha_inicio: '2024-01-01',
        fecha_fin: '2024-01-31',
        estado: 'Confirmada' as const,
      };

      mockedApi.get.mockResolvedValue({ data: mockReporte });

      const result = await getReporteRecargas(params);

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/recargas/'),
        { params }
      );
      expect(result).toEqual(mockReporte);
    });
  });

  describe('getReporteTopProductos', () => {
    it('debería obtener top productos', async () => {
      const mockReporte = {
        productos: [
          { id_producto: 1, nombre: 'Hamburguesa', cantidad_vendida: 50, total_vendido: 250000 },
          { id_producto: 2, nombre: 'Pizza', cantidad_vendida: 30, total_vendido: 180000 },
        ],
      };

      mockedApi.get.mockResolvedValue({ data: mockReporte });

      const params = {
        fecha_inicio: '2024-01-01',
        fecha_fin: '2024-01-31',
      };

      const result = await getReporteTopProductos(params);

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/top-productos/'),
        { params }
      );
      expect(result).toEqual(mockReporte);
    });

    it('debería obtener top productos con límite', async () => {
      const mockReporte = {
        productos: [
          { id_producto: 1, nombre: 'Hamburguesa', cantidad_vendida: 50, total_vendido: 250000 },
        ],
      };

      const params = {
        fecha_inicio: '2024-01-01',
        fecha_fin: '2024-01-31',
        limite: 5,
      };

      mockedApi.get.mockResolvedValue({ data: mockReporte });

      const result = await getReporteTopProductos(params);

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/top-productos/'),
        { params }
      );
      expect(result).toEqual(mockReporte);
    });
  });

  describe('getReporteConsumosTarjeta', () => {
    it('debería obtener reporte de consumos por tarjeta', async () => {
      const mockReporte = {
        total_consumos: 100,
        saldo_total: 50000,
        consumos_por_hijo: [],
      };

      const params = {
        nro_tarjeta: '123456',
        fecha_inicio: '2024-01-01',
        fecha_fin: '2024-01-31',
      };

      mockedApi.get.mockResolvedValue({ data: mockReporte });

      const result = await getReporteConsumosTarjeta(params);

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/consumos-tarjeta/'),
        { params }
      );
      expect(result).toEqual(mockReporte);
    });

    it('debería manejar errores al obtener consumos por tarjeta', async () => {
      mockedApi.get.mockRejectedValue(new Error('Cliente no encontrado'));

      const params = {
        nro_tarjeta: '999999',
        fecha_inicio: '2024-01-01',
        fecha_fin: '2024-01-31',
      };

      await expect(getReporteConsumosTarjeta(params)).rejects.toThrow('Cliente no encontrado');
    });
  });

  describe('getReporteFinanciero', () => {
    it('debería obtener reporte financiero', async () => {
      const mockReporte = {
        ingresos_ventas: 150000,
        ingresos_recargas: 500000,
        total_ingresos: 650000,
        gastos_compras: 300000,
        utilidad_neta: 350000,
      };

      mockedApi.get.mockResolvedValue({ data: mockReporte });

      const params = {
        fecha_inicio: '2024-01-01',
        fecha_fin: '2024-01-31',
      };

      const result = await getReporteFinanciero(params);

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/financiero/'),
        { params }
      );
      expect(result).toEqual(mockReporte);
    });

    it('debería obtener reporte financiero con rango de fechas', async () => {
      const mockReporte = {
        ingresos_ventas: 150000,
        ingresos_recargas: 500000,
        total_ingresos: 650000,
        gastos_compras: 300000,
        utilidad_neta: 350000,
      };

      const params = {
        fecha_inicio: '2024-01-01',
        fecha_fin: '2024-01-31',
      };

      mockedApi.get.mockResolvedValue({ data: mockReporte });

      const result = await getReporteFinanciero(params);

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/financiero/'),
        { params }
      );
      expect(result).toEqual(mockReporte);
    });
  });

  // ============================================================
  // DASHBOARDS
  // ============================================================

  describe('getKPIsPrincipales', () => {
    it('debería obtener KPIs principales sin fecha', async () => {
      const mockKPIs = {
        ventas_del_dia: 50000,
        recargas_del_dia: 100000,
        productos_bajo_stock: 5,
        ticket_promedio: 6000,
      };

      mockedApi.get.mockResolvedValue({ data: mockKPIs });

      const result = await getKPIsPrincipales();

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/kpis-principales/'),
        { params: {} }
      );
      expect(result).toEqual(mockKPIs);
    });

    it('debería obtener KPIs principales con fecha específica', async () => {
      const mockKPIs = {
        ventas_del_dia: 50000,
        recargas_del_dia: 100000,
        productos_bajo_stock: 5,
        ticket_promedio: 6000,
      };

      mockedApi.get.mockResolvedValue({ data: mockKPIs });

      const result = await getKPIsPrincipales('2024-01-15');

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/kpis-principales/'),
        { params: { fecha: '2024-01-15' } }
      );
      expect(result).toEqual(mockKPIs);
    });
  });

  describe('getDashboardVentas', () => {
    it('debería obtener dashboard de ventas', async () => {
      const mockDashboard = {
        total_ventas: 150000,
        cantidad_ventas: 25,
        ticket_promedio: 6000,
        ventas_por_hora: [],
        ventas_por_categoria: [],
        ventas_por_metodo_pago: [],
      };

      mockedApi.get.mockResolvedValue({ data: mockDashboard });

      const result = await getDashboardVentas();

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/dashboard-ventas/'),
        expect.objectContaining({ params: expect.anything() })
      );
      expect(result).toEqual(mockDashboard);
    });

    it('debería obtener dashboard de ventas con rango de fechas', async () => {
      const mockDashboard = {
        total_ventas: 150000,
        cantidad_ventas: 25,
        ticket_promedio: 6000,
        ventas_por_hora: [],
        ventas_por_categoria: [],
        ventas_por_metodo_pago: [],
      };

      const params = {
        dias: 30,
      };

      mockedApi.get.mockResolvedValue({ data: mockDashboard });

      const result = await getDashboardVentas(params);

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/dashboard-ventas/'),
        { params }
      );
      expect(result).toEqual(mockDashboard);
    });
  });

  describe('getDashboardRecargas', () => {
    it('debería obtener dashboard de recargas', async () => {
      const mockDashboard = {
        total_recargas: 500000,
        cantidad_recargas: 100,
        recarga_promedio: 5000,
        recargas_por_metodo: [],
        recargas_por_estado: [],
      };

      mockedApi.get.mockResolvedValue({ data: mockDashboard });

      const result = await getDashboardRecargas();

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/dashboard-recargas/'),
        expect.objectContaining({ params: expect.anything() })
      );
      expect(result).toEqual(mockDashboard);
    });

    it('debería obtener dashboard de recargas con filtros', async () => {
      const mockDashboard = {
        total_recargas: 500000,
        cantidad_recargas: 100,
        recarga_promedio: 5000,
        recargas_por_metodo: [],
        recargas_por_estado: [],
      };

      const params = {
        dias: 7,
      };

      mockedApi.get.mockResolvedValue({ data: mockDashboard });

      const result = await getDashboardRecargas(params);

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/dashboard-recargas/'),
        { params }
      );
      expect(result).toEqual(mockDashboard);
    });
  });

  describe('getDashboardFinanciero', () => {
    it('debería obtener dashboard financiero', async () => {
      const mockDashboard = {
        ingresos_ventas: 150000,
        ingresos_recargas: 500000,
        total_ingresos: 650000,
        gastos_compras: 300000,
        utilidad_neta: 350000,
        tendencia_ingresos: [],
        distribucion_gastos: [],
      };

      mockedApi.get.mockResolvedValue({ data: mockDashboard });

      const result = await getDashboardFinanciero();

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/dashboard-financiero/'),
        expect.objectContaining({ params: expect.anything() })
      );
      expect(result).toEqual(mockDashboard);
    });

    it('debería obtener dashboard financiero con parámetros', async () => {
      const mockDashboard = {
        ingresos_ventas: 150000,
        ingresos_recargas: 500000,
        total_ingresos: 650000,
        gastos_compras: 300000,
        utilidad_neta: 350000,
        tendencia_ingresos: [],
        distribucion_gastos: [],
      };

      const params = {
        mes: 1,
      };

      mockedApi.get.mockResolvedValue({ data: mockDashboard });

      const result = await getDashboardFinanciero(params);

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/dashboard-financiero/'),
        { params }
      );
      expect(result).toEqual(mockDashboard);
    });
  });

  // ============================================================
  // EXPORTACIONES
  // ============================================================

  describe('exportarReportePDF', () => {
    it('debería exportar reporte de ventas a PDF', async () => {
      const mockBlob = new Blob(['PDF content'], { type: 'application/pdf' });

      mockedApi.get.mockResolvedValue({ data: mockBlob });

      const result = await exportarReportePDF('ventas', {});

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/exportar-pdf/'),
        expect.objectContaining({ responseType: 'blob' })
      );
      expect(result).toEqual(mockBlob);
    });

    it('debería exportar reporte con parámetros a PDF', async () => {
      const mockBlob = new Blob(['PDF content'], { type: 'application/pdf' });
      const params = { fecha_inicio: '2024-01-01', fecha_fin: '2024-01-31' };

      mockedApi.get.mockResolvedValue({ data: mockBlob });

      const result = await exportarReportePDF('ventas', params);

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/exportar-pdf/'),
        expect.objectContaining({ responseType: 'blob' })
      );
      expect(result).toEqual(mockBlob);
    });

    it('debería manejar errores al exportar PDF', async () => {
      mockedApi.get.mockRejectedValue(new Error('Error al generar PDF'));

      await expect(exportarReportePDF('ventas', {})).rejects.toThrow('Error al generar PDF');
    });
  });

  describe('exportarReporteExcel', () => {
    it('debería exportar reporte de recargas a Excel', async () => {
      const mockBlob = new Blob(['Excel content'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });

      mockedApi.get.mockResolvedValue({ data: mockBlob });

      const result = await exportarReporteExcel('recargas', {});

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/exportar-excel/'),
        expect.objectContaining({ responseType: 'blob' })
      );
      expect(result).toEqual(mockBlob);
    });

    it('debería exportar reporte con parámetros a Excel', async () => {
      const mockBlob = new Blob(['Excel content'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      });
      const params = { fecha_inicio: '2024-01-01', fecha_fin: '2024-01-31' };

      mockedApi.get.mockResolvedValue({ data: mockBlob });

      const result = await exportarReporteExcel('recargas', params);

      expect(mockedApi.get).toHaveBeenCalledWith(
        expect.stringContaining('/reportes/exportar-excel/'),
        expect.objectContaining({ responseType: 'blob' })
      );
      expect(result).toEqual(mockBlob);
    });

    it('debería manejar errores al exportar Excel', async () => {
      mockedApi.get.mockRejectedValue(new Error('Error al generar Excel'));

      await expect(exportarReporteExcel('recargas', {})).rejects.toThrow('Error al generar Excel');
    });
  });

  // ============================================================
  // HELPERS
  // ============================================================

  describe('formatearMoneda', () => {
    it('debería formatear números como moneda', () => {
      const resultado1 = formatearMoneda(5000);
      const resultado2 = formatearMoneda(15000);
      const resultado3 = formatearMoneda(1500000);

      expect(resultado1).toContain('5');
      expect(resultado1).toMatch(/5[\.\,]?000|5000/);
      expect(resultado2).toContain('15');
      expect(resultado3).toContain('1');
      expect(resultado3).toContain('500');
    });

    it('debería formatear cero correctamente', () => {
      const resultado = formatearMoneda(0);
      expect(resultado).toMatch(/0/);
    });

    it('debería manejar números negativos', () => {
      const resultado = formatearMoneda(-5000);
      expect(resultado).toContain('5');
      expect(resultado).toMatch(/-|\(/);
    });
  });

  describe('formatearFecha', () => {
    it('debería formatear fecha ISO a formato local', () => {
      const fecha = '2024-01-15T12:00:00';
      const resultado = formatearFecha(fecha);
      expect(resultado).toMatch(/15|14/);
      expect(resultado).toMatch(/01|1/);
      expect(resultado).toMatch(/2024/);
    });

    it('debería formatear fecha con hora', () => {
      const fecha = '2024-01-15T10:30:00Z';
      const resultado = formatearFecha(fecha);
      expect(resultado).toMatch(/15|14/);
      expect(resultado).toMatch(/2024/);
    });
  });

  describe('formatearFechaHora', () => {
    it('debería formatear fecha y hora', async () => {
      const fecha = '2024-01-15T10:30:00';
      const resultado = formatearFechaHora(fecha);
      expect(resultado).toMatch(/15/);
      expect(resultado).toMatch(/2024/);
      expect(resultado).toMatch(/[0-9]{1,2}:[0-9]{2}/);
    });
  });

  describe('calcularRangoFechas', () => {
    it('debería calcular rango para "hoy"', () => {
      const resultado = calcularRangoFechas('hoy');
      expect(resultado).toHaveProperty('fecha_inicio');
      expect(resultado).toHaveProperty('fecha_fin');
      expect(resultado.fecha_inicio).toBe(resultado.fecha_fin);
    });

    it('debería calcular rango para "ayer"', () => {
      const resultado = calcularRangoFechas('ayer');
      expect(resultado).toHaveProperty('fecha_inicio');
      expect(resultado).toHaveProperty('fecha_fin');
      expect(resultado.fecha_inicio).not.toBe(resultado.fecha_fin);
    });

    it('debería calcular rango para "semana"', () => {
      const resultado = calcularRangoFechas('semana');
      expect(resultado).toHaveProperty('fecha_inicio');
      expect(resultado).toHaveProperty('fecha_fin');

      const inicio = new Date(resultado.fecha_inicio);
      const fin = new Date(resultado.fecha_fin);
      const diff = Math.floor((fin.getTime() - inicio.getTime()) / (1000 * 60 * 60 * 24));
      expect(diff).toBe(7);
    });

    it('debería calcular rango para "mes"', () => {
      const resultado = calcularRangoFechas('mes');
      expect(resultado).toHaveProperty('fecha_inicio');
      expect(resultado).toHaveProperty('fecha_fin');
    });

    it('debería calcular rango para "año"', () => {
      const resultado = calcularRangoFechas('año');
      expect(resultado).toHaveProperty('fecha_inicio');
      expect(resultado).toHaveProperty('fecha_fin');

      const inicio = new Date(resultado.fecha_inicio);
      const fin = new Date(resultado.fecha_fin);
      expect(fin.getFullYear() - inicio.getFullYear()).toBe(1);
    });
  });

  // ============================================================
  // INTEGRATION TESTS
  // ============================================================

  describe('Integration Scenarios', () => {
    it('debería obtener KPIs y luego dashboard de ventas', async () => {
      const mockKPIs = {
        fecha: '2024-01-15',
        ventas_del_dia: 50000,
        cantidad_ventas: 10,
        recargas_del_dia: 100000,
        cantidad_recargas: 20,
        tarjetas_activas: 50,
        productos_bajo_stock: 5,
        ticket_promedio: 6000,
        saldo_total_tarjetas: 250000,
      };

      const mockDashboard = {
        periodo: 'Mensual',
        fecha_inicio: '2024-01-01',
        fecha_fin: '2024-01-31',
        ventas_por_dia: [
          {
            fecha: '2024-01-15',
            cantidad_ventas: 10,
            total_vendido: 50000,
            ticket_promedio: 5000,
          },
        ],
        ventas_por_metodo_pago: [],
        productos_mas_vendidos: [],
        comparacion_semana_anterior: {
          periodo_actual: 50000,
          periodo_anterior: 45000,
          variacion_porcentual: 11.1,
        },
        tendencia: 'crecimiento' as const,
      };

      mockedApi.get.mockResolvedValueOnce({ data: mockKPIs });
      const kpis = await getKPIsPrincipales();
      expect(kpis.ventas_del_dia).toBe(50000);

      mockedApi.get.mockResolvedValueOnce({ data: mockDashboard });
      const dashboard = await getDashboardVentas();
      expect(dashboard.ventas_por_dia).toHaveLength(1);
      expect(dashboard.ventas_por_dia[0].total_vendido).toBe(50000);
    });

    it('debería exportar reporte después de consultarlo', async () => {
      const mockReporte = {
        total_ventas: 150000,
        cantidad_ventas: 25,
        ticket_promedio: 6000,
        ventas_por_dia: [],
      };

      const mockBlob = new Blob(['PDF content'], { type: 'application/pdf' });

      const params = {
        fecha_inicio: '2024-01-01',
        fecha_fin: '2024-01-31',
      };

      // Consultar reporte
      mockedApi.get.mockResolvedValueOnce({ data: mockReporte });
      const reporte = await getReporteVentas(params);
      expect(reporte.total_ventas).toBe(150000);

      // Exportar a PDF
      mockedApi.get.mockResolvedValueOnce({ data: mockBlob });
      const pdf = await exportarReportePDF('ventas', params);
      expect(pdf).toEqual(mockBlob);
    });
  });
});
