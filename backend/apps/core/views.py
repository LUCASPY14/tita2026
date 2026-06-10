"""
Views para la app core
"""

from django.core.cache import cache

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response

from common.permissions import IsAdmin, IsAdminOrReadOnly, IsCajeroOrAdmin, IsStaffOrClienteWeb, IsStaffUser

from django_filters.rest_framework import DjangoFilterBackend

# Los medios de pago y límites cambian rarísimo → TTL de 1 hora
_CACHE_TTL_LONG = 3600


def _invalidar_cache_core(*prefixes):
    for prefix in prefixes:
        try:
            cache.delete_pattern(f"{prefix}*")
        except (AttributeError, NotImplementedError):
            cache.clear()
            return

from .models import (
    Tarjeta,
    MovimientoTarjeta,
    TarjetaAutorizacion,
    CargaSaldo,
    ConsumoTarjeta,
    MedioPago,
    LimiteTransaccion,
    RegistroAutorizacion,
)
from .serializers import (
    TarjetaSerializer,
    MovimientoTarjetaSerializer,
    TarjetaAutorizacionSerializer,
    CargaSaldoSerializer,
    ConsumoTarjetaSerializer,
    MedioPagoSerializer,
    LimiteTransaccionSerializer,
    RegistroAutorizacionSerializer,
)
from .services import TarjetaService


class TarjetaViewSet(viewsets.ModelViewSet):
    queryset = Tarjeta.objects.select_related("hijo").all()
    serializer_class = TarjetaSerializer
    permission_classes = [IsStaffOrClienteWeb]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado"]
    search_fields = ["nro_tarjeta", "hijo__nombre", "hijo__apellido"]
    ordering = ["nro_tarjeta"]


class MovimientoTarjetaViewSet(viewsets.ModelViewSet):
    queryset = MovimientoTarjeta.objects.select_related("tarjeta").all()
    serializer_class = MovimientoTarjetaSerializer
    permission_classes = [IsStaffOrClienteWeb]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tarjeta", "tipo"]


class TarjetaAutorizacionViewSet(viewsets.ModelViewSet):
    queryset = TarjetaAutorizacion.objects.select_related("empleado").all()
    serializer_class = TarjetaAutorizacionSerializer
    permission_classes = [IsCajeroOrAdmin]


METODOS_CONFIRMACION_INMEDIATA = ("EFECTIVO", "POS DEBITO", "POS CREDITO")


