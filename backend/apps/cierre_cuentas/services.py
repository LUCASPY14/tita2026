"""
Servicio de cierre de cuentas de egresados.

Reglas de negocio (acordadas con la administración):

| Resolución            | Solicita                          | Autoriza                 |
|-----------------------|-----------------------------------|--------------------------|
| Cobro de deuda        | ADMIN, SUPERVISOR, CAJERO, COBRADOR | (ingreso: sin aprobación) |
| Traspaso a hermano    | ADMIN, SUPERVISOR                 | el mismo                 |
| Compensación          | ADMIN, SUPERVISOR                 | el mismo                 |
| Traslado a cta. cte.  | ADMIN, SUPERVISOR                 | el mismo                 |
| Devolución            | ADMIN, SUPERVISOR                 | solo ADMIN               |
| Condonación           | ADMIN, SUPERVISOR                 | solo ADMIN               |

Si la solicita un ADMIN, la decisión es suya y se ejecuta al momento. Si la solicita
un SUPERVISOR queda pendiente hasta que un ADMIN la apruebe o rechace.

Toda resolución ejecutada deja movimientos en el libro mayor (ajuste con signo en la
tarjeta / en el saldo de almuerzo), egreso o ingreso de caja cuando hay dinero, y
auditoría. Los saldos nunca se editan directamente.
"""
import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.usuarios.auditoria import registrar_auditoria
from common.permissions import exigir_rol
from common.utils.medios_pago import resolver_medio_pago

from .models import CierreCuentaAlumno, ResolucionSaldo

logger = logging.getLogger(__name__)

Tipo = ResolucionSaldo.Tipo
Bolsillo = ResolucionSaldo.Bolsillo

_PERSONAL_COBRO = {"ADMIN", "SUPERVISOR", "CAJERO", "COBRADOR"}
_AUTORIZADORES = {"ADMIN", "SUPERVISOR"}

QUIEN_SOLICITA = {
    Tipo.COBRO: _PERSONAL_COBRO,
    Tipo.TRASPASO_HERMANO: _AUTORIZADORES,
    Tipo.COMPENSACION: _AUTORIZADORES,
    Tipo.TRASLADO_CC: _AUTORIZADORES,
    Tipo.DEVOLUCION: _AUTORIZADORES,
    Tipo.CONDONACION: _AUTORIZADORES,
}
REQUIEREN_ADMIN = {Tipo.DEVOLUCION, Tipo.CONDONACION}

METODOS_COBRO = ("EFECTIVO", "POS DEBITO", "POS CREDITO", "TRANSFERENCIA")
METODOS_DEVOLUCION = ("EFECTIVO", "TRANSFERENCIA")
_METODOS_CON_CAJA = ("EFECTIVO", "POS DEBITO", "POS CREDITO")

ADVERTENCIA_SIN_CAJA = (
    "El cobro se registró, pero no tenés una caja abierta: el ingreso no quedó "
    "registrado en caja."
)


def _gs(n):
    return f"Gs. {int(n):,}"


def _cierre_caja_abierto(usuario):
    from apps.contabilidad.models import CierreCaja

    return CierreCaja.objects.filter(
        empleado=usuario, estado=CierreCaja.Estado.ABIERTO,
    ).select_related("caja").first()


