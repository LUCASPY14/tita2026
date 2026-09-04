"""
Admin para la app inventario
Gestión de stock, movimientos, ajustes y costos
"""

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Stock,
    MovimientoStock,
    AjusteInventario,
    DetalleAjuste,
    CostoHistorico,
)


# ==============================================================================
# STOCK
# ==============================================================================

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = [
        "producto_link",
        "cantidad_display",
        "requiere_reposicion_badge",
        "fecha_actualizacion",
    ]
    list_filter = ["fecha_actualizacion"]
    search_fields = ["producto__descripcion", "producto__codigo_barra"]
    readonly_fields = [
        "fecha_actualizacion",
        "costo_promedio",
        "valor_inventario",
        "dias_stock_disponible",
    ]
    list_select_related = ["producto"]
    ordering = ["producto__descripcion"]
    fieldsets = (
        ("Datos del Stock", {
            "fields": ("producto", "cantidad")
        }),
        ("Valores Calculados", {
            "fields": ("costo_promedio", "valor_inventario", "dias_stock_disponible"),
            "classes": ("collapse",),
        }),
        ("Auditoría", {
            "fields": ("fecha_actualizacion",),
        }),
    )

    def producto_link(self, obj):
        url = reverse("admin:productos_producto_change", args=[obj.producto.pk])
        return format_html('<a href="{}">{}</a>', url, obj.producto.descripcion)
    producto_link.short_description = "Producto"

    def cantidad_display(self, obj):
        color = "#dc3545" if obj.cantidad < obj.producto.stock_minimo else "#28a745"
        return format_html('<strong style="color:{};">{}</strong>', color, obj.cantidad)
    cantidad_display.short_description = "Cantidad"

    def requiere_reposicion_badge(self, obj):
        if obj.requiere_reposicion:
            return mark_safe('<span style="color:#dc3545;">⚠ Reponer</span>')  # nosec B308
        return mark_safe('<span style="color:#28a745;">✓ OK</span>')  # nosec B308
    requiere_reposicion_badge.short_description = "Reposición"


# ==============================================================================
# MOVIMIENTO DE STOCK
# ==============================================================================

