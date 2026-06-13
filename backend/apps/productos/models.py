"""
Modelos de la app productos
Gestión de productos, categorías, listas de precios y unidades de medida
"""

from decimal import Decimal

from django.db import models, transaction


# ==============================================================================
# CATEGORÍA
# ==============================================================================

class Categoria(models.Model):
    """Categoría jerárquica para organizar productos."""

    nombre = models.CharField(max_length=100, help_text="Nombre de la categoría")
    descripcion = models.TextField(blank=True, default="")
    categoria_padre = models.ForeignKey(
        "self",
        models.SET_NULL,
        blank=True,
        null=True,
        related_name="subcategorias",
        help_text="Categoría superior (nulo si es raíz)",
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def __str__(self):
        if self.categoria_padre:
            return f"{self.categoria_padre.nombre} > {self.nombre}"
        return self.nombre

    @property
    def es_categoria_raiz(self):
        return self.categoria_padre is None


# ==============================================================================
# UNIDAD DE MEDIDA
# ==============================================================================

class UnidadMedida(models.Model):
    """Unidad de medida para productos (kg, litro, unidad, etc.)."""

    nombre = models.CharField(max_length=50, help_text="Nombre completo (Kilogramo, Litro)")
    abreviatura = models.CharField(max_length=10, help_text="Abreviatura (Kg, L, Un)")
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Unidad de Medida"
        verbose_name_plural = "Unidades de Medida"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.abreviatura})"


# ==============================================================================
# PRODUCTO
# ==============================================================================

class Producto(models.Model):
    """Producto disponible en la cantina."""

    codigo_barra = models.CharField(
        max_length=50, unique=True, blank=True, null=True,
        help_text="Código de barras para escaneo",
    )
    codigo = models.CharField(
        max_length=50, unique=True, blank=True, null=True,
        help_text="Código interno del producto",
    )
    descripcion = models.CharField(
        max_length=255, help_text="Nombre descriptivo del producto"
    )
    categoria = models.ForeignKey(
        Categoria,
        models.PROTECT,
        related_name="productos",
    )
    unidad_medida = models.ForeignKey(
        UnidadMedida,
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos",
    )
    stock_minimo = models.DecimalField(
        max_digits=10, decimal_places=3, default=0,
        help_text="Cantidad mínima antes de generar alerta",
    )
    permite_stock_negativo = models.BooleanField(
        default=False,
        help_text="True si permite vender sin stock disponible",
    )
    es_servicio = models.BooleanField(
        default=False,
        help_text="True si es servicio (no requiere stock físico)",
    )
    requiere_stock = models.BooleanField(
        default=True,
        help_text="True si debe controlar stock",
    )
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["descripcion"]
        indexes = [
            models.Index(fields=["codigo_barra"], name="idx_prod_cod_barra"),
            models.Index(fields=["codigo"], name="idx_prod_codigo"),
            models.Index(fields=["descripcion"], name="idx_prod_desc"),
            models.Index(fields=["activo", "categoria"], name="idx_prod_activo_cat"),
            models.Index(fields=["categoria"], name="idx_prod_categoria"),
        ]

    def __str__(self):
        return f"{self.codigo or self.codigo_barra or 'S/C'} - {self.descripcion}"

    @property
    def precio_actual(self):
        lista_defecto = ListaPrecio.objects.filter(activo=True, es_por_defecto=True).first()
        if lista_defecto:
            precio = self.precios.filter(lista=lista_defecto).first()
            if precio:
                return precio.precio_unitario
        precio = self.precios.select_related("lista").order_by("lista__nombre").first()
        return precio.precio_unitario if precio else Decimal("0")

    @property
    def stock_actual(self):
        """Calcula el stock desde el inventario."""
        from apps.inventario.models import Stock  # importación lazy
        try:
            return Stock.objects.get(producto=self).cantidad
        except Stock.DoesNotExist:
            return Decimal("0")

    @property
    def requiere_reposicion(self):
        return self.stock_actual < self.stock_minimo


# ==============================================================================
# LISTA DE PRECIOS
# ==============================================================================

