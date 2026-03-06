"""
Modelos de la app ventas
Gestión de ventas, pagos, notas de crédito y promociones
"""

from django.db import models
from decimal import Decimal


class Ventas(models.Model):
    """
    Registro de ventas realizadas en la cantina.
    Incluye información de facturación, estado de pago y cliente.
    """

    id_venta = models.BigAutoField(primary_key=True)
    nro_factura_venta = models.BigIntegerField(
        blank=True, null=True, help_text="Número de factura legal"
    )
    fecha = models.DateTimeField(auto_now_add=True, help_text="Fecha y hora de la venta")
    monto_total = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Monto total de la venta"
    )
    saldo_pendiente = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        default=0,
        help_text="Saldo pendiente de pago",
    )
    estado_pago = models.CharField(max_length=10, help_text="Ej: Pagada, Pendiente, Parcial")
    estado = models.CharField(max_length=10, help_text="Ej: Activa, Cancelada, Anulada")
    tipo_venta = models.CharField(max_length=20, help_text="Ej: Contado, Crédito")
    motivo_credito = models.TextField(blank=True, null=True)
    genera_factura_legal = models.BooleanField(
        default=False, help_text="1 si genera factura electrónica"
    )
    autorizado_por = models.ForeignKey(
        "usuarios.Empleados",
        models.DO_NOTHING,
        db_column="autorizado_por",
        blank=True,
        null=True,
        related_name="ventas_autorizadas",
    )
    id_cliente = models.ForeignKey(
        "clientes.Clientes", models.DO_NOTHING, db_column="id_cliente", related_name="ventas"
    )
    id_empleado_cajero = models.ForeignKey(
        "usuarios.Empleados",
        models.DO_NOTHING,
        db_column="id_empleado_cajero",
        related_name="ventas_realizadas",
    )
    id_hijo = models.ForeignKey(
        "clientes.Hijos",
        models.DO_NOTHING,
        db_column="id_hijo",
        blank=True,
        null=True,
        related_name="ventas",
    )
    id_medio_pago = models.ForeignKey(
        "core.MediosPago",
        models.DO_NOTHING,
        db_column="id_medio_pago",
        blank=True,
        null=True,
        related_name="ventas",
    )
    id_documento = models.ForeignKey(
        "contabilidad.DocumentosTributarios",
        models.DO_NOTHING,
        db_column="id_documento",
        blank=True,
        null=True,
        related_name="ventas",
    )

    class Meta:
        managed = True
        db_table = "ventas"
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Venta #{self.id_venta} - {self.id_cliente} (${self.monto_total})"

    @property
    def esta_pagada(self):
        """Verifica si la venta está completamente pagada"""
        return self.saldo_pendiente == 0 or self.estado_pago.lower() == "pagada"

    @property
    def monto_pagado(self):
        """Calcula el monto ya pagado"""
        if self.saldo_pendiente:
            return self.monto_total - self.saldo_pendiente
        return self.monto_total


class DetallesVenta(models.Model):
    id_detalle = models.BigAutoField(primary_key=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    id_producto = models.ForeignKey(
        "productos.Productos", models.DO_NOTHING, db_column="id_producto"
    )
    id_venta = models.ForeignKey("Ventas", models.DO_NOTHING, db_column="id_venta")

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "detalles_venta"
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Venta"
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Venta"
        unique_together = (("id_venta", "id_producto"),)


class PagosVenta(models.Model):
    id_pago_venta = models.BigAutoField(primary_key=True)
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Monto de productos (base facturada, sin comisión)",
    )
    monto_comision = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Recargo por uso de POS (NO facturado, trasladado al cliente)",
    )
    referencia_transaccion = models.CharField(max_length=100, blank=True, null=True)
    fecha_pago = models.DateTimeField()
    estado = models.CharField(max_length=10)
    id_cierre = models.BigIntegerField(blank=True, null=True)
    id_medio_pago = models.ForeignKey(
        "core.MediosPago", models.DO_NOTHING, db_column="id_medio_pago"
    )
    nro_tarjeta_usada = models.ForeignKey(
        "core.Tarjetas", models.DO_NOTHING, db_column="nro_tarjeta_usada", blank=True, null=True
    )
    id_venta = models.ForeignKey("Ventas", models.DO_NOTHING, db_column="id_venta")

    @property
    def total_cobrado(self):
        """Total cobrado al cliente (monto + comisión)"""
        return self.monto + self.monto_comision

    @property
    def porcentaje_comision_aplicado(self):
        """Calcula el % de comisión aplicado"""
        if self.monto > 0:
            return (self.monto_comision / self.monto) * 100
        return Decimal("0.00")

    def __str__(self):
        return f"Pago #{self.id_pago_venta} - Gs. {self.total_cobrado:,.0f} ({self.id_medio_pago})"

    class Meta:
        managed = True
        db_table = "pagos_venta"
        verbose_name = "Pago de Venta"
        verbose_name_plural = "Pagos de Venta"


