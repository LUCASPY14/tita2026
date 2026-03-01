from django.contrib import admin
from .models import (
    PlanesAlmuerzo,
    TiposAlmuerzo,
    SuscripcionesAlmuerzo,
    RegistrosConsumoAlmuerzo,
    Alergenos
)

@admin.register(PlanesAlmuerzo)
class PlanesAlmuerzoAdmin(admin.ModelAdmin):
    list_display = ['id_plan_almuerzo', 'nombre_plan', 'precio_mensual', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre_plan']
    ordering = ['nombre_plan']

@admin.register(TiposAlmuerzo)
class TiposAlmuerzoAdmin(admin.ModelAdmin):
    list_display = ['id_tipo_almuerzo', 'nombre', 'precio_unitario', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre']
    ordering = ['nombre']

@admin.register(SuscripcionesAlmuerzo)
class SuscripcionesAlmuerzoAdmin(admin.ModelAdmin):
    list_display = ['id_suscripcion', 'id_hijo', 'id_plan_almuerzo', 'fecha_inicio', 'estado']
    list_filter = ['estado', 'fecha_inicio']
    ordering = ['-fecha_inicio']

@admin.register(RegistrosConsumoAlmuerzo)
class RegistrosConsumoAlmuerzoAdmin(admin.ModelAdmin):
    list_display = ['id_registro_consumo', 'fecha_consumo', 'hora_registro', 'id_hijo', 'estado']
    list_filter = ['estado', 'fecha_consumo']
    ordering = ['-fecha_consumo', 'hora_registro']

@admin.register(Alergenos)
class AlergenosAdmin(admin.ModelAdmin):
    list_display = ['id_alergeno', 'nombre', 'nivel_severidad', 'activo']
    list_filter = ['nivel_severidad', 'activo']
    search_fields = ['nombre']
    ordering = ['nombre']
