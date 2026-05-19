import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name="apps.almuerzos.tasks.generar_cuentas_mensuales")
def generar_cuentas_mensuales():
    """
    Crea CuentaAlmuerzoMensual para el mes actual para cada hijo
    con suscripción activa que no tenga cuenta aún.
    Se ejecuta el día 1 de cada mes a las 06:00.
    """
    from apps.almuerzos.models import SuscripcionAlmuerzo, CuentaAlmuerzoMensual

    hoy = timezone.now().date()
    anio, mes = hoy.year, hoy.month

    suscripciones = SuscripcionAlmuerzo.objects.filter(
        estado=SuscripcionAlmuerzo.Estado.ACTIVA,
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

        saldo_pendiente = int(cuenta.monto_total - cuenta.monto_pagado)
        Notificacion.objects.create(
            usuario=usuario,
            tipo=Notificacion.Tipo.ALMUERZO,
            titulo="Cuenta de almuerzo pendiente de pago",
            mensaje=(
                f"La cuenta de almuerzo de {cuenta.hijo.nombre_completo} "
                f"correspondiente a {cuenta.mes}/{cuenta.anio} "
                f"tiene un saldo pendiente de Gs. {saldo_pendiente:,}."
            ),
            destino=Notificacion.Destino.SISTEMA,
        )
        creadas += 1

    logger.info("alertar_cuentas_vencidas: %d notificaciones creadas", creadas)
    return {"notificaciones_creadas": creadas}
