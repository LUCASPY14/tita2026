export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
export const APP_NAME = import.meta.env.VITE_APP_NAME || 'Cantina Tita';

export const PAGINATION_SIZE = 10;
export const MAX_PAGE_SIZE = 100;

export interface MetodoPago {
  value: string;
  label: string;
}

export interface EstadoVenta {
  value: string;
  label: string;
}

export const METODOS_PAGO: MetodoPago[] = [
  { value: 'EFECTIVO', label: 'Efectivo' },
  { value: 'TARJETA', label: 'Tarjeta' },
  { value: 'TRANSFERENCIA', label: 'Transferencia' },
  { value: 'CREDITO', label: 'Crédito' },
];

export const ESTADOS_VENTA: EstadoVenta[] = [
  { value: 'PENDIENTE', label: 'Pendiente' },
  { value: 'COMPLETADA', label: 'Completada' },
  { value: 'CANCELADA', label: 'Cancelada' },
];
