/**
 * Push Notification Manager Component
 * Maneja suscripciones y recepción de notificaciones en el frontend
 */

import { useEffect, useState, useCallback } from 'react';
import { toast } from 'react-hot-toast';
import { Bell, BellOff, Settings, Check, X } from 'lucide-react';

interface PushNotificationManagerProps {
  userId?: string;
  onSubscriptionChange?: (subscribed: boolean) => void;
}

interface NotificationPermissionState {
  state: NotificationPermission;
  supported: boolean;
}

export function PushNotificationManager({ 
  onSubscriptionChange 
}: Omit<PushNotificationManagerProps, 'userId'>) {
  const [permission, setPermission] = useState<NotificationPermissionState>({
    state: 'default',
    supported: 'Notification' in window && 'serviceWorker' in navigator
  });
  
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [vapidPublicKey, setVapidPublicKey] = useState<string | null>(null);
  const [subscription, setSubscription] = useState<PushSubscription | null>(null);

  // Obtener VAPID public key del backend
  const getVapidPublicKey = useCallback(async () => {
    try {
      const response = await fetch('/api/push/vapid-public-key');
      const data = await response.json();
      
      if (data.publicKey) {
        setVapidPublicKey(data.publicKey);
        return data.publicKey;
      } else {
        throw new Error('No VAPID public key available');
      }
    } catch (error) {
      console.error('Error getting VAPID key:', error);
      toast.error('Error obteniendo configuración de notificaciones');
      return null;
    }
  }, []);

  // Verificar estado inicial
  useEffect(() => {
    const checkInitialState = async () => {
      if (!permission.supported) {
        console.log('Push notifications not supported');
        return;
      }

      // Verificar permisos
      const currentPermission = Notification.permission;
      setPermission(prev => ({ ...prev, state: currentPermission }));

      // Verificar suscripción existente
      try {
        const registration = await navigator.serviceWorker.ready;
        const existingSubscription = await registration.pushManager.getSubscription();
        
        if (existingSubscription) {
          setSubscription(existingSubscription);
          setIsSubscribed(true);
          console.log('Existing push subscription found');
        }
      } catch (error) {
        console.error('Error checking existing subscription:', error);
      }

      // Obtener VAPID key
      await getVapidPublicKey();
    };

    checkInitialState();
  }, [permission.supported, getVapidPublicKey]);

  // Convertir VAPID key a Uint8Array
  const urlBase64ToUint8Array = (base64String: string): Uint8Array => {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  };

  // Suscribirse a notificaciones
  const subscribe = async () => {
    if (!permission.supported) {
      toast.error('Las notificaciones no están soportadas en este navegador');
      return;
    }

    setIsLoading(true);

    try {
      // Solicitar permisos
      const notificationPermission = await Notification.requestPermission();
      setPermission(prev => ({ ...prev, state: notificationPermission }));

      if (notificationPermission !== 'granted') {
        toast.error('Permisos de notificación denegados');
        return;
      }

      // Obtener VAPID key si no la tenemos
      let publicKey = vapidPublicKey;
      if (!publicKey) {
        publicKey = await getVapidPublicKey();
        if (!publicKey) return;
      }

      // Suscribirse via Service Worker
      const registration = await navigator.serviceWorker.ready;
      const pushSubscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(publicKey) as Uint8Array<ArrayBuffer>
      });

      // Enviar suscripción al backend
      const response = await fetch('/api/push/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken') || ''
        },
        body: JSON.stringify({
          subscription: pushSubscription.toJSON()
        })
      });

      const result = await response.json();

      if (result.success) {
        setSubscription(pushSubscription);
        setIsSubscribed(true);
        onSubscriptionChange?.(true);
        toast.success('¡Notificaciones activadas!');
        
        // Enviar notificación de prueba
        setTimeout(() => sendTestNotification(), 1000);
      } else {
        throw new Error(result.error || 'Error en suscripción');
      }

    } catch (error) {
      console.error('Subscription error:', error);
      toast.error(`Error: ${error instanceof Error ? error.message : 'Error desconocido'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Desuscribirse
  const unsubscribe = async () => {
    if (!subscription) return;

    setIsLoading(true);

    try {
      // Desuscribir del navegador
      await subscription.unsubscribe();

      // Notificar al backend
      const response = await fetch('/api/push/unsubscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken') || ''
        }
      });

      const result = await response.json();

      if (result.success) {
        setSubscription(null);
        setIsSubscribed(false);
        onSubscriptionChange?.(false);
        toast.success('Notificaciones desactivadas');
      } else {
        throw new Error(result.error || 'Error al desuscribir');
      }

    } catch (error) {
      console.error('Unsubscribe error:', error);
      toast.error(`Error: ${error instanceof Error ? error.message : 'Error desconocido'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Enviar notificación de prueba
  const sendTestNotification = async () => {
    try {
      const response = await fetch('/api/push/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken') || ''
        }
      });

      const result = await response.json();

      if (!result.success) {
        console.warn('Test notification failed:', result.error);
      }
    } catch (error) {
      console.error('Test notification error:', error);
    }
  };

  // Helper para obtener cookie CSRF
  const getCookie = (name: string): string | null => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  };

  // Configurar listeners para notificaciones
  useEffect(() => {
    if (!permission.supported || !isSubscribed) return;

    const handleNotificationClick = (event: any) => {
      console.log('Notification clicked:', event);
      
      // Cerrar notificación
      event.notification.close();

      // Manejar acciones específicas
      const data = event.notification.data;
      if (data?.type === 'order' && data?.orderId) {
        // Navegar a la orden
        window.open(`/ordenes/${data.orderId}`, '_blank');
      } else if (data?.type === 'payment') {
        // Navegar a pagos
        window.open('/pagos', '_blank');
      }

      // Enfocar ventana
      if ('clients' in self && typeof self.clients !== 'undefined') {
        (self.clients as any).matchAll().then((clients: any) => {
          if (clients.length > 0) {
            clients[0].focus();
          }
        });
      }
    };

    // Registrar listener en service worker
    navigator.serviceWorker.addEventListener('message', (event) => {
      if (event.data?.type === 'NOTIFICATION_CLICKED') {
        handleNotificationClick(event.data);
      }
    });

    return () => {
      // Cleanup listeners
    };
  }, [permission.supported, isSubscribed]);

  if (!permission.supported) {
    return (
      <div className="flex items-center gap-2 text-gray-500">
        <BellOff className="h-4 w-4" />
        <span className="text-sm">Notificaciones no soportadas</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      {/* Estado de notificaciones */}
      <div className="flex items-center gap-2">
        {isSubscribed ? (
          <div className="flex items-center gap-1 text-green-600">
            <Bell className="h-4 w-4" />
            <span className="text-sm font-medium">ON</span>
          </div>
        ) : (
          <div className="flex items-center gap-1 text-gray-400">
            <BellOff className="h-4 w-4" />
            <span className="text-sm">OFF</span>
          </div>
        )}
      </div>

      {/* Botón de toggle */}
      <button
        onClick={isSubscribed ? unsubscribe : subscribe}
        disabled={isLoading}
        className={`
          flex items-center gap-1 px-2 py-1 rounded text-sm font-medium transition-colors
          ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-100'}
          ${isSubscribed ? 'text-red-600 hover:bg-red-50' : 'text-blue-600 hover:bg-blue-50'}
        `}
        title={isSubscribed ? 'Desactivar notificaciones' : 'Activar notificaciones'}
      >
        {isLoading ? (
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
        ) : isSubscribed ? (
          <X className="h-4 w-4" />
        ) : (
          <Check className="h-4 w-4" />
        )}
        <span>
          {isLoading ? 'Procesando...' : isSubscribed ? 'Desactivar' : 'Activar'}
        </span>
      </button>

      {/* Botón de configuración (futuro) */}
      {isSubscribed && (
        <button
          className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
          title="Configurar notificaciones"
          onClick={() => toast('Configuración próximamente', { icon: '⚙️' })}
        >
          <Settings className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}