from django.contrib import admin
from django.utils.html import format_html
from .models import (
    NotificacionesPortal,
    NotificacionesSaldo,
    SolicitudesNotificacion,
    PreferenciasNotificacion,
    EmailsEnviados,
    SmsEnviados,
    PlantillasEmail,
    PlantillasSms,
    CampanasComunicacion,
    AlertasAutomaticas,
    AlertaDestinatarios,
    AlertasSistema,
    HistorialAlertas,
    AnomaliasDetectadas,
    RestriccionesHorarias
)


# =============================================================================
# NOTIFICACIONES PORTAL
# =============================================================================

@admin.register(NotificacionesPortal)
class NotificacionesPortalAdmin(admin.ModelAdmin):
    list_display = ['id_notificacion', 'tipo_badge', 'titulo', 'id_usuario_portal', 'leida_badge', 'fecha_envio']
    list_filter = ['tipo', 'leida', 'fecha_envio']
    search_fields = ['titulo', 'mensaje']
    ordering = ['-fecha_envio']
    readonly_fields = ['id_notificacion', 'fecha_envio', 'creado_en']
    
    fieldsets = (
        ('Información', {
            'fields': ('id_notificacion', 'tipo', 'id_usuario_portal')
        }),
        ('Contenido', {
            'fields': ('titulo', 'mensaje')
        }),
        ('Estado', {
            'fields': ('leida', 'fecha_envio', 'fecha_lectura', 'creado_en')
        }),
    )
    
    def tipo_badge(self, obj):
        colores = {
            'alerta': 'red',
            'recordatorio': 'orange',
            'venta': 'green',
            'compra': 'blue',
            'inventario': 'purple',
            'pago': 'green',
            'saldo': 'orange',
            'sistema': 'gray',
            'promocion': 'pink',
            'informativa': 'lightblue'
        }
        color = colores.get(obj.tipo.lower(), 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.tipo
        )
    tipo_badge.short_description = 'Tipo'
    
    def leida_badge(self, obj):
        if obj.leida == 1:
            return format_html('<span style="color: green;">✓ Leída</span>')
        return format_html('<span style="color: orange;">○ No Leída</span>')
    leida_badge.short_description = 'Estado Lectura'


# =============================================================================
# NOTIFICACIONES SALDO  
# =============================================================================

@admin.register(NotificacionesSaldo)
class NotificacionesSaldoAdmin(admin.ModelAdmin):
    list_display = ['id_notificacion', 'tipo_notificacion', 'saldo_actual_badge', 'nro_tarjeta', 'enviada_email', 'enviada_sms', 'leida_badge', 'fecha_envio']
    list_filter = ['tipo_notificacion', 'enviada_email', 'enviada_sms', 'leida', 'fecha_creacion']
    search_fields = ['mensaje', 'email_destinatario']
    ordering = ['-fecha_creacion']
    readonly_fields = ['id_notificacion', 'fecha_creacion']
    
    fieldsets = (
        ('Información', {
            'fields': ('id_notificacion', 'tipo_notificacion', 'nro_tarjeta')
        }),
        ('Saldo', {
            'fields': ('saldo_actual', 'mensaje')
        }),
        ('Estado de Envío', {
            'fields': ('enviada_email', 'email_destinatario', 'enviada_sms', 'leida', 'fecha_creacion', 'fecha_envio')
        }),
    )
    
    def saldo_actual_badge(self, obj):
        # Mostrar el saldo en color según el monto
        if obj.saldo_actual < 50000:
            color = 'red'
        elif obj.saldo_actual < 100000:
            color = 'orange'
        else:
            color = 'green'
        return format_html(
            '<span style="color: {}; font-weight: bold;">₲{:,.0f}</span>',
            color, obj.saldo_actual
        )
    saldo_actual_badge.short_description = 'Saldo Actual'
    
    def leida_badge(self, obj):
        if obj.leida == 1:
            return format_html('<span style="color: green;">✓ Leída</span>')
        return format_html('<span style="color: orange;">○ No Leída</span>')
    leida_badge.short_description = 'Estado'


# =============================================================================
# SOLICITUDES NOTIFICACIÓN
# =============================================================================

