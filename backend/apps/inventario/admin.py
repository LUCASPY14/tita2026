from django.contrib import admin
from django.utils.html import format_html
from .models import (
    StockUnico,
    MovimientosStock,
    AjustesInventario,
    DetallesAjuste,
    CostosHistoricos,
    AlertasStock,
    LotesProducto,
    AlertasVencimiento
)


@admin.register(StockUnico)
class StockUnicoAdmin(admin.ModelAdmin):
    list_display = [
        'id_stock', 
        'nombre_producto',
        'cantidad_actual', 
        'valor_inventario',
        'estado_stock',
        'fecha_ultima_actualizacion'
    ]
    list_filter = ['fecha_ultima_actualizacion']
    search_fields = ['id_producto__descripcion', 'id_producto__codigo_barras']
    ordering = ['id_producto']
    readonly_fields = ['fecha_ultima_actualizacion']
    
    def nombre_producto(self, obj):
        return obj.id_producto.descripcion
    nombre_producto.short_description = 'Producto'
    
    def cantidad_actual(self, obj):
        if obj.requiere_reposicion:
            return format_html(
                '<span style="color: red; font-weight: bold;">{}</span>',
                obj.cantidad
            )
        return obj.cantidad
    cantidad_actual.short_description = 'Stock Actual'
    
    def estado_stock(self, obj):
        if obj.requiere_reposicion:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">⚠️ BAJO</span>'
            )
        return format_html(
            '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ OK</span>'
        )
    estado_stock.short_description = 'Estado'
    
    def valor_inventario(self, obj):
        return f"₲ {obj.valor_inventario:,.0f}"
    valor_inventario.short_description = 'Valor Total'


@admin.register(MovimientosStock)
class MovimientosStockAdmin(admin.ModelAdmin):
    list_display = [
        'id_movimiento_stock',
        'nombre_producto',
        'tipo_movimiento_color',
        'cantidad',
        'stock_resultante',
        'motivo_breve',
        'fecha_hora'
    ]
    list_filter = ['tipo_movimiento', 'fecha_hora']
    search_fields = ['id_producto__descripcion', 'motivo']
    ordering = ['-fecha_hora']
    readonly_fields = ['fecha_hora']
    date_hierarchy = 'fecha_hora'
    
    def nombre_producto(self, obj):
        return obj.id_producto.descripcion
    nombre_producto.short_description = 'Producto'
    
    def tipo_movimiento_color(self, obj):
        if obj.tipo_movimiento == 'Ingreso':
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">↑ {}</span>',
                obj.tipo_movimiento
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">↓ {}</span>',
                obj.tipo_movimiento
            )
    tipo_movimiento_color.short_description = 'Tipo'
    
    def motivo_breve(self, obj):
        return obj.motivo[:50] + '...' if len(obj.motivo) > 50 else obj.motivo
    motivo_breve.short_description = 'Motivo'


@admin.register(AjustesInventario)
class AjustesInventarioAdmin(admin.ModelAdmin):
    list_display = [
        'id_ajuste',
        'tipo_ajuste_color',
        'estado_ajuste_color',
        'motivo_breve',
        'fecha_hora',
        'autorizado_por'
    ]
    list_filter = ['tipo_ajuste', 'estado', 'fecha_hora']
    search_fields = ['motivo', 'id_empleado__nombre']
    ordering = ['-fecha_hora']
    readonly_fields = ['fecha_hora']
    date_hierarchy = 'fecha_hora'
    actions = ['aprobar_ajustes', 'rechazar_ajustes']
    
    def tipo_ajuste_color(self, obj):
        colores = {
            'Merma': '#dc3545',
            'Sobrante': '#28a745',
            'Correccion': '#ffc107',
            'Vencimiento': '#6c757d',
            'Deterioro': '#fd7e14'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colores.get(obj.tipo_ajuste, '#6c757d'),
            obj.tipo_ajuste
        )
    tipo_ajuste_color.short_description = 'Tipo'
    
    def estado_ajuste_color(self, obj):
        colores = {
            'Pendiente': '#ffc107',
            'Aprobado': '#28a745',
            'Rechazado': '#dc3545',
            'Aplicado': '#007bff'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colores.get(obj.estado, '#6c757d'),
            obj.estado
        )
    estado_ajuste_color.short_description = 'Estado'
    
    def motivo_breve(self, obj):
        return obj.motivo[:40] + '...' if len(obj.motivo) > 40 else obj.motivo
    motivo_breve.short_description = 'Motivo'
    
    def autorizado_por(self, obj):
        return obj.id_empleado.nombre if obj.id_empleado else '-'
    autorizado_por.short_description = 'Autorizado Por'
    
    def aprobar_ajustes(self, request, queryset):
        updated = queryset.update(estado='Aprobado')
        self.message_user(request, f'{updated} ajustes aprobados exitosamente.')
    aprobar_ajustes.short_description = "✓ Aprobar ajustes seleccionados"
    
    def rechazar_ajustes(self, request, queryset):
        updated = queryset.update(estado='Rechazado')
        self.message_user(request, f'{updated} ajustes rechazados.')
    rechazar_ajustes.short_description = "✗ Rechazar ajustes seleccionados"


@admin.register(DetallesAjuste)
class DetallesAjusteAdmin(admin.ModelAdmin):
    list_display = [
        'id_detalle',
        'id_ajuste',
        'nombre_producto',
        'cantidad_ajustada'
    ]
    list_filter = ['id_ajuste__tipo_ajuste', 'id_ajuste__fecha_hora']
    search_fields = ['id_producto__descripcion']
    ordering = ['-id_ajuste']
    
    def nombre_producto(self, obj):
        return obj.id_producto.descripcion
    nombre_producto.short_description = 'Producto'


