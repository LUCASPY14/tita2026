from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from decimal import Decimal
from .models import (
    Proveedores,
    Compras,
    DetallesCompra,
    PagosProveedores,
    AplicacionPagosCompras,
    NotasCreditoProveedor,
    DetallesNotaCreditoProveedor,
)


@admin.register(Proveedores)
class ProveedoresAdmin(admin.ModelAdmin):
    list_display = [
        "id_proveedor",
        "razon_social",
        "ruc_display",
        "telefono",
        "email",
        "ciudad",
        "estado_badge",
        "fecha_registro",
    ]
    list_filter = ["estado", "ciudad", "fecha_registro"]
    search_fields = ["razon_social", "ruc", "email", "telefono"]
    ordering = ["razon_social"]
    date_hierarchy = "fecha_registro"
    list_per_page = 25

    fieldsets = (
        ("Información Básica", {"fields": ("razon_social", "ruc", "estado")}),
        ("Datos de Contacto", {"fields": ("telefono", "email", "direccion", "ciudad")}),
        ("Auditoría", {"fields": ("fecha_registro",), "classes": ("collapse",)}),
    )

    readonly_fields = ["fecha_registro"]

    def ruc_display(self, obj):
        """Muestra RUC con formato"""
        return format_html("<code>{}</code>", obj.ruc)

    ruc_display.short_description = "RUC"

    def estado_badge(self, obj):
        """Badge coloreado para estado estado/inactivo"""
        if obj.estado:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
                "ACTIVO",
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            "INACTIVO",
        )

    estado_badge.short_description = "Estado"


@admin.register(Compras)
class ComprasAdmin(admin.ModelAdmin):
    list_display = [
        "id_compra",
        "nro_factura_display",
        "proveedor_nombre",
        "fecha",
        "tipo_pago_badge",
        "medio_pago_display",
        "monto_display",
        "saldo_display",
        "estado_badge",
    ]
    list_filter = ["estado_pago", "tipo_pago", "id_medio_pago", "fecha", "id_proveedor"]
    search_fields = ["nro_factura", "id_proveedor__razon_social", "observaciones"]
    ordering = ["-fecha", "-id_compra"]
    date_hierarchy = "fecha"
    list_per_page = 20

    fieldsets = (
        (
            "Información de Compra",
            {"fields": ("id_proveedor", "nro_factura", "fecha", "id_documento")},
        ),
        (
            "Forma de Pago",
            {"fields": ("tipo_pago", "id_medio_pago", "estado_pago")},
        ),
        ("Montos", {"fields": ("monto_total", "saldo_pendiente")}),
        ("Observaciones", {"fields": ("observaciones",), "classes": ("collapse",)}),
    )

    readonly_fields = []

    actions = ["marcar_como_pagado", "generar_orden_pago"]

    def nro_factura_display(self, obj):
        """Muestra número de factura con formato"""
        if obj.nro_factura:
            return format_html("<strong>{}</strong>", obj.nro_factura)
        return format_html('<em style="color: #999;">{}</em>', "Sin factura")

    nro_factura_display.short_description = "Nro. Factura"

    def tipo_pago_badge(self, obj):
        """Badge para tipo de pago"""
        if obj.tipo_pago == "Contado":
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
                "CONTADO",
            )
        else:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
                "CRÉDITO",
            )

    tipo_pago_badge.short_description = "Tipo Pago"

    def medio_pago_display(self, obj):
        """Muestra el medio de pago"""
        if obj.id_medio_pago:
            return obj.id_medio_pago.descripcion
        return format_html('<em style="color: #999;">{}</em>', "No especificado")

    medio_pago_display.short_description = "Medio de Pago"

    def proveedor_nombre(self, obj):
        """Muestra nombre del proveedor"""
        return obj.id_proveedor.razon_social

    proveedor_nombre.short_description = "Proveedor"
    proveedor_nombre.admin_order_field = "id_proveedor__razon_social"

    def monto_display(self, obj):
        """Muestra monto total formateado"""
        monto_formateado = f"{obj.monto_total:,.0f}"
        return format_html("₲ {}", monto_formateado)

    monto_display.short_description = "Monto Total"
    monto_display.admin_order_field = "monto_total"

    def saldo_display(self, obj):
        """Muestra saldo pendiente formateado"""
        if obj.saldo_pendiente and obj.saldo_pendiente > 0:
            color = "#dc3545" if obj.saldo_pendiente == obj.monto_total else "#fd7e14"
            saldo_formateado = f"{obj.saldo_pendiente:,.0f}"
            return format_html(
                '<span style="color: {}; font-weight: bold;">₲ {}</span>',
                color,
                saldo_formateado,
            )
        return format_html('<span style="color: #28a745;">{}</span>', "₲ 0")

    saldo_display.short_description = "Saldo Pendiente"
    saldo_display.admin_order_field = "saldo_pendiente"

    def estado_badge(self, obj):
        """Badge coloreado según estado de pago"""
        colores = {
            "Pendiente": ("#ffc107", "#000"),
            "Confirmado": ("#17a2b8", "#fff"),
            "Parcial": ("#fd7e14", "#fff"),
            "Pagado": ("#28a745", "#fff"),
            "Cancelado": ("#6c757d", "#fff"),
        }
        bg_color, text_color = colores.get(obj.estado_pago, ("#6c757d", "#fff"))
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            bg_color,
            text_color,
            obj.estado_pago.upper(),
        )

    estado_badge.short_description = "Estado"

    def marcar_como_pagado(self, request, queryset):
        """Acción para marcar compras como pagadas"""
        updated = queryset.filter(estado_pago__in=["Confirmado", "Parcial"]).update(
            estado_pago="Pagado", saldo_pendiente=0
        )
        self.message_user(request, f"{updated} compra(s) marcada(s) como pagada(s)")

    marcar_como_pagado.short_description = "Marcar como Pagado"

    def generar_orden_pago(self, request, queryset):
        """Acción para generar orden de pago (placeholder)"""
        count = queryset.filter(saldo_pendiente__gt=0).count()
        self.message_user(request, f"Generada orden de pago para {count} compra(s)")

    generar_orden_pago.short_description = "Generar Orden de Pago"


