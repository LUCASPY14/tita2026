"""
Modelos de la app ventas
Auto-generados desde la base de datos y organizados por funcionalidad
"""
from django.db import models


class Ventas(models.Model):
    id_venta = models.BigAutoField(primary_key=True)
    nro_factura_venta = models.BigIntegerField(blank=True, null=True)
    fecha = models.DateTimeField()
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_pendiente = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    estado_pago = models.CharField(max_length=10)
    estado = models.CharField(max_length=10)
    tipo_venta = models.CharField(max_length=20)
    motivo_credito = models.TextField(blank=True, null=True)
    genera_factura_legal = models.IntegerField()
    autorizado_por = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='autorizado_por', blank=True, null=True)
    id_cliente = models.ForeignKey('clientes.Clientes', models.DO_NOTHING, db_column='id_cliente')
    id_empleado_cajero = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='id_empleado_cajero', related_name='ventas_id_empleado_cajero_set')
    id_hijo = models.ForeignKey('clientes.Hijos', models.DO_NOTHING, db_column='id_hijo', blank=True, null=True)
    id_medio_pago = models.ForeignKey('core.MediosPago', models.DO_NOTHING, db_column='id_medio_pago', blank=True, null=True)
    id_documento = models.ForeignKey('contabilidad.DocumentosTributarios', models.DO_NOTHING, db_column='id_documento', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'ventas'

class DetallesVenta(models.Model):
    id_detalle = models.BigAutoField(primary_key=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    id_producto = models.ForeignKey('productos.Productos', models.DO_NOTHING, db_column='id_producto')
    id_venta = models.ForeignKey('Ventas', models.DO_NOTHING, db_column='id_venta')

    class Meta:
        managed = True
        db_table = 'detalles_venta'
        unique_together = (('id_venta', 'id_producto'),)

class PagosVenta(models.Model):
    id_pago_venta = models.BigAutoField(primary_key=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    referencia_transaccion = models.CharField(max_length=100, blank=True, null=True)
    fecha_pago = models.DateTimeField()
    estado = models.CharField(max_length=10)
    id_cierre = models.BigIntegerField(blank=True, null=True)
    id_medio_pago = models.ForeignKey('core.MediosPago', models.DO_NOTHING, db_column='id_medio_pago')
    nro_tarjeta_usada = models.ForeignKey('core.Tarjetas', models.DO_NOTHING, db_column='nro_tarjeta_usada', blank=True, null=True)
    id_venta = models.ForeignKey('Ventas', models.DO_NOTHING, db_column='id_venta')

    class Meta:
        managed = True
        db_table = 'pagos_venta'

class AplicacionPagosVentas(models.Model):
    id_aplicacion = models.BigAutoField(primary_key=True)
    monto_aplicado = models.DecimalField(max_digits=12, decimal_places=2)
    id_pago_venta = models.ForeignKey('PagosVenta', models.DO_NOTHING, db_column='id_pago_venta')
    id_venta = models.ForeignKey('Ventas', models.DO_NOTHING, db_column='id_venta')

    class Meta:
        managed = True
        db_table = 'aplicacion_pagos_ventas'

class NotasCreditoCliente(models.Model):
    id_nota = models.BigAutoField(primary_key=True)
    nro_nota_credito = models.BigIntegerField()
    fecha_emision = models.DateTimeField()
    motivo = models.TextField()
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=10)
    id_cliente = models.ForeignKey('clientes.Clientes', models.DO_NOTHING, db_column='id_cliente')
    id_empleado_autoriza = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='id_empleado_autoriza')
    id_venta_origen = models.ForeignKey('Ventas', models.DO_NOTHING, db_column='id_venta_origen', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'notas_credito_cliente'

class DetallesNotaCredito(models.Model):
    id_detalle_nota = models.BigAutoField(primary_key=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    id_nota = models.ForeignKey('NotasCreditoCliente', models.DO_NOTHING, db_column='id_nota')
    id_producto = models.ForeignKey('productos.Productos', models.DO_NOTHING, db_column='id_producto')

    class Meta:
        managed = True
        db_table = 'detalles_nota_credito'

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
    requiere_codigo = models.IntegerField()
    codigo_promocion = models.CharField(unique=True, max_length=50, blank=True, null=True)
    prioridad = models.IntegerField()
    activo = models.IntegerField()
    fecha_creacion = models.DateTimeField()
    usuario_creacion = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'promociones'

class CategoriasPromocion(models.Model):
    id_categoria_promocion = models.AutoField(primary_key=True)
    id_categoria = models.ForeignKey('productos.Categorias', models.DO_NOTHING, db_column='id_categoria')
    id_promocion = models.ForeignKey('Promociones', models.DO_NOTHING, db_column='id_promocion')

    class Meta:
        managed = True
        db_table = 'categorias_promocion'
        unique_together = (('id_promocion', 'id_categoria'),)

class ProductosPromocion(models.Model):
    id_producto_promocion = models.AutoField(primary_key=True)
    id_producto = models.ForeignKey('productos.Productos', models.DO_NOTHING, db_column='id_producto')
    id_promocion = models.ForeignKey('Promociones', models.DO_NOTHING, db_column='id_promocion')

    class Meta:
        managed = True
        db_table = 'productos_promocion'
        unique_together = (('id_promocion', 'id_producto'),)

class PromocionesAplicadas(models.Model):
    id_aplicacion = models.AutoField(primary_key=True)
    monto_descontado = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_aplicacion = models.DateTimeField()
    id_promocion = models.ForeignKey('Promociones', models.DO_NOTHING, db_column='id_promocion')
    id_venta = models.ForeignKey('Ventas', models.DO_NOTHING, db_column='id_venta')

    class Meta:
        managed = True
        db_table = 'promociones_aplicadas'
