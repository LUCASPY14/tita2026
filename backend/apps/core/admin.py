from django.contrib import admin
from .models import (
    Tarjetas,
    CargasSaldo,
    ConsumosTarjeta,
    MediosPago,
    ConfiguracionSistema
)

@admin.register(Tarjetas)
class TarjetasAdmin(admin.ModelAdmin):
    list_display = ['nro_tarjeta', 'id_hijo', 'saldo_actual', 'estado', 'fecha_creacion']
    list_filter = ['estado', 'fecha_creacion']
    search_fields = ['nro_tarjeta', 'codigo_barras']
    ordering = ['nro_tarjeta']

@admin.register(CargasSaldo)
class CargasSaldoAdmin(admin.ModelAdmin):
    list_display = ['id_carga', 'nro_tarjeta', 'monto_cargado', 'fecha_carga', 'estado']
    list_filter = ['estado', 'fecha_carga']
    search_fields = ['referencia']
    ordering = ['-fecha_carga']

@admin.register(ConsumosTarjeta)
class ConsumosTarjetaAdmin(admin.ModelAdmin):
    list_display = ['id_consumo', 'nro_tarjeta', 'monto_consumido', 'fecha_consumo']
    list_filter = ['fecha_consumo']
    ordering = ['-fecha_consumo']

@admin.register(MediosPago)
class MediosPagoAdmin(admin.ModelAdmin):
    list_display = ['id_medio_pago', 'descripcion', 'activo']
    list_filter = ['activo']
    search_fields = ['descripcion']
    ordering = ['descripcion']

@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    list_display = ['id_config', 'clave', 'valor', 'tipo', 'categoria']
    list_filter = ['tipo', 'categoria']
    search_fields = ['clave', 'descripcion']
    ordering = ['categoria', 'clave']
