"""
Servicio de integración con Bancard vPOS.

Flujo Single Buy:
  1. iniciar_pago()         → crea transacción en Bancard, devuelve process_id
  2. pago_url(process_id)   → URL donde el padre ingresa sus datos de tarjeta
  3. confirmar_pago()       → verifica el resultado con la API de Bancard
  4. acreditar_saldo()      → crea CargaSaldo + MovimientoTarjeta

Documentación oficial: https://comercios.bancard.com.py/docs/vpos
"""

import hashlib
import logging

import requests as http_client
from django.conf import settings
from django.utils import timezone

from common.circuit_breaker import CircuitBreaker, CircuitBreakerOpen

logger = logging.getLogger(__name__)

# Abre el circuito tras 5 fallos consecutivos; intenta recuperar tras 60s.
_bancard_cb = CircuitBreaker(
    name="bancard",
    failure_threshold=5,
    recovery_timeout=60.0,
    expected_exception=Exception,
)

# ─── Configuración ────────────────────────────────────────────────────────────

_SANDBOX_URL = "https://vpos.infonet.com.py:8888"
_PROD_URL    = "https://vpos.infonet.com.py"


def _base_url() -> str:
    return _SANDBOX_URL if getattr(settings, "BANCARD_SANDBOX", True) else _PROD_URL


def _public_key() -> str:
    return getattr(settings, "BANCARD_PUBLIC_KEY", "")


def _private_key() -> str:
    return getattr(settings, "BANCARD_PRIVATE_KEY", "")


# ─── Tokens ───────────────────────────────────────────────────────────────────

def _md5(*parts: str) -> str:
    # MD5 es requerido por el protocolo Bancard vPOS — no es una elección de seguridad propia.
    return hashlib.md5("".join(parts).encode("utf-8"), usedforsecurity=False).hexdigest()  # nosec B324


def _token_single_buy(shop_process_id: str, monto: int) -> str:
    """md5(private_key + shop_process_id + amount + currency)"""
    amount = f"{int(monto)}.00"
    return _md5(_private_key(), str(shop_process_id), amount, "PYG")


def _token_confirm_webhook(shop_process_id: str, monto: int) -> str:
    """md5(private_key + shop_process_id + 'confirm' + amount + currency) — verifica webhook entrante."""
    amount = f"{int(monto)}.00"
    return _md5(_private_key(), str(shop_process_id), "confirm", amount, "PYG")


def _token_get_confirmation(shop_process_id: str) -> str:
    """md5(private_key + shop_process_id + 'get_confirmation')"""
    return _md5(_private_key(), str(shop_process_id), "get_confirmation")


def _token_rollback(shop_process_id: str) -> str:
    """md5(private_key + shop_process_id + 'rollback' + '0.00')"""
    return _md5(_private_key(), str(shop_process_id), "rollback", "0.00")


def _token_cards_new(card_id: int, user_id: int) -> str:
    """md5(private_key + card_id + user_id + 'request_new_card')"""
    return _md5(_private_key(), str(card_id), str(user_id), "request_new_card")


def _token_users_cards(user_id: int) -> str:
    """md5(private_key + user_id + 'request_user_cards')"""
    return _md5(_private_key(), str(user_id), "request_user_cards")


def _token_charge(shop_process_id: str, monto: int, alias_token: str) -> str:
    """md5(private_key + shop_process_id + 'charge' + amount + currency + alias_token)"""
    amount = f"{int(monto)}.00"
    return _md5(_private_key(), str(shop_process_id), "charge", amount, "PYG", alias_token)


def _token_delete_card(user_id: int, card_token: str) -> str:
    """md5(private_key + 'delete_card' + user_id + card_token)"""
    return _md5(_private_key(), "delete_card", str(user_id), card_token)


# ─── API calls ────────────────────────────────────────────────────────────────

def iniciar_pago(
    *,
    shop_process_id: str,
    monto: int,
    descripcion: str,
    return_url: str,
    cancel_url: str,
) -> dict:
    """
    Crea una transacción Single Buy en Bancard.

    Retorna el JSON de Bancard. En caso de éxito:
      {"status": "success", "process_id": "xxxx-xxxx-..."}

    En caso de error:
      {"status": "error", "messages": [...]}
    """
    payload = {
        "public_key": _public_key(),
        "operation": {
            "token": _token_single_buy(shop_process_id, monto),
            "shop_process_id": shop_process_id,
            "amount": f"{int(monto)}.00",
            "currency": "PYG",
            "description": descripcion[:20],  # Bancard limita a 20 chars
            "return_url": return_url,
            "cancel_url": cancel_url,
        },
    }

    try:
        with _bancard_cb:
            resp = http_client.post(
                f"{_base_url()}/vpos/api/0.3/single_buy",
                json=payload,
                timeout=30,
                verify=getattr(settings, "BANCARD_SANDBOX", True) is False,
            )
        data = resp.json()
    except CircuitBreakerOpen as exc:
        logger.warning("Bancard iniciar_pago bloqueado por circuit breaker: %s", exc)
        return {"status": "error", "messages": [
            {"dsc": "Gateway de pagos temporalmente no disponible. Intente en unos minutos."}
        ]}
    except Exception as exc:
        logger.error("Bancard iniciar_pago error: %s", exc)
        return {"status": "error", "messages": [{"dsc": str(exc)}]}

    logger.info("Bancard iniciar_pago shop=%s status=%s", shop_process_id, data.get("status"))
    return data


