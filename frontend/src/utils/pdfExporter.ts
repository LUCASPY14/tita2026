import jsPDF from 'jspdf';
import type { 
  DashboardVentas, 
  DashboardKPIs,
  ReporteVentas
} from '../types';

// Configurar autoTable para jsPDF
import 'jspdf-autotable';

declare module 'jspdf' {
  interface jsPDF {
    autoTable: (options: any) => jsPDF;
  }
}

/**
 * Utilidades para exportación de reportes a PDF usando jsPDF
 */
export class PDFExporter {
  private doc: jsPDF;
  
  constructor(orientation: 'portrait' | 'landscape' = 'portrait') {
    this.doc = new jsPDF({
      orientation,
      unit: 'mm',
      format: 'a4',
    });
  }

  /**
   * Configura header del documento
   */
  private setupHeader(title: string, subtitle?: string) {
    const pageWidth = this.doc.internal.pageSize.width;
    
    // Logo o título principal
    this.doc.setFontSize(20);
    this.doc.setFont('helvetica', 'bold');
    this.doc.text('Cantina Tita', 20, 25);
    
    // Título del reporte
    this.doc.setFontSize(16);
    this.doc.setFont('helvetica', 'normal');
    this.doc.text(title, 20, 40);
    
    // Subtítulo si existe
    if (subtitle) {
      this.doc.setFontSize(12);
      this.doc.setTextColor(100, 100, 100);
      this.doc.text(subtitle, 20, 50);
    }
    
    // Fecha de generación
    const now = new Date();
    const fechaTexto = `Generado el ${now.toLocaleDateString('es-PY')} a las ${now.toLocaleTimeString('es-PY')}`;
    this.doc.setFontSize(10);
    this.doc.text(fechaTexto, pageWidth - 20, 25, { align: 'right' });
    
    // Línea separadora
    this.doc.setDrawColor(200, 200, 200);
    this.doc.line(20, 60, pageWidth - 20, 60);
    
    return 70; // Retorna la posición Y donde continúa el contenido
  }

  /**
   * Formatea números como moneda paraguaya
   */
  private formatGs(amount: number): string {
    return new Intl.NumberFormat('es-PY', {
      style: 'currency',
      currency: 'PYG',
      minimumFractionDigits: 0,
    }).format(amount);
  }

  /**
   * Exporta dashboard de ventas a PDF
   */
  exportDashboardVentas(data: DashboardVentas, kpis?: DashboardKPIs): void {
    let currentY = this.setupHeader(
      'Reporte de Ventas',
      `${data.periodo} (${data.fecha_inicio} al ${data.fecha_fin})`
    );

    // KPIs principales si están disponibles
    if (kpis) {
      currentY += 10;
      this.doc.setFontSize(14);
      this.doc.setFont('helvetica', 'bold');
      this.doc.text('Resumen Ejecutivo', 20, currentY);
      
      currentY += 15;
      const kpisData = [
        ['Ventas del día', kpis.cantidad_ventas.toString(), 'transacciones'],
        ['Ingresos del día', this.formatGs(kpis.ventas_del_dia), ''],
        ['Recargas realizadas', kpis.cantidad_recargas.toString(), 'operaciones'],
        ['Saldo en circulación', this.formatGs(kpis.saldo_total_tarjetas), ''],
      ];

      this.doc.autoTable({
        startY: currentY,
        head: [['Métrica', 'Valor', 'Unidad']],
        body: kpisData,
        styles: { fontSize: 10 },
        headStyles: { fillColor: [245, 158, 11] }, // Amber
        margin: { left: 20, right: 20 },
      });

      currentY = (this.doc as any).lastAutoTable.finalY + 15;
    }

    // Tabla de ventas por método de pago
    if (data.ventas_por_metodo_pago.length > 0) {
      this.doc.setFontSize(14);
      this.doc.setFont('helvetica', 'bold');
      this.doc.text('Ventas por Método de Pago', 20, currentY);
      
      currentY += 10;
      const metodosData = data.ventas_por_metodo_pago.map(metodo => [
        metodo.metodo_pago,
        metodo.cantidad.toString(),
        this.formatGs(metodo.total),
        `${((metodo.total / data.ventas_por_metodo_pago.reduce((sum, m) => sum + m.total, 0)) * 100).toFixed(1)}%`
      ]);

      this.doc.autoTable({
        startY: currentY,
        head: [['Método de Pago', 'Transacciones', 'Total', '% del Total']],
        body: metodosData,
        styles: { fontSize: 10 },
        headStyles: { fillColor: [59, 130, 246] }, // Blue
        margin: { left: 20, right: 20 },
      });

      currentY = (this.doc as any).lastAutoTable.finalY + 15;
    }

    // Productos más vendidos
    if (data.productos_mas_vendidos.length > 0) {
      this.doc.setFontSize(14);
      this.doc.setFont('helvetica', 'bold');
      this.doc.text('Productos Más Vendidos', 20, currentY);
      
      currentY += 10;
      const productosData = data.productos_mas_vendidos.slice(0, 10).map((producto, index) => [
        (index + 1).toString(),
        producto.id_producto__nombre,
        producto.cantidad_vendida.toString(),
        this.formatGs(producto.total_vendido),
      ]);

      this.doc.autoTable({
        startY: currentY,
        head: [['#', 'Producto', 'Cantidad', 'Total Vendido']],
        body: productosData,
        styles: { fontSize: 10 },
        headStyles: { fillColor: [16, 185, 129] }, // Green
        margin: { left: 20, right: 20 },
      });

      currentY = (this.doc as any).lastAutoTable.finalY + 15;
    }

    // Comparación con período anterior
    if (data.comparacion_semana_anterior) {
      const comp = data.comparacion_semana_anterior;
      this.doc.setFontSize(14);
      this.doc.setFont('helvetica', 'bold');
      this.doc.text('Comparación con Período Anterior', 20, currentY);
      
      currentY += 10;
      const variacion = comp.variacion_porcentual;
      const tendenciaTexto = variacion > 0 ? '↗ Crecimiento' : variacion < 0 ? '↘ Decrecimiento' : '→ Estable';
      
      const comparacionData = [
        ['Período actual', this.formatGs(comp.periodo_actual)],
        ['Período anterior', this.formatGs(comp.periodo_anterior)],
        ['Variación', `${variacion.toFixed(1)}%`],
        ['Tendencia', tendenciaTexto],
      ];

      this.doc.autoTable({
        startY: currentY,
        head: [['Concepto', 'Valor']],
        body: comparacionData,
        styles: { fontSize: 10 },
        headStyles: { fillColor: [139, 92, 246] }, // Purple
        margin: { left: 20, right: 20 },
      });
    }

    // Footer
    const pageHeight = this.doc.internal.pageSize.height;
    this.doc.setFontSize(8);
    this.doc.setTextColor(100, 100, 100);
    this.doc.text(
      'Generado automáticamente por Sistema de Gestión Cantina Tita',
      20,
      pageHeight - 20
    );

    this.save(`reporte-ventas-${data.fecha_inicio}-${data.fecha_fin}.pdf`);
  }

