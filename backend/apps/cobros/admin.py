from django.contrib import admin
from .models import PagosClientes, AplicacionPagosClientes


@admin.register(PagosClientes)
class PagosClientesAdmin(admin.ModelAdmin):
    list_display = [
        'id_pago_cliente',
        'id_cliente',
        'monto_total',
        'fecha_pago',
        'id_medio_pago',
        'estado',
        'id_empleado_cajero'
    ]
    list_filter = ['estado', 'fecha_pago', 'id_medio_pago']
    search_fields = [
        'id_cliente__nombres',
        'id_cliente__apellidos',
        'id_cliente__ruc_ci',
        'referencia'
    ]
    readonly_fields = ['fecha_pago']
    date_hierarchy = 'fecha_pago'


@admin.register(AplicacionPagosClientes)
class AplicacionPagosClientesAdmin(admin.ModelAdmin):
    list_display = [
        'id_aplicacion',
        'id_pago_cliente',
        'id_venta',
        'monto_aplicado',
        'fecha_aplicacion'
    ]
    list_filter = ['fecha_aplicacion']
    search_fields = ['id_venta__nro_factura_venta']
    readonly_fields = ['fecha_aplicacion']
    date_hierarchy = 'fecha_aplicacion'
