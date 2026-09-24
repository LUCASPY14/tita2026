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

    hoy = timezone.localdate()
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

    hoy = timezone.localdate()
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


# Si por algún motivo la tarea no corrió, no se da de baja "tarde" a un curso
# distinto (el de un año nuevo que ya ocupa el último grado).
_DIAS_MAX_BAJA_TARDIA = 30
_DIAS_ENTRE_AVISOS = 7


def _gs(n):
    return f"Gs. {abs(int(n)):,}"


def _texto_saldo(n):
    n = int(n or 0)
    if n > 0:
        return f"{_gs(n)} a favor"
    if n < 0:
        return f"{_gs(n)} en deuda"
    return "sin saldo"


def _saldos_del_alumno(hijo):
    """(saldo cantina, saldo almuerzo) del alumno; 0 si todavía no tiene registro."""
    from django.core.exceptions import ObjectDoesNotExist

    try:
        cantina = hijo.tarjeta.saldo_actual
    except ObjectDoesNotExist:
        cantina = 0
    try:
        almuerzo = hijo.saldo_almuerzo.saldo_actual
    except ObjectDoesNotExist:
        almuerzo = 0
    return cantina, almuerzo


def _notificar_staff(titulo, mensaje, roles=None):
    from apps.notificaciones.models import Notificacion
    from apps.usuarios.models import Usuario

    roles = roles or [Usuario.Rol.ADMIN]
    for usuario in Usuario.objects.filter(rol__in=roles, is_active=True):
        Notificacion.objects.create(
            usuario=usuario, tipo=Notificacion.Tipo.SISTEMA, titulo=titulo,
            mensaje=mensaje, destino=Notificacion.Destino.SISTEMA,
        )


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
    Da de baja a los alumnos del último curso una vez pasado el cierre del año
    lectivo configurado (por defecto 31/12), una sola vez por año. Corre todos
    los días a las 05:00: el calendario es configurable, no una fecha fija.

    No borra ni ajusta saldos: si quedan saldos o deudas pendientes, avisa a los
    administradores con el detalle (se resuelven en el cierre de cuentas).
    """
    from apps.clientes.models import Hijo, PromocionAlumno
    from apps.clientes.vigencia import obtener_calendario

    hoy = timezone.localdate()
    dados_de_baja = 0
    for anio in (hoy.year - 1, hoy.year):
        cal = obtener_calendario(anio)
        if hoy <= cal.fecha_cierre_lectivo:
            continue
        if cal.pk and cal.baja_ultimo_curso_aplicada:
            continue
        if (hoy - cal.fecha_cierre_lectivo).days > _DIAS_MAX_BAJA_TARDIA:
            logger.warning(
                "dar_baja_alumnos_ultimo_curso: el año %s cerró hace más de %d días y no se aplicó; se omite",
                anio, _DIAS_MAX_BAJA_TARDIA,
            )
            continue
        if cal.pk is None:
            cal.save()

        # Quien repite (o cambia de grado) según el borrador de promoción sigue activo.
        continuan = PromocionAlumno.objects.filter(
            promocion__anio=cal.anio,
            decision__in=[PromocionAlumno.Decision.REPITE, PromocionAlumno.Decision.CAMBIA],
        ).values("hijo_id")
        egresados = list(
            Hijo.objects.filter(activo=True, grado__es_ultimo=True)
            .exclude(pk__in=continuan)
            .select_related("tarjeta", "saldo_almuerzo")
        )
        ahora = timezone.now()
        Hijo.objects.filter(pk__in=[h.pk for h in egresados]).update(activo=False, fecha_baja=ahora)
        cal.baja_ultimo_curso_aplicada = True
        cal.save(update_fields=["baja_ultimo_curso_aplicada"])
        dados_de_baja += len(egresados)

        # Cada egresado necesita su expediente para resolver saldos y deudas.
        from apps.cierre_cuentas.services import CierreCuentaService
        for h in egresados:
            CierreCuentaService.abrir(h, cal.anio)

        pendientes = []
        for h in egresados:
            cantina, almuerzo = _saldos_del_alumno(h)
            if cantina or almuerzo:
                pendientes.append(
                    f"- {h.nombre_completo}: cantina {_texto_saldo(cantina)}, almuerzo {_texto_saldo(almuerzo)}"
                )
        if pendientes:
            _notificar_staff(
                f"Egresados {anio} con saldos por resolver ({len(pendientes)})",
                "Se dio de baja al último curso. Saldos pendientes:\n" + "\n".join(pendientes[:25])
                + (f"\n... y {len(pendientes) - 25} más" if len(pendientes) > 25 else ""),
            )

    logger.info("dar_baja_alumnos_ultimo_curso: %d alumnos dados de baja", dados_de_baja)
    return {"dados_de_baja": dados_de_baja}


@shared_task(
    name="apps.clientes.tasks.avisar_cierre_ultimo_curso",
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def avisar_cierre_ultimo_curso():
    """
    Desde la fecha de aviso (por defecto 01/10) y hasta el cierre, avisa cada
    semana los saldos y deudas de los alumnos del último curso:
    - a cada padre/responsable (notificación del portal y WhatsApp);
    - a administradores, supervisores, cajeros y cobradores, un resumen.
    Los alumnos siguen operando con normalidad hasta el cierre.
    """
    from apps.clientes.models import Hijo
    from apps.clientes.vigencia import obtener_calendario
    from apps.notificaciones.models import Notificacion
    from apps.notificaciones.services import whatsapp_cliente
    from apps.usuarios.models import Usuario

    hoy = timezone.localdate()
    cal = obtener_calendario(hoy.year)
    if not (cal.fecha_aviso_ultimo_curso <= hoy <= cal.fecha_cierre_lectivo):
        return {"avisados": 0, "motivo": "fuera del período de aviso"}
    # Desde la fecha de aviso el personal ya puede ver y resolver los saldos.
    from apps.cierre_cuentas.services import CierreCuentaService
    CierreCuentaService.abrir_masivo(cal.anio)

    if (hoy - cal.fecha_aviso_ultimo_curso).days % _DIAS_ENTRE_AVISOS != 0:
        return {"avisados": 0, "motivo": "no toca aviso hoy"}

    cierre = cal.fecha_cierre_lectivo.strftime("%d/%m/%Y")
    alumnos = (
        Hijo.objects.filter(activo=True, grado__es_ultimo=True)
        .select_related("grado", "tarjeta", "saldo_almuerzo", "cliente_responsable__usuario_portal")
    )
    avisados = 0
    deuda_total = a_favor_total = 0
    lineas = []
    for hijo in alumnos:
        cantina, almuerzo = _saldos_del_alumno(hijo)
        if not cantina and not almuerzo:
            continue
        for saldo in (cantina, almuerzo):
            if saldo < 0:
                deuda_total += -saldo
            else:
                a_favor_total += saldo
        lineas.append(
            f"- {hijo.nombre_completo}: cantina {_texto_saldo(cantina)}, almuerzo {_texto_saldo(almuerzo)}"
        )

        responsable = hijo.cliente_responsable
        mensaje = (
            f"Cierre de cuentas: {hijo.nombre_completo} cursa el último año y su tarjeta opera hasta el {cierre}. "
            f"Saldos hoy: cantina {_texto_saldo(cantina)}, almuerzo {_texto_saldo(almuerzo)}. "
            "Regularizá las deudas y consultá en administración por la devolución o el traspaso del saldo a favor."
        )
        try:
            usuario = responsable.usuario_portal
        except Exception:
            usuario = None
        if usuario:
            Notificacion.objects.create(
                usuario=usuario, tipo=Notificacion.Tipo.SISTEMA,
                titulo=f"Cierre de cuentas de {hijo.nombre}", mensaje=mensaje,
                destino=Notificacion.Destino.SISTEMA,
            )
        whatsapp_cliente(responsable, mensaje)
        avisados += 1

    if lineas:
        _notificar_staff(
            f"Último curso: {len(lineas)} alumnos con saldos por resolver",
            f"Cierre de cuentas el {cierre}. Deuda total {_gs(deuda_total)}, saldo a favor {_gs(a_favor_total)}.\n"
            + "\n".join(lineas[:25]) + (f"\n... y {len(lineas) - 25} más" if len(lineas) > 25 else ""),
            roles=[Usuario.Rol.ADMIN, Usuario.Rol.SUPERVISOR, Usuario.Rol.CAJERO, Usuario.Rol.COBRADOR],
        )

    logger.info("avisar_cierre_ultimo_curso: %d alumnos avisados", avisados)
    return {"avisados": avisados}


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
