from django.contrib import admin
from .models import Clientes, Hijos, Grados

# Register your models here.
@admin.register(Clientes)
class ClientesAdmin(admin.ModelAdmin):
    list_display = ['nombres', 'apellidos', 'ruc_ci', 'email', 'telefono', 'activo']
    list_filter = ['activo']
    search_fields = ['nombres', 'apellidos', 'ruc_ci', 'email']
    ordering = ['apellidos', 'nombres']

@admin.register(Hijos)
class HijosAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apellido', 'grado', 'activo']
    list_filter = ['activo', 'grado']
    search_fields = ['nombre', 'apellido']
    ordering = ['apellido', 'nombre']

@admin.register(Grados)
class GradosAdmin(admin.ModelAdmin):
    list_display = ['nombre_grado', 'nivel', 'orden_visualizacion', 'activo']
    list_filter = ['activo', 'nivel']
    search_fields = ['nombre_grado']
    ordering = ['orden_visualizacion']