@admin.register(DetallesCompra)
class DetallesCompraAdmin(admin.ModelAdmin):
    list_display = [
        "id_detalle",
        "compra_info",
        "producto_descripcion",
        "cantidad",
        "costo_display",
        "subtotal_display",
        "iva_display",
    ]
    list_filter = ["id_compra__fecha", "id_compra__id_proveedor"]
    search_fields = ["id_producto__descripcion", "id_compra__nro_factura"]
    ordering = ["-id_compra__fecha", "id_detalle"]
    list_per_page = 30

    def compra_info(self, obj):
        """Muestra información de la compra"""
        return format_html("Compra #{} - {}", obj.id_compra_id, obj.id_compra.nro_factura or "S/F")

    compra_info.short_description = "Compra"
    compra_info.admin_order_field = "id_compra"

    def producto_descripcion(self, obj):
        """Muestra descripción del producto"""
        return obj.id_producto.descripcion

    producto_descripcion.short_description = "Producto"
    producto_descripcion.admin_order_field = "id_producto__descripcion"

    def costo_display(self, obj):
        """Muestra costo unitario formateado"""
        costo_formateado = f"{obj.costo_unitario:,.2f}"
        return format_html("₲ {}", costo_formateado)

    costo_display.short_description = "Costo Unit."
    costo_display.admin_order_field = "costo_unitario"

    def subtotal_display(self, obj):
        """Muestra subtotal formateado"""
        subtotal_formateado = f"{obj.subtotal:,.2f}"
        return format_html("<strong>₲ {}</strong>", subtotal_formateado)

    subtotal_display.short_description = "Subtotal"
    subtotal_display.admin_order_field = "subtotal"

    def iva_display(self, obj):
        """Muestra IVA formateado"""
        if obj.monto_iva:
            iva_formateado = f"{obj.monto_iva:,.2f}"
            return format_html("₲ {}", iva_formateado)
        return "-"

    iva_display.short_description = "IVA"


