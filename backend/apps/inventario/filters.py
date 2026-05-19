"""
Filtros para la app inventario
"""

import django_filters

from .models import MovimientoStock, AlertaStock, LoteProducto, AlertaVencimiento


class MovimientoStockFilter(django_filters.FilterSet):
    fecha_desde = django_filters.DateFilter(field_name="fecha", lookup_expr="date__gte")
    fecha_hasta = django_filters.DateFilter(field_name="fecha", lookup_expr="date__lte")

    class Meta:
        model = MovimientoStock
        fields = ["producto", "tipo", "motivo", "fecha_desde", "fecha_hasta"]


class AlertaStockFilter(django_filters.FilterSet):
    class Meta:
        model = AlertaStock
        fields = ["producto", "tipo", "activa"]


class LoteProductoFilter(django_filters.FilterSet):
    vence_antes = django_filters.DateFilter(field_name="fecha_vencimiento", lookup_expr="lte")
    vence_despues = django_filters.DateFilter(field_name="fecha_vencimiento", lookup_expr="gte")

    class Meta:
        model = LoteProducto
        fields = ["producto", "bloqueado", "vence_antes", "vence_despues"]


class AlertaVencimientoFilter(django_filters.FilterSet):
    class Meta:
        model = AlertaVencimiento
        fields = ["lote", "tipo"]
