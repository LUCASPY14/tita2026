from django.contrib import admin
from .models import (
    Proveedores,
    Compras,
    DetallesCompra,
    PagosProveedores,
    NotasCreditoProveedor
)

@admin.register(Proveedores)
class ProveedoresAdmin(admin.ModelAdmin):
    list_display = ['id_proveedor', 'razon_social', 'ruc', 'telefono', 'email', 'activo']
    list_filter = ['activo', 'ciudad']
    search_fields = ['razon_social', 'ruc', 'email']
    ordering = ['razon_social']

@admin.register(Compras)
class ComprasAdmin(admin.ModelAdmin):
    list_display = ['id_compra', 'id_proveedor', 'fecha', 'monto_total', 'estado_pago']
    list_filter = ['estado_pago', 'fecha']
    search_fields = ['nro_factura']
    ordering = ['-fecha']

@admin.register(DetallesCompra)
class DetallesCompraAdmin(admin.ModelAdmin):
    list_display = ['id_detalle', 'id_compra', 'id_producto', 'cantidad', 'costo_unitario', 'subtotal']
    ordering = ['id_compra']

@admin.register(PagosProveedores)
class PagosProveedoresAdmin(admin.ModelAdmin):
    list_display = ['id_pago_proveedor', 'id_medio_pago', 'fecha_creacion']
    list_filter = ['fecha_creacion']
    ordering = ['-fecha_creacion']

@admin.register(NotasCreditoProveedor)
class NotasCreditoProveedorAdmin(admin.ModelAdmin):
    list_display = ['id_nota_proveedor', 'nro_factura_compra', 'fecha', 'id_proveedor', 'monto_total', 'estado']
    list_filter = ['estado', 'fecha']
    ordering = ['-fecha']
