"""
Views para la app clientes
"""

import csv
from datetime import date, timedelta
from decimal import Decimal

from django.http import HttpResponse

from rest_framework import viewsets, status
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdminOrReadOnly, IsCajeroOrAdmin, IsStaffOrClienteWeb, IsStaffUser

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Cliente,
    CuentaCorrienteCliente,
    TipoCliente,
    Hijo,
    Grado,
    HistorialGrado,
    RestriccionHijo,
    AutorizacionSaldoNegativo,
    Pais,
    Ciudad,
)
from .serializers import (
    ClienteSerializer,
    CuentaCorrienteClienteSerializer,
    TipoClienteSerializer,
    HijoSerializer,
    GradoSerializer,
    HistorialGradoSerializer,
    RestriccionHijoSerializer,
    AutorizacionSaldoNegativoSerializer,
    PaisSerializer,
    CiudadSerializer,
)


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related("tipo_cliente", "lista_precio").all()
    serializer_class = ClienteSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["activo", "tipo_cliente"]
    search_fields = ["ruc_ci", "nombres", "apellidos"]


class CuentaCorrienteClienteViewSet(viewsets.ModelViewSet):
    queryset = CuentaCorrienteCliente.objects.select_related("cliente").all()
    serializer_class = CuentaCorrienteClienteSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["cliente", "tipo"]


class TipoClienteViewSet(viewsets.ModelViewSet):
    queryset = TipoCliente.objects.all()
    serializer_class = TipoClienteSerializer
    permission_classes = [IsAdminOrReadOnly]


class HijoViewSet(viewsets.ModelViewSet):
    queryset = Hijo.objects.select_related("cliente_responsable").all()
    serializer_class = HijoSerializer
    permission_classes = [IsStaffOrClienteWeb]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["activo", "cliente_responsable"]
    search_fields = ["nombre", "apellido"]


class GradoViewSet(viewsets.ModelViewSet):
    queryset = Grado.objects.all()
    serializer_class = GradoSerializer
    permission_classes = [IsAdminOrReadOnly]


class HistorialGradoViewSet(viewsets.ModelViewSet):
    queryset = HistorialGrado.objects.select_related("hijo").all()
    serializer_class = HistorialGradoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["hijo", "anio_escolar"]


class RestriccionHijoViewSet(viewsets.ModelViewSet):
    queryset = RestriccionHijo.objects.select_related("hijo").all()
    serializer_class = RestriccionHijoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["hijo", "severidad", "activo"]


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
    queryset = Ciudad.objects.all()
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