def get_confirmation(shop_process_id: str) -> dict:
    """
    Consulta el resultado de una transacción (get_single_buy_confirmation).

    Retorna el JSON de Bancard con el campo "status":
      "success" + "confirmation" con response_code
      "error"   + "messages" con descripción
    """
    payload = {
        "public_key": _public_key(),
        "operation": {
            "token": _token_get_confirmation(shop_process_id),
            "shop_process_id": shop_process_id,
        },
    }

    try:
        with _bancard_cb:
            resp = http_client.post(
                f"{_base_url()}/vpos/api/0.3/single_buy/confirmations",
                json=payload,
                timeout=30,
                verify=getattr(settings, "BANCARD_SANDBOX", True) is False,
            )
        data = resp.json()
    except CircuitBreakerOpen as exc:
        logger.warning("Bancard get_confirmation bloqueado por circuit breaker shop=%s: %s", shop_process_id, exc)
        return {"status": "error", "messages": [
            {"dsc": "Gateway de pagos temporalmente no disponible. Intente en unos minutos."}
        ]}
    except Exception as exc:
        logger.error("Bancard get_confirmation error shop=%s: %s", shop_process_id, exc)
        return {"status": "error", "messages": [{"dsc": str(exc)}]}

    logger.info("Bancard get_confirmation shop=%s status=%s", shop_process_id, data.get("status"))
    return data


def rollback(shop_process_id: str) -> dict:
    """Reversa una transacción (single_buy_rollback)."""
    payload = {
        "public_key": _public_key(),
        "operation": {
            "token": _token_rollback(shop_process_id),
            "shop_process_id": shop_process_id,
        },
    }

    try:
        with _bancard_cb:
            resp = http_client.post(
                f"{_base_url()}/vpos/api/0.3/single_buy/rollback",
                json=payload,
                timeout=30,
                verify=getattr(settings, "BANCARD_SANDBOX", True) is False,
            )
        data = resp.json()
    except CircuitBreakerOpen as exc:
        logger.warning("Bancard rollback bloqueado shop=%s: %s", shop_process_id, exc)
        return {"status": "error", "messages": [{"dsc": "Gateway no disponible."}]}
    except Exception as exc:
        logger.error("Bancard rollback error shop=%s: %s", shop_process_id, exc)
        return {"status": "error", "messages": [{"dsc": str(exc)}]}

    logger.info("Bancard rollback shop=%s status=%s", shop_process_id, data.get("status"))
    return data


# ─── Tarjetas guardadas (catastro y pago con token) ───────────────────────────

def catastro_tarjeta(
    *,
    card_id: int,
    user_id: int,
    user_cell_phone: str,
    user_mail: str,
    return_url: str,
) -> dict:
    """Inicia el catastro de una tarjeta (cards_new). Devuelve process_id para el iframe."""
    payload = {
        "public_key": _public_key(),
        "operation": {
            "token": _token_cards_new(card_id, user_id),
            "card_id": card_id,
            "user_id": user_id,
            "user_cell_phone": user_cell_phone,
            "user_mail": user_mail,
            "return_url": return_url,
        },
    }

    try:
        with _bancard_cb:
            resp = http_client.post(
                f"{_base_url()}/vpos/api/0.3/cards/new",
                json=payload,
                timeout=30,
                verify=getattr(settings, "BANCARD_SANDBOX", True) is False,
            )
        data = resp.json()
    except CircuitBreakerOpen as exc:
        logger.warning("Bancard catastro_tarjeta bloqueado card_id=%s user_id=%s: %s", card_id, user_id, exc)
        return {"status": "error", "messages": [
            {"dsc": "Gateway de pagos temporalmente no disponible. Intente en unos minutos."}
        ]}
    except Exception as exc:
        logger.error("Bancard catastro_tarjeta error card_id=%s user_id=%s: %s", card_id, user_id, exc)
        return {"status": "error", "messages": [{"dsc": str(exc)}]}

    logger.info("Bancard catastro_tarjeta card_id=%s user_id=%s status=%s", card_id, user_id, data.get("status"))
    return data


