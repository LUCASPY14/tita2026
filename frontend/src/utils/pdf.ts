import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

const BRAND = 'Cantina Tita'
const BRAND_COLOR: [number, number, number] = [22, 163, 74]  // green-600
const GRAY: [number, number, number] = [100, 116, 139]       // slate-500

// Precarga del logo al inicializar el módulo — disponible antes del primer PDF
let LOGO_B64: string | null = null
let LOGO_W = 0
let LOGO_H = 0

fetch('/logo_tita.png')
  .then(r => r.blob())
  .then(blob => new Promise<string>((resolve) => {
    const reader = new FileReader()
    reader.onloadend = () => resolve(reader.result as string)
    reader.readAsDataURL(blob)
  }))
  .then(b64 => {
    // Detectar dimensiones reales para escalar proporcionalmente a 12mm de alto
    const img = new window.Image()
    img.onload = () => {
      const TARGET_H = 12
      LOGO_H = TARGET_H
      LOGO_W = (img.naturalWidth / img.naturalHeight) * TARGET_H
      LOGO_B64 = b64
    }
    img.src = b64
  })
  .catch(() => {})

function header(doc: jsPDF, title: string, subtitle?: string) {
  const W = doc.internal.pageSize.getWidth()
  doc.setFillColor(...BRAND_COLOR)
  doc.rect(0, 0, W, 18, 'F')
  doc.setTextColor(255, 255, 255)
  if (LOGO_B64) {
    // Logo centrado verticalmente en la barra, margen izquierdo de 4mm
    const y = (18 - LOGO_H) / 2
    doc.addImage(LOGO_B64, 'PNG', 4, y, LOGO_W, LOGO_H)
  } else {
    doc.setFontSize(11)
    doc.setFont('helvetica', 'bold')
    doc.text(BRAND, 14, 11)
  }
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
  const pages = doc.getNumberOfPages()
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
  const num = Number(n)
  if (isNaN(num)) return '0 Gs.'
  return Math.round(num).toLocaleString('es-PY') + ' Gs.'
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
  try {
    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
    let y = header(doc, 'Reporte de Ventas', `Período: ${desde} → ${hasta}`)

    doc.setFontSize(9)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(0, 0, 0)
    doc.text(`Total de ventas: ${data.ventas.cantidad}`, 14, y)
    doc.text(`Monto total: ${gs(data.ventas.monto_total)}`, 14, y + 6)
    y += 14

    doc.setFontSize(10)
    doc.setFont('helvetica', 'bold')
    doc.text('Ventas por tipo', 14, y)
    y += 4

    autoTable(doc, {
      startY: y,
      head: [['Tipo', 'Cantidad', 'Monto']],
      body: (data.ventas?.por_tipo ?? []).map(r => [TIPO_LABEL[r.tipo] ?? r.tipo, r.cantidad, gs(r.monto)]),
      styles: { fontSize: 8, cellPadding: 2 },
      headStyles: { fillColor: BRAND_COLOR, textColor: [255, 255, 255], fontStyle: 'bold' },
      columnStyles: { 1: { halign: 'center' }, 2: { halign: 'right' } },
      alternateRowStyles: { fillColor: [248, 250, 252] },
    })

    y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 10

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
  } catch (err) {
    console.error('Error generando PDF de ventas:', err)
    throw new Error('No se pudo generar el PDF')
  }
}

// ─── Reporte Cuenta Corriente ─────────────────────────────────────────────────

interface AgingItem {
  cliente: string; ruc_ci: string; telefono: string; email: string
  saldo_deuda: number; dias_atraso: number; aging: string
}

export function exportarCuentaCorrientePDF(items: AgingItem[], totalDeuda: number, fecha: string) {
  try {
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
  } catch (err) {
    console.error('Error generando PDF de cuenta corriente:', err)
    throw new Error('No se pudo generar el PDF')
  }
}

// ─── Cuentas Mensuales de Almuerzos ──────────────────────────────────────────

const MESES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

interface CuentaMensual {
  hijo_nombre: string; anio: number; mes: number
  cantidad_almuerzos: number; monto_total: string | number
  monto_pagado: string | number; saldo_pendiente: string | number; estado: string
}

