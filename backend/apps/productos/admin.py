"""
Admin para la app productos
Gestión de productos, categorías, listas de precios e impuestos
"""

from django.contrib import admin
from django.db import models
from django.db.models import Subquery, OuterRef, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Categoria,
    Producto,
    UnidadMedida,
    ListaPrecio,
    PrecioPorLista,
    HistoricoPrecio,
    Impuesto,
    ProductoImpuesto,
)


# ==============================================================================
# CATEGORÍA
# ==============================================================================

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "categoria_padre_link", "descripcion", "activo"]
    list_filter = ["activo", "categoria_padre"]
    search_fields = ["nombre", "descripcion"]
    ordering = ["nombre"]
    list_select_related = ["categoria_padre"]

    def categoria_padre_link(self, obj):
        if obj.categoria_padre:
            url = reverse("admin:productos_categoria_change", args=[obj.categoria_padre.pk])
            return format_html('<a href="{}">{}</a>', url, obj.categoria_padre.nombre)
        return "-"
    categoria_padre_link.short_description = "Categoría Padre"


# ==============================================================================
# PRODUCTO
# ==============================================================================

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = [
        "codigo_barra",
        "descripcion",
        "categoria_link",
        "precio_actual_display",
        "stock_display",
        "activo",
    ]
    list_filter = ["activo", "categoria", "es_servicio", "requiere_stock"]
    search_fields = ["codigo_barra", "codigo", "descripcion"]
    ordering = ["descripcion"]
    list_select_related = ["categoria"]
    fieldsets = (
        ("Identificación", {
            "fields": ("codigo_barra", "codigo", "descripcion")
        }),
        ("Clasificación", {
            "fields": ("categoria", "unidad_medida", "es_servicio")
        }),
        ("Stock", {
            "fields": ("requiere_stock", "permite_stock_negativo", "stock_minimo")
        }),
        ("Estado", {
            "fields": ("activo",),
        }),
    )

    def get_queryset(self, request):
        """Anota precio actual y stock para evitar N+1 queries."""
        from apps.inventario.models import Stock

        precio_subquery = PrecioPorLista.objects.filter(
            producto=OuterRef("pk")
        ).order_by("-fecha_vigencia").values("precio_unitario")[:1]

        stock_subquery = Stock.objects.filter(
            producto=OuterRef("pk")
        ).values("cantidad")[:1]

        return super().get_queryset(request).annotate(
            _precio_actual=Coalesce(
                Subquery(precio_subquery),
                Value(0, output_field=models.DecimalField()),
            ),
            _stock_actual=Coalesce(
                Subquery(stock_subquery),
                Value(0, output_field=models.DecimalField()),
            ),
        )

    def categoria_link(self, obj):
        url = reverse("admin:productos_categoria_change", args=[obj.categoria.pk])
        return format_html('<a href="{}">{}</a>', url, obj.categoria.nombre)
    categoria_link.short_description = "Categoría"

    def precio_actual_display(self, obj):
        precio = getattr(obj, "_precio_actual", 0)
        if precio:
            return f"₲{precio:,.0f}"
        return "-"
    precio_actual_display.short_description = "Precio Actual"

    def stock_display(self, obj):
        if not obj.requiere_stock:
            return format_html('<span style="color:#6c757d;">N/A</span>')
        stock = getattr(obj, "_stock_actual", 0)
        color = "#dc3545" if stock <= obj.stock_minimo else "#28a745"
        return format_html('<strong style="color:{};">{}</strong>', color, stock)
    stock_display.short_description = "Stock"


# ==============================================================================
# UNIDAD DE MEDIDA
# ==============================================================================

@admin.register(UnidadMedida)
class UnidadMedidaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "abreviatura", "activo"]
    search_fields = ["nombre", "abreviatura"]


# ==============================================================================
# LISTA DE PRECIOS
# ==============================================================================

@admin.register(ListaPrecio)
class ListaPrecioAdmin(admin.ModelAdmin):
    list_display = ["nombre", "moneda", "fecha_vigencia", "activo"]
    list_filter = ["activo", "moneda"]
    search_fields = ["nombre"]


# ==============================================================================
# PRECIO POR LISTA
# ==============================================================================

