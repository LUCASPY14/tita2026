"""
Views para la app notificaciones
"""

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdmin, IsStaffOrClienteWeb, IsStaffUser

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Notificacion,
    PreferenciaNotificacion,
    PlantillaEmail,
    EmailEnviado,
    SolicitudNotificacion,
)
from .serializers import (
    NotificacionSerializer,
    PreferenciaNotificacionSerializer,
    PlantillaEmailSerializer,
    EmailEnviadoSerializer,
    SolicitudNotificacionSerializer,
)


class NotificacionViewSet(viewsets.ModelViewSet):
    serializer_class = NotificacionSerializer
    permission_classes = [IsStaffOrClienteWeb]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo", "destino", "leida"]

    def get_queryset(self):
        qs = Notificacion.objects.select_related("usuario")
        if self.request.user.is_staff:
            return qs.all()
        return qs.filter(usuario=self.request.user)


class PreferenciaNotificacionViewSet(viewsets.ModelViewSet):
    serializer_class = PreferenciaNotificacionSerializer
    permission_classes = [IsStaffOrClienteWeb]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo_notificacion"]

    def get_queryset(self):
        qs = PreferenciaNotificacion.objects.select_related("usuario")
        if self.request.user.is_staff:
            return qs.all()
        return qs.filter(usuario=self.request.user)


class PlantillaEmailViewSet(viewsets.ModelViewSet):
    queryset = PlantillaEmail.objects.all()
    serializer_class = PlantillaEmailSerializer
    permission_classes = [IsAdmin]


class EmailEnviadoViewSet(viewsets.ModelViewSet):
    queryset = EmailEnviado.objects.select_related("cliente").all()
    serializer_class = EmailEnviadoSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["estado"]


class SolicitudNotificacionViewSet(viewsets.ModelViewSet):
    queryset = SolicitudNotificacion.objects.select_related("cliente").all()
    serializer_class = SolicitudNotificacionSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["cliente", "estado", "destino"]


class EnviarNotificacionView(APIView):
    """
    POST /api/notificaciones/enviar/
    Procesa solicitudes pendientes y las envía (SISTEMA o EMAIL).
    Body opcional: {"solicitud_ids": [1, 2, 3]}  → procesa solo esas.
    Sin body: procesa todas las PENDIENTES.
    """
    permission_classes = [IsStaffUser]

    def post(self, request):
        from .services import NotificacionService
        solicitud_ids = request.data.get("solicitud_ids") or None
        resultado = NotificacionService.procesar_pendientes(solicitud_ids=solicitud_ids)
        http_status = status.HTTP_200_OK if resultado["enviadas"] > 0 else status.HTTP_207_MULTI_STATUS
        return Response(resultado, status=http_status)
