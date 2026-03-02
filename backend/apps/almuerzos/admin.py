from django.contrib import admin
from django.utils.html import format_html
from .models import (
    PlanesAlmuerzo,
    TiposAlmuerzo,
    SuscripcionesAlmuerzo,
    RegistrosConsumoAlmuerzo,
    CuentasAlmuerzoMensual,
    PagosAlmuerzoMensual,
    PagosCuentasAlmuerzo,
    Alergenos,
    ProductosAlergenos
)


@admin.register(PlanesAlmuerzo)
class PlanesAlmuerzoAdmin(admin.ModelAdmin):
    list_display = ['id_plan_almuerzo', 'nombre_plan', 'precio_mensual_badge', 'dias_semana_incluidos', 'estado_badge', 'fecha_creacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['nombre_plan', 'descripcion']
    readonly_fields = ['id_plan_almuerzo', 'fecha_creacion']
    ordering = ['nombre_plan']
    
    fieldsets = (
        ('Información del Plan', {
            'fields': ('id_plan_almuerzo', 'nombre_plan', 'descripcion')
        }),
        ('Precios y Días', {
            'fields': ('precio_mensual', 'dias_semana_incluidos')
        }),
        ('Estado', {
            'fields': ('activo', 'fecha_creacion')
        }),
    )
    
    def precio_mensual_badge(self, obj):
        color = '#4CAF50' if obj.precio_mensual < 500000 else '#FF9800'
        return format_html(
            '<strong style="color: {};">₲{:,.0f}</strong>',
            color, obj.precio_mensual
        )
    precio_mensual_badge.short_description = 'Precio Mensual'
    
    def estado_badge(self, obj):
        if obj.activo:
            return format_html('<span style="background-color: #4CAF50; color: white; padding: 3px 8px; border-radius: 3px;">ACTIVO</span>')
        return format_html('<span style="background-color: #F44336; color: white; padding: 3px 8px; border-radius: 3px;">INACTIVO</span>')
    estado_badge.short_description = 'Estado'


@admin.register(TiposAlmuerzo)
class TiposAlmuerzoAdmin(admin.ModelAdmin):
    list_display = ['id_tipo_almuerzo', 'nombre', 'precio_unitario_badge', 'incluye_plato_principal', 'incluye_postre', 'incluye_bebida', 'estado_badge']
    list_filter = ['activo', 'incluye_plato_principal', 'incluye_postre', 'incluye_bebida']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['id_tipo_almuerzo', 'fecha_creacion']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información del Tipo', {
            'fields': ('id_tipo_almuerzo', 'nombre', 'descripcion', 'precio_unitario')
        }),
        ('Componentes Incluidos', {
            'fields': ('incluye_plato_principal', 'incluye_postre', 'incluye_bebida')
        }),
        ('Estado', {
            'fields': ('activo', 'fecha_creacion')
        }),
    )
    
    def precio_unitario_badge(self, obj):
        color = '#2196F3' if obj.precio_unitario < 50000 else '#FF9800'
        return format_html(
            '<strong style="color: {};">₲{:,.0f}</strong>',
            color, obj.precio_unitario
        )
    precio_unitario_badge.short_description = 'Precio'
    
    def estado_badge(self, obj):
        if obj.activo:
            return format_html('<span style="background-color: #4CAF50; color: white; padding: 3px 8px; border-radius: 3px;">ACTIVO</span>')
        return format_html('<span style="background-color: #F44336; color: white; padding: 3px 8px; border-radius: 3px;">INACTIVO</span>')
    estado_badge.short_description = 'Estado'


@admin.register(SuscripcionesAlmuerzo)
class SuscripcionesAlmuerzoAdmin(admin.ModelAdmin):
    list_display = ['id_suscripcion', 'id_hijo', 'id_plan_almuerzo', 'fecha_inicio', 'fecha_fin', 'estado_badge']
    list_filter = ['estado', 'fecha_inicio']
    search_fields = ['id_hijo__nombre', 'id_hijo__apellido', 'id_plan_almuerzo__nombre_plan']
    readonly_fields = ['id_suscripcion']
    ordering = ['-fecha_inicio']
    
    fieldsets = (
        ('Información de la Suscripción', {
            'fields': ('id_suscripcion', 'id_hijo', 'id_plan_almuerzo')
        }),
        ('Periodo', {
            'fields': ('fecha_inicio', 'fecha_fin', 'estado')
        }),
    )
    
    def estado_badge(self, obj):
        colores = {
            'Activa': '#4CAF50',
            'Pausada': '#FF9800',
            'Cancelada': '#F44336',
            'Finalizada': '#9E9E9E'
        }
        color = colores.get(obj.estado, '#607D8B')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.estado or 'N/A'
        )
    estado_badge.short_description = 'Estado'


