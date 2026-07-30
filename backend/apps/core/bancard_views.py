"""
Vistas para la integración Bancard vPOS.

Endpoints:
  POST /api/v1/bancard/iniciar/                → Recarga de tarjeta prepago
  POST /api/v1/bancard/iniciar-almuerzo/       → Pago de cuenta mensual de almuerzo
  POST /api/v1/bancard/confirmar/              → Webhook: Bancard notifica resultado de pago (sin auth)
  GET  /api/v1/bancard/retorno/                → Bancard redirige el browser aquí tras el pago
  GET  /api/v1/bancard/estado/<spid>/          → Consulta estado de un pago
"""

import time
import logging

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.throttling import SensitiveEndpointThrottle

from .models import PagoBancard, Tarjeta
from . import bancard_service
from common.throttling import BancardRetornoThrottle

logger = logging.getLogger(__name__)

def PORTAL_URL():
    return getattr(settings, "PORTAL_FRONTEND_URL", "http://localhost:5173")


# ─── POST /api/v1/bancard/iniciar/ ────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([SensitiveEndpointThrottle])
def bancard_iniciar(request):
    """
    Body: { "nro_tarjeta": "...", "monto": 150000 }

    Crea un PagoBancard, llama a Bancard y devuelve la URL donde el padre
    debe ingresar los datos de su tarjeta de débito/crédito.

    Respuesta: { "shop_process_id": "...", "redirect_url": "https://vpos.infonet.com.py/..." }
    """
    nro_tarjeta = request.data.get("nro_tarjeta")
    monto_raw   = request.data.get("monto")

    # ── Validaciones básicas ─────────────────────────────────────────────────
    if not nro_tarjeta or not monto_raw:
        return Response(
            {"detail": "Se requieren nro_tarjeta y monto."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        monto = int(monto_raw)
    except (TypeError, ValueError):
        return Response({"detail": "Monto inválido."}, status=status.HTTP_400_BAD_REQUEST)

    if monto < 10_000:
        return Response(
            {"detail": "El monto mínimo de carga es ₲10.000."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if monto > 5_000_000:
        return Response(
            {"detail": "El monto máximo de carga es ₲5.000.000."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── Obtener tarjeta ──────────────────────────────────────────────────────
    try:
        tarjeta = Tarjeta.objects.get(nro_tarjeta=nro_tarjeta)
    except Tarjeta.DoesNotExist:
        return Response({"detail": "Tarjeta no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    if tarjeta.estado != Tarjeta.Estado.ACTIVA:
        return Response(
            {"detail": f"La tarjeta está {tarjeta.estado.lower()}. No se puede recargar."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── Verificar que las claves Bancard están configuradas ──────────────────
    if not bancard_service._public_key() or not bancard_service._private_key():
        return Response(
            {"detail": "La integración de pagos no está configurada. Contactá con la administración."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # ── Obtener cliente del usuario autenticado ──────────────────────────────
    cliente = getattr(request.user, "cliente", None)

    # ── Crear PagoBancard ────────────────────────────────────────────────────
    shop_process_id = str(int(time.time() * 1000))

    pago = PagoBancard.objects.create(
        tarjeta=tarjeta,
        cliente=cliente,
        shop_process_id=shop_process_id,
        monto=monto,
        descripcion=f"Recarga tarjeta {nro_tarjeta}",
        ip_origen=request.META.get("REMOTE_ADDR"),
    )

    # ── Llamar a Bancard ─────────────────────────────────────────────────────
    base_return_url = settings.BANCARD_RETURN_URL
    return_url = f"{base_return_url}?shop_process_id={shop_process_id}"
    cancel_url = getattr(settings, "BANCARD_CANCEL_URL", f"{PORTAL_URL()}/portal/carga-saldo?estado=cancelado")

    resultado = bancard_service.iniciar_pago(
        shop_process_id=shop_process_id,
        monto=monto,
        descripcion=pago.descripcion,
        return_url=return_url,
        cancel_url=cancel_url,
    )

    pago.bancard_response = resultado
    pago.save(update_fields=["bancard_response"])

    if resultado.get("status") != "success":
        pago.estado = PagoBancard.Estado.ERROR
        pago.save(update_fields=["estado"])
        msgs = resultado.get("messages", [])
        desc = msgs[0].get("dsc", "Error al iniciar el pago.") if msgs else "Error al iniciar el pago."
        return Response({"detail": desc}, status=status.HTTP_502_BAD_GATEWAY)

    process_id = resultado.get("process_id", "")
    pago.process_id = process_id
    pago.save(update_fields=["process_id"])

    redirect_url = bancard_service.pago_url(process_id)

    return Response({
        "shop_process_id": shop_process_id,
        "process_id": process_id,
        "redirect_url": redirect_url,
        "script_url": bancard_service.checkout_script_url(),
    }, status=status.HTTP_201_CREATED)


# ─── POST /api/v1/bancard/iniciar-almuerzo/ ───────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([SensitiveEndpointThrottle])
def bancard_iniciar_almuerzo(request):
    """
    Inicia el pago de una CuentaAlmuerzoMensual vía Bancard.
    Solo disponible para CLIENTE_WEB (padres).

    Body: { "cuenta_id": 42, "monto": 150000 }

    Respuesta: { "shop_process_id": "...", "redirect_url": "https://vpos.infonet.com.py/..." }
    """
    if request.user.rol != "CLIENTE_WEB":
        return Response(
            {"detail": "Solo los padres pueden pagar almuerzos desde el portal."},
            status=status.HTTP_403_FORBIDDEN,
        )

    cuenta_id = request.data.get("cuenta_id")
    monto_raw = request.data.get("monto")

    if not cuenta_id or not monto_raw:
        return Response({"detail": "Se requieren cuenta_id y monto."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        monto = int(monto_raw)
    except (TypeError, ValueError):
        return Response({"detail": "Monto inválido."}, status=status.HTTP_400_BAD_REQUEST)

    if monto <= 0:
        return Response({"detail": "El monto debe ser mayor a cero."}, status=status.HTTP_400_BAD_REQUEST)

    # Verificar que la cuenta pertenece al hijo del cliente autenticado
    from apps.almuerzos.models import CuentaAlmuerzoMensual

    cliente = getattr(request.user, "cliente", None)
    if cliente is None:
        return Response(
            {"detail": "Tu usuario no tiene un perfil de cliente asociado."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        cuenta = CuentaAlmuerzoMensual.objects.get(pk=cuenta_id, hijo__cliente_responsable=cliente)
    except CuentaAlmuerzoMensual.DoesNotExist:
        return Response({"detail": "Cuenta de almuerzo no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    saldo_pendiente = cuenta.saldo_pendiente
    if saldo_pendiente <= 0:
        return Response({"detail": "Esta cuenta ya está al día."}, status=status.HTTP_400_BAD_REQUEST)

    if monto > int(saldo_pendiente):
        return Response(
            {"detail": f"El monto no puede superar el saldo pendiente de ₲{saldo_pendiente:,.0f}."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not bancard_service._public_key() or not bancard_service._private_key():
        return Response(
            {"detail": "La integración de pagos no está configurada. Contactá con la administración."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    shop_process_id = str(int(time.time() * 1000))

    pago = PagoBancard.objects.create(
        tipo=PagoBancard.Tipo.ALMUERZO,
        cuenta_almuerzo=cuenta,
        cliente=cliente,
        shop_process_id=shop_process_id,
        monto=monto,
        descripcion=f"Almuerzo {cuenta.hijo} {cuenta.mes}/{cuenta.anio}"[:20],
        ip_origen=request.META.get("REMOTE_ADDR"),
    )

    base_return_url = settings.BANCARD_RETURN_URL
    return_url = f"{base_return_url}?shop_process_id={shop_process_id}"
    cancel_url = getattr(settings, "BANCARD_CANCEL_URL_ALMUERZO",
                         f"{PORTAL_URL()}/portal/pagar-almuerzo?estado=cancelado")

    resultado = bancard_service.iniciar_pago(
        shop_process_id=shop_process_id,
        monto=monto,
        descripcion=pago.descripcion,
        return_url=return_url,
        cancel_url=cancel_url,
    )

    pago.bancard_response = resultado
    pago.save(update_fields=["bancard_response"])

    if resultado.get("status") != "success":
        pago.estado = PagoBancard.Estado.ERROR
        pago.save(update_fields=["estado"])
        msgs = resultado.get("messages", [])
        desc = msgs[0].get("dsc", "Error al iniciar el pago.") if msgs else "Error al iniciar el pago."
        return Response({"detail": desc}, status=status.HTTP_502_BAD_GATEWAY)

    process_id = resultado.get("process_id", "")
    pago.process_id = process_id
    pago.save(update_fields=["process_id"])

    return Response({
        "shop_process_id": shop_process_id,
        "process_id": process_id,
        "redirect_url": bancard_service.pago_url(process_id),
        "script_url": bancard_service.checkout_script_url(),
    }, status=status.HTTP_201_CREATED)


# ─── POST /api/v1/bancard/confirmar/ ─────────────────────────────────────────
# Webhook que Bancard llama al completarse un pago (sin autenticación JWT).
# Debe responder 200 con {"status": "success"} en < 30 segundos.

@api_view(["POST", "GET"])
@permission_classes([])
@throttle_classes([BancardRetornoThrottle])
def bancard_confirmar(request):
    """
    Bancard hace POST aquí al finalizar una transacción (single_buy_confirm).
    Verifica el token, acredita el saldo y responde {"status": "success"}.
    GET se usa solo para que el panel Bancard valide que la URL existe.
    """
    if request.method == "GET":
        return Response({"status": "ok"})

    operation = request.data.get("operation", {})
    shop_process_id = str(operation.get("shop_process_id", ""))
    token_recibido  = operation.get("token", "")
    response_code   = operation.get("response_code", "")
    monto_raw       = operation.get("amount", "0")

    if not shop_process_id:
        return Response({"status": "error"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        monto = int(float(monto_raw))
    except (TypeError, ValueError):
        monto = 0

    # Verificar token Bancard: md5(private_key + shop_process_id + "confirm" + amount + currency)
    token_esperado = bancard_service._token_confirm_webhook(shop_process_id, monto)
    if token_recibido != token_esperado:
        logger.warning("Bancard confirmar: token inválido shop=%s", shop_process_id)
        return Response({"status": "error"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        pago = PagoBancard.objects.get(shop_process_id=shop_process_id)
    except PagoBancard.DoesNotExist:
        logger.warning("Bancard confirmar: PagoBancard no encontrado shop=%s", shop_process_id)
        return Response({"status": "success"})  # Siempre 200 para no re-intentos de Bancard

    # Idempotente: si ya fue procesado no volver a acreditar
    if pago.estado != PagoBancard.Estado.PENDIENTE:
        return Response({"status": "success"})

    pago.bancard_response = request.data
    pago.save(update_fields=["bancard_response"])

    if response_code == "00":
        es_almuerzo = pago.tipo == PagoBancard.Tipo.ALMUERZO
        try:
            if es_almuerzo:
                bancard_service.acreditar_pago_almuerzo(pago)
            else:
                bancard_service.acreditar_saldo(pago)
                try:
                    from celery import current_app
                    current_app.send_task(
                        "apps.contabilidad.tasks.refrescar_mv_balance_cliente",
                        countdown=3,
                    )
                except Exception as exc:
                    logger.warning("No se pudo programar refrescar_mv_balance_cliente: %s", exc)
        except Exception as exc:
            logger.error("Bancard confirmar: error acreditando shop=%s: %s", shop_process_id, exc)
            pago.estado = PagoBancard.Estado.ERROR
            pago.save(update_fields=["estado"])
    else:
        pago.estado = PagoBancard.Estado.RECHAZADO
        pago.fecha_confirmacion = timezone.now()
        pago.save(update_fields=["estado", "fecha_confirmacion"])
        logger.info("Bancard confirmar: pago rechazado shop=%s code=%s", shop_process_id, response_code)

    return Response({"status": "success"})


# ─── GET /api/v1/bancard/retorno/ ─────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([])   # Bancard redirige el browser del padre sin sesión activa
@throttle_classes([BancardRetornoThrottle])
def bancard_retorno(request):
    """
    Bancard redirige el navegador del padre aquí tras completar el pago.
    El webhook POST /confirmar/ ya procesó el resultado — aquí solo leemos
    el estado y redirigimos al portal.
    Si el webhook todavía no llegó, consultamos a Bancard como fallback.
    """
    shop_process_id = request.GET.get("shop_process_id", "")

    if not shop_process_id:
        return HttpResponseRedirect(f"{PORTAL_URL()}/portal/carga-saldo?estado=error&msg=sin_id")

    try:
        pago = PagoBancard.objects.get(shop_process_id=shop_process_id)
    except PagoBancard.DoesNotExist:
        return HttpResponseRedirect(f"{PORTAL_URL()}/portal/carga-saldo?estado=error&msg=no_encontrado")

    destino_base = "pagar-almuerzo" if pago.tipo == PagoBancard.Tipo.ALMUERZO else "carga-saldo"

    # Si el webhook ya procesó el pago, redirigir directamente
    if pago.estado == PagoBancard.Estado.APROBADO:
        return HttpResponseRedirect(
            f"{PORTAL_URL()}/portal/{destino_base}?estado=aprobado&monto={pago.monto}"
        )
    if pago.estado == PagoBancard.Estado.RECHAZADO:
        return HttpResponseRedirect(
            f"{PORTAL_URL()}/portal/{destino_base}?estado=rechazado&monto={pago.monto}"
        )
    if pago.estado == PagoBancard.Estado.ERROR:
        return HttpResponseRedirect(
            f"{PORTAL_URL()}/portal/{destino_base}?estado=error&msg=acreditacion"
        )

    # Fallback: webhook aún no llegó — consultar estado a Bancard
    resultado = bancard_service.get_confirmation(shop_process_id)
    pago.bancard_response = resultado
    pago.save(update_fields=["bancard_response"])

    confirmacion = resultado.get("confirmation", {})
    response_code = confirmacion.get("response_code", "")

    if resultado.get("status") == "success" and response_code == "00":
        es_almuerzo = pago.tipo == PagoBancard.Tipo.ALMUERZO
        try:
            if es_almuerzo:
                bancard_service.acreditar_pago_almuerzo(pago)
            else:
                bancard_service.acreditar_saldo(pago)
        except Exception as exc:
            logger.error("Retorno fallback: error acreditando shop=%s: %s", shop_process_id, exc)
            pago.estado = PagoBancard.Estado.ERROR
            pago.save(update_fields=["estado"])
            return HttpResponseRedirect(
                f"{PORTAL_URL()}/portal/{destino_base}?estado=error&msg=acreditacion"
            )
        return HttpResponseRedirect(
            f"{PORTAL_URL()}/portal/{destino_base}?estado=aprobado&monto={pago.monto}"
        )

    pago.estado = PagoBancard.Estado.RECHAZADO
    pago.fecha_confirmacion = timezone.now()
    pago.save(update_fields=["estado", "fecha_confirmacion"])
    return HttpResponseRedirect(
        f"{PORTAL_URL()}/portal/{destino_base}?estado=rechazado&monto={pago.monto}"
    )


# ─── GET /api/v1/bancard/estado/<shop_process_id>/ ────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def bancard_estado(request, shop_process_id: str):
    """
    Permite al frontend consultar el estado actual de un PagoBancard.
    Útil para polling tras volver de la página de Bancard.
    """
    try:
        pago = PagoBancard.objects.get(shop_process_id=shop_process_id)
    except PagoBancard.DoesNotExist:
        return Response({"detail": "No encontrado."}, status=status.HTTP_404_NOT_FOUND)

    # Solo el dueño de la tarjeta (o admin) puede consultar
    cliente_usuario = getattr(request.user, "cliente", None)
    if (
        request.user.rol not in ("ADMIN",)
        and pago.cliente != cliente_usuario
    ):
        return Response({"detail": "Sin permiso."}, status=status.HTTP_403_FORBIDDEN)

    return Response({
        "shop_process_id": pago.shop_process_id,
        "estado": pago.estado,
        "monto": pago.monto,
        "fecha_creacion": pago.fecha_creacion,
        "fecha_confirmacion": pago.fecha_confirmacion,
    })