@admin.register(PagosProveedores)
class PagosProveedoresAdmin(admin.ModelAdmin):
    list_display = [
        "id_pago_proveedor",
        "medio_pago_nombre",
        "fecha_creacion",
        "monto_total_aplicado",
    ]
    list_filter = ["fecha_creacion", "id_medio_pago"]
    search_fields = ["id_medio_pago__nombre"]
    ordering = ["-fecha_creacion"]
    date_hierarchy = "fecha_creacion"
    list_per_page = 25

    def medio_pago_nombre(self, obj):
        """Muestra nombre del medio de pago"""
        return obj.id_medio_pago.nombre if hasattr(obj.id_medio_pago, "nombre") else str(obj.id_medio_pago)

    medio_pago_nombre.short_description = "Medio de Pago"

    def monto_total_aplicado(self, obj):
        """Calcula y muestra el monto total aplicado del pago"""
        total = AplicacionPagosCompras.objects.filter(id_pago_proveedor=obj).aggregate(total=Sum("monto_aplicado"))[
            "total"
        ] or Decimal("0.00")

        if total > 0:
            total_formateado = f"{total:,.2f}"
            return format_html('<span style="color: #28a745; font-weight: bold;">₲ {}</span>', total_formateado)
        return format_html('<em style="color: #999;">{}</em>', "₲ 0.00")

    monto_total_aplicado.short_description = "Monto Aplicado"


@admin.register(AplicacionPagosCompras)
class AplicacionPagosComprasAdmin(admin.ModelAdmin):
    list_display = ["id_aplicacion", "pago_info", "compra_info", "monto_display"]
    list_filter = ["id_pago_proveedor__fecha_creacion", "id_compra__id_proveedor"]
    search_fields = ["id_compra__nro_factura", "id_pago_proveedor__id_pago_proveedor"]
    ordering = ["-id_pago_proveedor__fecha_creacion"]
    list_per_page = 30

    def pago_info(self, obj):
        """Muestra información del pago"""
        return format_html(
            "Pago #{} - {}",
            obj.id_pago_proveedor_id,
            obj.id_pago_proveedor.fecha_creacion.strftime("%d/%m/%Y"),
        )

    pago_info.short_description = "Pago"

    def compra_info(self, obj):
        """Muestra información de la compra"""
        return format_html("Compra #{} - {}", obj.id_compra_id, obj.id_compra.nro_factura or "S/F")

    compra_info.short_description = "Compra"

    def monto_display(self, obj):
        """Muestra monto aplicado formateado"""
        monto_formateado = f"{obj.monto_aplicado:,.2f}"
        return format_html('<strong style="color: #28a745;">₲ {}</strong>', monto_formateado)

    monto_display.short_description = "Monto Aplicado"
    monto_display.admin_order_field = "monto_aplicado"


