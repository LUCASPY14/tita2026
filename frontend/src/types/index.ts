// Tipos globales y compartidos

export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  first_name?: string;
  last_name?: string;
}

export interface Cliente {
  id: number;
  nombre: string;
  ruc: string;
  telefono: string;
  email: string;
  direccion?: string;
  created_at: string;
  updated_at: string;
}

export interface Producto {
  id: number;
  codigo: string;
  nombre: string;
  descripcion?: string;
  precio: number;
  stock: number;
  stock_minimo: number;
  categoria?: Categoria;
  imagen?: string;
}

export interface Categoria {
  id: number;
  nombre: string;
  descripcion?: string;
}

export interface Venta {
  id: number;
  numero: string;
  fecha: string;
  cliente: Cliente;
  total: number;
  estado: 'PENDIENTE' | 'COMPLETADA' | 'CANCELADA';
  metodo_pago: 'EFECTIVO' | 'TARJETA' | 'TRANSFERENCIA' | 'CREDITO';
  items: DetalleVenta[];
}

export interface DetalleVenta {
  id: number;
  producto: Producto;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
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

