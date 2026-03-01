from django.contrib import admin
from .models import (
    Cajas,
    CierresCaja,
    MovimientosCaja,
    DocumentosTributarios,
    Timbrados,
    Impuestos
)

@admin.register(Cajas)
class CajasAdmin(admin.ModelAdmin):
    list_display = ['id_caja', 'nombre_caja', 'ubicacion', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre_caja', 'ubicacion']
    ordering = ['nombre_caja']

@admin.register(CierresCaja)
class CierresCajaAdmin(admin.ModelAdmin):
    list_display = ['id_cierre', 'id_caja', 'fecha_hora_apertura', 'fecha_hora_cierre', 'estado']
    list_filter = ['estado', 'fecha_hora_cierre']
    ordering = ['-fecha_hora_apertura']

@admin.register(MovimientosCaja)
class MovimientosCajaAdmin(admin.ModelAdmin):
    list_display = ['id_movimiento', 'id_cierre', 'tipo_movimiento', 'monto', 'fecha_movimiento']
    list_filter = ['tipo_movimiento', 'fecha_movimiento']
    search_fields = ['descripcion']
    ordering = ['-fecha_movimiento']

@admin.register(DocumentosTributarios)
class DocumentosTributariosAdmin(admin.ModelAdmin):
    list_display = ['id_documento', 'nro_secuencial', 'tipo_documento', 'fecha_emision', 'estado_sifen']
    list_filter = ['tipo_documento', 'estado_sifen', 'fecha_emision']
    search_fields = ['cdc']
    ordering = ['-fecha_emision']

@admin.register(Timbrados)
class TimbradosAdmin(admin.ModelAdmin):
    list_display = ['nro_timbrado', 'tipo_documento', 'fecha_inicio', 'fecha_fin', 'activo']
    list_filter = ['activo', 'tipo_documento']
    ordering = ['-fecha_inicio']

@admin.register(Impuestos)
class ImpuestosAdmin(admin.ModelAdmin):
    list_display = ['id_impuesto', 'nombre_impuesto', 'porcentaje', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre_impuesto']
    ordering = ['nombre_impuesto']
