"""
Tareas asíncronas de Celery para la app core
"""

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from celery import shared_task

from apps.core.models import CargasSaldo, Tarjetas


@shared_task(bind=True, max_retries=3)
def expirar_recargas_pendientes(self):
    """
    Tarea periódica para marcar como expiradas las recargas pendientes
    que superan el tiempo límite (24 horas por defecto).

    Se ejecuta diariamente a las 2 AM vía Celery Beat.

    Returns:
        dict: Resumen de la operación {expiradas: int, errores: int}
    """
    try:
        # Límite de tiempo: 24 horas atrás
        limite_expiracion = timezone.now() - timedelta(hours=24)

        # Buscar recargas pendientes antiguas
        recargas_a_expirar = CargasSaldo.objects.filter(
            estado__in=["pendiente", "pendiente_validacion"], fecha_carga__lt=limite_expiracion
        ).select_for_update()

        contador_expiradas = 0
        contador_errores = 0

        with transaction.atomic():
            for recarga in recargas_a_expirar:
                try:
                    recarga.estado = "expirada"
                    recarga.save(update_fields=["estado"])
                    contador_expiradas += 1
                except Exception as e:  # pragma: no cover
                    contador_errores += 1
                    print(f"Error al expirar recarga {recarga.id_carga}: {e}")

        resultado = {
            "success": True,
            "expiradas": contador_expiradas,
            "errores": contador_errores,
            "timestamp": timezone.now().isoformat(),
        }

        # Log del resultado
        print(f"[Celery] Recargas expiradas: {contador_expiradas}, Errores: {contador_errores}")

        return resultado

    except Exception as e:
        # Retry automático hasta max_retries veces
        raise self.retry(exc=e, countdown=300)  # Retry en 5 minutos


@shared_task
def confirmar_transaccion_bancard(shop_process_id: str):
    """
    Tarea para confirmar manualmente el estado de una transacción Bancard
    si no llegó el webhook.

    Args:
        shop_process_id: ID de la transacción (REC-{id}-{timestamp})

    Returns:
        dict: Resultado de la confirmación
    """
    from apps.api_integrations.services import BancardService

    try:
        bancard_service = BancardService()
        resultado = bancard_service.confirmar_transaccion(shop_process_id)

        if resultado.get("status") == "success":
            # Procesar como si fuera un webhook
            operation = resultado.get("confirmation", {})
            signature = resultado.get("signature", "")

            return bancard_service.procesar_webhook(
                shop_process_id=shop_process_id, operation=operation, signature=signature
            )

        return {
            "success": False,
            "error": "No se pudo confirmar con Bancard",
            "bancard_response": resultado,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@shared_task
def actualizar_saldos_masivos():
    """
    Tarea para recalcular saldos de tarjetas basándose en consumos
    (útil para sincronización o corrección de errores).

    Returns:
        dict: Resumen de la operación
    """
    tarjetas_actualizadas = 0
    errores = 0

    try:
        tarjetas = Tarjetas.objects.filter(estado="activa")

        for tarjeta in tarjetas:
            try:
                with transaction.atomic():
                    # Recalcular saldo desde ConsumosTarjeta
                    from django.db.models import Sum

                    from apps.core.models import ConsumosTarjeta

                    # Suma de consumos (negativos = ingresos, positivos = egresos)
                    suma_consumos = ConsumosTarjeta.objects.filter(nro_tarjeta=tarjeta).aggregate(
                        total=Sum("monto_consumido")
                    )["total"] or Decimal("0")

                    # saldo = recargas - consumos
                    # Si monto_consumido negativo = recarga, entonces saldo = -suma_consumos
                    saldo_calculado = -suma_consumos

                    if tarjeta.saldo_actual != saldo_calculado:
                        tarjeta.saldo_actual = saldo_calculado
                        tarjeta.save(update_fields=["saldo_actual"])
                        tarjetas_actualizadas += 1

            except Exception as e:
                errores += 1
                print(f"Error al actualizar tarjeta {tarjeta.nro_tarjeta}: {e}")

        return {
            "success": True,
            "tarjetas_procesadas": tarjetas.count(),
            "tarjetas_actualizadas": tarjetas_actualizadas,
            "errores": errores,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@shared_task
def limpiar_cache_configuraciones():
    """
    Tarea para limpiar cachés antiguos de ConfiguracionSistema.

    Se ejecuta periódicamente para liberar memoria.
    """
    from apps.core.models import CacheConfiguracion

    try:
        # Eliminar cachés más antiguos de 7 días
        limite = timezone.now() - timedelta(days=7)

        eliminados = CacheConfiguracion.objects.filter(timestamp__lt=limite).delete()[0]

        return {
            "success": True,
            "registros_eliminados": eliminados,
            "timestamp": timezone.now().isoformat(),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
