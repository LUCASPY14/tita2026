"""
Modelos de la app compras
Gestión de proveedores, compras y cuentas corrientes de proveedores
"""

from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone


# ==============================================================================
# PROVEEDOR
# ==============================================================================

class Proveedor(models.Model):
    """Proveedores de productos para la cantina."""

    id_proveedor = models.BigAutoField(primary_key=True)
    ruc = models.CharField(
        unique=True, max_length=20, help_text="RUC del proveedor"
    )
    razon_social = models.CharField(
        max_length=255, help_text="Razón social o nombre comercial"
    )
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=254, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.ForeignKey(
        "clientes.Ciudad",
        models.SET_NULL,
        blank=True,
        null=True,
        related_name="proveedores",
    )
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ["razon_social"]
        indexes = [
            models.Index(fields=["ruc"], name="idx_prov_ruc"),
        ]

    def __str__(self):
        return self.razon_social

    @property
    def saldo_cuenta_corriente(self):
        """Saldo actual con el proveedor. Positivo = deuda pendiente de pago."""
        ultimo = self.movimientos_cuenta.order_by("-id_movimiento_ccp").first()
        return ultimo.saldo_resultante if ultimo else Decimal("0")


# ==============================================================================
# CUENTA CORRIENTE DE PROVEEDORES
# ==============================================================================

class CuentaCorrienteProveedor(models.Model):
    """
    Movimientos de cuenta corriente de proveedores.
    Débito = compra a crédito (aumenta la deuda con el proveedor).
    Crédito = pago o nota de crédito (reduce la deuda).
    """

    class Tipo(models.TextChoices):
        DEBITO = "DEBITO", "Débito"        # Compra a crédito
        CREDITO = "CREDITO", "Crédito"     # Pago realizado
        NOTA_CREDITO = "NOTA_CREDITO", "Nota de Crédito"  # Devolución
        AJUSTE = "AJUSTE", "Ajuste"        # Corrección manual

    id_movimiento_ccp = models.BigAutoField(primary_key=True)
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name="movimientos_cuenta",
    )
    fecha = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=15, choices=Tipo.choices)
    monto = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Monto en Guaraníes"
    )
    saldo_anterior = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Saldo antes del movimiento"
    )
    saldo_resultante = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Saldo después del movimiento"
    )
    descripcion = models.CharField(
        max_length=255, blank=True, null=True
    )

    # Referencias a documentos origen
    compra = models.ForeignKey(
        "Compra",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_cuenta",
    )
    pago = models.ForeignKey(
        "PagoProveedor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_cuenta",
    )
    nota_credito = models.ForeignKey(
        "NotaCreditoProveedor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_cuenta",
    )

    # Auditoría
    creado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="movimientos_proveedor_creados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de Cuenta Corriente Proveedor"
        verbose_name_plural = "Cuentas Corrientes de Proveedores"
        ordering = ["-fecha", "-id_movimiento_ccp"]
        indexes = [
            models.Index(fields=["proveedor", "fecha"], name="idx_cc_prov_fecha"),
            models.Index(fields=["proveedor", "tipo"], name="idx_cc_prov_tipo"),
            models.Index(fields=["compra"], name="idx_cc_prov_compra"),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.proveedor} - ₲{self.monto:,.0f}"

    def save(self, *args, **kwargs):
        """Calcula automáticamente el saldo resultante con bloqueo pesimista."""
        with transaction.atomic():
            # Lock the proveedor row (always exists) so concurrent movements can't
            # read the same saldo_anterior — including the first concurrent movement.
            Proveedor.objects.select_for_update().get(pk=self.proveedor_id)
            ultimo = (
                CuentaCorrienteProveedor.objects
                .filter(proveedor=self.proveedor)
                .order_by("-id_movimiento_ccp")
                .first()
            )
            self.saldo_anterior = ultimo.saldo_resultante if ultimo else Decimal("0")

            if self.tipo == self.Tipo.DEBITO:
                self.saldo_resultante = self.saldo_anterior + self.monto
            elif self.tipo in (self.Tipo.CREDITO, self.Tipo.NOTA_CREDITO, self.Tipo.AJUSTE):
                self.saldo_resultante = self.saldo_anterior - self.monto

            super().save(*args, **kwargs)


