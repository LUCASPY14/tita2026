"""
Servicios de negocio para core
Tarjetas, recargas y consumos
"""

import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

from rest_framework.exceptions import ValidationError

from .models import Tarjeta, MovimientoTarjeta, CargaSaldo


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

            try:
                from apps.notificaciones.services import whatsapp_cliente
                cliente_resp = tarjeta.hijo.cliente_responsable
                whatsapp_cliente(
                    cliente_resp,
                    f"Recarga exitosa: se acreditaron Gs. {int(monto):,} a la tarjeta de "
                    f"{tarjeta.hijo.nombre_completo}. Nuevo saldo: Gs. {int(tarjeta.saldo_actual):,}.",
                )
            except Exception:
                logger.warning(
                    "WhatsApp de recarga no enviado para tarjeta %s",
                    tarjeta.pk,
                    exc_info=True,
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

            now = timezone.now()
            carga.estado = CargaSaldo.Estado.CONFIRMADA
            carga.supervisor_aprobador = responsable
            carga.fecha_aprobacion = now
            carga.fecha_confirmacion = now
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

            try:
                from apps.notificaciones.services import whatsapp_cliente
                cliente_resp = tarjeta.hijo.cliente_responsable
                whatsapp_cliente(
                    cliente_resp,
                    f"Recarga exitosa: se acreditaron Gs. {int(carga.monto_cargado):,} a la tarjeta de "
                    f"{tarjeta.hijo.nombre_completo}. Nuevo saldo: Gs. {int(tarjeta.saldo_actual):,}.",
                )
            except Exception:
                logger.warning(
                    "WhatsApp de confirmación no enviado para tarjeta %s",
                    tarjeta.pk,
                    exc_info=True,
                )

            return carga