@admin.register(CostosHistoricos)
class CostosHistoricosAdmin(admin.ModelAdmin):
    list_display = [
        'id_costo_historico',
        'nombre_producto',
        'costo_unitario_format',
        'cantidad_comprada',
        'fecha_compra'
    ]
    list_filter = ['fecha_compra']
    search_fields = ['id_producto__descripcion']
    ordering = ['-fecha_compra']
    date_hierarchy = 'fecha_compra'
    
    def nombre_producto(self, obj):
        return obj.id_producto.descripcion
    nombre_producto.short_description = 'Producto'
    
    def costo_unitario_format(self, obj):
        return f"₲ {obj.costo_unitario:,.0f}"
    costo_unitario_format.short_description = 'Costo Unitario'


@admin.register(AlertasStock)
class AlertasStockAdmin(admin.ModelAdmin):
    list_display = [
        'id_alerta',
        'nombre_producto',
        'stock_actual',
        'stock_minimo',
        'tipo_alerta_color',
        'activa',
        'fecha_generada'
    ]
    list_filter = ['tipo_alerta', 'activa', 'fecha_generada']
    search_fields = ['id_producto__descripcion']
    ordering = ['-fecha_generada']
    readonly_fields = ['fecha_generada', 'fecha_resuelta']
    actions = ['marcar_como_resuelta']
    
    def nombre_producto(self, obj):
        return obj.id_producto.descripcion
    nombre_producto.short_description = 'Producto'
    
    def tipo_alerta_color(self, obj):
        colores = {
            'stock_critico': '#dc3545',
            'stock_cero': '#fd7e14',
            'stock_minimo': '#ffc107'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colores.get(obj.tipo_alerta, '#6c757d'),
            obj.get_tipo_alerta_display()
        )
    tipo_alerta_color.short_description = 'Tipo'
    
    def marcar_como_resuelta(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(activa=False, fecha_resuelta=timezone.now())
        self.message_user(request, f'{updated} alertas marcadas como resueltas.')
    marcar_como_resuelta.short_description = "✓ Marcar como resueltas"


@admin.register(LotesProducto)
class LotesProductoAdmin(admin.ModelAdmin):
    list_display = [
        'id_lote',
        'numero_lote',
        'nombre_producto',
        'cantidad_disponible',
        'fecha_vencimiento_color',
        'bloqueado',
        'fecha_creacion'
    ]
    list_filter = ['bloqueado', 'fecha_vencimiento', 'fecha_creacion']
    search_fields = ['numero_lote', 'id_producto__descripcion']
    ordering = ['fecha_vencimiento', '-fecha_creacion']
    readonly_fields = ['fecha_creacion']
    date_hierarchy = 'fecha_vencimiento'
    actions = ['marcar_como_bloqueado']
    
    def nombre_producto(self, obj):
        return obj.id_producto.descripcion
    nombre_producto.short_description = 'Producto'
    
    def fecha_vencimiento_color(self, obj):
        from django.utils import timezone
        
        if not obj.fecha_vencimiento:
            return '-'
        
        dias_restantes = obj.dias_hasta_vencimiento
        
        if dias_restantes < 0:
            color = '#dc3545'  # Rojo - vencido
            icono = '✗'
        elif dias_restantes <= 7:
            color = '#fd7e14'  # Naranja - vence pronto
            icono = '⚠️'
        elif dias_restantes <= 30:
            color = '#ffc107'  # Amarillo - atención
            icono = '⏰'
        else:
            color = '#28a745'  # Verde - OK
            icono = '✓'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{} {} ({} días)</span>',
            color,
            icono,
            obj.fecha_vencimiento.strftime('%d/%m/%Y'),
            dias_restantes
        )
    fecha_vencimiento_color.short_description = 'Vencimiento'
    
    def marcar_como_bloqueado(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(bloqueado=True, motivo_bloqueo='vencido', fecha_bloqueo=timezone.now())
        self.message_user(request, f'{updated} lotes marcados como bloqueados.')
    marcar_como_bloqueado.short_description = "Marcar como bloqueados"


@admin.register(AlertasVencimiento)
class AlertasVencimientoAdmin(admin.ModelAdmin):
    list_display = [
        'id_alerta',
        'nombre_lote',
        'fecha_vencimiento',
        'dias_restantes_color',
        'cantidad_lote',
        'accion_tomada',
        'fecha_generada'
    ]
    list_filter = ['tipo_alerta', 'accion_tomada', 'fecha_generada']
    search_fields = ['id_lote__numero_lote']
    ordering = ['fecha_vencimiento', '-fecha_generada']
    readonly_fields = ['fecha_generada', 'fecha_accion']
    date_hierarchy = 'fecha_vencimiento'
    actions = ['marcar_como_descartado']
    
    def nombre_lote(self, obj):
        return obj.id_lote.numero_lote
    nombre_lote.short_description = 'Lote'
    
    def dias_restantes_color(self, obj):
        dias = obj.dias_restantes
        
        if dias < 0:
            color = '#dc3545'
            texto = f'VENCIDO hace {abs(dias)} días'
        elif dias <= 3:
            color = '#dc3545'
            texto = f'{dias} días ⚠️ CRÍTICO'
        elif dias <= 7:
            color = '#fd7e14'
            texto = f'{dias} días ⚠️'
        elif dias <= 15:
            color = '#ffc107'
            texto = f'{dias} días'
        else:
            color = '#17a2b8'
            texto = f'{dias} días'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            texto
        )
    dias_restantes_color.short_description = 'Días Restantes'
    
    def marcar_como_descartado(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(accion_tomada='descartado', fecha_accion=timezone.now())
        self.message_user(request, f'{updated} alertas marcadas como descartadas.')
    marcar_como_descartado.short_description = "Marcar como descartados"

