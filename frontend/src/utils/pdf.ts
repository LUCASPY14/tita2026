import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

const BRAND = 'Cantina Tita'
const BRAND_COLOR: [number, number, number] = [22, 163, 74]  // green-600
const GRAY: [number, number, number] = [100, 116, 139]       // slate-500

function header(doc: jsPDF, title: string, subtitle?: string) {
  const W = doc.internal.pageSize.getWidth()
  doc.setFillColor(...BRAND_COLOR)
  doc.rect(0, 0, W, 18, 'F')
  doc.setTextColor(255, 255, 255)
  doc.setFontSize(11)
  doc.setFont('helvetica', 'bold')
  doc.text(BRAND, 14, 11)
  doc.setFontSize(9)
  doc.setFont('helvetica', 'normal')
  doc.text(title, W / 2, 11, { align: 'center' })
  const hoy = new Date().toLocaleDateString('es-PY', { day: '2-digit', month: '2-digit', year: 'numeric' })
  doc.text(hoy, W - 14, 11, { align: 'right' })
  doc.setTextColor(0, 0, 0)
  let y = 24
  if (subtitle) {
    doc.setFontSize(9)
    doc.setTextColor(...GRAY)
    doc.text(subtitle, 14, y)
    y += 7
  }
  return y
}

function footer(doc: jsPDF) {
  const pages = (doc.internal as { getNumberOfPages(): number }).getNumberOfPages()
  const W = doc.internal.pageSize.getWidth()
  const H = doc.internal.pageSize.getHeight()
  for (let i = 1; i <= pages; i++) {
    doc.setPage(i)
    doc.setFontSize(7)
    doc.setTextColor(...GRAY)
    doc.text(`Página ${i} de ${pages}`, W / 2, H - 6, { align: 'center' })
    doc.text(BRAND, 14, H - 6)
  }
}

function gs(n: number | string | null | undefined) {
  return (Number(n) || 0).toLocaleString('es-PY') + ' Gs.'
}

// ─── Reporte de Ventas ────────────────────────────────────────────────────────

interface VentaTipo { tipo: string; cantidad: number; monto: number }
interface CierreCaja {
  caja: string; fecha_apertura: string; fecha_cierre: string
  monto_inicial: number; monto_contado_fisico: number; diferencia: number
}
interface ReporteData {
  ventas: { cantidad: number; monto_total: number; por_tipo: VentaTipo[] }
  cierres_caja: CierreCaja[]
}

const TIPO_LABEL: Record<string, string> = {
  VENTA_TARJETA: 'Tarjeta prepago', VENTA_EFECTIVO: 'Efectivo',
  CONSUMO_ALMUERZO: 'Almuerzo', CARGA_SALDO: 'Carga de saldo',
}

export function exportarReporteVentasPDF(data: ReporteData, desde: string, hasta: string) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  let y = header(doc, 'Reporte de Ventas', `Período: ${desde} → ${hasta}`)

  // Summary
  doc.setFontSize(9)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(0, 0, 0)
  doc.text(`Total de ventas: ${data.ventas.cantidad}`, 14, y)
  doc.text(`Monto total: ${gs(data.ventas.monto_total)}`, 14, y + 6)
  y += 14

  // Por tipo
  doc.setFontSize(10)
  doc.setFont('helvetica', 'bold')
  doc.text('Ventas por tipo', 14, y)
  y += 4

  autoTable(doc, {
    startY: y,
    head: [['Tipo', 'Cantidad', 'Monto']],
    body: data.ventas.por_tipo.map(r => [TIPO_LABEL[r.tipo] ?? r.tipo, r.cantidad, gs(r.monto)]),
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: BRAND_COLOR, textColor: [255, 255, 255], fontStyle: 'bold' },
    columnStyles: { 1: { halign: 'center' }, 2: { halign: 'right' } },
    alternateRowStyles: { fillColor: [248, 250, 252] },
  })

  y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 10

  // Cierres de caja
  if (data.cierres_caja.length) {
    doc.setFontSize(10)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(0, 0, 0)
    doc.text('Cierres de caja', 14, y)
    y += 4

    const fmt = (iso: string) => new Date(iso).toLocaleString('es-PY', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
    autoTable(doc, {
      startY: y,
      head: [['Caja', 'Apertura', 'Cierre', 'Inicial', 'Contado', 'Diferencia']],
      body: data.cierres_caja.map(r => [
        r.caja, fmt(r.fecha_apertura), r.fecha_cierre ? fmt(r.fecha_cierre) : '—',
        gs(r.monto_inicial), gs(r.monto_contado_fisico),
        (r.diferencia >= 0 ? '+' : '') + gs(r.diferencia),
      ]),
      styles: { fontSize: 7.5, cellPadding: 2 },
      headStyles: { fillColor: BRAND_COLOR, textColor: [255, 255, 255], fontStyle: 'bold' },
      columnStyles: { 3: { halign: 'right' }, 4: { halign: 'right' }, 5: { halign: 'right' } },
      alternateRowStyles: { fillColor: [248, 250, 252] },
    })
  }

  footer(doc)
  doc.save(`reporte_ventas_${desde}_${hasta}.pdf`)
}

// ─── Reporte Cuenta Corriente ─────────────────────────────────────────────────

interface AgingItem {
  cliente: string; ruc_ci: string; telefono: string; email: string
  saldo_deuda: number; dias_atraso: number; aging: string
}

