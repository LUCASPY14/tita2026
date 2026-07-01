"""
Views para la app clientes
"""

import csv
from datetime import date
from decimal import Decimal

from django.http import HttpResponse

from rest_framework import viewsets, status
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdminOrReadOnly, IsCajeroOrAdmin, IsStaffOrClienteWeb, IsStaffUser

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.decorators import action

from .models import (
    AlumnoResponsable,
    AutorizacionSaldoNegativo,
    Ciudad,
    Cliente,
    CuentaCorrienteCliente,
    Grado,
    HistorialGrado,
    Hijo,
    Pais,
    RestriccionHijo,
    TipoCliente,
)
from .serializers import (
    AlumnoResponsableSerializer,
    AutorizacionSaldoNegativoSerializer,
    CiudadSerializer,
    ClienteSerializer,
    CuentaCorrienteClienteSerializer,
    GradoSerializer,
    HistorialGradoSerializer,
    HijoSerializer,
    PaisSerializer,
    RestriccionHijoSerializer,
    TipoClienteSerializer,
)
from .services import cambiar_titular


def _crear_usuario_portal(cliente):
    """Crea (o vincula) un usuario CLIENTE_WEB para el cliente dado.

    - Si ya tiene usuario portal, no hace nada.
    - Usa el email del cliente como identificador; si no tiene email, genera
      uno sintético: <ruc_ci_limpio>@portal.tita.local
    - La contraseña inicial es el RUC/CI tal como está almacenado.
    - El usuario queda marcado con debe_cambiar_contrasena=True.
    """
    from apps.usuarios.models import Usuario

    if hasattr(cliente, "usuario_portal") and cliente.usuario_portal_id:
        return

    ruc_ci_limpio = cliente.ruc_ci.strip()
    email = (cliente.email or "").strip()
    if not email:
        sufijo = ruc_ci_limpio.replace("-", "").replace(".", "")
        email = f"{sufijo}@portal.tita.local"

    if Usuario.objects.filter(email=email).exists():
        # Ya existe un usuario con ese email: vincular si no tiene cliente
        usuario = Usuario.objects.get(email=email)
        if not usuario.cliente_id:
            usuario.cliente = cliente
            usuario.save(update_fields=["cliente"])
        return

    Usuario.objects.create_user(
        email=email,
        password=ruc_ci_limpio,
        nombre=cliente.nombres,
        apellido=cliente.apellidos,
        rol=Usuario.Rol.CLIENTE_WEB,
        is_active=True,
        email_verificado=bool(cliente.email),
        debe_cambiar_contrasena=True,
        cliente=cliente,
    )


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related("tipo_cliente", "lista_precio").all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["activo", "tipo_cliente"]
    search_fields = ["ruc_ci", "nombres", "apellidos"]

    def perform_create(self, serializer):
        cliente = serializer.save()
        _crear_usuario_portal(cliente)

    @action(detail=True, methods=["post"], url_path="reset-pin",
            permission_classes=[IsAdminOrReadOnly])
    def reset_pin(self, request, pk=None):
        """Solo ADMIN: resetea el PIN del cliente a '0000'."""
        if request.user.rol != "ADMIN":
            return Response({"error": "Solo el administrador puede resetear el PIN."},
                            status=status.HTTP_403_FORBIDDEN)
        cliente = self.get_object()
        cliente.set_pin("0000")
        return Response({"ok": True, "mensaje": "PIN reseteado a 0000."})

    @action(detail=True, methods=["post"], url_path="cambiar-pin",
            permission_classes=[IsAdminOrReadOnly])
    def cambiar_pin(self, request, pk=None):
        """El padre (CLIENTE_WEB) cambia su propio PIN. El admin puede cambiar cualquiera."""
        cliente = self.get_object()
        user = request.user

        # Verificar que el cliente web solo modifique su propio PIN
        if user.rol == "CLIENTE_WEB":
            if not hasattr(user, "cliente") or user.cliente_id != cliente.pk:
                return Response({"error": "No podés modificar el PIN de otro cliente."},
                                status=status.HTTP_403_FORBIDDEN)

        pin_actual = request.data.get("pin_actual", "")
        pin_nuevo = request.data.get("pin_nuevo", "")

        if not pin_nuevo or len(pin_nuevo) != 4 or not pin_nuevo.isdigit():
            return Response({"error": "El PIN nuevo debe ser exactamente 4 dígitos."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Admin no necesita confirmar el PIN actual
        if user.rol != "ADMIN":
            if not cliente.check_pin(pin_actual):
                return Response({"error": "PIN actual incorrecto."},
                                status=status.HTTP_400_BAD_REQUEST)

        cliente.set_pin(pin_nuevo)
        return Response({"ok": True, "mensaje": "PIN actualizado correctamente."})


class CuentaCorrienteClienteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CuentaCorrienteCliente.objects.select_related("cliente").all()
    serializer_class = CuentaCorrienteClienteSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["cliente", "tipo"]


class TipoClienteViewSet(viewsets.ModelViewSet):
    queryset = TipoCliente.objects.all()
    serializer_class = TipoClienteSerializer
    permission_classes = [IsAdminOrReadOnly]


class HijoViewSet(viewsets.ModelViewSet):
    serializer_class = HijoSerializer
    permission_classes = [IsStaffOrClienteWeb]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["activo", "cliente_responsable"]
    search_fields = ["nombre", "apellido"]

    def get_queryset(self):
        from django.db.models import Prefetch
        qs = Hijo.objects.select_related("cliente_responsable", "grado").prefetch_related(
            Prefetch(
                "responsables",
                queryset=AlumnoResponsable.objects.filter(activo=True)
                    .select_related("cliente")
                    .order_by("orden_cobro"),
            )
        )
        if self.request.user.es_cliente_web:
            cliente = getattr(self.request.user, "cliente", None)
            if cliente is None:
                return qs.none()
            qs = qs.filter(cliente_responsable=cliente)
        return qs


class GradoViewSet(viewsets.ModelViewSet):
    queryset = Grado.objects.all()
    serializer_class = GradoSerializer
    permission_classes = [IsAdminOrReadOnly]


class HistorialGradoViewSet(viewsets.ModelViewSet):
    queryset = HistorialGrado.objects.select_related("hijo").all()
    serializer_class = HistorialGradoSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["hijo", "anio_escolar"]


class RestriccionHijoViewSet(viewsets.ModelViewSet):
    serializer_class = RestriccionHijoSerializer
    permission_classes = [IsStaffOrClienteWeb]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["hijo", "severidad", "activo"]

    def get_queryset(self):
        qs = RestriccionHijo.objects.select_related("hijo__cliente_responsable")
        if self.request.user.es_cliente_web:
            cliente = getattr(self.request.user, "cliente", None)
            if cliente is None:
                return qs.none()
            qs = qs.filter(hijo__cliente_responsable=cliente)
        return qs


class AutorizacionSaldoNegativoViewSet(viewsets.ModelViewSet):
    queryset = AutorizacionSaldoNegativo.objects.select_related("cliente", "venta").all()
    serializer_class = AutorizacionSaldoNegativoSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["cliente", "estado"]


class PaisViewSet(viewsets.ModelViewSet):
    queryset = Pais.objects.all()
    serializer_class = PaisSerializer
    permission_classes = [IsAdminOrReadOnly]


class CiudadViewSet(viewsets.ModelViewSet):
    queryset = Ciudad.objects.select_related("pais").all()
    serializer_class = CiudadSerializer
    permission_classes = [IsAdminOrReadOnly]


# ==============================================================================
# REPORTE CUENTA CORRIENTE
# ==============================================================================

class ReporteCuentaCorrienteView(APIView):
    """
    GET /api/clientes/reporte-cuenta-corriente/
    Clientes con saldo pendiente y distribución por aging (30/60/90/90+ días).
    Opcional: ?formato=csv
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        hoy = date.today()

        # Último movimiento por cliente para conocer saldo actual
        from django.db.models import OuterRef, Subquery

        ultimo_mov = (
            CuentaCorrienteCliente.objects
            .filter(cliente=OuterRef("pk"))
            .order_by("-id")
            .values("saldo_resultante")[:1]
        )
        clientes_con_saldo = (
            Cliente.objects
            .filter(activo=True)
            .annotate(saldo_deuda=Subquery(ultimo_mov))
            .filter(saldo_deuda__gt=0)
            .order_by("-saldo_deuda")
        )

        filas = []
        for cliente in clientes_con_saldo:
            saldo = Decimal(str(cliente.saldo_deuda or 0))

            # Buscar la venta pendiente más antigua para calcular aging
            venta_antigua = (
                CuentaCorrienteCliente.objects
                .filter(cliente=cliente, tipo="DEBITO")
                .order_by("fecha")
                .values("fecha")
                .first()
            )
            dias_atraso = 0
            if venta_antigua:
                dias_atraso = (hoy - venta_antigua["fecha"].date()).days

            if dias_atraso <= 30:
                bucket = "0-30"
            elif dias_atraso <= 60:
                bucket = "31-60"
            elif dias_atraso <= 90:
                bucket = "61-90"
            else:
                bucket = "90+"

            filas.append({
                "cliente_id": cliente.pk,
                "cliente": cliente.nombre_completo,
                "ruc_ci": cliente.ruc_ci,
                "telefono": cliente.telefono or "",
                "email": cliente.email or "",
                "saldo_deuda": int(saldo),
                "dias_atraso": dias_atraso,
                "aging": bucket,
            })

        # Totales por bucket
        aging_totales = {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
        for f in filas:
            aging_totales[f["aging"]] += f["saldo_deuda"]

        total_deuda = sum(f["saldo_deuda"] for f in filas)

        if request.query_params.get("formato") == "csv":
            resp = HttpResponse(content_type="text/csv; charset=utf-8-sig")
            resp["Content-Disposition"] = (
                f'attachment; filename="cuenta_corriente_{hoy}.csv"'
            )
            writer = csv.writer(resp)
            writer.writerow(["REPORTE CUENTA CORRIENTE", str(hoy)])
            writer.writerow([])
            writer.writerow(["Cliente", "RUC/CI", "Teléfono", "Email", "Saldo (Gs)", "Días atraso", "Aging"])
            for f in filas:
                writer.writerow([f["cliente"], f["ruc_ci"], f["telefono"],
                                  f["email"], f["saldo_deuda"], f["dias_atraso"], f["aging"]])
            writer.writerow([])
            writer.writerow(["TOTALES POR AGING"])
            for bucket, total in aging_totales.items():
                writer.writerow([bucket, total])
            return resp

        return Response({
            "fecha": str(hoy),
            "resumen": {
                "clientes_con_deuda": len(filas),
                "total_deuda": total_deuda,
                "aging": aging_totales,
            },
            "detalle": filas,
        })


# ==============================================================================
# ALUMNO RESPONSABLE
# ==============================================================================

class AlumnoResponsableViewSet(viewsets.ModelViewSet):
    """
    CRUD de responsables de un alumno.

    Rutas automáticas (router):
      GET    /clientes/responsables/          → lista (filtrable por hijo, cliente, activo)
      POST   /clientes/responsables/          → crear responsable
      GET    /clientes/responsables/{id}/     → detalle
      PATCH  /clientes/responsables/{id}/     → editar
      DELETE /clientes/responsables/{id}/     → eliminar (valida que no sea el último titular)

    Acciones custom:
      POST /clientes/responsables/{id}/set_titular/ → designar como titular
    """

    serializer_class = AlumnoResponsableSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["hijo", "cliente", "activo", "es_titular"]

    def get_queryset(self):
        return (
            AlumnoResponsable.objects.select_related("hijo", "cliente", "agregado_por")
            .order_by("hijo_id", "orden_cobro")
        )

    def perform_create(self, serializer):
        serializer.save(agregado_por=self.request.user)

    def perform_destroy(self, instance):
        # Impedir eliminar el único titular activo
        if instance.es_titular and instance.activo:
            otros_activos = AlumnoResponsable.objects.filter(
                hijo=instance.hijo, activo=True
            ).exclude(pk=instance.pk).count()
            if otros_activos == 0:
                from rest_framework.exceptions import ValidationError
                raise ValidationError(
                    "No se puede eliminar al único responsable activo del alumno. "
                    "Agregue otro responsable antes de eliminar este."
                )
        instance.delete()

    @action(detail=True, methods=["post"], url_path="set_titular")
    def set_titular(self, request, pk=None):
        """
        POST /clientes/responsables/{id}/set_titular/
        Designa este responsable como titular del alumno.
        Sincroniza Hijo.cliente_responsable automáticamente.
        """
        responsable = self.get_object()
        try:
            actualizado = cambiar_titular(
                hijo=responsable.hijo,
                nuevo_cliente_id=responsable.cliente_id,
                changed_by=request.user,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            AlumnoResponsableSerializer(actualizado).data,
            status=status.HTTP_200_OK,
        )
