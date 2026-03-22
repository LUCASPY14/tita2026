from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Impuestos
from .serializers import ImpuestosSerializer


class ImpuestosViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para impuestos/tasas (IVA 10%, IVA 5%, Exenta)."""
    queryset = Impuestos.objects.filter(estado=True).order_by('nombre_impuesto')
    serializer_class = ImpuestosSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
