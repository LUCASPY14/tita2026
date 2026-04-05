"""
Modelos de la app contabilidad
Auto-generados desde la base de datos y organizados por funcionalidad
"""

from django.db import models


class Cajas(models.Model):
    id_caja = models.AutoField(primary_key=True)
    nombre_caja = models.CharField(max_length=50)
    ubicacion = models.CharField(max_length=100, blank=True, null=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "cajas"


class CierresCaja(models.Model):
    id_cierre = models.BigAutoField(primary_key=True)
    fecha_hora_apertura = models.DateTimeField()
    fecha_hora_cierre = models.DateTimeField(blank=True, null=True)
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    monto_contado_fisico = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    diferencia_efectivo = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    estado = models.CharField(max_length=7, blank=True, null=True)
    id_caja = models.ForeignKey("Cajas", models.DO_NOTHING, db_column="id_caja")
    id_empleado = models.ForeignKey(
        "usuarios.Empleados", models.DO_NOTHING, db_column="id_empleado"
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "cierres_caja"


class MovimientosCaja(models.Model):
    id_movimiento = models.BigAutoField(primary_key=True)
    tipo_movimiento = models.CharField(max_length=20)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    monto_comision = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_movimiento = models.DateTimeField()
    descripcion = models.CharField(max_length=200, blank=True, null=True)
    id_cierre = models.ForeignKey(
        "CierresCaja", models.DO_NOTHING, db_column="id_cierre", blank=True, null=True
    )
    id_medio_pago = models.ForeignKey(
        "core.MediosPago", models.DO_NOTHING, db_column="id_medio_pago"
    )
    id_venta = models.ForeignKey(
        "ventas.Ventas", models.DO_NOTHING, db_column="id_venta", blank=True, null=True
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "movimientos_caja"


class TarifasComision(models.Model):
    id_tarifa = models.AutoField(primary_key=True)
    fecha_inicio_vigencia = models.DateTimeField()
    fecha_fin_vigencia = models.DateTimeField(blank=True, null=True)
    porcentaje_comision = models.DecimalField(max_digits=5, decimal_places=4)
    monto_fijo_comision = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    estado = models.BooleanField(default=True)
    id_medio_pago = models.ForeignKey(
        "core.MediosPago", models.DO_NOTHING, db_column="id_medio_pago"
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "tarifas_comision"


class AuditoriaComisiones(models.Model):
    id_auditoria = models.BigAutoField(primary_key=True)
    fecha_cambio = models.DateTimeField()
    campo_modificado = models.CharField(max_length=50)
    valor_anterior = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    valor_nuevo = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    id_empleado_modifico = models.ForeignKey(
        "usuarios.Empleados",
        models.DO_NOTHING,
        db_column="id_empleado_modifico",
        blank=True,
        null=True,
    )
    id_tarifa = models.ForeignKey(
        "TarifasComision", models.DO_NOTHING, db_column="id_tarifa", blank=True, null=True
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "auditoria_comisiones"


class ConciliacionPagos(models.Model):
    id_conciliacion = models.BigAutoField(primary_key=True)
    fecha_acreditacion = models.DateTimeField(blank=True, null=True)
    fecha_conciliacion = models.DateTimeField()
    estado = models.CharField(max_length=20)
    monto_acreditado = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    id_pago_venta = models.OneToOneField(
        "ventas.PagosVenta", models.DO_NOTHING, db_column="id_pago_venta"
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "conciliacion_pagos"


class DocumentosTributarios(models.Model):
    CONDICION_CHOICES = [
        ('CONTADO', 'Contado'),
        ('CREDITO', 'Crédito'),
    ]

    id_documento = models.BigAutoField(primary_key=True)
    nro_secuencial = models.IntegerField(
        help_text="Número secuencial fiscal dentro del rango del timbrado"
    )
    fecha_emision = models.DateTimeField()
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    nro_timbrado = models.ForeignKey("Timbrados", models.DO_NOTHING, db_column="nro_timbrado")
    tipo_documento = models.CharField(max_length=20, default='Factura')
    nro_preimpreso_interno = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Número de formulario preimpreso (ej: 001-001-0000123)",
    )
    id_cliente = models.ForeignKey(
        "clientes.Clientes",
        models.SET_NULL,
        db_column="id_cliente",
        blank=True,
        null=True,
        related_name="documentos",
        help_text="Cliente al que se emite la factura",
    )
    condicion_venta = models.CharField(
        max_length=7,
        choices=CONDICION_CHOICES,
        default='CONTADO',
        help_text='Condición de venta exigida por la SET',
    )
    plazo_dias = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        help_text='Plazo en días para condición Crédito (obligatorio si CREDITO)',
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "documentos_tributarios"
        verbose_name = "Documento Tributario"
        verbose_name_plural = "Documentos Tributarios"
        unique_together = (("nro_timbrado", "nro_secuencial"),)


class DocumentoImpuestos(models.Model):
    id_documento = models.OneToOneField(
        "DocumentosTributarios", models.DO_NOTHING, db_column="id_documento", primary_key=True
    )
    id_impuesto = models.ForeignKey("Impuestos", models.DO_NOTHING, db_column="id_impuesto")
    base_imponible = models.DecimalField(max_digits=12, decimal_places=2)
    monto_impuesto = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.__class__.__name__} - Doc:{self.id_documento_id} Imp:{self.id_impuesto_id}"

    class Meta:
        managed = False
        db_table = "documento_impuestos"
        unique_together = [["id_documento", "id_impuesto"]]


class Timbrados(models.Model):
    nro_timbrado = models.IntegerField(primary_key=True)
    tipo_documento = models.CharField(max_length=12)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    nro_inicial = models.IntegerField()
    nro_final = models.IntegerField()
    estado = models.BooleanField(default=True)
    es_electronico = models.SmallIntegerField(default=0, help_text="0=impreso, 1=electrónico")
    id_punto = models.ForeignKey("PuntosExpedicion", models.DO_NOTHING, db_column="id_punto")

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "timbrados"
        verbose_name = "Timbrado"
        verbose_name_plural = "Timbrados"


class PuntosExpedicion(models.Model):
    id_punto = models.AutoField(primary_key=True)
    codigo_establecimiento = models.CharField(max_length=3)
    codigo_punto_expedicion = models.CharField(max_length=3)
    descripcion_ubicacion = models.CharField(max_length=100, blank=True, null=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "puntos_expedicion"
        unique_together = (("codigo_establecimiento", "codigo_punto_expedicion"),)


class DatosEmpresa(models.Model):
    id_empresa = models.AutoField(primary_key=True)
    ruc = models.CharField(max_length=20)
    razon_social = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "datos_empresa"


class Impuestos(models.Model):
    id_impuesto = models.AutoField(primary_key=True)
    nombre_impuesto = models.CharField(unique=True, max_length=50)
    porcentaje = models.DecimalField(max_digits=4, decimal_places=2)
    vigente_desde = models.DateField()
    vigente_hasta = models.DateField(blank=True, null=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "impuestos"
        verbose_name = "Impuesto"
        verbose_name_plural = "Impuestos"
