from django.contrib import admin
from .models import Productos, Categorias, UnidadesMedida

# Register your models here.
@admin.register(Categorias)
class CategoriasAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre']
    ordering = ['nombre']

@admin.register(Productos)
class ProductosAdmin(admin.ModelAdmin):
    list_display = ['codigo_barra', 'descripcion', 'activo']
    list_filter = ['activo']
    search_fields = ['codigo_barra', 'descripcion']
    ordering = ['descripcion']

@admin.register(UnidadesMedida)
class UnidadesMedidaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'abreviatura', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'abreviatura']
    ordering = ['nombre']
