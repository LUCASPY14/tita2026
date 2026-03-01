"""
Modelos de la app inventario
Auto-generados desde la base de datos y organizados por funcionalidad
"""
from django.db import models


class StockUnico(models.Model):
    id_stock = models.AutoField(primary_key=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    fecha_ultima_actualizacion = models.DateTimeField()
    id_producto = models.OneToOneField('productos.Productos', models.DO_NOTHING, db_column='id_producto')

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'stock_unico'

class MovimientosStock(models.Model):
    id_movimiento_stock = models.BigAutoField(primary_key=True)
    fecha_hora = models.DateTimeField()
    tipo_movimiento = models.CharField(max_length=7)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    stock_resultante = models.DecimalField(max_digits=10, decimal_places=3)
    id_compra = models.ForeignKey('compras.Compras', models.DO_NOTHING, db_column='id_compra', blank=True, null=True)
    id_venta = models.ForeignKey('ventas.Ventas', models.DO_NOTHING, db_column='id_venta', blank=True, null=True)
    id_ajuste = models.BigIntegerField(blank=True, null=True)
    id_empleado_autoriza = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='id_empleado_autoriza')
    id_producto = models.ForeignKey('productos.Productos', models.DO_NOTHING, db_column='id_producto')

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'movimientos_stock'

class AjustesInventario(models.Model):
    id_ajuste = models.BigAutoField(primary_key=True)
    fecha_hora = models.DateTimeField()
    tipo_ajuste = models.CharField(max_length=8)
    motivo = models.CharField(max_length=255)
    estado = models.CharField(max_length=10)

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'ajustes_inventario'
        verbose_name = 'Ajuste de Inventario'
        verbose_name_plural = 'Ajustes de Inventario'

class DetallesAjuste(models.Model):
    id_detalle = models.BigAutoField(primary_key=True)
    cantidad_ajustada = models.DecimalField(max_digits=8, decimal_places=3)
    id_ajuste = models.ForeignKey('AjustesInventario', models.DO_NOTHING, db_column='id_ajuste')
    id_movimiento_stock = models.OneToOneField('MovimientosStock', models.DO_NOTHING, db_column='id_movimiento_stock')
    id_producto = models.ForeignKey('productos.Productos', models.DO_NOTHING, db_column='id_producto')

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'detalles_ajuste'
        unique_together = (('id_ajuste', 'id_producto'),)

class CostosHistoricos(models.Model):
    id_costo_historico = models.BigAutoField(primary_key=True)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_compra = models.DateTimeField()
    id_compra = models.ForeignKey('compras.Compras', models.DO_NOTHING, db_column='id_compra', blank=True, null=True)
    id_producto = models.ForeignKey('productos.Productos', models.DO_NOTHING, db_column='id_producto')

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'costos_historicos'
