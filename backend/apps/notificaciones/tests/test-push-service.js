#!/usr/bin/env node

/**
 * Script para probar el servicio de Push Notifications
 * Simula el comportamiento del backend Django
 */

const PushNotificationService = require('./push-notification-service');

async function testPushNotificationService() {
  console.log('🧪 Testing Push Notification Service...\n');
  
  const service = new PushNotificationService();
  
  // Test 1: Verificar inicialización
  console.log('1️⃣ Verificando inicialización...');
  const publicKey = service.getPublicKey();
  console.log('✅ Public Key:', publicKey.substring(0, 20) + '...');
  
  // Test 2: Crear suscripción de prueba
  console.log('\n2️⃣ Creando suscripción de prueba...');
  const mockSubscription = {
    endpoint: 'https://fcm.googleapis.com/fcm/send/test-endpoint',
    keys: {
      p256dh: 'test-p256dh-key',
      auth: 'test-auth-key'
    }
  };
  
  const subscribeResult = service.subscribe('test-user', mockSubscription);
  console.log('✅ Subscription result:', subscribeResult.success ? 'Success' : 'Failed');
  
  // Test 3: Verificar estadísticas
  console.log('\n3️⃣ Verificando estadísticas...');
  const stats = service.getStats();
  console.log('📊 Stats:', stats);
  
  // Test 4: Generar diferentes tipos de notificaciones
  console.log('\n4️⃣ Generando notificaciones del sistema...');
  
  const notifications = [
    service.generateSystemNotification('new_order', { orderId: '001' }),
    service.generateSystemNotification('low_stock', { product: 'Café', productId: '123' }),
    service.generateSystemNotification('payment_received', { amount: 15000 }),
    service.generateSystemNotification('daily_summary', { orders: 25, total: 350000, date: '2024-01-15' }),
    service.generateSystemNotification('system_update', { version: '1.5.0' })
  ];
  
  notifications.forEach((notif, index) => {
    console.log(`📄 Notification ${index + 1}:`, notif.title, '-', notif.body);
  });
  
  // Test 5: Listar suscripciones
  console.log('\n5️⃣ Listando suscripciones...');
  const subscriptions = service.listSubscriptions();
  console.log('📋 Subscriptions:', subscriptions);

  console.log('\n✅ All tests completed successfully!');
  console.log('\n💡 Next steps:');
  console.log('   1. Start Django backend: python manage.py runserver');
  console.log('   2. Start React frontend: npm start');
  console.log('   3. Test notifications from frontend UI');
  
  return true;
}

// Función para simular endpoints de Django
function simulateBackendEndpoints() {
  const express = require('express');
  const app = express();
  app.use(express.json());
  
  const service = new PushNotificationService();
  
  // GET /api/push/vapid-public-key
  app.get('/api/push/vapid-public-key', (req, res) => {
    res.json({ publicKey: service.getPublicKey() });
  });
  
  // POST /api/push/subscribe
  app.post('/api/push/subscribe', (req, res) => {
    const { subscription } = req.body;
    const userId = req.headers['x-user-id'] || 'anonymous';
    
    const result = service.subscribe(userId, subscription);
    res.json(result);
  });
  
  // POST /api/push/unsubscribe  
  app.post('/api/push/unsubscribe', (req, res) => {
    const userId = req.headers['x-user-id'] || 'anonymous';
    
    const result = service.unsubscribe(userId);
    res.json(result);
  });
  
  // POST /api/push/test
  app.post('/api/push/test', async (req, res) => {
    const userId = req.headers['x-user-id'] || 'anonymous';
    
    try {
      const result = await service.sendTestNotification(userId);
      res.json({ success: result });
    } catch (error) {
      res.status(500).json({ success: false, error: error.message });
    }
  });
  
  // POST /api/push/send-to-all
  app.post('/api/push/send-to-all', async (req, res) => {
    const { notification } = req.body;
    
    try {
      const result = await service.sendToAll(notification);
      res.json({ success: true, result });
    } catch (error) {
      res.status(500).json({ success: false, error: error.message });
    }
  });
  
  // GET /api/push/stats
  app.get('/api/push/stats', (req, res) => {
    const stats = service.getStats();
    res.json(stats);
  });
  
  const port = process.env.PORT || 3001;
  app.listen(port, () => {
    console.log(`\n🚀 Push notification test server running on port ${port}`);
    console.log(`📡 Endpoints available:`);
    console.log(`   GET  http://localhost:${port}/api/push/vapid-public-key`);
    console.log(`   POST http://localhost:${port}/api/push/subscribe`);
    console.log(`   POST http://localhost:${port}/api/push/unsubscribe`);
    console.log(`   POST http://localhost:${port}/api/push/test`);
    console.log(`   POST http://localhost:${port}/api/push/send-to-all`);
    console.log(`   GET  http://localhost:${port}/api/push/stats\n`);
  });
  
  return app;
}

// Función principal
async function main() {
  const args = process.argv.slice(2);
  
  if (args.includes('--server')) {
    console.log('🌐 Starting test server...');
    simulateBackendEndpoints();
  } else {
    await testPushNotificationService();
    console.log('\n🌐 To start test server, run: node test-push-service.js --server');
  }
}

// Ejecutar si es llamado directamente
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { 
  testPushNotificationService, 
  simulateBackendEndpoints 
};