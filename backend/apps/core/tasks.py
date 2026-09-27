import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

# Deuda de cantina en una tarjeta a partir de la cual se avisa a los admins.
_MONTO_ALERTA_SALDO_TARJETA = 100_000


@shared_task(
    name="apps.core.tasks.crear_particion_anio_siguiente",
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=True,
)
def crear_particion_anio_siguiente():
    """
    Crea las particiones del año siguiente para tablas históricas particionadas.
    Se ejecuta automáticamente el 1 de diciembre de cada año (via Celery Beat).
    Equivalente a: python manage.py create_year_partition --year <año+1>
    """
    from django.core.management import call_command
    from io import StringIO

    siguiente = timezone.now().year + 1
    out = StringIO()
    try:
        call_command("create_year_partition", year=siguiente, stdout=out)
        resultado = out.getvalue()
        logger.info("crear_particion_anio_siguiente: año=%d\n%s", siguiente, resultado)
        return {"año": siguiente, "resultado": resultado}
    except Exception as exc:
        logger.error("crear_particion_anio_siguiente: fallo para año=%d: %s", siguiente, exc)
        raise


@shared_task(
    name="apps.core.tasks.expirar_recargas_pendientes",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def expirar_recargas_pendientes():
    """Expira cargas de saldo PENDIENTE con más de 24 horas sin confirmar."""
    from .models import CargaSaldo

    limite = timezone.now() - timedelta(hours=24)
    actualizadas = CargaSaldo.objects.filter(
        estado=CargaSaldo.Estado.PENDIENTE,
        fecha_carga__lt=limite,
    ).update(estado=CargaSaldo.Estado.RECHAZADA)

    logger.info("expirar_recargas_pendientes: %d cargas expiradas", actualizadas)
    return {"expiradas": actualizadas}


@shared_task(
    name="apps.core.tasks.alertar_saldo_tarjeta_negativo",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def alertar_saldo_tarjeta_negativo():
    """
    Avisa a ADMIN de tarjetas con deuda de cantina alta: desde
    _MONTO_ALERTA_SALDO_TARJETA, o desde el 80% de su tope si el tope es menor.
    Como el alerta de almuerzo, no deduplica: mientras siga por encima del
    umbral vuelve a avisar cada día.
    """
    from decimal import Decimal

    from apps.notificaciones.models import Notificacion
    from apps.usuarios.models import Usuario

    from .models import Tarjeta

    admins = list(Usuario.objects.filter(rol=Usuario.Rol.ADMIN, is_active=True))
    alertadas = 0
    for tarjeta in Tarjeta.objects.filter(saldo_actual__lt=0).select_related("hijo", "cliente_directo"):
        deuda = -tarjeta.saldo_actual
        tope = tarjeta.deuda_maxima
        umbral = Decimal(_MONTO_ALERTA_SALDO_TARJETA)
        if tope:
            umbral = min(umbral, tope * Decimal("0.8"))
        if deuda < umbral:
            continue

        titular = (
            tarjeta.hijo.nombre_completo if tarjeta.hijo_id
            else tarjeta.cliente_directo.nombre_completo if tarjeta.cliente_directo_id
            else tarjeta.nro_tarjeta
        )
        tope_txt = "sin tope" if tope is None else f"tope Gs. {tope:,.0f}"
        mensaje = f"Deuda de cantina de {titular} (tarjeta {tarjeta.nro_tarjeta}): Gs. {deuda:,.0f} ({tope_txt})."
        try:
            for admin in admins:
                Notificacion.objects.create(
                    usuario=admin,
                    tipo=Notificacion.Tipo.SISTEMA,
                    titulo=f"Deuda de cantina alta: {titular}",
                    mensaje=mensaje,
                    destino=Notificacion.Destino.SISTEMA,
                )
        except Exception as exc:
            logger.warning("No se pudo notificar deuda de tarjeta %s: %s", tarjeta.nro_tarjeta, exc)
        alertadas += 1

    logger.info("alertar_saldo_tarjeta_negativo: %d tarjetas en alerta", alertadas)
    return {"alertadas": alertadas}


@shared_task(
    name="apps.core.tasks.verificar_consistencia_saldos",
    autoretry_for=(Exception,),
    max_retries=2,
)
def verificar_consistencia_saldos():
    """
    Compara saldo_actual (Tarjeta y SaldoAlmuerzo) contra la suma real de sus
    movimientos. Con los triggers de sincronización (trg_sync_saldo_tarjeta,
    trg_sync_saldo_almuerzo) esto no debería divergir nunca desde un
    movimiento normal — esta tarea es la red de seguridad para el caso que
    los triggers no cubren: alguien (o algún código futuro) edita
    saldo_actual directo, sin pasar por un movimiento.

    No corrige nada solo — avisa a ADMINS por email para revisar a mano,
    igual que el aviso de tareas críticas en celery_app.py.
    """
    from decimal import Decimal
    from django.conf import settings
    from django.db.models import Case, DecimalField, F, Sum, When
    from django.db.models.functions import Coalesce

    from .models import Tarjeta
    from apps.almuerzos.models import SaldoAlmuerzo

    calculado_tarjeta = Coalesce(
        Sum(
            Case(
                When(movimientos__tipo="CONSUMO", then=-F("movimientos__monto")),
                default=F("movimientos__monto"),
                output_field=DecimalField(max_digits=12, decimal_places=0),
            )
        ),
        Decimal("0"),
    )
    desajustes_tarjeta = list(
        Tarjeta.objects
        .annotate(calculado=calculado_tarjeta)
        .exclude(saldo_actual=F("calculado"))
        .values_list("nro_tarjeta", "saldo_actual", "calculado")
    )

    calculado_almuerzo = Coalesce(Sum("movimientos__monto"), Decimal("0"))
    desajustes_almuerzo = list(
        SaldoAlmuerzo.objects
        .annotate(calculado=calculado_almuerzo)
        .exclude(saldo_actual=F("calculado"))
        .values_list("hijo_id", "saldo_actual", "calculado")
    )

    total = len(desajustes_tarjeta) + len(desajustes_almuerzo)
    logger.info(
        "verificar_consistencia_saldos: %d desajustes de tarjeta, %d de almuerzo",
        len(desajustes_tarjeta), len(desajustes_almuerzo),
    )

    if total:
        lineas = [
            f"  - Tarjeta {nro}: guardado Gs. {int(guardado):,} vs. calculado Gs. {int(calc):,}"
            for nro, guardado, calc in desajustes_tarjeta
        ] + [
            f"  - SaldoAlmuerzo (hijo_id={hijo_id}): guardado Gs. {int(guardado):,} vs. calculado Gs. {int(calc):,}"
            for hijo_id, guardado, calc in desajustes_almuerzo
        ]
        cuerpo = (
            f"Se encontraron {total} saldo(s) que no coinciden con la suma de sus movimientos.\n"
            "Esto no debería pasar con los triggers de sincronización activos — revisar a mano:\n\n"
            + "\n".join(lineas)
        )
        for _, admin_email in getattr(settings, "ADMINS", []):
            try:
                from apps.notificaciones.services import EmailService
                EmailService.enviar_simple(
                    destinatario_email=admin_email,
                    destinatario_nombre="Admin",
                    asunto=f"[Cantina Tita] {total} saldo(s) desincronizados",
                    cuerpo=cuerpo,
                )
            except Exception:
                logger.warning("No se pudo enviar alerta de saldos desincronizados", exc_info=True)

    return {"desajustes_tarjeta": len(desajustes_tarjeta), "desajustes_almuerzo": len(desajustes_almuerzo)}