@admin.register(RegistrosConsumoAlmuerzo)
class RegistrosConsumoAlmuerzoAdmin(admin.ModelAdmin):
    list_display = ['id_registro_consumo', 'fecha_consumo', 'hora_registro', 'id_hijo', 'costo_badge', 'estado_badge', 'marcado_en_cuenta']
    list_filter = ['estado', 'fecha_consumo', 'marcado_en_cuenta']
    search_fields = ['id_hijo__nombre', 'id_hijo__apellido']
    readonly_fields = ['id_registro_consumo']
    ordering = ['-fecha_consumo', '-hora_registro']
    
    fieldsets = (
        ('Información del Registro', {
            'fields': ('id_registro_consumo', 'id_hijo', 'id_suscripcion', 'id_tipo_almuerzo')
        }),
        ('Fecha y Hora', {
            'fields': ('fecha_consumo', 'hora_registro')
        }),
        ('Costo y Estado', {
            'fields': ('costo_almuerzo', 'estado', 'motivo_rechazo', 'marcado_en_cuenta')
        }),
        ('Empleado y Tarjeta', {
            'fields': ('id_empleado_registro', 'nro_tarjeta'),
            'classes': ('collapse',)
        }),
    )
    
    def costo_badge(self, obj):
        if not obj.costo_almuerzo:
            return format_html('<span style="color: #999;">N/A</span>')
        return format_html('<strong>₲{:,.0f}</strong>', obj.costo_almuerzo)
    costo_badge.short_description = 'Costo'
    
    def estado_badge(self, obj):
        colores = {
            'Registrado': '#2196F3',
            'Confirmado': '#4CAF50',
            'Rechazado': '#F44336',
            'Cancelado': '#FF9800'
        }
        color = colores.get(obj.estado, '#607D8B')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.estado
        )
    estado_badge.short_description = 'Estado'


@admin.register(CuentasAlmuerzoMensual)
class CuentasAlmuerzoMensualAdmin(admin.ModelAdmin):
    list_display = ['id_cuenta', 'id_hijo', 'periodo_display', 'cantidad_almuerzos', 'monto_total_badge', 'monto_pagado_badge', 'saldo_badge', 'estado_badge']
    list_filter = ['estado', 'anio', 'mes', 'forma_cobro']
    search_fields = ['id_hijo__nombre', 'id_hijo__apellido']
    readonly_fields = ['id_cuenta', 'fecha_generacion', 'fecha_actualizacion', 'saldo_pendiente_display']
    ordering = ['-anio', '-mes']
    
    fieldsets = (
        ('Información de la Cuenta', {
            'fields': ('id_cuenta', 'id_hijo')
        }),
        ('Periodo', {
            'fields': ('anio', 'mes', 'fecha_generacion')
        }),
        ('Montos', {
            'fields': ('cantidad_almuerzos', 'monto_total', 'forma_cobro', 'monto_pagado', 'saldo_pendiente_display')
        }),
        ('Estado', {
            'fields': ('estado', 'fecha_actualizacion', 'observaciones')
        }),
    )
    
    def periodo_display(self, obj):
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        return format_html('<strong>{} {}</strong>', meses[obj.mes] if obj.mes <= 12 else obj.mes, obj.anio)
    periodo_display.short_description = 'Periodo'
    
    def monto_total_badge(self, obj):
        return format_html('<strong>₲{:,.0f}</strong>', obj.monto_total)
    monto_total_badge.short_description = 'Total'
    
    def monto_pagado_badge(self, obj):
        color = '#4CAF50' if obj.monto_pagado >= obj.monto_total else '#FF9800'
        return format_html('<strong style="color: {};">₲{:,.0f}</strong>', color, obj.monto_pagado)
    monto_pagado_badge.short_description = 'Pagado'
    
    def saldo_badge(self, obj):
        saldo = obj.monto_total - obj.monto_pagado
        color = '#4CAF50' if saldo <= 0 else '#F44336'
        return format_html('<strong style="color: {};">₲{:,.0f}</strong>', color, saldo)
    saldo_badge.short_description = 'Saldo'
    
    def saldo_pendiente_display(self, obj):
        saldo = obj.monto_total - obj.monto_pagado
        return format_html('<strong>₲{:,.2f}</strong>', saldo)
    saldo_pendiente_display.short_description = 'Saldo Pendiente'
    
    def estado_badge(self, obj):
        colores = {
            'Pendiente': '#FF9800',
            'Pagada': '#4CAF50',
            'Vencida': '#F44336',
            'Cancelada': '#9E9E9E'
        }
        color = colores.get(obj.estado, '#607D8B')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.estado
        )
    estado_badge.short_description = 'Estado'


