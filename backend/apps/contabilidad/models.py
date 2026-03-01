"""
Modelos de la app contabilidad
Auto-generados desde la base de datos y organizados por funcionalidad
"""
from django.db import models


class Cajas(models.Model):
    id_caja = models.AutoField(primary_key=True)
    nombre_caja = models.CharField(max_length=50)
    ubicacion = models.CharField(max_length=100, blank=True, null=True)
    activo = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'cajas'

class CierresCaja(models.Model):
    id_cierre = models.BigAutoField(primary_key=True)
    fecha_hora_apertura = models.DateTimeField()
    fecha_hora_cierre = models.DateTimeField(blank=True, null=True)
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    monto_contado_fisico = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    diferencia_efectivo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estado = models.CharField(max_length=7, blank=True, null=True)
    id_caja = models.ForeignKey('Cajas', models.DO_NOTHING, db_column='id_caja')
    id_empleado = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='id_empleado')

    class Meta:
        managed = True
        db_table = 'cierres_caja'

class MovimientosCaja(models.Model):
    id_movimiento = models.BigAutoField(primary_key=True)
    tipo_movimiento = models.CharField(max_length=20)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    monto_comision = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_movimiento = models.DateTimeField()
    descripcion = models.CharField(max_length=200, blank=True, null=True)
    id_cierre = models.ForeignKey('CierresCaja', models.DO_NOTHING, db_column='id_cierre')
    id_medio_pago = models.ForeignKey('core.MediosPago', models.DO_NOTHING, db_column='id_medio_pago')
    id_venta = models.ForeignKey('ventas.Ventas', models.DO_NOTHING, db_column='id_venta', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'movimientos_caja'

class TarifasComision(models.Model):
    id_tarifa = models.AutoField(primary_key=True)
    fecha_inicio_vigencia = models.DateTimeField()
    fecha_fin_vigencia = models.DateTimeField(blank=True, null=True)
    porcentaje_comision = models.DecimalField(max_digits=5, decimal_places=4)
    monto_fijo_comision = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    activo = models.IntegerField()
    id_medio_pago = models.ForeignKey('core.MediosPago', models.DO_NOTHING, db_column='id_medio_pago')

    class Meta:
        managed = True
        db_table = 'tarifas_comision'

class AuditoriaComisiones(models.Model):
    id_auditoria = models.BigAutoField(primary_key=True)
    fecha_cambio = models.DateTimeField()
    campo_modificado = models.CharField(max_length=50)
    valor_anterior = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    valor_nuevo = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    id_empleado_modifico = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='id_empleado_modifico', blank=True, null=True)
    id_tarifa = models.ForeignKey('TarifasComision', models.DO_NOTHING, db_column='id_tarifa', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'auditoria_comisiones'

class ConciliacionPagos(models.Model):
    id_conciliacion = models.BigAutoField(primary_key=True)
    fecha_acreditacion = models.DateTimeField(blank=True, null=True)
    fecha_conciliacion = models.DateTimeField()
    estado = models.CharField(max_length=20)
    monto_acreditado = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField()
    id_pago_venta = models.OneToOneField('ventas.PagosVenta', models.DO_NOTHING, db_column='id_pago_venta')

    class Meta:
        managed = True
        db_table = 'conciliacion_pagos'

class DocumentosTributarios(models.Model):
    id_documento = models.BigAutoField(primary_key=True)
    nro_secuencial = models.IntegerField()
    fecha_emision = models.DateTimeField()
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    nro_timbrado = models.ForeignKey('Timbrados', models.DO_NOTHING, db_column='nro_timbrado')
    tipo_documento = models.CharField(max_length=11)
    cdc = models.CharField(max_length=44, blank=True, null=True)
    url_kude = models.CharField(max_length=255, blank=True, null=True)
    estado_sifen = models.CharField(max_length=9, blank=True, null=True)
    fecha_envio = models.DateTimeField(blank=True, null=True)
    fecha_respuesta = models.DateTimeField(blank=True, null=True)
    nro_preimpreso_interno = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'documentos_tributarios'
        unique_together = (('nro_timbrado', 'nro_secuencial'),)

class DocumentoImpuestos(models.Model):
    pk = models.CompositePrimaryKey('id_documento', 'id_impuesto')
    id_documento = models.ForeignKey('DocumentosTributarios', models.DO_NOTHING, db_column='id_documento')
    id_impuesto = models.ForeignKey('Impuestos', models.DO_NOTHING, db_column='id_impuesto')
    base_imponible = models.DecimalField(max_digits=12, decimal_places=2)
    monto_impuesto = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = True
        db_table = 'documento_impuestos'

class Timbrados(models.Model):
    nro_timbrado = models.IntegerField(primary_key=True)
    tipo_documento = models.CharField(max_length=12)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    nro_inicial = models.IntegerField()
    nro_final = models.IntegerField()
    es_electronico = models.IntegerField()
    activo = models.IntegerField()
    id_punto = models.ForeignKey('PuntosExpedicion', models.DO_NOTHING, db_column='id_punto')

    class Meta:
        managed = True
        db_table = 'timbrados'

class PuntosExpedicion(models.Model):
    id_punto = models.AutoField(primary_key=True)
    codigo_establecimiento = models.CharField(max_length=3)
    codigo_punto_expedicion = models.CharField(max_length=3)
    descripcion_ubicacion = models.CharField(max_length=100, blank=True, null=True)
    activo = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'puntos_expedicion'
        unique_together = (('codigo_establecimiento', 'codigo_punto_expedicion'),)

class DatosEmpresa(models.Model):
    id_empresa = models.AutoField(primary_key=True)
    ruc = models.CharField(max_length=20)
    razon_social = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    activo = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'datos_empresa'

class Impuestos(models.Model):
    id_impuesto = models.AutoField(primary_key=True)
    nombre_impuesto = models.CharField(unique=True, max_length=50)
    porcentaje = models.DecimalField(max_digits=4, decimal_places=2)
    vigente_desde = models.DateField()
    vigente_hasta = models.DateField(blank=True, null=True)
    activo = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'impuestos'