@admin.register(SolicitudesNotificacion)
class SolicitudesNotificacionAdmin(admin.ModelAdmin):
    list_display = ['id_solicitud', 'id_cliente', 'saldo_alerta_badge', 'destino', 'estado_badge', 'fecha_solicitud']
    list_filter = ['destino', 'estado', 'fecha_solicitud']
    search_fields = ['mensaje', 'id_cliente__nombre', 'id_cliente__apellido']
    ordering = ['-fecha_solicitud']
    readonly_fields = ['id_solicitud', 'fecha_solicitud']
    
    fieldsets = (
        ('Información', {
            'fields': ('id_solicitud', 'id_cliente', 'nro_tarjeta')
        }),
        ('Configuración Alerta', {
            'fields': ('saldo_alerta', 'mensaje', 'destino')
        }),
        ('Estado', {
            'fields': ('estado', 'fecha_solicitud', 'fecha_envio')
        }),
    )
    
    def saldo_alerta_badge(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: orange;">₲{:,.0f}</span>',
            obj.saldo_alerta
        )
    saldo_alerta_badge.short_description = 'Saldo de Alerta'
    
    def estado_badge(self, obj):
        colores = {
            'Pendiente': 'orange',
            'Enviada': 'green',
            'Cancelada': 'red'
        }
        color = colores.get(obj.estado, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.estado or 'Sin Estado'
        )
    estado_badge.short_description = 'Estado'


# =============================================================================
# PREFERENCIAS NOTIFICACIÓN
# =============================================================================

@admin.register(PreferenciasNotificacion)
class PreferenciasNotificacionAdmin(admin.ModelAdmin):
    list_display = ['id_preferencia', 'id_usuario_portal', 'tipo_notificacion', 'email_activo_badge', 'push_activo_badge', 'actualizado_en']
    list_filter = ['tipo_notificacion', 'email_activo', 'push_activo']
    search_fields = ['tipo_notificacion']
    ordering = ['id_usuario_portal', 'tipo_notificacion']
    readonly_fields = ['id_preferencia', 'creado_en', 'actualizado_en']
    
    fieldsets = (
        ('Información', {
            'fields': ('id_preferencia', 'id_usuario_portal', 'tipo_notificacion')
        }),
        ('Preferencias', {
            'fields': ('email_activo', 'push_activo')
        }),
        ('Fechas', {
            'fields': ('creado_en', 'actualizado_en')
        }),
    )
    
    def email_activo_badge(self, obj):
        if obj.email_activo == 1:
            return format_html('<span style="color: green;">✓ Activo</span>')
        return format_html('<span style="color: gray;">✗ Inactivo</span>')
    email_activo_badge.short_description = 'Email'
    
    def push_activo_badge(self, obj):
        if obj.push_activo == 1:
            return format_html('<span style="color: green;">✓ Activo</span>')
        return format_html('<span style="color: gray;">✗ Inactivo</span>')
    push_activo_badge.short_description = 'Push'


# =============================================================================
# EMAILS ENVIADOS
# =============================================================================

@admin.register(EmailsEnviados)
class EmailsEnviadosAdmin(admin.ModelAdmin):
    list_display = ['id_email', 'email_destinatario', 'nombre_destinatario', 'asunto', 'estado_badge', 'intentos_badge', 'fecha_envio']
    list_filter = ['estado', 'fecha_envio', 'id_template']
    search_fields = ['email_destinatario', 'nombre_destinatario', 'asunto']
    ordering = ['-fecha_envio']
    readonly_fields = ['id_email', 'fecha_envio']
    
    fieldsets = (
        ('Destinatario', {
            'fields': ('email_destinatario', 'nombre_destinatario', 'id_cliente')
        }),
        ('Contenido', {
            'fields': ('asunto', 'cuerpo', 'id_template')
        }),
        ('Estado', {
            'fields': ('estado', 'intentos', 'mensaje_error')
        }),
        ('Fechas', {
            'fields': ('fecha_envio', 'fecha_entrega', 'fecha_apertura')
        }),
        ('Registro', {
            'fields': ('enviado_por',)
        }),
    )
    
    def estado_badge(self, obj):
        colores = {
            'Pendiente': 'orange',
            'Enviado': 'blue',
            'Entregado': 'green',
            'Fallido': 'red',
            'Rebotado': 'darkred',
            'Abierto': 'lightgreen',
            'Marcado_Spam': 'gray'
        }
        color = colores.get(obj.estado, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.estado
        )
    estado_badge.short_description = 'Estado'
    
    def intentos_badge(self, obj):
        if obj.intentos > 3:
            color = 'red'
        elif obj.intentos > 1:
            color = 'orange'
        else:
            color = 'green'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.intentos
        )
    intentos_badge.short_description = 'Intentos'


