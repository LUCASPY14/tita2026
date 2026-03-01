"""
Modelos de la app productos
Auto-generados desde la base de datos y organizados por funcionalidad
"""
from django.db import models


class Productos(models.Model):
    id_producto = models.AutoField(primary_key=True)
    codigo_barra = models.CharField(unique=True, max_length=50, blank=True, null=True)
    descripcion = models.CharField(max_length=255)
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=3)
    permite_stock_negativo = models.IntegerField()
    activo = models.IntegerField()
    id_categoria = models.ForeignKey('Categorias', models.DO_NOTHING, db_column='id_categoria')
    id_impuesto = models.ForeignKey('contabilidad.Impuestos', models.DO_NOTHING, db_column='id_impuesto')
    id_unidad_medida = models.ForeignKey('UnidadesMedida', models.DO_NOTHING, db_column='id_unidad_medida', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'productos'

class Categorias(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    activo = models.IntegerField()
    id_categoria_padre = models.ForeignKey('self', models.DO_NOTHING, db_column='id_categoria_padre', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'categorias'

class UnidadesMedida(models.Model):
    id_unidad_medida = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    abreviatura = models.CharField(max_length=10)
    activo = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'unidades_medida'

class ListasPrecios(models.Model):
    id_lista = models.AutoField(primary_key=True)
    nombre_lista = models.CharField(unique=True, max_length=100)
    fecha_vigencia = models.DateField(blank=True, null=True)
    moneda = models.CharField(max_length=3)
    activo = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'listas_precios'

class PreciosPorLista(models.Model):
    id_precio = models.AutoField(primary_key=True)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_vigencia = models.DateTimeField()
    id_lista = models.ForeignKey('ListasPrecios', models.DO_NOTHING, db_column='id_lista')
    id_producto = models.ForeignKey('Productos', models.DO_NOTHING, db_column='id_producto')

    class Meta:
        managed = True
        db_table = 'precios_por_lista'
        unique_together = (('id_producto', 'id_lista'),)

class HistoricoPrecios(models.Model):
    id_historico = models.BigAutoField(primary_key=True)
    precio_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    precio_nuevo = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_cambio = models.DateTimeField()
    id_empleado = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='id_empleado', blank=True, null=True)
    id_producto = models.ForeignKey('Productos', models.DO_NOTHING, db_column='id_producto')

    class Meta:
        managed = True
        db_table = 'historico_precios'
