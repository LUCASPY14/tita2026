"""
Django views para Push Notifications
Integra con el backend existente de Python
"""

import json
import logging
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)

# Configuración VAPID
VAPID_PUBLIC_KEY = getattr(settings, 'VAPID_PUBLIC_KEY', None)
VAPID_PRIVATE_KEY = getattr(settings, 'VAPID_PRIVATE_KEY', None) 
VAPID_EMAIL = getattr(settings, 'VAPID_EMAIL', 'admin@cantina-tita.com')

class PushNotificationManager:
    """
    Manager para Push Notifications que usa el servicio Node.js
    """
    
    def __init__(self):
        self.service_script = os.path.join(
            settings.BASE_DIR, 'push-notification-service.js'
        )
        self.subscriptions = {}  # Cache local, en producción usar BD
        
    def get_vapid_public_key(self):
        """Obtener la VAPID public key del servicio"""
        try:
            result = self.call_node_service('getPublicKey')
            return result.get('publicKey')
        except Exception as e:
            logger.error(f"Error getting VAPID key: {e}")
            return None
            
    def subscribe_user(self, user_id, subscription_data):
        """Suscribir usuario a notificaciones"""
        try:
            result = self.call_node_service('subscribe', {
                'userId': str(user_id),
                'subscription': subscription_data
            })
            
            if result.get('success'):
                self.subscriptions[str(user_id)] = {
                    'subscription': subscription_data,
                    'subscribed_at': datetime.now().isoformat(),
                    'active': True
                }
                logger.info(f"User {user_id} subscribed to push notifications")
                
            return result
            
        except Exception as e:
            logger.error(f"Subscription error for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
            
    def unsubscribe_user(self, user_id):
        """Desuscribir usuario"""
        try:
            result = self.call_node_service('unsubscribe', {
                'userId': str(user_id)
            })
            
            if result.get('success') and str(user_id) in self.subscriptions:
                del self.subscriptions[str(user_id)]
                logger.info(f"User {user_id} unsubscribed from push notifications")
                
            return result
            
        except Exception as e:
            logger.error(f"Unsubscribe error for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_notification_to_user(self, user_id, notification):
        """Enviar notificación a usuario específico"""
        try:
            result = self.call_node_service('sendToUser', {
                'userId': str(user_id),
                'notification': notification
            })
            
            logger.info(f"Notification sent to user {user_id}: {notification.get('title', 'No title')}")
            return result
            
        except Exception as e:
            logger.error(f"Send notification error for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_notification_to_all(self, notification):
        """Enviar notificación a todos los usuarios suscritos"""
        try:
            result = self.call_node_service('sendToAll', {
                'notification': notification
            })
            
            logger.info(f"Broadcast notification sent: {notification.get('title', 'No title')}")
            return result
            
        except Exception as e:
            logger.error(f"Broadcast notification error: {e}")
            return {'success': False, 'error': str(e)}
            
    def get_subscription_stats(self):
        """Obtener estadísticas de suscripciones"""
        try:
            return self.call_node_service('getStats')
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {'error': str(e)}
    
    def call_node_service(self, method, params=None):
        """
        Llamar al servicio Node.js de push notifications
        """
        command_data = {
            'method': method,
            'params': params or {}
        }
        
        # Crear archivo temporal con comando
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(command_data, f)
            temp_file = f.name
        
        try:
            # Ejecutar servicio Node.js
            result = subprocess.run([
                'node', '-e', f'''
                    const PushService = require('{self.service_script}');
                    const fs = require('fs');
                    const data = JSON.parse(fs.readFileSync('{temp_file}', 'utf8'));
                    
                    const service = new PushService();
                    const method = data.method;
                    const params = data.params;
                    
                    (async () => {{
                        try {{
                            let result;
                            if (method === 'getPublicKey') {{
                                result = {{ publicKey: service.getPublicKey() }};
                            }} else if (method === 'subscribe') {{
                                result = service.subscribe(params.userId, params.subscription);
                            }} else if (method === 'unsubscribe') {{
                                result = service.unsubscribe(params.userId);
                            }} else if (method === 'sendToUser') {{
                                result = await service.sendToUser(params.userId, params.notification);
                            }} else if (method === 'sendToAll') {{
                                result = await service.sendToAll(params.notification);
                            }} else if (method === 'getStats') {{
                                result = service.getStats();
                            }} else {{
                                result = {{ error: 'Unknown method' }};
                            }}
                            
                            console.log(JSON.stringify(result));
                        }} catch (error) {{
                            console.log(JSON.stringify({{ error: error.message }}));
                        }}
                    }})();
                '''
            ], capture_output=True, text=True, cwd=settings.BASE_DIR)
            
            if result.returncode == 0:
                return json.loads(result.stdout.strip())
            else:
                raise Exception(f"Node.js error: {result.stderr}")
                
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_file):
                os.unlink(temp_file)

# Instancia global del manager
push_manager = PushNotificationManager()

@csrf_exempt
@require_http_methods(["GET"])
def get_vapid_public_key(request):
    """
    Endpoint para obtener la VAPID public key
    """
    try:
        public_key = push_manager.get_vapid_public_key()
        
        if not public_key:
            return JsonResponse({
                'error': 'VAPID keys not configured'
            }, status=500)
            
        return JsonResponse({
            'publicKey': public_key
        })
        
    except Exception as e:
        logger.error(f"Error getting VAPID public key: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def subscribe_push_notifications(request):
    """
    Endpoint para suscribir usuario a notificaciones push
    """
    try:
        data = json.loads(request.body)
        subscription = data.get('subscription')
        
        if not subscription:
            return JsonResponse({
                'error': 'Subscription data required'
            }, status=400)
        
        result = push_manager.subscribe_user(
            request.user.id, 
            subscription
        )
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Subscription error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required  
@require_http_methods(["POST"])
def unsubscribe_push_notifications(request):
    """
    Endpoint para desuscribir usuario de notificaciones
    """
    try:
        result = push_manager.unsubscribe_user(request.user.id)
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Unsubscribe error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"]) 
def send_test_notification(request):
    """
    Enviar notificación de prueba al usuario actual
    """
    try:
        notification = {
            'title': '🧪 Notificación de Prueba',
            'body': 'Esta es una prueba de push notification',
            'icon': '/icons/icon-192x192.png',
            'badge': '/icons/badge-72x72.png',
            'tag': 'test-notification',
            'data': {
                'type': 'test',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        result = push_manager.send_notification_to_user(
            request.user.id,
            notification
        )
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Test notification error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_notification_stats(request):
    """
    Obtener estadísticas de notificaciones (solo admin)
    """
    try:
        if not request.user.is_staff:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
            
        stats = push_manager.get_subscription_stats()
        return JsonResponse(stats)
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# Funciones de utilidad para enviar notificaciones desde otras partes del sistema

def send_order_notification(order_id, user_id=None):
    """
    Enviar notificación de nueva orden
    """
    notification = {
        'title': '📋 Nueva Orden',
        'body': f'Orden #{order_id} recibida',
        'icon': '/icons/icon-192x192.png',
        'badge': '/icons/badge-72x72.png',
        'tag': 'new-order',
        'data': {
            'orderId': order_id,
            'type': 'order'
        },
        'actions': [
            {'action': 'view', 'title': 'Ver Orden'},
            {'action': 'dismiss', 'title': 'Descartar'}
        ]
    }
    
    if user_id:
        return push_manager.send_notification_to_user(user_id, notification)
    else:
        return push_manager.send_notification_to_all(notification)

def send_payment_notification(payment_amount, user_id=None):
    """
    Enviar notificación de pago recibido
    """
    notification = {
        'title': '💰 Pago Recibido',
        'body': f'Pago recibido por ${payment_amount:,.2f}',
        'icon': '/icons/icon-192x192.png',
        'badge': '/icons/badge-72x72.png',
        'tag': 'payment',
        'data': {
            'amount': payment_amount,
            'type': 'payment'
        }
    }
    
    if user_id:
        return push_manager.send_notification_to_user(user_id, notification)
    else:
        return push_manager.send_notification_to_all(notification)

def send_low_stock_notification(product_name, quantity, user_id=None):
    """
    Enviar notificación de stock bajo
    """
    notification = {
        'title': '⚠️ Stock Bajo',
        'body': f'{product_name} - Quedan {quantity} unidades',
        'icon': '/icons/icon-192x192.png',
        'badge': '/icons/badge-72x72.png',
        'tag': 'low-stock',
        'data': {
            'product': product_name,
            'quantity': quantity,
            'type': 'inventory'
        }
    }
    
    if user_id:
        return push_manager.send_notification_to_user(user_id, notification)  
    else:
        return push_manager.send_notification_to_all(notification)