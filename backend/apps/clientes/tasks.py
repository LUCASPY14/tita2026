import logging
from datetime import timedelta

from celery import shared_task
from django.db.models import DateField, DecimalField, OuterRef, Subquery
from django.utils import timezone

logger = logging.getLogger(__name__)

_DIAS_DEUDA_PROLONGADA = 7


@shared_task(
    name="apps.clientes.tasks.alertar_saldo_negativo_prolongado",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def alertar_saldo_negativo_prolongado():
    """
    Detecta clientes activos con deuda en cuenta corriente sin movimientos
    en los últimos DIAS_DEUDA_PROLONGADA días y genera notificaciones.

    Criterio: el último movimiento de la cuenta tiene saldo_resultante > 0
    y su fecha es anterior al umbral de días — la deuda existe y no hubo
    ningún pago ni crédito reciente.

    Corre diario a las 09:15.
    """
    from apps.clientes.models import Cliente, CuentaCorrienteCliente
    from apps.notificaciones.models import Notificacion
    from apps.notificaciones.services import whatsapp_cliente
    from apps.usuarios.models import Usuario

    hoy = timezone.now().date()
    fecha_corte = hoy - timedelta(days=_DIAS_DEUDA_PROLONGADA)

    ultimo = CuentaCorrienteCliente.objects.filter(
        cliente=OuterRef("pk")
    ).order_by("-id_movimiento_cc")

    clientes_en_deuda = (
        Cliente.objects.filter(activo=True)
        .annotate(
            saldo_cc=Subquery(
                ultimo.values("saldo_resultante")[:1],
                output_field=DecimalField(),
            ),
            fecha_ultimo_mov=Subquery(
                ultimo.values("fecha")[:1],
                output_field=DateField(),
            ),
        )
        .filter(
            saldo_cc__gt=0,
            fecha_ultimo_mov__lte=fecha_corte,
        )
    )

    alertados = 0
    for cliente in clientes_en_deuda:
        fecha_mov = cliente.fecha_ultimo_mov
        if hasattr(fecha_mov, "date"):
            fecha_mov = fecha_mov.date()
        dias = (hoy - fecha_mov).days
        monto = int(cliente.saldo_cc)
        msg = (
            f"Deuda en cuenta corriente de {cliente.nombre_completo}: "
            f"Gs. {monto:,} pendiente hace {dias} días. "
            f"Acercate a la cantina para regularizar."
        )

        # Notificación en sistema para los admins
        try:
            for admin in Usuario.objects.filter(rol=Usuario.Rol.ADMIN, is_active=True):
                Notificacion.objects.create(
                    usuario=admin,
                    tipo=Notificacion.Tipo.SISTEMA,
                    titulo=f"Deuda prolongada: {cliente.nombre_completo}",
                    mensaje=msg,
                    destino=Notificacion.Destino.SISTEMA,
                )
        except Exception as exc:
            logger.warning("No se pudo notificar admin para %s: %s", cliente, exc)

        # Notificación al usuario del portal si existe
        try:
            usuario_portal = cliente.usuario_portal
            Notificacion.objects.create(
                usuario=usuario_portal,
                tipo=Notificacion.Tipo.VENTA_DEUDA,
                titulo="Deuda pendiente en la cantina",
                mensaje=msg,
                destino=Notificacion.Destino.SISTEMA,
            )
        except Exception:
            pass  # Cliente sin usuario portal — normal

        # WhatsApp (silencioso si NOTIFICACIONES_ACTIVAS=False)
        try:
            whatsapp_cliente(cliente, msg)
        except Exception as exc:
            logger.warning("No se pudo enviar WhatsApp a %s: %s", cliente, exc)

        alertados += 1

    logger.info(
        "alertar_saldo_negativo_prolongado: %d clientes con deuda >%d días",
        alertados, _DIAS_DEUDA_PROLONGADA,
    )
    return {"clientes_alertados": alertados, "dias_umbral": _DIAS_DEUDA_PROLONGADA}


@shared_task(
    name="apps.clientes.tasks.resumen_mensual_deuda_clientes",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def resumen_mensual_deuda_clientes():
    """
    El día 5 de cada mes a las 08:30 envía un email a los ADMINS con
    el listado de clientes que tienen saldo positivo (deuda) en cuenta corriente.
    """
    from django.conf import settings

    from apps.clientes.models import Cliente, CuentaCorrienteCliente
    from apps.notificaciones.services import EmailService

    ultimo = CuentaCorrienteCliente.objects.filter(
        cliente=OuterRef("pk")
    ).order_by("-id_movimiento_cc")

    clientes_con_deuda = (
        Cliente.objects.filter(activo=True)
        .annotate(
            saldo_cc=Subquery(
                ultimo.values("saldo_resultante")[:1],
                output_field=DecimalField(),
            ),
        )
        .filter(saldo_cc__gt=0)
        .order_by("-saldo_cc")
    )

    total = clientes_con_deuda.count()
    if total == 0:
        logger.info("resumen_mensual_deuda_clientes: sin deudas pendientes")
        return {"clientes_con_deuda": 0}

    monto_total = sum(int(c.saldo_cc) for c in clientes_con_deuda)

    lineas = "\n".join(
        f"  - {c.nombre_completo} ({c.ruc_ci}): Gs. {int(c.saldo_cc):,}"
        for c in clientes_con_deuda
    )

    hoy = timezone.now().date()
    cuerpo = (
        f"Resumen de deudas en cuenta corriente al {hoy:%d/%m/%Y}.\n\n"
        f"Total clientes con deuda: {total}\n"
        f"Monto total adeudado: Gs. {monto_total:,}\n\n"
        f"Detalle:\n{lineas}\n"
    )

    enviados = 0
    for _, admin_email in getattr(settings, "ADMINS", []):
        try:
            EmailService.enviar_simple(
                destinatario_email=admin_email,
                destinatario_nombre="Admin",
                asunto=f"[Cantina Tita] Deudas en cuenta corriente — {hoy:%m/%Y}",
                cuerpo=cuerpo,
            )
            enviados += 1
        except Exception as exc:
            logger.warning("No se pudo enviar email a %s: %s", admin_email, exc)

    logger.info(
        "resumen_mensual_deuda_clientes: %d clientes, Gs. %d total, %d emails enviados",
        total, monto_total, enviados,
    )
    return {"clientes_con_deuda": total, "monto_total": monto_total, "emails_enviados": enviados}


_DIAS_GRACIA_PURGA = 365


@shared_task(
    name="apps.clientes.tasks.dar_baja_alumnos_ultimo_curso",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def dar_baja_alumnos_ultimo_curso():
    """
    Da de baja automáticamente a los alumnos del último grado/curso al
    finalizar el año lectivo. Corre el 20 de diciembre a las 05:00.
    """
    from apps.clientes.models import Hijo

    ahora = timezone.now()
    total = Hijo.objects.filter(activo=True, grado__es_ultimo=True).update(
        activo=False, fecha_baja=ahora,
    )
    logger.info("dar_baja_alumnos_ultimo_curso: %d alumnos dados de baja", total)
    return {"dados_de_baja": total}


@shared_task(
    name="apps.clientes.tasks.marcar_alumnos_pendientes_purga",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def marcar_alumnos_pendientes_purga():
    """
    Detecta alumnos dados de baja hace más de un año y los marca como
    pendientes de purga de datos sensibles, notificando a los ADMIN.
    La purga en sí requiere aprobación manual (HijoViewSet.aprobar_purga)
    — esta tarea nunca borra ni anonimiza datos por su cuenta.

    Corre el día 1 de cada mes a las 07:00.
    """
    from apps.clientes.models import Hijo
    from apps.notificaciones.models import Notificacion
    from apps.usuarios.models import Usuario

    corte = timezone.now() - timedelta(days=_DIAS_GRACIA_PURGA)
    candidatos = Hijo.objects.filter(
        activo=False,
        fecha_baja__lte=corte,
        datos_purgados=False,
        purga_solicitada_en__isnull=True,
    )

    if not candidatos.exists():
        logger.info("marcar_alumnos_pendientes_purga: sin alumnos elegibles")
        return {"marcados": 0}

    admins = list(Usuario.objects.filter(rol=Usuario.Rol.ADMIN, is_active=True))
    if not admins:
        logger.warning("marcar_alumnos_pendientes_purga: no hay usuarios ADMIN activos")

    marcados = 0
    for hijo in candidatos:
        hijo.purga_solicitada_en = timezone.now()
        hijo.save(update_fields=["purga_solicitada_en"])
        for admin in admins:
            Notificacion.objects.create(
                usuario=admin,
                tipo=Notificacion.Tipo.SISTEMA,
                titulo="Alumno pendiente de purga de datos",
                mensaje=(
                    f"{hijo.nombre_completo} fue dado de baja el "
                    f"{hijo.fecha_baja.strftime('%d/%m/%Y')} (hace más de un año). "
                    f"Revisar y aprobar la purga de sus datos sensibles."
                ),
                destino=Notificacion.Destino.SISTEMA,
            )
        marcados += 1

    logger.info("marcar_alumnos_pendientes_purga: %d alumnos marcados", marcados)
    return {"marcados": marcados}
