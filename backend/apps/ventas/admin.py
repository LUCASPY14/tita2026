"""
Admin para la app ventas
Gestión de ventas, detalles, pagos y notas de crédito
"""

from django.contrib import admin
from django.db import models
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Venta,
    DetalleVenta,
    PagoVenta,
    AplicacionPago,
    NotaCredito,
    DetalleNotaCredito,
    CondicionVenta,
)


# ==============================================================================
# DETALLE DE VENTA (INLINE)
# ==============================================================================

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    fields = ["producto", "cantidad", "precio_unitario", "subtotal", "iva_10", "iva_5"]
    readonly_fields = ["subtotal", "iva_10", "iva_5"]
    autocomplete_fields = ["producto"]

    def has_add_permission(self, request, obj=None):
        """No permite agregar detalles si la venta está anulada."""
        if obj and obj.estado == "ANULADA":
            return False
        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        """No permite modificar detalles si la venta está anulada."""
        if obj and obj.estado == "ANULADA":
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """No permite eliminar detalles si la venta está anulada."""
        if obj and obj.estado == "ANULADA":
            return False
        return super().has_delete_permission(request, obj)


# ==============================================================================
# VENTA
# ==============================================================================

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "fecha",
        "cliente_link",
        "tipo_badge",
        "monto_total_display",
        "saldo_pendiente_display",
        "estado_pago_badge",
        "estado_badge",
    ]
    list_filter = ["estado", "estado_pago", "tipo", "fecha"]
    search_fields = ["cliente__ruc_ci", "cliente__nombres", "nro_factura"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["cliente"]
    date_hierarchy = "fecha"
    ordering = ["-fecha"]
    inlines = [DetalleVentaInline]
    fieldsets = (
        ("Datos de la Venta", {
            "fields": ("cliente", "hijo", "tipo", "fecha")
        }),
        ("Montos", {
            "fields": (
                "monto_total", "monto_gravada_10", "monto_gravada_5", "monto_exenta",
                "iva_10", "iva_5",
            )
        }),
        ("Facturación", {
            "fields": ("nro_factura", "genera_factura_legal", "factura")
        }),
        ("Estado", {
            "fields": ("estado", "estado_pago", "motivo_credito")
        }),
        ("Medio de Pago y Caja", {
            "fields": ("medio_pago", "caja")
        }),
        ("Auditoría", {
            "fields": ("cajero", "autorizado_por", "fecha_creacion"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        """Anota total pagado para evitar N+1 queries en saldo_pendiente_display."""
        cero = Value(0, output_field=models.DecimalField())
        return super().get_queryset(request).annotate(
            _total_pagado=Coalesce(
                Sum("aplicaciones_pago__monto_aplicado"),
                cero,
            )
        )

    def get_readonly_fields(self, request, obj=None):
        """Ventas anuladas inmutables."""
        if obj and obj.estado == "ANULADA":
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def cliente_link(self, obj):
        url = reverse("admin:clientes_cliente_change", args=[obj.cliente.pk])
        return format_html('<a href="{}">{}</a>', url, obj.cliente.nombre_completo)
    cliente_link.short_description = "Cliente"

    def tipo_badge(self, obj):
        colors = {"CONTADO": "#28a745", "CREDITO": "#fd7e14"}
        color = colors.get(obj.tipo, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_tipo_display(),
        )
    tipo_badge.short_description = "Tipo"

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

    def estado_badge(self, obj):
        colors = {"ACTIVA": "#28a745", "ANULADA": "#dc3545"}
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.get_estado_display(),
        )
    estado_badge.short_description = "Estado"


# ==============================================================================
# PAGO DE VENTA
# ==============================================================================

@admin.register(PagoVenta)
class PagoVentaAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "cliente_link",
        "venta_link",
        "monto_display",
        "medio_pago_link",
        "estado_badge",
        "fecha",
    ]
    list_filter = ["estado", "medio_pago", "fecha"]
    search_fields = ["cliente__ruc_ci", "referencia", "ref_transferencia"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["cliente", "venta", "medio_pago"]
    date_hierarchy = "fecha"
    ordering = ["-fecha"]
    fieldsets = (
        ("Datos del Pago", {
            "fields": ("cliente", "venta", "monto", "monto_comision", "medio_pago")
        }),
        ("Referencias", {
            "fields": ("referencia", "ref_pago_pos", "ref_transferencia", "banco_emisor")
        }),
        ("Estado y Cierre", {
            "fields": ("estado", "cierre_caja")
        }),
        ("Auditoría", {
            "fields": ("cajero", "observaciones", "fecha_creacion"),
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

    def cliente_link(self, obj):
        url = reverse("admin:clientes_cliente_change", args=[obj.cliente.pk])
        return format_html('<a href="{}">{}</a>', url, obj.cliente.nombre_completo)
    cliente_link.short_description = "Cliente"

    def venta_link(self, obj):
        if obj.venta:
            url = reverse("admin:ventas_venta_change", args=[obj.venta.pk])
            return format_html('<a href="{}">Venta #{}</a>', url, obj.venta.pk)
        return format_html('<span style="color:#6c757d;">A cuenta</span>')
    venta_link.short_description = "Venta"

    def monto_display(self, obj):
        return f"₲{obj.monto:,.0f}"
    monto_display.short_description = "Monto"

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
# APLICACIÓN DE PAGO
# ==============================================================================

@admin.register(AplicacionPago)
class AplicacionPagoAdmin(admin.ModelAdmin):
    list_display = ["id", "pago_link", "venta_link", "monto_aplicado_display"]
    search_fields = ["pago__cliente__ruc_ci", "pago__referencia"]
    list_select_related = ["pago", "venta"]

    def get_readonly_fields(self, request, obj=None):
        """Aplicación de pago inmutable una vez creada."""
        if obj:
            return [f.name for f in self.model._meta.fields]
        return []

    def has_delete_permission(self, request, obj=None):
        """No permite eliminar aplicaciones de pago."""
        return False

    def pago_link(self, obj):
        url = reverse("admin:ventas_pagoventa_change", args=[obj.pago.pk])
        return format_html('<a href="{}">Pago #{}</a>', url, obj.pago.pk)
    pago_link.short_description = "Pago"

    def venta_link(self, obj):
        url = reverse("admin:ventas_venta_change", args=[obj.venta.pk])
        return format_html('<a href="{}">Venta #{}</a>', url, obj.venta.pk)
    venta_link.short_description = "Venta"

    def monto_aplicado_display(self, obj):
        return f"₲{obj.monto_aplicado:,.0f}"
    monto_aplicado_display.short_description = "Monto Aplicado"


# ==============================================================================
# NOTA DE CRÉDITO
# ==============================================================================

@admin.register(NotaCredito)
class NotaCreditoAdmin(admin.ModelAdmin):
    list_display = [
        "nro_nota_credito",
        "cliente_link",
        "venta_origen_link",
        "monto_total_display",
        "estado_badge",
        "fecha_emision",
    ]
    list_filter = ["estado", "fecha_emision"]
    search_fields = ["nro_nota_credito", "cliente__ruc_ci", "motivo"]
    readonly_fields = ["fecha_creacion"]
    list_select_related = ["cliente", "venta_origen"]
    date_hierarchy = "fecha_emision"
    ordering = ["-fecha_emision"]
    fieldsets = (
        ("Datos de la Nota", {
            "fields": ("nro_nota_credito", "cliente", "venta_origen", "monto_total")
        }),
        ("Detalle", {
            "fields": ("motivo", "estado", "fecha_emision")
        }),
        ("Auditoría", {
            "fields": ("empleado_autoriza", "fecha_creacion"),
            "classes": ("collapse",),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Nota de crédito inmutable una vez aplicada o anulada."""
        if obj and obj.estado in ("APLICADA", "ANULADA"):
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def cliente_link(self, obj):
        url = reverse("admin:clientes_cliente_change", args=[obj.cliente.pk])
        return format_html('<a href="{}">{}</a>', url, obj.cliente.nombre_completo)
    cliente_link.short_description = "Cliente"

    def venta_origen_link(self, obj):
        if obj.venta_origen:
            url = reverse("admin:ventas_venta_change", args=[obj.venta_origen.pk])
            return format_html('<a href="{}">Venta #{}</a>', url, obj.venta_origen.pk)
        return "-"
    venta_origen_link.short_description = "Venta Origen"

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
# DETALLE DE NOTA DE CRÉDITO
# ==============================================================================

@admin.register(DetalleNotaCredito)
class DetalleNotaCreditoAdmin(admin.ModelAdmin):
    list_display = ["id", "nota_credito_link", "producto_link", "cantidad", "subtotal_display"]
    search_fields = ["nota_credito__nro_nota_credito", "producto__descripcion"]
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
        url = reverse("admin:ventas_notacredito_change", args=[obj.nota_credito.pk])
        return format_html('<a href="{}">NC #{}</a>', url, obj.nota_credito.nro_nota_credito)
    nota_credito_link.short_description = "Nota de Crédito"

    def producto_link(self, obj):
        url = reverse("admin:productos_producto_change", args=[obj.producto.pk])
        return format_html('<a href="{}">{}</a>', url, obj.producto.descripcion)
    producto_link.short_description = "Producto"

    def subtotal_display(self, obj):
        return f"₲{obj.subtotal:,.0f}"
    subtotal_display.short_description = "Subtotal"


# ==============================================================================
# CONDICIÓN DE VENTA
# ==============================================================================

@admin.register(CondicionVenta)
class CondicionVentaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "plazo_dias"]
    search_fields = ["nombre"]
