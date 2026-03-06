from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from datetime import timedelta
from .models import (
    Tarjetas,
    TarjetasAutorizacion,
    CargasSaldo,
    ConsumosTarjeta,
    TransaccionesOnline,
    MediosPago,
    ConfiguracionSistema,
    CacheConfiguracion,
    LimitesTransaccion,
    RegistroAutorizaciones,
)


@admin.register(Tarjetas)
class TarjetasAdmin(admin.ModelAdmin):
    """Admin avanzado para Tarjetas de estudiantes"""

    list_display = [
        "nro_tarjeta_badge",
        "hijo_info",
        "saldo_display",
        "saldo_disponible_display",
        "estado_badge",
        "alerta_saldo",
        "fecha_vencimiento_display",
    ]

    list_filter = ["estado", "permite_saldo_negativo", "fecha_creacion"]
    search_fields = ["nro_tarjeta", "codigo_barras", "id_hijo__nombre", "id_hijo__apellido"]
    readonly_fields = ["fecha_creacion", "ultima_notificacion_saldo"]
    ordering = ["-fecha_creacion"]

    fieldsets = (
        (
            "Información de la Tarjeta",
            {"fields": ("nro_tarjeta", "codigo_barras", "id_hijo", "estado")},
        ),
        (
            "Saldo y Crédito",
            {
                "fields": (
                    "saldo_actual",
                    "saldo_alerta",
                    "permite_saldo_negativo",
                    "limite_credito",
                )
            },
        ),
        (
            "Notificaciones",
            {
                "fields": ("notificar_saldo_bajo", "ultima_notificacion_saldo"),
                "classes": ("collapse",),
            },
        ),
        ("Fechas", {"fields": ("fecha_vencimiento", "fecha_creacion"), "classes": ("collapse",)}),
    )

    def nro_tarjeta_badge(self, obj):
        """Número de tarjeta en badge"""
        return format_html(
            '<code style="background:#e9ecef;padding:2px 6px;border-radius:3px;">{}</code>',
            obj.nro_tarjeta,
        )

    nro_tarjeta_badge.short_description = "Nº Tarjeta"

    def hijo_info(self, obj):
        """Información del hijo asociado"""
        if obj.id_hijo:
            return format_html(
                '{} {} <small style="color:#6c757d;">(ID: {})</small>',
                obj.id_hijo.nombre,
                obj.id_hijo.apellido,
                obj.id_hijo.id_hijo,
            )
        return "-"

    hijo_info.short_description = "Estudiante"

    def saldo_display(self, obj):
        """Saldo actual formateado"""
        color = "#28a745" if obj.saldo_actual >= 0 else "#dc3545"
        return format_html('<strong style="color:{};">₲{:,.2f}</strong>', color, obj.saldo_actual)

    saldo_display.short_description = "Saldo Actual"

    def saldo_disponible_display(self, obj):
        """Saldo disponible considerando límite de crédito"""
        saldo_disp = obj.saldo_disponible
        return format_html("₲{:,.2f}", saldo_disp)

    saldo_disponible_display.short_description = "Saldo Disponible"

    def estado_badge(self, obj):
        """Estado con color"""
        colors = {
            "Activa": "#28a745",
            "Bloqueada": "#ffc107",
            "Vencida": "#6c757d",
            "Cancelada": "#dc3545",
            "Suspendida": "#fd7e14",
        }
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.estado.upper(),
        )

    estado_badge.short_description = "Estado"

    def alerta_saldo(self, obj):
        """Indicador de alerta de saldo"""
        if obj.esta_en_alerta:
            return format_html('<span style="color:#dc3545;">⚠️ Saldo bajo</span>')
        return format_html('<span style="color:#28a745;">✓ OK</span>')

    alerta_saldo.short_description = "Alerta"

    def fecha_vencimiento_display(self, obj):
        """Fecha de vencimiento formateada"""
        if obj.fecha_vencimiento:
            from datetime import date

            hoy = date.today()
            if obj.fecha_vencimiento < hoy:
                color = "#dc3545"
                estado = "(VENCIDA)"
            elif obj.fecha_vencimiento <= hoy + timedelta(days=30):
                color = "#ffc107"
                estado = "(Próxima)"
            else:
                color = "#28a745"
                estado = ""

            return format_html(
                '<span style="color:{};">{} {}</span>',
                color,
                obj.fecha_vencimiento.strftime("%d/%m/%Y"),
                estado,
            )
        return "-"

    fecha_vencimiento_display.short_description = "Vencimiento"


