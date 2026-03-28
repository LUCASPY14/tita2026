import React from 'react';
import { Wifi, WifiOff, Activity, AlertCircle } from 'lucide-react';
import { useNotificationContext } from '../../contexts/NotificationContext';

interface NotificationStreamIndicatorProps {
  className?: string;
  showLabel?: boolean;
}

/**
 * Indicador visual del estado de conexión del stream de notificaciones
 * 
 * Muestra:
 * - Verde: Conectado
 * - Amarillo: Conectando/Reconectando
 * - Rojo: Error de conexión
 * - Gris: Desconectado
 */
export const NotificationStreamIndicator: React.FC<NotificationStreamIndicatorProps> = ({
  className = '',
  showLabel = false,
}) => {
  const {
    streamConnected,
    streamConnecting,
    streamError,
    lastHeartbeat,
    newNotifications,
  } = useNotificationContext();

  const getStatus = () => {
    if (streamError) return 'error';
    if (streamConnecting) return 'connecting';
    if (streamConnected) return 'connected';
    return 'disconnected';
  };

  const status = getStatus();

  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          icon: Activity,
          color: 'text-green-500',
          bgColor: 'bg-green-100',
          label: 'Conectado',
          animate: 'animate-pulse',
        };
      case 'connecting':
        return {
          icon: Wifi,
          color: 'text-yellow-500',
          bgColor: 'bg-yellow-100',
          label: 'Conectando...',
          animate: 'animate-spin',
        };
      case 'error':
        return {
          icon: AlertCircle,
          color: 'text-red-500',
          bgColor: 'bg-red-100',
          label: 'Error',
          animate: '',
        };
      default:
        return {
          icon: WifiOff,
          color: 'text-gray-400',
          bgColor: 'bg-gray-100',
          label: 'Desconectado',
          animate: '',
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  // Calcular tiempo desde último heartbeat
  const getHeartbeatStatus = () => {
    if (!lastHeartbeat) return null;
    const now = Date.now();
    const lastBeat = lastHeartbeat.getTime();
    const diffSeconds = Math.floor((now - lastBeat) / 1000);
    
    if (diffSeconds > 60) return 'Hace más de 1m';
    if (diffSeconds > 30) return `Hace ${diffSeconds}s`;
    return 'Activo';
  };

  const heartbeatStatus = getHeartbeatStatus();

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Indicador de nuevas notificaciones */}
      {newNotifications.length > 0 && (
        <div className="relative">
          <div className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center animate-bounce">
            {newNotifications.length > 9 ? '9+' : newNotifications.length}
          </div>
        </div>
      )}
      
      {/* Icono de estado principal */}
      <div className={`p-1.5 rounded-full ${config.bgColor} relative group`}>
        <Icon 
          className={`w-4 h-4 ${config.color} ${config.animate}`}
          strokeWidth={2}
        />
        
        {/* Tooltip con información detallada */}
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-800 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50">
          <div className="font-medium">{config.label}</div>
          {heartbeatStatus && (
            <div className="text-gray-300">{heartbeatStatus}</div>
          )}
          {streamError && (
            <div className="text-red-300 mt-1 max-w-xs">{streamError}</div>
          )}
          {/* Flecha del tooltip */}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-800"></div>
        </div>
      </div>
      
      {/* Etiqueta de texto opcional */}
      {showLabel && (
        <span className={`text-sm font-medium ${config.color}`}>
          {config.label}
          {newNotifications.length > 0 && (
            <span className="ml-1 bg-red-100 text-red-800 px-1.5 py-0.5 rounded-full text-xs">
              {newNotifications.length}
            </span>
          )}
        </span>
      )}
    </div>
  );
};

export default NotificationStreamIndicator;