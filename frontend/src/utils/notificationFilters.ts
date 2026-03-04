import { UserRole } from '../services/auth.service';
import type { AlertaSistema, NotificacionPortal } from '../types';

/**
 * Configuración de tipos de alerta y roles objetivo
 */
export interface AlertaConfig {
  tipo: string;
  criticidad: 'critico' | 'alto' | 'medio' | 'bajo';
  rolesObjetivo: UserRole[];
  descripcion: string;
}

/**
 * Configuración de alertas del sistema
 * Define qué roles deben ver cada tipo de alerta
 */
export const ALERTAS_CONFIG: Record<string, AlertaConfig> = {
  // Alertas Críticas - Solo Admin y Gerente
  'Sistema Caído': {
    tipo: 'Sistema Caído',
    criticidad: 'critico',
    rolesObjetivo: ['admin', 'gerente'],
    descripcion: 'Problema crítico del sistema',
  },
  'Error de Base de Datos': {
    tipo: 'Error de Base de Datos',
    criticidad: 'critico',
    rolesObjetivo: ['admin'],
    descripcion: 'Error en la base de datos',
  },
  'Seguridad Comprometida': {
    tipo: 'Seguridad Comprometida',
    criticidad: 'critico',
    rolesObjetivo: ['admin'],
    descripcion: 'Posible brecha de seguridad',
  },
  
  // Alertas Altas - Admin, Gerente
  'Stock Crítico': {
    tipo: 'Stock Crítico',
    criticidad: 'alto',
    rolesObjetivo: ['admin', 'gerente'],
    descripcion: 'Producto con stock crítico',
  },
  'Cuenta por Pagar Vencida': {
    tipo: 'Cuenta por Pagar Vencida',
    criticidad: 'alto',
    rolesObjetivo: ['admin', 'gerente'],
    descripcion: 'Deuda vencida con proveedor',
  },
  'Cuenta por Cobrar Vencida': {
    tipo: 'Cuenta por Cobrar Vencida',
    criticidad: 'alto',
    rolesObjetivo: ['admin', 'gerente'],
    descripcion: 'Cliente con deuda vencida',
  },
  'Límite de Crédito Excedido': {
    tipo: 'Límite de Crédito Excedido',
    criticidad: 'alto',
    rolesObjetivo: ['admin', 'gerente', 'cajero'],
    descripcion: 'Cliente sobrepasó límite de crédito',
  },
  
  // Alertas Medias - Admin, Gerente, Cajero
  'Stock Bajo': {
    tipo: 'Stock Bajo',
    criticidad: 'medio',
    rolesObjetivo: ['admin', 'gerente', 'cajero'],
    descripcion: 'Producto con stock bajo',
  },
  'Venta Grande': {
    tipo: 'Venta Grande',
    criticidad: 'medio',
    rolesObjetivo: ['admin', 'gerente'],
    descripcion: 'Venta de monto elevado',
  },
  'Devolución de Producto': {
    tipo: 'Devolución de Producto',
    criticidad: 'medio',
    rolesObjetivo: ['admin', 'gerente', 'cajero'],
    descripcion: 'Cliente devolvió producto',
  },
  
  // Alertas Bajas - Todos
  'Producto Próximo a Vencer': {
    tipo: 'Producto Próximo a Vencer',
    criticidad: 'bajo',
    rolesObjetivo: ['admin', 'gerente', 'cajero', 'empleado'],
    descripcion: 'Producto próximo a vencer',
  },
  'Recordatorio': {
    tipo: 'Recordatorio',
    criticidad: 'bajo',
    rolesObjetivo: ['admin', 'gerente', 'cajero', 'empleado'],
    descripcion: 'Recordatorio general',
  },
};

/**
 * Configuración de tipos de notificaciones
 */
export interface NotificacionConfig {
  tipo: string;
  rolesObjetivo: UserRole[];
  descripcion: string;
}

export const NOTIFICACIONES_CONFIG: Record<string, NotificacionConfig> = {
  // Notificaciones específicas por rol
  'Nueva Venta': {
    tipo: 'Nueva Venta',
    rolesObjetivo: ['admin', 'gerente', 'cajero'],
    descripcion: 'Se registró una nueva venta',
  },
  'Pago Recibido': {
    tipo: 'Pago Recibido',
    rolesObjetivo: ['admin', 'gerente', 'cajero'],
    descripcion: 'Se recibió un pago',
  },
  'Cliente Nuevo': {
    tipo: 'Cliente Nuevo',
    rolesObjetivo: ['admin', 'gerente'],
    descripcion: 'Nuevo cliente registrado',
  },
  'Producto Nuevo': {
    tipo: 'Producto Nuevo',
    rolesObjetivo: ['admin', 'gerente'],
    descripcion: 'Nuevo producto agregado',
  },
  'Reporte Generado': {
    tipo: 'Reporte Generado',
    rolesObjetivo: ['admin', 'gerente'],
    descripcion: 'Reporte listo para descargar',
  },
  'Tarea Asignada': {
    tipo: 'Tarea Asignada',
    rolesObjetivo: ['admin', 'gerente', 'cajero', 'empleado'],
    descripcion: 'Nueva tarea asignada',
  },
  'Mensaje del Sistema': {
    tipo: 'Mensaje del Sistema',
    rolesObjetivo: ['admin', 'gerente', 'cajero', 'empleado'],
    descripcion: 'Mensaje general del sistema',
  },
  'Actualización Disponible': {
    tipo: 'Actualización Disponible',
    rolesObjetivo: ['admin'],
    descripcion: 'Nueva versión disponible',
  },
};

