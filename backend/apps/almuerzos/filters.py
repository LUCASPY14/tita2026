import django_filters
from .models import RegistroConsumoAlmuerzo


class RegistroConsumoFilter(django_filters.FilterSet):
    fecha_desde = django_filters.DateFilter(field_name="fecha_consumo", lookup_expr="gte")
    fecha_hasta = django_filters.DateFilter(field_name="fecha_consumo", lookup_expr="lte")

    class Meta:
        model = RegistroConsumoAlmuerzo
        fields = ["estado", "hijo", "fecha_consumo", "ya_cobrado", "fecha_desde", "fecha_hasta"]
