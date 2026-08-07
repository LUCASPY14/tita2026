"""
Servicios de negocio para almuerzos
"""

import logging
from datetime import date
from decimal import Decimal

from django.db import models, transaction

from rest_framework.exceptions import ValidationError

from .models import (
    PrecioAlmuerzo,
    SuscripcionAlmuerzo,
    RegistroConsumoAlmuerzo,
    CuentaAlmuerzoMensual,
    SaldoAlmuerzo,
    MovimientoSaldoAlmuerzo,
    RecargaSaldoAlmuerzo,
)
from .validators import validar_limite_registros_diarios

logger = logging.getLogger(__name__)


class AlmuerzoService:
    """Servicio para registrar consumo de almuerzos."""

    @staticmethod
    def get_precio_activo(fecha=None):
        """Retorna el precio de almuerzo vigente para una fecha."""
        if fecha is None:
            fecha = date.today()
        return (
            PrecioAlmuerzo.objects.filter(
                fecha_inicio_vigencia__lte=fecha,
                activo=True,
            )
            .filter(
                models.Q(fecha_fin_vigencia__isnull=True) |
                models.Q(fecha_fin_vigencia__gte=fecha)
            )
            .order_by("-fecha_inicio_vigencia")
            .first()
        )

    @staticmethod
    def registrar_consumo(
        *,
        hijo,
        fecha_consumo,
        nro_tarjeta,
        registrado_por,
        tipo_almuerzo=None,
        suscripcion=None,
    ) -> RegistroConsumoAlmuerzo:
        """
        Registra un consumo de almuerzo.

        Reglas de negocio:
        - Maximo 2 registros por dia por alumno
        - Solo el primer registro del dia genera costo
        - El costo se agrega a la cuenta mensual
        """
        if not nro_tarjeta:
            raise ValidationError({"error": "Debe especificar la tarjeta."})

        # Validar que la tarjeta pertenece al hijo y está activa
        if nro_tarjeta.hijo_id != hijo.pk:
            raise ValidationError({"error": "La tarjeta no pertenece al estudiante indicado."})
        if nro_tarjeta.estado != "ACTIVA":
            raise ValidationError({
                "error": f"La tarjeta está {nro_tarjeta.get_estado_display().lower()} y no puede usarse."
            })

        # No permitir consumos en fecha futura
        if fecha_consumo > date.today():
            raise ValidationError({"error": "No se puede registrar un consumo en fecha futura."})

        # Validar suscripcion activa
        if suscripcion and suscripcion.estado != SuscripcionAlmuerzo.Estado.ACTIVA:
            raise ValidationError({
                "error": "La suscripcion no esta activa.",
                "estado": suscripcion.estado,
            })

        with transaction.atomic():
            # Bloquear registros del alumno en el dia
            es_primer_registro = validar_limite_registros_diarios(hijo, fecha_consumo)

            # Determinar costo. El almuerzo es una cuenta corriente: nunca se
            # bloquea el registro por saldo — puede quedar negativo.
            if es_primer_registro:
                precio_obj = AlmuerzoService.get_precio_activo(fecha_consumo)
                if precio_obj:
                    costo = precio_obj.precio_unitario
                elif tipo_almuerzo:
                    costo = tipo_almuerzo.precio_unitario
                else:
                    raise ValidationError({
                        "error": "No hay precio de almuerzo configurado."
                    })
            else:
                costo = Decimal("0")

            # Asegurar que exista la cuenta mensual ANTES de crear el registro:
            # el trigger trg_sync_cuenta_almuerzo (migración 0014) recalcula
            # cantidad_almuerzos/monto_total desde los registros reales en cada
            # INSERT sobre RegistroConsumoAlmuerzo, pero solo si la fila de la
            # cuenta ya existe. Si la creamos después, el INSERT no tiene qué
            # actualizar y hay que sumar el costo también acá — no lo hacemos:
            # el trigger es la única fuente de verdad para esos dos campos.
            if es_primer_registro:
                AlmuerzoService._asegurar_cuenta_mensual(hijo, fecha_consumo)

            # Crear registro (dispara el trigger, que sincroniza la cuenta)
            registro = RegistroConsumoAlmuerzo.objects.create(
                hijo=hijo,
                fecha_consumo=fecha_consumo,
                nro_tarjeta=nro_tarjeta,
                tipo_almuerzo=tipo_almuerzo,
                suscripcion=suscripcion,
                registrado_por=registrado_por,
                costo_almuerzo=costo,
                ya_cobrado=es_primer_registro,
                estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
            )

            if es_primer_registro:
                # Si no se marca, cerrar_cuentas_mes_anterior lo vuelve a sumar
                # al cerrar el mes (el trigger ya lo contó al crearlo).
                registro.marcado_en_cuenta = True
                registro.save(update_fields=["marcado_en_cuenta"])

                AlmuerzoService._debitar_saldo_almuerzo(registro)

        if es_primer_registro:
            AlmuerzoService._notificar_ingreso_comedor(registro)

        return registro

    @staticmethod
    def _asegurar_cuenta_mensual(hijo, fecha):
        """Crea la cuenta mensual del alumno si todavía no existe.

        No suma cantidad_almuerzos/monto_total acá: eso lo hace el trigger
        trg_sync_cuenta_almuerzo al insertar el RegistroConsumoAlmuerzo.
        """
        CuentaAlmuerzoMensual.objects.get_or_create(
            hijo=hijo,
            anio=fecha.year,
            mes=fecha.month,
            defaults={
                "cantidad_almuerzos": 0,
                "monto_total": 0,
                "monto_pagado": 0,
                "forma_cobro": CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
                "estado": CuentaAlmuerzoMensual.Estado.PENDIENTE,
            },
        )

    @staticmethod
    def _debitar_saldo_almuerzo(registro):
        """Descuenta el costo del almuerzo del saldo corriente del hijo.

        Es una cuenta corriente, no un prepago estricto: puede quedar
        negativo, nunca bloquea el registro del consumo.
        """
        saldo, _ = SaldoAlmuerzo.objects.get_or_create(hijo=registro.hijo)
        saldo = SaldoAlmuerzo.objects.select_for_update().get(pk=saldo.pk)
        saldo.saldo_actual -= registro.costo_almuerzo
        saldo.save(update_fields=["saldo_actual"])
        MovimientoSaldoAlmuerzo.objects.create(
            saldo=saldo,
            tipo=MovimientoSaldoAlmuerzo.Tipo.CONSUMO,
            monto=-registro.costo_almuerzo,
            saldo_resultante=saldo.saldo_actual,
            registro_consumo=registro,
        )

    @staticmethod
    def _revertir_saldo_almuerzo(registro):
        """Devuelve al saldo corriente el costo de un almuerzo anulado."""
        saldo, _ = SaldoAlmuerzo.objects.get_or_create(hijo=registro.hijo)
        saldo = SaldoAlmuerzo.objects.select_for_update().get(pk=saldo.pk)
        saldo.saldo_actual += registro.costo_almuerzo
        saldo.save(update_fields=["saldo_actual"])
        MovimientoSaldoAlmuerzo.objects.create(
            saldo=saldo,
            tipo=MovimientoSaldoAlmuerzo.Tipo.AJUSTE,
            monto=registro.costo_almuerzo,
            saldo_resultante=saldo.saldo_actual,
            registro_consumo=registro,
            observaciones="Reversión por anulación de registro de consumo",
        )

    @staticmethod
    def _notificar_ingreso_comedor(registro):
        """Avisa por WhatsApp al responsable que el hijo almorzó hoy."""
        from apps.notificaciones.services import whatsapp_cliente
        try:
            whatsapp_cliente(
                registro.hijo.cliente_responsable,
                f"{registro.hijo.nombre_completo} almorzó hoy "
                f"{registro.fecha_consumo.strftime('%d/%m/%Y')}. "
                f"Costo: Gs. {int(registro.costo_almuerzo):,}."
            )
        except Exception:
            logger.warning(
                "WhatsApp: fallo al notificar almuerzo de %s", registro.hijo_id, exc_info=True
            )

    @staticmethod
    def recargar_saldo(
        *,
        hijo,
        monto: Decimal,
        registrado_por=None,
        metodo_pago: str = "EFECTIVO",
        referencia: str = "",
        cierre_caja=None,
        medio_pago_obj=None,
    ) -> RecargaSaldoAlmuerzo:
        """
        Carga saldo de almuerzo de un hijo (cuenta corriente, no descuenta
        nada de la tarjeta de cantina).

        Flujo:
        1. Crear RecargaSaldoAlmuerzo CONFIRMADA
        2. Actualizar SaldoAlmuerzo.saldo_actual
        3. Crear MovimientoSaldoAlmuerzo (RECARGA)
        4. Crear MovimientoCaja INGRESO si hay cierre abierto
        """
        if monto <= 0:
            raise ValidationError({"error": "El monto debe ser mayor a 0."})

        with transaction.atomic():
            recarga = RecargaSaldoAlmuerzo.objects.create(
                hijo=hijo,
                monto_cargado=monto,
                metodo_pago=metodo_pago,
                referencia=referencia,
                registrado_por=registrado_por,
                estado=RecargaSaldoAlmuerzo.Estado.CONFIRMADA,
            )

            saldo, _ = SaldoAlmuerzo.objects.get_or_create(hijo=hijo)
            saldo = SaldoAlmuerzo.objects.select_for_update().get(pk=saldo.pk)
            saldo.saldo_actual += monto
            saldo.save(update_fields=["saldo_actual"])

            MovimientoSaldoAlmuerzo.objects.create(
                saldo=saldo,
                tipo=MovimientoSaldoAlmuerzo.Tipo.RECARGA,
                monto=monto,
                saldo_resultante=saldo.saldo_actual,
                recarga=recarga,
            )

            if cierre_caja:
                from apps.contabilidad.models import MovimientoCaja
                MovimientoCaja.objects.create(
                    cierre=cierre_caja,
                    tipo=MovimientoCaja.Tipo.INGRESO,
                    monto=monto,
                    descripcion=f"Recarga almuerzo #{recarga.pk} - {hijo}",
                    medio_pago=medio_pago_obj,
                )

            try:
                from apps.notificaciones.services import whatsapp_cliente
                whatsapp_cliente(
                    hijo.cliente_responsable,
                    f"Recarga exitosa: se acreditaron Gs. {int(monto):,} al saldo de almuerzo de "
                    f"{hijo.nombre_completo}. Nuevo saldo: Gs. {int(saldo.saldo_actual):,}.",
                )
            except Exception:
                logger.warning(
                    "WhatsApp de recarga de almuerzo no enviado para hijo %s", hijo.pk, exc_info=True
                )

            return recarga

    @staticmethod
    def confirmar_recarga(*, recarga, cierre_caja=None, medio_pago_obj=None) -> RecargaSaldoAlmuerzo:
        """Confirma una RecargaSaldoAlmuerzo PENDIENTE (ej: transferencia)."""
        if recarga.estado != RecargaSaldoAlmuerzo.Estado.PENDIENTE:
            raise ValidationError({"error": "La recarga no está en estado PENDIENTE."})

        with transaction.atomic():
            recarga = RecargaSaldoAlmuerzo.objects.select_for_update().get(pk=recarga.pk)
            recarga.estado = RecargaSaldoAlmuerzo.Estado.CONFIRMADA
            recarga.save(update_fields=["estado"])

            saldo, _ = SaldoAlmuerzo.objects.get_or_create(hijo=recarga.hijo)
            saldo = SaldoAlmuerzo.objects.select_for_update().get(pk=saldo.pk)
            saldo.saldo_actual += recarga.monto_cargado
            saldo.save(update_fields=["saldo_actual"])

            MovimientoSaldoAlmuerzo.objects.create(
                saldo=saldo,
                tipo=MovimientoSaldoAlmuerzo.Tipo.RECARGA,
                monto=recarga.monto_cargado,
                saldo_resultante=saldo.saldo_actual,
                recarga=recarga,
                observaciones="Confirmación de recarga pendiente",
            )

            if cierre_caja:
                from apps.contabilidad.models import MovimientoCaja
                MovimientoCaja.objects.create(
                    cierre=cierre_caja,
                    tipo=MovimientoCaja.Tipo.INGRESO,
                    monto=recarga.monto_cargado,
                    descripcion=f"Recarga almuerzo confirmada #{recarga.pk} - {recarga.hijo}",
                    medio_pago=medio_pago_obj,
                )

            try:
                from apps.notificaciones.services import whatsapp_cliente
                whatsapp_cliente(
                    recarga.hijo.cliente_responsable,
                    f"Recarga exitosa: se acreditaron Gs. {int(recarga.monto_cargado):,} al saldo de "
                    f"almuerzo de {recarga.hijo.nombre_completo}. Nuevo saldo: Gs. {int(saldo.saldo_actual):,}.",
                )
            except Exception:
                logger.warning(
                    "WhatsApp de confirmación de recarga de almuerzo no enviado para hijo %s",
                    recarga.hijo_id, exc_info=True,
                )

            return recarga
