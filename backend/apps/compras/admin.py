"""
Admin para la app compras
Gestión de proveedores, compras, pagos y cuentas corrientes
"""

from django.contrib import admin
from django.db import models
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Proveedor,
    CuentaCorrienteProveedor,
    Compra,
    DetalleCompra,
    PagoProveedor,
    AplicacionPagoCompra,
    NotaCreditoProveedor,
    DetalleNotaCreditoProveedor,
    OrdenCompra,
    DetalleOrdenCompra,
)


# ==============================================================================
# DETALLE DE COMPRA (INLINE)
# ==============================================================================

class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 0
    fields = ["producto", "cantidad", "costo_unitario", "subtotal", "monto_iva"]
    readonly_fields = ["subtotal", "monto_iva"]
    autocomplete_fields = ["producto"]

    def has_add_permission(self, request, obj=None):
        """No permite agregar detalles si la compra está pagada."""
        if obj and obj.estado_pago == "PAGADO":
            return False
        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        """No permite modificar detalles si la compra está pagada."""
        if obj and obj.estado_pago == "PAGADO":
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """No permite eliminar detalles si la compra está pagada."""
        if obj and obj.estado_pago == "PAGADO":
            return False
        return super().has_delete_permission(request, obj)


# ==============================================================================
# PROVEEDOR
# ==============================================================================

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = [
        "ruc",
        "razon_social",
        "telefono",
        "email",
        "saldo_display",
        "activo",
    ]
    list_filter = ["activo"]
    search_fields = ["ruc", "razon_social", "email"]
    readonly_fields = ["fecha_registro"]
    ordering = ["razon_social"]

    def get_queryset(self, request):
        """Anota saldo de cuenta corriente para evitar N+1 queries."""
        cero = Value(0, output_field=models.DecimalField())
        return super().get_queryset(request).annotate(
            _saldo_cc=Coalesce(
                Sum("movimientos_cuenta__monto", filter=models.Q(movimientos_cuenta__tipo="DEBITO")),
                cero,
            ) - Coalesce(
                Sum("movimientos_cuenta__monto", filter=~models.Q(movimientos_cuenta__tipo="DEBITO")),
                cero,
            )
        )

    def saldo_display(self, obj):
        saldo = getattr(obj, "_saldo_cc", 0) or 0
        color = "#dc3545" if saldo > 0 else "#28a745"
        return format_html('<strong style="color:{};">₲{:,}</strong>', color, saldo)
    saldo_display.short_description = "Saldo Cta. Cte."


# ==============================================================================
# CUENTA CORRIENTE PROVEEDOR
# ==============================================================================

@admin.register(CuentaCorrienteProveedor)
class CuentaCorrienteProveedorAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "proveedor_link",
        "fecha",
        "tipo_badge",
        "monto_display",
        "saldo_resultante_display",
        "descripcion",
    ]
    list_filter = ["tipo", "fecha"]
    search_fields = ["proveedor__razon_social", "proveedor__ruc", "descripcion"]
    readonly_fields = ["fecha_creacion", "saldo_anterior", "saldo_resultante"]
    list_select_related = ["proveedor"]
    date_hierarchy = "fecha"
    ordering = ["-fecha", "-id"]

    def get_readonly_fields(self, request, obj=None):
        """Movimiento de cuenta corriente inmutable una vez creado."""
        if obj:
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def proveedor_link(self, obj):
        url = reverse("admin:compras_proveedor_change", args=[obj.proveedor.pk])
        return format_html('<a href="{}">{}</a>', url, obj.proveedor.razon_social)
    proveedor_link.short_description = "Proveedor"

    def tipo_badge(self, obj):
        colors = {
            "DEBITO": "#dc3545",
            "CREDITO": "#28a745",
            "NOTA_CREDITO": "#0d6efd",
            "AJUSTE": "#ffc107",
        }
        color = colors.get(obj.tipo, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_tipo_display(),
        )
    tipo_badge.short_description = "Tipo"

    def monto_display(self, obj):
        return f"₲{obj.monto:,.0f}"
    monto_display.short_description = "Monto"

    def saldo_resultante_display(self, obj):
        color = "#dc3545" if obj.saldo_resultante > 0 else "#28a745"
        return format_html('<strong style="color:{};">₲{:,}</strong>', color, obj.saldo_resultante)
    saldo_resultante_display.short_description = "Saldo Resultante"