def listar_tarjetas(user_id: int) -> dict:
    """Lista las tarjetas catastradas de un usuario (users_cards), con alias_token fresco."""
    payload = {
        "public_key": _public_key(),
        "operation": {
            "token": _token_users_cards(user_id),
            "extra_response_attributes": ["cards.bancard_proccesed"],
        },
    }

    try:
        with _bancard_cb:
            resp = http_client.post(
                f"{_base_url()}/vpos/api/0.3/users/{user_id}/cards",
                json=payload,
                timeout=30,
                verify=getattr(settings, "BANCARD_SANDBOX", True) is False,
            )
        data = resp.json()
    except CircuitBreakerOpen as exc:
        logger.warning("Bancard listar_tarjetas bloqueado user_id=%s: %s", user_id, exc)
        return {"status": "error", "messages": [
            {"dsc": "Gateway de pagos temporalmente no disponible. Intente en unos minutos."}
        ]}
    except Exception as exc:
        logger.error("Bancard listar_tarjetas error user_id=%s: %s", user_id, exc)
        return {"status": "error", "messages": [{"dsc": str(exc)}]}

    logger.info("Bancard listar_tarjetas user_id=%s status=%s", user_id, data.get("status"))
    return data


def pagar_con_token(
    *,
    shop_process_id: str,
    monto: int,
    alias_token: str,
    descripcion: str,
    return_url: str,
) -> dict:
    """
    Cobra usando una tarjeta guardada (charge). La respuesta puede venir resuelta en el
    mismo request (con response_code) o requerir 3D Secure (con process_id para un iframe).
    """
    payload = {
        "public_key": _public_key(),
        "operation": {
            "token": _token_charge(shop_process_id, monto, alias_token),
            "shop_process_id": shop_process_id,
            "amount": f"{int(monto)}.00",
            "currency": "PYG",
            "number_of_payments": 1,
            "description": descripcion[:20],
            # El manual lo marca opcional, pero Bancard lo exige en la práctica para charge.
            "additional_data": "",
            "alias_token": alias_token,
            "return_url": return_url,
            "extra_response_attributes": ["confirmation.process_id"],
        },
    }

    try:
        with _bancard_cb:
            resp = http_client.post(
                f"{_base_url()}/vpos/api/0.3/charge",
                json=payload,
                timeout=30,
                verify=getattr(settings, "BANCARD_SANDBOX", True) is False,
            )
        data = resp.json()
    except CircuitBreakerOpen as exc:
        logger.warning("Bancard pagar_con_token bloqueado shop=%s: %s", shop_process_id, exc)
        return {"status": "error", "messages": [
            {"dsc": "Gateway de pagos temporalmente no disponible. Intente en unos minutos."}
        ]}
    except Exception as exc:
        logger.error("Bancard pagar_con_token error shop=%s: %s", shop_process_id, exc)
        return {"status": "error", "messages": [{"dsc": str(exc)}]}

    logger.info("Bancard pagar_con_token shop=%s response_code=%s", shop_process_id, (data.get("operation") or {}).get("response_code"))
    return data


def eliminar_tarjeta(*, user_id: int, alias_token: str) -> dict:
    """Elimina una tarjeta catastrada (delete_card)."""
    payload = {
        "public_key": _public_key(),
        "operation": {
            "token": _token_delete_card(user_id, alias_token),
            "alias_token": alias_token,
        },
    }

    try:
        with _bancard_cb:
            resp = http_client.request(
                "DELETE",
                f"{_base_url()}/vpos/api/0.3/users/{user_id}/cards",
                json=payload,
                timeout=30,
                verify=getattr(settings, "BANCARD_SANDBOX", True) is False,
            )
        data = resp.json()
    except CircuitBreakerOpen as exc:
        logger.warning("Bancard eliminar_tarjeta bloqueado user_id=%s: %s", user_id, exc)
        return {"status": "error", "messages": [{"dsc": "Gateway de pagos temporalmente no disponible."}]}
    except Exception as exc:
        logger.error("Bancard eliminar_tarjeta error user_id=%s: %s", user_id, exc)
        return {"status": "error", "messages": [{"dsc": str(exc)}]}

    logger.info("Bancard eliminar_tarjeta user_id=%s status=%s", user_id, data.get("status"))
    return data


# ─── URL del hosted payment page ──────────────────────────────────────────────

def pago_url(process_id: str) -> str:
    """URL de Bancard donde el titular ingresa sus datos de tarjeta (método redirect)."""
    return f"{_base_url()}/payment-card?process_id={process_id}"


def checkout_script_url() -> str:
    """URL del script JS de Bancard Checkout para renderizar el formulario embebido."""
    return f"{_base_url()}/checkout/javascript/dist/bancard-checkout-3.0.0.js"


