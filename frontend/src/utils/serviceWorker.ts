/**
 * Registro y gestión del Service Worker para PWA
 * Basado en Workbox pero usando service worker personalizado
 */

interface ServiceWorkerRegistrationResult {
  registration?: ServiceWorkerRegistration;
  error?: Error;
  isSupported: boolean;
}

interface PWAInstallPrompt {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

declare global {
  interface Window {
    deferredPrompt?: PWAInstallPrompt;
  }
}

class ServiceWorkerManager {
  private registration: ServiceWorkerRegistration | null = null;
  private updateAvailable = false;
  private installPrompt: PWAInstallPrompt | null = null;

  /**
   * Registra el service worker
   */
  async register(): Promise<ServiceWorkerRegistrationResult> {
    // Verificar soporte
    if (!('serviceWorker' in navigator)) {
      console.warn('[PWA] Service Worker no soportado en este navegador');
      return { isSupported: false };
    }

    try {
      console.log('[PWA] Registrando Service Worker...');
      
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
      });

      console.log('[PWA] Service Worker registrado exitosamente:', registration.scope);
      this.registration = registration;

      // Configurar listeners
      this.setupUpdateListener(registration);
      this.setupInstallPromptListener();
      this.setupPushNotifications(registration);

      // Verificar actualizaciones
      this.checkForUpdates(registration);

