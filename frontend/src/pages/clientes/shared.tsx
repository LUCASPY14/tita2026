import toast from 'react-hot-toast'
import { METODOS_PAGO as METODOS } from '../../constants/mediosPago'
import type { BadgeColor } from '../../components/ui/Badge'

// ─── Interfaces ───────────────────────────────────────────────────────────────

export interface TipoCliente { id: number; nombre: string; activo: boolean }
export interface ListaPrecio { id: number; nombre: string }
export interface Ciudad { id: number; nombre: string }

export interface Cliente {
  id: number
  nombres: string
  apellidos: string
  razon_social: string | null
  ruc_ci: string
  direccion: string | null
  ciudad: string | null
  telefono: string | null
  email: string | null
  limite_credito: string
  activo: boolean
  fecha_registro: string
  lista_precio: number
  tipo_cliente: number
  tipo_cliente_nombre: string
  saldo_cuenta_corriente: string
  saldo_negativo_tarjetas: string
  modalidad_facturacion: 'INMEDIATA' | 'MENSUAL'
}

export interface ClienteForm {
  nombres: string
  apellidos: string
  razon_social: string
  ruc_ci: string
  direccion: string
  ciudad: string
  telefono: string
  email: string
  limite_credito: string
  activo: boolean
  lista_precio: string
  tipo_cliente: string
  modalidad_facturacion: 'INMEDIATA' | 'MENSUAL'
}

export interface GradoOption { id: number; nombre: string; activo: boolean }

export interface Hijo {
  id: number
  nombre: string
  apellido: string
  fecha_nacimiento: string | null
  grado: number | null
  grado_nombre: string | null
  // La foto no viaja como URL cruda — foto_url apunta al endpoint protegido
  // (solo ADMIN/CAJERO); hay que pedirla con useAuthenticatedImage.
  foto_url: string | null
  activo: boolean
  fecha_baja: string | null
  cliente_responsable: number
  cliente_nombre: string
}

export interface HijoForm {
  nombre: string
  apellido: string
  fecha_nacimiento: string
  grado: string
  activo: boolean
}

export interface RestriccionHijo {
  id: number
  hijo: number
  tipo: string
  descripcion: string | null
  severidad: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA'
  activo: boolean
  hijo_nombre: string
}

export interface AlumnoResponsable {
  id: number
  hijo: number
  cliente: number
  cliente_nombre: string
  cliente_ruc_ci: string
  cliente_telefono: string | null
  cliente_email: string | null
  parentesco: string
  parentesco_display: string
  es_titular: boolean
  orden_cobro: number
  recibe_notificaciones: boolean
  puede_ver_saldo: boolean
  activo: boolean
}

export interface AgregarResponsableForm {
  cliente: string
  parentesco: string
  orden_cobro: string
  recibe_notificaciones: boolean
  puede_ver_saldo: boolean
}

export interface DetalleConsumo {
  id: number
  producto_nombre: string
  cantidad: string
  precio_unitario: string
  subtotal: string
}

export interface VentaConsumo {
  id: number
  fecha: string
  monto_total: string
  estado: string
  detalles: DetalleConsumo[]
}

export interface PagoCC {
  saldo_anterior: string | number
  saldo_resultante: string | number
  monto: string | number
  descripcion: string
}

// ─── Constants ────────────────────────────────────────────────────────────────

export const RUC_CI_REGEX = /^(\d{6,8}(-\d{1,2})?|\d{1,8}-\d{1}|\d{6,8})$/

export const BLANK_CLIENTE: ClienteForm = {
  nombres: '', apellidos: '', razon_social: '', ruc_ci: '',
  direccion: '', ciudad: '', telefono: '', email: '',
  limite_credito: '0', activo: true, lista_precio: '', tipo_cliente: '',
  modalidad_facturacion: 'INMEDIATA',
}

export const BLANK_HIJO: HijoForm = {
  nombre: '', apellido: '', fecha_nacimiento: '', grado: '', activo: true,
}