/**
 * Determina si una alerta es relevante para un rol específico
 */
export const esAlertaRelevante = (
  alerta: AlertaSistema,
  userRole: UserRole
): boolean => {
  // Si la alerta tiene roles_objetivo definidos, usar esos
  if (alerta.roles_objetivo && alerta.roles_objetivo.length > 0) {
    return alerta.roles_objetivo.includes(userRole);
  }

  // Si no, usar la configuración por tipo
  const config = ALERTAS_CONFIG[alerta.tipo];
  if (!config) {
    // Si no hay configuración, mostrar solo a admin y gerente
    return userRole === 'admin' || userRole === 'gerente';
  }

  return config.rolesObjetivo.includes(userRole);
};

/**
 * Determina si una notificación es relevante para un rol específico
 */
export const esNotificacionRelevante = (
  notificacion: NotificacionPortal,
  userRole: UserRole
): boolean => {
  const config = NOTIFICACIONES_CONFIG[notificacion.tipo];
  if (!config) {
    // Si no hay configuración, mostrar a todos
    return true;
  }

  return config.rolesObjetivo.includes(userRole);
};

/**
 * Filtra alertas según el rol del usuario
 */
export const filtrarAlertasPorRol = (
  alertas: AlertaSistema[],
  userRole: UserRole
): AlertaSistema[] => {
  if (!alertas || !Array.isArray(alertas)) {
    return [];
  }
  return alertas.filter(alerta => esAlertaRelevante(alerta, userRole));
};

/**
 * Filtra notificaciones según el rol del usuario
 */
export const filtrarNotificacionesPorRol = (
  notificaciones: NotificacionPortal[],
  userRole: UserRole
): NotificacionPortal[] => {
  if (!notificaciones || !Array.isArray(notificaciones)) {
    return [];
  }
  return notificaciones.filter(notif => esNotificacionRelevante(notif, userRole));
};

/**
 * Obtiene la criticidad de una alerta (para ordenamiento)
 */
export const getCriticidadNivel = (criticidad?: string): number => {
  const niveles: Record<string, number> = {
    'critico': 4,
    'alto': 3,
    'medio': 2,
    'bajo': 1,
  };
  return niveles[criticidad || 'bajo'] || 0;
};

/**
 * Ordena alertas por criticidad (más críticas primero)
 */
export const ordenarAlertasPorCriticidad = (alertas: AlertaSistema[]): AlertaSistema[] => {
  if (!alertas || !Array.isArray(alertas)) {
    return [];
  }
  return [...alertas].sort((a, b) => {
    const nivelA = getCriticidadNivel(a.criticidad);
    const nivelB = getCriticidadNivel(b.criticidad);
    return nivelB - nivelA;
  });
};

/**
 * Enriquece alertas con información de criticidad basada en config
 */
export const enriquecerAlertas = (alertas: AlertaSistema[]): AlertaSistema[] => {
  if (!alertas || !Array.isArray(alertas)) {
    return [];
  }
  return alertas.map(alerta => {
    const config = ALERTAS_CONFIG[alerta.tipo];
    if (config && !alerta.criticidad) {
      return {
        ...alerta,
        criticidad: config.criticidad,
        roles_objetivo: config.rolesObjetivo,
      };
    }
    return alerta;
  });
};

/**
 * Obtiene resumen de notificaciones por criticidad
 */
export interface ResumenCriticidad {
  criticas: number;
  altas: number;
  medias: number;
  bajas: number;
}

export const obtenerResumenCriticidad = (
  alertas: AlertaSistema[]
): ResumenCriticidad => {
  if (!alertas || !Array.isArray(alertas)) {
    return { criticas: 0, altas: 0, medias: 0, bajas: 0 };
  }
  return {
    criticas: alertas.filter(a => a.criticidad === 'critico').length,
    altas: alertas.filter(a => a.criticidad === 'alto').length,
    medias: alertas.filter(a => a.criticidad === 'medio').length,
    bajas: alertas.filter(a => a.criticidad === 'bajo').length,
  };
};
