import { formatDateTime } from '../../lib/format'
import {
  BOLSILLO_LABEL, TIPO_LABEL, formatGs,
  type CierreDetalle, type Resolucion,
} from './shared'

const escapar = (s: string | null | undefined) =>
  (s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c] as string))

const fila = (etiqueta: string, valor: string | null | undefined) =>
  valor ? `<div class="row"><span class="label">${etiqueta}:</span><span>${escapar(valor)}</span></div>` : ''

/** Comprobante imprimible de una resolución ejecutada (para el padre y el archivo). */
export function imprimirComprobante(cierre: CierreDetalle, res: Resolucion) {
  const win = window.open('', '_blank', 'width=460,height=720')
  if (!win) return

  const destino = res.tipo === 'TRASPASO_HERMANO'
    ? `${res.hijo_destino_nombre ?? ''} (${BOLSILLO_LABEL[(res.bolsillo_destino || res.bolsillo_origen) as 'CANTINA' | 'ALMUERZO']})`
    : res.tipo === 'COMPENSACION'
      ? `Deuda de ${BOLSILLO_LABEL[res.bolsillo_destino as 'CANTINA' | 'ALMUERZO']}`
      : ''

  win.document.write(`<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>Comprobante de cierre de cuentas #${res.id_resolucion}</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: monospace; font-size: 13px; padding: 16px; max-width: 400px; margin: auto; }
  h1 { font-size: 16px; text-align: center; margin-bottom: 2px; }
  h2 { font-size: 13px; text-align: center; margin-bottom: 8px; font-weight: normal; }
  .divider { border-top: 1px dashed #000; margin: 8px 0; }
  .row { display: flex; justify-content: space-between; gap: 12px; margin: 3px 0; }
  .label { color: #555; }
  .big { font-size: 22px; font-weight: bold; text-align: center; margin: 10px 0; }
  .firma { margin-top: 36px; border-top: 1px solid #000; text-align: center; padding-top: 4px; font-size: 11px; }
  .footer { font-size: 11px; text-align: center; color: #777; margin-top: 14px; }
  @media print { body { padding: 0; } }
</style>
</head>
<body>
<h1>LA CANTINA DE TITA</h1>
<h2>Comprobante de cierre de cuentas</h2>
<div class="divider"></div>
${fila('Comprobante', `#${res.id_resolucion}`)}
${fila('Fecha', formatDateTime(res.fecha_ejecucion))}
<div class="divider"></div>
${fila('Alumno', cierre.hijo_nombre)}
${fila('Grado', cierre.hijo_grado)}
${fila('Tarjeta', cierre.nro_tarjeta)}
${fila('Responsable', cierre.cliente_nombre)}
<div class="divider"></div>
<div class="row"><span class="label">Operación:</span><span><strong>${escapar(TIPO_LABEL[res.tipo])}</strong></span></div>
${fila('Bolsillo', BOLSILLO_LABEL[res.bolsillo_origen])}
${fila('Destino', destino)}
${fila('Medio', res.metodo_pago)}
${fila('Referencia', res.referencia)}
${fila('Motivo', res.motivo)}
<div class="big">${escapar(formatGs(res.monto))}</div>
<div class="divider"></div>
${fila('Registró', res.solicitado_por_nombre)}
${fila('Autorizó', res.decidido_por_nombre)}
<div class="firma">Firma del responsable</div>
<div class="footer">Conserve este comprobante.</div>
<script>window.onload = function(){ window.print(); }</script>
</body>
</html>`)
  win.document.close()
}
