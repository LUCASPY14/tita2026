// Tipos globales y compartidos

export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  first_name?: string;
  last_name?: string;
}

// Tipos para módulo de Clientes
export interface Cliente {
  id_cliente: number;
  nombres: string;
  apellidos: string;
  razon_social?: string;
  ruc_ci: string;
  direccion?: string;
  ciudad?: string;
  telefono?: string;
  email?: string;
  limite_credito?: number;
  activo: boolean;
  fecha_registro: string;
  id_lista: number;
  id_tipo_cliente: number;
  // Propiedades calculadas (desde backend)
  nombre_completo?: string;
  credito_utilizado?: number;
  credito_disponible?: number;
  tiene_credito_disponible?: boolean;
  porcentaje_credito_usado?: number;
}

export interface TipoCliente {
  id_tipo_cliente: number;
  nombre: string;
  descripcion?: string;
  activo: boolean;
}

export interface CuentaCorriente {
  total_debe: number;
  total_haber: number;
  saldo_neto: number;
  limite_credito: number;
  credito_disponible: number;
  porcentaje_usado: number;
  cantidad_facturas_pendientes: number;
  cantidad_notas_credito: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  message: string;
  errors?: Record<string, string[]>;
  status?: number;
}

// Tipos para módulo de Recargas
export interface Hijo {
  id_hijo: number;
  nombre: string;
  apellido: string;
  fecha_nacimiento?: string;
  grado?: string;
  foto_perfil?: string;
  activo: boolean;
  id_cliente_responsable: number;
  nombre_completo?: string;
}

export interface Tarjeta {
  nro_tarjeta: string;
  saldo_actual: number;
  estado: 'Activa' | 'Bloqueada' | 'Inactiva';
  fecha_vencimiento?: string;
  saldo_alerta?: number;
  fecha_creacion: string;
  permite_saldo_negativo: boolean;
  limite_credito: number;
  notificar_saldo_bajo: boolean;
  id_hijo: number;
  codigo_barras?: string;
  hijo_nombre?: string;
  hijo_apellido?: string;
  saldo_disponible?: number;
}

export interface CargaSaldo {
  id_carga: number;
  fecha_carga: string;
  monto_cargado: number;
  referencia?: string;
  estado: 'Pendiente' | 'Confirmada' | 'Rechazada' | 'Cancelada';
  pay_request_id?: string;
  tx_id?: string;
  fecha_confirmacion?: string;
  custom_identifier?: string;
  nro_tarjeta: string;
  id_cliente_origen?: number;
  tarjeta_numero?: string;
  hijo_nombre?: string;
  cliente_nombre?: string;
  metodo_pago?: 'efectivo' | 'tarjeta_pos' | 'transferencia' | 'bancard';
  numero_comprobante?: string;
}

// Tipos para módulo de POS y Productos
export interface Producto {
  id_producto: number;
  codigo_barra?: string;
  descripcion: string;
  stock_minimo: number;
  permite_stock_negativo: boolean;
  activo: boolean;
  id_categoria: number;
  id_impuesto: number;
  id_unidad_medida?: number;
  // Propiedades calculadas/relacionadas
  categoria_nombre?: string;
  unidad_medida_nombre?: string;
  unidad_medida_abreviatura?: string;
  precio?: number; // Precio según lista del cliente
  stock_actual?: number;
  requiere_reposicion?: boolean;
}

export interface Categoria {
  id_categoria: number;
  nombre: string;
  activo: boolean;
  id_categoria_padre?: number;
  // Propiedades calculadas
  es_categoria_raiz?: boolean;
  nombre_completo?: string;
}

export interface UnidadMedida {
  id_unidad_medida: number;
  nombre: string;
  abreviatura: string;
  activo: boolean;
}

export interface ListaPrecio {
  id_lista: number;
  nombre_lista: string;
  fecha_vigencia?: string;
  moneda: string;
  activo: boolean;
}

export interface PrecioPorLista {
  id_precio: number;
  precio_unitario: number;
  fecha_vigencia: string;
  id_lista: number;
  id_producto: number;
  // Propiedades relacionadas
  lista_nombre?: string;
  producto_descripcion?: string;
}

