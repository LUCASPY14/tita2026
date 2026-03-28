import React, { createContext, useContext, ReactNode } from 'react';
import { useNotificationStream } from '../hooks/useNotificationStream';
import { useNotificationsByRole } from '../hooks/useNotificationsByRole';
import type { NotificacionPortal, AlertaSistema, ResumenNotificaciones } from '../types';

interface NotificationContextType {
  // Datos de notificaciones (basado en rol)
  notificaciones: NotificacionPortal[];
  alertas: AlertaSistema[];
  resumen: ResumenNotificaciones | null;
  cargando: boolean;
  error: string | null;
  
  // Estados del stream en tiempo real
  streamConnected: boolean;
  streamConnecting: boolean;
  streamError: string | null;
  lastHeartbeat: Date | null;
  newNotifications: NotificacionPortal[];
  
  // Acciones
  refrescar: () => Promise<void>;
  marcarComoLeida: (id: number) => Promise<void>;
  marcarTodasComoLeidas: () => Promise<void>;
  clearNewNotifications: () => void;
  connectStream: () => void;
  disconnectStream: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

interface NotificationProviderProps {
  children: ReactNode;
}

/**
 * Provider de notificaciones que combina:
 * 1. Hook de notificaciones filtradas por rol (useNotificationsByRole)  
 * 2. Hook de stream en tiempo real (useNotificationStream)
 * 
 * Proporciona una API unificada para:
 * - Gestión de notificaciones basada en roles
 * - Notificaciones en tiempo real via SSE
 * - Integración con react-hot-toast existente
 */
export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  // Hook de notificaciones por rol (sistema existente)
  const {
    notificaciones,
    alertas,
    resumen,
    cargando,
    error,
    refrescar,
    marcarComoLeida,
    marcarTodasComoLeidas,
  } = useNotificationsByRole();

  // Hook de stream en tiempo real (nuevo)
  const {
    isConnected: streamConnected,
    isConnecting: streamConnecting,
    error: streamError,
    lastHeartbeat,
    newNotifications,
    clearNewNotifications,
    connect: connectStream,
    disconnect: disconnectStream,
  } = useNotificationStream();

  return (
    <NotificationContext.Provider
      value={{
        // Datos de notificaciones
        notificaciones,
        alertas,
        resumen,
        cargando,
        error,
        
        // Estados del stream
        streamConnected,
        streamConnecting,
        streamError,
        lastHeartbeat,
        newNotifications,
        
        // Acciones
        refrescar,
        marcarComoLeida,
        marcarTodasComoLeidas,
        clearNewNotifications,
        connectStream,
        disconnectStream,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
};

/**
 * Hook para usar el contexto de notificaciones
 * 
 * @example
 * ```tsx
 * const { notificaciones, streamConnected, newNotifications } = useNotificationContext();
 * ```
 */
export const useNotificationContext = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotificationContext debe usarse dentro de NotificationProvider');
  }
  return context;
};

export default NotificationProvider;