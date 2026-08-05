import type { ReactNode } from 'react'

// ─── Types ────────────────────────────────────────────────────────────────────

export type TabKey =
  | 'ventas' | 'cuenta_corriente' | 'almuerzos' | 'productos' | 'cajeros'
  | 'stock' | 'tarjetas' | 'consumo' | 'notas_credito' | 'aging_proveedores'
  | 'compras_proveedores' | 'diferencias_caja' | 'medios_pago' | 'consumo_grado'
  | 'cobranza_almuerzos' | 'auditoria' | 'intentos_login' | 'personal_inactivo'

// ─── Interfaces ───────────────────────────────────────────────────────────────

export interface VentaTipo { tipo: string; cantidad: number; monto: number }

export interface CierreCajaReporte {
  id: number; caja: string; fecha_apertura: string; fecha_cierre: string
  monto_inicial: number; monto_contado_fisico: number; diferencia: number
}

export interface ReporteData {
  periodo: { desde: string; hasta: string }
  ventas: { cantidad: number; monto_total: number; por_tipo: VentaTipo[] }
  cierres_caja: CierreCajaReporte[]
}

export interface AgingItem {
  cliente_id: number; cliente: string; ruc_ci: string; telefono: string
  email: string; saldo_deuda: number; dias_atraso: number; aging: string
}

export interface CuentaCorrienteData {
  fecha: string
  resumen: {
    clientes_con_deuda: number; total_deuda: number
    aging: { '0-30': number; '31-60': number; '61-90': number; '90+': number }
  }
  detalle: AgingItem[]
}

export interface AlmuerzoFila {
  hijo_id: number; hijo: string; grado: string; nro_tarjeta: string
  cantidad_almuerzos: number
  monto_total: number; monto_pagado: number; monto_pendiente: number; estado: string
}

export interface AlmuerzosData {
  filas: AlmuerzoFila[]
  totales: {
    alumnos: number; cantidad_almuerzos: number; monto_total: number
    monto_pagado: number; monto_pendiente: number; con_deuda: number
  }
}

export interface ProductoVenta {
  producto_id: number; descripcion: string; categoria: string
  total_cantidad: number; total_monto: number; num_ventas: number
}

export type ProductoVentaRanked = ProductoVenta & { rank: number }

export interface ProductosData {
  periodo: { desde: string; hasta: string }
  total_monto: number
  productos: ProductoVenta[]
}

export interface CajeroVenta {
  cajero_id: number; username: string; nombre: string
  cantidad_ventas: number; monto_total: number; ticket_promedio: number
}

export interface CajerosData {
  periodo: { desde: string; hasta: string }
  total_monto: number
  cajeros: CajeroVenta[]
}

export interface ProductoStock {
  producto_id: number; descripcion: string; categoria: string; unidad: string
  stock_actual: number; stock_minimo: number; requiere_reposicion: boolean
  costo_promedio: number; valor_inventario: number; dias_stock: number | null
}

export interface StockData {
  resumen: {
    total_productos: number; productos_bajo_minimo: number; valor_total_inventario: number
  }
  productos: ProductoStock[]
}

export interface TarjetaReporte {
  nro_tarjeta: string; alumno: string; grado: string; saldo_actual: number
  total_recargado: number; total_consumido: number; num_recargas: number; num_consumos: number
}

export interface TarjetasData {
  periodo: { desde: string | null; hasta: string | null }
  resumen: {
    total_tarjetas: number; saldo_total: number
    total_recargado: number; total_consumido: number
  }
  tarjetas: TarjetaReporte[]
}

export interface TendenciaPoint { fecha: string; cantidad: number; monto: number }

export interface DetalleConsumoRep {
  id: number; producto_nombre: string; cantidad: string
  precio_unitario: string; subtotal: string
}

export interface VentaConsumoRep {
  id: number; fecha: string; monto_total: string; tarjeta: string | null
  hijo: number | null; hijo_nombre: string | null; hijo_grado: string | null
  cliente_nombre: string; detalles: DetalleConsumoRep[]
}

export interface ConsumoGradoFila {
  grado: string; nivel: number
  n_consumos: number; n_rechazados: number; n_anulados: number
  tasa_rechazo: number; monto_total: number
}

export interface HorarioPico { hora: number; n: number }

export interface ConsumoGradoData {
  periodo: { desde: string; hasta: string }
  resumen: { total_consumos: number; total_rechazados: number; tasa_rechazo_global: number }
  por_grado: ConsumoGradoFila[]
  horarios_pico: HorarioPico[]
}

export interface CobranzaMesFila {
  mes: number; mes_nombre: string
  n_alumnos: number; pagados: number; parciales: number; pendientes: number
  monto_total: number; monto_cobrado: number; monto_pendiente: number; tasa_cobro: number
}

export interface CobranzaFormaFila {
  forma_cobro: string; n_cuentas: number; monto_total: number
}

export interface CobranzaAlmuerzosData {
  anio: number
  resumen: {
    monto_anual: number; cobrado_anual: number; pendiente_anual: number
    tasa_cobro_anual: number; meses_con_datos: number
  }
  por_mes: CobranzaMesFila[]
  por_forma_cobro: CobranzaFormaFila[]
}

export interface CompraProveedorFila {
  proveedor_id: number; proveedor: string; ruc: string
  n_compras: number; monto_total: number
  entregadas: number; entrega_parcial: number; entrega_pendiente: number; tasa_entrega: number
  pagadas: number; pago_parcial: number; pago_pendiente: number
}