      return { registration, isSupported: true };
    } catch (error) {
      console.error('[PWA] Error registrando Service Worker:', error);
      return { error: error as Error, isSupported: true };
    }
  }

  /**
   * Configura listener para actualizaciones del SW
   */
  private setupUpdateListener(registration: ServiceWorkerRegistration): void {
    registration.addEventListener('updatefound', () => {
      console.log('[PWA] Actualización encontrada');
      
      const newWorker = registration.installing;
      if (newWorker) {
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            console.log('[PWA] Nueva versión disponible');
            this.updateAvailable = true;
            this.showUpdateNotification();
          }
        });
      }
    });

    // Listener para cuando el SW toma control
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      console.log('[PWA] Service Worker tomó control, recargando página...');
      window.location.reload();
    });
  }

  /**
   * Configura listener para prompt de instalación
   */
  private setupInstallPromptListener(): void {
    window.addEventListener('beforeinstallprompt', (event) => {
      console.log('[PWA] Install prompt disponible');
      
      // Prevenir el prompt automático
      event.preventDefault();
      
      // Guardar el prompt para uso posterior
      this.installPrompt = event as unknown as PWAInstallPrompt;
      
      // Mostrar botón de instalación personalizado
      this.showInstallButton();
    });

    // Listener para cuando la app es instalada
    window.addEventListener('appinstalled', () => {
      console.log('[PWA] App instalada exitosamente');
      this.installPrompt = null;
      this.hideInstallButton();
    });
  }

  /**
   * Configura push notifications
   */
  private async setupPushNotifications(_registration: ServiceWorkerRegistration): Promise<void> {
    if (!('PushManager' in window)) {
      console.warn('[PWA] Push notifications no soportadas');
      return;
    }

    try {
      // Verificar permisos
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        console.log('[PWA] Permisos de notificación denegados');
        return;
      }

      console.log('[PWA] Push notifications habilitadas');
      
      // Aquí se podría suscribir al push service
      // const subscription = await registration.pushManager.subscribe({...});
    } catch (error) {
      console.error('[PWA] Error configurando push notifications:', error);
    }
  }

  /**
   * Verifica actualizaciones manualmente
   */
  private checkForUpdates(registration: ServiceWorkerRegistration): void {
    // Verificar actualizaciones cada 30 minutos
    setInterval(() => {
      console.log('[PWA] Verificando actualizaciones...');
      registration.update();
    }, 30 * 60 * 1000);
  }

  /**
   * Muestra notificación de actualización disponible
   */
  private showUpdateNotification(): void {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.id = 'pwa-update-notification';
    notification.innerHTML = `
      <div style="
        position: fixed;
        top: 20px;
        right: 20px;
        background: #f59e0b;
        color: white;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        max-width: 300px;
        font-family: system-ui, -apple-system, sans-serif;
      ">
        <div style="font-weight: 600; margin-bottom: 8px;">
          🔄 Nueva versión disponible
        </div>
        <div style="font-size: 14px; margin-bottom: 12px;">
          Hay una actualización de la aplicación lista para instalar.
        </div>
        <div style="display: flex; gap: 8px;">
          <button id="pwa-update-btn" style="
            background: white;
            color: #f59e0b;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
          ">
            Actualizar
          </button>
          <button id="pwa-dismiss-btn" style="
            background: transparent;
            color: white;
            border: 1px solid white;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
          ">
            Después
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(notification);

    // Listeners para botones
    document.getElementById('pwa-update-btn')?.addEventListener('click', () => {
      this.applyUpdate();
      notification.remove();
    });

    document.getElementById('pwa-dismiss-btn')?.addEventListener('click', () => {
      notification.remove();
    });
  }

  /**
   * Muestra botón de instalación de PWA
   */
  private showInstallButton(): void {
    // Crear botón de instalación
    const installBtn = document.createElement('button');
    installBtn.id = 'pwa-install-btn';
    installBtn.innerHTML = `
      <span style="margin-right: 8px;">📱</span>
      Instalar App
    `;
    installBtn.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #10b981;
      color: white;
      border: none;
      padding: 12px 16px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 9999;
      display: flex;
      align-items: center;
      font-family: system-ui, -apple-system, sans-serif;
      transition: all 0.2s ease;
    `;

    installBtn.addEventListener('mouseenter', () => {
      installBtn.style.transform = 'translateY(-2px)';
      installBtn.style.boxShadow = '0 6px 16px rgba(0,0,0,0.2)';
    });

    installBtn.addEventListener('mouseleave', () => {
      installBtn.style.transform = 'translateY(0)';
      installBtn.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    });

    installBtn.addEventListener('click', () => {
      this.promptInstall();
    });

    document.body.appendChild(installBtn);
  }

  /**
   * Oculta botón de instalación
   */
  private hideInstallButton(): void {
    const installBtn = document.getElementById('pwa-install-btn');
    if (installBtn) {
      installBtn.remove();
    }
  }

  /**
   * Aplica la actualización del service worker
   */
  async applyUpdate(): Promise<void> {
    if (!this.registration) return;

    // Enviar mensaje al SW para que se active inmediatamente
    const waitingWorker = this.registration.waiting;
    if (waitingWorker) {
      waitingWorker.postMessage({ type: 'SKIP_WAITING' });
    }
  }

  /**
   * Muestra prompt de instalación de PWA
   */
  async promptInstall(): Promise<void> {
    if (!this.installPrompt) {
      console.log('[PWA] Install prompt no disponible');
      return;
    }

    try {
      // Mostrar prompt nativo
      await this.installPrompt.prompt();
      
      // Esperar respuesta del usuario
      const choiceResult = await this.installPrompt.userChoice;
      
      if (choiceResult.outcome === 'accepted') {
        console.log('[PWA] Usuario aceptó instalación');
      } else {
        console.log('[PWA] Usuario rechazó instalación');
      }
      
      // Limpiar prompt
      this.installPrompt = null;
      this.hideInstallButton();
    } catch (error) {
      console.error('[PWA] Error mostrando install prompt:', error);
    }
  }

  /**
   * Verifica si la app está instalada
   */
  isInstalled(): boolean {
    return window.matchMedia('(display-mode: standalone)').matches ||
           (window.navigator as any).standalone === true;
  }

  /**
   * Obtiene información del service worker
   */
  getInfo(): object {
    return {
      isRegistered: !!this.registration,
      isInstalled: this.isInstalled(),
      updateAvailable: this.updateAvailable,
      scope: this.registration?.scope,
      state: this.registration?.active?.state,
    };
  }
}

// Export singleton instance
export const swManager = new ServiceWorkerManager();

/**
 * Hook React para PWA Service Worker
 */
export const usePWA = () => {
  return {
    register: () => swManager.register(),
    isInstalled: () => swManager.isInstalled(),
    promptInstall: () => swManager.promptInstall(),
    getInfo: () => swManager.getInfo(),
  };
};

export default swManager;