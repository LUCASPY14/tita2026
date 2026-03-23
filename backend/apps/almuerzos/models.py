"""
Modelos de la app almuerzos
Auto-generados desde la base de datos y organizados por funcionalidad
"""

from django.db import models


class PrecioAlmuerzo(models.Model):
    """Historial de precios unitarios del almuerzo con vigencia."""

    TIPO_CHOICES = [
        ("precio_unitario", "Precio Unitario"),
    ]

    id_precio = models.AutoField(primary_key=True)
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Precio por almuerzo en guaraníes"
    )
    fecha_inicio_vigencia = models.DateField(help_text="Fecha desde la cual aplica este precio")
    fecha_fin_vigencia = models.DateField(
        blank=True, null=True, help_text="Fecha hasta la cual aplica (vacío = sin vencimiento)"
    )
    descripcion = models.CharField(
        max_length=200, blank=True, help_text="Ej: Ajuste por inflación 2026"
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Precio almuerzo: Gs {self.precio_unitario} ({self.fecha_inicio_vigencia})"

    class Meta:
        managed = True
        db_table = "precios_almuerzo"
        ordering = ["-fecha_inicio_vigencia"]


class PlanesAlmuerzo(models.Model):
    TIPO_PLAN_CHOICES = [
        ("cantidad", "Mensual con cantidad de almuerzos"),
        ("sin_limite", "Mensual sin límite (cuenta corriente)"),
    ]

    id_plan_almuerzo = models.AutoField(primary_key=True)
    nombre_plan = models.CharField(unique=True, max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio_mensual = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Precio mensual fijo (solo referencia para facturación global)"
    )
    tipo_plan = models.CharField(
        max_length=20,
        choices=TIPO_PLAN_CHOICES,
        default="sin_limite",
        help_text="sin_limite: se registra consumo y se cobra al final del mes. cantidad: tiene cuota mensual de almuerzos.",
    )
    cantidad_almuerzos_mes = models.IntegerField(
        blank=True,
        null=True,
        help_text="Solo para tipo=cantidad: máximo de almuerzos incluidos por mes",
    )
    limite_credito_mensual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Monto máximo acumulable en la cuenta corriente por mes. Null = sin límite.",
    )
    dias_semana_incluidos = models.CharField(max_length=60)
    fecha_creacion = models.DateTimeField(blank=True, null=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "planes_almuerzo"


class TiposAlmuerzo(models.Model):
    id_tipo_almuerzo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    incluye_plato_principal = models.BooleanField(default=True, help_text="Incluye plato principal")
    incluye_postre = models.BooleanField(default=False, help_text="Incluye postre")
    incluye_bebida = models.BooleanField(default=False, help_text="Incluye bebida")
    fecha_creacion = models.DateTimeField()
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "tipos_almuerzo"


class SuscripcionesAlmuerzo(models.Model):
    id_suscripcion = models.BigAutoField(primary_key=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=10, blank=True, null=True)
    id_hijo = models.ForeignKey("clientes.Hijos", models.DO_NOTHING, db_column="id_hijo")
    id_plan_almuerzo = models.ForeignKey(
        "PlanesAlmuerzo", models.DO_NOTHING, db_column="id_plan_almuerzo"
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "suscripciones_almuerzo"
        unique_together = (("id_hijo", "id_plan_almuerzo", "estado"),)


class RegistrosConsumoAlmuerzo(models.Model):
    id_registro_consumo = models.BigAutoField(primary_key=True)
    fecha_consumo = models.DateField()
    hora_registro = models.TimeField()
    costo_almuerzo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ya_cobrado = models.BooleanField(
        default=True,
        help_text="Indica si este registro generó cobro de saldo. El primer registro del día cobra (True), el segundo no cobra (False)",
    )
    marcado_en_cuenta = models.BooleanField(
        default=False,
        help_text="Indica si el consumo se agregó a la cuenta mensual de almuerzo (NO relacionado con saldo de cantina)",
    )
    estado = models.CharField(max_length=20)
    motivo_rechazo = models.CharField(max_length=255, blank=True, null=True)
    id_hijo = models.ForeignKey("clientes.Hijos", models.DO_NOTHING, db_column="id_hijo")
    id_suscripcion = models.ForeignKey(
        "SuscripcionesAlmuerzo",
        models.DO_NOTHING,
        db_column="id_suscripcion",
        blank=True,
        null=True,
    )
    id_tipo_almuerzo = models.ForeignKey(
        "TiposAlmuerzo", models.DO_NOTHING, db_column="id_tipo_almuerzo", blank=True, null=True
    )
    nro_tarjeta = models.ForeignKey(
        "core.Tarjetas", models.DO_NOTHING, db_column="nro_tarjeta", blank=True, null=True
    )
    id_empleado_registro = models.ForeignKey(
        "usuarios.Empleados",
        models.DO_NOTHING,
        db_column="id_empleado_registro",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "registros_consumo_almuerzo"


class CuentasAlmuerzoMensual(models.Model):
    ESTADO_CHOICES = [
        ("pendiente", "Pendiente"),
        ("validacion_pendiente", "Validación Pendiente"),
        ("pagado", "Pagado"),
        ("parcial", "Parcial"),
        ("anulado", "Anulado"),
    ]

    FORMA_PAGO_CHOICES = [
        ("efectivo", "Efectivo"),
        ("transferencia", "Transferencia bancaria"),
        ("online", "Pago online"),
        ("debito_automatico", "Débito automático"),
    ]

    id_cuenta = models.BigAutoField(primary_key=True)
    anio = models.IntegerField()
    mes = models.SmallIntegerField()
    cantidad_almuerzos = models.IntegerField()
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    forma_cobro = models.CharField(max_length=20)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=25, default="pendiente")
    fecha_generacion = models.DateField()
    fecha_actualizacion = models.DateTimeField()
    observaciones = models.TextField(blank=True, null=True)
    # Campos de pago
    forma_pago = models.CharField(
        max_length=25, blank=True, choices=FORMA_PAGO_CHOICES,
        help_text="Método de pago utilizado"
    )
    comprobante_pago = models.TextField(
        blank=True,
        help_text="Referencia, URL o descripción del comprobante de pago"
    )
    fecha_pago = models.DateField(
        blank=True, null=True, help_text="Fecha efectiva del pago"
    )
    id_hijo = models.ForeignKey("clientes.Hijos", models.DO_NOTHING, db_column="id_hijo")
    # Documento tributario generado (factura física o electrónica)
    id_documento = models.ForeignKey(
        "contabilidad.DocumentosTributarios",
        models.SET_NULL,
        db_column="id_documento",
        blank=True,
        null=True,
        help_text="Factura/comprobante tributario emitido para esta cuenta",
    )
    nro_comprobante = models.CharField(
        max_length=30,
        blank=True,
        help_text="Número de comprobante formateado (ej: 001-001-0000001)",
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "cuentas_almuerzo_mensual"
        unique_together = (("id_hijo", "anio", "mes"),)


class PagosAlmuerzoMensual(models.Model):
    id_pago_almuerzo = models.BigAutoField(primary_key=True)
    fecha_pago = models.DateTimeField()
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    mes_pagado = models.DateField()
    estado = models.CharField(max_length=9, blank=True, null=True)
    id_suscripcion = models.ForeignKey(
        "SuscripcionesAlmuerzo", models.DO_NOTHING, db_column="id_suscripcion"
    )
    id_venta = models.OneToOneField(
        "ventas.Ventas", models.DO_NOTHING, db_column="id_venta", blank=True, null=True
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "pagos_almuerzo_mensual"
        unique_together = (("id_suscripcion", "mes_pagado"),)


class PagosCuentasAlmuerzo(models.Model):
    id_pago = models.BigAutoField(primary_key=True)
    fecha_pago = models.DateTimeField()
    medio_pago = models.CharField(max_length=15)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    referencia = models.CharField(max_length=50, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    id_cuenta = models.ForeignKey(
        "CuentasAlmuerzoMensual", models.DO_NOTHING, db_column="id_cuenta"
    )
    id_empleado_registro = models.ForeignKey(
        "usuarios.Empleados",
        models.DO_NOTHING,
        db_column="id_empleado_registro",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "pagos_cuentas_almuerzo"


class Alergenos(models.Model):
    id_alergeno = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    palabras_clave = models.JSONField()
    nivel_severidad = models.CharField(max_length=10)
    icono = models.CharField(max_length=10, blank=True, null=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField()
    usuario_creacion = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "alergenos"


class ProductosAlergenos(models.Model):
    id_producto_alergeno = models.AutoField(primary_key=True)
    contiene = models.BooleanField(
        default=True, help_text="True=Contiene el alérgeno, False=Puede contener trazas"
    )
    observaciones = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField()
    usuario_registro = models.CharField(max_length=100, blank=True, null=True)
    id_alergeno = models.ForeignKey("Alergenos", models.DO_NOTHING, db_column="id_alergeno")
    id_producto = models.ForeignKey(
        "productos.Productos", models.DO_NOTHING, db_column="id_producto"
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "productos_alergenos"
        unique_together = (("id_producto", "id_alergeno"),)
