import type { BadgeColor } from '../../components/ui/Badge'
import { formatCurrency } from '../../lib/format'

export { extractErrorMessage } from '../tarjetas/shared'

export type Bolsillo = 'CANTINA' | 'ALMUERZO'
export type TipoResolucion =
  | 'DEVOLUCION' | 'TRASPASO_HERMANO' | 'COMPENSACION' | 'COBRO' | 'TRASLADO_CC' | 'CONDONACION'
export type EstadoResolucion = 'SOLICITADA' | 'EJECUTADA' | 'RECHAZADA'
export type EstadoCierre = 'ABIERTO' | 'PARCIAL' | 'RESUELTO' | 'CERRADO_CON_SALDO'

export interface Resolucion {
  id_resolucion: number
  cierre: number
  hijo: number
  hijo_nombre: string
  tipo: TipoResolucion
  tipo_display: string
  estado: EstadoResolucion
  estado_display: string
  bolsillo_origen: Bolsillo
  bolsillo_destino: Bolsillo | ''
  hijo_destino: number | null
  hijo_destino_nombre: string | null
  monto: string | number
  metodo_pago: string
  referencia: string
  motivo: string
  solicitado_por_nombre: string
  fecha_solicitud: string
  decidido_por_nombre: string | null
  fecha_decision: string | null
  motivo_rechazo: string
  fecha_ejecucion: string | null
}

export interface Cierre {
  id_cierre_cuenta: number
  hijo: number
  hijo_nombre: string
  hijo_grado: string | null
  hijo_activo: boolean
  cliente_id: number
  cliente_nombre: string
  cliente_permite_cuenta_corriente: boolean
  nro_tarjeta: string
  anio: number
  estado: EstadoCierre
  estado_display: string
  saldo_cantina_inicial: string | number
  saldo_almuerzo_inicial: string | number
  saldo_cantina_actual: number
  saldo_almuerzo_actual: number
  deuda_pendiente: number
  a_favor_pendiente: number
  resoluciones_pendientes: number
  fecha_apertura: string
  fecha_cierre: string | null
  motivo_cierre: string
}

export interface Hermano {
  id_hijo: number
  nombre_completo: string
  grado: string
  nro_tarjeta: string
}

export interface CierreDetalle extends Cierre {
  resoluciones: Resolucion[]
  hermanos: Hermano[]
}

export interface ResumenCierres {
  anio: number
  alumnos: number
  por_estado: Record<EstadoCierre, number>
  saldo_a_devolver: number
  deuda_a_cobrar: number
  resoluciones_pendientes: number
}

export const formatGs = (n: number | string | null | undefined) => formatCurrency(Number(n) || 0)

export const TIPO_LABEL: Record<TipoResolucion, string> = {
  DEVOLUCION: 'Devolución',
  TRASPASO_HERMANO: 'Traspaso a hermano',
  COMPENSACION: 'Compensación entre bolsillos',
  COBRO: 'Cobro de deuda',
  TRASLADO_CC: 'Traslado a cuenta corriente familiar',
  CONDONACION: 'Condonación',
}

export const BOLSILLO_LABEL: Record<Bolsillo, string> = { CANTINA: 'Cantina', ALMUERZO: 'Almuerzo' }

export const ESTADO_CIERRE_LABEL: Record<EstadoCierre, string> = {
  ABIERTO: 'Abierto', PARCIAL: 'Parcial', RESUELTO: 'Resuelto', CERRADO_CON_SALDO: 'Cerrado con saldo',
}
export const ESTADO_CIERRE_COLOR: Record<EstadoCierre, BadgeColor> = {
  ABIERTO: 'yellow', PARCIAL: 'blue', RESUELTO: 'green', CERRADO_CON_SALDO: 'orange',
}
export const ESTADO_RES_COLOR: Record<EstadoResolucion, BadgeColor> = {
  SOLICITADA: 'yellow', EJECUTADA: 'green', RECHAZADA: 'red',
}

export const METODOS_COBRO = [
  { value: 'EFECTIVO', label: 'Efectivo' },
  { value: 'POS DEBITO', label: 'POS débito' },
  { value: 'POS CREDITO', label: 'POS crédito' },
  { value: 'TRANSFERENCIA', label: 'Transferencia' },
]
export const METODOS_DEVOLUCION = [
  { value: 'EFECTIVO', label: 'Efectivo (sale de tu caja)' },
  { value: 'TRANSFERENCIA', label: 'Transferencia' },
]

/** Quién decide con impacto económico. Cajeros y cobradores solo cobran. */
export const puedeGestionar = (rol?: string) => rol === 'ADMIN' || rol === 'SUPERVISOR'
export const esAdmin = (rol?: string) => rol === 'ADMIN'

export const saldoDe = (c: Cierre, bolsillo: Bolsillo) =>
  bolsillo === 'CANTINA' ? c.saldo_cantina_actual : c.saldo_almuerzo_actual

export interface OpcionResolucion {
  tipo: TipoResolucion
  label: string
  /** El supervisor la solicita y un administrador la aprueba. */
  pideAprobacion: boolean
}

/** Acciones válidas para un bolsillo según su saldo, el rol y los datos del responsable. */
export function opcionesResolucion(
  c: Cierre, bolsillo: Bolsillo, rol: string | undefined, hermanos: Hermano[],
): OpcionResolucion[] {
  const saldo = saldoDe(c, bolsillo)
  const otro = saldoDe(c, bolsillo === 'CANTINA' ? 'ALMUERZO' : 'CANTINA')
  const gestiona = puedeGestionar(rol)
  const sinAprobacion = esAdmin(rol)
  const op = (tipo: TipoResolucion, pideAprobacion = false): OpcionResolucion => ({
    tipo, label: TIPO_LABEL[tipo], pideAprobacion,
  })
  const salida: OpcionResolucion[] = []
  if (saldo > 0 && gestiona) {
    salida.push(op('DEVOLUCION', !sinAprobacion))
    if (hermanos.length > 0) salida.push(op('TRASPASO_HERMANO'))
    if (otro < 0) salida.push(op('COMPENSACION'))
  }
  if (saldo < 0) {
    salida.push(op('COBRO'))
    if (gestiona) {
      if (c.cliente_permite_cuenta_corriente) salida.push(op('TRASLADO_CC'))
      salida.push(op('CONDONACION', !sinAprobacion))
    }
  }
  return salida
}

/** Tope del monto según el tipo: saldo a favor, deuda o el menor de ambos (compensación). */
export function montoMaximo(c: Cierre, bolsillo: Bolsillo, tipo: TipoResolucion): number {
  const saldo = saldoDe(c, bolsillo)
  if (tipo === 'COMPENSACION') {
    const otro = saldoDe(c, bolsillo === 'CANTINA' ? 'ALMUERZO' : 'CANTINA')
    return Math.max(0, Math.min(saldo, -otro))
  }
  return Math.abs(saldo)
}
