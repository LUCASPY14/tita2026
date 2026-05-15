"""
Views para la app notificaciones
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

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
    queryset = Notificacion.objects.select_related("usuario").all()
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["usuario", "tipo", "destino", "leida"]


class PreferenciaNotificacionViewSet(viewsets.ModelViewSet):
    queryset = PreferenciaNotificacion.objects.select_related("usuario").all()
    serializer_class = PreferenciaNotificacionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["usuario", "tipo_notificacion"]


class PlantillaEmailViewSet(viewsets.ModelViewSet):
    queryset = PlantillaEmail.objects.all()
    serializer_class = PlantillaEmailSerializer
    permission_classes = [IsAuthenticated]


class EmailEnviadoViewSet(viewsets.ModelViewSet):
    queryset = EmailEnviado.objects.select_related("cliente").all()
    serializer_class = EmailEnviadoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["estado"]


class SolicitudNotificacionViewSet(viewsets.ModelViewSet):
    queryset = SolicitudNotificacion.objects.select_related("cliente").all()
    serializer_class = SolicitudNotificacionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["cliente", "estado", "destino"]