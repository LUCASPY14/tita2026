/**
 * Backend service para Push Notifications
 * Maneja subscripciones VAPID y envío de notificaciones
 */

const webpush = require('web-push');
const crypto = require('crypto');

class PushNotificationService {
  constructor() {
    this.subscriptions = new Map(); // En producción usar BD
    this.vapidKeys = null;
    this.initialize();
  }

  initialize() {
    // Configurar VAPID keys
    this.setupVapidKeys();
    
    console.log('🔔 Push Notification Service initialized');
    console.log('📧 Contact email:', process.env.VAPID_EMAIL || 'admin@cantina-tita.com');
  }

  setupVapidKeys() {
    // En desarrollo, generar keys o usar las del .env
    const publicKey = process.env.VAPID_PUBLIC_KEY;
    const privateKey = process.env.VAPID_PRIVATE_KEY;
    const email = process.env.VAPID_EMAIL || 'admin@cantina-tita.com';

    if (publicKey && privateKey) {
      this.vapidKeys = { publicKey, privateKey };
      console.log('✅ Using VAPID keys from environment');
    } else {
      // Generar nuevas keys para desarrollo
      this.vapidKeys = webpush.generateVAPIDKeys();
      console.log('🔑 Generated new VAPID keys for development');
      console.log('📋 Public Key:', this.vapidKeys.publicKey);
      console.log('🔒 Private Key:', this.vapidKeys.privateKey);
      console.log('\n💡 Save these keys to .env file:');
      console.log(`VAPID_PUBLIC_KEY=${this.vapidKeys.publicKey}`);
      console.log(`VAPID_PRIVATE_KEY=${this.vapidKeys.privateKey}`);
      console.log(`VAPID_EMAIL=${email}\n`);
    }

    // Configurar web-push
    webpush.setVapidDetails(
      `mailto:${email}`,
      this.vapidKeys.publicKey,
      this.vapidKeys.privateKey
    );
  }

  getPublicKey() {
    return this.vapidKeys.publicKey;
  }

