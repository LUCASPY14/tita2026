"""
Views para la app core
"""

from django.core.cache import cache

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response

from common.pagination import CursorResultsSetPagination
from common.permissions import IsAdminOrReadOnly, IsCajeroOrAdmin, IsStaffOrClienteWeb, IsStaffUser
from common.throttling import SensitiveEndpointThrottle
from common.utils.medios_pago import resolver_medio_pago
from apps.usuarios.auditoria import registrar_auditoria

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
    CargaSaldo,
    MedioPago,
)
from .serializers import (
    TarjetaSerializer,
    MovimientoTarjetaSerializer,
    CargaSaldoSerializer,
    MedioPagoSerializer,
)
from .services import TarjetaService


class TarjetaViewSet(viewsets.ModelViewSet):
    queryset = Tarjeta.objects.select_related(
        "hijo__grado",
        "hijo__cliente_responsable__lista_precio",
        "cliente_directo__lista_precio",
    ).prefetch_related("hijo__restricciones").all()
    serializer_class = TarjetaSerializer
    permission_classes = [IsStaffOrClienteWeb]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado"]
    search_fields = [
        "nro_tarjeta",
        "hijo__nombre", "hijo__apellido",
        "cliente_directo__nombres", "cliente_directo__apellidos", "cliente_directo__razon_social",
    ]
    ordering = ["nro_tarjeta"]

    def _cambiar_estado(self, request, pk, desde, hacia, operacion):
        tarjeta = self.get_object()
        if tarjeta.estado != desde:
            return Response(
                {"error": f"Solo se puede pasar de {desde} a {hacia}. Estado actual: {tarjeta.estado}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tarjeta.estado = hacia
        tarjeta.save(update_fields=["estado"])
        registrar_auditoria(
            request=request,
            operacion=operacion,
            tabla="core_tarjeta",
            id_registro=None,
            descripcion=f"Tarjeta {tarjeta.nro_tarjeta}: {desde} → {hacia}",
        )
        return Response(self.get_serializer(tarjeta).data)

    @action(detail=True, methods=["post"], url_path="bloquear", throttle_classes=[SensitiveEndpointThrottle])
    def bloquear(self, request, pk=None):
        """Solo se puede bloquear una tarjeta ACTIVA — VENCIDA/CANCELADA no vuelven atrás por acá."""
        return self._cambiar_estado(request, pk, Tarjeta.Estado.ACTIVA, Tarjeta.Estado.BLOQUEADA, "BLOQUEAR_TARJETA")

    @action(detail=True, methods=["post"], url_path="activar", throttle_classes=[SensitiveEndpointThrottle])
    def activar(self, request, pk=None):
        """Solo se puede reactivar una tarjeta BLOQUEADA."""
        return self._cambiar_estado(request, pk, Tarjeta.Estado.BLOQUEADA, Tarjeta.Estado.ACTIVA, "ACTIVAR_TARJETA")


class MovimientoTarjetaViewSet(viewsets.ModelViewSet):
    queryset = MovimientoTarjeta.objects.select_related("tarjeta").all()
    serializer_class = MovimientoTarjetaSerializer
    permission_classes = [IsStaffOrClienteWeb]
    pagination_class = CursorResultsSetPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["tarjeta", "tipo"]
    ordering = ["-fecha"]


METODOS_CONFIRMACION_INMEDIATA = ("EFECTIVO", "POS DEBITO", "POS CREDITO")


class CargaSaldoViewSet(viewsets.ModelViewSet):
    queryset = CargaSaldo.objects.select_related("tarjeta", "cliente_origen", "responsable").all()
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
            from django.db import transaction as _tx
            from apps.contabilidad.models import CierreCaja
            cierre_caja = CierreCaja.objects.filter(
                empleado=request.user, estado=CierreCaja.Estado.ABIERTO
            ).select_related("caja").first()
            medio_pago_obj = resolver_medio_pago(metodo)
            nro_factura = (request.data.get("nro_factura") or "").strip()

            with _tx.atomic():
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
                if nro_factura:
                    from apps.contabilidad.services import FacturacionService
                    FacturacionService.emitir_para_origen(
                        tipo="CARGA_SALDO",
                        origen_id=carga.id,
                        nro_factura=nro_factura,
                    )
            registrar_auditoria(
                request=request,
                operacion="RECARGA_SALDO",
                tabla="core_cargasaldo",
                id_registro=carga.id,
                descripcion=(
                    f"Recarga {data['monto_cargado']} Gs. en tarjeta"
                    f" {data['tarjeta'].nro_tarjeta} vía {metodo}"
                ),
            )
            out = self.get_serializer(carga)
            return Response(out.data, status=status.HTTP_201_CREATED)

        if metodo == "CUENTA_CORRIENTE":
            from apps.clientes.models import CuentaCorrienteCliente
            tarjeta_obj = data["tarjeta"]
            tarjeta_obj = Tarjeta.objects.select_related(
                "hijo__cliente_responsable"
            ).get(pk=tarjeta_obj.pk)
            cliente = tarjeta_obj.hijo.cliente_responsable

            carga = TarjetaService.cargar_saldo(
                tarjeta=tarjeta_obj,
                monto=data["monto_cargado"],
                cliente_origen=cliente,
                responsable=request.user,
                metodo_pago=metodo,
                referencia=data.get("referencia") or "",
            )

            CuentaCorrienteCliente.objects.create(
                cliente=cliente,
                tipo=CuentaCorrienteCliente.Tipo.DEBITO,
                monto=data["monto_cargado"],
                descripcion=(
                    f"Recarga tarjeta {tarjeta_obj.nro_tarjeta}"
                    f" - {tarjeta_obj.hijo.nombre_completo}"
                ),
                creado_por=request.user,
            )

            registrar_auditoria(
                request=request,
                operacion="RECARGA_SALDO",
                tabla="core_cargasaldo",
                id_registro=carga.id,
                descripcion=(
                    f"Recarga {data['monto_cargado']} Gs. en tarjeta"
                    f" {tarjeta_obj.nro_tarjeta} vía CUENTA_CORRIENTE"
                ),
            )
            out = self.get_serializer(carga)
            return Response(out.data, status=status.HTTP_201_CREATED)

        # Pagos por transferencia u otros: quedan PENDIENTE para confirmacion manual
        carga = serializer.save(responsable=self.request.user)
        registrar_auditoria(
            request=request,
            operacion="RECARGA_SALDO_PENDIENTE",
            tabla="core_cargasaldo",
            id_registro=carga.id,
            descripcion=(
                f"Recarga {carga.monto_cargado} Gs. en tarjeta"
                f" {carga.tarjeta_id} vía {metodo} — PENDIENTE confirmación"
            ),
        )
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
        from django.db import transaction
        from apps.contabilidad.models import CierreCaja
        cierre_caja = CierreCaja.objects.filter(
            empleado=request.user, estado=CierreCaja.Estado.ABIERTO
        ).select_related("caja").first()
        medio_pago_obj = resolver_medio_pago(carga.metodo_pago)
        nro_factura = (request.data.get("nro_factura") or "").strip()
        with transaction.atomic():
            carga_confirmada = TarjetaService.confirmar_carga(
                carga=carga,
                responsable=request.user,
                cierre_caja=cierre_caja,
                medio_pago_obj=medio_pago_obj,
            )
            if nro_factura:
                from apps.contabilidad.services import FacturacionService
                FacturacionService.emitir_para_origen(
                    tipo="CARGA_SALDO",
                    origen_id=carga_confirmada.id,
                    nro_factura=nro_factura,
                )
        registrar_auditoria(
            request=request,
            operacion="CONFIRMAR_CARGA",
            tabla="core_cargasaldo",
            id_registro=carga_confirmada.id,
            descripcion=(
                f"Confirmación carga {carga_confirmada.monto_cargado} Gs."
                f" en tarjeta {carga_confirmada.tarjeta_id}"
            ),
        )
        return Response(self.get_serializer(carga_confirmada).data)


class MedioPagoViewSet(viewsets.ModelViewSet):
    queryset = MedioPago.objects.all()
    serializer_class = MedioPagoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["activo"]

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

        from django.db.models import DecimalField
        from django.db.models.functions import Coalesce
        from django.db.models import Value

        tarjetas_qs = (
            Tarjeta.objects
            .select_related("hijo", "hijo__grado", "cliente_directo")
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
            # Una tarjeta es de un alumno (hijo) o de un docente/funcionario
            # (cliente_directo) — nunca ambos (constraint tarjeta_tiene_titular).
            titular = str(t.hijo) if t.hijo_id else str(t.cliente_directo) if t.cliente_directo_id else "—"
            filas.append({
                "nro_tarjeta": t.nro_tarjeta,
                "alumno": titular,
                "grado": str(t.hijo.grado) if t.hijo_id and t.hijo.grado else "",
                "saldo_actual": int(t.saldo_actual),
                "total_recargado": int(t.total_recargado or 0),
                "total_consumido": int(t.total_consumido or 0),
                "num_recargas": t.num_recargas or 0,
                "num_consumos": t.num_consumos or 0,
            })

        total_saldo = sum(f["saldo_actual"] for f in filas)
        total_recargado = sum(f["total_recargado"] for f in filas)
        total_consumido = sum(f["total_consumido"] for f in filas)

        fmt = request.query_params.get("formato")

        if fmt == "pdf":
            from common.pdf_report import pdf_response
            def fmt_gs(n):
                return f"{int(n):,} Gs.".replace(",", ".")
            subtitle = f"Período: {desde} al {hasta}" if desde and hasta else "Saldos actuales"
            rows = [
                [f["nro_tarjeta"], f["alumno"], f["grado"] or "—",
                 fmt_gs(f["saldo_actual"]), fmt_gs(f["total_recargado"]),
                 fmt_gs(f["total_consumido"]), f["num_recargas"], f["num_consumos"]]
                for f in filas
            ]
            periodo_fn = f"_{desde}_{hasta}" if desde and hasta else ""
            headers = [
                "Tarjeta", "Alumno", "Grado", "Saldo Actual",
                "Recargado", "Consumido", "Recargas", "Consumos",
            ]
            totals = [
                "TOTALES", "", "", fmt_gs(total_saldo),
                fmt_gs(total_recargado), fmt_gs(total_consumido), "", "",
            ]
            return pdf_response(
                filename=f"reporte_tarjetas{periodo_fn}.pdf",
                title="Reporte de Tarjetas Prepago",
                subtitle=subtitle,
                headers=headers,
                rows=rows,
                totals=totals,
                landscape=True,
            )

        if fmt == "csv":
            periodo = f"_{desde}_{hasta}" if desde and hasta else ""
            response = HR(content_type="text/csv; charset=utf-8-sig")
            response["Content-Disposition"] = f'attachment; filename="reporte_tarjetas{periodo}.csv"'
            writer = csv_mod.writer(response)
            writer.writerow(["REPORTE DE TARJETAS PREPAGO"])
            if desde and hasta:
                writer.writerow([f"Período: {desde} al {hasta}"])
            writer.writerow([])
            writer.writerow([
                "Nro Tarjeta", "Alumno", "Grado",
                "Saldo Actual (Gs)", "Recargado (Gs)", "Consumido (Gs)",
                "Nro Recargas", "Nro Consumos",
            ])
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