export const BLANK_RESP: AgregarResponsableForm = {
  cliente: '', parentesco: 'OTRO', orden_cobro: '1',
  recibe_notificaciones: true, puede_ver_saldo: false,
}

export const PARENTESCO_LABELS: Record<string, string> = {
  PADRE: 'Padre', MADRE: 'Madre', ABUELO: 'Abuelo', ABUELA: 'Abuela',
  TIO: 'Tío', TIA: 'Tía', TUTOR: 'Tutor/a Legal', OTRO: 'Otro',
}

export const SEV_COLOR: Record<string, BadgeColor> = {
  BAJA: 'blue', MEDIA: 'yellow', ALTA: 'orange', CRITICA: 'red',
}

export const SEV_LABEL: Record<string, string> = {
  BAJA: 'Baja', MEDIA: 'Media', ALTA: 'Alta', CRITICA: 'Crítica',
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

export function extractErrorMessage(err: unknown): string {
  const e = err as { response?: { data?: unknown } }
  const data = e?.response?.data
  if (!data) return 'Error inesperado'
  if (typeof data === 'string') return data
  if (typeof data === 'object') {
    const d = data as Record<string, unknown>
    if (d.detail) return String(d.detail)
    const first = Object.values(d)[0]
    if (Array.isArray(first)) return String(first[0])
    return JSON.stringify(data)
  }
  return 'Error inesperado'
}

export function formatGs(value: string | number | null | undefined): string {
  return (Number(value) || 0).toLocaleString('es-PY') + ' Gs.'
}

export function formatFechaConsumo(iso: string) {
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export function formatGsConsumo(v: string | number) {
  return (Number(v) || 0).toLocaleString('es-PY') + ' Gs.'
}

export function abrirReciboCC(cliente: Cliente, pago: PagoCC, metodo: string) {
  const metodoLabel = METODOS.find(m => m.value === metodo)?.label ?? metodo
  const win = window.open('', '_blank', 'width=420,height=580')
  if (!win) { toast.error('Bloqueaste las ventanas emergentes'); return }
  win.document.write(`<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"/><title>Recibo de Pago CC</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:monospace;font-size:13px;padding:16px;max-width:380px;margin:auto}
  h1{font-size:16px;font-weight:bold;text-align:center;margin-bottom:4px}
  .center{text-align:center}
  .divider{border-top:1px dashed #000;margin:8px 0}
  .row{display:flex;justify-content:space-between;margin:3px 0}
  .label{color:#555}
  .big{font-size:22px;font-weight:bold;text-align:center;margin:10px 0}
  .footer{font-size:11px;text-align:center;color:#777;margin-top:12px}
  @media print{body{padding:0}}
</style>
</head>
<body>
<h1>La Cantina de Tita</h1>
<p class="center">Recibo de Pago</p>
<div class="divider"></div>
<div class="row"><span class="label">Cliente:</span><span>${cliente.apellidos}, ${cliente.nombres}</span></div>
<div class="row"><span class="label">RUC/CI:</span><span>${cliente.ruc_ci}</span></div>
<div class="row"><span class="label">Método:</span><span>${metodoLabel}</span></div>
<div class="row"><span class="label">Saldo anterior:</span><span>${(Number(pago.saldo_anterior) || 0).toLocaleString('es-PY')} Gs.</span></div>
<div class="divider"></div>
<div class="big">${(Number(pago.monto) || 0).toLocaleString('es-PY')} Gs.</div>
<div class="divider"></div>
<div class="row"><span class="label">Saldo restante:</span><span>${(Number(pago.saldo_resultante) || 0).toLocaleString('es-PY')} Gs.</span></div>
<div class="footer">Fecha: ${new Date().toLocaleString('es-PY')}</div>
<script>window.onload=()=>{window.print()}</script>
</body></html>`)
  win.document.close()
}