# ==============================================================================
# COMPRA
# ==============================================================================

class Compra(models.Model):
    """Compra de productos a un proveedor."""

    class TipoPago(models.TextChoices):
        CONTADO = "CONTADO", "Contado"
        CREDITO = "CREDITO", "Crédito"

    class EstadoPago(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PARCIAL = "PARCIAL", "Parcial"
        PAGADO = "PAGADO", "Pagado"
        ANULADA = "ANULADA", "Anulada"

    class EstadoEntrega(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        RECIBIDA  = "RECIBIDA",  "Recibida"

    id_compra = models.BigAutoField(primary_key=True)
    proveedor = models.ForeignKey(
        Proveedor, models.PROTECT, related_name="compras"
    )
    fecha = models.DateTimeField(default=timezone.now)
    monto_total = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        help_text="Monto total en Guaraníes"
    )
    tipo_pago = models.CharField(
        max_length=10, choices=TipoPago.choices, default=TipoPago.CONTADO
    )
    estado_pago = models.CharField(
        max_length=10, choices=EstadoPago.choices, default=EstadoPago.PENDIENTE
    )
    estado_entrega = models.CharField(
        max_length=10,
        choices=EstadoEntrega.choices,
        default=EstadoEntrega.PENDIENTE,
        help_text="Estado de recepcion de la mercaderia",
    )
    nro_factura_proveedor = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="Número de factura del proveedor",
    )
    observaciones = models.TextField(blank=True, null=True)
    medio_pago = models.ForeignKey(
        "core.MedioPago",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="compras",
    )
    creado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="compras_creadas",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["proveedor", "fecha"], name="idx_compra_prov_fecha"),
            models.Index(fields=["estado_pago", "fecha"], name="idx_compra_estado_fecha"),
        ]

    def __str__(self):
        return f"Compra #{self.pk} - {self.proveedor}"

    @property
    def total_pagado(self):
        """Suma de pagos aplicados a esta compra."""
        if self.tipo_pago == self.TipoPago.CONTADO:
            return self.monto_total
        if hasattr(self, "_total_pagado"):
            return self._total_pagado
        total = self.aplicaciones_pago.aggregate(
            total=models.Sum("monto_aplicado")
        )["total"]
        return total or Decimal("0")

    @property
    def saldo_pendiente(self):
        """Saldo pendiente de pago. Las compras CONTADO siempre tienen saldo 0."""
        if self.tipo_pago == self.TipoPago.CONTADO:
            return Decimal("0")
        return self.monto_total - self.total_pagado


# ==============================================================================
# DETALLE DE COMPRA
# ==============================================================================

class DetalleCompra(models.Model):
    """Productos incluidos en una compra."""

    id_detalle_compra = models.BigAutoField(primary_key=True)
    compra = models.ForeignKey(
        Compra, models.CASCADE, related_name="detalles"
    )
    producto = models.ForeignKey(
        "productos.Producto", models.PROTECT, related_name="detalles_compra"
    )
    cantidad = models.DecimalField(
        max_digits=10, decimal_places=3, help_text="Cantidad comprada"
    )
    costo_unitario = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Costo por unidad en Guaraníes"
    )
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Subtotal en Guaraníes"
    )
    monto_iva = models.DecimalField(
        max_digits=12, decimal_places=0, default=0, help_text="IVA aplicado"
    )

    class Meta:
        verbose_name = "Detalle de Compra"
        verbose_name_plural = "Detalles de Compra"
        unique_together = [("compra", "producto")]

    def __str__(self):
        return f"{self.producto} x {self.cantidad}"


# ==============================================================================
# PAGO A PROVEEDOR
# ==============================================================================