# ─── Acreditar saldo ──────────────────────────────────────────────────────────

def acreditar_saldo(pago_bancard) -> None:
    """
    Crea el CargaSaldo y acredita el monto en la tarjeta del estudiante.
    Solo se llama cuando Bancard confirma el pago como aprobado.
    """
    from decimal import Decimal
    from .services import TarjetaService

    carga = TarjetaService.cargar_saldo(
        tarjeta=pago_bancard.tarjeta,
        monto=Decimal(pago_bancard.monto),
        cliente_origen=pago_bancard.cliente,
        responsable=None,
        metodo_pago="TARJETA_BANCARD",
        referencia=pago_bancard.shop_process_id,
    )
    pago_bancard.carga_saldo = carga
    pago_bancard.estado = pago_bancard.Estado.APROBADO
    pago_bancard.fecha_confirmacion = timezone.now()
    pago_bancard.save(update_fields=["carga_saldo", "estado", "fecha_confirmacion"])


def acreditar_pago_almuerzo(pago_bancard) -> None:
    """
    Registra un PagoCuentaAlmuerzo y actualiza la CuentaAlmuerzoMensual.
    Solo se llama cuando Bancard confirma el pago de tipo ALMUERZO como aprobado.
    El registrado_por es el usuario CLIENTE_WEB del padre.
    """
    from decimal import Decimal
    from django.db import transaction
    from apps.almuerzos.models import CuentaAlmuerzoMensual, PagoCuentaAlmuerzo

    usuario = pago_bancard.cliente.usuario_portal
    monto = Decimal(pago_bancard.monto)

    with transaction.atomic():
        cuenta = (
            CuentaAlmuerzoMensual.objects
            .select_for_update()
            .get(pk=pago_bancard.cuenta_almuerzo_id)
        )
        PagoCuentaAlmuerzo.objects.create(
            cuenta=cuenta,
            monto=monto,
            medio_pago="BANCARD",
            referencia=pago_bancard.shop_process_id,
            registrado_por=usuario,
        )
        cuenta.registrar_pago(monto)
        pago_bancard.estado = pago_bancard.Estado.APROBADO
        pago_bancard.fecha_confirmacion = timezone.now()
        pago_bancard.save(update_fields=["estado", "fecha_confirmacion"])


def procesar_resultado_pago(pago_bancard, response_code: str) -> None:
    """
    Acredita o rechaza un PagoBancard según el response_code de Bancard.
    Compartido por el webhook de confirmación (single_buy/charge) y por el charge
    síncrono con tarjeta guardada (que puede resolver sin pasar por el webhook).
    Idempotente a nivel de llamador: no reprocesar si pago_bancard.estado != PENDIENTE.
    """
    if response_code == "00":
        es_almuerzo = pago_bancard.tipo == pago_bancard.Tipo.ALMUERZO
        try:
            if es_almuerzo:
                acreditar_pago_almuerzo(pago_bancard)
            else:
                acreditar_saldo(pago_bancard)
                try:
                    from celery import current_app
                    current_app.send_task(
                        "apps.contabilidad.tasks.refrescar_mv_balance_cliente",
                        countdown=3,
                    )
                except Exception as exc:
                    logger.warning("No se pudo programar refrescar_mv_balance_cliente: %s", exc)
        except Exception as exc:
            logger.error("Bancard: error acreditando shop=%s: %s", pago_bancard.shop_process_id, exc)
            pago_bancard.estado = pago_bancard.Estado.ERROR
            pago_bancard.save(update_fields=["estado"])
    else:
        pago_bancard.estado = pago_bancard.Estado.RECHAZADO
        pago_bancard.fecha_confirmacion = timezone.now()
        pago_bancard.save(update_fields=["estado", "fecha_confirmacion"])
        logger.info("Bancard: pago rechazado shop=%s code=%s", pago_bancard.shop_process_id, response_code)


def proxima_tarjeta_guardada_disponible(user_id: int) -> int | None:
    """
    Consulta cuántas tarjetas tiene catastradas el usuario y devuelve el próximo
    card_id a enviar en cards_new (máx. 5 por usuario). None si ya llegó al máximo.

    El card_id que nosotros elegimos aquí es solo un identificador de la solicitud
    de catastro — Bancard NO lo devuelve en users_cards (ahí usa su propio id
    interno, ver bancard_views._obtener_alias_token), así que no hace falta que
    coincida con nada más adelante; alcanza con no repetir uno en uso.
    """
    resultado = listar_tarjetas(user_id)
    cantidad_actual = 0
    if resultado.get("status") == "success":
        cantidad_actual = len(resultado.get("cards") or [])

    if cantidad_actual >= 5:
        return None
    return cantidad_actual + 1