class AplicacionPagosVentas(models.Model):
    id_aplicacion = models.BigAutoField(primary_key=True)
    monto_aplicado = models.DecimalField(max_digits=12, decimal_places=2)
    id_pago_venta = models.ForeignKey("PagosVenta", models.DO_NOTHING, db_column="id_pago_venta")
    id_venta = models.ForeignKey("Ventas", models.DO_NOTHING, db_column="id_venta")

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "aplicacion_pagos_ventas"
        verbose_name = "Aplicación de Pago"
        verbose_name_plural = "Aplicaciones de Pagos"
        verbose_name = "Aplicación de Pago"
        verbose_name_plural = "Aplicaciones de Pagos"


class NotasCreditoCliente(models.Model):
    id_nota = models.BigAutoField(primary_key=True)
    nro_nota_credito = models.BigIntegerField()
    fecha_emision = models.DateTimeField()
    motivo = models.TextField()
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=10)
    id_cliente = models.ForeignKey("clientes.Clientes", models.DO_NOTHING, db_column="id_cliente")
    id_empleado_autoriza = models.ForeignKey(
        "usuarios.Empleados", models.DO_NOTHING, db_column="id_empleado_autoriza"
    )
    id_venta_origen = models.ForeignKey(
        "Ventas", models.DO_NOTHING, db_column="id_venta_origen", blank=True, null=True
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "notas_credito_cliente"
        verbose_name = "Nota de Crédito"
        verbose_name_plural = "Notas de Crédito"
        verbose_name = "Nota de Crédito"
        verbose_name_plural = "Notas de Crédito"


class DetallesNotaCredito(models.Model):
    id_detalle_nota = models.BigAutoField(primary_key=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    id_nota = models.ForeignKey("NotasCreditoCliente", models.DO_NOTHING, db_column="id_nota")
    id_producto = models.ForeignKey(
        "productos.Productos", models.DO_NOTHING, db_column="id_producto"
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "detalles_nota_credito"
        verbose_name = "Detalle de Nota de Crédito"
        verbose_name_plural = "Detalles de Notas de Crédito"
        verbose_name = "Detalle de Nota de Crédito"
        verbose_name_plural = "Detalles de Notas de Crédito"


class Promociones(models.Model):
    id_promocion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    tipo_promocion = models.CharField(max_length=25)
    valor_descuento = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)
    dias_semana = models.JSONField(blank=True, null=True)
    aplica_a = models.CharField(max_length=20)
    min_cantidad = models.IntegerField()
    monto_minimo = models.DecimalField(max_digits=10, decimal_places=2)
    max_usos_cliente = models.IntegerField(blank=True, null=True)
    max_usos_total = models.IntegerField(blank=True, null=True)
    usos_actuales = models.IntegerField()
    requiere_codigo = models.BooleanField(default=True)
    codigo_promocion = models.CharField(unique=True, max_length=50, blank=True, null=True)
    prioridad = models.IntegerField()
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField()
    usuario_creacion = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "promociones"
        verbose_name = "Promoción"
        verbose_name_plural = "Promociones"
        verbose_name = "Promoción"
        verbose_name_plural = "Promociones"


class CategoriasPromocion(models.Model):
    id_categoria_promocion = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey(
        "productos.Categorias", models.DO_NOTHING, db_column="id_categoria"
    )
    id_promocion = models.ForeignKey("Promociones", models.DO_NOTHING, db_column="id_promocion")

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "categorias_promocion"
        verbose_name = "Categoría en Promoción"
        verbose_name_plural = "Categorías en Promociones"
        verbose_name = "Categoría en Promoción"
        verbose_name_plural = "Categorías en Promociones"
        unique_together = (("id_promocion", "id_categoria"),)


class ProductosPromocion(models.Model):
    id_producto_promocion = models.AutoField(primary_key=True)
    id_producto = models.ForeignKey(
        "productos.Productos", models.DO_NOTHING, db_column="id_producto"
    )
    id_promocion = models.ForeignKey("Promociones", models.DO_NOTHING, db_column="id_promocion")

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "productos_promocion"
        verbose_name = "Producto en Promoción"
        verbose_name_plural = "Productos en Promociones"
        verbose_name = "Producto en Promoción"
        verbose_name_plural = "Productos en Promociones"
        unique_together = (("id_promocion", "id_producto"),)


class PromocionesAplicadas(models.Model):
    id_aplicacion = models.AutoField(primary_key=True)
    monto_descontado = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_aplicacion = models.DateTimeField()
    id_promocion = models.ForeignKey("Promociones", models.DO_NOTHING, db_column="id_promocion")
    id_venta = models.ForeignKey("Ventas", models.DO_NOTHING, db_column="id_venta")

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "promociones_aplicadas"
        verbose_name = "Promoción Aplicada"
        verbose_name_plural = "Promociones Aplicadas"
        verbose_name = "Promoción Aplicada"
        verbose_name_plural = "Promociones Aplicadas"
