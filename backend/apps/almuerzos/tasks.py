import logging
from datetime import date, timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

_MONTO_ALERTA_SALDO_ALMUERZO = 100_000


@shared_task(
    name="apps.almuerzos.tasks.cerrar_cuentas_mes_anterior",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def cerrar_cuentas_mes_anterior():
    """
    Resumen mensual de almuerzos del mes anterior — WhatsApp informativo a
    cada familia con cuántos almuerzos consumió y el total (calculado en
    vivo desde RegistroConsumoAlmuerzo, no de ninguna cuenta intermedia).

    Se ejecuta el día 1 de cada mes a las 05:00.

    Esto es puramente informativo: no cierra ni cobra nada — la deuda real
    vive en SaldoAlmuerzo y ya tiene sus propios avisos (avisar_deuda_almuerzo
    semanal a las familias, alertar_saldo_almuerzo_negativo diario a admin).
    """
    from django.db.models import Count, Sum
    from apps.almuerzos.models import RegistroConsumoAlmuerzo

    hoy = timezone.now().date()
    primer_dia_mes = date(hoy.year, hoy.month, 1)
    ultimo_dia_mes_ant = primer_dia_mes - timedelta(days=1)
    anio_ant, mes_ant = ultimo_dia_mes_ant.year, ultimo_dia_mes_ant.month

    logger.info("cerrar_cuentas_mes_anterior: resumen de %02d/%d", mes_ant, anio_ant)

    resumen_por_hijo = (
        RegistroConsumoAlmuerzo.objects.filter(
            fecha_consumo__year=anio_ant,
            fecha_consumo__month=mes_ant,
            estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
            ya_cobrado=True,
        )
        .values("hijo_id", "hijo__nombre", "hijo__apellido", "hijo__cliente_responsable")
        .annotate(cantidad=Count("id_registro_consumo"), monto=Sum("costo_almuerzo"))
    )

    from apps.clientes.models import Cliente
    from apps.notificaciones.services import whatsapp_cliente

    enviados = 0
    for fila in resumen_por_hijo:
        try:
            responsable = Cliente.objects.get(pk=fila["hijo__cliente_responsable"])
            nombre_hijo = f"{fila['hijo__nombre']} {fila['hijo__apellido']}"
            whatsapp_cliente(
                responsable,
                f"Resumen de almuerzos {mes_ant:02d}/{anio_ant} de "
                f"{nombre_hijo}: "
                f"{fila['cantidad']} almuerzo(s), "
                f"total Gs. {int(fila['monto'] or 0):,}."
            )
            enviados += 1
        except Exception:
            logger.warning(
                "No se pudo enviar WhatsApp de resumen para hijo=%s (%02d/%d)",
                fila["hijo_id"], mes_ant, anio_ant,
                exc_info=True,
            )

    logger.info(
        "cerrar_cuentas_mes_anterior: %02d/%d — %d resúmenes enviados",
        mes_ant, anio_ant, enviados,
    )

    # Notificación al admin con el resumen
    try:
        from django.conf import settings
        from apps.notificaciones.services import EmailService
        for _, admin_email in getattr(settings, "ADMINS", []):
            EmailService.enviar_simple(
                destinatario_email=admin_email,
                destinatario_nombre="Admin",
                asunto=f"[Cantina Tita] Resumen mensual almuerzos {mes_ant:02d}/{anio_ant}",
                cuerpo=(
                    f"Resumen mensual de almuerzos para {mes_ant:02d}/{anio_ant}.\n\n"
                    f"  Familias notificadas: {enviados}\n"
                ),
            )
    except Exception as exc:
        logger.warning("No se pudo enviar email de resumen: %s", exc)

    return {
        "mes": mes_ant,
        "anio": anio_ant,
        "enviados": enviados,
    }


@shared_task(
    name="apps.almuerzos.tasks.avisar_deuda_almuerzo",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def avisar_deuda_almuerzo():
    """
    Avisa a los padres cuyo saldo corriente de almuerzo está en negativo.
    Se ejecuta todos los viernes a las 08:00 — sin días de gracia, se avisa
    apenas hay deuda, sin importar hace cuánto quedó negativo.
    """
    from apps.almuerzos.models import SaldoAlmuerzo
    from apps.notificaciones.models import Notificacion

    saldos_deudores = SaldoAlmuerzo.objects.filter(
        saldo_actual__lt=0,
    ).select_related("hijo__cliente_responsable__usuario_portal")

    from apps.notificaciones.services import whatsapp_cliente
    creadas = 0
    for saldo in saldos_deudores:
        hijo = saldo.hijo
        deuda = -saldo.saldo_actual
        msg = (
            f"Saldo de almuerzo de {hijo.nombre_completo}: "
            f"Gs. {deuda:,.0f} en negativo. "
            f"Podés recargar desde el portal de padres o acercarte a la cantina."
        )

        try:
            usuario = hijo.cliente_responsable.usuario_portal
        except AttributeError:
            usuario = None

        if usuario:
            Notificacion.objects.create(
                usuario=usuario,
                tipo=Notificacion.Tipo.ALMUERZO,
                titulo="Saldo de almuerzo en negativo",
                mensaje=msg,
                destino=Notificacion.Destino.SISTEMA,
            )
            creadas += 1

        whatsapp_cliente(hijo.cliente_responsable, msg)

    logger.info("avisar_deuda_almuerzo: %d notificaciones creadas", creadas)
    return {"notificaciones_creadas": creadas}


@shared_task(
    name="apps.almuerzos.tasks.alertar_saldo_almuerzo_negativo",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def alertar_saldo_almuerzo_negativo():
    """
    Avisa a ADMIN cuando la deuda de saldo de almuerzo de un alumno supera
    _MONTO_ALERTA_SALDO_ALMUERZO. No deduplica entre corridas — mientras
    la deuda siga superando el umbral, vuelve a notificar cada día
    (mismo criterio que apps.clientes.tasks.alertar_saldo_negativo_prolongado).

    No reemplaza a avisar_deuda_almuerzo (aviso semanal a los padres por
    cualquier saldo negativo) — esta tarea es la visibilidad para admin.
    """
    from apps.almuerzos.models import SaldoAlmuerzo
    from apps.notificaciones.models import Notificacion
    from apps.usuarios.models import Usuario

    saldos_en_alerta = SaldoAlmuerzo.objects.filter(
        saldo_actual__lte=-_MONTO_ALERTA_SALDO_ALMUERZO,
    ).select_related("hijo__cliente_responsable")

    admins = list(Usuario.objects.filter(rol=Usuario.Rol.ADMIN, is_active=True))
    alertados = 0
    for saldo in saldos_en_alerta:
        hijo = saldo.hijo
        deuda = -saldo.saldo_actual
        msg = (
            f"Deuda de almuerzo de {hijo.nombre_completo}: "
            f"Gs. {deuda:,.0f} — supera el umbral de alerta "
            f"(Gs. {_MONTO_ALERTA_SALDO_ALMUERZO:,.0f})."
        )

        try:
            for admin in admins:
                Notificacion.objects.create(
                    usuario=admin,
                    tipo=Notificacion.Tipo.SISTEMA,
                    titulo=f"Deuda de almuerzo alta: {hijo.nombre_completo}",
                    mensaje=msg,
                    destino=Notificacion.Destino.SISTEMA,
                )
        except Exception as exc:
            logger.warning("No se pudo notificar admin para %s: %s", hijo, exc)

        alertados += 1

    logger.info(
        "alertar_saldo_almuerzo_negativo: %d alumnos con deuda >Gs.%d",
        alertados, _MONTO_ALERTA_SALDO_ALMUERZO,
    )
    return {"alertados": alertados}
