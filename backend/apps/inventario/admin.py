from django.contrib import admin
from .models import (
    StockUnico,
    MovimientosStock,
    AjustesInventario
)

@admin.register(StockUnico)
class StockUnicoAdmin(admin.ModelAdmin):
    list_display = ['id_stock', 'id_producto', 'cantidad', 'fecha_ultima_actualizacion']
    list_filter = ['fecha_ultima_actualizacion']
    ordering = ['id_producto']

@admin.register(MovimientosStock)
class MovimientosStockAdmin(admin.ModelAdmin):
    list_display = ['id_movimiento_stock', 'id_producto', 'tipo_movimiento', 'cantidad', 'fecha_hora']
    list_filter = ['tipo_movimiento', 'fecha_hora']
    ordering = ['-fecha_hora']

@admin.register(AjustesInventario)
class AjustesInventarioAdmin(admin.ModelAdmin):
    list_display = ['id_ajuste', 'tipo_ajuste', 'motivo', 'estado', 'fecha_hora']
    list_filter = ['tipo_ajuste', 'estado', 'fecha_hora']
    search_fields = ['motivo']
    ordering = ['-fecha_hora']