@admin.register(TarjetasAutorizacion)
class TarjetasAutorizacionAdmin(admin.ModelAdmin):
    """Admin para Tarjetas de Autorización de empleados"""

    list_display = [
        "codigo_barra_badge",
        "tipo_badge",
        "empleado_info",
        "permisos_badge",
        "estado_badge",
        "fecha_vencimiento_display",
    ]

    list_filter = ["tipo_autorizacion", "activo", "fecha_creacion"]
    search_fields = ["codigo_barra", "id_empleado__nombre", "id_empleado__apellido"]
    readonly_fields = ["fecha_creacion"]
    date_hierarchy = "fecha_creacion"

    fieldsets = (
        (
            "Información de la Tarjeta",
            {"fields": ("codigo_barra", "tipo_autorizacion", "id_empleado", "activo")},
        ),
        (
            "Permisos",
            {
                "fields": (
                    "puede_anular_almuerzos",
                    "puede_anular_ventas",
                    "puede_anular_recargas",
                    "puede_modificar_precios",
                )
            },
        ),
        (
            "Vigencia",
            {
                "fields": ("fecha_vencimiento", "fecha_creacion"),
            },
        ),
        ("Observaciones", {"fields": ("observaciones",), "classes": ("collapse",)}),
    )

    def codigo_barra_badge(self, obj):
        """Código de barras en badge"""
        return format_html(
            '<code style="background:#e9ecef;padding:2px 6px;border-radius:3px;">{}</code>',
            obj.codigo_barra,
        )

    codigo_barra_badge.short_description = "Código de Barras"

    def tipo_badge(self, obj):
        """Tipo de autorización con color"""
        colors = {
            "Supervisor": "#17a2b8",
            "Gerente": "#6610f2",
            "Director": "#e83e8c",
            "Temporal": "#ffc107",
        }
        color = colors.get(obj.tipo_autorizacion, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.tipo_autorizacion.upper(),
        )

    tipo_badge.short_description = "Tipo"

    def empleado_info(self, obj):
        """Información del empleado"""
        if obj.id_empleado:
            return format_html("{} {}", obj.id_empleado.nombre, obj.id_empleado.apellido)
        return "-"

    empleado_info.short_description = "Empleado"

    def permisos_badge(self, obj):
        """Permisos activos"""
        permisos = []
        if obj.puede_anular_almuerzos:
            permisos.append("Almuerzos")
        if obj.puede_anular_ventas:
            permisos.append("Ventas")
        if obj.puede_anular_recargas:
            permisos.append("Recargas")
        if obj.puede_modificar_precios:
            permisos.append("Precios")

        if permisos:
            return format_html("<small>{}</small>", ", ".join(permisos))
        return format_html('<small style="color:#6c757d;">Sin permisos</small>')

    permisos_badge.short_description = "Permisos"

    def estado_badge(self, obj):
        """Estado activo/inactivo"""
        if obj.activo:
            return format_html(
                '<span style="background:#28a745;color:white;padding:2px 8px;border-radius:3px;font-size:11px;">ACTIVA</span>'
            )
        return format_html(
            '<span style="background:#6c757d;color:white;padding:2px 8px;border-radius:3px;font-size:11px;">INACTIVA</span>'
        )

    estado_badge.short_description = "Estado"

    def fecha_vencimiento_display(self, obj):
        """Fecha de vencimiento formateada"""
        if obj.fecha_vencimiento:
            from datetime import date

            hoy = date.today()
            if obj.fecha_vencimiento < hoy:
                color = "#dc3545"
                estado = "(VENCIDA)"
            else:
                color = "#28a745"
                estado = ""

            return format_html(
                '<span style="color:{};">{} {}</span>',
                color,
                obj.fecha_vencimiento.strftime("%d/%m/%Y"),
                estado,
            )
        return format_html('<small style="color:#6c757d;">Sin vencimiento</small>')

    fecha_vencimiento_display.short_description = "Vencimiento"