export function exportarCuentaCorrientePDF(items: AgingItem[], totalDeuda: number, fecha: string) {
  const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' })
  let y = header(doc, 'Reporte de Cuenta Corriente', `Generado: ${fecha}`)

  doc.setFontSize(9)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(0, 0, 0)
  doc.text(`Clientes con deuda: ${items.length}   |   Total deuda: ${gs(totalDeuda)}`, 14, y)
  y += 8

  autoTable(doc, {
    startY: y,
    head: [['Cliente', 'RUC/CI', 'Teléfono', 'Email', 'Saldo Deuda', 'Días Atraso', 'Aging']],
    body: items.map(r => [r.cliente, r.ruc_ci, r.telefono || '—', r.email || '—', gs(r.saldo_deuda), `${r.dias_atraso}d`, r.aging]),
    styles: { fontSize: 7.5, cellPadding: 2 },
    headStyles: { fillColor: BRAND_COLOR, textColor: [255, 255, 255], fontStyle: 'bold' },
    columnStyles: { 4: { halign: 'right' }, 5: { halign: 'center' }, 6: { halign: 'center' } },
    alternateRowStyles: { fillColor: [248, 250, 252] },
  })

  footer(doc)
  doc.save(`cuenta_corriente_${fecha}.pdf`)
}

// ─── Cuentas Mensuales de Almuerzos ──────────────────────────────────────────

const MESES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

interface CuentaMensual {
  hijo_nombre: string; anio: number; mes: number
  cantidad_almuerzos: number; monto_total: string | number
  monto_pagado: string | number; saldo_pendiente: string | number; estado: string
}

export function exportarCuentasMensualesPDF(cuentas: CuentaMensual[], mes?: number | '', anio?: number | '') {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  const periodo = mes && anio ? `${MESES[mes as number]} ${anio}` : anio ? String(anio) : 'Todos los períodos'
  let y = header(doc, 'Cuentas Mensuales de Almuerzos', `Período: ${periodo}`)

  const totalPendiente = cuentas.reduce((s, c) => s + (Number(c.saldo_pendiente) || 0), 0)
  const totalFacturado = cuentas.reduce((s, c) => s + (Number(c.monto_total) || 0), 0)
  doc.setFontSize(9)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(0, 0, 0)
  doc.text(`Total facturado: ${gs(totalFacturado)}   |   Saldo pendiente: ${gs(totalPendiente)}   |   Cuentas: ${cuentas.length}`, 14, y)
  y += 8

  autoTable(doc, {
    startY: y,
    head: [['Estudiante', 'Período', 'Almuerzos', 'Total', 'Pagado', 'Saldo', 'Estado']],
    body: cuentas.map(c => [
      c.hijo_nombre,
      `${MESES[c.mes]} ${c.anio}`,
      c.cantidad_almuerzos,
      gs(c.monto_total),
      gs(c.monto_pagado),
      gs(c.saldo_pendiente),
      c.estado,
    ]),
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: BRAND_COLOR, textColor: [255, 255, 255], fontStyle: 'bold' },
    columnStyles: { 2: { halign: 'center' }, 3: { halign: 'right' }, 4: { halign: 'right' }, 5: { halign: 'right' }, 6: { halign: 'center' } },
    alternateRowStyles: { fillColor: [248, 250, 252] },
    didDrawCell: (data) => {
      if (data.column.index === 6 && data.section === 'body') {
        const estado = cuentas[data.row.index]?.estado
        const colors: Record<string, [number, number, number]> = {
          PAGADO: [22, 163, 74], PENDIENTE: [234, 88, 12], PARCIAL: [37, 99, 235], ANULADO: [100, 116, 139]
        }
        const color = colors[estado] ?? [100, 116, 139]
        doc.setTextColor(...color)
        doc.setFont('helvetica', 'bold')
        doc.text(estado, data.cell.x + data.cell.width / 2, data.cell.y + data.cell.height / 2 + 1, { align: 'center' })
        doc.setTextColor(0, 0, 0)
        doc.setFont('helvetica', 'normal')
        return false
      }
    },
  })

  footer(doc)
  const suffix = mes && anio ? `${anio}_${String(mes as number).padStart(2, '0')}` : anio || 'todos'
  doc.save(`cuentas_almuerzos_${suffix}.pdf`)
}

// ─── Registro de Ingresos al Comedor ─────────────────────────────────────────

interface IngresoComedor {
  nombre: string; hora: string; grado: string; tarjeta: string; saldo: string | number
}

export function exportarIngresosComedorPDF(ingresos: IngresoComedor[], fecha: string) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  let y = header(doc, 'Registro de Ingresos al Comedor', `Fecha: ${fecha}`)

  doc.setFontSize(9)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(0, 0, 0)
  doc.text(`Total de ingresos: ${ingresos.length}`, 14, y)
  y += 8

  autoTable(doc, {
    startY: y,
    head: [['Hora', 'Estudiante', 'Grado', 'Nro. Tarjeta', 'Saldo Restante']],
    body: ingresos.map(r => [r.hora, r.nombre, r.grado, r.tarjeta, gs(r.saldo)]),
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: BRAND_COLOR, textColor: [255, 255, 255], fontStyle: 'bold' },
    columnStyles: { 0: { halign: 'center' }, 4: { halign: 'right' } },
    alternateRowStyles: { fillColor: [248, 250, 252] },
  })

  footer(doc)
  doc.save(`ingresos_comedor_${fecha}.pdf`)
}
