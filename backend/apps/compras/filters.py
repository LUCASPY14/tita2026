import django_filters
from .models import Compra


class CompraFilter(django_filters.FilterSet):
    fecha_desde = django_filters.DateFilter(field_name="fecha", lookup_expr="date__gte")
    fecha_hasta = django_filters.DateFilter(field_name="fecha", lookup_expr="date__lte")

    class Meta:
        model = Compra
        fields = ["proveedor", "estado_pago", "estado_entrega", "tipo_pago", "fecha_desde", "fecha_hasta"]