@admin.register(CargasSaldo)
class CargasSaldoAdmin(admin.ModelAdmin):
    """Admin para Cargas de Saldo"""

    list_display = [
        "id_carga",
        "nro_tarjeta_link",
        "monto_display",
        "estado_badge",
        "fecha_carga_display",
        "referencia_badge",
        "cliente_info",
    ]

    list_filter = ["estado", "fecha_carga"]
    search_fields = ["id_carga", "referencia", "tx_id", "nro_tarjeta__nro_tarjeta"]
    readonly_fields = ["fecha_carga", "fecha_confirmacion"]
    date_hierarchy = "fecha_carga"
    ordering = ["-fecha_carga"]

    def nro_tarjeta_link(self, obj):
        """Link a la tarjeta"""
        if obj.nro_tarjeta:
            url = reverse("admin:core_tarjetas_change", args=[obj.nro_tarjeta.nro_tarjeta])
            return format_html('<a href="{}">{}</a>', url, obj.nro_tarjeta.nro_tarjeta)
        return "-"

    nro_tarjeta_link.short_description = "Tarjeta"

    def monto_display(self, obj):
        """Monto formateado"""
        return format_html('<strong style="color:#28a745;">₲{:,.2f}</strong>', obj.monto_cargado)

    monto_display.short_description = "Monto"

    def estado_badge(self, obj):
        """Estado con color"""
        colors = {
            "Pendiente": "#ffc107",
            "Confirmado": "#28a745",
            "Rechazado": "#dc3545",
            "Cancelado": "#6c757d",
            "Reembolsado": "#fd7e14",
        }
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.estado.upper(),
        )

    estado_badge.short_description = "Estado"

    def fecha_carga_display(self, obj):
        """Fecha de carga formateada"""
        return obj.fecha_carga.strftime("%d/%m/%Y %H:%M")

    fecha_carga_display.short_description = "Fecha Carga"

    def referencia_badge(self, obj):
        """Referencia en badge"""
        if obj.referencia:
            return format_html(
                '<code style="background:#e9ecef;padding:2px 6px;border-radius:3px;">{}</code>',
                obj.referencia[:20] + "..." if len(obj.referencia) > 20 else obj.referencia,
            )
        return "-"

    referencia_badge.short_description = "Referencia"

    def cliente_info(self, obj):
        """Información del cliente origen"""
        if obj.id_cliente_origen:
            return format_html(
                "{} {}", obj.id_cliente_origen.nombre, obj.id_cliente_origen.apellido
            )
        return format_html('<small style="color:#6c757d;">-</small>')

    cliente_info.short_description = "Cliente"


@admin.register(ConsumosTarjeta)
class ConsumosTarjetaAdmin(admin.ModelAdmin):
    """Admin para Consumos de Tarjeta"""

    list_display = [
        "id_consumo",
        "nro_tarjeta_link",
        "monto_display",
        "detalle_corto",
        "saldos_display",
        "fecha_consumo_display",
        "empleado_registro",
    ]

    list_filter = ["fecha_consumo"]
    search_fields = ["id_consumo", "nro_tarjeta__nro_tarjeta", "detalle"]
    readonly_fields = ["fecha_consumo", "saldo_anterior", "saldo_posterior"]
    date_hierarchy = "fecha_consumo"
    ordering = ["-fecha_consumo"]

    def nro_tarjeta_link(self, obj):
        """Link a la tarjeta"""
        if obj.nro_tarjeta:
            url = reverse("admin:core_tarjetas_change", args=[obj.nro_tarjeta.nro_tarjeta])
            return format_html('<a href="{}">{}</a>', url, obj.nro_tarjeta.nro_tarjeta)
        return "-"

    nro_tarjeta_link.short_description = "Tarjeta"

    def monto_display(self, obj):
        """Monto consumido formateado"""
        return format_html('<strong style="color:#dc3545;">-₲{:,.2f}</strong>', obj.monto_consumido)

    monto_display.short_description = "Monto"

    def detalle_corto(self, obj):
        """Detalle truncado"""
        if obj.detalle:
            if len(obj.detalle) > 40:
                return obj.detalle[:40] + "..."
            return obj.detalle
        return "-"

    detalle_corto.short_description = "Detalle"

    def saldos_display(self, obj):
        """Saldos anterior y posterior"""
        return format_html(
            "<small>₲{:,.2f} → ₲{:,.2f}</small>", obj.saldo_anterior, obj.saldo_posterior
        )

    saldos_display.short_description = "Saldos"

    def fecha_consumo_display(self, obj):
        """Fecha de consumo formateada"""
        return obj.fecha_consumo.strftime("%d/%m/%Y %H:%M")

    fecha_consumo_display.short_description = "Fecha"

    def empleado_registro(self, obj):
        """Empleado que registró"""
        if obj.id_empleado_registro:
            return format_html(
                "<small>{} {}</small>",
                obj.id_empleado_registro.nombre,
                obj.id_empleado_registro.apellido,
            )
        return format_html('<small style="color:#6c757d;">Sistema</small>')

    empleado_registro.short_description = "Registrado por"