class PagoProveedor(models.Model):
    """Pago realizado a un proveedor."""

    class Estado(models.TextChoices):
        CONCILIADO = "CONCILIADO", "Conciliado"

    id_pago_proveedor = models.BigAutoField(primary_key=True)
    proveedor = models.ForeignKey(
        Proveedor, models.PROTECT, related_name="pagos"
    )
    monto_total = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Monto total del pago en Guaraníes"
    )
    fecha = models.DateTimeField(default=timezone.now)
    referencia = models.CharField(
        max_length=100, blank=True, null=True, help_text="Nro de transferencia, cheque, etc."
    )
    observaciones = models.TextField(blank=True, null=True)
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.CONCILIADO
    )
    medio_pago = models.ForeignKey(
        "core.MedioPago",
        models.PROTECT,
        related_name="pagos_proveedores",
    )
    creado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="pagos_proveedores_creados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pago a Proveedor"
        verbose_name_plural = "Pagos a Proveedores"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Pago #{self.pk} - {self.proveedor} - ₲{self.monto_total:,.0f}"


# ==============================================================================
# APLICACIÓN DE PAGOS A COMPRAS
# ==============================================================================

class AplicacionPagoCompra(models.Model):
    """Relación entre un pago y las compras que cubre."""

    id_aplicacion_pago_compra = models.BigAutoField(primary_key=True)
    pago = models.ForeignKey(
        PagoProveedor, models.CASCADE, related_name="aplicaciones"
    )
    compra = models.ForeignKey(
        Compra, models.CASCADE, related_name="aplicaciones_pago"
    )
    monto_aplicado = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Monto aplicado a esta compra"
    )

    class Meta:
        verbose_name = "Aplicación de Pago"
        verbose_name_plural = "Aplicaciones de Pagos"
        ordering = ["id_aplicacion_pago_compra"]

    def __str__(self):
        return f"₲{self.monto_aplicado:,.0f} → Compra #{self.compra_id}"


# ==============================================================================
# NOTA DE CRÉDITO DE PROVEEDOR
# ==============================================================================

class NotaCreditoProveedor(models.Model):
    """Nota de crédito emitida por un proveedor (devolución, descuento)."""

    class Estado(models.TextChoices):
        EMITIDA = "EMITIDA", "Emitida"
        APLICADA = "APLICADA", "Aplicada"
        ANULADA = "ANULADA", "Anulada"

    class TipoNC(models.TextChoices):
        AJUSTE_PRECIO = "AJUSTE_PRECIO", "Ajuste de precio"
        DEVOLUCION = "DEVOLUCION", "Devolución de mercadería"

    id_nc_proveedor = models.BigAutoField(primary_key=True)
    proveedor = models.ForeignKey(
        Proveedor, models.PROTECT, related_name="notas_credito"
    )
    compra_original = models.ForeignKey(
        Compra,
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="notas_credito",
    )
    fecha = models.DateTimeField(default=timezone.now)
    monto_total = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Monto total en Guaraníes"
    )
    nro_factura_compra = models.CharField(
        max_length=50, blank=True, null=True, help_text="Nro de factura de la compra original"
    )
    observacion = models.CharField(max_length=255, blank=True, null=True)
    tipo_nc = models.CharField(
        max_length=20,
        choices=TipoNC.choices,
        default=TipoNC.AJUSTE_PRECIO,
        help_text="Tipo de nota de crédito",
    )
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.EMITIDA
    )
    creado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="notas_credito_proveedor_creadas",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Nota de Crédito de Proveedor"
        verbose_name_plural = "Notas de Crédito de Proveedores"
        ordering = ["-fecha"]

    def __str__(self):
        return f"NC #{self.pk} - {self.proveedor} - ₲{self.monto_total:,.0f}"


# ==============================================================================
# ORDEN DE COMPRA (OC) — workflow de aprobación
# ==============================================================================