class CierreCuentaService:

    # ── Saldos ───────────────────────────────────────────────────────────────

    @staticmethod
    def saldos(hijo):
        """(saldo de cantina, saldo de almuerzo) vigentes; 0 si no tiene registro."""
        from apps.almuerzos.models import SaldoAlmuerzo
        from apps.core.models import Tarjeta

        tarjeta = Tarjeta.objects.filter(hijo=hijo).first()
        saldo_almuerzo = SaldoAlmuerzo.objects.filter(hijo=hijo).first()
        return (
            tarjeta.saldo_actual if tarjeta else Decimal("0"),
            saldo_almuerzo.saldo_actual if saldo_almuerzo else Decimal("0"),
        )

    @staticmethod
    def _saldo_bolsillo(hijo, bolsillo, bloquear=False):
        """Saldo actual del bolsillo; con `bloquear` toma el lock de la fila."""
        from apps.almuerzos.models import SaldoAlmuerzo
        from apps.core.models import Tarjeta

        if bolsillo == Bolsillo.CANTINA:
            qs = Tarjeta.objects.select_for_update() if bloquear else Tarjeta.objects
            tarjeta = qs.filter(hijo=hijo).first()
            if tarjeta is None:
                raise ValidationError({"error": f"{hijo.nombre_completo} no tiene tarjeta de cantina."})
            return tarjeta.saldo_actual
        SaldoAlmuerzo.objects.get_or_create(hijo=hijo)
        qs = SaldoAlmuerzo.objects.select_for_update() if bloquear else SaldoAlmuerzo.objects
        return qs.get(hijo=hijo).saldo_actual

    # ── Apertura ─────────────────────────────────────────────────────────────

    @staticmethod
    def abrir(hijo, anio=None, usuario=None):
        """Abre (o devuelve) el expediente de cierre del alumno para el año."""
        anio = anio or timezone.localdate().year
        cantina, almuerzo = CierreCuentaService.saldos(hijo)
        cierre, creado = CierreCuentaAlumno.objects.get_or_create(
            hijo=hijo, anio=anio,
            defaults={
                "saldo_cantina_inicial": cantina,
                "saldo_almuerzo_inicial": almuerzo,
                "abierto_por": usuario,
                # Sin saldos no hay nada que resolver.
                "estado": (
                    CierreCuentaAlumno.Estado.RESUELTO if not cantina and not almuerzo
                    else CierreCuentaAlumno.Estado.ABIERTO
                ),
                "fecha_cierre": timezone.now() if not cantina and not almuerzo else None,
            },
        )
        if creado:
            registrar_auditoria(
                usuario=usuario, operacion="CIERRE_CUENTA_ABRIR", tabla="cierre_cuentas_cierrecuentaalumno",
                id_registro=cierre.pk,
                descripcion=(
                    f"Cierre {anio} de {hijo.nombre_completo}: cantina {_gs(cantina)}, "
                    f"almuerzo {_gs(almuerzo)}"
                ),
            )
        return cierre, creado

    @staticmethod
    def abrir_masivo(anio=None, usuario=None):
        """Abre el expediente de todos los alumnos del último curso (activos) y de los
        dados de baja en el año. Es idempotente."""
        from apps.clientes.models import Hijo

        anio = anio or timezone.localdate().year
        alumnos = Hijo.objects.filter(
            Q(activo=True, grado__es_ultimo=True) | Q(activo=False, fecha_baja__year=anio)
        ).select_related("tarjeta", "saldo_almuerzo")
        creados = existentes = 0
        for hijo in alumnos:
            _, creado = CierreCuentaService.abrir(hijo, anio, usuario)
            creados += creado
            existentes += not creado
        return {"anio": anio, "creados": creados, "existentes": existentes}

    # ── Resoluciones ─────────────────────────────────────────────────────────

    @staticmethod
    def registrar_resolucion(
        *, cierre, tipo, bolsillo_origen, monto, usuario,
        bolsillo_destino="", hijo_destino=None, metodo_pago="", referencia="", motivo="",
    ):
        """Crea la resolución. Devuelve (resolucion, advertencia).

        Se ejecuta al momento salvo devolución/condonación pedidas por un
        SUPERVISOR, que quedan pendientes de un ADMIN.
        """
        if tipo not in Tipo.values:
            raise ValidationError({"tipo": "Tipo de resolución inválido."})
        exigir_rol(
            usuario, QUIEN_SOLICITA[tipo],
            "No tenés permiso para registrar este tipo de resolución.",
        )
        if cierre.estado == CierreCuentaAlumno.Estado.CERRADO_CON_SALDO:
            raise ValidationError({"error": "El cierre de cuenta ya fue cerrado."})
        if bolsillo_origen not in Bolsillo.values:
            raise ValidationError({"bolsillo_origen": "Bolsillo inválido."})
        monto = Decimal(monto)
        if monto <= 0 or monto != monto.to_integral_value():
            raise ValidationError({"monto": "El monto debe ser un entero mayor a cero."})

        res = ResolucionSaldo(
            cierre=cierre, tipo=tipo, bolsillo_origen=bolsillo_origen,
            bolsillo_destino=bolsillo_destino or "", hijo_destino=hijo_destino,
            monto=monto, metodo_pago=(metodo_pago or "").upper(), referencia=referencia or "",
            motivo=motivo or "", solicitado_por=usuario,
        )
        with transaction.atomic():
            CierreCuentaService._validar(res, bloquear=False)
            res.save()

        pide_admin = tipo in REQUIEREN_ADMIN and usuario.rol != "ADMIN"
        registrar_auditoria(
            usuario=usuario, operacion=f"CIERRE_CUENTA_{tipo}_SOLICITADA",
            tabla="cierre_cuentas_resolucionsaldo", id_registro=res.pk,
            descripcion=f"{res.get_tipo_display()} {_gs(monto)} de {cierre.hijo.nombre_completo} ({bolsillo_origen})",
        )
        if pide_admin:
            CierreCuentaService._notificar_admins_pendiente(res)
            return res, None
        advertencia = CierreCuentaService._ejecutar(res, usuario)
        res.refresh_from_db()
        return res, advertencia

    @staticmethod
    def aprobar(resolucion, usuario):
        exigir_rol(usuario, {"ADMIN"}, "Solo un administrador puede aprobar esta resolución.")
        advertencia = CierreCuentaService._ejecutar(resolucion, usuario)
        resolucion.refresh_from_db()
        return resolucion, advertencia

    @staticmethod
    def rechazar(resolucion, usuario, motivo):
        exigir_rol(usuario, {"ADMIN"}, "Solo un administrador puede rechazar esta resolución.")
        if not (motivo or "").strip():
            raise ValidationError({"motivo": "Indicá el motivo del rechazo."})
        with transaction.atomic():
            res = ResolucionSaldo.objects.select_for_update().get(pk=resolucion.pk)
            if res.estado != ResolucionSaldo.Estado.SOLICITADA:
                raise ValidationError({"error": "La resolución ya fue procesada."})
            res.estado = ResolucionSaldo.Estado.RECHAZADA
            res.motivo_rechazo = motivo.strip()
            res.decidido_por = usuario
            res.fecha_decision = timezone.now()
            res.save()
        registrar_auditoria(
            usuario=usuario, operacion=f"CIERRE_CUENTA_{res.tipo}_RECHAZADA",
            tabla="cierre_cuentas_resolucionsaldo", id_registro=res.pk,
            descripcion=f"Rechazada: {motivo.strip()}",
        )
        CierreCuentaService._notificar_solicitante_rechazo(res)
        return res

    @staticmethod
    def cerrar_con_saldo(cierre, usuario, motivo):
        """Cierra el expediente dejando saldos pendientes registrados (solo ADMIN).
        No bloquea la baja: la deuda o el saldo quedan reportados."""
        exigir_rol(usuario, {"ADMIN"}, "Solo un administrador puede cerrar un expediente con saldo pendiente.")
        if not (motivo or "").strip():
            raise ValidationError({"motivo": "Indicá el motivo del cierre."})
        with transaction.atomic():
            cierre = CierreCuentaAlumno.objects.select_for_update().get(pk=cierre.pk)
            if cierre.estado in (
                CierreCuentaAlumno.Estado.CERRADO_CON_SALDO, CierreCuentaAlumno.Estado.RESUELTO,
            ):
                raise ValidationError({"error": "El expediente ya está cerrado."})
            if cierre.resoluciones.filter(estado=ResolucionSaldo.Estado.SOLICITADA).exists():
                raise ValidationError({"error": "Hay resoluciones pendientes de aprobación."})
            cantina, almuerzo = CierreCuentaService.saldos(cierre.hijo)
            cierre.estado = CierreCuentaAlumno.Estado.CERRADO_CON_SALDO
            cierre.fecha_cierre = timezone.now()
            cierre.cerrado_por = usuario
            cierre.motivo_cierre = motivo.strip()
            cierre.saldo_cantina_final = cantina
            cierre.saldo_almuerzo_final = almuerzo
            cierre.save()
        registrar_auditoria(
            usuario=usuario, operacion="CIERRE_CUENTA_CERRAR_CON_SALDO",
            tabla="cierre_cuentas_cierrecuentaalumno", id_registro=cierre.pk,
            descripcion=(
                f"{cierre.hijo.nombre_completo}: cantina {_gs(cantina)}, almuerzo {_gs(almuerzo)}. "
                f"Motivo: {motivo.strip()}"
            ),
        )
        return cierre

    # ── Validación ───────────────────────────────────────────────────────────

    @staticmethod
    def _validar(res, bloquear):
        """Valida la resolución contra los saldos actuales (se repite al ejecutar,
        con las filas bloqueadas, porque los saldos pueden haber cambiado)."""
        hijo = res.cierre.hijo
        tipo = res.tipo
        saldo_origen = CierreCuentaService._saldo_bolsillo(hijo, res.bolsillo_origen, bloquear)

        if tipo in (Tipo.DEVOLUCION, Tipo.TRASPASO_HERMANO, Tipo.COMPENSACION):
            if saldo_origen <= 0:
                raise ValidationError({"error": "El bolsillo de origen no tiene saldo a favor."})
            if res.monto > saldo_origen:
                raise ValidationError({"monto": f"El monto supera el saldo a favor ({_gs(saldo_origen)})."})
        else:  # COBRO, TRASLADO_CC, CONDONACION: operan sobre una deuda
            if saldo_origen >= 0:
                raise ValidationError({"error": "El bolsillo indicado no tiene deuda."})
            if res.monto > -saldo_origen:
                raise ValidationError({"monto": f"El monto supera la deuda ({_gs(-saldo_origen)})."})

        if tipo == Tipo.DEVOLUCION:
            if res.metodo_pago not in METODOS_DEVOLUCION:
                raise ValidationError({"metodo_pago": "La devolución es en EFECTIVO o TRANSFERENCIA."})
            if res.metodo_pago == "TRANSFERENCIA" and not res.referencia.strip():
                raise ValidationError({"referencia": "Indicá la referencia de la transferencia."})

        elif tipo == Tipo.COBRO:
            if res.metodo_pago not in METODOS_COBRO:
                raise ValidationError({"metodo_pago": f"Medio de cobro inválido. Use: {', '.join(METODOS_COBRO)}."})
            if res.metodo_pago == "TRANSFERENCIA" and not res.referencia.strip():
                raise ValidationError({"referencia": "Indicá la referencia de la transferencia."})

        elif tipo == Tipo.CONDONACION:
            if len((res.motivo or "").strip()) < 10:
                raise ValidationError({"motivo": "La condonación requiere un motivo (mínimo 10 caracteres)."})

        elif tipo == Tipo.COMPENSACION:
            if res.bolsillo_destino not in Bolsillo.values or res.bolsillo_destino == res.bolsillo_origen:
                raise ValidationError({"bolsillo_destino": "Indicá el otro bolsillo del mismo alumno."})
            saldo_destino = CierreCuentaService._saldo_bolsillo(hijo, res.bolsillo_destino, bloquear)
            if saldo_destino >= 0:
                raise ValidationError({"error": "El bolsillo de destino no tiene deuda para compensar."})
            if res.monto > -saldo_destino:
                raise ValidationError({"monto": f"El monto supera la deuda a compensar ({_gs(-saldo_destino)})."})

        elif tipo == Tipo.TRASPASO_HERMANO:
            CierreCuentaService._validar_hermano(res)

        elif tipo == Tipo.TRASLADO_CC:
            CierreCuentaService._validar_cuenta_corriente(res, bloquear)

    @staticmethod
    def _validar_hermano(res):
        from apps.clientes.vigencia import motivo_no_recarga_hijo, motivo_no_recarga_tarjeta
        from apps.core.models import Tarjeta

        hijo, destino = res.cierre.hijo, res.hijo_destino
        if destino is None:
            raise ValidationError({"hijo_destino": "Indicá el hermano que recibe el saldo."})
        if destino.pk == hijo.pk:
            raise ValidationError({"hijo_destino": "El destino debe ser otro alumno."})
        if destino.cliente_responsable_id != hijo.cliente_responsable_id:
            raise ValidationError({"hijo_destino": "Solo se puede traspasar a un hermano del mismo responsable."})
        if not destino.activo:
            raise ValidationError({"hijo_destino": "El hermano está dado de baja."})
        if not res.bolsillo_destino:
            res.bolsillo_destino = res.bolsillo_origen
        if res.bolsillo_destino not in Bolsillo.values:
            raise ValidationError({"bolsillo_destino": "Bolsillo de destino inválido."})
        if res.bolsillo_destino == Bolsillo.CANTINA:
            tarjeta = Tarjeta.objects.filter(hijo=destino).first()
            if tarjeta is None or tarjeta.estado != Tarjeta.Estado.ACTIVA:
                raise ValidationError({"hijo_destino": "El hermano no tiene una tarjeta de cantina activa."})
            motivo = motivo_no_recarga_tarjeta(tarjeta)
        else:
            motivo = motivo_no_recarga_hijo(destino)
        if motivo:
            raise ValidationError({"hijo_destino": motivo})

    @staticmethod
    def _validar_cuenta_corriente(res, bloquear):
        from apps.clientes.models import CuentaCorrienteCliente

        cliente = res.cierre.hijo.cliente_responsable
        if not cliente.permite_cuenta_corriente:
            raise ValidationError({"error": "El responsable no tiene habilitada la cuenta corriente."})
        if cliente.limite_credito:  # 0 = sin límite
            qs = CuentaCorrienteCliente.objects.filter(cliente=cliente).order_by("-id_movimiento_cc")
            ultimo = (qs.select_for_update() if bloquear else qs).first()
            saldo_cc = ultimo.saldo_resultante if ultimo else Decimal("0")
            if saldo_cc + res.monto > cliente.limite_credito:
                raise ValidationError({
                    "error": (
                        f"El traslado excede el límite de crédito autorizado ({_gs(cliente.limite_credito)}); "
                        f"deuda actual {_gs(saldo_cc)}."
                    ),
                })

    # ── Ejecución ────────────────────────────────────────────────────────────

    @staticmethod
    def _mover(hijo, bolsillo, delta, descripcion, usuario):
        """Ajusta un bolsillo dejando el movimiento en su libro mayor.
        Devuelve el movimiento (tarjeta: su id entero; almuerzo: la instancia)."""
        from apps.almuerzos.models import MovimientoSaldoAlmuerzo, SaldoAlmuerzo
        from apps.core.models import MovimientoTarjeta, Tarjeta

        if bolsillo == Bolsillo.CANTINA:
            tarjeta = Tarjeta.objects.select_for_update().get(hijo=hijo)
            anterior = tarjeta.saldo_actual
            movimiento = MovimientoTarjeta.objects.create(
                tarjeta=tarjeta, tipo=MovimientoTarjeta.Tipo.AJUSTE, monto=delta,
                saldo_anterior=anterior, saldo_resultante=anterior + delta,
                descripcion=descripcion[:255], creado_por=usuario,
            )
            Tarjeta.objects.filter(pk=tarjeta.pk).update(saldo_actual=anterior + delta)
            return movimiento.pk

        saldo = SaldoAlmuerzo.objects.select_for_update().get(hijo=hijo)
        saldo.saldo_actual += delta
        saldo.save(update_fields=["saldo_actual"])
        return MovimientoSaldoAlmuerzo.objects.create(
            saldo=saldo, tipo=MovimientoSaldoAlmuerzo.Tipo.AJUSTE, monto=delta,
            saldo_resultante=saldo.saldo_actual, observaciones=descripcion[:200],
        )

    @staticmethod
    def _guardar_movimiento(res, campo_tarjeta, campo_almuerzo, bolsillo, movimiento):
        if bolsillo == Bolsillo.CANTINA:
            setattr(res, campo_tarjeta, movimiento)
        else:
            setattr(res, campo_almuerzo, movimiento)

    @staticmethod
    def _ejecutar(resolucion, ejecutor):
        from apps.almuerzos.services import AlmuerzoService
        from apps.clientes.models import CuentaCorrienteCliente
        from apps.contabilidad.models import MovimientoCaja
        from apps.core.models import Tarjeta
        from apps.core.services import TarjetaService

        advertencia = None
        with transaction.atomic():
            res = (
                ResolucionSaldo.objects.select_for_update(of=("self",))
                .select_related("cierre__hijo__cliente_responsable", "hijo_destino")
                .get(pk=resolucion.pk)
            )
            if res.estado != ResolucionSaldo.Estado.SOLICITADA:
                raise ValidationError({"error": "La resolución ya fue procesada."})
            CierreCuentaService._validar(res, bloquear=True)

            cierre, hijo = res.cierre, res.cierre.hijo
            cliente = hijo.cliente_responsable
            etiqueta = f"Cierre de cuentas {cierre.anio}: {res.get_tipo_display()} #{res.pk}"
            origen, monto = res.bolsillo_origen, res.monto

            if res.tipo == Tipo.DEVOLUCION:
                cierre_caja = None
                if res.metodo_pago == "EFECTIVO":
                    cierre_caja = _cierre_caja_abierto(ejecutor)
                    if cierre_caja is None:
                        raise ValidationError({
                            "error": "Abrí tu caja para registrar la devolución en efectivo, "
                                     "o elegí devolución por transferencia.",
                        })
                mov = CierreCuentaService._mover(hijo, origen, -monto, etiqueta, ejecutor)
                CierreCuentaService._guardar_movimiento(
                    res, "movimiento_tarjeta_origen_id", "movimiento_almuerzo_origen", origen, mov)
                if cierre_caja:
                    res.movimiento_caja = MovimientoCaja.objects.create(
                        cierre=cierre_caja, tipo=MovimientoCaja.Tipo.EGRESO, monto=monto,
                        descripcion=f"Devolución {etiqueta} - {hijo.nombre_completo}"[:200],
                        medio_pago=resolver_medio_pago("EFECTIVO"),
                    )

            elif res.tipo == Tipo.TRASPASO_HERMANO:
                hermano = res.hijo_destino
                mov_o = CierreCuentaService._mover(
                    hijo, origen, -monto, f"{etiqueta} → {hermano.nombre_completo}", ejecutor)
                mov_d = CierreCuentaService._mover(
                    hermano, res.bolsillo_destino, monto, f"{etiqueta} ← {hijo.nombre_completo}", ejecutor)
                CierreCuentaService._guardar_movimiento(
                    res, "movimiento_tarjeta_origen_id", "movimiento_almuerzo_origen", origen, mov_o)
                CierreCuentaService._guardar_movimiento(
                    res, "movimiento_tarjeta_destino_id", "movimiento_almuerzo_destino", res.bolsillo_destino, mov_d)

            elif res.tipo == Tipo.COMPENSACION:
                mov_o = CierreCuentaService._mover(hijo, origen, -monto, etiqueta, ejecutor)
                mov_d = CierreCuentaService._mover(hijo, res.bolsillo_destino, monto, etiqueta, ejecutor)
                CierreCuentaService._guardar_movimiento(
                    res, "movimiento_tarjeta_origen_id", "movimiento_almuerzo_origen", origen, mov_o)
                CierreCuentaService._guardar_movimiento(
                    res, "movimiento_tarjeta_destino_id", "movimiento_almuerzo_destino", res.bolsillo_destino, mov_d)

            elif res.tipo == Tipo.COBRO:
                cierre_caja = _cierre_caja_abierto(ejecutor) if res.metodo_pago in _METODOS_CON_CAJA else None
                medio = resolver_medio_pago(res.metodo_pago)
                if origen == Bolsillo.CANTINA:
                    tarjeta = Tarjeta.objects.get(hijo=hijo)
                    res.carga_saldo = TarjetaService.cargar_saldo(
                        tarjeta=tarjeta, monto=monto, cliente_origen=cliente, responsable=ejecutor,
                        metodo_pago=res.metodo_pago, referencia=res.referencia,
                        cierre_caja=cierre_caja, medio_pago_obj=medio,
                    )
                else:
                    res.recarga_almuerzo = AlmuerzoService.recargar_saldo(
                        hijo=hijo, monto=monto, registrado_por=ejecutor, metodo_pago=res.metodo_pago,
                        referencia=res.referencia, cierre_caja=cierre_caja, medio_pago_obj=medio,
                    )
                if res.metodo_pago in _METODOS_CON_CAJA and cierre_caja is None:
                    advertencia = ADVERTENCIA_SIN_CAJA

            elif res.tipo == Tipo.TRASLADO_CC:
                mov = CierreCuentaService._mover(hijo, origen, monto, etiqueta, ejecutor)
                CierreCuentaService._guardar_movimiento(
                    res, "movimiento_tarjeta_origen_id", "movimiento_almuerzo_origen", origen, mov)
                res.movimiento_cc = CuentaCorrienteCliente.objects.create(
                    cliente=cliente, tipo=CuentaCorrienteCliente.Tipo.DEBITO, monto=monto,
                    descripcion=f"Traslado de deuda de {hijo.nombre_completo} ({etiqueta})"[:255],
                    creado_por=ejecutor,
                    origen=(
                        CuentaCorrienteCliente.Origen.CANTINA if origen == Bolsillo.CANTINA
                        else CuentaCorrienteCliente.Origen.ALMUERZO
                    ),
                )

            elif res.tipo == Tipo.CONDONACION:
                mov = CierreCuentaService._mover(
                    hijo, origen, monto, f"{etiqueta}: {res.motivo.strip()}", ejecutor)
                CierreCuentaService._guardar_movimiento(
                    res, "movimiento_tarjeta_origen_id", "movimiento_almuerzo_origen", origen, mov)

            ahora = timezone.now()
            res.estado = ResolucionSaldo.Estado.EJECUTADA
            res.fecha_ejecucion = ahora
            if res.tipo in REQUIEREN_ADMIN:
                res.decidido_por = ejecutor
                res.fecha_decision = ahora
            res.save()
            CierreCuentaService._recalcular_estado(cierre, ejecutor)

        registrar_auditoria(
            usuario=ejecutor, operacion=f"CIERRE_CUENTA_{res.tipo}_EJECUTADA",
            tabla="cierre_cuentas_resolucionsaldo", id_registro=res.pk,
            descripcion=(
                f"{res.get_tipo_display()} {_gs(res.monto)} de {res.cierre.hijo.nombre_completo} "
                f"({res.bolsillo_origen}); solicitó {res.solicitado_por.email}"
            ),
        )
        CierreCuentaService._notificar_familia(res)
        return advertencia

    @staticmethod
    def _recalcular_estado(cierre, usuario=None):
        if cierre.estado == CierreCuentaAlumno.Estado.CERRADO_CON_SALDO:
            return
        cantina, almuerzo = CierreCuentaService.saldos(cierre.hijo)
        if not cantina and not almuerzo:
            cierre.estado = CierreCuentaAlumno.Estado.RESUELTO
            cierre.fecha_cierre = cierre.fecha_cierre or timezone.now()
            cierre.cerrado_por = cierre.cerrado_por or usuario
            cierre.saldo_cantina_final, cierre.saldo_almuerzo_final = cantina, almuerzo
        elif cierre.resoluciones.filter(estado=ResolucionSaldo.Estado.EJECUTADA).exists():
            cierre.estado = CierreCuentaAlumno.Estado.PARCIAL
        cierre.save()

    # ── Notificaciones ───────────────────────────────────────────────────────

    @staticmethod
    def _notificar_familia(res):
        from apps.notificaciones.models import Notificacion
        from apps.notificaciones.services import whatsapp_cliente

        hijo = res.cierre.hijo
        bolsillo = "cantina" if res.bolsillo_origen == Bolsillo.CANTINA else "almuerzo"
        textos = {
            Tipo.DEVOLUCION: f"Se registró la devolución de {_gs(res.monto)} del saldo de {bolsillo} de {hijo.nombre_completo}.",
            Tipo.TRASPASO_HERMANO: (
                f"Se traspasaron {_gs(res.monto)} del saldo de {bolsillo} de {hijo.nombre_completo} "
                f"a {res.hijo_destino.nombre_completo if res.hijo_destino else 'su hermano/a'}."
            ),
            Tipo.COMPENSACION: f"Se compensaron {_gs(res.monto)} entre los saldos de cantina y almuerzo de {hijo.nombre_completo}.",
            Tipo.COBRO: f"Se registró el pago de {_gs(res.monto)} de la deuda de {bolsillo} de {hijo.nombre_completo}. Gracias.",
            Tipo.TRASLADO_CC: f"La deuda de {bolsillo} de {hijo.nombre_completo} ({_gs(res.monto)}) pasó a su cuenta corriente.",
            Tipo.CONDONACION: f"Se condonó {_gs(res.monto)} de la deuda de {bolsillo} de {hijo.nombre_completo}.",
        }
        mensaje = textos[res.tipo]
        responsable = hijo.cliente_responsable
        try:
            usuario = responsable.usuario_portal
        except Exception:
            usuario = None
        try:
            if usuario:
                Notificacion.objects.create(
                    usuario=usuario, tipo=Notificacion.Tipo.SISTEMA,
                    titulo=f"Cierre de cuentas de {hijo.nombre}", mensaje=mensaje,
                    destino=Notificacion.Destino.SISTEMA,
                )
            whatsapp_cliente(responsable, mensaje)
        except Exception:
            logger.warning("No se pudo notificar a la familia de la resolución %s", res.pk, exc_info=True)

    @staticmethod
    def _notificar_admins_pendiente(res):
        from apps.notificaciones.models import Notificacion
        from apps.usuarios.models import Usuario

        hijo = res.cierre.hijo
        for admin in Usuario.objects.filter(rol=Usuario.Rol.ADMIN, is_active=True):
            Notificacion.objects.create(
                usuario=admin, tipo=Notificacion.Tipo.SISTEMA,
                titulo=f"Aprobación pendiente: {res.get_tipo_display().lower()} de {hijo.nombre_completo}",
                mensaje=(
                    f"{res.solicitado_por.nombre_completo} solicita {res.get_tipo_display().lower()} "
                    f"de {_gs(res.monto)} ({res.bolsillo_origen.lower()}). Motivo: {res.motivo or '—'}."
                ),
                destino=Notificacion.Destino.SISTEMA,
            )

    @staticmethod
    def _notificar_solicitante_rechazo(res):
        from apps.notificaciones.models import Notificacion

        Notificacion.objects.create(
            usuario=res.solicitado_por, tipo=Notificacion.Tipo.SISTEMA,
            titulo=f"Resolución rechazada: {res.cierre.hijo.nombre_completo}",
            mensaje=f"Se rechazó la {res.get_tipo_display().lower()} de {_gs(res.monto)}. Motivo: {res.motivo_rechazo}",
            destino=Notificacion.Destino.SISTEMA,
        )
