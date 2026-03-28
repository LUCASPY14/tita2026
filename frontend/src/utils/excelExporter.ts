import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';
import type { 
  DashboardVentas, 
  DashboardKPIs,
  ReporteVentas
} from '../types';

/**
 * Utilidades para exportación de reportes a Excel usando XLSX
 */
export class ExcelExporter {
  
  /**
   * Formatea números como moneda paraguaya
   */
  // private formatGs(amount: number): string {
  //   return new Intl.NumberFormat('es-PY', {
  //     style: 'currency',
  //     currency: 'PYG',
  //     minimumFractionDigits: 0,
  //   }).format(amount);
  // }

  /**
   * Crea workbook con múltiples hojas para dashboard de ventas
   */
  exportDashboardVentas(data: DashboardVentas, kpis?: DashboardKPIs): void {
    const workbook = XLSX.utils.book_new();

    // Hoja 1: Resumen Ejecutivo
    if (kpis) {
      const resumenData = [
        ['RESUMEN EJECUTIVO'],
        [''],
        ['Período:', `${data.periodo} (${data.fecha_inicio} al ${data.fecha_fin})`],
        ['Generado:', new Date().toLocaleString('es-PY')],
        [''],
        ['KPIS PRINCIPALES'],
        ['Métrica', 'Valor', 'Unidad'],
        ['Ventas del día', kpis.cantidad_ventas, 'transacciones'],
        ['Ingresos del día', kpis.ventas_del_dia, 'Gs.'],
        ['Recargas realizadas', kpis.cantidad_recargas, 'operaciones'],
        ['Saldo en circulación', kpis.saldo_total_tarjetas, 'Gs.'],
        [''],
        ['COMPARACIÓN PERÍODO'],
        ['Período actual', data.comparacion_semana_anterior.periodo_actual, 'Gs.'],
        ['Período anterior', data.comparacion_semana_anterior.periodo_anterior, 'Gs.'],
        ['Variación', `${data.comparacion_semana_anterior.variacion_porcentual.toFixed(1)}%`, ''],
        ['Tendencia', data.tendencia, ''],
      ];

      const resumenSheet = XLSX.utils.aoa_to_sheet(resumenData);
      
      // Aplicar estilos (ancho de columnas)
      resumenSheet['!cols'] = [
        { wch: 25 }, // Columna A
        { wch: 15 }, // Columna B  
        { wch: 15 }, // Columna C
      ];

      XLSX.utils.book_append_sheet(workbook, resumenSheet, 'Resumen');
    }

    // Hoja 2: Métodos de Pago
    if (data.ventas_por_metodo_pago.length > 0) {
      const totalGeneral = data.ventas_por_metodo_pago.reduce((sum, m) => sum + m.total, 0);
      
      const metodosData = [
        ['VENTAS POR MÉTODO DE PAGO'],
        [''],
        ['Método de Pago', 'Cantidad', 'Total (Gs.)', '% del Total'],
        ...data.ventas_por_metodo_pago.map(metodo => [
          metodo.metodo_pago,
          metodo.cantidad,
          metodo.total,
          `${((metodo.total / totalGeneral) * 100).toFixed(1)}%`
        ]),
        [''],
        ['TOTAL GENERAL', data.ventas_por_metodo_pago.reduce((sum, m) => sum + m.cantidad, 0), totalGeneral, '100.0%']
      ];

      const metodosSheet = XLSX.utils.aoa_to_sheet(metodosData);
      metodosSheet['!cols'] = [
        { wch: 20 }, // Método
        { wch: 12 }, // Cantidad
        { wch: 15 }, // Total
        { wch: 12 }, // Porcentaje
      ];

      XLSX.utils.book_append_sheet(workbook, metodosSheet, 'Métodos de Pago');
    }

    // Hoja 3: Productos Más Vendidos
    if (data.productos_mas_vendidos.length > 0) {
      const productosData = [
        ['PRODUCTOS MÁS VENDIDOS'],
        [''],
        ['#', 'Código', 'Producto', 'Cantidad', 'Total Vendido (Gs.)'],
        ...data.productos_mas_vendidos.slice(0, 20).map((producto, index) => [
          index + 1,
          producto.id_producto__codigo,
          producto.id_producto__nombre,
          producto.cantidad_vendida,
          producto.total_vendido
        ])
      ];

      const productosSheet = XLSX.utils.aoa_to_sheet(productosData);
      productosSheet['!cols'] = [
        { wch: 5 },  // #
        { wch: 15 }, // Código
        { wch: 30 }, // Producto
        { wch: 12 }, // Cantidad
        { wch: 18 }, // Total
      ];

      XLSX.utils.book_append_sheet(workbook, productosSheet, 'Top Productos');
    }

    // Hoja 4: Ventas por Día
    if (data.ventas_por_dia.length > 0) {
      const ventasDiaData = [
        ['VENTAS POR DÍA'],
        [''],
        ['Fecha', 'Cantidad Ventas', 'Total Vendido (Gs.)', 'Ticket Promedio (Gs.)'],
        ...data.ventas_por_dia.map(venta => [
          venta.fecha,
          venta.cantidad_ventas,
          venta.total_vendido,
          venta.ticket_promedio
        ])
      ];

      const ventasDiaSheet = XLSX.utils.aoa_to_sheet(ventasDiaData);
      ventasDiaSheet['!cols'] = [
        { wch: 12 }, // Fecha
        { wch: 15 }, // Cantidad
        { wch: 18 }, // Total
        { wch: 18 }, // Promedio
      ];

      XLSX.utils.book_append_sheet(workbook, ventasDiaSheet, 'Ventas por Día');
    }

    // Generar y descargar archivo
    const fileName = `reporte-ventas-${data.fecha_inicio}-${data.fecha_fin}.xlsx`;
    this.saveWorkbook(workbook, fileName);
  }