const ESTADO_COLOR: Record<string, [number, number, number]> = {
  PAGADO: [22, 163, 74], PENDIENTE: [234, 88, 12], PARCIAL: [37, 99, 235], ANULADO: [100, 116, 139],
}

export function exportarCuentasMensualesPDF(cuentas: CuentaMensual[], mes?: number, anio?: number) {
  try {
    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
    const periodo = (mes != null && anio != null) ? `${MESES[mes]} ${anio}` : anio != null ? String(anio) : 'Todos los períodos'
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
      didParseCell: (data) => {
        if (data.column.index === 6 && data.section === 'body') {
          const estado = cuentas[data.row.index]?.estado
          data.cell.styles.textColor = ESTADO_COLOR[estado] ?? GRAY
          data.cell.styles.fontStyle = 'bold'
        }
      },
    })

    footer(doc)
    const suffix = (mes != null && anio != null) ? `${anio}_${String(mes).padStart(2, '0')}` : anio ?? 'todos'
    doc.save(`cuentas_almuerzos_${suffix}.pdf`)
  } catch (err) {
    console.error('Error generando PDF de cuentas mensuales:', err)
    throw new Error('No se pudo generar el PDF')
  }
}

// ─── Reporte de Almuerzos por Período ────────────────────────────────────────

const MESES_ALM = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

const ESTADO_COLOR_ALM: Record<string, [number, number, number]> = {
  PAGADO: [22, 163, 74], PENDIENTE: [234, 88, 12], PARCIAL: [37, 99, 235],
}

interface AlmuerzoFila {
  hijo: string; grado: string
  cantidad_almuerzos: number
  monto_total: number; monto_pagado: number; monto_pendiente: number
  estado: string
}

interface AlmuerzoTotales {
  alumnos: number; cantidad_almuerzos: number
  monto_total: number; monto_pagado: number; monto_pendiente: number; con_deuda: number
}

export function exportarAlmuerzosPDF(
  filas: AlmuerzoFila[],
  totales: AlmuerzoTotales,
  anio: number,
  mes?: number,
  grado?: string,
) {
  try {
    const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' })
    const periodo = mes ? `${MESES_ALM[mes]} ${anio}` : String(anio)
    const subtituloExtra = grado ? ` — Grado: ${grado}` : ''
    let y = header(doc, 'Reporte de Almuerzos', `Período: ${periodo}${subtituloExtra}`)

    // KPI summary row
    doc.setFontSize(8.5)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(0, 0, 0)
    doc.text(
      `Alumnos: ${totales.alumnos}   |   Almuerzos: ${totales.cantidad_almuerzos}   |   ` +
      `Total: ${gs(totales.monto_total)}   |   Pagado: ${gs(totales.monto_pagado)}   |   ` +
      `Pendiente: ${gs(totales.monto_pendiente)}   |   Con deuda: ${totales.con_deuda}`,
      14, y
    )
    y += 9

    autoTable(doc, {
      startY: y,
      head: [['Estudiante', 'Grado', 'Almuerzos', 'Total', 'Pagado', 'Pendiente', 'Estado']],
      body: filas.map(f => [
        f.hijo,
        f.grado || '—',
        f.cantidad_almuerzos,
        gs(f.monto_total),
        gs(f.monto_pagado),
        gs(f.monto_pendiente),
        f.estado,
      ]),
      styles: { fontSize: 8, cellPadding: 2.5 },
      headStyles: { fillColor: BRAND_COLOR, textColor: [255, 255, 255], fontStyle: 'bold' },
      columnStyles: {
        2: { halign: 'center' },
        3: { halign: 'right' }, 4: { halign: 'right' }, 5: { halign: 'right' },
        6: { halign: 'center' },
      },
      alternateRowStyles: { fillColor: [248, 250, 252] },
      didParseCell: (data) => {
        if (data.column.index === 6 && data.section === 'body') {
          const estado = filas[data.row.index]?.estado
          data.cell.styles.textColor = ESTADO_COLOR_ALM[estado] ?? GRAY
          data.cell.styles.fontStyle = 'bold'
        }
        // Pendiente en rojo si > 0
        if (data.column.index === 5 && data.section === 'body') {
          const pendiente = filas[data.row.index]?.monto_pendiente ?? 0
          if (Number(pendiente) > 0) data.cell.styles.textColor = [220, 38, 38]
        }
      },
    })

    footer(doc)
    const suffix = mes ? `${anio}_${String(mes).padStart(2, '0')}` : anio
    doc.save(`almuerzos_${suffix}.pdf`)
  } catch (err) {
    console.error('Error generando PDF de almuerzos:', err)
    throw new Error('No se pudo generar el PDF')
  }
}

