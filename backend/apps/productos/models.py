"""
Modelos de la app productos
Gestión de productos, categorías, precios y unidades de medida
"""
from django.db import models
from decimal import Decimal


class Productos(models.Model):
    """
    Productos disponibles en la cantina.
    Maneja stock, precios por lista y configuraciones de venta.
    """
    id_producto = models.AutoField(primary_key=True)
    codigo_barra = models.CharField(unique=True, max_length=50, blank=True, null=True, help_text="Código de barras del producto")
    descripcion = models.CharField(max_length=255, help_text="Nombre/descripción del producto")
    stock_minimo = models.DecimalField(max_digits=10, decimal_places=3, default=0, help_text="Stock mínimo para alertas")
    permite_stock_negativo = models.BooleanField(default=False, help_text="1 si permite vender sin stock")
    activo = models.BooleanField(default=True, help_text="1=Activo, 0=Inactivo")
    id_categoria = models.ForeignKey('Categorias', models.DO_NOTHING, db_column='id_categoria', related_name='productos')
    id_impuesto = models.ForeignKey('contabilidad.Impuestos', models.DO_NOTHING, db_column='id_impuesto', related_name='productos')
    id_unidad_medida = models.ForeignKey('UnidadesMedida', models.DO_NOTHING, db_column='id_unidad_medida', blank=True, null=True, related_name='productos')

    class Meta:
        managed = True
        db_table = 'productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['descripcion']

    def __str__(self):
        return f"{self.codigo_barra or 'S/C'} - {self.descripcion}"

    @property
    def stock_actual(self):
        """Calcula el stock actual desde el inventario"""
        # Aquí se puede consultar el modelo de inventario
        return Decimal('0.00')

    @property
    def requiere_reposicion(self):
        """Verifica si el stock está por debajo del mínimo"""
        return self.stock_actual < self.stock_minimo


class Categorias(models.Model):
    """
    Categorías para organizar productos (jerárquicas).
    """
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, help_text="Nombre de la categoría")
    activo = models.BooleanField(default=True)
    id_categoria_padre = models.ForeignKey('self', models.DO_NOTHING, db_column='id_categoria_padre', blank=True, null=True, related_name='subcategorias')

    class Meta:
        managed = True
        db_table = 'categorias'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        if self.id_categoria_padre:
            return f"{self.id_categoria_padre.nombre} > {self.nombre}"
        return self.nombre

    @property
    def es_categoria_raiz(self):
        """Retorna True si es una categoría de nivel superior"""
        return self.id_categoria_padre is None


class UnidadesMedida(models.Model):
    """
    Unidades de medida para productos (kg, unidad, litro, etc.)
    """
    id_unidad_medida = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, help_text="Nombre completo (Kilogramo, Litro)")
    abreviatura = models.CharField(max_length=10, help_text="Abreviatura (Kg, L)")
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'unidades_medida'
        verbose_name = 'Unidad de Medida'
        verbose_name_plural = 'Unidades de Medida'
        verbose_name = 'Unidad de Medida'
        verbose_name_plural = 'Unidades de Medida'
        verbose_name = 'Unidad de Medida'
        verbose_name_plural = 'Unidades de Medida'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.abreviatura})"


class ListasPrecios(models.Model):
    """
    Listas de precios diferenciadas (mayorista, minorista, estudiante, etc.)
    """
    id_lista = models.AutoField(primary_key=True)
    nombre_lista = models.CharField(unique=True, max_length=100, help_text="Nombre de la lista de precios")
    fecha_vigencia = models.DateField(blank=True, null=True, help_text="Fecha desde la cual es válida")
    moneda = models.CharField(max_length=3, default='PYG', help_text="Código de moneda (PYG, USD)")
    activo = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = 'listas_precios'
        verbose_name = 'Lista de Precios'
        verbose_name_plural = 'Listas de Precios'
        verbose_name = 'Lista de Precios'
        verbose_name_plural = 'Listas de Precios'
        verbose_name = 'Lista de Precios'
        verbose_name_plural = 'Listas de Precios'
        ordering = ['nombre_lista']

    def __str__(self):
        return f"{self.nombre_lista} ({self.moneda})"


class PreciosPorLista(models.Model):
    """
    Precios específicos de cada producto según la lista de precios.
    """
    id_precio = models.AutoField(primary_key=True)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, help_text="Precio del producto en esta lista")
    fecha_vigencia = models.DateTimeField(auto_now_add=True, help_text="Fecha desde la cual es válido este precio")
    id_lista = models.ForeignKey('ListasPrecios', models.DO_NOTHING, db_column='id_lista', related_name='precios')
    id_producto = models.ForeignKey('Productos', models.DO_NOTHING, db_column='id_producto', related_name='precios')

    class Meta:
        managed = True
        db_table = 'precios_por_lista'
        verbose_name = 'Precio por Lista'
        verbose_name_plural = 'Precios por Lista'
        verbose_name = 'Precio por Lista'
        verbose_name_plural = 'Precios por Lista'
        unique_together = (('id_producto', 'id_lista'),)
        verbose_name = 'Precio por Lista'
        verbose_name_plural = 'Precios por Lista'
        ordering = ['id_lista', 'id_producto']

    def __str__(self):
        return f"{self.id_producto} - {self.id_lista}: ${self.precio_unitario}"


class HistoricoPrecios(models.Model):
    """
    Registro histórico de cambios de precios de productos.
    """
    id_historico = models.BigAutoField(primary_key=True)
    precio_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    precio_nuevo = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    id_empleado = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='id_empleado', blank=True, null=True, related_name='cambios_precios')
    id_producto = models.ForeignKey('Productos', models.DO_NOTHING, db_column='id_producto', related_name='historico_precios')

    class Meta:
        managed = True
        db_table = 'historico_precios'
        verbose_name = 'Histórico de Precio'
        verbose_name_plural = 'Histórico de Precios'
        verbose_name = 'Histórico de Precio'
        verbose_name_plural = 'Histórico de Precios'
        verbose_name = 'Histórico de Precio'
        verbose_name_plural = 'Histórico de Precios'
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"{self.id_producto}: ${self.precio_anterior} → ${self.precio_nuevo}"

    @property
    def variacion_porcentual(self):
        """Calcula el porcentaje de cambio de precio"""
        if self.precio_anterior and self.precio_anterior > 0:
            return ((self.precio_nuevo - self.precio_anterior) / self.precio_anterior) * 100
        return Decimal('0.00')
