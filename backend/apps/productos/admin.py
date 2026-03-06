"""
Administración del módulo de Productos
Configuración avanzada del panel de administración para gestión de productos, categorías, precios y unidades
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum, Avg
from django.urls import reverse
from django.utils.safestring import mark_safe
from decimal import Decimal

from .models import (
    Productos,
    Categorias,
    UnidadesMedida,
    ListasPrecios,
    PreciosPorLista,
    HistoricoPrecios,
)

# ==================== ADMIN DE CATEGORÍAS ====================


@admin.register(Categorias)
class CategoriasAdmin(admin.ModelAdmin):
    """
    Administración de Categorías con jerarquía visual
    """

    list_display = [
        "nombre_con_jerarquia",
        "id_categoria",
        "categoria_padre_link",
        "total_productos",
        "estado_badge",
        "nivel_jerarquia",
    ]
    list_filter = ["activo", "id_categoria_padre"]
    search_fields = ["nombre"]
    ordering = ["nombre"]
    list_per_page = 50

    fieldsets = (
        ("Información Básica", {"fields": ("nombre", "activo")}),
        (
            "Jerarquía",
            {
                "fields": ("id_categoria_padre",),
                "description": "Seleccione una categoría padre para crear una subcategoría",
            },
        ),
    )

    def nombre_con_jerarquia(self, obj):
        """Muestra el nombre con indentación según nivel jerárquico"""
        nivel = 0
        actual = obj
        while actual.id_categoria_padre:
            nivel += 1
            actual = actual.id_categoria_padre

        indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * nivel
        icono = "📁" if obj.subcategorias.exists() else "📄"
        return format_html("{}{}  {}", mark_safe(indent), icono, obj.nombre)

    nombre_con_jerarquia.short_description = "Categoría"

    def categoria_padre_link(self, obj):
        """Link a la categoría padre"""
        if obj.id_categoria_padre:
            url = reverse(
                "admin:productos_categorias_change", args=[obj.id_categoria_padre.id_categoria]
            )
            return format_html('<a href="{}">{}</a>', url, obj.id_categoria_padre.nombre)
        return "-"

    categoria_padre_link.short_description = "Padre"

    def total_productos(self, obj):
        """Total de productos en esta categoría"""
        total = obj.productos.count()
        activos = obj.productos.filter(activo=True).count()

        if total > 0:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">{}</span> / {} productos',
                activos,
                total,
            )
        return "0 productos"

    total_productos.short_description = "Productos"

    def estado_badge(self, obj):
        """Badge coloreado de estado"""
        if obj.activo:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">ACTIVO</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">INACTIVO</span>'
        )

    estado_badge.short_description = "Estado"

    def nivel_jerarquia(self, obj):
        """Muestra el nivel jerárquico (0=raíz, 1=hija, etc.)"""
        nivel = 0
        actual = obj
        while actual.id_categoria_padre:
            nivel += 1
            actual = actual.id_categoria_padre

        labels = ["Raíz", "Nivel 1", "Nivel 2", "Nivel 3", "Nivel 4"]
        label = labels[nivel] if nivel < len(labels) else f"Nivel {nivel}"

        colores = ["#007bff", "#17a2b8", "#ffc107", "#fd7e14", "#dc3545"]
        color = colores[min(nivel, len(colores) - 1)]

        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            label,
        )

    nivel_jerarquia.short_description = "Nivel"

    actions = ["activar_categorias", "desactivar_categorias"]

    def activar_categorias(self, request, queryset):
        """Acción para activar categorías"""
        updated = queryset.update(activo=True)
        self.message_user(request, f"{updated} categoría(s) activada(s) exitosamente.")

    activar_categorias.short_description = "Activar categorías seleccionadas"

    def desactivar_categorias(self, request, queryset):
        """Acción para desactivar categorías (solo si no tienen productos activos)"""
        count = 0
        for categoria in queryset:
            productos_activos = categoria.productos.filter(activo=True).count()
            if productos_activos == 0:
                categoria.activo = False
                categoria.save()
                count += 1

        if count > 0:
            self.message_user(request, f"{count} categoría(s) desactivada(s) exitosamente.")
        else:
            self.message_user(
                request,
                "No se desactivaron categorías (tienen productos activos).",
                level="warning",
            )

    desactivar_categorias.short_description = "Desactivar categorías seleccionadas"


# ==================== ADMIN DE UNIDADES DE MEDIDA ====================


@admin.register(UnidadesMedida)
class UnidadesMedidaAdmin(admin.ModelAdmin):
    """
    Administración de Unidades de Medida
    """

    list_display = ["nombre", "abreviatura_badge", "total_productos", "estado_badge"]
    list_filter = ["activo"]
    search_fields = ["nombre", "abreviatura"]
    ordering = ["nombre"]
    list_per_page = 50

    fieldsets = (("Información Básica", {"fields": ("nombre", "abreviatura", "activo")}),)

    def abreviatura_badge(self, obj):
        """Abreviatura en badge"""
        return format_html(
            '<code style="background-color: #f8f9fa; padding: 2px 6px; border-radius: 3px; font-weight: bold;">{}</code>',
            obj.abreviatura,
        )

    abreviatura_badge.short_description = "Abreviatura"

    def total_productos(self, obj):
        """Total de productos con esta unidad"""
        total = obj.productos.count()
        activos = obj.productos.filter(activo=True).count()

        if total > 0:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">{}</span> / {} productos',
                activos,
                total,
            )
        return "0 productos"

    total_productos.short_description = "Productos"

    def estado_badge(self, obj):
        """Badge de estado"""
        if obj.activo:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">ACTIVO</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">INACTIVO</span>'
        )

    estado_badge.short_description = "Estado"


# ==================== ADMIN DE PRODUCTOS ====================


@admin.register(Productos)
class ProductosAdmin(admin.ModelAdmin):
    """
    Administración de Productos con información completa
    """

    list_display = [
        "codigo_barra_badge",
        "descripcion_corta",
        "categoria_tag",
        "impuesto_info",
        "stock_minimo_display",
        "permite_stock_neg",
        "estado_badge",
    ]
    list_filter = ["activo", "permite_stock_negativo", "id_categoria", "id_impuesto"]
    search_fields = ["codigo_barra", "descripcion"]
    ordering = ["descripcion"]
    list_per_page = 50
    autocomplete_fields = ["id_categoria", "id_impuesto", "id_unidad_medida"]

    fieldsets = (
        ("Información Básica", {"fields": ("codigo_barra", "descripcion", "activo")}),
        (
            "Clasificación",
            {
                "fields": ("id_categoria", "id_unidad_medida", "id_impuesto"),
                "description": "Categoría, unidad de medida e impuesto del producto",
            },
        ),
        (
            "Configuración de Stock",
            {
                "fields": ("stock_minimo", "permite_stock_negativo"),
                "description": "Configuración de alertas y control de stock",
            },
        ),
    )

    def codigo_barra_badge(self, obj):
        """Código de barras en badge"""
        if obj.codigo_barra:
            return format_html(
                '<code style="background-color: #e9ecef; padding: 3px 8px; border-radius: 3px; font-family: monospace; font-size: 12px;">{}</code>',
                obj.codigo_barra,
            )
        return format_html('<span style="color: #6c757d; font-style: italic;">Sin código</span>')

    codigo_barra_badge.short_description = "Código"

    def descripcion_corta(self, obj):
        """Descripción limitada a 50 caracteres"""
        if len(obj.descripcion) > 50:
            return f"{obj.descripcion[:47]}..."
        return obj.descripcion

    descripcion_corta.short_description = "Descripción"

    def categoria_tag(self, obj):
        """Categoría en tag coloreado"""
        if obj.id_categoria:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
                obj.id_categoria.nombre,
            )
        return "-"

    categoria_tag.short_description = "Categoría"

    def impuesto_info(self, obj):
        """Información del impuesto"""
        if obj.id_impuesto:
            return format_html(
                '<span style="font-weight: bold;">{}%</span>', obj.id_impuesto.porcentaje
            )
        return "-"

    impuesto_info.short_description = "IVA"

    def stock_minimo_display(self, obj):
        """Stock mínimo formateado"""
        return format_html(
            '<span style="color: #007bff; font-weight: bold;">{}</span> {}',
            obj.stock_minimo,
            obj.id_unidad_medida.abreviatura if obj.id_unidad_medida else "UN",
        )

    stock_minimo_display.short_description = "Stock Mín."

    def permite_stock_neg(self, obj):
        """Icono para stock negativo permitido"""
        if obj.permite_stock_negativo:
            return format_html("✅")
        return format_html("❌")

    permite_stock_neg.short_description = "Stock -"
    permite_stock_neg.boolean = True

    def estado_badge(self, obj):
        """Badge de estado"""
        if obj.activo:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">ACTIVO</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">INACTIVO</span>'
        )

    estado_badge.short_description = "Estado"

    actions = ["activar_productos", "desactivar_productos", "duplicar_producto"]

    def activar_productos(self, request, queryset):
        """Acción para activar productos"""
        updated = queryset.update(activo=True)
        self.message_user(request, f"{updated} producto(s) activado(s) exitosamente.")

    activar_productos.short_description = "Activar productos seleccionados"

    def desactivar_productos(self, request, queryset):
        """Acción para desactivar productos"""
        updated = queryset.update(activo=False)
        self.message_user(request, f"{updated} producto(s) desactivado(s) exitosamente.")

    desactivar_productos.short_description = "Desactivar productos seleccionados"

    def duplicar_producto(self, request, queryset):
        """Duplicar producto seleccionado (crea copia sin código de barras)"""
        if queryset.count() != 1:
            self.message_user(
                request, "Seleccione exactamente un producto para duplicar.", level="error"
            )
            return

        producto = queryset.first()
        producto.pk = None
        producto.codigo_barra = None
        producto.descripcion = f"{producto.descripcion} (Copia)"
        producto.activo = False
        producto.save()

        self.message_user(request, f"Producto duplicado: {producto.descripcion}")

    duplicar_producto.short_description = "Duplicar producto"


# ==================== ADMIN DE LISTAS DE PRECIOS ====================


@admin.register(ListasPrecios)
class ListasPreciosAdmin(admin.ModelAdmin):
    """
    Administración de Listas de Precios
    """

    list_display = [
        "nombre_lista_badge",
        "moneda_display",
        "fecha_vigencia_display",
        "total_precios",
        "estado_badge",
    ]
    list_filter = ["activo", "moneda", "fecha_vigencia"]
    search_fields = ["nombre_lista"]
    ordering = ["nombre_lista"]
    date_hierarchy = "fecha_vigencia"
    list_per_page = 50

    fieldsets = (
        ("Información Básica", {"fields": ("nombre_lista", "moneda", "activo")}),
        (
            "Vigencia",
            {
                "fields": ("fecha_vigencia",),
                "description": "Fecha desde la cual es válida esta lista de precios",
            },
        ),
    )

    def nombre_lista_badge(self, obj):
        """Nombre de lista en badge"""
        return format_html(
            '<span style="background-color: #007bff; color: white; padding: 4px 12px; border-radius: 3px; font-weight: bold;">{}</span>',
            obj.nombre_lista,
        )

    nombre_lista_badge.short_description = "Lista"

    def moneda_display(self, obj):
        """Moneda en badge"""
        colores = {
            "PYG": "#198754",
            "USD": "#0d6efd",
            "EUR": "#6610f2",
            "BRL": "#ffc107",
            "ARS": "#17a2b8",
        }
        color = colores.get(obj.moneda, "#6c757d")

        simbolos = {
            "PYG": "₲",
            "USD": "$",
            "EUR": "€",
            "BRL": "R$",
            "ARS": "$",
        }
        simbolo = simbolos.get(obj.moneda, obj.moneda)

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold; font-size: 13px;">{} {}</span>',
            color,
            simbolo,
            obj.moneda,
        )

    moneda_display.short_description = "Moneda"

    def fecha_vigencia_display(self, obj):
        """Fecha de vigencia formateada"""
        if obj.fecha_vigencia:
            from django.utils import timezone

            hoy = timezone.now().date()

            if obj.fecha_vigencia > hoy:
                color = "#ffc107"  # Amarillo para futuro
                label = f'{obj.fecha_vigencia.strftime("%d/%m/%Y")} (Futuro)'
            elif obj.fecha_vigencia == hoy:
                color = "#28a745"  # Verde para hoy
                label = f'{obj.fecha_vigencia.strftime("%d/%m/%Y")} (HOY)'
            else:
                color = "#17a2b8"  # Azul para pasado
                label = obj.fecha_vigencia.strftime("%d/%m/%Y")

            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>', color, label
            )
        return "-"

    fecha_vigencia_display.short_description = "Vigencia"

    def total_precios(self, obj):
        """Total de precios en esta lista"""
        total = obj.precios.count()

        if total > 0:
            promedio = obj.precios.aggregate(Avg("precio_unitario"))[
                "precio_unitario__avg"
            ] or Decimal("0")
            return format_html(
                '<span style="font-weight: bold;">{}</span> precios<br><small style="color: #6c757d;">Promedio: ₲{:,.0f}</small>',
                total,
                promedio,
            )
        return "0 precios"

    total_precios.short_description = "Precios"

    def estado_badge(self, obj):
        """Badge de estado"""
        if obj.activo:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">ACTIVA</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">INACTIVA</span>'
        )

    estado_badge.short_description = "Estado"


# ==================== ADMIN DE PRECIOS POR LISTA ====================


@admin.register(PreciosPorLista)
class PreciosPorListaAdmin(admin.ModelAdmin):
    """
    Administración de Precios por Lista
    """

    list_display = [
        "producto_info",
        "lista_badge",
        "precio_display",
        "fecha_vigencia_display",
        "precio_anterior_info",
    ]
    list_filter = ["id_lista", "fecha_vigencia"]
    search_fields = [
        "id_producto__descripcion",
        "id_producto__codigo_barra",
        "id_lista__nombre_lista",
    ]
    ordering = ["-fecha_vigencia", "id_lista"]
    date_hierarchy = "fecha_vigencia"
    list_per_page = 50
    autocomplete_fields = ["id_producto", "id_lista"]

    fieldsets = (
        ("Producto y Lista", {"fields": ("id_producto", "id_lista")}),
        (
            "Precio",
            {"fields": ("precio_unitario",), "description": "Precio del producto en esta lista"},
        ),
    )

    def producto_info(self, obj):
        """Información del producto"""
        producto = obj.id_producto
        if producto.codigo_barra:
            return format_html(
                '<strong>{}</strong><br><small style="color: #6c757d;">{}</small>',
                producto.descripcion[:40],
                producto.codigo_barra,
            )
        return format_html("<strong>{}</strong>", producto.descripcion[:40])

    producto_info.short_description = "Producto"

    def lista_badge(self, obj):
        """Lista en badge"""
        return format_html(
            '<span style="background-color: #007bff; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            obj.id_lista.nombre_lista,
        )

    lista_badge.short_description = "Lista"

    def precio_display(self, obj):
        """Precio formateado"""
        simbolos = {
            "PYG": "₲",
            "USD": "$",
            "EUR": "€",
            "BRL": "R$",
            "ARS": "$",
        }
        simbolo = simbolos.get(obj.id_lista.moneda, obj.id_lista.moneda)

        return format_html(
            '<span style="color: #28a745; font-weight: bold; font-size: 14px;">{} {:,.2f}</span>',
            simbolo,
            obj.precio_unitario,
        )

    precio_display.short_description = "Precio"

    def fecha_vigencia_display(self, obj):
        """Fecha de vigencia"""
        return obj.fecha_vigencia.strftime("%d/%m/%Y %H:%M")

    fecha_vigencia_display.short_description = "Vigencia"

    def precio_anterior_info(self, obj):
        """Muestra variación vs precio anterior"""
        # Buscar precio anterior
        precio_anterior = (
            PreciosPorLista.objects.filter(
                id_producto=obj.id_producto,
                id_lista=obj.id_lista,
                fecha_vigencia__lt=obj.fecha_vigencia,
            )
            .order_by("-fecha_vigencia")
            .first()
        )

        if precio_anterior:
            diferencia = obj.precio_unitario - precio_anterior.precio_unitario
            porcentaje = (diferencia / precio_anterior.precio_unitario) * 100

            if diferencia > 0:
                return format_html(
                    '<span style="color: #dc3545;">▲ {:,.0f} ({:+.1f}%)</span>',
                    diferencia,
                    porcentaje,
                )
            elif diferencia < 0:
                return format_html(
                    '<span style="color: #28a745;">▼ {:,.0f} ({:.1f}%)</span>',
                    abs(diferencia),
                    porcentaje,
                )
            return "="
        return "-"

    precio_anterior_info.short_description = "Variación"


# ==================== ADMIN DE HISTÓRICO DE PRECIOS ====================


@admin.register(HistoricoPrecios)
class HistoricoPreciosAdmin(admin.ModelAdmin):
    """
    Administración de Histórico de Precios
    """

    list_display = [
        "producto_link",
        "precio_anterior_display",
        "flecha",
        "precio_nuevo_display",
        "variacion_display",
        "fecha_cambio_display",
        "empleado_info",
    ]
    list_filter = ["fecha_cambio"]
    search_fields = [
        "id_producto__descripcion",
        "id_producto__codigo_barra",
        "id_empleado__nombre",
        "id_empleado__apellido",
    ]
    ordering = ["-fecha_cambio"]
    date_hierarchy = "fecha_cambio"
    list_per_page = 100
    autocomplete_fields = ["id_producto", "id_empleado"]

    fieldsets = (
        ("Producto", {"fields": ("id_producto",)}),
        (
            "Cambio de Precio",
            {
                "fields": ("precio_anterior", "precio_nuevo"),
                "description": "Registro del cambio de precio",
            },
        ),
        (
            "Auditoría",
            {
                "fields": ("id_empleado",),
                "description": "Empleado que realizó el cambio (opcional)",
            },
        ),
    )

    def producto_link(self, obj):
        """Link al producto"""
        url = reverse("admin:productos_productos_change", args=[obj.id_producto.id_producto])
        return format_html(
            '<a href="{}" style="font-weight: bold;">{}</a>', url, obj.id_producto.descripcion[:40]
        )

    producto_link.short_description = "Producto"

    def precio_anterior_display(self, obj):
        """Precio anterior formateado"""
        return format_html(
            '<span style="color: #dc3545; font-weight: bold;">₲{:,.2f}</span>', obj.precio_anterior
        )

    precio_anterior_display.short_description = "Precio Anterior"

    def flecha(self, obj):
        """Flecha indicando cambio"""
        return format_html("→")

    flecha.short_description = ""

    def precio_nuevo_display(self, obj):
        """Precio nuevo formateado"""
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">₲{:,.2f}</span>', obj.precio_nuevo
        )

    precio_nuevo_display.short_description = "Precio Nuevo"

    def variacion_display(self, obj):
        """Variación porcentual con badge"""
        if obj.variacion_porcentual > 0:
            color = "#dc3545"  # Rojo para aumento
            simbolo = "▲"
        else:
            color = "#28a745"  # Verde para disminución
            simbolo = "▼"

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{} {:.1f}%</span>',
            color,
            simbolo,
            abs(obj.variacion_porcentual),
        )

    variacion_display.short_description = "Variación"

    def fecha_cambio_display(self, obj):
        """Fecha de cambio formateada"""
        return obj.fecha_cambio.strftime("%d/%m/%Y %H:%M")

    fecha_cambio_display.short_description = "Fecha"

    def empleado_info(self, obj):
        """Información del empleado"""
        if obj.id_empleado:
            return format_html(
                '<span style="color: #6c757d;">{} {}</span>',
                obj.id_empleado.nombre,
                obj.id_empleado.apellido,
            )
        return format_html('<span style="color: #6c757d; font-style: italic;">Sistema</span>')

    empleado_info.short_description = "Registrado por"
