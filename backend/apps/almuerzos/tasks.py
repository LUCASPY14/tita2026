import calendar
import logging
from datetime import date

from celery import shared_task
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="apps.almuerzos.tasks.cerrar_cuentas_mes_anterior")
def cerrar_cuentas_mes_anterior():
    """
    Cierre mensual de cuentas de almuerzo del mes anterior.

    Se ejecuta el día 1 de cada mes a las 05:00 (antes de generar_cuentas_mensuales).

    Operación:
      1. Calcula el mes anterior.
      2. Para cada CuentaAlmuerzoMensual del mes anterior:
         - Cuenta los RegistroConsumoAlmuerzo validados y aún no marcados en cuenta.
         - Actualiza cantidad_almuerzos + monto_total usando el costo registrado.
         - Marca esos registros como marcado_en_cuenta=True.
         - Anula la cuenta si no hubo ningún consumo (0 almuerzos).
      3. Envía notificación admin con el resumen del cierre.
    """
    from django.db.models import Count, Sum
    from apps.almuerzos.models import (
        CuentaAlmuerzoMensual, RegistroConsumoAlmuerzo
    )

    hoy = timezone.now().date()
    # Mes anterior
    primer_dia_mes = date(hoy.year, hoy.month, 1)
    ultimo_dia_mes_ant = primer_dia_mes - timezone.timedelta(days=1)
    anio_ant, mes_ant = ultimo_dia_mes_ant.year, ultimo_dia_mes_ant.month

    logger.info("cerrar_cuentas_mes_anterior: cerrando %02d/%d", mes_ant, anio_ant)

    cuentas = CuentaAlmuerzoMensual.objects.filter(
        anio=anio_ant, mes=mes_ant
    ).exclude(
        estado=CuentaAlmuerzoMensual.Estado.ANULADO
    ).select_related("hijo")

    cerradas = anuladas = actualizadas = 0

    with transaction.atomic():
        for cuenta in cuentas:
            # Registros pendientes de marcar para este hijo en el mes
            registros_qs = RegistroConsumoAlmuerzo.objects.filter(
                hijo=cuenta.hijo,
                fecha_consumo__year=anio_ant,
                fecha_consumo__month=mes_ant,
                ya_cobrado=True,
                marcado_en_cuenta=False,
                estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
            )

            totales = registros_qs.aggregate(
                cantidad=Count("id"),
                monto=Sum("costo_almuerzo"),
            )
            cantidad = totales["cantidad"] or 0
            monto = totales["monto"] or 0

            if cantidad == 0 and cuenta.cantidad_almuerzos == 0:
                cuenta.estado = CuentaAlmuerzoMensual.Estado.ANULADO
                cuenta.observaciones = (
                    "Anulada automáticamente en cierre mensual: sin consumos registrados."
                )
                cuenta.save(update_fields=["estado", "observaciones"])
                anuladas += 1
                continue

            # Actualizar totales acumulados
            cuenta.cantidad_almuerzos = cuenta.cantidad_almuerzos + cantidad
            cuenta.monto_total = cuenta.monto_total + monto
            cuenta._calcular_estado()
            cuenta.save(update_fields=["cantidad_almuerzos", "monto_total", "estado", "fecha_pago"])

            # Marcar registros como incorporados a la cuenta
            registros_qs.update(marcado_en_cuenta=True)
            actualizadas += 1

    cerradas = actualizadas + anuladas
    logger.info(
        "cerrar_cuentas_mes_anterior: %02d/%d — %d actualizadas, %d anuladas, %d total",
        mes_ant, anio_ant, actualizadas, anuladas, cerradas,
    )

    # Notificación al admin con el resumen
    try:
        from django.conf import settings
        from apps.notificaciones.services import EmailService
        for _, admin_email in getattr(settings, "ADMINS", []):
            EmailService.enviar_simple(
                destinatario_email=admin_email,
                destinatario_nombre="Admin",
                asunto=f"[Cantina Tita] Cierre mensual almuerzos {mes_ant:02d}/{anio_ant}",
                cuerpo=(
                    f"Cierre mensual completado para {mes_ant:02d}/{anio_ant}.\n\n"
                    f"  Cuentas actualizadas: {actualizadas}\n"
                    f"  Cuentas anuladas (sin consumo): {anuladas}\n"
                    f"  Total procesadas: {cerradas}\n"
                ),
            )
    except Exception as exc:
        logger.warning("No se pudo enviar email de cierre: %s", exc)

    return {
        "mes": mes_ant,
        "anio": anio_ant,
        "actualizadas": actualizadas,
        "anuladas": anuladas,
    }