@admin.register(TransaccionesOnline)
class TransaccionesOnlineAdmin(admin.ModelAdmin):
    """Admin para Transacciones Online"""

    list_display = [
        "id_transaccion",
        "monto_display",
        "metodo_pago_badge",
        "estado_badge",
        "fecha_transaccion_display",
        "referencia_badge",
    ]

    list_filter = ["metodo_pago", "estado", "fecha_transaccion"]
    search_fields = ["id_transaccion", "referencia_pago", "id_transaccion_externa"]
    readonly_fields = ["creado_en", "actualizado_en"]
    date_hierarchy = "fecha_transaccion"
    ordering = ["-fecha_transaccion"]

    def monto_display(self, obj):
        """Monto formateado"""
        return format_html('<strong style="color:#0d6efd;">₲{:,.2f}</strong>', obj.monto)

    monto_display.short_description = "Monto"

    def metodo_pago_badge(self, obj):
        """Método de pago con color"""
        colors = {
            "tarjeta_credito": "#6610f2",
            "tarjeta_debito": "#0d6efd",
            "transferencia": "#17a2b8",
            "qr": "#28a745",
            "billetera": "#fd7e14",
        }
        nombres = {
            "tarjeta_credito": "T. Crédito",
            "tarjeta_debito": "T. Débito",
            "transferencia": "Transferencia",
            "qr": "QR",
            "billetera": "Billetera",
        }
        color = colors.get(obj.metodo_pago, "#6c757d")
        nombre = nombres.get(obj.metodo_pago, obj.metodo_pago)
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            nombre.upper(),
        )

    metodo_pago_badge.short_description = "Método"

    def estado_badge(self, obj):
        """Estado con color"""
        colors = {
            "Pendiente": "#ffc107",
            "Confirmado": "#28a745",
            "Rechazado": "#dc3545",
            "Cancelado": "#6c757d",
        }
        color = colors.get(obj.estado, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:11px;">{}</span>',
            color,
            obj.estado.upper(),
        )

    estado_badge.short_description = "Estado"

    def fecha_transaccion_display(self, obj):
        """Fecha de transacción formateada"""
        return obj.fecha_transaccion.strftime("%d/%m/%Y %H:%M")

    fecha_transaccion_display.short_description = "Fecha"

    def referencia_badge(self, obj):
        """Referencia en badge"""
        if obj.referencia_pago:
            return format_html(
                '<code style="background:#e9ecef;padding:2px 6px;border-radius:3px;">{}</code>',
                (
                    obj.referencia_pago[:20] + "..."
                    if len(obj.referencia_pago) > 20
                    else obj.referencia_pago
                ),
            )
        return "-"

    referencia_badge.short_description = "Referencia"


@admin.register(MediosPago)
class MediosPagoAdmin(admin.ModelAdmin):
    """Admin para Medios de Pago"""

    list_display = [
        "id_medio_pago",
        "descripcion_badge",
        "genera_comision_badge",
        "requiere_validacion_badge",
        "estado_badge",
    ]

    list_filter = ["genera_comision", "requiere_validacion", "activo"]
    search_fields = ["descripcion"]
    ordering = ["descripcion"]

    def descripcion_badge(self, obj):
        """Descripción en badge"""
        return format_html("<strong>{}</strong>", obj.descripcion)

    descripcion_badge.short_description = "Descripción"

    def genera_comision_badge(self, obj):
        """Indicador de comisión"""
        if obj.genera_comision:
            return format_html('<span style="color:#fd7e14;">✓ Cobra comisión</span>')
        return format_html('<span style="color:#6c757d;">-</span>')

    genera_comision_badge.short_description = "Comisión"

    def requiere_validacion_badge(self, obj):
        """Indicador de validación"""
        if obj.requiere_validacion:
            return format_html('<span style="color:#0d6efd;">✓ Requiere validación</span>')
        return format_html('<span style="color:#6c757d;">-</span>')

    requiere_validacion_badge.short_description = "Validación"

    def estado_badge(self, obj):
        """Estado activo/inactivo"""
        if obj.activo:
            return format_html(
                '<span style="background:#28a745;color:white;padding:2px 8px;border-radius:3px;font-size:11px;">ACTIVO</span>'
            )
        return format_html(
            '<span style="background:#6c757d;color:white;padding:2px 8px;border-radius:3px;font-size:11px;">INACTIVO</span>'
        )

    estado_badge.short_description = "Estado"


