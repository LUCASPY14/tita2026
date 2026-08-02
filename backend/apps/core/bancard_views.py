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
from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.throttling import SensitiveEndpointThrottle

from .models import PagoBancard, SolicitudCatastroBancard, Tarjeta
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

    if monto < 5_000:
        return Response(
            {"detail": "El monto mínimo de carga es ₲5.000."},
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
    cancel_url = getattr(
        settings, "BANCARD_CANCEL_URL",
        f"{PORTAL_URL()}/pago-completado?estado=cancelado&tipo=saldo",
    )

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
    cancel_url = getattr(
        settings, "BANCARD_CANCEL_URL_ALMUERZO",
        f"{PORTAL_URL()}/pago-completado?estado=cancelado&tipo=almuerzo",
    )

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

    bancard_service.procesar_resultado_pago(pago, response_code)

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

    tipo_param = "almuerzo" if pago.tipo == PagoBancard.Tipo.ALMUERZO else "saldo"

    def _resultado_url(estado: str, monto: int | None = None) -> str:
        url = f"{PORTAL_URL()}/pago-completado?estado={estado}&tipo={tipo_param}"
        if monto is not None:
            url += f"&monto={monto}"
        return url

    # Si el webhook ya procesó el pago, redirigir directamente
    if pago.estado == PagoBancard.Estado.APROBADO:
        return HttpResponseRedirect(_resultado_url("aprobado", pago.monto))
    if pago.estado == PagoBancard.Estado.RECHAZADO:
        return HttpResponseRedirect(_resultado_url("rechazado", pago.monto))
    if pago.estado == PagoBancard.Estado.ERROR:
        return HttpResponseRedirect(_resultado_url("error"))

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
            return HttpResponseRedirect(_resultado_url("error"))
        return HttpResponseRedirect(_resultado_url("aprobado", pago.monto))

    pago.estado = PagoBancard.Estado.RECHAZADO
    pago.fecha_confirmacion = timezone.now()
    pago.save(update_fields=["estado", "fecha_confirmacion"])
    return HttpResponseRedirect(_resultado_url("rechazado", pago.monto))


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


# ─── Tarjetas guardadas (catastro y pago con token) ───────────────────────────

def _obtener_alias_token(user_id: int, card_id: int) -> tuple[str | None, str]:
    """Busca en users_cards la tarjeta con ese card_id y devuelve su alias_token fresco."""
    resultado = bancard_service.listar_tarjetas(user_id)
    if resultado.get("status") != "success":
        return None, ""
    for tarjeta in resultado.get("cards") or []:
        try:
            if int(tarjeta.get("card_id")) == card_id:
                return tarjeta.get("alias_token"), tarjeta.get("card_masked_number", "")
        except (TypeError, ValueError):
            continue
    return None, ""


def _resolver_respuesta_charge(pago: PagoBancard, resultado: dict) -> Response:
    """
    Interpreta la respuesta de bancard_service.pagar_con_token y resuelve el PagoBancard:
    - status: error → fallo de request, marca ERROR.
    - detalle.process_id presente → requiere 3D Secure, el frontend debe levantar el iframe.
    - detalle.response_code presente → resuelto en el mismo request (aprobado o rechazado).

    El manual documenta el detalle bajo "operation", pero en la práctica Bancard lo
    devuelve bajo "confirmation" para un charge resuelto sincrónicamente (confirmado
    contra sandbox real) — se acepta cualquiera de las dos claves.
    """
    if resultado.get("status") == "error":
        pago.estado = PagoBancard.Estado.ERROR
        pago.save(update_fields=["estado"])
        msgs = resultado.get("messages", [])
        desc = msgs[0].get("dsc", "Error al procesar el pago.") if msgs else "Error al procesar el pago."
        return Response({"detail": desc}, status=status.HTTP_502_BAD_GATEWAY)

    detalle = resultado.get("confirmation") or resultado.get("operation") or {}
    process_id = detalle.get("process_id")

    if process_id:
        pago.process_id = process_id
        pago.save(update_fields=["process_id"])
        return Response({
            "shop_process_id": pago.shop_process_id,
            "process_id": process_id,
            "script_url": bancard_service.checkout_script_url(),
            "requires_3ds": True,
        }, status=status.HTTP_201_CREATED)

    response_code = detalle.get("response_code")
    if not response_code:
        pago.estado = PagoBancard.Estado.ERROR
        pago.save(update_fields=["estado"])
        return Response({"detail": "Respuesta inesperada de Bancard."}, status=status.HTTP_502_BAD_GATEWAY)

    bancard_service.procesar_resultado_pago(pago, response_code)
    pago.refresh_from_db(fields=["estado"])

    if pago.estado == PagoBancard.Estado.APROBADO:
        return Response({"estado": "aprobado", "monto": int(pago.monto), "shop_process_id": pago.shop_process_id})
    if pago.estado == PagoBancard.Estado.ERROR:
        return Response(
            {"detail": "Ocurrió un error al acreditar el pago. Contactá con la administración."},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    return Response({"estado": "rechazado", "detail": detalle.get("response_description", "Pago rechazado.")})


# ─── POST /api/v1/bancard/tarjetas/catastro/ ──────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([SensitiveEndpointThrottle])
def bancard_catastro_tarjeta(request):
    """
    Inicia el catastro de una tarjeta guardada (cards_new).
    Respuesta: { "process_id": "...", "script_url": "...", "card_id": 1 }
    """
    cliente = getattr(request.user, "cliente", None)
    if cliente is None:
        return Response(
            {"detail": "Tu usuario no tiene un perfil de cliente asociado."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not bancard_service._public_key() or not bancard_service._private_key():
        return Response(
            {"detail": "La integración de pagos no está configurada. Contactá con la administración."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    card_id = bancard_service.proxima_tarjeta_guardada_disponible(cliente.id)
    if card_id is None:
        return Response(
            {"detail": "Ya alcanzaste el máximo de 5 tarjetas guardadas."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    referencia = str(int(time.time() * 1000))
    SolicitudCatastroBancard.objects.create(
        cliente=cliente,
        referencia=referencia,
        card_id=card_id,
        ip_origen=request.META.get("REMOTE_ADDR"),
    )

    # No derivamos del path de BANCARD_RETURN_URL (puede ser el alias corto
    # /api/v1/bancard/retorno/ o el path completo /api/v1/core/bancard/retorno/,
    # ambos válidos para ese webhook) — reconstruimos el host y apuntamos directo
    # al path real de este endpoint, montado bajo apps.core.urls.
    parsed = urlsplit(settings.BANCARD_RETURN_URL)
    host_base = f"{parsed.scheme}://{parsed.netloc}"
    return_url = f"{host_base}/api/v1/core/bancard/tarjetas/retorno-catastro/?referencia={referencia}"

    resultado = bancard_service.catastro_tarjeta(
        card_id=card_id,
        user_id=cliente.id,
        user_cell_phone=cliente.telefono or "",
        user_mail=cliente.email or "",
        return_url=return_url,
    )

    if resultado.get("status") != "success":
        msgs = resultado.get("messages", [])
        desc = msgs[0].get("dsc", "Error al iniciar el catastro.") if msgs else "Error al iniciar el catastro."
        return Response({"detail": desc}, status=status.HTTP_502_BAD_GATEWAY)

    process_id = resultado.get("process_id", "")
    SolicitudCatastroBancard.objects.filter(referencia=referencia).update(process_id=process_id)

    return Response({
        "process_id": process_id,
        "script_url": bancard_service.checkout_script_url(),
        "card_id": card_id,
    }, status=status.HTTP_201_CREATED)


# ─── GET /api/v1/bancard/tarjetas/retorno-catastro/ ───────────────────────────

@api_view(["GET"])
@permission_classes([])   # Bancard redirige el browser del padre sin sesión activa
@throttle_classes([BancardRetornoThrottle])
def bancard_retorno_catastro(request):
    """
    Bancard redirige el navegador aquí tras completar (o abandonar) el catastro,
    agregando su propio parámetro `status` a la return_url (add_new_card_success /
    add_new_card_fail — ver manual, sección "Mensajes de respuesta del iframe de
    catastro"). Esa es la señal autoritativa: el `card_id` que nosotros elegimos al
    iniciar el catastro es solo un identificador de la solicitud — Bancard NO lo
    devuelve en users_cards (ahí usa su propio id interno), así que no sirve para
    verificar por matching contra la lista de tarjetas.
    """
    referencia = request.GET.get("referencia", "")
    if not referencia:
        return HttpResponseRedirect(f"{PORTAL_URL()}/pago-completado?estado=error&tipo=catastro")

    try:
        solicitud = SolicitudCatastroBancard.objects.get(referencia=referencia)
    except SolicitudCatastroBancard.DoesNotExist:
        return HttpResponseRedirect(f"{PORTAL_URL()}/pago-completado?estado=error&tipo=catastro")

    solicitud.resuelto = True
    solicitud.save(update_fields=["resuelto"])

    tarjeta_confirmada = request.GET.get("status") == "add_new_card_success"
    estado = "aprobado" if tarjeta_confirmada else "rechazado"
    return HttpResponseRedirect(f"{PORTAL_URL()}/pago-completado?estado={estado}&tipo=catastro")


# ─── GET /api/v1/bancard/tarjetas/ ─────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def bancard_listar_tarjetas(request):
    """Lista las tarjetas guardadas del cliente autenticado (consulta en vivo a Bancard)."""
    cliente = getattr(request.user, "cliente", None)
    if cliente is None:
        return Response(
            {"detail": "Tu usuario no tiene un perfil de cliente asociado."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    resultado = bancard_service.listar_tarjetas(cliente.id)
    if resultado.get("status") != "success":
        return Response({"tarjetas": []})

    tarjetas = []
    for tarjeta in resultado.get("cards") or []:
        try:
            card_id = int(tarjeta.get("card_id"))
        except (TypeError, ValueError):
            continue
        tarjetas.append({
            "card_id": card_id,
            "card_masked_number": tarjeta.get("card_masked_number", ""),
            "card_brand": tarjeta.get("card_brand", ""),
            "expiration_date": tarjeta.get("expiration_date", ""),
        })

    return Response({"tarjetas": tarjetas})


# ─── DELETE /api/v1/bancard/tarjetas/<card_id>/ ────────────────────────────────

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@throttle_classes([SensitiveEndpointThrottle])
def bancard_eliminar_tarjeta(request, card_id: int):
    """Elimina una tarjeta guardada del cliente autenticado."""
    cliente = getattr(request.user, "cliente", None)
    if cliente is None:
        return Response(
            {"detail": "Tu usuario no tiene un perfil de cliente asociado."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    alias_token, _ = _obtener_alias_token(cliente.id, card_id)
    if alias_token is None:
        return Response({"detail": "Tarjeta no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    resultado = bancard_service.eliminar_tarjeta(user_id=cliente.id, alias_token=alias_token)
    if resultado.get("status") != "success":
        return Response({"detail": "No se pudo eliminar la tarjeta."}, status=status.HTTP_502_BAD_GATEWAY)

    return Response({"status": "success"})


# ─── POST /api/v1/bancard/pagar-con-tarjeta/ ───────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([SensitiveEndpointThrottle])
def bancard_pagar_con_tarjeta(request):
    """
    Recarga de saldo pagando con una tarjeta guardada (charge).
    Body: { "nro_tarjeta": "...", "monto": 150000, "card_id": 1 }
    """
    nro_tarjeta = request.data.get("nro_tarjeta")
    monto_raw = request.data.get("monto")
    card_id_raw = request.data.get("card_id")

    if not nro_tarjeta or not monto_raw or not card_id_raw:
        return Response(
            {"detail": "Se requieren nro_tarjeta, monto y card_id."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        monto = int(monto_raw)
        card_id = int(card_id_raw)
    except (TypeError, ValueError):
        return Response({"detail": "Datos inválidos."}, status=status.HTTP_400_BAD_REQUEST)

    if monto < 5_000:
        return Response(
            {"detail": "El monto mínimo de carga es ₲5.000."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if monto > 5_000_000:
        return Response(
            {"detail": "El monto máximo de carga es ₲5.000.000."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        tarjeta = Tarjeta.objects.get(nro_tarjeta=nro_tarjeta)
    except Tarjeta.DoesNotExist:
        return Response({"detail": "Tarjeta no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    if tarjeta.estado != Tarjeta.Estado.ACTIVA:
        return Response(
            {"detail": f"La tarjeta está {tarjeta.estado.lower()}. No se puede recargar."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cliente = getattr(request.user, "cliente", None)
    if cliente is None:
        return Response(
            {"detail": "Tu usuario no tiene un perfil de cliente asociado."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not bancard_service._public_key() or not bancard_service._private_key():
        return Response(
            {"detail": "La integración de pagos no está configurada. Contactá con la administración."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    alias_token, card_masked = _obtener_alias_token(cliente.id, card_id)
    if alias_token is None:
        return Response(
            {"detail": "Tarjeta guardada no encontrada. Puede haber vencido — intentá agregarla de nuevo."},
            status=status.HTTP_404_NOT_FOUND,
        )

    shop_process_id = str(int(time.time() * 1000))
    pago = PagoBancard.objects.create(
        tarjeta=tarjeta,
        cliente=cliente,
        shop_process_id=shop_process_id,
        monto=monto,
        descripcion=f"Recarga tarjeta {nro_tarjeta}",
        card_id_bancard=card_id,
        card_masked_number=card_masked,
        ip_origen=request.META.get("REMOTE_ADDR"),
    )

    return_url = f"{settings.BANCARD_RETURN_URL}?shop_process_id={shop_process_id}"
    resultado = bancard_service.pagar_con_token(
        shop_process_id=shop_process_id,
        monto=monto,
        alias_token=alias_token,
        descripcion=pago.descripcion,
        return_url=return_url,
    )
    pago.bancard_response = resultado
    pago.save(update_fields=["bancard_response"])

    return _resolver_respuesta_charge(pago, resultado)


# ─── POST /api/v1/bancard/pagar-almuerzo-con-tarjeta/ ─────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([SensitiveEndpointThrottle])
def bancard_pagar_almuerzo_con_tarjeta(request):
    """
    Pago de cuenta de almuerzo con una tarjeta guardada (charge).
    Body: { "cuenta_id": 42, "monto": 150000, "card_id": 1 }
    """
    if request.user.rol != "CLIENTE_WEB":
        return Response(
            {"detail": "Solo los padres pueden pagar almuerzos desde el portal."},
            status=status.HTTP_403_FORBIDDEN,
        )

    cuenta_id = request.data.get("cuenta_id")
    monto_raw = request.data.get("monto")
    card_id_raw = request.data.get("card_id")

    if not cuenta_id or not monto_raw or not card_id_raw:
        return Response(
            {"detail": "Se requieren cuenta_id, monto y card_id."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        monto = int(monto_raw)
        card_id = int(card_id_raw)
    except (TypeError, ValueError):
        return Response({"detail": "Datos inválidos."}, status=status.HTTP_400_BAD_REQUEST)

    if monto <= 0:
        return Response({"detail": "El monto debe ser mayor a cero."}, status=status.HTTP_400_BAD_REQUEST)

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

    alias_token, card_masked = _obtener_alias_token(cliente.id, card_id)
    if alias_token is None:
        return Response(
            {"detail": "Tarjeta guardada no encontrada. Puede haber vencido — intentá agregarla de nuevo."},
            status=status.HTTP_404_NOT_FOUND,
        )

    shop_process_id = str(int(time.time() * 1000))
    pago = PagoBancard.objects.create(
        tipo=PagoBancard.Tipo.ALMUERZO,
        cuenta_almuerzo=cuenta,
        cliente=cliente,
        shop_process_id=shop_process_id,
        monto=monto,
        descripcion=f"Almuerzo {cuenta.hijo} {cuenta.mes}/{cuenta.anio}"[:20],
        card_id_bancard=card_id,
        card_masked_number=card_masked,
        ip_origen=request.META.get("REMOTE_ADDR"),
    )

    return_url = f"{settings.BANCARD_RETURN_URL}?shop_process_id={shop_process_id}"
    resultado = bancard_service.pagar_con_token(
        shop_process_id=shop_process_id,
        monto=monto,
        alias_token=alias_token,
        descripcion=pago.descripcion,
        return_url=return_url,
    )
    pago.bancard_response = resultado
    pago.save(update_fields=["bancard_response"])

    return _resolver_respuesta_charge(pago, resultado)