@admin.register(PrecioPorLista)
class PrecioPorListaAdmin(admin.ModelAdmin):
    list_display = ["producto_link", "lista_link", "precio_unitario_display", "fecha_vigencia"]
    list_filter = ["lista"]
    search_fields = ["producto__descripcion", "producto__codigo_barra"]
    ordering = ["lista", "producto__descripcion"]
    list_select_related = ["producto", "lista"]
    readonly_fields = ["fecha_vigencia"]

    def producto_link(self, obj):
        url = reverse("admin:productos_producto_change", args=[obj.producto.pk])
        return format_html('<a href="{}">{}</a>', url, obj.producto.descripcion)
    producto_link.short_description = "Producto"

    def lista_link(self, obj):
        url = reverse("admin:productos_listaprecio_change", args=[obj.lista.pk])
        return format_html('<a href="{}">{}</a>', url, obj.lista.nombre)
    lista_link.short_description = "Lista"

    def precio_unitario_display(self, obj):
        return f"₲{obj.precio_unitario:,.0f}"
    precio_unitario_display.short_description = "Precio"


# ==============================================================================
# HISTÓRICO DE PRECIOS
# ==============================================================================

@admin.register(HistoricoPrecio)
class HistoricoPrecioAdmin(admin.ModelAdmin):
    list_display = [
        "producto_link",
        "precio_anterior_display",
        "precio_nuevo_display",
        "variacion_badge",
        "modificado_por_link",
        "fecha_cambio",
    ]
    list_filter = ["fecha_cambio"]
    search_fields = ["producto__descripcion"]
    ordering = ["-fecha_cambio"]
    readonly_fields = ["fecha_cambio"]
    list_select_related = ["producto", "modificado_por"]

    def producto_link(self, obj):
        url = reverse("admin:productos_producto_change", args=[obj.producto.pk])
        return format_html('<a href="{}">{}</a>', url, obj.producto.descripcion)
    producto_link.short_description = "Producto"

    def precio_anterior_display(self, obj):
        return f"₲{obj.precio_anterior:,.0f}"
    precio_anterior_display.short_description = "Precio Anterior"

    def precio_nuevo_display(self, obj):
        return f"₲{obj.precio_nuevo:,.0f}"
    precio_nuevo_display.short_description = "Precio Nuevo"

    def variacion_badge(self, obj):
        variacion = obj.variacion_porcentual
        if variacion > 0:
            color = "#dc3545"
            texto = f"+{variacion:.1f}%"
        elif variacion < 0:
            color = "#28a745"
            texto = f"{variacion:.1f}%"
        else:
            color = "#6c757d"
            texto = "0%"
        return format_html('<strong style="color:{};">{}</strong>', color, texto)
    variacion_badge.short_description = "Variación"

    def modificado_por_link(self, obj):
        if obj.modificado_por:
            url = reverse("admin:usuarios_usuario_change", args=[obj.modificado_por.pk])
            return format_html('<a href="{}">{}</a>', url, obj.modificado_por.nombre_completo)
        return "-"
    modificado_por_link.short_description = "Modificado por"


# ==============================================================================
# IMPUESTO
# ==============================================================================

@admin.register(Impuesto)
class ImpuestoAdmin(admin.ModelAdmin):
    list_display = ["nombre", "porcentaje", "vigente_desde", "vigente_hasta", "activo"]
    list_filter = ["activo"]
    search_fields = ["nombre"]


# ==============================================================================
# PRODUCTO - IMPUESTO
# ==============================================================================

@admin.register(ProductoImpuesto)
class ProductoImpuestoAdmin(admin.ModelAdmin):
    list_display = ["producto_link", "impuesto_link", "fecha_asignacion"]
    list_filter = ["impuesto"]
    search_fields = ["producto__descripcion"]
    list_select_related = ["producto", "impuesto"]

    def producto_link(self, obj):
        url = reverse("admin:productos_producto_change", args=[obj.producto.pk])
        return format_html('<a href="{}">{}</a>', url, obj.producto.descripcion)
    producto_link.short_description = "Producto"

    def impuesto_link(self, obj):
        url = reverse("admin:productos_impuesto_change", args=[obj.impuesto.pk])
        return format_html('<a href="{}">{} ({}%)</a>', url, obj.impuesto.nombre, obj.impuesto.porcentaje)
    impuesto_link.short_description = "Impuesto"