// ─── Reporte de Consumo por Tarjeta ──────────────────────────────────────────

interface DetalleConsumoPdf {
  producto_nombre: string
  cantidad: string
  precio_unitario: string
  subtotal: string
}
interface VentaConsumoPdf {
  fecha: string
  alumno: string
  grado: string | null
  tarjeta: string | null
  monto_total: string
  detalles: DetalleConsumoPdf[]
}

export function exportarConsumoPDF(ventas: VentaConsumoPdf[], desde: string, hasta: string, filtroTarjeta?: string) {
  try {
    const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' })
    const subtitle = filtroTarjeta
      ? `Tarjeta: ${filtroTarjeta} — ${desde} al ${hasta}`
      : `Período: ${desde} al ${hasta}`
    let y = header(doc, 'Reporte de Consumo', subtitle)

    const totalMonto = ventas.reduce((s, v) => s + Number(v.monto_total), 0)
    doc.setFontSize(8.5)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(0, 0, 0)
    doc.text(`Compras: ${ventas.length}   |   Total: ${gs(totalMonto)}`, 14, y)
    y += 8

    const fmt = (iso: string) => new Date(iso).toLocaleString('es-PY', {
      day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
    })

    const rows: string[][] = []
    for (const v of ventas) {
      if (v.detalles.length === 0) {
        rows.push([fmt(v.fecha), v.alumno, v.grado ?? '', v.tarjeta ?? '', '—', '', '', '', gs(Number(v.monto_total))])
      } else {
        v.detalles.forEach((d, i) => {
          rows.push([
            i === 0 ? fmt(v.fecha) : '',
            i === 0 ? v.alumno : '',
            i === 0 ? (v.grado ?? '') : '',
            i === 0 ? (v.tarjeta ?? '') : '',
            d.producto_nombre,
            d.cantidad,
            gs(Number(d.precio_unitario)),
            gs(Number(d.subtotal)),
            i === 0 ? gs(Number(v.monto_total)) : '',
          ])
        })
      }
    }
    rows.push(['', '', '', '', '', '', '', 'TOTAL', gs(totalMonto)])

    autoTable(doc, {
      startY: y,
      head: [['Fecha/Hora', 'Alumno', 'Grado', 'Tarjeta', 'Producto', 'Cant.', 'Precio Unit.', 'Subtotal', 'Total']],
      body: rows,
      styles: { fontSize: 7, cellPadding: 2 },
      headStyles: { fillColor: BRAND_COLOR, textColor: [255, 255, 255], fontStyle: 'bold' },
      columnStyles: {
        5: { halign: 'center' },
        6: { halign: 'right' },
        7: { halign: 'right' },
        8: { halign: 'right', fontStyle: 'bold' },
      },
      alternateRowStyles: { fillColor: [248, 250, 252] },
      didParseCell: (data) => {
        if (data.row.index === rows.length - 1 && data.section === 'body') {
          data.cell.styles.fontStyle = 'bold'
          data.cell.styles.fillColor = [240, 253, 244]
        }
      },
    })

    footer(doc)
    doc.save(`consumo_${desde}_${hasta}.pdf`)
  } catch (err) {
    console.error('Error generando PDF de consumo:', err)
    throw new Error('No se pudo generar el PDF')
  }
}

// ─── Registro de Ingresos al Comedor ─────────────────────────────────────────

interface IngresoComedor {
  nombre: string; hora: string; grado: string; tarjeta: string; saldo: string | number
}

export function exportarIngresosComedorPDF(ingresos: IngresoComedor[], fecha: string) {
  try {
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
  } catch (err) {
    console.error('Error generando PDF de ingresos comedor:', err)
    throw new Error('No se pudo generar el PDF')
  }
}