  // Suscribir usuario a notificaciones
  subscribe(userId, subscription) {
    try {
      // Validar subscription
      if (!subscription || !subscription.endpoint) {
        throw new Error('Invalid subscription object');
      }

      // Agregar timestamp y user info
      const enhancedSubscription = {
        ...subscription,
        userId,
        subscribedAt: new Date().toISOString(),
        active: true
      };

      this.subscriptions.set(userId, enhancedSubscription);
      console.log(`✅ User ${userId} subscribed to push notifications`);
      
      return {
        success: true,
        message: 'Successfully subscribed to notifications',
        publicKey: this.vapidKeys.publicKey
      };
      
    } catch (error) {
      console.error('❌ Subscription error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Desuscribir usuario
  unsubscribe(userId) {
    if (this.subscriptions.has(userId)) {
      this.subscriptions.delete(userId);
      console.log(`🔕 User ${userId} unsubscribed from notifications`);
      return { success: true, message: 'Successfully unsubscribed' };
    }
    
    return { success: false, message: 'User not found' };
  }

  // Enviar notificación a un usuario específico
  async sendToUser(userId, notification) {
    const subscription = this.subscriptions.get(userId);
    
    if (!subscription) {
      throw new Error(`User ${userId} is not subscribed`);
    }

    try {
      const payload = JSON.stringify(notification);
      const result = await webpush.sendNotification(subscription, payload);
      
      console.log(`📤 Notification sent to ${userId}:`, notification.title);
      return { success: true, result };
      
    } catch (error) {
      console.error(`❌ Failed to send to ${userId}:`, error);
      
      // Si el endpoint expiró, desuscribir automáticamente
      if (error.statusCode === 410) {
        console.log(`🔄 Removing expired subscription for ${userId}`);
        this.unsubscribe(userId);
      }
      
      throw error;
    }
  }

  // Enviar notificación a todos los usuarios suscritos
  async sendToAll(notification) {
    const results = [];
    const failed = [];

    for (const [userId, subscription] of this.subscriptions) {
      try {
        await this.sendToUser(userId, notification);
        results.push(userId);
      } catch (error) {
        failed.push({ userId, error: error.message });
      }
    }

    console.log(`📊 Broadcast complete: ${results.length} sent, ${failed.length} failed`);
    return { sent: results, failed };
  }

  // Enviar notificaciones basadas en roles
  async sendToRole(role, notification) {
    // Por ahora enviamos a todos, en futuro filtrar por rol
    return this.sendToAll(notification);
  }

  // Generar notificaciones específicas del sistema
  generateSystemNotification(type, data = {}) {
    const notifications = {
      new_order: {
        title: '📋 Nueva Orden',
        body: `Orden #${data.orderId} recibida`,
        icon: '/icons/icon-192x192.png',
        badge: '/icons/badge-72x72.png',
        tag: 'new-order',
        data: { orderId: data.orderId, type: 'order' },
        actions: [
          { action: 'view', title: 'Ver Orden' },
          { action: 'dismiss', title: 'Descartar' }
        ]
      },
      
      low_stock: {
        title: '⚠️ Stock Bajo',
        body: `${data.product} está por agotarse`,
        icon: '/icons/icon-192x192.png',
        badge: '/icons/badge-72x72.png',
        tag: 'low-stock',
        data: { productId: data.productId, type: 'inventory' }
      },
      
      payment_received: {
        title: '💰 Pago Recibido',
        body: `Pagó recibido por $${data.amount}`,
        icon: '/icons/icon-192x192.png',
        badge: '/icons/badge-72x72.png',
        tag: 'payment',
        data: { paymentId: data.paymentId, type: 'payment' }
      },

      daily_summary: {
        title: '📊 Resumen Diario',
        body: `${data.orders} órdenes, $${data.total} en ventas`,
        icon: '/icons/icon-192x192.png',
        badge: '/icons/badge-72x72.png',
        tag: 'daily-summary',
        data: { date: data.date, type: 'summary' }
      },

      system_update: {
        title: '🔄 Sistema Actualizado',
        body: 'La aplicación se ha actualizado',
        icon: '/icons/icon-192x192.png',
        badge: '/icons/badge-72x72.png',
        tag: 'system-update',
        data: { version: data.version, type: 'system' }
      }
    };

    return notifications[type] || {
      title: 'Notificación',
      body: data.message || 'Nueva notificación del sistema',
      icon: '/icons/icon-192x192.png'
    };
  }

  // Obtener estadísticas de suscripciones
  getStats() {
    const total = this.subscriptions.size;
    const active = Array.from(this.subscriptions.values()).filter(s => s.active).length;
    
    return {
      totalSubscriptions: total,
      activeSubscriptions: active,
      vapidPublicKey: this.vapidKeys.publicKey.substring(0, 20) + '...',
      lastSubscription: total > 0 ? Array.from(this.subscriptions.values()).pop().subscribedAt : null
    };
  }

  // Listar todas las suscripciones
  listSubscriptions() {
    return Array.from(this.subscriptions.entries()).map(([userId, sub]) => ({
      userId,
      subscribedAt: sub.subscribedAt,
      active: sub.active,
      endpoint: sub.endpoint.substring(0, 50) + '...'
    }));
  }

  // Testing helpers
  async sendTestNotification(userId = 'test-user') {
    // Crear suscripción de prueba si no existe
    if (!this.subscriptions.has(userId)) {
      console.log('📝 No subscription found, use frontend to subscribe first');
      return false;
    }

    const testNotification = this.generateSystemNotification('system_update', {
      version: '1.0.0',
      message: 'Esta es una notificación de prueba'
    });

    try {
      await this.sendToUser(userId, testNotification);
      return true;
    } catch (error) {
      console.error('❌ Test notification failed:', error);
      return false;
    }
  }
}

module.exports = PushNotificationService;