# =============================================================================
# SMS ENVIADOS
# =============================================================================

@admin.register(SmsEnviados)
class SmsEnviadosAdmin(admin.ModelAdmin):
    list_display = ['id_sms', 'telefono', 'mensaje_preview', 'estado_badge', 'costo_badge', 'fecha_envio']
    list_filter = ['estado', 'fecha_envio', 'id_template']
    search_fields = ['telefono', 'mensaje']
    ordering = ['-fecha_envio']
    readonly_fields = ['id_sms', 'fecha_envio']
    
    fieldsets = (
        ('Destinatario', {
            'fields': ('telefono', 'id_cliente')
        }),
        ('Mensaje', {
            'fields': ('mensaje', 'id_template')
        }),
        ('Estado', {
            'fields': ('estado', 'costo')
        }),
        ('Fechas', {
            'fields': ('fecha_envio', 'fecha_entrega')
        }),
        ('Registro', {
            'fields': ('enviado_por',)
        }),
    )
    
    def mensaje_preview(self, obj):
        if len(obj.mensaje) > 50:
            return obj.mensaje[:50] + '...'
        return obj.mensaje
    mensaje_preview.short_description = 'Mensaje'
    
    def estado_badge(self, obj):
        colores = {
            'Pendiente': 'orange',
            'Enviado': 'blue',
            'Entregado': 'green',
            'Fallido': 'red',
            'Rechazado': 'darkred'
        }
        color = colores.get(obj.estado, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.estado
        )
    estado_badge.short_description = 'Estado'
    
    def costo_badge(self, obj):
        if obj.costo:
            return format_html(
                '<span style="color: green; font-weight: bold;">₲{:,.0f}</span>',
                obj.costo
            )
        return '-'
    costo_badge.short_description = 'Costo'


# =============================================================================
# PLANTILLAS EMAIL
# =============================================================================

@admin.register(PlantillasEmail)
class PlantillasEmailAdmin(admin.ModelAdmin):
    list_display = ['id_template', 'codigo', 'nombre', 'categoria', 'activo_badge', 'variables_count', 'updated_at']
    list_filter = ['categoria', 'activo', 'created_at']
    search_fields = ['codigo', 'nombre', 'asunto']
    ordering = ['categoria', 'nombre']
    readonly_fields = ['id_template', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información', {
            'fields': ('id_template', 'codigo', 'nombre', 'descripcion', 'categoria')
        }),
        ('Contenido', {
            'fields': ('asunto', 'cuerpo_html', 'cuerpo_texto', 'variables')
        }),
        ('Estado', {
            'fields': ('activo', 'created_at', 'updated_at', 'created_by')
        }),
    )
    
    def activo_badge(self, obj):
        if obj.activo:
            return format_html('<span style="color: green;">✓ Activo</span>')
        return format_html('<span style="color: red;">✗ Inactivo</span>')
    activo_badge.short_description = 'Estado'
    
    def variables_count(self, obj):
        count = len(obj.variables) if obj.variables else 0
        return format_html('<span style="font-weight: bold;">{} variables</span>', count)
    variables_count.short_description = 'Variables'


# =============================================================================
# PLANTILLAS SMS
# =============================================================================

@admin.register(PlantillasSms)
class PlantillasSmsAdmin(admin.ModelAdmin):
    list_display = ['id_template', 'codigo', 'nombre', 'mensaje_preview', 'categoria', 'activo_badge', 'variables_count']
    list_filter = ['categoria', 'activo', 'created_at']
    search_fields = ['codigo', 'nombre', 'mensaje']
    ordering = ['categoria', 'nombre']
    readonly_fields = ['id_template', 'created_at']
    
    fieldsets = (
        ('Información', {
            'fields': ('id_template', 'codigo', 'nombre', 'categoria')
        }),
        ('Mensaje', {
            'fields': ('mensaje', 'variables')
        }),
        ('Estado', {
            'fields': ('activo', 'created_at')
        }),
    )
    
    def mensaje_preview(self, obj):
        if len(obj.mensaje) > 50:
            return obj.mensaje[:50] + '...'
        return obj.mensaje
    mensaje_preview.short_description = 'Mensaje'
    
    def activo_badge(self, obj):
        if obj.activo:
            return format_html('<span style="color: green;">✓ Activo</span>')
        return format_html('<span style="color: red;">✗ Inactivo</span>')
    activo_badge.short_description = 'Estado'
    
    def variables_count(self, obj):
        count = len(obj.variables) if obj.variables else 0
        return format_html('<span style="font-weight: bold;">{} variables</span>', count)
    variables_count.short_description = 'Variables'


