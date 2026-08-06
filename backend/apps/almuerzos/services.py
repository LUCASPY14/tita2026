"""
Servicios de negocio para almuerzos
"""

from datetime import date
from decimal import Decimal

from django.db import models, transaction

from rest_framework.exceptions import ValidationError

from .models import (
    PrecioAlmuerzo,
    SuscripcionAlmuerzo,
    RegistroConsumoAlmuerzo,
    CuentaAlmuerzoMensual,
)
from .validators import validar_limite_registros_diarios


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

            # Determinar costo
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

                # Verificar limite de credito mensual
                if suscripcion and suscripcion.plan.limite_credito_mensual:
                    cuenta_mes = CuentaAlmuerzoMensual.objects.filter(
                        hijo=hijo,
                        anio=fecha_consumo.year,
                        mes=fecha_consumo.month,
                    ).first()
                    saldo = (
                        (cuenta_mes.monto_total - cuenta_mes.monto_pagado)
                        if cuenta_mes else Decimal("0")
                    )
                    if saldo + costo > suscripcion.plan.limite_credito_mensual:
                        raise ValidationError({
                            "error": "Limite de credito mensual alcanzado.",
                            "saldo_pendiente": str(saldo),
                            "limite": str(suscripcion.plan.limite_credito_mensual),
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
