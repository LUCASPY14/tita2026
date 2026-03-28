import React, { useState, useEffect } from 'react';
import { usePWA } from '../../utils/serviceWorker';

interface PWAStatusProps {
  className?: string;
}

const PWAStatus: React.FC<PWAStatusProps> = ({ className = '' }) => {
  const { isInstalled, getInfo } = usePWA();
  const [pwsInfo, setPwaInfo] = useState<any>(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    // Actualizar info del PWA
    const updateInfo = () => {
      const info = getInfo();
      setPwaInfo(info);
    };

    updateInfo();

    // Listeners para estado de conexión
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Actualizar info periódicamente
    const interval = setInterval(updateInfo, 5000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, [getInfo]);

  if (!pwsInfo?.isRegistered) {
    return null;
  }

  const installed = isInstalled();
  
  return (
    <div className={`flex items-center space-x-2 text-xs ${className}`}>
      {/* Indicador de estado de instalación */}
      <div className="flex items-center space-x-1">
        <div 
          className={`w-2 h-2 rounded-full ${
            installed ? 'bg-green-500' : 'bg-yellow-500'
          }`}
          title={installed ? 'PWA Instalada' : 'PWA No Instalada'}
        />
        <span className="text-gray-600">
          {installed ? 'APP' : 'WEB'}
        </span>
      </div>

      {/* Indicador de conexión */}
      <div className="flex items-center space-x-1">
        <div 
          className={`w-2 h-2 rounded-full ${
            isOnline ? 'bg-green-500' : 'bg-red-500'
          }`}
          title={isOnline ? 'En línea' : 'Sin conexión'}
        />
        <span className="text-gray-600">
          {isOnline ? 'ONLINE' : 'OFFLINE'}
        </span>
      </div>

      {/* Indicador de actualización */}
      {pwsInfo.updateAvailable && (
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          <span className="text-blue-600 font-medium">UPDATE</span>
        </div>
      )}

      {/* Indicador de Service Worker activo */}
      {pwsInfo.state === 'activated' && (
        <div className="flex items-center space-x-1">
          <div className="w-2 h-2 rounded-full bg-purple-500" />
          <span className="text-gray-600">SW</span>
        </div>
      )}
    </div>
  );
};

export default PWAStatus;