@shared_task(name="apps.almuerzos.tasks.generar_cuentas_mensuales")
def generar_cuentas_mensuales():
    """
    Crea CuentaAlmuerzoMensual para el mes actual para cada hijo
    con suscripción activa que no tenga cuenta aún.
    Se ejecuta el día 1 de cada mes a las 06:00.
    """
    import calendar
    from datetime import date
    from django.db import models as db_models
    from apps.almuerzos.models import SuscripcionAlmuerzo, CuentaAlmuerzoMensual

    hoy = timezone.now().date()
    anio, mes = hoy.year, hoy.month
    primer_dia = date(anio, mes, 1)
    ultimo_dia = date(anio, mes, calendar.monthrange(anio, mes)[1])

    suscripciones = SuscripcionAlmuerzo.objects.filter(
        estado=SuscripcionAlmuerzo.Estado.ACTIVA,
        fecha_inicio__lte=ultimo_dia,
    ).filter(
        db_models.Q(fecha_fin__isnull=True) | db_models.Q(fecha_fin__gte=primer_dia)
    ).select_related("hijo")

    creadas = 0
    for suscripcion in suscripciones:
        _, fue_creada = CuentaAlmuerzoMensual.objects.get_or_create(
            hijo=suscripcion.hijo,
            anio=anio,
            mes=mes,
            defaults={
                "cantidad_almuerzos": 0,
                "monto_total": 0,
                "monto_pagado": 0,
                "forma_cobro": CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
                "estado": CuentaAlmuerzoMensual.Estado.PENDIENTE,
            },
        )
        if fue_creada:
            creadas += 1

    logger.info(
        "generar_cuentas_mensuales: %d cuentas creadas para %d/%d",
        creadas, mes, anio,
    )
    return {"cuentas_creadas": creadas, "mes": mes, "anio": anio}


@shared_task(name="apps.almuerzos.tasks.alertar_cuentas_vencidas")
def alertar_cuentas_vencidas():
    """
    Genera notificaciones para cuentas de almuerzo de meses anteriores
    que aún no estén pagadas.
    Se ejecuta el día 10 de cada mes a las 08:00.
    """
    from apps.almuerzos.models import CuentaAlmuerzoMensual
    from apps.notificaciones.models import Notificacion

    hoy = timezone.now().date()
    anio_actual, mes_actual = hoy.year, hoy.month

    cuentas_pendientes = CuentaAlmuerzoMensual.objects.filter(
        estado__in=[
            CuentaAlmuerzoMensual.Estado.PENDIENTE,
            CuentaAlmuerzoMensual.Estado.PARCIAL,
        ],
    ).exclude(
        anio=anio_actual, mes=mes_actual,
    ).select_related(
        "hijo__cliente_responsable__usuario_portal"
    )

    creadas = 0
    for cuenta in cuentas_pendientes:
        try:
            usuario = cuenta.hijo.cliente_responsable.usuario_portal
        except AttributeError:
            continue
        if not usuario:
            continue

        saldo_pendiente = cuenta.monto_total - cuenta.monto_pagado
        Notificacion.objects.create(
            usuario=usuario,
            tipo=Notificacion.Tipo.ALMUERZO,
            titulo="Cuenta de almuerzo pendiente de pago",
            mensaje=(
                f"La cuenta de almuerzo de {cuenta.hijo.nombre_completo} "
                f"correspondiente a {cuenta.mes:02d}/{cuenta.anio} "
                f"tiene un saldo pendiente de Gs. {saldo_pendiente:,.0f}."
            ),
            destino=Notificacion.Destino.SISTEMA,
        )
        creadas += 1

    logger.info("alertar_cuentas_vencidas: %d notificaciones creadas", creadas)
    return {"notificaciones_creadas": creadas}
