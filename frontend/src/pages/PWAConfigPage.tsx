import React from 'react';
import PWAManager from '../components/common/PWAManager';
import { 
  Smartphone, 
  Settings, 
  Bell, 
  Wifi,
  Shield,
  Zap
} from 'lucide-react';

const PWAConfigPage: React.FC = () => {
  const features = [
    {
      icon: Smartphone,
      title: 'Instalación Nativa',
      description: 'Los usuarios pueden instalar la app como una aplicación nativa en sus dispositivos.',
      benefits: [
        'Acceso rápido desde el escritorio',
        'Funcionamiento como app independiente',
        'Icono en el menú de aplicaciones'
      ]
    },
    {
      icon: Wifi,
      title: 'Funcionamiento Offline',
      description: 'La aplicación funciona parcialmente sin conexión a internet.',
      benefits: [
        'Páginas visitadas disponibles offline',
        'Caché inteligente de recursos',
        'Sincronización cuando vuelve la conexión'
      ]
    },
    {
      icon: Bell,
      title: 'Push Notifications',
      description: 'Notificaciones del sistema para alertas importantes.',
      benefits: [
        'Notificaciones en tiempo real',
        'Alertas de stock bajo',
        'Recordatorios de tareas pendientes'
      ]
    },
    {
      icon: Zap,
      title: 'Carga Rápida',
      description: 'Carga optimizada y cache inteligente para mejor rendimiento.',
      benefits: [
        'Inicio instantáneo después de la primera carga',
        'Recursos optimizados en cache',
        'Experiencia fluida y responsive'
      ]
    }
  ];

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center space-x-3 mb-4">
          <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-3">
            <Settings className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Configuración PWA</h1>
        </div>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Convierte Cantina Tita en una Aplicación Web Progresiva para una mejor experiencia de usuario
        </p>
      </div>

      {/* PWA Manager */}
      <PWAManager />

      {/* Características PWA */}
      <div className="bg-white border border-gray-200 rounded-lg p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          ¿Qué incluye la PWA?
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {features.map((feature, index) => {
            const IconComponent = feature.icon;
            return (
              <div key={index} className="space-y-4">
                <div className="flex items-start space-x-4">
                  <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-3 flex-shrink-0">
                    <IconComponent className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{feature.title}</h3>
                    <p className="text-gray-600 mt-1">{feature.description}</p>
                  </div>
                </div>
                
                <div className="ml-16">
                  <h4 className="font-medium text-gray-900 mb-2">Beneficios:</h4>
                  <ul className="space-y-1">
                    {feature.benefits.map((benefit, idx) => (
                      <li key={idx} className="flex items-center space-x-2 text-sm text-gray-600">
                        <div className="w-1.5 h-1.5 bg-green-500 rounded-full flex-shrink-0" />
                        <span>{benefit}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Guía de instalación */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">
          📱 Guía de Instalación para Usuarios
        </h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Android/Chrome */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
              <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">A</span>
              </div>
              <span>Android / Chrome</span>
            </h3>
            
            <ol className="list-decimal list-inside space-y-2 text-sm text-gray-700">
              <li>Abre la aplicación en Chrome</li>
              <li>Toca el menú (⋮) y selecciona "Instalar app"</li>
              <li>O usa el botón "Instalar App" cuando aparezca</li>
              <li>Confirma la instalación</li>
              <li>La app aparecerá en tu menú de aplicaciones</li>
            </ol>
          </div>
          
          {/* iOS/Safari */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
              <div className="w-6 h-6 bg-gray-800 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">i</span>
              </div>
              <span>iOS / Safari</span>
            </h3>
            
            <ol className="list-decimal list-inside space-y-2 text-sm text-gray-700">
              <li>Abre la aplicación en Safari</li>
              <li>Toca el botón "Compartir" (📤)</li>
              <li>Selecciona "Agregar a pantalla de inicio"</li>
              <li>Personaliza el nombre si deseas</li>
              <li>Toca "Agregar" para completar</li>
            </ol>
          </div>
        </div>
        
        <div className="mt-6 p-4 bg-white rounded-lg border border-blue-200">
          <div className="flex items-start space-x-3">
            <Shield className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-medium text-gray-900">Seguridad y Privacidad</h4>
              <p className="text-sm text-gray-600 mt-1">
                La PWA funciona de forma segura y no requiere permisos especiales. 
                Los datos se mantienen seguros y la aplicación funciona como una versión optimizada del sitio web.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Estadísticas y métricas */}
      <div className="bg-white border border-gray-200 rounded-lg p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Impacto de PWA</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-500 mb-2">~58%</div>
            <p className="text-sm text-gray-600">Aumento en engagement promedio</p>
          </div>
          
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-500 mb-2">~40%</div>
            <p className="text-sm text-gray-600">Mejora en tiempo de carga</p>
          </div>
          
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-500 mb-2">~65%</div>
            <p className="text-sm text-gray-600">Reducción en abandono de sesión</p>
          </div>
        </div>
        
        <p className="text-xs text-gray-500 text-center mt-4">
          * Métricas basadas en estudios de Google sobre PWAs en aplicaciones empresariales
        </p>
      </div>
    </div>
  );
};

export default PWAConfigPage;