export interface HistoricoPrecio {
  id_historico: number;
  precio_anterior: number;
  precio_nuevo: number;
  fecha_cambio: string;
  id_empleado?: number;
  id_producto: number;
  // Propiedades calculadas
  variacion_porcentual?: number;
  empleado_nombre?: string;
  producto_descripcion?: string;
}

export interface ItemCarrito {
  producto: Producto;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

export interface MedioPago {
  id_medio_pago: number;
  nombre: string;
  genera_comision: boolean;
  activo: boolean;
}

export interface VentaData {
  id_cliente?: number;
  id_hijo?: number;
  nro_tarjeta?: string;
  tipo_venta: 'Contado' | 'Credito';
  id_medio_pago?: number;
  numero_comprobante?: string;
  detalles: {
    id_producto: number;
    cantidad: number;
    precio_unitario: number;
  }[];
}

export interface Venta {
  id_venta: number;
  nro_factura_venta?: number;
  fecha: string;
  monto_total: number;
  saldo_pendiente: number;
  estado_pago: string;
  estado: string;
  tipo_venta: string;
  id_cliente?: number;
  id_hijo?: number;
  cliente_nombre?: string;
  hijo_nombre?: string;
}



// Tipos para módulo de Compras
export interface Proveedor {
  id_proveedor: number;
  ruc: string;
  razon_social: string;
  telefono?: string;
  email?: string;
  direccion?: string;
  ciudad?: string;
  activo: boolean;
  fecha_registro: string;
}

export interface Compra {
  id_compra: number;
  fecha: string;
  monto_total: number;
  saldo_pendiente: number;
  estado_pago: 'Pendiente' | 'Parcial' | 'Pagado';
  nro_factura?: string;
  observaciones?: string;
  id_proveedor: number;
  id_documento?: number;
  // Propiedades relacionadas
  proveedor_nombre?: string;
  detalles?: DetalleCompra[];
}

export interface DetalleCompra {
  id_detalle: number;
  costo_unitario: number;
  cantidad: number;
  subtotal: number;
  monto_iva?: number;
  id_compra: number;
  id_producto: number;
  // Propiedades relacionadas
  producto_nombre?: string;
  producto_descripcion?: string;
}

export interface CompraData {
  fecha: string;
  id_proveedor: number;
  nro_factura?: string;
  observaciones?: string;
  detalles: {
    id_producto: number;
    cantidad: number;
    costo_unitario: number;
  }[];
}

export interface PagoProveedor {
  id_pago_proveedor: number;
  fecha_creacion: string;
  id_medio_pago: number;
  // Propiedades relacionadas
  medio_pago_descripcion?: string;
}

export interface NotaCreditoProveedor {
  id_nota_proveedor: number;
  nro_factura_compra?: number;
  fecha: string;
  monto_total: number;
  observacion?: string;
  estado: 'Pendiente' | 'Aplicada' | 'Cancelada';
  fecha_creacion: string;
  id_compra_original?: number;
  id_proveedor: number;
  // Propiedades relacionadas
  proveedor_nombre?: string;
}

export interface CuentaCorrienteProveedor {
  total_compras: number;
  total_pagado: number;
  saldo_pendiente: number;
  compras_pendientes: number;
  notas_credito: number;
  proveedor?: {
    id: number;
    razon_social: string;
    ruc: string;
  };
}

// Tipos para módulo de Almuerzos
export interface PlanAlmuerzo {
  id_plan_almuerzo: number;
  nombre_plan: string;
  descripcion?: string;
  precio_mensual: number;
  dias_semana_incluidos: string;
  fecha_creacion?: string;
  activo: boolean;
}

export interface TipoAlmuerzo {
  id_tipo_almuerzo: number;
  nombre: string;
  descripcion?: string;
  precio_unitario: number;
  incluye_plato_principal: boolean;
  incluye_postre: boolean;
  incluye_bebida: boolean;
  fecha_creacion: string;
  activo: boolean;
}

export interface SuscripcionAlmuerzo {
  id_suscripcion: number;
  fecha_inicio: string;
  fecha_fin?: string;
  estado: 'Activa' | 'Pendiente' | 'Finalizada' | 'Cancelada';
  id_hijo: number;
  id_plan_almuerzo: number;
  // Propiedades relacionadas
  hijo_nombre?: string;
  plan_nombre?: string;
}

export interface RegistroConsumoAlmuerzo {
  id_registro_consumo: number;
  fecha_consumo: string;
  hora_registro: string;
  costo_almuerzo?: number;
  ya_cobrado: boolean;
  marcado_en_cuenta: boolean;
  estado: 'Confirmado' | 'Pendiente' | 'Rechazado';
  motivo_rechazo?: string;
  id_hijo: number;
  id_suscripcion?: number;
  id_tipo_almuerzo?: number;
  nro_tarjeta?: string;
  id_empleado_registro?: number;
  // Propiedades relacionadas
  hijo_nombre?: string;
  tipo_almuerzo_nombre?: string;
}

export interface CuentaAlmuerzoMensual {
  id_cuenta: number;
  anio: number;
  mes: number;
  cantidad_almuerzos: number;
  monto_total: number;
  forma_cobro: string;
  monto_pagado: number;
  estado: 'Pendiente' | 'Pagada' | 'Parcial';
  fecha_generacion: string;
  fecha_actualizacion: string;
  observaciones?: string;
  id_hijo: number;
}

export interface Alergeno {
  id_alergeno: number;
  nombre: string;
  descripcion?: string;
  palabras_clave: string[];
  nivel_severidad: 'Bajo' | 'Medio' | 'Alto';
  icono?: string;
  activo: boolean;
  fecha_creacion: string;
  usuario_creacion?: string;
}

export interface RegistroConsumoData {
  fecha_consumo: string;
  id_hijo: number;
  nro_tarjeta: string;
  id_tipo_almuerzo?: number;
  id_suscripcion?: number;
}

// Tipos para módulo de Reportes y Estadísticas
export interface ReporteVentas {
  fecha_inicio: string;
  fecha_fin: string;
  total_ventas: number;
  total_monto: number;
  promedio_ticket: number;
  ventas_efectivo: number;
  ventas_tarjeta: number;
  ventas_online: number;
  top_productos: TopProductoVenta[];
  ventas_por_dia: VentaPorDia[];
  detalles: DetalleVentaReporte[];
}

export interface TopProductoVenta {
  id_producto__nombre: string;
  id_producto__codigo: string;
  cantidad_vendida: number;
  total_vendido: number;
}

export interface VentaPorDia {
  fecha: string;
  cantidad: number;
  monto_total: number;
}

export interface DetalleVentaReporte {
  id_venta: number;
  fecha_venta: string;
  total: number;
  metodo_pago: string;
  id_empleado__nombre: string;
  id_empleado__apellido: string;
}

export interface ReporteRecargas {
  fecha_inicio: string;
  fecha_fin: string;
  total_recargas: number;
  total_acreditado: number;
  total_comisiones: number;
  total_cobrado: number;
  recargas_por_metodo: RecargaPorMetodo[];
  recargas_por_estado: RecargaPorEstado[];
  estadisticas_diarias: EstadisticaDiariaRecarga[];
}

export interface RecargaPorMetodo {
  metodo_pago: string;
  cantidad: number;
  monto_total: number;
  comision_total: number;
}

export interface RecargaPorEstado {
  estado: string;
  cantidad: number;
  monto_total: number;
}

export interface EstadisticaDiariaRecarga {
  fecha: string;
  cantidad_recargas: number;
  monto_acreditado: number;
  comision_total: number;
}

export interface ReporteTopProductos {
  fecha_inicio: string;
  fecha_fin: string;
  top_productos: ProductoMasVendido[];
  total_productos_vendidos: number;
  monto_total_ventas: number;
}

export interface ProductoMasVendido {
  id_producto__id_producto: number;
  id_producto__codigo: string;
  id_producto__nombre: string;
  id_producto__id_categoria__nombre: string;
  cantidad_vendida: number;
  total_vendido: number;
  precio_promedio: number;
  ventas_count: number;
}

export interface ReporteConsumosTarjeta {
  nro_tarjeta: string;
  estudiante: string;
  total_consumos: number;
  monto_total_consumido: number;
  saldo_inicial: number;
  saldo_final: number;
  consumos: ConsumoDetalle[];
}

export interface ConsumoDetalle {
  id_consumo: number;
  fecha_consumo: string;
  monto_consumido: number;
  saldo_anterior: number;
  saldo_nuevo: number;
  id_venta__id_venta?: number;
}

export interface ReporteFinanciero {
  fecha_inicio: string;
  fecha_fin: string;
  ingresos_ventas: number;
  ingresos_recargas: number;
  comisiones_cobradas: number;
  ingreso_total: number;
  costo_inventario: number;
  margen_bruto: number;
  porcentaje_margen: number;
}

export interface DashboardKPIs {
  fecha: string;
  ventas_del_dia: number;
  cantidad_ventas: number;
  recargas_del_dia: number;
  cantidad_recargas: number;
  tarjetas_activas: number;
  productos_bajo_stock: number;
  ticket_promedio: number;
  saldo_total_tarjetas: number;
}

export interface DashboardVentas {
  periodo: string;
  fecha_inicio: string;
  fecha_fin: string;
  ventas_por_dia: VentaDiaDashboard[];
  ventas_por_metodo_pago: VentaPorMetodoPago[];
  productos_mas_vendidos: ProductoDashboard[];
  comparacion_semana_anterior: ComparacionPeriodo;
  tendencia: 'crecimiento' | 'decrecimiento' | 'estable';
}

export interface VentaDiaDashboard {
  fecha: string;
  cantidad_ventas: number;
  total_vendido: number;
  ticket_promedio: number;
}

export interface VentaPorMetodoPago {
  metodo_pago: string;
  cantidad: number;
  total: number;
}

export interface ProductoDashboard {
  id_producto__nombre: string;
  id_producto__codigo: string;
  cantidad_vendida: number;
  total_vendido: number;
}

export interface ComparacionPeriodo {
  periodo_actual: number;
  periodo_anterior: number;
  variacion_porcentual: number;
}

export interface DashboardRecargas {
  periodo: string;
  fecha_inicio: string;
  fecha_fin: string;
  recargas_por_dia: RecargaDiaDashboard[];
  recargas_por_metodo: RecargaPorMetodoDashboard[];
  comisiones_generadas: number;
  total_recargas: number;
  recargas_exitosas: number;
  tasa_exito: number;
}

export interface RecargaDiaDashboard {
  fecha: string;
  cantidad_recargas: number;
  monto_total: number;
  comision_total: number;
}

export interface RecargaPorMetodoDashboard {
  metodo_pago: string;
  cantidad: number;
  monto_total: number;
  comision_total: number;
}

export interface DashboardFinanciero {
  mes: number;
  fecha_inicio: string;
  fecha_fin: string;
  ingresos_totales: number;
  ingresos_ventas: number;
  ingresos_comisiones: number;
  gastos_estimados: number;
  margen_neto: number;
  proyeccion_fin_mes: number;
  dias_transcurridos: number;
  dias_totales: number;
}

// Parámetros para consultas de reportes
export interface ReporteVentasParams {
  fecha_inicio: string;
  fecha_fin: string;
  metodo_pago?: string;
  id_empleado?: number;
}

export interface ReporteRecargasParams {
  fecha_inicio: string;
  fecha_fin: string;
  metodo_pago?: string;
  estado?: string;
}

export interface ReporteTopProductosParams {
  fecha_inicio: string;
  fecha_fin: string;
  limite?: number;
}

export interface ReporteConsumosTarjetaParams {
  nro_tarjeta: string;
  fecha_inicio: string;
  fecha_fin: string;
}

export interface ReporteFinancieroParams {
  fecha_inicio: string;
  fecha_fin: string;
}

export interface DashboardVentasParams {
  dias?: number;
}

export interface DashboardRecargasParams {
  dias?: number;
}

export interface DashboardFinancieroParams {
  mes?: number;
}