@admin.register(NotasCreditoProveedor)
class NotasCreditoProveedorAdmin(admin.ModelAdmin):
    list_display = [
        "id_nota_proveedor",
        "nro_factura_display",
        "proveedor_nombre",
        "fecha",
        "monto_display",
        "estado_badge",
        "fecha_creacion",
    ]
    list_filter = ["estado", "fecha", "id_proveedor"]
    search_fields = ["nro_factura_compra", "id_proveedor__razon_social", "observacion"]
    ordering = ["-fecha", "-id_nota_proveedor"]
    date_hierarchy = "fecha"
    list_per_page = 20

    fieldsets = (
        (
            "Información de NC",
            {"fields": ("id_proveedor", "id_compra_original", "nro_factura_compra", "fecha")},
        ),
        ("Montos y Estado", {"fields": ("monto_total", "estado")}),
        ("Observaciones", {"fields": ("observacion",), "classes": ("collapse",)}),
        ("Auditoría", {"fields": ("fecha_creacion",), "classes": ("collapse",)}),
    )

    readonly_fields = ["fecha_creacion"]

    actions = ["marcar_como_aplicado", "rechazar_nota"]

    def nro_factura_display(self, obj):
        """Muestra número de factura con formato"""
        if obj.nro_factura_compra:
            return format_html("<code>{}</code>", obj.nro_factura_compra)
        return format_html('<em style="color: #999;">{}</em>', "S/F")

    nro_factura_display.short_description = "Nro. Factura"

    def proveedor_nombre(self, obj):
        """Muestra nombre del proveedor"""
        return obj.id_proveedor.razon_social

    proveedor_nombre.short_description = "Proveedor"
    proveedor_nombre.admin_order_field = "id_proveedor__razon_social"

    def monto_display(self, obj):
        """Muestra monto total formateado"""
        monto_formateado = f"{obj.monto_total:,.2f}"
        return format_html('<span style="color: #dc3545; font-weight: bold;">₲ {}</span>', monto_formateado)

    monto_display.short_description = "Monto NC"
    monto_display.admin_order_field = "monto_total"

    def estado_badge(self, obj):
        """Badge coloreado según estado"""
        colores = {
            "Pendiente": ("#ffc107", "#000"),
            "Aplicado": ("#28a745", "#fff"),
            "Rechazado": ("#dc3545", "#fff"),
        }
        bg_color, text_color = colores.get(obj.estado, ("#6c757d", "#fff"))
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            bg_color,
            text_color,
            obj.estado.upper(),
        )

    estado_badge.short_description = "Estado"

    def marcar_como_aplicado(self, request, queryset):
        """Acción para marcar NCs como aplicadas"""
        updated = queryset.filter(estado="Pendiente").update(estado="Aplicado")
        self.message_user(request, f"{updated} nota(s) de crédito marcada(s) como aplicada(s)")

    marcar_como_aplicado.short_description = "Marcar como Aplicado"

    def rechazar_nota(self, request, queryset):
        """Acción para rechazar NCs"""
        updated = queryset.filter(estado="Pendiente").update(estado="Rechazado")
        self.message_user(request, f"{updated} nota(s) de crédito rechazada(s)")

    rechazar_nota.short_description = "Rechazar NC"


@admin.register(DetallesNotaCreditoProveedor)
class DetallesNotaCreditoProveedorAdmin(admin.ModelAdmin):
    list_display = [
        "id_detalle_nc_proveedor",
        "nota_info",
        "producto_descripcion",
        "cantidad",
        "precio_display",
        "subtotal_display",
    ]
    list_filter = ["id_nota_proveedor__fecha", "id_nota_proveedor__id_proveedor"]
    search_fields = ["id_producto__descripcion", "id_nota_proveedor__nro_factura_compra"]
    ordering = ["-id_nota_proveedor__fecha", "id_detalle_nc_proveedor"]
    list_per_page = 30

    def nota_info(self, obj):
        """Muestra información de la NC"""
        return format_html(
            "NC #{} - Fact. {}",
            obj.id_nota_proveedor_id,
            obj.id_nota_proveedor.nro_factura_compra or "S/F",
        )

    nota_info.short_description = "Nota de Crédito"

    def producto_descripcion(self, obj):
        """Muestra descripción del producto"""
        return obj.id_producto.descripcion

    producto_descripcion.short_description = "Producto"
    producto_descripcion.admin_order_field = "id_producto__descripcion"

    def precio_display(self, obj):
        """Muestra precio unitario formateado"""
        precio_formateado = f"{obj.precio_unitario:,.2f}"
        return format_html("₲ {}", precio_formateado)

    precio_display.short_description = "Precio Unit."
    precio_display.admin_order_field = "precio_unitario"

    def subtotal_display(self, obj):
        """Muestra subtotal formateado"""
        subtotal_formateado = f"{obj.subtotal:,.2f}"
        return format_html('<strong style="color: #dc3545;">₲ {}</strong>', subtotal_formateado)

    subtotal_display.short_description = "Subtotal"
    subtotal_display.admin_order_field = "subtotal"
