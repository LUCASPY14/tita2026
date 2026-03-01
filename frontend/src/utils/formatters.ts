import { format, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';

/**
 * Formatea una fecha en formato dd/MM/yyyy
 */
export const formatDate = (date: string | Date | null): string => {
  if (!date) return '';
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, 'dd/MM/yyyy', { locale: es });
};

/**
 * Formatea una fecha y hora en formato dd/MM/yyyy HH:mm
 */
export const formatDateTime = (date: string | Date | null): string => {
  if (!date) return '';
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, 'dd/MM/yyyy HH:mm', { locale: es });
};

/**
 * Formatea un monto en formato de moneda paraguaya
 */
export const formatCurrency = (amount: number | null | undefined): string => {
  if (amount === null || amount === undefined) return 'Gs. 0';
  return `Gs. ${Number(amount).toLocaleString('es-PY')}`;
};

/**
 * Formatea un número con separadores de miles
 */
export const formatNumber = (number: number | null | undefined): string => {
  if (number === null || number === undefined) return '0';
  return Number(number).toLocaleString('es-PY');
};
