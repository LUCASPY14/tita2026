"""
Modelos de la app compras
Auto-generados desde la base de datos y organizados por funcionalidad
"""
from django.db import models


class Proveedores(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    ruc = models.CharField(unique=True, max_length=20)
    razon_social = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=254, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    activo = models.IntegerField()
    fecha_registro = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'proveedores'

class Compras(models.Model):
    id_compra = models.BigAutoField(primary_key=True)
    fecha = models.DateTimeField()
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_pendiente = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    estado_pago = models.CharField(max_length=10)
    nro_factura = models.CharField(max_length=50, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    id_proveedor = models.ForeignKey('Proveedores', models.DO_NOTHING, db_column='id_proveedor')
    id_documento = models.ForeignKey('contabilidad.DocumentosTributarios', models.DO_NOTHING, db_column='id_documento', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'compras'

class DetallesCompra(models.Model):
    id_detalle = models.BigAutoField(primary_key=True)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.DecimalField(max_digits=8, decimal_places=3)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    monto_iva = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    id_compra = models.ForeignKey('Compras', models.DO_NOTHING, db_column='id_compra')
    id_producto = models.ForeignKey('productos.Productos', models.DO_NOTHING, db_column='id_producto')

    class Meta:
        managed = True
        db_table = 'detalles_compra'
        unique_together = (('id_compra', 'id_producto'),)

class PagosProveedores(models.Model):
    id_pago_proveedor = models.BigAutoField(primary_key=True)
    fecha_creacion = models.DateTimeField()
    id_medio_pago = models.ForeignKey('core.MediosPago', models.DO_NOTHING, db_column='id_medio_pago')

    class Meta:
        managed = True
        db_table = 'pagos_proveedores'

class AplicacionPagosCompras(models.Model):
    id_aplicacion = models.BigAutoField(primary_key=True)
    monto_aplicado = models.DecimalField(max_digits=12, decimal_places=2)
    id_compra = models.ForeignKey('Compras', models.DO_NOTHING, db_column='id_compra')
    id_pago_proveedor = models.ForeignKey('PagosProveedores', models.DO_NOTHING, db_column='id_pago_proveedor')

    class Meta:
        managed = True
        db_table = 'aplicacion_pagos_compras'

class NotasCreditoProveedor(models.Model):
    id_nota_proveedor = models.BigAutoField(primary_key=True)
    nro_factura_compra = models.BigIntegerField(blank=True, null=True)
    fecha = models.DateTimeField()
    monto_total = models.DecimalField(max_digits=12, decimal_places=2)
    observacion = models.CharField(max_length=255, blank=True, null=True)
    estado = models.CharField(max_length=10)
    fecha_creacion = models.DateTimeField()
    id_compra_original = models.ForeignKey('Compras', models.DO_NOTHING, db_column='id_compra_original', blank=True, null=True)
    id_proveedor = models.ForeignKey('Proveedores', models.DO_NOTHING, db_column='id_proveedor')

    class Meta:
        managed = True
        db_table = 'notas_credito_proveedor'

class DetallesNotaCreditoProveedor(models.Model):
    id_detalle_nc_proveedor = models.BigAutoField(primary_key=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    id_nota_proveedor = models.ForeignKey('NotasCreditoProveedor', models.DO_NOTHING, db_column='id_nota_proveedor')
    id_producto = models.ForeignKey('productos.Productos', models.DO_NOTHING, db_column='id_producto')

    class Meta:
        managed = True
        db_table = 'detalles_nota_credito_proveedor'