@admin.register(MovimientoStock)
class MovimientoStockAdmin(admin.ModelAdmin):
    list_display = [
        "id_movimiento_stock",
        "producto_link",
        "tipo_badge",
        "motivo_badge",
        "cantidad_display",
        "stock_resultante_display",
        "fecha",
    ]
    list_filter = ["tipo", "motivo", "fecha"]
    search_fields = ["producto__descripcion", "producto__codigo_barra", "observaciones"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["producto"]
    date_hierarchy = "fecha"
    ordering = ["-fecha"]

    def get_readonly_fields(self, request, obj=None):
        """Movimiento inmutable una vez creado."""
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def producto_link(self, obj):
        url = reverse("admin:productos_producto_change", args=[obj.producto.pk])
        return format_html('<a href="{}">{}</a>', url, obj.producto.descripcion)
    producto_link.short_description = "Producto"

    def tipo_badge(self, obj):
        colors = {"INGRESO": "#28a745", "EGRESO": "#dc3545"}
        color = colors.get(obj.tipo, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_tipo_display(),
        )
    tipo_badge.short_description = "Tipo"

    def motivo_badge(self, obj):
        return format_html(
            '<span style="background:#17a2b8;color:white;padding:2px 6px;border-radius:3px;font-size:10px;">{}</span>',
            obj.get_motivo_display(),
        )
    motivo_badge.short_description = "Motivo"

    def cantidad_display(self, obj):
        signo = "+" if obj.tipo == "INGRESO" else "-"
        return f"{signo}{obj.cantidad}"
    cantidad_display.short_description = "Cantidad"

    def stock_resultante_display(self, obj):
        color = "#dc3545" if obj.stock_resultante < 0 else "#28a745"
        return format_html('<strong style="color:{};">{}</strong>', color, obj.stock_resultante)
    stock_resultante_display.short_description = "Stock Resultante"


# ==============================================================================
# AJUSTE DE INVENTARIO
# ==============================================================================

@admin.register(AjusteInventario)
class AjusteInventarioAdmin(admin.ModelAdmin):
    list_display = [
        "id_ajuste",
        "tipo_badge",
        "estado_badge",
        "motivo",
        "solicitado_por_link",
        "fecha",
    ]
    list_filter = ["tipo", "estado", "fecha"]
    search_fields = ["motivo", "solicitado_por__nombre", "solicitado_por__apellido"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["solicitado_por"]
    date_hierarchy = "fecha"
    ordering = ["-fecha"]
    fieldsets = (
        ("Datos del Ajuste", {
            "fields": ("tipo", "estado", "motivo")
        }),
        ("Aprobación", {
            "fields": ("solicitado_por", "aprobado_por", "fecha_aprobacion")
        }),
        ("Auditoría", {
            "fields": ("fecha_creacion",),
            "classes": ("collapse",),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Ajuste inmutable cuando está aprobado o rechazado."""
        if obj and obj.estado in ("APROBADO", "RECHAZADO"):
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def tipo_badge(self, obj):
        colors = {"AUMENTO": "#28a745", "MERMA": "#dc3545"}
        color = colors.get(obj.tipo, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_tipo_display(),
        )
    tipo_badge.short_description = "Tipo"

    def estado_badge(self, obj):
        colors = {"PENDIENTE": "#ffc107", "APROBADO": "#28a745", "RECHAZADO": "#dc3545"}
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_estado_display(),
        )
    estado_badge.short_description = "Estado"

    def solicitado_por_link(self, obj):
        if obj.solicitado_por:
            url = reverse("admin:usuarios_usuario_change", args=[obj.solicitado_por.pk])
            return format_html('<a href="{}">{}</a>', url, obj.solicitado_por.nombre_completo)
        return "-"
    solicitado_por_link.short_description = "Solicitado por"


# ==============================================================================
# DETALLE DE AJUSTE
# ==============================================================================

@admin.register(DetalleAjuste)
class DetalleAjusteAdmin(admin.ModelAdmin):
    list_display = ["id_detalle_ajuste", "ajuste_link", "producto_link", "cantidad"]
    search_fields = ["ajuste__motivo", "producto__descripcion"]
    list_select_related = ["ajuste", "producto"]

    def get_readonly_fields(self, request, obj=None):
        """Detalle inmutable una vez creado."""
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []

    def has_delete_permission(self, request, obj=None):
        """No permite eliminar detalles de ajuste."""
        return False

    def ajuste_link(self, obj):
        url = reverse("admin:inventario_ajusteinventario_change", args=[obj.ajuste.pk])
        return format_html('<a href="{}">Ajuste #{}</a>', url, obj.ajuste.pk)
    ajuste_link.short_description = "Ajuste"

    def producto_link(self, obj):
        url = reverse("admin:productos_producto_change", args=[obj.producto.pk])
        return format_html('<a href="{}">{}</a>', url, obj.producto.descripcion)
    producto_link.short_description = "Producto"


# ==============================================================================
# COSTO HISTÓRICO
# ==============================================================================

@admin.register(CostoHistorico)
class CostoHistoricoAdmin(admin.ModelAdmin):
    list_display = [
        "id_costo_historico",
        "producto_link",
        "costo_unitario_display",
        "cantidad_comprada",
        "costo_total_display",
        "fecha_compra",
    ]
    list_filter = ["fecha_compra"]
    search_fields = ["producto__descripcion"]
    list_select_related = ["producto"]
    date_hierarchy = "fecha_compra"
    ordering = ["-fecha_compra"]

    def get_readonly_fields(self, request, obj=None):
        """Costo histórico inmutable una vez creado."""
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []

    def producto_link(self, obj):
        url = reverse("admin:productos_producto_change", args=[obj.producto.pk])
        return format_html('<a href="{}">{}</a>', url, obj.producto.descripcion)
    producto_link.short_description = "Producto"

    def costo_unitario_display(self, obj):
        return f"₲{obj.costo_unitario:,.0f}"
    costo_unitario_display.short_description = "Costo Unitario"

    def costo_total_display(self, obj):
        return f"₲{obj.costo_total:,.0f}"
    costo_total_display.short_description = "Costo Total"
