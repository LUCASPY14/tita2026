"""
Views para la app contabilidad
"""

import csv
from datetime import timedelta

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdmin, IsCajeroOrAdmin, IsStaffUser

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Caja,
    CierreCaja,
    MovimientoCaja,
    ConciliacionPago,
    Factura,
    DatosEmpresa,
)
from .serializers import (
    CajaSerializer,
    CierreCajaSerializer,
    CerrarCajaSerializer,
    MovimientoCajaSerializer,
    ConciliacionPagoSerializer,
    FacturaSerializer,
    DatosEmpresaSerializer,
    EmitirFacturaSerializer,
    PendienteItemSerializer,
)
from .services import FacturacionService


class CajaViewSet(viewsets.ModelViewSet):
    queryset = Caja.objects.all()
    serializer_class = CajaSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre", "descripcion"]
    ordering_fields = ["nombre", "id"]
    ordering = ["nombre"]


class CierreCajaViewSet(viewsets.ModelViewSet):
    queryset = CierreCaja.objects.select_related("caja", "empleado").all()
    serializer_class = CierreCajaSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["caja", "estado"]

    @action(detail=True, methods=["post"], url_path="conciliar")
    def conciliar(self, request, pk=None):
        """Marca un cierre de caja como CONCILIADO. Solo aplica a cierres CERRADOS."""
        cierre = self.get_object()
        if cierre.estado != CierreCaja.Estado.CERRADO:
            return Response(
                {"error": f"Solo se pueden conciliar cierres en estado CERRADO. Estado actual: {cierre.estado}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cierre.estado = CierreCaja.Estado.CONCILIADO
        cierre.observaciones_conciliacion = request.data.get("observaciones", "") or ""
        cierre.save(update_fields=["estado", "observaciones_conciliacion"])
        return Response(CierreCajaSerializer(cierre).data)

    @action(detail=True, methods=["post"], url_path="cerrar")
    def cerrar(self, request, pk=None):
        """Cierra una caja abierta registrando el monto contado físicamente."""
        cierre = self.get_object()
        if cierre.estado != CierreCaja.Estado.ABIERTO:
            return Response(
                {"error": "La caja ya está cerrada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CerrarCajaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        monto_contado = serializer.validated_data["monto_contado_fisico"]

        from django.db.models import Sum as DSum
        ingresos = (
            MovimientoCaja.objects.filter(cierre=cierre, tipo=MovimientoCaja.Tipo.INGRESO)
            .aggregate(total=DSum("monto"))["total"] or 0
        )
        egresos = (
            MovimientoCaja.objects.filter(cierre=cierre, tipo=MovimientoCaja.Tipo.EGRESO)
            .aggregate(total=DSum("monto"))["total"] or 0
        )
        monto_esperado = cierre.monto_inicial + ingresos - egresos

        cierre.monto_contado_fisico = monto_contado
        cierre.diferencia_efectivo = monto_contado - monto_esperado
        cierre.fecha_cierre = timezone.now()
        cierre.estado = CierreCaja.Estado.CERRADO
        cierre.save()

        return Response(CierreCajaSerializer(cierre).data)

    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        """Retorna HTML imprimible del cierre de caja (el navegador exporta a PDF)."""
        cierre = self.get_object()

        from django.db.models import Sum as DSum
        movimientos = MovimientoCaja.objects.filter(cierre=cierre).select_related("medio_pago")
        ingresos = movimientos.filter(tipo=MovimientoCaja.Tipo.INGRESO).aggregate(
            total=DSum("monto")
        )["total"] or 0
        egresos = movimientos.filter(tipo=MovimientoCaja.Tipo.EGRESO).aggregate(
            total=DSum("monto")
        )["total"] or 0

        empresa = None
        try:
            empresa = DatosEmpresa.objects.first()
        except Exception:
            pass

        html = render_to_string("contabilidad/cierre_print.html", {
            "cierre": cierre,
            "movimientos": movimientos,
            "ingresos": int(ingresos),
            "egresos": int(egresos),
            "empresa": empresa,
        })
        return HttpResponse(html, content_type="text/html; charset=utf-8")


class MovimientoCajaViewSet(viewsets.ModelViewSet):
    queryset = MovimientoCaja.objects.select_related("cierre", "medio_pago").all()
    serializer_class = MovimientoCajaSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["cierre", "tipo", "medio_pago"]


class ConciliacionPagoViewSet(viewsets.ModelViewSet):
    queryset = ConciliacionPago.objects.select_related("pago_venta").all()
    serializer_class = ConciliacionPagoSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["estado"]


class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.select_related("cliente", "venta").all()
    serializer_class = FacturaSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["estado", "cliente"]

    def create(self, request, *args, **kwargs):
        """POST directo a /facturas/ debe usar el endpoint /facturas/emitir/."""
        return Response(
            {"detail": "Use POST /facturas/emitir/ para emitir una factura."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=False, methods=["get"], url_path="pendiente-facturar")
    def pendiente_facturar(self, request):
        """Lista cargas de saldo y pagos de almuerzo sin factura emitida."""
        data = FacturacionService.get_pendientes()

        items = []
        for c in data["cargas"]:
            nombre = ""
            if c.cliente_origen:
                nombre = c.cliente_origen.nombre_completo
            elif c.tarjeta and c.tarjeta.hijo:
                nombre = c.tarjeta.hijo.nombre_completo
            items.append({
                "tipo": "CARGA_SALDO",
                "id": c.pk,
                "cliente_nombre": nombre,
                "descripcion": f"Carga de saldo tarjeta {c.tarjeta_id or '-'}",
                "monto": int(c.monto_cargado),
                "fecha": c.fecha_carga,
            })

        for p in data["pagos"]:
            cuenta = p.cuenta
            items.append({
                "tipo": "PAGO_ALMUERZO",
                "id": p.pk,
                "cliente_nombre": cuenta.hijo.cliente_responsable.nombre_completo,
                "descripcion": f"Pago almuerzo {cuenta.hijo.nombre_completo} — {cuenta.mes}/{cuenta.anio}",
                "monto": int(p.monto),
                "fecha": p.fecha_pago,
            })

        items.sort(key=lambda x: x["fecha"], reverse=True)
        serializer = PendienteItemSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="emitir")
    def emitir(self, request):
        """Emite una factura para una carga de saldo o pago de almuerzo."""
        serializer = EmitirFacturaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        factura = FacturacionService.emitir_para_origen(
            tipo=serializer.validated_data["tipo"],
            origen_id=serializer.validated_data["origen_id"],
            nro_factura=serializer.validated_data["nro_factura"],
        )
        return Response(FacturaSerializer(factura).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="anular")
    def anular(self, request, pk=None):
        """Anula una factura emitida."""
        factura = self.get_object()
        factura = FacturacionService.anular_factura(factura)
        return Response(FacturaSerializer(factura).data)

    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        """Retorna HTML imprimible de la factura (el navegador exporta a PDF)."""
        factura = self.get_object()

        # Determinar el concepto según el origen de la factura
        concepto = "Servicios"
        if hasattr(factura, "carga_saldo") and factura.carga_saldo:
            carga = factura.carga_saldo
            concepto = f"Carga de saldo tarjeta {carga.tarjeta_id}"
        elif hasattr(factura, "pago_cuenta_almuerzo") and factura.pago_cuenta_almuerzo:
            pago = factura.pago_cuenta_almuerzo
            cuenta = pago.cuenta
            concepto = (
                f"Pago almuerzo — {cuenta.hijo.nombre_completo} "
                f"({cuenta.mes}/{cuenta.anio})"
            )

        empresa = None
        try:
            empresa = DatosEmpresa.objects.first()
        except Exception:
            pass

        html = render_to_string("contabilidad/factura_print.html", {
            "factura": factura,
            "concepto": concepto,
            "empresa": empresa,
        })
        return HttpResponse(html, content_type="text/html; charset=utf-8")


class DatosEmpresaViewSet(viewsets.ModelViewSet):
    queryset = DatosEmpresa.objects.all()
    serializer_class = DatosEmpresaSerializer
    permission_classes = [IsAdmin]


class ReportePeriodoView(APIView):
    """
    GET /api/contabilidad/reportes/?fecha_desde=YYYY-MM-DD&fecha_hasta=YYYY-MM-DD
    Retorna resumen de ventas y cierres de caja para el período.
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        from django.db.models import Count, Sum
        from apps.ventas.models import Venta

        fecha_desde = request.query_params.get("fecha_desde")
        fecha_hasta = request.query_params.get("fecha_hasta")

        if not fecha_desde or not fecha_hasta:
            return Response(
                {"error": "Se requieren los parámetros fecha_desde y fecha_hasta (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ventas_qs = Venta.objects.filter(
            fecha__date__gte=fecha_desde,
            fecha__date__lte=fecha_hasta,
            estado=Venta.Estado.ACTIVA,
        )
        ventas_agg = ventas_qs.aggregate(
            cantidad=Count("id"),
            monto_total=Sum("monto_total"),
        )

        ventas_por_tipo = list(
            ventas_qs.values("tipo").annotate(
                cantidad=Count("id"),
                monto=Sum("monto_total"),
            )
        )

        cierres_qs = CierreCaja.objects.filter(
            fecha_apertura__date__gte=fecha_desde,
            fecha_apertura__date__lte=fecha_hasta,
            estado=CierreCaja.Estado.CERRADO,
        ).select_related("caja")

        cierres_data = []
        for c in cierres_qs:
            cierres_data.append({
                "id": c.pk,
                "caja": c.caja.nombre if c.caja else "-",
                "fecha_apertura": c.fecha_apertura,
                "fecha_cierre": c.fecha_cierre,
                "monto_inicial": int(c.monto_inicial),
                "monto_contado_fisico": int(c.monto_contado_fisico or 0),
                "diferencia": int(c.diferencia_efectivo or 0),
            })

        data = {
            "periodo": {"desde": fecha_desde, "hasta": fecha_hasta},
            "ventas": {
                "cantidad": ventas_agg["cantidad"] or 0,
                "monto_total": int(ventas_agg["monto_total"] or 0),
                "por_tipo": ventas_por_tipo,
            },
            "cierres_caja": cierres_data,
        }

        if request.query_params.get("formato") == "csv":
            return self._exportar_csv(data, fecha_desde, fecha_hasta)

        return Response(data)

    def _exportar_csv(self, data, fecha_desde, fecha_hasta):
        response = HttpResponse(
            content_type="text/csv; charset=utf-8-sig",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="reporte_{fecha_desde}_{fecha_hasta}.csv"'
        )
        writer = csv.writer(response)

        writer.writerow(["REPORTE DE VENTAS", f"{fecha_desde} al {fecha_hasta}"])
        writer.writerow([])
        writer.writerow(["Resumen de Ventas"])
        writer.writerow(["Cantidad total", data["ventas"]["cantidad"]])
        writer.writerow(["Monto total (Gs)", data["ventas"]["monto_total"]])
        writer.writerow([])

        writer.writerow(["Tipo", "Cantidad", "Monto (Gs)"])
        for row in data["ventas"]["por_tipo"]:
            writer.writerow([row["tipo"], row["cantidad"], int(row.get("monto") or 0)])
        writer.writerow([])

        writer.writerow(["CIERRES DE CAJA"])
        writer.writerow(["Caja", "Apertura", "Cierre", "Monto Inicial", "Contado", "Diferencia"])
        for c in data["cierres_caja"]:
            writer.writerow([
                c["caja"], c["fecha_apertura"], c["fecha_cierre"],
                c["monto_inicial"], c["monto_contado_fisico"], c["diferencia"],
            ])

        return response


class DashboardResumenView(APIView):
    """
    GET /api/contabilidad/dashboard/
    Retorna un resumen del día para el panel de control.
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        from django.db.models import Count, Sum
        from apps.ventas.models import Venta
        from apps.clientes.models import Cliente
        from apps.productos.models import Producto
        from apps.inventario.models import AlertaStock

        hoy = timezone.now().date()

        ventas_hoy = Venta.objects.filter(
            fecha__date=hoy,
            estado=Venta.Estado.ACTIVA,
        ).aggregate(
            cantidad=Count("id"),
            monto=Sum("monto_total"),
        )

        clientes_total = Cliente.objects.filter(activo=True).count()
        productos_total = Producto.objects.filter(activo=True).count()
        stock_bajo = AlertaStock.objects.filter(activa=True).count()

        cajas_abiertas = CierreCaja.objects.filter(
            estado=CierreCaja.Estado.ABIERTO
        ).count()

        return Response({
            "ventasHoy": ventas_hoy["cantidad"] or 0,
            "montoHoy": int(ventas_hoy["monto"] or 0),
            "clientes": clientes_total,
            "productos": productos_total,
            "stockBajo": stock_bajo,
            "cajasAbiertas": cajas_abiertas,
        })


class DashboardTendenciaView(APIView):
    """
    GET /api/contabilidad/dashboard/tendencia/?dias=7
    Ventas diarias de los últimos N días (máx 90) para el gráfico de tendencia.
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        from django.db.models import Count, Sum
        from django.db.models.functions import TruncDate
        from apps.ventas.models import Venta

        dias = min(max(int(request.query_params.get("dias", 7)), 1), 90)
        hasta = timezone.now().date()
        desde = hasta - timedelta(days=dias - 1)

        ventas_qs = (
            Venta.objects
            .filter(fecha__date__gte=desde, fecha__date__lte=hasta, estado=Venta.Estado.ACTIVA)
            .annotate(dia=TruncDate("fecha"))
            .values("dia")
            .annotate(cantidad=Count("id"), monto=Sum("monto_total"))
            .order_by("dia")
        )

        dias_map = {v["dia"]: v for v in ventas_qs}
        resultado = []
        current = desde
        while current <= hasta:
            v = dias_map.get(current)
            resultado.append({
                "fecha": current.isoformat(),
                "cantidad": v["cantidad"] if v else 0,
                "monto": int(v["monto"] or 0) if v else 0,
            })
            current += timedelta(days=1)

        return Response({
            "dias": dias,
            "desde": desde.isoformat(),
            "hasta": hasta.isoformat(),
            "data": resultado,
        })