export interface FunnelOC { BORRADOR: number; PENDIENTE: number; APROBADA: number; RECHAZADA: number; CONVERTIDA: number; total: number }

export interface ComprasProveedoresData {
  periodo: { desde: string; hasta: string }
  resumen: { total_compras: number; monto_total: number; n_proveedores: number }
  por_proveedor: CompraProveedorFila[]
  funnel_oc: FunnelOC
}

export interface DiferenciaEmpleado {
  empleado_id: number; empleado: string
  n_cierres: number; diferencia_total: number; diferencia_promedio: number; mayor_diferencia: number
}

export interface TendenciaDiferencia { fecha: string; diferencia: number; empleado: string; caja: string; cierre_id: number }

export interface DiferenciasCajaData {
  periodo: { desde: string; hasta: string }
  resumen: { total_diferencia: number; n_cierres: number; n_positivos: number; n_negativos: number; n_cero: number }
  por_empleado: DiferenciaEmpleado[]
  tendencia: TendenciaDiferencia[]
}

export interface MedioPagoFila {
  medio_pago_id: number; descripcion: string
  n_pagos: number; monto_total: number
  n_conciliados: number; monto_conciliado: number
  n_pendientes: number; monto_pendiente: number
}

export interface MediosPagoData {
  periodo: { desde: string; hasta: string }
  resumen: { total_pagos: number; monto_total: number; n_medios: number }
  por_medio_pago: MedioPagoFila[]
}

export interface NCResumen {
  total_emitidas: number; total_aplicadas: number; total_anuladas: number
  monto_emitidas: number; monto_aplicadas: number; monto_anuladas: number; monto_total: number
}

export interface NCVentaFila {
  id: number; nro_nota_credito: string; fecha_emision: string
  cliente_id: number; cliente: string; ruc_ci: string
  estado: string; motivo: string; monto_total: number
  empleado_autoriza: string; venta_origen_id: number | null
}

export interface NCCompraFila {
  id: number; fecha: string
  proveedor_id: number; proveedor: string; ruc: string
  estado: string; observacion: string; nro_factura_compra: string
  monto_total: number; creado_por: string; compra_original_id: number | null
}

export interface NCVentaData { periodo: { desde: string; hasta: string }; resumen: NCResumen; detalle: NCVentaFila[] }
export interface NCCompraData { periodo: { desde: string; hasta: string }; resumen: NCResumen; detalle: NCCompraFila[] }

export interface AgingProveedorItem {
  proveedor_id: number; proveedor: string; ruc: string; telefono: string
  email: string; saldo_deuda: number; dias_atraso: number; aging: string
}

export interface AgingProveedoresData {
  fecha: string
  resumen: {
    proveedores_con_deuda: number; total_deuda: number
    aging: { '0-30': number; '31-60': number; '61-90': number; '90+': number }
  }
  detalle: AgingProveedorItem[]
}

export interface AuditoriaTop { operacion?: string; tabla?: string; n: number }
export interface AuditoriaFila {
  fecha: string; usuario: string | null
  operacion: string; tabla: string | null; objeto_id: number | null
  resultado: string; ip: string | null; descripcion: string | null; mensaje_error: string | null
}
export interface AuditoriaData {
  resumen: { total_eventos: number; por_resultado: { EXITO: number; ERROR: number; DENEGADO: number } }
  top_operaciones: AuditoriaTop[]
  top_tablas: AuditoriaTop[]
  detalle: AuditoriaFila[]
}

export interface TopIpRow { ip: string; exitosos: number; fallidos: number; bloqueada: boolean }
export interface TopEmailRow { email: string; fallidos: number; ultimo_intento: string }
export interface IntentoPorMotivo { motivo: string; n: number }
export interface IntentoTendencia { fecha: string; total: number; fallidos: number; exitosos: number }
export interface IntentosLoginData {
  resumen: { total_intentos: number; fallidos: number; exitosos: number; tasa_fallo: number; ips_bloqueadas: number }
  top_ips: TopIpRow[]
  top_emails: TopEmailRow[]
  por_motivo: IntentoPorMotivo[]
  tendencia: IntentoTendencia[]
}

export interface PersonalPorRol { rol: string; n: number }
export interface PersonalFila {
  usuario_id: number; email: string; nombre: string; rol: string
  ultima_actividad: string | null; dias_inactivo: number
}
export interface PersonalInactivoData {
  resumen: { total_inactivos: number; promedio_dias_inactivo: number; max_dias_inactivo: number }
  por_rol: PersonalPorRol[]; detalle: PersonalFila[]
}

// ─── Sub-components ───────────────────────────────────────────────────────────

export function KpiCard({ label, value, color = 'text-slate-800' }: { label: string; value: string | number; color?: string }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-4">
      <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
      <p className={`text-lg font-bold mt-0.5 tabular-nums ${color}`}>{value}</p>
    </div>
  )
}

export function FilterBar({ children }: { children: ReactNode }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap items-end gap-4">
      {children}
    </div>
  )
}

export function EmptyState({ icon, text }: { icon: ReactNode; text: string }) {
  return (
    <div className="text-center py-20 text-slate-400">
      <div className="w-12 h-12 mx-auto mb-3 opacity-30">{icon}</div>
      <p className="text-sm font-medium">{text}</p>
    </div>
  )
}