# ==============================================================================
# COMPRA
# ==============================================================================

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "fecha",
        "proveedor_link",
        "tipo_pago_badge",
        "monto_total_display",
        "saldo_pendiente_display",
        "estado_pago_badge",
    ]
    list_filter = ["estado_pago", "tipo_pago", "fecha"]
    search_fields = ["proveedor__razon_social", "nro_factura_proveedor"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["proveedor"]
    date_hierarchy = "fecha"
    ordering = ["-fecha"]
    inlines = [DetalleCompraInline]
    fieldsets = (
        ("Datos de la Compra", {
            "fields": ("proveedor", "tipo_pago", "fecha")
        }),
        ("Montos", {
            "fields": ("monto_total",)
        }),
        ("Factura del Proveedor", {
            "fields": ("nro_factura_proveedor",)
        }),
        ("Estado", {
            "fields": ("estado_pago", "observaciones")
        }),
        ("Medio de Pago", {
            "fields": ("medio_pago",)
        }),
        ("Auditoría", {
            "fields": ("creado_por", "fecha_creacion"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        """Anota total pagado para evitar N+1 queries."""
        cero = Value(0, output_field=models.DecimalField())
        return super().get_queryset(request).annotate(
            _total_pagado=Coalesce(
                Sum("aplicaciones_pago__monto_aplicado"),
                cero,
            )
        )

    def get_readonly_fields(self, request, obj=None):
        """Compras pagadas inmutables."""
        if obj and obj.estado_pago == "PAGADO":
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def proveedor_link(self, obj):
        url = reverse("admin:compras_proveedor_change", args=[obj.proveedor.pk])
        return format_html('<a href="{}">{}</a>', url, obj.proveedor.razon_social)
    proveedor_link.short_description = "Proveedor"

    def tipo_pago_badge(self, obj):
        colors = {"CONTADO": "#28a745", "CREDITO": "#fd7e14"}
        color = colors.get(obj.tipo_pago, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_tipo_pago_display(),
        )
    tipo_pago_badge.short_description = "Tipo"

    def monto_total_display(self, obj):
        return f"₲{obj.monto_total:,.0f}"
    monto_total_display.short_description = "Total"

    def saldo_pendiente_display(self, obj):
        total_pagado = getattr(obj, "_total_pagado", 0) or 0
        saldo = obj.monto_total - total_pagado
        if saldo <= 0:
            return format_html('<span style="color:#28a745;">₲0</span>')
        return format_html('<span style="color:#dc3545;">₲{:,}</span>', saldo)
    saldo_pendiente_display.short_description = "Saldo Pend."

    def estado_pago_badge(self, obj):
        colors = {"PAGADO": "#28a745", "PARCIAL": "#ffc107", "PENDIENTE": "#dc3545"}
        color = colors.get(obj.estado_pago, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_estado_pago_display(),
        )
    estado_pago_badge.short_description = "Estado Pago"


# ==============================================================================
# PAGO A PROVEEDOR
# ==============================================================================

@admin.register(PagoProveedor)
class PagoProveedorAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "proveedor_link",
        "monto_total_display",
        "medio_pago_link",
        "estado_badge",
        "fecha",
    ]
    list_filter = ["estado", "medio_pago", "fecha"]
    search_fields = ["proveedor__razon_social", "referencia"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["proveedor", "medio_pago"]
    date_hierarchy = "fecha"
    ordering = ["-fecha"]
    fieldsets = (
        ("Datos del Pago", {
            "fields": ("proveedor", "monto_total", "medio_pago")
        }),
        ("Referencia", {
            "fields": ("referencia",)
        }),
        ("Estado", {
            "fields": ("estado", "observaciones")
        }),
        ("Auditoría", {
            "fields": ("creado_por", "fecha_creacion"),
            "classes": ("collapse",),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Pagos conciliados/rechazados inmutables."""
        if obj and obj.estado in ("CONCILIADO", "RECHAZADO"):
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        """No permite eliminar pagos conciliados o rechazados."""
        if obj and obj.estado in ("CONCILIADO", "RECHAZADO"):
            return False
        return super().has_delete_permission(request, obj)

    def proveedor_link(self, obj):
        url = reverse("admin:compras_proveedor_change", args=[obj.proveedor.pk])
        return format_html('<a href="{}">{}</a>', url, obj.proveedor.razon_social)
    proveedor_link.short_description = "Proveedor"

    def monto_total_display(self, obj):
        return f"₲{obj.monto_total:,.0f}"
    monto_total_display.short_description = "Monto"

    def medio_pago_link(self, obj):
        url = reverse("admin:core_mediopago_change", args=[obj.medio_pago.pk])
        return format_html('<a href="{}">{}</a>', url, obj.medio_pago.descripcion)
    medio_pago_link.short_description = "Medio de Pago"

    def estado_badge(self, obj):
        colors = {"PENDIENTE": "#ffc107", "CONCILIADO": "#28a745", "RECHAZADO": "#dc3545"}
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_estado_display(),
        )
    estado_badge.short_description = "Estado"


# ==============================================================================
# APLICACIÓN DE PAGO A COMPRA
# ==============================================================================

@admin.register(AplicacionPagoCompra)
class AplicacionPagoCompraAdmin(admin.ModelAdmin):
    list_display = ["id", "pago_link", "compra_link", "monto_aplicado_display"]
    search_fields = ["pago__proveedor__razon_social", "pago__referencia"]
    list_select_related = ["pago", "compra"]

    def get_readonly_fields(self, request, obj=None):
        """Aplicación de pago inmutable una vez creada."""
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []

    def has_delete_permission(self, request, obj=None):
        """No permite eliminar aplicaciones de pago."""
        return False

    def pago_link(self, obj):
        url = reverse("admin:compras_pagoproveedor_change", args=[obj.pago.pk])
        return format_html('<a href="{}">Pago #{}</a>', url, obj.pago.pk)
    pago_link.short_description = "Pago"

    def compra_link(self, obj):
        url = reverse("admin:compras_compra_change", args=[obj.compra.pk])
        return format_html('<a href="{}">Compra #{}</a>', url, obj.compra.pk)
    compra_link.short_description = "Compra"

    def monto_aplicado_display(self, obj):
        return f"₲{obj.monto_aplicado:,.0f}"
    monto_aplicado_display.short_description = "Monto Aplicado"


# ==============================================================================
# NOTA DE CRÉDITO PROVEEDOR
# ==============================================================================

@admin.register(NotaCreditoProveedor)
class NotaCreditoProveedorAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "proveedor_link",
        "compra_original_link",
        "monto_total_display",
        "estado_badge",
        "fecha",
    ]
    list_filter = ["estado", "fecha"]
    search_fields = ["proveedor__razon_social", "nro_factura_compra"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["proveedor", "compra_original"]
    date_hierarchy = "fecha"
    ordering = ["-fecha"]
    fieldsets = (
        ("Datos de la Nota", {
            "fields": ("proveedor", "compra_original", "monto_total", "nro_factura_compra")
        }),
        ("Estado", {
            "fields": ("estado", "observacion")
        }),
        ("Auditoría", {
            "fields": ("creado_por", "fecha_creacion"),
            "classes": ("collapse",),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Nota de crédito inmutable una vez aplicada o anulada."""
        if obj and obj.estado in ("APLICADA", "ANULADA"):
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        """No permite eliminar notas aplicadas o anuladas."""
        if obj and obj.estado in ("APLICADA", "ANULADA"):
            return False
        return super().has_delete_permission(request, obj)

    def proveedor_link(self, obj):
        url = reverse("admin:compras_proveedor_change", args=[obj.proveedor.pk])
        return format_html('<a href="{}">{}</a>', url, obj.proveedor.razon_social)
    proveedor_link.short_description = "Proveedor"

    def compra_original_link(self, obj):
        if obj.compra_original:
            url = reverse("admin:compras_compra_change", args=[obj.compra_original.pk])
            return format_html('<a href="{}">Compra #{}</a>', url, obj.compra_original.pk)
        return "-"
    compra_original_link.short_description = "Compra Original"

    def monto_total_display(self, obj):
        return f"₲{obj.monto_total:,.0f}"
    monto_total_display.short_description = "Monto"

    def estado_badge(self, obj):
        colors = {"EMITIDA": "#ffc107", "APLICADA": "#28a745", "ANULADA": "#6c757d"}
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_estado_display(),
        )
    estado_badge.short_description = "Estado"


# ==============================================================================
# DETALLE DE NOTA DE CRÉDITO PROVEEDOR
# ==============================================================================

@admin.register(DetalleNotaCreditoProveedor)
class DetalleNotaCreditoProveedorAdmin(admin.ModelAdmin):
    list_display = ["id", "nota_credito_link", "producto_link", "cantidad", "subtotal_display"]
    search_fields = ["nota_credito__proveedor__razon_social", "producto__descripcion"]
    list_select_related = ["nota_credito", "producto"]

    def get_readonly_fields(self, request, obj=None):
        """Detalle inmutable una vez creado."""
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []

    def has_delete_permission(self, request, obj=None):
        """No permite eliminar detalles de notas de crédito."""
        return False

    def nota_credito_link(self, obj):
        url = reverse("admin:compras_notacreditoproveedor_change", args=[obj.nota_credito.pk])
        return format_html('<a href="{}">NC #{}</a>', url, obj.nota_credito.pk)
    nota_credito_link.short_description = "Nota de Crédito"

    def producto_link(self, obj):
        url = reverse("admin:productos_producto_change", args=[obj.producto.pk])
        return format_html('<a href="{}">{}</a>', url, obj.producto.descripcion)
    producto_link.short_description = "Producto"

    def subtotal_display(self, obj):
        return f"₲{obj.subtotal:,.0f}"
    subtotal_display.short_description = "Subtotal"


# ==============================================================================
# ORDEN DE COMPRA
# ==============================================================================

class DetalleOrdenCompraInline(admin.TabularInline):
    model = DetalleOrdenCompra
    extra = 0
    fields = ["producto", "cantidad", "costo_unitario", "subtotal"]
    readonly_fields = ["subtotal"]
    autocomplete_fields = ["producto"]


@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = ["id", "proveedor_link", "estado_badge", "monto_total_display", "fecha_creacion"]
    list_filter = ["estado"]
    search_fields = ["proveedor__razon_social"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["proveedor"]
    ordering = ["-fecha_creacion"]
    inlines = [DetalleOrdenCompraInline]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.estado in ("APROBADA", "CONVERTIDA", "RECHAZADA"):
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def proveedor_link(self, obj):
        url = reverse("admin:compras_proveedor_change", args=[obj.proveedor.pk])
        return format_html('<a href="{}">{}</a>', url, obj.proveedor.razon_social)
    proveedor_link.short_description = "Proveedor"

    def monto_total_display(self, obj):
        return f"₲{obj.monto_total:,.0f}" if obj.monto_total else "-"
    monto_total_display.short_description = "Total"

    def estado_badge(self, obj):
        colors = {
            "BORRADOR": "#6c757d",
            "PENDIENTE": "#ffc107",
            "APROBADA": "#28a745",
            "RECHAZADA": "#dc3545",
            "CONVERTIDA": "#0d6efd",
        }
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color, obj.get_estado_display(),
        )
    estado_badge.short_description = "Estado"