class OrdenCompra(models.Model):
    """
    Orden de compra pre-compra que pasa por aprobación.

    Flujo: BORRADOR → PENDIENTE → APROBADA → CONVERTIDA
                               ↘ RECHAZADA
    """

    class Estado(models.TextChoices):
        BORRADOR  = "BORRADOR",   "Borrador"
        PENDIENTE = "PENDIENTE",  "Pendiente de aprobación"
        APROBADA  = "APROBADA",   "Aprobada"
        RECHAZADA = "RECHAZADA",  "Rechazada"
        CONVERTIDA = "CONVERTIDA", "Convertida en Compra"

    class TipoPago(models.TextChoices):
        CONTADO = "CONTADO", "Contado"
        CREDITO = "CREDITO", "Crédito"

    id_orden_compra = models.BigAutoField(primary_key=True)
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.PROTECT, related_name="ordenes_compra",
    )
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.BORRADOR,
    )
    tipo_pago = models.CharField(
        max_length=10, choices=TipoPago.choices, default=TipoPago.CONTADO,
    )
    monto_total = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
    )
    nro_factura_esperada = models.CharField(
        max_length=50, blank=True, null=True,
    )
    observaciones = models.TextField(blank=True, null=True)
    motivo_rechazo = models.CharField(max_length=500, blank=True, null=True)

    aprobado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="ordenes_aprobadas",
    )
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)

    compra_generada = models.OneToOneField(
        "Compra",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="orden_compra_origen",
    )

    creado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="ordenes_compra_creadas",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Orden de Compra"
        verbose_name_plural = "Órdenes de Compra"
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["proveedor", "estado"], name="idx_oc_prov_estado"),
            models.Index(fields=["estado", "fecha_creacion"], name="idx_oc_estado_fecha"),
        ]

    def __str__(self):
        return f"OC #{self.pk} — {self.proveedor} [{self.get_estado_display()}]"


class DetalleOrdenCompra(models.Model):
    """Productos incluidos en una Orden de Compra."""

    id_detalle_oc = models.BigAutoField(primary_key=True)
    orden = models.ForeignKey(
        OrdenCompra, on_delete=models.CASCADE, related_name="detalles",
    )
    producto = models.ForeignKey(
        "productos.Producto", on_delete=models.PROTECT, related_name="detalles_oc",
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    costo_unitario = models.DecimalField(max_digits=12, decimal_places=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=0)

    class Meta:
        verbose_name = "Detalle de OC"
        verbose_name_plural = "Detalles de OC"
        unique_together = [("orden", "producto")]

    def __str__(self):
        return f"{self.producto} x {self.cantidad} (OC #{self.orden_id})"


class DetalleNotaCreditoProveedor(models.Model):
    """Productos incluidos en una nota de crédito de proveedor."""

    id_detalle_ncp = models.BigAutoField(primary_key=True)
    nota_credito = models.ForeignKey(
        NotaCreditoProveedor, models.CASCADE, related_name="detalles"
    )
    producto = models.ForeignKey(
        "productos.Producto", models.PROTECT, related_name="detalles_nc_proveedor"
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    precio_unitario = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Precio en Guaraníes"
    )
    subtotal = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Subtotal en Guaraníes"
    )

    class Meta:
        verbose_name = "Detalle de NC de Proveedor"
        verbose_name_plural = "Detalles de NC de Proveedores"
        ordering = ["id_detalle_ncp"]

    def __str__(self):
        return f"{self.producto} x {self.cantidad} (NC #{self.nota_credito_id})"


# ==============================================================================
# CATÁLOGO DE PRODUCTOS POR PROVEEDOR
# ==============================================================================

class ProductoProveedor(models.Model):
    """
    Relación entre un proveedor y los productos que suministra.
    Se crea/actualiza automáticamente al confirmar la entrega de una compra.
    Almacena el último precio de compra conocido para ese proveedor.
    """

    id_producto_proveedor = models.BigAutoField(primary_key=True)
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        related_name="productos_proveedor",
    )
    producto = models.ForeignKey(
        "productos.Producto",
        on_delete=models.CASCADE,
        related_name="proveedores_producto",
    )
    precio_compra = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        help_text="Último precio de compra registrado (Gs.)",
    )
    fecha_ultima_compra = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de la última compra confirmada",
    )

    class Meta:
        verbose_name = "Producto de Proveedor"
        verbose_name_plural = "Productos de Proveedor"
        unique_together = [("proveedor", "producto")]
        ordering = ["producto__descripcion"]
        indexes = [
            models.Index(fields=["proveedor"], name="idx_pp_proveedor"),
            models.Index(fields=["producto"], name="idx_pp_producto"),
        ]

    def __str__(self):
        return f"{self.producto} — {self.proveedor} @ ₲{self.precio_compra:,.0f}"
