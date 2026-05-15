"""
Modelos de la app contabilidad
Gestión de cajas, cierres, movimientos, facturación y comisiones
"""

from decimal import Decimal

from django.db import models
from django.utils import timezone


# ==============================================================================
# CAJA
# ==============================================================================

class Caja(models.Model):
    """Caja registradora o punto de venta físico."""

    nombre = models.CharField(max_length=50)
    ubicacion = models.CharField(max_length=100, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"

    def __str__(self):
        return self.nombre


# ==============================================================================
# CIERRE DE CAJA
# ==============================================================================

class CierreCaja(models.Model):
    """Cierre diario de caja con arqueo."""

    class Estado(models.TextChoices):
        ABIERTO = "ABIERTO", "Abierto"
        CERRADO = "CERRADO", "Cerrado"
        CONCILIADO = "CONCILIADO", "Conciliado"

    caja = models.ForeignKey(
        Caja, models.PROTECT, related_name="cierres"
    )
    empleado = models.ForeignKey(
        "usuarios.Usuario", models.PROTECT, related_name="cierres_caja"
    )
    fecha_apertura = models.DateTimeField(default=timezone.now)
    fecha_cierre = models.DateTimeField(blank=True, null=True)
    monto_inicial = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        help_text="Monto en Guaraníes al abrir la caja",
    )
    monto_contado_fisico = models.DecimalField(
        max_digits=12, decimal_places=0, blank=True, null=True,
        help_text="Monto contado al cerrar",
    )
    diferencia_efectivo = models.DecimalField(
        max_digits=12, decimal_places=0, blank=True, null=True,
        help_text="Diferencia entre lo esperado y lo contado",
    )
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.ABIERTO
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cierre de Caja"
        verbose_name_plural = "Cierres de Caja"
        ordering = ["-fecha_apertura"]
        indexes = [
            models.Index(fields=["caja", "fecha_apertura"]),
            models.Index(fields=["empleado", "fecha_apertura"]),
            models.Index(fields=["estado"]),
        ]

    def __str__(self):
        return f"Cierre #{self.pk} - {self.caja} ({self.get_estado_display()})"


# ==============================================================================
# MOVIMIENTO DE CAJA
# ==============================================================================

class MovimientoCaja(models.Model):
    """Movimiento de dinero dentro de un cierre de caja."""

    class Tipo(models.TextChoices):
        INGRESO = "INGRESO", "Ingreso"
        EGRESO = "EGRESO", "Egreso"

    cierre = models.ForeignKey(
        CierreCaja, models.PROTECT,
        null=True, blank=True,
        related_name="movimientos",
    )
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    monto = models.DecimalField(max_digits=12, decimal_places=0)
    monto_comision = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        help_text="Comisión del medio de pago",
    )
    fecha = models.DateTimeField(default=timezone.now)
    descripcion = models.CharField(max_length=200, blank=True, null=True)
    medio_pago = models.ForeignKey(
        "core.MedioPago", models.PROTECT, related_name="movimientos_caja"
    )
    venta = models.ForeignKey(
        "ventas.Venta",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_caja",
    )

    class Meta:
        verbose_name = "Movimiento de Caja"
        verbose_name_plural = "Movimientos de Caja"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["cierre", "fecha"]),
            models.Index(fields=["venta"]),
            models.Index(fields=["fecha", "tipo"]),
        ]

    def __str__(self):
        signo = "+" if self.tipo == self.Tipo.INGRESO else "-"
        return f"{signo}₲{self.monto:,.0f} - {self.descripcion or self.get_tipo_display()}"


# ==============================================================================
# CONCILIACIÓN DE PAGOS
# ==============================================================================

class ConciliacionPago(models.Model):
    """Conciliación entre un pago registrado y el extracto bancario."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        CONCILIADO = "CONCILIADO", "Conciliado"
        DISCREPANCIA = "DISCREPANCIA", "Discrepancia"

    pago_venta = models.OneToOneField(
        "ventas.PagoVenta",
        models.PROTECT,
        related_name="conciliacion",
    )
    fecha_acreditacion = models.DateTimeField(blank=True, null=True)
    fecha_conciliacion = models.DateTimeField(default=timezone.now)
    monto_acreditado = models.DecimalField(
        max_digits=12, decimal_places=0, blank=True, null=True,
        help_text="Monto en extracto bancario",
    )
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.PENDIENTE
    )
    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Conciliación de Pago"
        verbose_name_plural = "Conciliaciones de Pagos"
        ordering = ["-fecha_conciliacion"]

    def __str__(self):
        return f"Conciliación #{self.pk} - Pago #{self.pago_venta_id}"



# ==============================================================================
# FACTURA (PAPEL PREIMPRESO)
# ==============================================================================

class Factura(models.Model):
    """Factura en papel preimpreso con numeración controlada."""

    class Estado(models.TextChoices):
        EMITIDA = "EMITIDA", "Emitida"
        ANULADA = "ANULADA", "Anulada"

    nro_factura = models.CharField(
        max_length=20, unique=True,
        help_text="Número preimpreso (ej: 001-001-0001234)",
    )
    fecha_emision = models.DateTimeField(default=timezone.now)
    monto_total = models.DecimalField(max_digits=12, decimal_places=0)
    iva_10 = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    iva_5 = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    monto_exenta = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    estado = models.CharField(
        max_length=10, choices=Estado.choices, default=Estado.EMITIDA
    )
    venta = models.OneToOneField(
        "ventas.Venta",
        models.PROTECT,
        null=True,
        blank=True,
        related_name="factura_venta",
        help_text="Venta asociada a esta factura",
    )
    cliente = models.ForeignKey(
        "clientes.Cliente",
        models.PROTECT,
        related_name="facturas",
    )
    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ["-fecha_emision"]

    def __str__(self):
        return f"Factura {self.nro_factura} - ₲{self.monto_total:,.0f}"


# ==============================================================================
# DATOS DE LA EMPRESA
# ==============================================================================

class DatosEmpresa(models.Model):
    """Datos fiscales de la cantina para emisión de documentos."""

    ruc = models.CharField(max_length=20)
    razon_social = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True, default="Paraguay")
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Datos de Empresa"
        verbose_name_plural = "Datos de Empresa"

    def __str__(self):
        return f"{self.razon_social} - RUC {self.ruc}"
