import type { BadgeColor } from '../../components/ui/Badge'
import { METODOS_PAGO as METODOS } from '../../constants/mediosPago'

export function extractErrorMessage(err: unknown): string {
  const e = err as { response?: { data?: unknown } }
  const data = e?.response?.data
  if (!data) return 'Error inesperado'
  if (typeof data === 'string') return data
  if (typeof data === 'object') {
    const d = data as Record<string, unknown>
    if (d.detail) return String(d.detail)
    if (d.error) return String(d.error)
    const first = Object.values(d)[0]
    if (Array.isArray(first)) return String(first[0])
    return JSON.stringify(data)
  }
  return 'Error inesperado'
}

export function formatGs(n: number | string | null | undefined): string {
  return 'Gs. ' + (Number(n) || 0).toLocaleString('es-PY')
}

export function formatFecha(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export interface Tarjeta {
  nro_tarjeta: string
  codigo_barras: string | null
  hijo: number | null
  hijo_nombre: string
  hijo_grado: string
  cliente_nombre: string
  cliente_id: number
  cliente_saldo_cc: string | number
  cliente_limite_credito: string | number
  cliente_permite_cuenta_corriente: boolean
  cliente_modalidad_facturacion: 'INMEDIATA' | 'MENSUAL'
  saldo_actual: string | number
  saldo_disponible: string | number
  estado: string
}

export interface Movimiento {
  id_movimiento_tarjeta: number
  tipo: string
  monto: string | number
  saldo_anterior: string | number
  saldo_resultante: string | number
  descripcion: string
  fecha: string
}

export interface CargaReciente {
  id_carga: number
  monto_cargado: string | number
  metodo_pago: string
  estado: string
  fecha_carga: string
}

export interface UltimaCarga {
  monto: number
  metodo: string
  tipoCobro: 'CONTADO' | 'CREDITO'
  estado: string
  tarjeta: Tarjeta
  fecha: string
}

export const TIPO_COLOR: Record<string, BadgeColor> = {
  RECARGA: 'green', CONSUMO: 'blue', AJUSTE: 'orange', REVERSO: 'purple',
}

export const ESTADO_COLOR: Record<string, BadgeColor> = {
  CONFIRMADA: 'green', PENDIENTE: 'yellow', RECHAZADA: 'red',
}

export const MONTOS_RAPIDOS = [10000, 20000, 50000, 100000, 200000]

export function abrirRecibo(carga: UltimaCarga) {
  const metodoLabel = carga.tipoCobro === 'CREDITO'
    ? 'Cuenta Corriente (Crédito)'
    : (METODOS.find(m => m.value === carga.metodo)?.label ?? carga.metodo)

  const win = window.open('', '_blank', 'width=420,height=600')
  if (!win) { return }

  win.document.write(`<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>Recibo de Recarga</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: monospace; font-size: 13px; padding: 16px; max-width: 380px; margin: auto; }
  h1 { font-size: 16px; font-weight: bold; text-align: center; margin-bottom: 4px; }
  .center { text-align: center; }
  .divider { border-top: 1px dashed #000; margin: 8px 0; }
  .row { display: flex; justify-content: space-between; margin: 3px 0; }
  .label { color: #555; }
  .big { font-size: 22px; font-weight: bold; text-align: center; margin: 10px 0; }
  .footer { font-size: 11px; text-align: center; color: #777; margin-top: 12px; }
  @media print { body { padding: 0; } }
</style>
</head>
<body>
<h1>LA CANTINA DE TITA</h1>
<p class="center">Recibo de Recarga de Saldo</p>
<div class="divider"></div>
<div class="row"><span class="label">Fecha:</span><span>${new Date(carga.fecha).toLocaleString('es-PY')}</span></div>
<div class="divider"></div>
<div class="row"><span class="label">Alumno:</span><span>${carga.tarjeta.hijo_nombre}</span></div>
<div class="row"><span class="label">Grado:</span><span>${carga.tarjeta.hijo_grado || '—'}</span></div>
<div class="row"><span class="label">Tarjeta:</span><span>${carga.tarjeta.nro_tarjeta}</span></div>
<div class="row"><span class="label">Responsable:</span><span>${carga.tarjeta.cliente_nombre}</span></div>
<div class="divider"></div>
<div class="row"><span class="label">Método:</span><span>${metodoLabel}</span></div>
<div class="big">Gs. ${carga.monto.toLocaleString('es-PY')}</div>
<div class="divider"></div>
<div class="row"><span class="label">Nuevo saldo tarjeta:</span><span>Gs. ${Number(carga.tarjeta.saldo_disponible).toLocaleString('es-PY')}</span></div>
<div class="footer">Gracias por su pago.<br/>Conserve este comprobante.</div>
<script>window.onload = function(){ window.print(); }</script>
</body>
</html>`)
  win.document.close()
}
