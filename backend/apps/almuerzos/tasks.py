"""
Celery tasks para el módulo de Almuerzos
"""
from celery import shared_task
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@shared_task(name='apps.almuerzos.tasks.generar_cuentas_mensuales')
def generar_cuentas_mensuales():
    """
    Genera automáticamente las CuentasAlmuerzoMensual para el mes actual
    para todos los hijos con suscripción activa que aún no tengan cuenta.
    Se ejecuta el 1ro de cada mes.
    """
    from apps.almuerzos.models import SuscripcionesAlmuerzo, CuentasAlmuerzoMensual
    from apps.notificaciones.models import AlertasSistema

    hoy = timezone.now().date()
    anio = hoy.year
    mes = hoy.month

    suscripciones_activas = SuscripcionesAlmuerzo.objects.filter(
        estado='activo'
    ).select_related('id_hijo', 'id_plan')

    creadas = 0
    for suscripcion in suscripciones_activas:
        existe = CuentasAlmuerzoMensual.objects.filter(
            id_hijo=suscripcion.id_hijo,
            anio=anio,
            mes=mes,
        ).exists()
        if not existe:
            try:
                CuentasAlmuerzoMensual.objects.create(
                    id_hijo=suscripcion.id_hijo,
                    anio=anio,
                    mes=mes,
                    monto_total=Decimal('0.00'),
                    monto_pagado=Decimal('0.00'),
                    estado='pendiente',
                )
                creadas += 1
            except Exception as e:
                logger.warning(f"Error creando cuenta almuerzo para hijo {suscripcion.id_hijo_id}: {e}")

    logger.info(f"generar_cuentas_mensuales: {creadas} cuentas creadas para {mes}/{anio}")
    return {'creadas': creadas, 'mes': mes, 'anio': anio}


@shared_task(name='apps.almuerzos.tasks.alertar_cuentas_vencidas')
def alertar_cuentas_vencidas():
    """
    Genera alertas para CuentasAlmuerzoMensual con estado 'pendiente' de
    meses anteriores (deuda vencida). Se ejecuta el día 10 de cada mes.
    """
    from apps.almuerzos.models import CuentasAlmuerzoMensual
    from apps.notificaciones.models import AlertasSistema

    hoy = timezone.now().date()
    cuentas_vencidas = CuentasAlmuerzoMensual.objects.filter(
        estado='pendiente',
    ).exclude(
        anio=hoy.year,
        mes=hoy.month,
    ).select_related('id_hijo')

    alertas = 0
    for cuenta in cuentas_vencidas:
        ya_existe = AlertasSistema.objects.filter(
            tipo_alerta='deuda_almuerzo',
            referencia_id=cuenta.pk,
        ).exists()
        if not ya_existe:
            try:
                AlertasSistema.objects.create(
                    tipo_alerta='deuda_almuerzo',
                    nivel='alta',
                    titulo=f"Deuda almuerzos pendiente — {cuenta.mes}/{cuenta.anio}",
                    descripcion=(
                        f"Hijo: {cuenta.id_hijo}\n"
                        f"Monto: {cuenta.monto_total}\n"
                        f"Saldo: {cuenta.monto_total - cuenta.monto_pagado}"
                    ),
                    referencia_id=cuenta.pk,
                    leida=False,
                )
                alertas += 1
            except Exception as e:
                logger.warning(f"Error creando alerta para cuenta {cuenta.pk}: {e}")

    logger.info(f"alertar_cuentas_vencidas: {alertas} alertas generadas")
    return {'alertas': alertas}
