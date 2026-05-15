"""
Servicios de negocio para contabilidad
Caja y facturacion
"""

from decimal import Decimal

from django.db import models, transaction, IntegrityError
from django.utils import timezone

from rest_framework.exceptions import ValidationError

from .models import Caja, CierreCaja, MovimientoCaja, Factura


class CajaService:
    """Servicio para operaciones de caja."""

    @staticmethod
    def abrir_caja(*, caja, empleado, monto_inicial: Decimal = 0) -> CierreCaja:
        """
        Abre una caja para iniciar operaciones.
        Valida que no haya otra caja abierta.
        """
        with transaction.atomic():
            caja_obj = Caja.objects.select_for_update().get(pk=caja.pk)

            if CierreCaja.objects.filter(
                caja=caja_obj, estado=CierreCaja.Estado.ABIERTO
            ).exists():
                raise ValidationError({"error": "La caja ya tiene un cierre abierto."})

            return CierreCaja.objects.create(
                caja=caja_obj,
                empleado=empleado,
                monto_inicial=monto_inicial,
                estado=CierreCaja.Estado.ABIERTO,
            )

    @staticmethod
    def cerrar_caja(*, cierre, monto_contado: Decimal) -> CierreCaja:
        """
        Cierra una caja y calcula la diferencia.
        """
        with transaction.atomic():
            cierre = CierreCaja.objects.select_for_update().get(pk=cierre.pk)

            if cierre.estado != CierreCaja.Estado.ABIERTO:
                raise ValidationError({"error": "La caja no esta abierta."})

            ingresos = (
                MovimientoCaja.objects.filter(
                    cierre=cierre, tipo=MovimientoCaja.Tipo.INGRESO
                ).aggregate(total=models.Sum("monto"))["total"]
            ) or Decimal("0")

            egresos = (
                MovimientoCaja.objects.filter(
                    cierre=cierre, tipo=MovimientoCaja.Tipo.EGRESO
                ).aggregate(total=models.Sum("monto"))["total"]
            ) or Decimal("0")

            monto_esperado = cierre.monto_inicial + ingresos - egresos
            diferencia = monto_contado - monto_esperado

            cierre.monto_contado_fisico = monto_contado
            cierre.diferencia_efectivo = diferencia
            cierre.fecha_cierre = timezone.now()
            cierre.estado = CierreCaja.Estado.CERRADO
            cierre.save()

            return cierre

    @staticmethod
    def registrar_movimiento(
        *,
        cierre,
        tipo: str,
        monto: Decimal,
        medio_pago,
        descripcion: str = "",
        venta=None,
    ) -> MovimientoCaja:
        """Registra un movimiento en un cierre de caja."""
        if monto <= 0:
            raise ValidationError({"error": "El monto debe ser mayor a 0."})

        if tipo not in (MovimientoCaja.Tipo.INGRESO, MovimientoCaja.Tipo.EGRESO):
            raise ValidationError({"error": f"Tipo invalido: {tipo}."})

        with transaction.atomic():
            cierre_obj = CierreCaja.objects.select_for_update().get(pk=cierre.pk)

            if cierre_obj.estado != CierreCaja.Estado.ABIERTO:
                raise ValidationError({"error": "La caja no esta abierta."})

            return MovimientoCaja.objects.create(
                cierre=cierre_obj,
                tipo=tipo,
                monto=monto,
                medio_pago=medio_pago,
                descripcion=descripcion,
                venta=venta,
            )


class FacturacionService:
    """Servicio para factura en papel preimpreso."""

    @staticmethod
    def emitir_factura(
        *,
        cliente,
        venta=None,
        nro_factura: str,
        monto_total: Decimal,
        iva_10: Decimal = 0,
        iva_5: Decimal = 0,
        monto_exenta: Decimal = 0,
        observaciones: str = "",
    ) -> Factura:
        """
        Registra una factura preimpresa.
        Valida que el numero no este duplicado.
        """
        with transaction.atomic():
            if Factura.objects.filter(nro_factura=nro_factura).exists():
                raise ValidationError({"error": f"La factura {nro_factura} ya fue registrada."})

            try:
                return Factura.objects.create(
                    cliente=cliente,
                    venta=venta,
                    nro_factura=nro_factura,
                    monto_total=monto_total,
                    iva_10=iva_10,
                    iva_5=iva_5,
                    monto_exenta=monto_exenta,
                    observaciones=observaciones,
                )
            except IntegrityError:
                raise ValidationError({"error": f"La factura {nro_factura} ya fue registrada."})

    @staticmethod
    def anular_factura(factura) -> Factura:
        """Anula una factura."""
        with transaction.atomic():
            factura = Factura.objects.select_for_update().get(pk=factura.pk)

            if factura.estado == Factura.Estado.ANULADA:
                raise ValidationError({"error": "La factura ya esta anulada."})

            factura.estado = Factura.Estado.ANULADA
            factura.save()
            return factura