  /**
   * Exporta reporte detallado de ventas
   */
  exportReporteVentas(ventas: ReporteVentas): void {
    const workbook = XLSX.utils.book_new();

    if (!ventas.detalles || ventas.detalles.length === 0) {
      const emptyData = [
        ['REPORTE DE VENTAS'],
        [''],
        ['No hay ventas para mostrar en el período seleccionado.'],
        ['Generado:', new Date().toLocaleString('es-PY')],
      ];
      
      const emptySheet = XLSX.utils.aoa_to_sheet(emptyData);
      XLSX.utils.book_append_sheet(workbook, emptySheet, 'Ventas');
    } else {
      // Hoja principal con todas las ventas
      const ventasData = [
        ['REPORTE DETALLADO DE VENTAS'],
        [''],
        ['Generado:', new Date().toLocaleString('es-PY')],
        ['Total de transacciones:', ventas.detalles ? ventas.detalles.length : 0],
        ['Total facturado:', ventas.total_monto || 0, 'Gs.'],
        [''],
        ['#', 'Fecha', 'Hora', 'ID Venta', 'Empleado', 'Método Pago', 'Total (Gs.)', 'Estado'],
        ...(ventas.detalles ? ventas.detalles.map((detalle, index) => [
          index + 1,
          new Date(detalle.fecha_venta).toLocaleDateString('es-PY'),
          new Date(detalle.fecha_venta).toLocaleTimeString('es-PY'),
          detalle.id_venta || '-',
          `${detalle.id_empleado__nombre} ${detalle.id_empleado__apellido}`,
          detalle.metodo_pago,
          detalle.total,
          'Completada'
        ]) : [])
      ];

      const ventasSheet = XLSX.utils.aoa_to_sheet(ventasData);
      ventasSheet['!cols'] = [
        { wch: 5 },  // #
        { wch: 12 }, // Fecha
        { wch: 10 }, // Hora
        { wch: 15 }, // Ticket
        { wch: 20 }, // Cliente
        { wch: 15 }, // Método
        { wch: 15 }, // Total
        { wch: 12 }, // Estado
      ];

      XLSX.utils.book_append_sheet(workbook, ventasSheet, 'Ventas Detalladas');

      // Hoja resumen por método de pago
      const metodosPago = ventas.detalles ? ventas.detalles.reduce((acc, detalle) => {
        const metodo = detalle.metodo_pago || 'Sin especificar';
        if (!acc[metodo]) {
          acc[metodo] = { cantidad: 0, total: 0 };
        }
        acc[metodo].cantidad += 1;
        acc[metodo].total += detalle.total;
        return acc;
      }, {} as Record<string, { cantidad: number; total: number }>) : {};

      const resumenData = [
        ['RESUMEN POR MÉTODO DE PAGO'],
        [''],
        ['Método de Pago', 'Cantidad', 'Total (Gs.)', '% del Total'],
        ...Object.entries(metodosPago).map(([metodo, data]: [string, any]) => [
          metodo,
          data.cantidad,
          data.total,
          `${((data.total / (ventas.total_monto || 1)) * 100).toFixed(1)}%`
        ])
      ];

      const resumenSheet = XLSX.utils.aoa_to_sheet(resumenData);
      resumenSheet['!cols'] = [
        { wch: 20 }, // Método
        { wch: 12 }, // Cantidad
        { wch: 15 }, // Total
        { wch: 12 }, // Porcentaje
      ];

      XLSX.utils.book_append_sheet(workbook, resumenSheet, 'Resumen');
    }

    const fileName = `ventas-detallado-${new Date().toISOString().split('T')[0]}.xlsx`;
    this.saveWorkbook(workbook, fileName);
  }

  /**
   * Guarda el workbook como archivo Excel
   */
  private saveWorkbook(workbook: XLSX.WorkBook, fileName: string): void {
    const excelBuffer = XLSX.write(workbook, { 
      bookType: 'xlsx', 
      type: 'array',
      cellStyles: true 
    });
    
    const data = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    saveAs(data, fileName);
  }
}

/**
 * Funciones de conveniencia para exportar diferentes tipos de reportes a Excel
 */
export const exportToExcel = {
  /**
   * Exporta dashboard de ventas a Excel
   */
  dashboardVentas: (data: DashboardVentas, kpis?: DashboardKPIs) => {
    const exporter = new ExcelExporter();
    exporter.exportDashboardVentas(data, kpis);
  },

  /**
   * Exporta reporte detallado de ventas a Excel
   */
  reporteVentas: (ventas: ReporteVentas) => {
    const exporter = new ExcelExporter();
    exporter.exportReporteVentas(ventas);
  },

  /**
   * Exporta datos simples a Excel (genérico)
   */
  simple: (data: any[][], fileName: string, sheetName: string = 'Datos') => {
    const workbook = XLSX.utils.book_new();
    const worksheet = XLSX.utils.aoa_to_sheet(data);
    XLSX.utils.book_append_sheet(workbook, worksheet, sheetName);
    
    const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    saveAs(blob, `${fileName}.xlsx`);
  },
};

export default exportToExcel;