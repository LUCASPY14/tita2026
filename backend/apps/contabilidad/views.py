from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Impuestos, DatosEmpresa, Timbrados, DocumentosTributarios
from .serializers import (
    ImpuestosSerializer, DatosEmpresaSerializer,
    TimbradoSerializer, DocumentosTributariosSerializer,
)
from datetime import date


class ImpuestosViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para impuestos/tasas (IVA 10%, IVA 5%, Exenta)."""
    queryset = Impuestos.objects.filter(estado=True).order_by('nombre_impuesto')
    serializer_class = ImpuestosSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class DatosEmpresaViewSet(viewsets.ReadOnlyModelViewSet):
    """Datos de la empresa emisora (RUC, razón social, dirección)."""
    queryset = DatosEmpresa.objects.filter(estado=True)
    serializer_class = DatosEmpresaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    @action(detail=False, methods=["get"], url_path="activa")
    def activa(self, request):
        """Devuelve los datos de la empresa activa."""
        empresa = DatosEmpresa.objects.filter(estado=True).first()
        if not empresa:
            return Response({"detail": "No hay datos de empresa configurados."}, status=404)
        return Response(DatosEmpresaSerializer(empresa).data)


class TimbradosViewSet(viewsets.ReadOnlyModelViewSet):
    """Timbrados registrados ante la SET."""
    queryset = Timbrados.objects.filter(estado=True).order_by("-fecha_inicio")
    serializer_class = TimbradoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    @action(detail=False, methods=["get"], url_path="vigente")
    def vigente(self, request):
        """Devuelve el timbrado físico (no electrónico) vigente a hoy."""
        hoy = date.today()
        timbrado = Timbrados.objects.filter(
            estado=True,
            es_electronico=0,
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy,
        ).order_by("-fecha_inicio").first()
        if not timbrado:
            return Response(
                {"detail": "No hay timbrado físico vigente configurado."}, status=404
            )
        return Response(TimbradoSerializer(timbrado).data)


class DocumentosTributariosViewSet(viewsets.ReadOnlyModelViewSet):
    """Documentos tributarios emitidos (facturas físicas y electrónicas)."""
    queryset = DocumentosTributarios.objects.select_related("nro_timbrado").order_by("-fecha_emision")
    serializer_class = DocumentosTributariosSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["tipo_documento", "estado_sifen"]
