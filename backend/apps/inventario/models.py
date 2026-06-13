"""
Modelos de la app inventario
Gestión de stock, movimientos, lotes, ajustes y costos
"""

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


# ==============================================================================
# STOCK (INVENTARIO ACTUAL)
# ==============================================================================

class Stock(models.Model):
    """
    Inventario actual de cada producto.
    Un solo registro por producto (OneToOne).
    """

    producto = models.OneToOneField(
        "productos.Producto",
        models.PROTECT,
        related_name="stock",
        help_text="Producto asociado",
    )
    cantidad = models.DecimalField(
        max_digits=10, decimal_places=3, default=0,
        help_text="Stock actual disponible",
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"
        indexes = [
            models.Index(fields=["producto"]),
            models.Index(fields=["-fecha_actualizacion"]),
        ]

    def __str__(self):
        return f"{self.producto}: {self.cantidad}"

    @property
    def costo_promedio(self):
        """Costo promedio ponderado basado en compras históricas."""
        costos = self.producto.costos_historicos.aggregate(
            total_monto=models.Sum(
                models.F("costo_unitario") * models.F("cantidad_comprada")
            ),
            total_cantidad=models.Sum("cantidad_comprada"),
        )
        if costos["total_cantidad"] and costos["total_cantidad"] > 0:
            return (costos["total_monto"] / costos["total_cantidad"]).quantize(Decimal("1"))
        return Decimal("0")

    @property
    def valor_inventario(self):
        return (self.cantidad * self.costo_promedio).quantize(Decimal("1"))

    @property
    def requiere_reposicion(self):
        return self.cantidad <= self.producto.stock_minimo

    @property
    def dias_stock_disponible(self):
        """Días estimados de stock según venta promedio de 30 días."""
        hace_30_dias = timezone.now() - timedelta(days=30)
        ventas_mes = MovimientoStock.objects.filter(
            producto=self.producto,
            tipo=MovimientoStock.Tipo.EGRESO,
            fecha__gte=hace_30_dias,
        ).aggregate(total=models.Sum("cantidad"))["total"] or Decimal("0")

        if ventas_mes > 0:
            venta_diaria = ventas_mes / 30
            if venta_diaria > 0:
                return int(self.cantidad / venta_diaria)
        return None

    def clean(self):
        if self.cantidad < 0 and not self.producto.permite_stock_negativo:
            raise ValidationError({
                "cantidad": f"{self.producto} no permite stock negativo."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ==============================================================================
# MOVIMIENTO DE STOCK
# ==============================================================================

class MovimientoStock(models.Model):
    """Historial de todos los movimientos de inventario."""

    class Tipo(models.TextChoices):
        INGRESO = "INGRESO", "Ingreso"
        EGRESO = "EGRESO", "Egreso"

    class Motivo(models.TextChoices):
        COMPRA = "COMPRA", "Compra a proveedor"
        VENTA = "VENTA", "Venta a cliente"
        AJUSTE_AUMENTO = "AJUSTE_AUMENTO", "Ajuste de inventario (aumento)"
        AJUSTE_MERMA = "AJUSTE_MERMA", "Ajuste de inventario (merma)"
        DEVOLUCION_CLIENTE = "DEVOLUCION_CLIENTE", "Devolución de cliente"
        DEVOLUCION_PROVEEDOR = "DEVOLUCION_PROVEEDOR", "Devolución a proveedor"
        CORRECCION = "CORRECCION", "Corrección manual"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
        VENCIDO = "VENCIDO", "Baja por vencimiento"
        DANADO = "DANADO", "Baja por daño"
        INVENTARIO_INICIAL = "INVENTARIO_INICIAL", "Inventario inicial"

    producto = models.ForeignKey(
        "productos.Producto",
        models.PROTECT,
        related_name="movimientos_stock",
    )
    fecha = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    motivo = models.CharField(max_length=25, choices=Motivo.choices)
    cantidad = models.DecimalField(
        max_digits=10, decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
        help_text="Cantidad (siempre positiva)",
    )
    stock_resultante = models.DecimalField(
        max_digits=10, decimal_places=3,
        help_text="Stock después del movimiento",
    )
    observaciones = models.TextField(blank=True, null=True)

    # Referencias a documentos origen
    compra = models.ForeignKey(
        "compras.Compra",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_stock",
    )
    venta = models.ForeignKey(
        "ventas.Venta",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_stock",
    )
    ajuste = models.ForeignKey(
        "AjusteInventario",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos",
    )

    # Auditoría
    autorizado_por = models.ForeignKey(
        "usuarios.Usuario",
        models.PROTECT,
        related_name="movimientos_stock_autorizados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de Stock"
        verbose_name_plural = "Movimientos de Stock"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["producto", "-fecha"]),
            models.Index(fields=["tipo", "motivo"]),
            models.Index(fields=["-fecha"]),
        ]

    def __str__(self):
        signo = "+" if self.tipo == self.Tipo.INGRESO else "-"
        return f"{self.producto}: {signo}{self.cantidad} ({self.get_motivo_display()})"

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError({"cantidad": "La cantidad debe ser mayor a cero."})

        motivos_ingreso = [
            self.Motivo.COMPRA,
            self.Motivo.AJUSTE_AUMENTO,
            self.Motivo.DEVOLUCION_CLIENTE,
            self.Motivo.INVENTARIO_INICIAL,
            self.Motivo.TRANSFERENCIA,
        ]
        motivos_egreso = [
            self.Motivo.VENTA,
            self.Motivo.AJUSTE_MERMA,
            self.Motivo.DEVOLUCION_PROVEEDOR,
            self.Motivo.VENCIDO,
            self.Motivo.DANADO,
        ]

        if self.tipo == self.Tipo.INGRESO and self.motivo in motivos_egreso:
            raise ValidationError({
                "motivo": f"Motivo '{self.get_motivo_display()}' no válido para Ingreso."
            })
        if self.tipo == self.Tipo.EGRESO and self.motivo in motivos_ingreso:
            raise ValidationError({
                "motivo": f"Motivo '{self.get_motivo_display()}' no válido para Egreso."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ==============================================================================
# AJUSTE DE INVENTARIO
# ==============================================================================

class AjusteInventario(models.Model):
    """Ajuste manual de inventario (aumento o merma)."""

    class TipoAjuste(models.TextChoices):
        AUMENTO = "AUMENTO", "Aumento de stock"
        MERMA = "MERMA", "Disminución de stock"

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        APROBADO = "APROBADO", "Aprobado"
        RECHAZADO = "RECHAZADO", "Rechazado"

    fecha = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=10, choices=TipoAjuste.choices)
    motivo = models.CharField(max_length=255, help_text="Razón del ajuste")
    estado = models.CharField(
        max_length=10, choices=Estado.choices, default=Estado.PENDIENTE
    )
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    solicitado_por = models.ForeignKey(
        "usuarios.Usuario",
        models.PROTECT,
        null=True,
        blank=True,
        related_name="ajustes_solicitados",
    )
    aprobado_por = models.ForeignKey(
        "usuarios.Usuario",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="ajustes_aprobados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Ajuste de Inventario"
        verbose_name_plural = "Ajustes de Inventario"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Ajuste #{self.pk} - {self.get_tipo_display()} ({self.get_estado_display()})"


class DetalleAjuste(models.Model):
    """Producto incluido en un ajuste de inventario."""

    ajuste = models.ForeignKey(
        AjusteInventario, models.CASCADE, related_name="detalles"
    )
    producto = models.ForeignKey(
        "productos.Producto", models.PROTECT, related_name="detalles_ajuste"
    )
    cantidad = models.DecimalField(
        max_digits=10, decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
        help_text="Cantidad a ajustar (siempre positiva)",
    )
    movimiento_stock = models.OneToOneField(
        MovimientoStock,
        models.SET_NULL,
        null=True,
        blank=True,
        help_text="Movimiento generado al aprobar",
    )

    class Meta:
        verbose_name = "Detalle de Ajuste"
        verbose_name_plural = "Detalles de Ajustes"
        unique_together = [("ajuste", "producto")]

    def __str__(self):
        return f"{self.producto}: {self.cantidad}"


# ==============================================================================
# COSTO HISTÓRICO
# ==============================================================================

class CostoHistorico(models.Model):
    """Historial de costos de compra para cálculo de costo promedio."""

    producto = models.ForeignKey(
        "productos.Producto",
        models.PROTECT,
        related_name="costos_historicos",
    )
    compra = models.ForeignKey(
        "compras.Compra",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="costos_productos",
    )
    costo_unitario = models.DecimalField(
        max_digits=12, decimal_places=0,
        help_text="Costo por unidad en Guaraníes",
    )
    cantidad_comprada = models.DecimalField(
        max_digits=10, decimal_places=3, default=Decimal("1.000"),
    )
    fecha_compra = models.DateTimeField()

    class Meta:
        verbose_name = "Costo Histórico"
        verbose_name_plural = "Costos Históricos"
        ordering = ["-fecha_compra"]
        indexes = [
            models.Index(fields=["producto", "-fecha_compra"]),
        ]

    def __str__(self):
        return f"{self.producto}: ₲{self.costo_unitario:,.0f} ({self.fecha_compra.date()})"

    @property
    def costo_total(self):
        return (self.costo_unitario * self.cantidad_comprada).quantize(Decimal("1"))


# ==============================================================================
# ALERTA DE STOCK
# ==============================================================================

class AlertaStock(models.Model):
    """Alerta cuando el stock está por debajo del mínimo."""

    class TipoAlerta(models.TextChoices):
        STOCK_MINIMO = "STOCK_MINIMO", "Stock bajo el mínimo"
        STOCK_CERO = "STOCK_CERO", "Stock agotado"
        STOCK_CRITICO = "STOCK_CRITICO", "Stock crítico (50% del mínimo)"

    producto = models.ForeignKey(
        "productos.Producto",
        models.PROTECT,
        related_name="alertas_stock",
    )
    tipo = models.CharField(max_length=15, choices=TipoAlerta.choices)
    stock_actual = models.DecimalField(max_digits=10, decimal_places=3)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=3)
    activa = models.BooleanField(default=True)
    notificacion_enviada = models.BooleanField(default=False)
    fecha_generada = models.DateTimeField(auto_now_add=True)
    fecha_resuelta = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Alerta de Stock"
        verbose_name_plural = "Alertas de Stock"
        ordering = ["-fecha_generada"]
        indexes = [
            models.Index(fields=["producto", "activa"]),
            models.Index(fields=["-fecha_generada"]),
        ]

    def __str__(self):
        estado = "Activa" if self.activa else "Resuelta"
        return f"{self.producto}: {self.get_tipo_display()} - {estado}"


# ==============================================================================
# LOTE DE PRODUCTO
# ==============================================================================

class LoteProducto(models.Model):
    """Lote de producto con fecha de vencimiento (FIFO)."""

    class MotivoBloqueo(models.TextChoices):
        VENCIDO = "VENCIDO", "Producto vencido"
        DEFECTUOSO = "DEFECTUOSO", "Lote defectuoso"
        RETIRADO = "RETIRADO", "Retiro preventivo"
        OTRO = "OTRO", "Otro motivo"

    producto = models.ForeignKey(
        "productos.Producto", models.PROTECT, related_name="lotes"
    )
    compra = models.ForeignKey(
        "compras.Compra",
        models.SET_NULL,
        null=True,
        blank=True,
        help_text="Compra origen del lote",
    )
    numero_lote = models.CharField(max_length=100)
    fecha_fabricacion = models.DateField(blank=True, null=True)
    fecha_vencimiento = models.DateField()
    cantidad_inicial = models.DecimalField(max_digits=10, decimal_places=3)
    cantidad_disponible = models.DecimalField(max_digits=10, decimal_places=3)
    bloqueado = models.BooleanField(default=False)
    motivo_bloqueo = models.CharField(
        max_length=15, choices=MotivoBloqueo.choices, blank=True, null=True
    )
    fecha_bloqueo = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Lote de Producto"
        verbose_name_plural = "Lotes de Productos"
        ordering = ["fecha_vencimiento"]  # FIFO
        indexes = [
            models.Index(fields=["producto", "fecha_vencimiento"]),
            models.Index(fields=["fecha_vencimiento", "bloqueado"]),
            models.Index(fields=["numero_lote"]),
        ]

    def __str__(self):
        estado = "Bloqueado" if self.bloqueado else "Disponible"
        return f"Lote {self.numero_lote} - {self.producto} ({estado})"

    @property
    def dias_hasta_vencimiento(self):
        if not self.fecha_vencimiento:
            return None
        return (self.fecha_vencimiento - timezone.now().date()).days

    @property
    def esta_vencido(self):
        return self.dias_hasta_vencimiento is not None and self.dias_hasta_vencimiento < 0

    @property
    def proximo_a_vencer(self):
        dias = self.dias_hasta_vencimiento
        return dias is not None and 0 <= dias <= 30

    def clean(self):
        if self.fecha_fabricacion and self.fecha_vencimiento:
            if self.fecha_vencimiento <= self.fecha_fabricacion:
                raise ValidationError({
                    "fecha_vencimiento": "Debe ser posterior a la fecha de fabricación."
                })
        if self.cantidad_disponible > self.cantidad_inicial:
            raise ValidationError({
                "cantidad_disponible": "No puede ser mayor a la cantidad inicial."
            })
        if self.bloqueado and not self.motivo_bloqueo:
            raise ValidationError({"motivo_bloqueo": "Debe especificar el motivo."})


# ==============================================================================
# ALERTA DE VENCIMIENTO
# ==============================================================================

class AlertaVencimiento(models.Model):
    """Alerta de productos próximos a vencer."""

    class TipoAlerta(models.TextChoices):
        DIAS_30 = "30_DIAS", "30 días para vencer"
        DIAS_15 = "15_DIAS", "15 días para vencer"
        DIAS_7 = "7_DIAS", "7 días para vencer"
        DIAS_3 = "3_DIAS", "3 días para vencer"
        VENCIDO = "VENCIDO", "Producto vencido"

    class Accion(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        DESCUENTO = "DESCUENTO", "Descuento aplicado"
        DEVUELTO = "DEVUELTO", "Devuelto a proveedor"
        DONADO = "DONADO", "Donado"
        DESCARTADO = "DESCARTADO", "Descartado"
        VENDIDO = "VENDIDO", "Vendido a tiempo"

    lote = models.ForeignKey(
        LoteProducto, models.CASCADE, related_name="alertas"
    )
    tipo = models.CharField(max_length=10, choices=TipoAlerta.choices)
    dias_restantes = models.IntegerField()
    fecha_vencimiento = models.DateField()
    cantidad_lote = models.DecimalField(max_digits=10, decimal_places=3)
    accion_tomada = models.CharField(
        max_length=15, choices=Accion.choices, default=Accion.PENDIENTE,
        null=True, blank=True,
    )
    fecha_accion = models.DateTimeField(null=True, blank=True)
    responsable = models.ForeignKey(
        "usuarios.Usuario",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="alertas_vencimiento",
    )
    notificacion_enviada = models.BooleanField(default=False)
    fecha_generada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Alerta de Vencimiento"
        verbose_name_plural = "Alertas de Vencimiento"
        ordering = ["fecha_vencimiento", "-fecha_generada"]
        indexes = [
            models.Index(fields=["lote", "tipo"]),
            models.Index(fields=["fecha_vencimiento"]),
            models.Index(fields=["accion_tomada"]),
        ]

    def __str__(self):
        return f"{self.lote} - {self.get_tipo_display()}"
