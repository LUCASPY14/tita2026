import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuthContext } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import type { NotificacionPortal } from '../types';

interface NotificationStreamEvent {
  type: 'connected' | 'new_notifications' | 'heartbeat' | 'error';
  message?: string;
  timestamp?: string;
  count?: number;
  notifications?: NotificacionPortal[];
}

interface UseNotificationStreamReturn {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  lastHeartbeat: Date | null;
  connect: () => void;
  disconnect: () => void;
  newNotifications: NotificacionPortal[];
  clearNewNotifications: () => void;
}

/**
 * Hook para gestionar stream de notificaciones en tiempo real via Server-Sent Events
 * 
 * Este hook:
 * - Conecta automáticamente al stream SSE cuando el usuario está autenticado
 * - Maneja reconexión automática en caso de desconexión
 * - Muestra notificaciones toast cuando llegan nuevas notificaciones
 * - Proporciona estado de conexión y control manual
 * 
 * @example
 * ```tsx
 * const { isConnected, newNotifications } = useNotificationStream();
 * ```
 */
export const useNotificationStream = (): UseNotificationStreamReturn => {
  const { user } = useAuthContext();
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastHeartbeat, setLastHeartbeat] = useState<Date | null>(null);
  const [newNotifications, setNewNotifications] = useState<NotificacionPortal[]>([]);
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const clearNewNotifications = useCallback(() => {
    setNewNotifications([]);
  }, []);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    setIsConnected(false);
    setIsConnecting(false);
    setError(null);
    reconnectAttempts.current = 0;
  }, []);

  const connect = useCallback(() => {
    if (!user?.id || eventSourceRef.current) {
      return;
    }

    setIsConnecting(true);
    setError(null);

    const url = `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/notificaciones-portal/stream/?id_usuario_portal=${user.id}`;
    
    try {
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        reconnectAttempts.current = 0;
        console.log('✅ Conectado al stream de notificaciones');
      };

      eventSource.onmessage = (event) => {
        try {
          const data: NotificationStreamEvent = JSON.parse(event.data);
          
          switch (data.type) {
            case 'connected':
              console.log('📡 Stream de notificaciones establecido');
              break;
              
            case 'new_notifications':
              if (data.notifications && data.notifications.length > 0) {
                setNewNotifications(prev => [...data.notifications!, ...prev].slice(0, 50)); // Mantener últimas 50
                
                // Mostrar toast para nuevas notificaciones
                const count = data.count || data.notifications.length;
                if (count === 1) {
                  const notif = data.notifications[0];
                  toast.success(`${notif.titulo}`, {
                    duration: 5000,
                    icon: '🔔',
                  });
                } else {
                  toast.success(`${count} nuevas notificaciones`, {
                    duration: 4000,
                    icon: '🔔',
                  });
                }
              }
              break;
              
            case 'heartbeat':
              setLastHeartbeat(new Date(data.timestamp!));
              break;
              
            case 'error':
              setError(data.message || 'Error en el stream');
              break;
          }
        } catch (parseError) {
          console.error('Error parsing SSE data:', parseError);
        }
      };

      eventSource.onerror = () => {
        setIsConnected(false);
        setIsConnecting(false);
        
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000); // Exponential backoff, max 30s
          
          setError(`Desconectado. Reintentando en ${delay / 1000}s... (${reconnectAttempts.current}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            disconnect();
            connect();
          }, delay);
        } else {
          setError('No se pudo mantener la conexión. Verifica tu conexión a internet.');
          disconnect();
        }
      };

    } catch (err) {
      setIsConnecting(false);
      setError('Error al establecer conexión SSE');
      console.error('SSE connection error:', err);
    }
  }, [user?.id, disconnect]);

  // Auto-conectar cuando el usuario está autenticado
  useEffect(() => {
    if (!user?.id) {
      connect();
    } else {
      disconnect();
    }

    // Cleanup al desmontar
    return () => {
      disconnect();
    };
  }, [user?.id, connect, disconnect]);

  // Cleanup de timeouts al desmontar
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    isConnected,
    isConnecting,
    error,
    lastHeartbeat,
    connect,
    disconnect,
    newNotifications,
    clearNewNotifications,
  };
};

export default useNotificationStream;