# =============================================================================
# CAMPAÑAS COMUNICACIÓN
# =============================================================================

@admin.register(CampanasComunicacion)
class CampanasComunicacionAdmin(admin.ModelAdmin):
    list_display = ['id_campana', 'nombre', 'tipo_badge', 'estado_badge', 'total_destinatarios', 'tasa_entrega', 'created_at']
    list_filter = ['tipo', 'estado', 'created_at', 'fecha_programada']
    search_fields = ['nombre', 'descripcion']
    ordering = ['-created_at']
    readonly_fields = ['id_campana', 'created_at']
    
    fieldsets = (
        ('Información', {
            'fields': ('id_campana', 'nombre', 'descripcion', 'tipo')
        }),
        ('Segmentación', {
            'fields': ('segmentacion',)
        }),
        ('Plantillas', {
            'fields': ('id_email_template', 'id_sms_template')
        }),
        ('Programación', {
            'fields': ('fecha_programada', 'fecha_enviada', 'estado')
        }),
        ('Estadísticas', {
            'fields': ('total_destinatarios', 'total_enviados', 'total_entregados')
        }),
        ('Registro', {
            'fields': ('created_at', 'created_by')
        }),
    )
    
    def tipo_badge(self, obj):
        colores = {
            'Email': 'blue',
            'SMS': 'green',
            'Mixta': 'purple',
            'Push': 'orange'
        }
        color = colores.get(obj.tipo, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.tipo
        )
    tipo_badge.short_description = 'Tipo'
    
    def estado_badge(self, obj):
        colores = {
            'Borrador': 'gray',
            'Programada': 'blue',
            'Enviando': 'orange',
            'Enviada': 'green',
            'Cancelada': 'red',
            'Fallida': 'darkred'
        }
        color = colores.get(obj.estado, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.estado
        )
    estado_badge.short_description = 'Estado'
    
    def tasa_entrega(self, obj):
        if obj.total_enviados > 0:
            tasa = (obj.total_entregados / obj.total_enviados) * 100
            color = 'green' if tasa >= 90 else ('orange' if tasa >= 70 else 'red')
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color, tasa
            )
        return '-'
    tasa_entrega.short_description = 'Tasa Entrega'


# =============================================================================
# ALERTAS AUTOMÁTICAS
# =============================================================================

@admin.register(AlertasAutomaticas)
class AlertasAutomaticasAdmin(admin.ModelAdmin):
    list_display = ['id_alerta', 'nombre', 'tipo_alerta_badge', 'criticidad_badge', 'frecuencia_min', 'activo_badge', 'ultima_verificacion']
    list_filter = ['tipo_alerta', 'criticidad', 'activo']
    search_fields = ['nombre', 'descripcion']
    ordering = ['criticidad', 'nombre']
    readonly_fields = ['id_alerta', 'ultima_verificacion']
    
    fieldsets = (
        ('Información', {
            'fields': ('id_alerta', 'nombre', 'descripcion')
        }),
        ('Configuración', {
            'fields': ('tipo_alerta', 'criticidad', 'condicion', 'frecuencia_min')
        }),
        ('Estado', {
            'fields': ('activo', 'ultima_verificacion')
        }),
    )
    
    def tipo_alerta_badge(self, obj):
        colores = {
            'Inventario': 'purple',
            'Ventas': 'green',
            'Compras': 'blue',
            'Saldo': 'orange',
            'Sistema': 'red',
            'Seguridad': 'darkred'
        }
        color = colores.get(obj.tipo_alerta, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.tipo_alerta
        )
    tipo_alerta_badge.short_description = 'Tipo'
    
    def criticidad_badge(self, obj):
        iconos_colores = {
            'Baja': ('🟢', 'green'),
            'Media': ('🟡', 'orange'),
            'Alta': ('🟠', 'darkorange'),
            'Crítica': ('🔴', 'red')
        }
        icono, color = iconos_colores.get(obj.criticidad, ('○', 'gray'))
        return format_html(
            '{} <span style="color: {}; font-weight: bold;">{}</span>',
            icono, color, obj.criticidad
        )
    criticidad_badge.short_description = 'Criticidad'
    
    def activo_badge(self, obj):
        if obj.activo:
            return format_html('<span style="color: green;">✓ Activo</span>')
        return format_html('<span style="color: red;">✗ Inactivo</span>')
    activo_badge.short_description = 'Estado'


