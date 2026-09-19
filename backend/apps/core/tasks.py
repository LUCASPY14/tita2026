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
