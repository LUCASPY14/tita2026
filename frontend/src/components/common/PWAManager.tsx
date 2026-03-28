import React, { useState, useEffect } from 'react';
import { 
  Smartphone, 
  Wifi, 
  WifiOff, 
  Download, 
  RefreshCw, 
  Settings, 
  Bell,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';
import { usePWA } from '../../utils/serviceWorker';

interface PWAManagerProps {
  className?: string;
}

const PWAManager: React.FC<PWAManagerProps> = ({ className = '' }) => {
  const { register, isInstalled, promptInstall, getInfo } = usePWA();
  const [pwaInfo, setPwaInfo] = useState<any>(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const updateInfo = () => {
      const info = getInfo();
      setPwaInfo(info);
    };

    updateInfo();

    // Listeners para eventos de conexión
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Actualizar info periódicamente
    const interval = setInterval(updateInfo, 2000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, [getInfo]);

  const handleInstall = async () => {
    setIsLoading(true);
    try {
      await promptInstall();
    } catch (error) {
      console.error('Error instalando PWA:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegisterSW = async () => {
    setIsLoading(true);
    try {
      const result = await register();
      console.log('Service Worker registrado:', result);
    } catch (error) {
      console.error('Error registrando Service Worker:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const installed = isInstalled();

  // Información de características PWA
  const pwAFeatures = [
    {
      feature: 'Service Worker',
      status: pwaInfo?.isRegistered ? 'enabled' : 'disabled',
      icon: Settings,
      description: 'Habilita cache y funcionalidad offline'
    },
    {
      feature: 'App Instalada',
      status: installed ? 'enabled' : 'disabled', 
      icon: Smartphone,
      description: 'App instalada como aplicación nativa'
    },
    {
      feature: 'Push Notifications',
      status: 'Notification' in window && Notification.permission === 'granted' ? 'enabled' : 'disabled',
      icon: Bell,
      description: 'Notificaciones push del sistema'
    },
    {
      feature: 'Offline Support',
      status: pwaInfo?.isRegistered ? 'enabled' : 'disabled',
      icon: isOnline ? Wifi : WifiOff,
      description: 'Funcionalidad básica sin conexión'
    }
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'enabled':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'disabled':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'enabled':
        return 'bg-green-50 border-green-200';
      case 'disabled':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-yellow-50 border-yellow-200';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Aplicación Web Progresiva</h2>
          <p className="text-gray-600 mt-1">
            Gestiona las características PWA de Cantina Tita
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isOnline ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-gray-600">
            {isOnline ? 'En línea' : 'Sin conexión'}
          </span>
        </div>
      </div>

      {/* Estado general */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {pwAFeatures.map((feature) => {
          const IconComponent = feature.icon;
          return (
            <div
              key={feature.feature}
              className={`p-4 border rounded-lg ${getStatusColor(feature.status)}`}
            >
              <div className="flex items-center justify-between mb-2">
                <IconComponent className="h-6 w-6 text-gray-700" />
                {getStatusIcon(feature.status)}
              </div>
              <h3 className="font-semibold text-gray-900 text-sm">{feature.feature}</h3>
              <p className="text-xs text-gray-600 mt-1">{feature.description}</p>
            </div>
          );
        })}
      </div>

      {/* Acciones */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Acciones PWA</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Instalación */}
          {!installed && (
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Download className="h-5 w-5 text-blue-500" />
                <span className="font-medium text-gray-900">Instalar Aplicación</span>
              </div>
              <p className="text-sm text-gray-600">
                Instala Cantina Tita como app nativa para un acceso más rápido
              </p>
              <button
                onClick={handleInstall}
                disabled={isLoading}
                className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center space-x-2"
              >
                {isLoading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                <span>{isLoading ? 'Instalando...' : 'Instalar App'}</span>
              </button>
            </div>
          )}

          {installed && (
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span className="font-medium text-gray-900">App Instalada</span>
              </div>
              <p className="text-sm text-gray-600">
                La aplicación está instalada y disponible desde tu dispositivo
              </p>
            </div>
          )}

          {/* Service Worker */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Settings className="h-5 w-5 text-purple-500" />
              <span className="font-medium text-gray-900">Service Worker</span>
            </div>
            <p className="text-sm text-gray-600">
              {pwaInfo?.isRegistered 
                ? 'Service Worker activo y funcionando' 
                : 'Registrar Service Worker para funciones offline'}
            </p>
            {!pwaInfo?.isRegistered && (
              <button
                onClick={handleRegisterSW}
                disabled={isLoading}
                className="w-full bg-purple-500 hover:bg-purple-600 disabled:bg-purple-300 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center space-x-2"
              >
                {isLoading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Settings className="h-4 w-4" />
                )}
                <span>{isLoading ? 'Registrando...' : 'Activar Service Worker'}</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Información técnica */}
      {pwaInfo && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Información Técnica</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Estado SW:</span>
              <span className="ml-2 text-gray-600">{pwaInfo.state || 'No registrado'}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Scope:</span>
              <span className="ml-2 text-gray-600">{pwaInfo.scope || 'N/A'}</span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Actualización disponible:</span>
              <span className="ml-2 text-gray-600">
                {pwaInfo.updateAvailable ? 'Sí' : 'No'}
              </span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Display Mode:</span>
              <span className="ml-2 text-gray-600">
                {installed ? 'standalone' : 'browser'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PWAManager;