@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    """Admin para Configuración del Sistema"""

    list_display = [
        "clave_badge",
        "valor_display",
        "tipo_badge",
        "categoria_badge",
        "requerido_badge",
        "updated_info",
    ]

    list_filter = ["tipo", "categoria", "requerido", "activo"]
    search_fields = ["clave", "descripcion"]
    readonly_fields = ["updated_at"]
    ordering = ["categoria", "clave"]

    fieldsets = (
        ("Identificación", {"fields": ("clave", "descripcion", "categoria")}),
        ("Valor", {"fields": ("valor", "valor_defecto", "tipo")}),
        (
            "Validación",
            {
                "fields": ("validacion", "valores_permitidos", "valor_min", "valor_max"),
                "classes": ("collapse",),
            },
        ),
        (
            "Configuración",
            {"fields": ("requerido", "requiere_reinicio", "solo_superuser", "activo")},
        ),
        ("Auditoría", {"fields": ("updated_at", "updated_by"), "classes": ("collapse",)}),
    )

    def clave_badge(self, obj):
        """Clave en badge"""
        return format_html(
            '<code style="background:#e9ecef;padding:2px 6px;border-radius:3px;font-family:monospace;">{}</code>',
            obj.clave,
        )

    clave_badge.short_description = "Clave"

    def valor_display(self, obj):
        """Valor truncado"""
        if len(obj.valor) > 50:
            return format_html('<span title="{}">{}</span>', obj.valor, obj.valor[:47] + "...")
        return obj.valor

    valor_display.short_description = "Valor"

    def tipo_badge(self, obj):
        """Tipo de configuración con color"""
        colors = {
            "string": "#6c757d",
            "int": "#0d6efd",
            "decimal": "#17a2b8",
            "bool": "#28a745",
            "json": "#6610f2",
            "email": "#e83e8c",
            "url": "#fd7e14",
            "date": "#ffc107",
        }
        color = colors.get(obj.tipo, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 6px;border-radius:3px;font-size:10px;">{}</span>',
            color,
            obj.tipo.upper(),
        )

    tipo_badge.short_description = "Tipo"

    def categoria_badge(self, obj):
        """Categoría en badge"""
        return format_html(
            '<span style="background:#e9ecef;padding:2px 6px;border-radius:3px;font-size:10px;">{}</span>',
            obj.categoria,
        )

    categoria_badge.short_description = "Categoría"

    def requerido_badge(self, obj):
        """Indicador de requerido"""
        if obj.requerido:
            return format_html('<span style="color:#dc3545;">✓ Obligatorio</span>')
        return format_html('<span style="color:#6c757d;">Opcional</span>')

    requerido_badge.short_description = "Requerido"

    def updated_info(self, obj):
        """Información de actualización"""
        if obj.updated_by:
            return format_html(
                "<small>{}<br/>{}</small>",
                obj.updated_at.strftime("%d/%m/%Y %H:%M"),
                f"{obj.updated_by.nombre} {obj.updated_by.apellido}",
            )
        return obj.updated_at.strftime("%d/%m/%Y %H:%M")

    updated_info.short_description = "Última actualización"


