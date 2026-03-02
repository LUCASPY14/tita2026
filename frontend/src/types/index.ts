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


