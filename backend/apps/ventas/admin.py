from django.contrib import admin
from .models import Ventas, DetallesVenta, PagosVenta, NotasCreditoCliente, Promociones, CondicionVenta


@admin.register(Ventas)
class VentasAdmin(admin.ModelAdmin):
    list_display = ["id_venta", "fecha", "id_cliente", "monto_total", "estado_pago", "estado"]
    list_filter = ["estado_pago", "estado", "tipo_venta"]
    ordering = ["-fecha"]


@admin.register(DetallesVenta)
class DetallesVentaAdmin(admin.ModelAdmin):
    list_display = [
        "id_detalle",
        "id_venta",
        "id_producto",
        "cantidad",
        "precio_unitario",
        "subtotal",
    ]
    ordering = ["id_venta"]


@admin.register(PagosVenta)
class PagosVentaAdmin(admin.ModelAdmin):
    list_display = ["id_pago_venta", "id_venta", "monto", "fecha_pago", "estado"]
    list_filter = ["estado", "fecha_pago"]
    ordering = ["-fecha_pago"]


@admin.register(NotasCreditoCliente)
class NotasCreditoClienteAdmin(admin.ModelAdmin):
    list_display = [
        "id_nota",
        "nro_nota_credito",
        "id_cliente",
        "fecha_emision",
        "monto_total",
        "estado",
    ]
    list_filter = ["estado", "fecha_emision"]
    ordering = ["-fecha_emision"]


@admin.register(Promociones)
class PromocionesAdmin(admin.ModelAdmin):
    list_display = [
        "id_promocion",
        "nombre",
        "tipo_promocion",
        "fecha_inicio",
        "fecha_fin",
        "estado",
    ]
    list_filter = ["estado", "tipo_promocion"]
    search_fields = ["nombre", "codigo_promocion"]
    ordering = ["-fecha_inicio"]


@admin.register(CondicionVenta)
class CondicionVentaAdmin(admin.ModelAdmin):
    list_display = ['id_condicion_venta', 'nombre']
    search_fields = ['nombre']
