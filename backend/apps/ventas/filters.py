import django_filters
from .models import Venta


class VentaFilter(django_filters.FilterSet):
    fecha_desde = django_filters.DateFilter(field_name="fecha", lookup_expr="date__gte")
    fecha_hasta = django_filters.DateFilter(field_name="fecha", lookup_expr="date__lte")
    tipo = django_filters.CharFilter(field_name="tipo", lookup_expr="exact")
    estado = django_filters.CharFilter(field_name="estado", lookup_expr="exact")
    estado_pago = django_filters.CharFilter(field_name="estado_pago", lookup_expr="exact")

    class Meta:
        model = Venta
        fields = ["estado", "estado_pago", "tipo", "cliente", "hijo", "tarjeta", "cajero", "fecha_desde", "fecha_hasta"]