# =============================================================================
# ALERTA DESTINATARIOS
# =============================================================================

@admin.register(AlertaDestinatarios)
class AlertaDestinatariosAdmin(admin.ModelAdmin):
    list_display = ['id_destinatario', 'id_alerta', 'id_empleado', 'via_email_badge', 'via_sistema_badge', 'activo_badge']
    list_filter = ['via_email', 'via_sistema', 'activo', 'id_alerta']
    search_fields = ['id_empleado__nombre', 'id_empleado__apellido']
    ordering = ['id_alerta', 'id_empleado']
    readonly_fields = ['id_destinatario']
    
    fieldsets = (
        ('Información', {
            'fields': ('id_destinatario', 'id_alerta', 'id_empleado')
        }),
        ('Canales de Notificación', {
            'fields': ('via_email', 'via_sistema')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )
    
    def via_email_badge(self, obj):
        if obj.via_email == 1:
            return format_html('<span style="color: green;">✓ Email</span>')
        return format_html('<span style="color: gray;">✗ Email</span>')
    via_email_badge.short_description = 'Email'
    
    def via_sistema_badge(self, obj):
        if obj.via_sistema == 1:
            return format_html('<span style="color: green;">✓ Sistema</span>')
        return format_html('<span style="color: gray;">✗ Sistema</span>')
    via_sistema_badge.short_description = 'Sistema'
    
    def activo_badge(self, obj):
        if obj.activo:
            return format_html('<span style="color: green;">✓ Activo</span>')
        return format_html('<span style="color: red;">✗ Inactivo</span>')
    activo_badge.short_description = 'Estado'


# =============================================================================
# ALERTAS SISTEMA
# =============================================================================

@admin.register(AlertasSistema)
class AlertasSistemaAdmin(admin.ModelAdmin):
    list_display = ['id_alerta', 'tipo_badge', 'mensaje_preview', 'estado_badge', 'fecha_creacion', 'fecha_resolucion']
    list_filter = ['tipo', 'estado', 'fecha_creacion']
    search_fields = ['mensaje', 'observaciones']
    ordering = ['-fecha_creacion']
    readonly_fields = ['id_alerta', 'fecha_creacion']
    
    fieldsets = (
        ('Información', {
            'fields': ('id_alerta', 'tipo', 'mensaje')
        }),
        ('Estado', {
            'fields': ('estado', 'fecha_creacion', 'fecha_leida')
        }),
        ('Resolución', {
            'fields': ('id_empleado_resuelve', 'fecha_resolucion', 'observaciones')
        }),
    )
    
    def mensaje_preview(self, obj):
        if len(obj.mensaje) > 60:
            return obj.mensaje[:60] + '...'
        return obj.mensaje
    mensaje_preview.short_description = 'Mensaje'
    
    def tipo_badge(self,obj):
        colores = {
            'error': 'red',
            'warning': 'orange',
            'info': 'blue',
            'success': 'green',
            'critical': 'darkred'
        }
        color = colores.get(obj.tipo.lower(), 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; text-transform: uppercase;">{}</span>',
            color, obj.tipo
        )
    tipo_badge.short_description = 'Tipo'
    
    def estado_badge(self, obj):
        colores = {
            'Pendiente': 'orange',
            'Resuelta': 'green',
            'Ignorada': 'gray'
        }
        color = colores.get(obj.estado, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.estado or 'Sin Estado'
        )
    estado_badge.short_description = 'Estado'


# =============================================================================
# HISTORIAL ALERTAS
# =============================================================================

@admin.register(HistorialAlertas)
class HistorialAlertasAdmin(admin.ModelAdmin):
    list_display = ['id_historial', 'id_alerta', 'fecha_disparada', 'resuelto_badge', 'resuelto_por', 'fecha_resolucion']
    list_filter = ['resuelto', 'fecha_disparada', 'id_alerta']
    search_fields = ['mensaje']
    ordering = ['-fecha_disparada']
    readonly_fields = ['id_historial', 'fecha_disparada']
    
    fieldsets = (
        ('Información', {
            'fields': ('id_historial', 'id_alerta', 'fecha_disparada')
        }),
        ('Mensaje', {
            'fields': ('mensaje', 'datos_contexto')
        }),
        ('Resolución', {
            'fields': ('resuelto', 'resuelto_por', 'fecha_resolucion')
        }),
    )
    
    def resuelto_badge(self, obj):
        if obj.resuelto == 1:
            return format_html('<span style="color: green;">✓ Resuelto</span>')
        return format_html('<span style="color: orange;">○ Pendiente</span>')
    resuelto_badge.short_description = 'Estado'


# =============================================================================
# ANOMALÍAS DETECTADAS
# =============================================================================

@admin.register(AnomaliasDetectadas)
class AnomaliasDetectadasAdmin(admin.ModelAdmin):
    list_display = ['id_anomalia', 'usuario', 'tipo_anomalia_badge', 'nivel_riesgo_badge', 'ip_address', 'notificado_badge', 'fecha_deteccion']
    list_filter = ['tipo_anomalia', 'nivel_riesgo', 'notificado', 'fecha_deteccion']
    search_fields = ['usuario', 'ip_address', 'descripcion']
    ordering = ['-fecha_deteccion']
    readonly_fields = ['id_anomalia', 'fecha_deteccion']
    
    fieldsets = (
        ('Información', {
            'fields': ('id_anomalia', 'usuario', 'fecha_deteccion')
        }),
        ('Anomalía', {
            'fields': ('tipo_anomalia', 'nivel_riesgo', 'descripcion', 'ip_address')
        }),
        ('Estado', {
            'fields': ('notificado',)
        }),
    )
    
    def tipo_anomalia_badge(self, obj):
        colores = {
            'acceso_inusual': 'orange',
            'intentos_fallidos': 'red',
            'cambio_horario': 'blue',
            'ip_sospechosa': 'darkred',
            'múltiples_sesiones': 'purple',
            'actividad_alta': 'pink'
        }
        color = colores.get(obj.tipo_anomalia.lower(), 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.tipo_anomalia
        )
    tipo_anomalia_badge.short_description = 'Tipo'
    
    def nivel_riesgo_badge(self, obj):
        iconos_colores = {
            'Bajo': ('🟢', 'green'),
            'Medio': ('🟡', 'orange'),
            'Alto': ('🟠', 'darkorange'),
            'Crítico': ('🔴', 'red')
        }
        icono, color = iconos_colores.get(obj.nivel_riesgo, ('○', 'gray'))
        return format_html(
            '{} <span style="color: {}; font-weight: bold;">{}</span>',
            icono, color, obj.nivel_riesgo
        )
    nivel_riesgo_badge.short_description = 'Nivel de Riesgo'
    
    def notificado_badge(self, obj):
        if obj.notificado == 1:
            return format_html('<span style="color: green;">✓ Notificado</span>')
        return format_html('<span style="color: orange;">○ Sin Notificar</span>')
    notificado_badge.short_description = 'Notificado'


# =============================================================================
# RESTRICCIONES HORARIAS
# =============================================================================

@admin.register(RestriccionesHorarias)
class RestriccionesHorariasAdmin(admin.ModelAdmin):
    list_display = ['id_restriccion', 'usuario', 'tipo_usuario', 'dia_semana', 'rango_horario', 'activo_badge', 'fecha_creacion']
    list_filter = ['tipo_usuario', 'dia_semana', 'activo', 'fecha_creacion']
    search_fields = ['usuario']
    ordering = ['tipo_usuario', 'dia_semana', 'hora_inicio']
    readonly_fields = ['id_restriccion', 'fecha_creacion']
    
    fieldsets = (
        ('Información', {
            'fields': ('id_restriccion', 'usuario', 'tipo_usuario')
        }),
        ('Restricción', {
            'fields': ('dia_semana', 'hora_inicio', 'hora_fin')
        }),
        ('Estado', {
            'fields': ('activo', 'fecha_creacion')
        }),
    )
    
    def rango_horario(self, obj):
        return format_html(
            '<span style="font-weight: bold;">{} - {}</span>',
            obj.hora_inicio.strftime('%H:%M'),
            obj.hora_fin.strftime('%H:%M')
        )
    rango_horario.short_description = 'Horario Permitido'
    
    def activo_badge(self, obj):
        if obj.activo:
            return format_html('<span style="color: green;">✓ Activo</span>')
        return format_html('<span style="color: red;">✗ Inactivo</span>')
    activo_badge.short_description = 'Estado'