@admin.register(PagosAlmuerzoMensual)
class PagosAlmuerzoMensualAdmin(admin.ModelAdmin):
    list_display = ['id_pago_almuerzo', 'id_suscripcion', 'mes_pagado', 'monto_pagado_badge', 'fecha_pago', 'estado_badge']
    list_filter = ['estado', 'fecha_pago']
    search_fields = ['id_suscripcion__id_hijo__nombre', 'id_suscripcion__id_hijo__apellido']
    readonly_fields = ['id_pago_almuerzo', 'fecha_pago']
    ordering = ['-fecha_pago']
    
    fieldsets = (
        ('Información del Pago', {
            'fields': ('id_pago_almuerzo', 'id_suscripcion', 'id_venta')
        }),
        ('Detalles del Pago', {
            'fields': ('monto_pagado', 'mes_pagado', 'fecha_pago', 'estado')
        }),
    )
    
    def monto_pagado_badge(self, obj):
        return format_html('<strong style="color: #4CAF50;">₲{:,.0f}</strong>', obj.monto_pagado)
    monto_pagado_badge.short_description = 'Monto'
    
    def estado_badge(self, obj):
        if not obj.estado:
            return format_html('<span style="color: #999;">N/A</span>')
        colores = {
            'Pendiente': '#FF9800',
            'Confirmado': '#4CAF50',
            'Rechazado': '#F44336'
        }
        color = colores.get(obj.estado, '#607D8B')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.estado
        )
    estado_badge.short_description = 'Estado'


@admin.register(PagosCuentasAlmuerzo)
class PagosCuentasAlmuerzoAdmin(admin.ModelAdmin):
    list_display = ['id_pago', 'id_cuenta', 'fecha_pago', 'medio_pago', 'monto_badge', 'referencia', 'id_empleado_registro']
    list_filter = ['medio_pago', 'fecha_pago']
    search_fields = ['referencia', 'id_cuenta__id_hijo__nombre']
    readonly_fields = ['id_pago', 'fecha_pago']
    ordering = ['-fecha_pago']
    
    fieldsets = (
        ('Información del Pago', {
            'fields': ('id_pago', 'id_cuenta', 'fecha_pago')
        }),
        ('Detalles del Pago', {
            'fields': ('monto', 'medio_pago', 'referencia')
        }),
        ('Empleado y Observaciones', {
            'fields': ('id_empleado_registro', 'observaciones'),
            'classes': ('collapse',)
        }),
    )
    
    def monto_badge(self, obj):
        return format_html('<strong style="color: #4CAF50;">₲{:,.0f}</strong>', obj.monto)
    monto_badge.short_description = 'Monto'


@admin.register(Alergenos)
class AlergenosAdmin(admin.ModelAdmin):
    list_display = ['id_alergeno', 'nombre', 'icono', 'nivel_severidad_badge', 'estado_badge', 'fecha_creacion']
    list_filter = ['nivel_severidad', 'activo', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['id_alergeno', 'fecha_creacion']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información del Alérgeno', {
            'fields': ('id_alergeno', 'nombre', 'descripcion', 'icono')
        }),
        ('Clasificación', {
            'fields': ('nivel_severidad', 'palabras_clave')
        }),
        ('Registro', {
            'fields': ('activo', 'fecha_creacion', 'usuario_creacion'),
            'classes': ('collapse',)
        }),
    )
    
    def nivel_severidad_badge(self, obj):
        colores = {
            'Critica': '#F44336',
            'Alta': '#FF9800',
            'Media': '#FFC107',
            'Baja': '#4CAF50'
        }
        color = colores.get(obj.nivel_severidad, '#607D8B')
        icono = '🔴' if obj.nivel_severidad == 'Critica' else ('🟡' if obj.nivel_severidad in ['Alta', 'Media'] else '🟢')
        return format_html(
            '{} <span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            icono, color, obj.nivel_severidad
        )
    nivel_severidad_badge.short_description = 'Severidad'
    
    def estado_badge(self, obj):
        if obj.activo:
            return format_html('<span style="background-color: #4CAF50; color: white; padding: 3px 8px; border-radius: 3px;">ACTIVO</span>')
        return format_html('<span style="background-color: #F44336; color: white; padding: 3px 8px; border-radius: 3px;">INACTIVO</span>')
    estado_badge.short_description = 'Estado'


@admin.register(ProductosAlergenos)
class ProductosAlergenosAdmin(admin.ModelAdmin):
    list_display = ['id_producto_alergeno', 'id_producto', 'id_alergeno', 'contiene_badge', 'fecha_registro', 'usuario_registro']
    list_filter = ['contiene', 'fecha_registro']
    search_fields = ['id_producto__nombre', 'id_alergeno__nombre', 'observaciones']
    readonly_fields = ['id_producto_alergeno', 'fecha_registro']
    ordering = ['-fecha_registro']
    
    fieldsets = (
        ('Relación Producto-Alérgeno', {
            'fields': ('id_producto_alergeno', 'id_producto', 'id_alergeno')
        }),
        ('Detalles', {
            'fields': ('contiene', 'observaciones')
        }),
        ('Registro', {
            'fields': ('fecha_registro', 'usuario_registro'),
            'classes': ('collapse',)
        }),
    )
    
    def contiene_badge(self, obj):
        if obj.contiene:
            return format_html('<span style="background-color: #F44336; color: white; padding: 3px 8px; border-radius: 3px;">⚠️ CONTIENE</span>')
        return format_html('<span style="background-color: #FF9800; color: white; padding: 3px 8px; border-radius: 3px;">PUEDE CONTENER TRAZAS</span>')
    contiene_badge.short_description = 'Estado'