  /**
   * Exporta reporte de ventas (tabla de transacciones)
   */
  exportReporteVentas(ventas: ReporteVentas): void {
    let currentY = this.setupHeader('Reporte Detallado de Ventas');
    
    currentY += 10;
    
    if (!ventas.detalles || ventas.detalles.length === 0) {
      this.doc.setFontSize(12);
      this.doc.setTextColor(100, 100, 100);
      this.doc.text('No hay ventas para mostrar en el período seleccionado.', 20, currentY);
    } else {
      const ventasData = ventas.detalles.map((detalle, index) => [
        (index + 1).toString(),
        new Date(detalle.fecha_venta).toLocaleDateString('es-PY'),
        detalle.id_venta.toString() || '-',
        detalle.metodo_pago,
        this.formatGs(detalle.total),
        'Completada',
      ]);

      this.doc.autoTable({
        startY: currentY,
        head: [['#', 'Fecha', 'ID Venta', 'Método Pago', 'Total', 'Estado']],
        body: ventasData,
        styles: { fontSize: 9 },
        headStyles: { fillColor: [245, 158, 11] },
        margin: { left: 15, right: 15 },
        columnStyles: {
          0: { cellWidth: 15 },
          1: { cellWidth: 25 },
          2: { cellWidth: 25 },
          3: { cellWidth: 30 },
          4: { cellWidth: 30, halign: 'right' },
          5: { cellWidth: 20 },
        },
      });

      // Totales
      const currentYAfterTable = (this.doc as any).lastAutoTable.finalY + 10;
      const totalVentas = ventas.total_monto || 0;
      
      this.doc.setFontSize(12);
      this.doc.setFont('helvetica', 'bold');
      this.doc.text(`Total de Ventas: ${this.formatGs(totalVentas)}`, 20, currentYAfterTable);
      this.doc.text(`Cantidad de Transacciones: ${ventas.detalles?.length || 0}`, 20, currentYAfterTable + 8);
    }

    this.save(`reporte-ventas-detallado-${new Date().toISOString().split('T')[0]}.pdf`);
  }

  /**
   * Guarda el PDF con el nombre especificado
   */
  private save(filename: string): void {
    this.doc.save(filename);
  }
}

/**
 * Funciones de conveniencia para exportar diferentes tipos de reportes
 */
export const exportToPDF = {
  /**
   * Exporta dashboard de ventas a PDF
   */
  dashboardVentas: (data: DashboardVentas, kpis?: DashboardKPIs) => {
    const exporter = new PDFExporter();
    exporter.exportDashboardVentas(data, kpis);
  },

  /**
   * Exporta reporte detallado de ventas a PDF
   */
  reporteVentas: (ventas: ReporteVentas) => {
    const exporter = new PDFExporter('landscape');
    exporter.exportReporteVentas(ventas);
  },
};

export default exportToPDF;