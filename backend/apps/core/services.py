"""
Servicios de negocio para core
Tarjetas, recargas y consumos
"""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from .models import Tarjeta, MovimientoTarjeta, CargaSaldo, ConsumoTarjeta


class TarjetaService:
    """Servicio para operaciones con tarjetas."""

    @staticmethod
    def _validar_activa(tarjeta):
        """Valida que la tarjeta este activa."""
        if tarjeta.estado != Tarjeta.Estado.ACTIVA:
            raise ValidationError({
                "error": "La tarjeta no esta activa.",
                "estado": tarjeta.estado,
            })

    @staticmethod
    def cargar_saldo(
        *,
        tarjeta,
        monto: Decimal,
        cliente_origen,
        responsable,
        medio_pago=None,
        metodo_pago: str = "EFECTIVO",
        referencia: str = "",
        cierre_caja=None,
        medio_pago_obj=None,
    ) -> CargaSaldo:
        """
        Carga saldo a una tarjeta.

        Flujo:
        1. Validar tarjeta activa
        2. Crear CargaSaldo
        3. Actualizar Tarjeta.saldo_actual
        4. Crear MovimientoTarjeta (RECARGA)
        5. Crear MovimientoCaja INGRESO si hay cierre abierto
        """
        if monto <= 0:
            raise ValidationError({"error": "El monto debe ser mayor a 0."})

        with transaction.atomic():
            tarjeta = Tarjeta.objects.select_for_update().get(pk=tarjeta.pk)
            TarjetaService._validar_activa(tarjeta)

            carga = CargaSaldo.objects.create(
                tarjeta=tarjeta,
                cliente_origen=cliente_origen,
                monto_cargado=monto,
                metodo_pago=metodo_pago,
                referencia=referencia,
                responsable=responsable,
                estado=CargaSaldo.Estado.CONFIRMADA,
                fecha_confirmacion=timezone.now(),
            )

            saldo_anterior = tarjeta.saldo_actual
            tarjeta.saldo_actual += monto
            tarjeta.save()

            MovimientoTarjeta.objects.create(
                tarjeta=tarjeta,
                tipo=MovimientoTarjeta.Tipo.RECARGA,
                monto=monto,
                saldo_anterior=saldo_anterior,
                saldo_resultante=tarjeta.saldo_actual,
                carga=carga,
                descripcion=f"Recarga #{carga.pk}",
                creado_por=responsable,
            )

            if cierre_caja:
                from apps.contabilidad.models import MovimientoCaja
                MovimientoCaja.objects.create(
                    cierre=cierre_caja,
                    tipo=MovimientoCaja.Tipo.INGRESO,
                    monto=monto,
                    descripcion=f"Recarga #{carga.pk} - {tarjeta}",
                    medio_pago=medio_pago_obj,
                )

            return carga

    @staticmethod
    def confirmar_carga(*, carga, responsable, cierre_caja=None, medio_pago_obj=None) -> "CargaSaldo":
        """
        Confirma una CargaSaldo PENDIENTE: actualiza el saldo de la tarjeta
        y genera el MovimientoTarjeta correspondiente.
        """
        from django.utils import timezone

        if carga.estado != CargaSaldo.Estado.PENDIENTE:
            raise ValidationError({"error": "La carga no está en estado PENDIENTE."})

        with transaction.atomic():
            tarjeta = Tarjeta.objects.select_for_update().get(pk=carga.tarjeta_id)
            TarjetaService._validar_activa(tarjeta)

            saldo_anterior = tarjeta.saldo_actual
            tarjeta.saldo_actual += carga.monto_cargado
            tarjeta.save()

            carga.estado = CargaSaldo.Estado.CONFIRMADA
            carga.responsable = responsable
            carga.fecha_confirmacion = timezone.now()
            carga.save()

            MovimientoTarjeta.objects.create(
                tarjeta=tarjeta,
                tipo=MovimientoTarjeta.Tipo.RECARGA,
                monto=carga.monto_cargado,
                saldo_anterior=saldo_anterior,
                saldo_resultante=tarjeta.saldo_actual,
                carga=carga,
                descripcion=f"Recarga confirmada #{carga.pk}",
                creado_por=responsable,
            )

            if cierre_caja:
                from apps.contabilidad.models import MovimientoCaja
                MovimientoCaja.objects.create(
                    cierre=cierre_caja,
                    tipo=MovimientoCaja.Tipo.INGRESO,
                    monto=carga.monto_cargado,
                    descripcion=f"Recarga confirmada #{carga.pk} - {tarjeta}",
                    medio_pago=medio_pago_obj,
                )

            return carga

    @staticmethod
    def consumir_saldo(
        *,
        tarjeta,
        monto: Decimal,
        registrado_por,
        detalle: str = "",
    ) -> ConsumoTarjeta:
        """
        Registra un consumo de saldo de tarjeta.

        Flujo:
        1. Validar tarjeta activa
        2. Validar saldo disponible (incluye limite_credito)
        3. Actualizar Tarjeta.saldo_actual
        4. Crear ConsumoTarjeta
        5. Crear MovimientoTarjeta (CONSUMO)
        """
        if monto <= 0:
            raise ValidationError({"error": "El monto debe ser mayor a 0."})

        with transaction.atomic():
            tarjeta = Tarjeta.objects.select_for_update().get(pk=tarjeta.pk)
            TarjetaService._validar_activa(tarjeta)

            if tarjeta.saldo_disponible < monto:
                raise ValidationError({
                    "error": "Saldo insuficiente.",
                    "saldo_disponible": str(tarjeta.saldo_disponible),
                    "monto": str(monto),
                })

            saldo_anterior = tarjeta.saldo_actual
            tarjeta.saldo_actual -= monto
            tarjeta.save()

            consumo = ConsumoTarjeta.objects.create(
                tarjeta=tarjeta,
                monto_consumido=monto,
                saldo_anterior=saldo_anterior,
                saldo_posterior=tarjeta.saldo_actual,
                detalle=detalle,
                registrado_por=registrado_por,
            )

            MovimientoTarjeta.objects.create(
                tarjeta=tarjeta,
                tipo=MovimientoTarjeta.Tipo.CONSUMO,
                monto=monto,
                saldo_anterior=saldo_anterior,
                saldo_resultante=tarjeta.saldo_actual,
                consumo=consumo,
                descripcion=detalle or f"Consumo #{consumo.pk}",
                creado_por=registrado_por,
            )

            return consumo