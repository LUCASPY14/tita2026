"""
Filtros para la app inventario
"""

import django_filters

from .models import MovimientoStock


class MovimientoStockFilter(django_filters.FilterSet):
    fecha_desde = django_filters.DateFilter(field_name="fecha", lookup_expr="date__gte")
    fecha_hasta = django_filters.DateFilter(field_name="fecha", lookup_expr="date__lte")
    tipo = django_filters.CharFilter(field_name="tipo", lookup_expr="exact")
    motivo = django_filters.CharFilter(field_name="motivo", lookup_expr="exact")

    class Meta:
        model = MovimientoStock
        fields = ["producto", "tipo", "motivo", "fecha_desde", "fecha_hasta"]
