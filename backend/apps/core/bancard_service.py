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

def _token(shop_process_id: str, suffix: str) -> str:
    """
    MD5(private_key + shop_process_id + suffix)
    suffix = "request"       para crear transacción
    suffix = "confirmacion"  para verificar resultado
    """
    raw = f"{_private_key()}{shop_process_id}{suffix}"
    # MD5 es requerido por el protocolo Bancard vPOS — no es una elección de seguridad propia.
    return hashlib.md5(raw.encode("utf-8"), usedforsecurity=False).hexdigest()  # nosec B324


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
            "token": _token(shop_process_id, "request"),
            "shop_process_id": shop_process_id,
            "amount": f"{int(monto)}.00",
            "currency": "PYG",
            "description": descripcion[:20],  # Bancard limita a 20 chars
            "return_url": return_url,
            "cancel_url": cancel_url,
            "zimple": False,
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


def confirmar_pago(shop_process_id: str) -> dict:
    """
    Consulta el resultado de una transacción ya procesada por el titular.

    Retorna el JSON de Bancard con el campo "status":
      "success" + "confirmation" con payment_id y response_code
      "error"   + "messages" con descripción
    """
    payload = {
        "public_key": _public_key(),
        "operation": {
            "token": _token(shop_process_id, "confirmacion"),
            "shop_process_id": shop_process_id,
        },
    }

    try:
        with _bancard_cb:
            resp = http_client.post(
                f"{_base_url()}/vpos/api/0.3/single_buy/{shop_process_id}",
                json=payload,
                timeout=30,
                verify=getattr(settings, "BANCARD_SANDBOX", True) is False,
            )
        data = resp.json()
    except CircuitBreakerOpen as exc:
        logger.warning("Bancard confirmar_pago bloqueado por circuit breaker shop=%s: %s", shop_process_id, exc)
        return {"status": "error", "messages": [
            {"dsc": "Gateway de pagos temporalmente no disponible. Intente en unos minutos."}
        ]}
    except Exception as exc:
        logger.error("Bancard confirmar_pago error shop=%s: %s", shop_process_id, exc)
        return {"status": "error", "messages": [{"dsc": str(exc)}]}

    logger.info("Bancard confirmar_pago shop=%s status=%s", shop_process_id, data.get("status"))
    return data


# ─── URL del hosted payment page ──────────────────────────────────────────────

def pago_url(process_id: str) -> str:
    """URL de Bancard donde el titular ingresa sus datos de tarjeta."""
    return f"{_base_url()}/payment-card?process_id={process_id}"


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

    usuario = pago_bancard.cliente.usuario
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