class ListaPrecio(models.Model):
    """Lista de precios diferenciada (minorista, mayorista, estudiante)."""

    nombre = models.CharField(unique=True, max_length=100)
    fecha_vigencia = models.DateField(blank=True, null=True)
    moneda = models.CharField(max_length=3, default="PYG")
    activo = models.BooleanField(default=True)
    es_por_defecto = models.BooleanField(
        default=False,
        help_text="Lista usada como referencia cuando no se especifica ninguna (solo una puede ser por defecto)",
    )

    class Meta:
        verbose_name = "Lista de Precios"
        verbose_name_plural = "Listas de Precios"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.moneda})"

    def save(self, *args, **kwargs):
        if self.es_por_defecto:
            with transaction.atomic():
                # Desactiva la lista por defecto anterior antes de guardar la nueva.
                ListaPrecio.objects.filter(es_por_defecto=True).exclude(pk=self.pk).update(
                    es_por_defecto=False
                )
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)


# ==============================================================================
# PRECIO POR LISTA
# ==============================================================================

class PrecioPorLista(models.Model):
    """Precio de un producto en una lista específica."""

    producto = models.ForeignKey(
        Producto, models.CASCADE, related_name="precios"
    )
    lista = models.ForeignKey(
        ListaPrecio, models.CASCADE, related_name="precios"
    )
    precio_unitario = models.DecimalField(
        max_digits=12, decimal_places=0,
        help_text="Precio en Guaraníes (sin decimales)",
    )
    fecha_vigencia = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Precio por Lista"
        verbose_name_plural = "Precios por Lista"
        unique_together = [("producto", "lista")]
        ordering = ["lista", "producto"]

    def __str__(self):
        return f"{self.producto} - {self.lista}: ₲{self.precio_unitario:,.0f}"


# ==============================================================================
# HISTÓRICO DE PRECIOS
# ==============================================================================

class HistoricoPrecio(models.Model):
    """Registro de cambios de precios."""

    producto = models.ForeignKey(
        Producto, models.CASCADE, related_name="historico_precios"
    )
    precio_anterior = models.DecimalField(max_digits=12, decimal_places=0)
    precio_nuevo = models.DecimalField(max_digits=12, decimal_places=0)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    modificado_por = models.ForeignKey(
        "usuarios.Usuario",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="cambios_precios",
    )

    class Meta:
        verbose_name = "Histórico de Precio"
        verbose_name_plural = "Histórico de Precios"
        ordering = ["-fecha_cambio"]

    def __str__(self):
        return f"{self.producto}: ₲{self.precio_anterior:,.0f} → ₲{self.precio_nuevo:,.0f}"

    @property
    def variacion_porcentual(self):
        if self.precio_anterior and self.precio_anterior > 0:
            return ((self.precio_nuevo - self.precio_anterior) / self.precio_anterior) * 100
        return Decimal("0")


# ==============================================================================
# IMPUESTO
# ==============================================================================

class Impuesto(models.Model):
    """Impuesto aplicable a productos (IVA 10%, IVA 5%, Exento)."""

    nombre = models.CharField(max_length=100, unique=True)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    vigente_desde = models.DateField()
    vigente_hasta = models.DateField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Impuesto"
        verbose_name_plural = "Impuestos"
        ordering = ["porcentaje"]

    def __str__(self):
        return f"{self.nombre} ({self.porcentaje}%)"


# ==============================================================================
# PRODUCTO - IMPUESTO (relación)
# ==============================================================================

class ProductoImpuesto(models.Model):
    """Relación producto-impuesto (un producto puede tener varios impuestos)."""

    producto = models.ForeignKey(
        Producto, models.CASCADE, related_name="impuestos"
    )
    impuesto = models.ForeignKey(
        Impuesto, models.PROTECT, related_name="productos"
    )
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Impuesto de Producto"
        verbose_name_plural = "Impuestos de Productos"
        unique_together = [("producto", "impuesto")]

    def __str__(self):
        return f"{self.producto} - {self.impuesto}"
