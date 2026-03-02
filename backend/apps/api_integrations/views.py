"""
Views de la app api_integrations
Manejo de webhooks de APIs externas
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def bancard_webhook(request):
    """
    Webhook para recibir confirmaciones de pago de Bancard.
    
    Bancard envía una notificación POST cuando una transacción es completada.
    
    Body esperado:
    {
        "operation": {
            "response": "S" o "N",  // S=Aprobada, N=Rechazada
            "response_details": "Descripción",
            "amount": "100.00",
            "currency": "PYG",
            "authorization_number": "123456",
            "ticket_number": "789012",
            "response_code": "00",
            "response_description": "Transacción aprobada",
            "security_information": {...}
        },
        "shop_process_id": "REC-123-1234567890",
        "signature": "abc123xyz..."  // Firma HMAC-SHA256
    }
    
    Validaciones:
    1. Verificar firma HMAC-SHA256
    2. Validar IP whitelist (opcional)
    3. Prevenir duplicados (idempotencia)
    4. Actualizar estado de recarga
    5. Acreditar saldo si aprobado
    
    Returns:
        200: Webhook procesado correctamente
        400: Error en validación
        500: Error interno
    """
    try:
        # Parsear JSON del body
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return Response(
                {'error': 'JSON inválido en el body'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extraer datos
        operation = data.get('operation', {})
        shop_process_id = data.get('shop_process_id')
        signature = data.get('signature')
        
        # Validar datos requeridos
        if not all([operation, shop_process_id, signature]):
            return Response(
                {'error': 'Faltan datos requeridos: operation, shop_process_id, signature'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar IP whitelist (opcional, configurar en settings)
        # ip_cliente = request.META.get('REMOTE_ADDR')
        # if ip_cliente not in settings.BANCARD_IP_WHITELIST:
        #     return Response(
        #         {'error': 'IP no autorizada'},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        
        # Procesar webhook con BancardService
        from apps.api_integrations.services import BancardService
        
        bancard_service = BancardService()
        resultado = bancard_service.procesar_webhook(
            shop_process_id=shop_process_id,
            operation=operation,
            signature=signature
        )
        
        # Loguear webhook en LogsWebhooks
        from apps.api_integrations.models import LogsWebhooks
        from django.utils import timezone
        
        try:
            LogsWebhooks.objects.create(
                timestamp=timezone.now(),
                proveedor='Bancard',
                evento='payment_confirmation',
                payload=json.dumps(data),
                headers=json.dumps(dict(request.headers)),
                procesado=resultado.get('success', False),
                resultado=json.dumps(resultado),
                ip_origen=request.META.get('REMOTE_ADDR'),
                id_transaccion=shop_process_id
            )
        except Exception as log_error:
            # No fallar si falla el logging
            print(f"Error logging webhook: {log_error}")
        
        # Retornar respuesta
        if resultado.get('success'):
            return Response(
                {
                    'success': True,
                    'message': 'Webhook procesado correctamente',
                    'recarga_id': resultado.get('recarga_id'),
                    'estado': resultado.get('estado')
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'success': False,
                    'error': resultado.get('error')
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        # Error inesperado
        return Response(
            {
                'success': False,
                'error': f'Error interno al procesar webhook: {str(e)}'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def webhook_test(request):
    """
    Endpoint de prueba para verificar que el webhook está accesible.
    """
    return Response(
        {
            'status': 'ok',
            'message': 'Webhook endpoint de Bancard está activo',
            'método': 'POST',
            'path': '/api/webhooks/bancard/'
        },
        status=status.HTTP_200_OK
    )

