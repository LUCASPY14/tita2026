from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from common.permissions import (
    ROLES_AUTORIZADORES, IsAdmin, IsCajeroCobradorSupervisorOrAdmin, exigir_rol,
)

from .models import CierreCuentaAlumno, ResolucionSaldo
from .serializers import (
    AbrirCierreSerializer, AbrirMasivoSerializer, CierreCuentaDetalleSerializer,
    CierreCuentaSerializer, MotivoSerializer, RegistrarResolucionSerializer,
    ResolucionSaldoSerializer,
)
from .services import CierreCuentaService


class CierreCuentaViewSet(viewsets.ReadOnlyModelViewSet):
    """Expedientes de cierre de cuenta de alumnos que egresan.

    Lectura: ADMIN, SUPERVISOR, CAJERO, COBRADOR. Cada acción valida además el rol
    que corresponde (ver CierreCuentaService).
    """

    permission_classes = [IsCajeroCobradorSupervisorOrAdmin]
    queryset = CierreCuentaAlumno.objects.select_related(
        "hijo__grado", "hijo__cliente_responsable", "hijo__tarjeta", "hijo__saldo_almuerzo",
    ).prefetch_related("resoluciones").all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["anio", "estado", "hijo"]
    search_fields = ["hijo__nombre", "hijo__apellido", "hijo__tarjeta__nro_tarjeta"]
    ordering_fields = ["anio", "fecha_apertura", "hijo__apellido"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CierreCuentaDetalleSerializer
        return CierreCuentaSerializer

    @action(detail=False, methods=["post"], url_path="abrir")
    def abrir(self, request):
        """Abre el expediente de un alumno (por ejemplo un retiro fuera del último curso)."""
        exigir_rol(request.user, ROLES_AUTORIZADORES, "Solo un administrador o supervisor abre un cierre.")
        datos = AbrirCierreSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        cierre, creado = CierreCuentaService.abrir(
            datos.validated_data["hijo"], datos.validated_data.get("anio"), request.user,
        )
        return Response(
            CierreCuentaSerializer(cierre, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED if creado else status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="abrir-masivo")
    def abrir_masivo(self, request):
        """Abre el expediente de todos los alumnos del último curso y de los dados de baja en el año."""
        exigir_rol(request.user, ROLES_AUTORIZADORES, "Solo un administrador o supervisor abre cierres.")
        datos = AbrirMasivoSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        return Response(CierreCuentaService.abrir_masivo(datos.validated_data.get("anio"), request.user))

    @action(detail=True, methods=["post"], url_path="resoluciones")
    def resoluciones(self, request, pk=None):
        cierre = self.get_object()
        datos = RegistrarResolucionSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        resolucion, advertencia = CierreCuentaService.registrar_resolucion(
            cierre=cierre, usuario=request.user, **datos.validated_data,
        )
        salida = {"resolucion": ResolucionSaldoSerializer(resolucion).data}
        if advertencia:
            salida["advertencia"] = advertencia
        return Response(salida, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cerrar")
    def cerrar(self, request, pk=None):
        """Cierra el expediente dejando saldos pendientes registrados (solo ADMIN)."""
        cierre = self.get_object()
        datos = MotivoSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        cierre = CierreCuentaService.cerrar_con_saldo(cierre, request.user, datos.validated_data["motivo"])
        return Response(CierreCuentaDetalleSerializer(cierre, context=self.get_serializer_context()).data)

    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        """Totales del año: alumnos, estados, saldo a devolver, deuda a cobrar y pendientes."""
        anio = int(request.query_params.get("anio") or timezone.localdate().year)
        cierres = list(self.get_queryset().filter(anio=anio))
        a_devolver = deuda = 0
        for c in cierres:
            if c.estado == CierreCuentaAlumno.Estado.RESUELTO:
                continue
            for saldo in (self._saldo(c, "tarjeta"), self._saldo(c, "saldo_almuerzo")):
                if saldo > 0:
                    a_devolver += saldo
                else:
                    deuda += -saldo
        pendientes = ResolucionSaldo.objects.filter(
            cierre__anio=anio, estado=ResolucionSaldo.Estado.SOLICITADA,
        ).count()
        por_estado = {e: 0 for e in CierreCuentaAlumno.Estado.values}
        for c in cierres:
            por_estado[c.estado] += 1
        return Response({
            "anio": anio,
            "alumnos": len(cierres),
            "por_estado": por_estado,
            "saldo_a_devolver": int(a_devolver),
            "deuda_a_cobrar": int(deuda),
            "resoluciones_pendientes": pendientes,
        })

    @staticmethod
    def _saldo(cierre, relacion):
        try:
            return getattr(cierre.hijo, relacion).saldo_actual
        except ObjectDoesNotExist:
            return 0


class ResolucionSaldoViewSet(viewsets.ReadOnlyModelViewSet):
    """Historial de resoluciones (línea de tiempo) y su aprobación o rechazo."""

    permission_classes = [IsCajeroCobradorSupervisorOrAdmin]
    queryset = ResolucionSaldo.objects.select_related(
        "cierre__hijo", "hijo_destino", "solicitado_por", "decidido_por",
    ).all()
    serializer_class = ResolucionSaldoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["cierre", "estado", "tipo", "cierre__hijo", "cierre__anio"]
    ordering_fields = ["fecha_solicitud", "monto"]

    def get_permissions(self):
        if self.action in ("aprobar", "rechazar"):
            return [IsAdmin()]
        return super().get_permissions()

    @action(detail=True, methods=["post"], url_path="aprobar")
    def aprobar(self, request, pk=None):
        resolucion, advertencia = CierreCuentaService.aprobar(self.get_object(), request.user)
        salida = {"resolucion": ResolucionSaldoSerializer(resolucion).data}
        if advertencia:
            salida["advertencia"] = advertencia
        return Response(salida)

    @action(detail=True, methods=["post"], url_path="rechazar")
    def rechazar(self, request, pk=None):
        datos = MotivoSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        resolucion = CierreCuentaService.rechazar(self.get_object(), request.user, datos.validated_data["motivo"])
        return Response({"resolucion": ResolucionSaldoSerializer(resolucion).data})
