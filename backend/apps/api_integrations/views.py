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
@api_view(["POST"])
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
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return Response({"error": "JSON inválido en el body"}, status=status.HTTP_400_BAD_REQUEST)

        # Extraer datos
        operation = data.get("operation", {})
        shop_process_id = data.get("shop_process_id")
        signature = data.get("signature")

        # Validar datos requeridos
        if not all([operation, shop_process_id, signature]):
            return Response(
                {"error": "Faltan datos requeridos: operation, shop_process_id, signature"},
                status=status.HTTP_400_BAD_REQUEST,
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
            shop_process_id=shop_process_id, operation=operation, signature=signature
        )

        # Loguear webhook en LogsWebhooks
        from apps.api_integrations.models import LogsWebhooks
        from django.utils import timezone

        try:
            LogsWebhooks.objects.create(
                timestamp=timezone.now(),
                evento_tipo="payment_confirmation",
                payload=json.dumps(data),
                headers=dict(request.headers),
                verificacion_ok=1,
                procesado_ok=1 if resultado.get("success", False) else 0,
                ip_origen=request.META.get("REMOTE_ADDR", ""),
            )
        except Exception as log_error:  # pragma: no cover
            # No fallar si falla el logging
            print(f"Error logging webhook: {log_error}")

        # Retornar respuesta
        if resultado.get("success"):
            return Response(
                {
                    "success": True,
                    "message": "Webhook procesado correctamente",
                    "recarga_id": resultado.get("recarga_id"),
                    "estado": resultado.get("estado"),
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"success": False, "error": resultado.get("error")},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        # Error inesperado
        return Response(
            {"success": False, "error": f"Error interno al procesar webhook: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@csrf_exempt
@api_view(["GET"])
@permission_classes([AllowAny])
def webhook_test(request):
    """
    Endpoint de prueba para verificar que el webhook está accesible.
    """
    return Response(
        {
            "status": "ok",
            "message": "Webhook endpoint está activo",
            "método": "POST",
            "paths": {"sipap": "/api/v1/webhooks/sipap/"},
        },
        status=status.HTTP_200_OK,
    )


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def sipap_webhook(request):
    """
    Webhook para recibir confirmaciones de pago de SIPAP QR.

    Red SIPAP envía una notificación POST cuando un pago QR es completado.

    Body esperado:
    {
        "txn_id": "COB-123-1713308400",
        "estado": "aprobado",  // aprobado, rechazado, expirado
        "monto": "14402000.00",
        "moneda": "PYG",
        "banco_origen": "Banco Continental",
        "referencia_bancaria": "TXN-987654321",
        "fecha_pago": "2026-04-16T14:30:00Z",
        "metadata": {
            "id_cobro": 123,
            "id_cliente": 456
        }
    }

    Headers esperados:
    X-SIPAP-Signature: Firma RSA-2048 del banco en base64

    Validaciones:
    1. Verificar firma RSA con clave pública del banco
    2. Validar IP whitelist
    3. Prevenir duplicados (idempotencia)
    4. Aplicar pago a facturas (FIFO)
    5. Actualizar saldos

    Returns:
        200: Webhook procesado correctamente
        400: Error en validación
        403: IP no autorizada o firma inválida
        500: Error interno
    """
    try:
        # Parsear JSON del body
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return Response({"error": "JSON inválido en el body"}, status=status.HTTP_400_BAD_REQUEST)

        # Extraer firma del header
        firma = request.headers.get("X-SIPAP-Signature", "")

        if not firma:
            return Response({"error": "Header X-SIPAP-Signature requerido"}, status=status.HTTP_400_BAD_REQUEST)

        # Obtener IP de origen
        ip_origen = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if ip_origen:
            # Si viene de proxy, tomar primera IP
            ip_origen = ip_origen.split(",")[0].strip()
        else:
            ip_origen = request.META.get("REMOTE_ADDR", "")

        # Procesar webhook con SIPAPService
        from apps.api_integrations.services.sipap_service import SIPAPService

        sipap_service = SIPAPService()
        resultado = sipap_service.procesar_webhook(payload=data, firma=firma, ip_origen=ip_origen)

        # Loguear webhook en LogsWebhooks
        from apps.api_integrations.models import LogsWebhooks
        from django.utils import timezone

        try:
            LogsWebhooks.objects.create(
                timestamp=timezone.now(),
                evento_tipo="sipap_payment_confirmation",
                payload=json.dumps(data),
                headers=dict(request.headers),
                verificacion_ok=1 if resultado.get("success", False) else 0,
                procesado_ok=1 if resultado.get("success", False) else 0,
                ip_origen=ip_origen,
            )
        except Exception as log_error:  # pragma: no cover
            # No fallar si falla el logging
            print(f"Error logging webhook SIPAP: {log_error}")

        # Retornar respuesta
        if resultado.get("success"):
            return Response(
                {
                    "success": True,
                    "message": resultado.get("mensaje", "Webhook procesado correctamente"),
                    "txn_id": resultado.get("txn_id"),
                    "id_pago_cliente": resultado.get("id_pago_cliente"),
                    "monto": resultado.get("monto"),
                    "facturas_aplicadas": resultado.get("facturas_aplicadas", 0),
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"success": False, "error": resultado.get("mensaje", "Error desconocido")},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except Exception as e:
        # Error inesperado
        return Response(
            {"success": False, "error": f"Error interno al procesar webhook SIPAP: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