@admin.register(CacheConfiguracion)
class CacheConfiguracionAdmin(admin.ModelAdmin):
    """Admin para Configuración de Caché"""

    list_display = [
        "clave_badge",
        "tipo_cache_badge",
        "ttl_display",
        "size_display",
        "performance_display",
        "activo_badge",
    ]

    list_filter = ["tipo_cache", "auto_invalidate", "activo"]
    search_fields = ["clave", "descripcion"]
    readonly_fields = ["hits", "misses", "ultima_limpieza"]
    ordering = ["clave"]

    def clave_badge(self, obj):
        """Clave en badge"""
        return format_html(
            '<code style="background:#e9ecef;padding:2px 6px;border-radius:3px;">{}</code>',
            obj.clave,
        )

    clave_badge.short_description = "Clave"

    def tipo_cache_badge(self, obj):
        """Tipo de caché"""
        colors = {
            "memory": "#28a745",
            "redis": "#dc3545",
            "database": "#0d6efd",
        }
        color = colors.get(obj.tipo_cache, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 6px;border-radius:3px;font-size:10px;">{}</span>',
            color,
            obj.tipo_cache.upper(),
        )

    tipo_cache_badge.short_description = "Tipo"

    def ttl_display(self, obj):
        """TTL formateado"""
        if obj.ttl_segundos < 60:
            return format_html("{} seg", obj.ttl_segundos)
        elif obj.ttl_segundos < 3600:
            return format_html("{} min", obj.ttl_segundos // 60)
        else:
            return format_html("{} hrs", obj.ttl_segundos // 3600)

    ttl_display.short_description = "TTL"

    def size_display(self, obj):
        """Tamaño máximo formateado"""
        return format_html("{} MB", obj.max_size_mb)

    size_display.short_description = "Tamaño"

    def performance_display(self, obj):
        """Ratio de hits vs misses"""
        total = obj.hits + obj.misses
        if total > 0:
            hit_rate = (obj.hits / total) * 100
            color = "#28a745" if hit_rate >= 80 else "#ffc107" if hit_rate >= 60 else "#dc3545"
            return format_html(
                '<span style="color:{};">{:.1f}% ({}/{})</span>', color, hit_rate, obj.hits, total
            )
        return "-"

    performance_display.short_description = "Performance (Hits/Total)"

    def activo_badge(self, obj):
        """Estado activo"""
        if obj.activo:
            return format_html(
                '<span style="background:#28a745;color:white;padding:2px 8px;border-radius:3px;font-size:11px;">ACTIVO</span>'
            )
        return format_html(
            '<span style="background:#6c757d;color:white;padding:2px 8px;border-radius:3px;font-size:11px;">INACTIVO</span>'
        )

    activo_badge.short_description = "Estado"


@admin.register(LimitesTransaccion)
class LimitesTransaccionAdmin(admin.ModelAdmin):
    """Admin para Límites de Transacción"""

    list_display = [
        "rol_badge",
        "operacion_badge",
        "monto_limite_display",
        "doble_autorizacion_badge",
        "activo_badge",
    ]

    list_filter = ["id_rol", "tipo_operacion", "requiere_autorizacion_doble", "activo"]
    search_fields = ["id_rol__nombre_rol", "observaciones"]
    readonly_fields = ["fecha_creacion", "fecha_modificacion"]
    ordering = ["id_rol", "tipo_operacion"]

    fieldsets = (
        (
            "Configuración",
            {"fields": ("id_rol", "tipo_operacion", "monto_maximo_sin_autorizacion")},
        ),
        ("Autorización", {"fields": ("requiere_autorizacion_doble", "roles_autorizadores")}),
        ("Estado", {"fields": ("activo", "observaciones")}),
        (
            "Auditoría",
            {
                "fields": ("id_empleado_configurador", "fecha_creacion", "fecha_modificacion"),
                "classes": ("collapse",),
            },
        ),
    )

    filter_horizontal = ["roles_autorizadores"]

    def rol_badge(self, obj):
        """Rol en badge"""
        return format_html("<strong>{}</strong>", obj.id_rol.nombre_rol)

    rol_badge.short_description = "Rol"

    def operacion_badge(self, obj):
        """Tipo de operación con color"""
        colors = {
            "venta": "#28a745",
            "descuento": "#ffc107",
            "nota_credito_cliente": "#0d6efd",
            "nota_credito_proveedor": "#17a2b8",
            "ajuste_inventario": "#6610f2",
            "exceder_credito": "#dc3545",
            "anular_venta": "#fd7e14",
            "retiro_caja": "#e83e8c",
            "devolucion": "#6c757d",
        }
        color = colors.get(obj.tipo_operacion, "#6c757d")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:3px;font-size:10px;">{}</span>',
            color,
            obj.get_tipo_operacion_display().upper(),
        )

    operacion_badge.short_description = "Operación"

    def monto_limite_display(self, obj):
        """Monto límite formateado"""
        return format_html(
            '<strong style="color:#0d6efd;">₲{:,.2f}</strong>', obj.monto_maximo_sin_autorizacion
        )

    monto_limite_display.short_description = "Monto Límite"

    def doble_autorizacion_badge(self, obj):
        """Indicador de doble autorización"""
        if obj.requiere_autorizacion_doble:
            return format_html('<span style="color:#dc3545;">⚠️ Requiere doble autorización</span>')
        return format_html('<span style="color:#6c757d;">Autorización simple</span>')

    doble_autorizacion_badge.short_description = "Autorización"

    def activo_badge(self, obj):
        """Estado activo"""
        if obj.activo:
            return format_html(
                '<span style="background:#28a745;color:white;padding:2px 8px;border-radius:3px;font-size:11px;">ACTIVO</span>'
            )
        return format_html(
            '<span style="background:#6c757d;color:white;padding:2px 8px;border-radius:3px;font-size:11px;">INACTIVO</span>'
        )

    activo_badge.short_description = "Estado"


@admin.register(RegistroAutorizaciones)
class RegistroAutorizacionesAdmin(admin.ModelAdmin):
    """Admin para Registro de Autorizaciones"""

    list_display = [
        "id_autorizacion",
        "operacion_badge",
        "monto_display",
        "solicitante_info",
        "autorizador_info",
        "autorizador2_info",
        "fecha_autorizacion_display",
    ]

    list_filter = ["tipo_operacion", "fecha_autorizacion"]
    search_fields = [
        "id_empleado_solicitante__nombre",
        "id_empleado_solicitante__apellido",
        "id_empleado_autorizador__nombre",
        "id_empleado_autorizador__apellido",
        "motivo",
    ]
    readonly_fields = ["fecha_autorizacion", "ip_address"]
    date_hierarchy = "fecha_autorizacion"
    ordering = ["-fecha_autorizacion"]

    fieldsets = (
        ("Operación", {"fields": ("tipo_operacion", "monto", "motivo")}),
        (
            "Participantes",
            {
                "fields": (
                    "id_empleado_solicitante",
                    "id_empleado_autorizador",
                    "id_empleado_autorizador_2",
                )
            },
        ),
        (
            "Referencias",
            {"fields": ("id_venta", "id_compra", "id_ajuste"), "classes": ("collapse",)},
        ),
        ("Auditoría", {"fields": ("fecha_autorizacion", "ip_address"), "classes": ("collapse",)}),
    )

    def operacion_badge(self, obj):
        """Tipo de operación"""
        return format_html(
            '<span style="background:#17a2b8;color:white;padding:2px 8px;border-radius:3px;font-size:10px;">{}</span>',
            obj.tipo_operacion.upper().replace("_", " "),
        )

    operacion_badge.short_description = "Operación"

    def monto_display(self, obj):
        """Monto formateado"""
        return format_html('<strong style="color:#dc3545;">₲{:,.2f}</strong>', obj.monto)

    monto_display.short_description = "Monto"

    def solicitante_info(self, obj):
        """Empleado solicitante"""
        if obj.id_empleado_solicitante:
            return format_html(
                "{} {}", obj.id_empleado_solicitante.nombre, obj.id_empleado_solicitante.apellido
            )
        return "-"

    solicitante_info.short_description = "Solicitante"

    def autorizador_info(self, obj):
        """Primer autorizador"""
        if obj.id_empleado_autorizador:
            return format_html(
                '<span style="color:#28a745;">{} {}</span>',
                obj.id_empleado_autorizador.nombre,
                obj.id_empleado_autorizador.apellido,
            )
        return "-"

    autorizador_info.short_description = "Autorizador 1"

    def autorizador2_info(self, obj):
        """Segundo autorizador"""
        if obj.id_empleado_autorizador_2:
            return format_html(
                '<span style="color:#28a745;">{} {}</span>',
                obj.id_empleado_autorizador_2.nombre,
                obj.id_empleado_autorizador_2.apellido,
            )
        return format_html('<small style="color:#6c757d;">-</small>')

    autorizador2_info.short_description = "Autorizador 2"

    def fecha_autorizacion_display(self, obj):
        """Fecha de autorización formateada"""
        return obj.fecha_autorizacion.strftime("%d/%m/%Y %H:%M")

    fecha_autorizacion_display.short_description = "Fecha"