class CargaSaldoViewSet(viewsets.ModelViewSet):
    queryset = CargaSaldo.objects.select_related("tarjeta", "cliente_origen").all()
    serializer_class = CargaSaldoSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tarjeta", "estado"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        metodo = data.get("metodo_pago", "")

        if metodo in METODOS_CONFIRMACION_INMEDIATA:
            from apps.contabilidad.models import CierreCaja
            cierre_caja = CierreCaja.objects.filter(
                empleado=request.user, estado=CierreCaja.Estado.ABIERTO
            ).select_related("caja").first()
            medio_pago_obj = MedioPago.objects.filter(descripcion__iexact=metodo).first()

            carga = TarjetaService.cargar_saldo(
                tarjeta=data["tarjeta"],
                monto=data["monto_cargado"],
                cliente_origen=data.get("cliente_origen"),
                responsable=self.request.user,
                metodo_pago=metodo,
                referencia=data.get("referencia") or "",
                cierre_caja=cierre_caja,
                medio_pago_obj=medio_pago_obj,
            )
            out = self.get_serializer(carga)
            return Response(out.data, status=status.HTTP_201_CREATED)

        # Pagos por transferencia u otros: quedan PENDIENTE para confirmacion manual
        carga = serializer.save(responsable=self.request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"], url_path="confirmar")
    def confirmar(self, request, pk=None):
        """POST /api/core/cargas-saldo/<id>/confirmar/ — confirma una carga PENDIENTE."""
        carga = self.get_object()
        if carga.estado != CargaSaldo.Estado.PENDIENTE:
            return Response(
                {"error": f"Solo se pueden confirmar cargas PENDIENTE. Estado actual: {carga.estado}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from apps.contabilidad.models import CierreCaja
        cierre_caja = CierreCaja.objects.filter(
            empleado=request.user, estado=CierreCaja.Estado.ABIERTO
        ).select_related("caja").first()
        medio_pago_obj = (
            MedioPago.objects.filter(descripcion__iexact=carga.metodo_pago).first()
            if carga.metodo_pago else None
        )
        carga_confirmada = TarjetaService.confirmar_carga(
            carga=carga,
            responsable=request.user,
            cierre_caja=cierre_caja,
            medio_pago_obj=medio_pago_obj,
        )
        return Response(self.get_serializer(carga_confirmada).data)


class ConsumoTarjetaViewSet(viewsets.ModelViewSet):
    queryset = ConsumoTarjeta.objects.select_related("tarjeta").all()
    serializer_class = ConsumoTarjetaSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tarjeta"]


class MedioPagoViewSet(viewsets.ModelViewSet):
    queryset = MedioPago.objects.all()
    serializer_class = MedioPagoSerializer
    permission_classes = [IsAdminOrReadOnly]

    def list(self, request, *args, **kwargs):
        cache_key = f"medios_pago_list_{request.query_params.urlencode()}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, _CACHE_TTL_LONG)
        return response

    def perform_create(self, serializer):
        super().perform_create(serializer)
        _invalidar_cache_core("medios_pago_list_")

    def perform_update(self, serializer):
        super().perform_update(serializer)
        _invalidar_cache_core("medios_pago_list_")

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        _invalidar_cache_core("medios_pago_list_")


class LimiteTransaccionViewSet(viewsets.ModelViewSet):
    queryset = LimiteTransaccion.objects.select_related("rol").all()
    serializer_class = LimiteTransaccionSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["rol", "tipo_operacion", "activo"]


class RegistroAutorizacionViewSet(viewsets.ModelViewSet):
    queryset = RegistroAutorizacion.objects.select_related("solicitante", "autorizador").all()
    serializer_class = RegistroAutorizacionSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo_operacion"]


class ReporteTarjetasView(APIView):
    """
    GET /api/core/reporte-tarjetas/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
    Saldo actual, recargas y consumos por tarjeta/alumno.
    Sin desde/hasta: solo saldos actuales sin movimientos del período.
    Opcional: ?formato=csv
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        import csv as csv_mod
        from django.db.models import Sum, Count, Q
        from django.http import HttpResponse as HR

        desde = request.query_params.get("desde")
        hasta = request.query_params.get("hasta")

        recarga_filter = Q(movimientos__tipo=MovimientoTarjeta.Tipo.RECARGA)
        consumo_filter = Q(movimientos__tipo=MovimientoTarjeta.Tipo.CONSUMO)
        if desde and hasta:
            date_q = Q(movimientos__fecha__date__gte=desde, movimientos__fecha__date__lte=hasta)
            recarga_filter &= date_q
            consumo_filter &= date_q

        from django.db.models import DecimalField, IntegerField
        from django.db.models.functions import Coalesce
        from django.db.models import Value

        tarjetas_qs = (
            Tarjeta.objects
            .select_related("hijo", "hijo__grado")
            .filter(estado=Tarjeta.Estado.ACTIVA)
            .annotate(
                total_recargado=Coalesce(
                    Sum("movimientos__monto", filter=recarga_filter),
                    Value(0), output_field=DecimalField(max_digits=12, decimal_places=0)
                ),
                total_consumido=Coalesce(
                    Sum("movimientos__monto", filter=consumo_filter),
                    Value(0), output_field=DecimalField(max_digits=12, decimal_places=0)
                ),
                num_recargas=Count("movimientos__id", filter=recarga_filter),
                num_consumos=Count("movimientos__id", filter=consumo_filter),
            )
            .order_by("hijo__apellido", "hijo__nombre")
        )

        filas = []
        for t in tarjetas_qs:
            filas.append({
                "nro_tarjeta": t.nro_tarjeta,
                "alumno": str(t.hijo),
                "grado": str(t.hijo.grado) if t.hijo.grado else "",
                "saldo_actual": int(t.saldo_actual),
                "total_recargado": int(t.total_recargado or 0),
                "total_consumido": int(t.total_consumido or 0),
                "num_recargas": t.num_recargas or 0,
                "num_consumos": t.num_consumos or 0,
            })

        total_saldo = sum(f["saldo_actual"] for f in filas)
        total_recargado = sum(f["total_recargado"] for f in filas)
        total_consumido = sum(f["total_consumido"] for f in filas)

        if request.query_params.get("formato") == "csv":
            periodo = f"_{desde}_{hasta}" if desde and hasta else ""
            response = HR(content_type="text/csv; charset=utf-8-sig")
            response["Content-Disposition"] = f'attachment; filename="reporte_tarjetas{periodo}.csv"'
            writer = csv_mod.writer(response)
            writer.writerow(["REPORTE DE TARJETAS PREPAGO"])
            if desde and hasta:
                writer.writerow([f"Período: {desde} al {hasta}"])
            writer.writerow([])
            writer.writerow(["Nro Tarjeta", "Alumno", "Grado", "Saldo Actual (Gs)", "Recargado (Gs)", "Consumido (Gs)", "Nro Recargas", "Nro Consumos"])
            for f in filas:
                writer.writerow([
                    f["nro_tarjeta"], f["alumno"], f["grado"],
                    f["saldo_actual"], f["total_recargado"], f["total_consumido"],
                    f["num_recargas"], f["num_consumos"],
                ])
            writer.writerow([])
            writer.writerow(["TOTALES", "", "", total_saldo, total_recargado, total_consumido, "", ""])
            return response

        return Response({
            "periodo": {"desde": desde, "hasta": hasta},
            "resumen": {
                "total_tarjetas": len(filas),
                "saldo_total": total_saldo,
                "total_recargado": total_recargado,
                "total_consumido": total_consumido,
            },
            "tarjetas": filas,
        })