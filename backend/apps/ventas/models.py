"""
Modelos de la app ventas
Gestión de ventas, detalles, pagos y notas de crédito
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from simple_history.models import HistoricalRecords


# ==============================================================================
# VENTA
# ==============================================================================

class Venta(models.Model):
    """Venta realizada en la cantina."""

    class Tipo(models.TextChoices):
        CONTADO = "CONTADO", "Contado"
        CREDITO = "CREDITO", "Crédito"

    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        ANULADA = "ANULADA", "Anulada"

    class EstadoPago(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PARCIAL = "PARCIAL", "Parcial"
        PAGADO = "PAGADO", "Pagado"

    cliente = models.ForeignKey(
        "clientes.Cliente",
        models.PROTECT,
        related_name="ventas_factura",
        help_text="Cliente que realizó la compra",
    )
    hijo = models.ForeignKey(
        "clientes.Hijo",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas_factura",
        help_text="Hijo que recibió el producto (si aplica)",
    )
    fecha = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(
        max_length=10, choices=Tipo.choices, default=Tipo.CONTADO
    )
    estado = models.CharField(
        max_length=10, choices=Estado.choices, default=Estado.ACTIVA
    )
    estado_pago = models.CharField(
        max_length=10, choices=EstadoPago.choices, default=EstadoPago.PENDIENTE
    )

    # Totales en Guaraníes (sin decimales)
    monto_total = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    monto_gravada_10 = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    monto_gravada_5 = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    monto_exenta = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    iva_10 = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    iva_5 = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    # Facturación
    nro_factura = models.CharField(
        max_length=50, blank=True, null=True, help_text="Número de factura legal"
    )
    genera_factura_legal = models.BooleanField(default=False)

    # Relaciones opcionales
    medio_pago = models.ForeignKey(
        "core.MedioPago",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas_factura",
    )
    tarjeta = models.ForeignKey(
        "core.Tarjeta",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas",
        help_text="Tarjeta usada en el pago (permite reverso al anular)",
    )
    factura = models.ForeignKey(
        "contabilidad.Factura",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas_factura",
        help_text="Factura preimpresa asociada",
    )
    caja = models.ForeignKey(
        "contabilidad.Caja",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas_factura",
    )
    motivo_credito = models.TextField(
        blank=True, null=True, help_text="Motivo si se vendió a crédito"
    )

    # Auditoría
    cajero = models.ForeignKey(
        "usuarios.Usuario",
        models.PROTECT,
        related_name="ventas_realizadas",
    )
    autorizado_por = models.ForeignKey(
        "usuarios.Usuario",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas_autorizadas",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["cliente", "fecha"], name="idx_venta_cliente_fecha"),
            models.Index(fields=["fecha"], name="idx_venta_fecha"),
            models.Index(fields=["estado", "fecha"], name="idx_venta_estado_fecha"),
            models.Index(fields=["estado_pago"], name="idx_venta_estado_pago"),
            models.Index(fields=["nro_factura"], name="idx_venta_factura"),
        ]

    def __str__(self):
        return f"Venta #{self.pk} - {self.cliente} - ₲{self.monto_total:,.0f}"

    @property
    def total_pagado(self):
        """Suma de pagos aplicados a esta venta."""
        total = self.aplicaciones_pago.aggregate(
            total=models.Sum("monto_aplicado")
        )["total"]
        return total or Decimal("0")

    @property
    def saldo_pendiente(self):
        """Saldo pendiente de pago."""
        return self.monto_total - self.total_pagado

    @property
    def esta_pagada(self):
        return self.saldo_pendiente <= 0


# ==============================================================================
# DETALLE DE VENTA
# ==============================================================================

class DetalleVenta(models.Model):
    """Producto incluido en una venta con discriminación de IVA."""

    venta = models.ForeignKey(
        Venta, models.CASCADE, related_name="detalles"
    )
    producto = models.ForeignKey(
        "productos.Producto", models.PROTECT, related_name="detalles_venta"
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    precio_unitario = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Precio unitario en Guaraníes"
    )
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Subtotal en Guaraníes"
    )

    # Discriminación de IVA por producto (Paraguay)
    monto_gravada_10 = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    monto_gravada_5 = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    monto_exenta = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    iva_10 = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    iva_5 = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    class Meta:
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Venta"
        unique_together = [("venta", "producto")]
        indexes = [
            models.Index(fields=["venta"], name="idx_det_venta"),
            models.Index(fields=["producto"], name="idx_det_producto"),
        ]

    def __str__(self):
        return f"{self.producto} x {self.cantidad} - ₲{self.subtotal:,.0f}"


# ==============================================================================
# PAGO (UNIFICADO)
# ==============================================================================

class PagoVenta(models.Model):
    """
    Pago recibido de un cliente.
    Puede aplicarse a una venta específica o ser un pago a cuenta corriente.
    """

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        CONCILIADO = "CONCILIADO", "Conciliado"
        RECHAZADO = "RECHAZADO", "Rechazado"
        ANULADO = "ANULADO", "Anulado"

    cliente = models.ForeignKey(
        "clientes.Cliente",
        models.PROTECT,
        related_name="pagos",
        help_text="Cliente que realiza el pago",
    )
    venta = models.ForeignKey(
        Venta,
        models.PROTECT,
        null=True,
        blank=True,
        related_name="pagos",
        help_text="Venta asociada (nulo si es pago a cuenta corriente)",
    )
    monto = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Monto pagado en Guaraníes"
    )
    monto_comision = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        help_text="Comisión por medio de pago (POS, transferencia)",
    )
    fecha = models.DateTimeField(default=timezone.now)
    referencia = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Referencia de la transacción",
    )
    ref_pago_pos = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Referencia del terminal POS",
    )
    ref_transferencia = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Comprobante de transferencia bancaria",
    )
    banco_emisor = models.CharField(
        max_length=100, blank=True, null=True
    )
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.PENDIENTE
    )
    medio_pago = models.ForeignKey(
        "core.MedioPago",
        models.PROTECT,
        related_name="pagos",
    )
    cierre_caja = models.ForeignKey(
        "contabilidad.CierreCaja",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="pagos",
    )
    cajero = models.ForeignKey(
        "usuarios.Usuario",
        models.PROTECT,
        related_name="pagos_recibidos",
    )
    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["cliente", "fecha"], name="idx_pago_cliente_fecha"),
            models.Index(fields=["venta", "fecha"], name="idx_pago_venta_fecha"),
            models.Index(fields=["estado"], name="idx_pago_estado"),
        ]

    def __str__(self):
        if self.venta:
            return f"Pago #{self.pk} - Venta #{self.venta_id} - ₲{self.monto:,.0f}"
        return f"Pago #{self.pk} - {self.cliente} (a cuenta) - ₲{self.monto:,.0f}"

    @property
    def total_cobrado(self):
        """Total cobrado al cliente (monto + comisión)."""
        return self.monto + self.monto_comision

    def anular(self):
        """
        Anula el pago y revierte sus aplicaciones.
        Recalcula el estado_pago de cada venta afectada.
        """
        if self.estado == self.Estado.ANULADO:
            raise ValidationError("El pago ya está anulado.")
        if self.estado == self.Estado.CONCILIADO:
            raise ValidationError("No se puede anular un pago conciliado.")

        with transaction.atomic():
            ventas_afectadas = list(
                self.aplicaciones.select_related("venta").values_list("venta_id", flat=True)
            )
            self.aplicaciones.all().delete()
            self.estado = self.Estado.ANULADO
            self.save(update_fields=["estado"])

            for venta in Venta.objects.filter(pk__in=ventas_afectadas):
                total = venta.total_pagado
                if total <= 0:
                    venta.estado_pago = Venta.EstadoPago.PENDIENTE
                elif total >= venta.monto_total:
                    venta.estado_pago = Venta.EstadoPago.PAGADO
                else:
                    venta.estado_pago = Venta.EstadoPago.PARCIAL
                venta.save(update_fields=["estado_pago"])


# ==============================================================================
# APLICACIÓN DE PAGOS
# ==============================================================================

class AplicacionPago(models.Model):
    """Distribución de un pago entre una o más ventas."""

    pago = models.ForeignKey(
        PagoVenta, models.CASCADE, related_name="aplicaciones"
    )
    venta = models.ForeignKey(
        Venta, models.CASCADE, related_name="aplicaciones_pago"
    )
    monto_aplicado = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Monto aplicado a esta venta"
    )

    class Meta:
        verbose_name = "Aplicación de Pago"
        verbose_name_plural = "Aplicaciones de Pagos"

    def __str__(self):
        return f"₲{self.monto_aplicado:,.0f} → Venta #{self.venta_id}"

    def clean(self):
        if self.monto_aplicado is None or self.monto_aplicado <= 0:
            raise ValidationError({"monto_aplicado": "El monto aplicado debe ser mayor a cero."})

        if self.venta_id:
            saldo = self.venta.saldo_pendiente
            if self.monto_aplicado > saldo:
                raise ValidationError(
                    {"monto_aplicado": f"El monto (₲{self.monto_aplicado:,.0f}) supera el saldo pendiente de la venta (₲{saldo:,.0f})."}
                )

        if self.pago_id:
            ya_aplicado = (
                self.pago.aplicaciones
                .exclude(pk=self.pk)
                .aggregate(total=models.Sum("monto_aplicado"))["total"]
            ) or Decimal("0")
            disponible = self.pago.monto - ya_aplicado
            if self.monto_aplicado > disponible:
                raise ValidationError(
                    {"monto_aplicado": f"El monto (₲{self.monto_aplicado:,.0f}) supera el saldo disponible del pago (₲{disponible:,.0f})."}
                )


# ==============================================================================
# NOTA DE CRÉDITO
# ==============================================================================

class NotaCredito(models.Model):
    """Nota de crédito emitida a un cliente (devolución, descuento)."""

    class Estado(models.TextChoices):
        EMITIDA = "EMITIDA", "Emitida"
        APLICADA = "APLICADA", "Aplicada"
        ANULADA = "ANULADA", "Anulada"

    cliente = models.ForeignKey(
        "clientes.Cliente", models.PROTECT, related_name="notas_credito"
    )
    venta_origen = models.ForeignKey(
        Venta,
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="notas_credito",
    )
    nro_nota_credito = models.CharField(max_length=50, unique=True)
    fecha_emision = models.DateTimeField(default=timezone.now)
    monto_total = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Monto en Guaraníes"
    )
    motivo = models.TextField()
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.EMITIDA
    )
    empleado_autoriza = models.ForeignKey(
        "usuarios.Usuario",
        models.PROTECT,
        related_name="notas_credito_autorizadas",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Nota de Crédito"
        verbose_name_plural = "Notas de Crédito"
        ordering = ["-fecha_emision"]

    def __str__(self):
        return f"NC #{self.nro_nota_credito} - {self.cliente} - ₲{self.monto_total:,.0f}"


class DetalleNotaCredito(models.Model):
    """Producto incluido en una nota de crédito."""

    nota_credito = models.ForeignKey(
        NotaCredito, models.CASCADE, related_name="detalles"
    )
    producto = models.ForeignKey(
        "productos.Producto", models.PROTECT, related_name="detalles_nc"
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    precio_unitario = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Precio en Guaraníes"
    )
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Subtotal en Guaraníes"
    )

    class Meta:
        verbose_name = "Detalle de Nota de Crédito"
        verbose_name_plural = "Detalles de Notas de Crédito"

    def __str__(self):
        return f"{self.producto} x {self.cantidad} (NC #{self.nota_credito_id})"


# ==============================================================================
# CONDICIÓN DE VENTA
# ==============================================================================

class CondicionVenta(models.Model):
    """Condición de venta (contado, crédito 30 días, etc.)."""

    nombre = models.CharField(max_length=100, unique=True)
    plazo_dias = models.IntegerField(default=0, help_text="Días de plazo para pago")

    class Meta:
        verbose_name = "Condición de Venta"
        verbose_name_plural = "Condiciones de Venta"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
