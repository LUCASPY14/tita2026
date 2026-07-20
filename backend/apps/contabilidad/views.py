"""
Views para la app contabilidad
"""

import csv
from datetime import timedelta

from django.http import HttpResponse
from django.template.loader import render_to_string

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from common.object_permissions import CajaOwnerQuerysetMixin, IsCajaOwnerOrAdmin
from common.permissions import IsAdmin, IsCajeroOrAdmin, IsStaffUser, IsStaffOrClienteWeb

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
from .services import CajaService, FacturacionService


class CajaViewSet(viewsets.ModelViewSet):
    queryset = Caja.objects.all()
    serializer_class = CajaSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre", "ubicacion"]
    ordering_fields = ["nombre", "id"]
    ordering = ["nombre"]


class CierreCajaViewSet(CajaOwnerQuerysetMixin, viewsets.ModelViewSet):
    queryset = CierreCaja.objects.select_related("caja", "empleado").all()
    serializer_class = CierreCajaSerializer
    permission_classes = [IsCajeroOrAdmin, IsCajaOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["caja", "estado", "empleado"]
    cajero_field = "empleado"

    @action(detail=False, methods=["get"], url_path="mi-caja")
    def mi_caja(self, request):
        """Retorna el CierreCaja ABIERTO del usuario autenticado, si existe."""
        cierre = CierreCaja.objects.filter(
            empleado=request.user, estado=CierreCaja.Estado.ABIERTO
        ).select_related("caja").first()
        if not cierre:
            return Response(None, status=status.HTTP_200_OK)
        return Response(CierreCajaSerializer(cierre).data)

    def create(self, request, *args, **kwargs):
        """Abre una caja usando CajaService para validar duplicados y asignar el empleado."""
        from decimal import Decimal
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        cierre = CajaService.abrir_caja(
            caja=data["caja"],
            empleado=request.user,
            monto_inicial=data.get("monto_inicial", Decimal("0")),
        )
        out = CierreCajaSerializer(cierre)
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)

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
        from decimal import Decimal
        monto_contado = Decimal(serializer.validated_data["monto_contado_fisico"])

        cierre = CajaService.cerrar_caja(cierre=cierre, monto_contado=monto_contado)
        return Response(CierreCajaSerializer(cierre).data)

    @action(detail=True, methods=["get"], url_path="arqueo")
    def arqueo(self, request, pk=None):
        """
        GET /api/contabilidad/cierres-caja/{id}/arqueo/
        Devuelve el arqueo separado en tres categorías:
          - efectivo: billetes en cajón (medio_pago EFECTIVO)
          - pos:      pagos con terminal POS / transferencia
          - prepago:  ventas con tarjeta RFID (sin medio_pago físico)
        """
        from django.db.models import Sum as DSum, Q
        cierre = self.get_object()

        movs = MovimientoCaja.objects.filter(cierre=cierre).select_related("medio_pago")
        ing = movs.filter(tipo=MovimientoCaja.Tipo.INGRESO)
        egr = movs.filter(tipo=MovimientoCaja.Tipo.EGRESO)

        # ── Totales globales ──────────────────────────────────────────────────
        ingresos_total = int(ing.aggregate(t=DSum("monto"))["t"] or 0)
        egresos_total  = int(egr.aggregate(t=DSum("monto"))["t"] or 0)

        # ── Efectivo (cajón) ──────────────────────────────────────────────────
        efectivo_ingresos = int(
            ing.filter(medio_pago__descripcion__iexact="efectivo")
               .aggregate(t=DSum("monto"))["t"] or 0
        )
        # Egresos EFECTIVO + sin medio_pago (retiros manuales en cash)
        efectivo_egresos = int(
            egr.filter(
                Q(medio_pago__descripcion__iexact="efectivo") | Q(medio_pago__isnull=True)
            ).aggregate(t=DSum("monto"))["t"] or 0
        )
        efectivo_esperado = int(cierre.monto_inicial) + efectivo_ingresos - efectivo_egresos

        # ── POS / Transferencia (no cash) ─────────────────────────────────────
        pos_total = int(
            ing.filter(medio_pago__isnull=False)
               .exclude(medio_pago__descripcion__iexact="efectivo")
               .filter(
                   Q(medio_pago__descripcion__icontains="pos")
                   | Q(medio_pago__descripcion__icontains="tpv")
                   | Q(medio_pago__descripcion__icontains="débito")
                   | Q(medio_pago__descripcion__icontains="debito")
                   | Q(medio_pago__descripcion__icontains="crédito")
                   | Q(medio_pago__descripcion__icontains="credito")
                   | Q(medio_pago__descripcion__icontains="transf")
               )
               .aggregate(t=DSum("monto"))["t"] or 0
        )

        # ── Prepago (tarjeta RFID, sin medio_pago físico) ─────────────────────
        prepago_total = int(
            ing.filter(medio_pago__isnull=True).aggregate(t=DSum("monto"))["t"] or 0
        )

        # ── Agrupado por medio para desglose visual ───────────────────────────
        def agrupar(qs):
            rows = (
                qs.values("medio_pago__descripcion")
                .annotate(total=DSum("monto"))
                .order_by("-total")
            )
            return [
                {"medio": r["medio_pago__descripcion"] or "Tarjeta prepago", "total": int(r["total"] or 0)}
                for r in rows
            ]

        return Response({
            "monto_inicial":      int(cierre.monto_inicial),
            "efectivo_esperado":  efectivo_esperado,
            "efectivo_ingresos":  efectivo_ingresos,
            "efectivo_egresos":   efectivo_egresos,
            "pos_total":          pos_total,
            "prepago_total":      prepago_total,
            "ingresos_total":     ingresos_total,
            "egresos_total":      egresos_total,
            "ingresos_por_medio": agrupar(ing),
            "egresos_por_medio":  agrupar(egr),
        })

    @action(detail=True, methods=["post"], url_path="registrar-movimiento")
    def registrar_movimiento(self, request, pk=None):
        """
        POST /api/contabilidad/cierres-caja/{id}/registrar-movimiento/
        Registra un INGRESO o EGRESO manual en el cierre activo.
        Body: { tipo, monto, medio_pago (id), descripcion }
        """
        from decimal import Decimal
        from apps.core.models import MedioPago

        cierre = self.get_object()
        if cierre.estado != CierreCaja.Estado.ABIERTO:
            return Response(
                {"error": "Solo se pueden registrar movimientos en cajas ABIERTAS."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tipo = request.data.get("tipo", "")
        if tipo not in (MovimientoCaja.Tipo.INGRESO, MovimientoCaja.Tipo.EGRESO):
            return Response({"error": "Tipo debe ser INGRESO o EGRESO."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            monto = Decimal(str(request.data.get("monto", 0)))
        except Exception:
            return Response({"error": "Monto inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if monto <= 0:
            return Response({"error": "El monto debe ser mayor a 0."}, status=status.HTTP_400_BAD_REQUEST)

        medio_pago_id = request.data.get("medio_pago")
        medio_pago = None
        if medio_pago_id:
            try:
                medio_pago = MedioPago.objects.get(pk=medio_pago_id)
            except MedioPago.DoesNotExist:
                return Response({"error": "Medio de pago no encontrado."}, status=status.HTTP_400_BAD_REQUEST)

        descripcion = request.data.get("descripcion", "")

        mov = CajaService.registrar_movimiento(
            cierre=cierre,
            tipo=tipo,
            monto=monto,
            medio_pago=medio_pago,
            descripcion=descripcion,
        )
        return Response(MovimientoCajaSerializer(mov).data, status=status.HTTP_201_CREATED)

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

    @action(detail=True, methods=["get"], url_path="pdf",
            permission_classes=[IsStaffOrClienteWeb])
    def pdf(self, request, pk=None):
        """Retorna HTML imprimible de la factura (el navegador exporta a PDF)."""
        factura = self.get_object()

        # CLIENTE_WEB solo puede ver sus propias facturas
        if request.user.rol == "CLIENTE_WEB":
            cliente = getattr(request.user, "cliente", None)
            if not cliente or factura.cliente_id != cliente.pk:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied()

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
        from django.db.models import Count, Sum, F
        from apps.ventas.models import Venta
        from apps.clientes.models import Cliente
        from apps.productos.models import Producto
        from apps.inventario.models import AlertaStock
        from apps.core.models import CargaSaldo, Tarjeta
        from apps.almuerzos.models import RegistroConsumoAlmuerzo

        from django.utils.timezone import localdate
        hoy = localdate()

        ventas_hoy = Venta.objects.filter(
            fecha__date=hoy,
            estado=Venta.Estado.ACTIVA,
        ).aggregate(cantidad=Count("id"), monto=Sum("monto_total"))

        recargas_hoy = CargaSaldo.objects.filter(
            fecha_carga__date=hoy,
            estado=CargaSaldo.Estado.CONFIRMADA,
        ).aggregate(cantidad=Count("id"), monto=Sum("monto_cargado"))

        almuerzos_hoy = RegistroConsumoAlmuerzo.objects.filter(fecha_consumo=hoy).count()

        tarjetas_alerta = Tarjeta.objects.filter(
            notificar_saldo_bajo=True,
            saldo_alerta__isnull=False,
            saldo_actual__lte=F("saldo_alerta"),
        ).count()

        return Response({
            "ventasHoy":        ventas_hoy["cantidad"] or 0,
            "montoHoy":         int(ventas_hoy["monto"] or 0),
            "clientes":         Cliente.objects.filter(activo=True).count(),
            "productos":        Producto.objects.filter(activo=True).count(),
            "stockBajo":        AlertaStock.objects.filter(activa=True).count(),
            "cajasAbiertas":    CierreCaja.objects.filter(estado=CierreCaja.Estado.ABIERTO).count(),
            "recargasHoy":      recargas_hoy["cantidad"] or 0,
            "montoRecargasHoy": int(recargas_hoy["monto"] or 0),
            "almuerzoHoy":      almuerzos_hoy,
            "tarjetasEnAlerta": tarjetas_alerta,
        })


class DashboardTendenciaView(APIView):
    """
    GET /api/contabilidad/dashboard/tendencia/?dias=7
    GET /api/contabilidad/dashboard/tendencia/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
    Ventas diarias para el gráfico de tendencia.
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        from datetime import date
        from django.db.models import Count, Sum
        from django.db.models.functions import TruncDate
        from apps.ventas.models import Venta

        from django.utils.timezone import localdate

        desde_str = request.query_params.get("desde")
        hasta_str = request.query_params.get("hasta")
        if desde_str and hasta_str:
            try:
                desde = date.fromisoformat(desde_str)
                hasta = date.fromisoformat(hasta_str)
            except ValueError:
                return Response({"error": "Formato de fecha inválido (YYYY-MM-DD)."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            dias = min(max(int(request.query_params.get("dias", 7)), 1), 90)
            hasta = localdate()
            desde = hasta - timedelta(days=dias - 1)

        dias = (hasta - desde).days + 1

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


class ReporteDiferenciasCajaView(APIView):
    """
    GET /api/contabilidad/reporte-diferencias-caja/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
    Diferencias de caja por período: tendencia y resumen por empleado.
    Opcional: ?formato=csv
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        from decimal import Decimal
        from django.db.models import Count, Sum, Max, Min, Avg

        desde = request.query_params.get("desde")
        hasta = request.query_params.get("hasta")

        if not desde or not hasta:
            return Response(
                {"error": "Se requieren los parámetros desde y hasta (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cierres = (
            CierreCaja.objects
            .filter(
                estado=CierreCaja.Estado.CERRADO,
                fecha_cierre__date__gte=desde,
                fecha_cierre__date__lte=hasta,
                diferencia_efectivo__isnull=False,
            )
            .select_related("empleado", "caja")
            .order_by("fecha_cierre")
        )

        # Tendencia: cada cierre como punto en el tiempo
        tendencia = [
            {
                "fecha": c.fecha_cierre.strftime("%Y-%m-%d"),
                "diferencia": int(c.diferencia_efectivo),
                "empleado": f"{c.empleado.nombre} {c.empleado.apellido}".strip() if c.empleado else "",
                "caja": c.caja.nombre if c.caja else "",
                "cierre_id": c.pk,
            }
            for c in cierres
        ]

        # Resumen por empleado
        por_empleado_qs = (
            CierreCaja.objects
            .filter(
                estado=CierreCaja.Estado.CERRADO,
                fecha_cierre__date__gte=desde,
                fecha_cierre__date__lte=hasta,
                diferencia_efectivo__isnull=False,
            )
            .values("empleado__id", "empleado__nombre", "empleado__apellido")
            .annotate(
                n_cierres=Count("id"),
                diferencia_total=Sum("diferencia_efectivo"),
                diferencia_promedio=Avg("diferencia_efectivo"),
                mayor_diferencia=Max("diferencia_efectivo"),
            )
            .order_by("-diferencia_total")
        )

        por_empleado = [
            {
                "empleado_id": r["empleado__id"],
                "empleado": f"{r['empleado__nombre'] or ''} {r['empleado__apellido'] or ''}".strip(),
                "n_cierres": r["n_cierres"],
                "diferencia_total": int(r["diferencia_total"] or 0),
                "diferencia_promedio": int(r["diferencia_promedio"] or 0),
                "mayor_diferencia": int(r["mayor_diferencia"] or 0),
            }
            for r in por_empleado_qs
        ]

        total_diferencia = sum(r["diferencia_total"] for r in por_empleado)
        n_negativos = sum(1 for t in tendencia if t["diferencia"] < 0)
        n_positivos = sum(1 for t in tendencia if t["diferencia"] > 0)
        n_cero = sum(1 for t in tendencia if t["diferencia"] == 0)

        if request.query_params.get("formato") == "csv":
            response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
            response["Content-Disposition"] = (
                f'attachment; filename="diferencias_caja_{desde}_{hasta}.csv"'
            )
            writer = csv.writer(response)
            writer.writerow(["DIFERENCIAS DE CAJA", f"{desde} al {hasta}"])
            writer.writerow([])
            writer.writerow(["Resumen por Empleado"])
            writer.writerow(["Empleado", "N° Cierres", "Diferencia Total (Gs)", "Promedio (Gs)", "Mayor (Gs)"])
            for r in por_empleado:
                writer.writerow([r["empleado"], r["n_cierres"], r["diferencia_total"],
                                  r["diferencia_promedio"], r["mayor_diferencia"]])
            writer.writerow([])
            writer.writerow(["Detalle Cronológico"])
            writer.writerow(["Fecha", "Caja", "Empleado", "Diferencia (Gs)"])
            for t in tendencia:
                writer.writerow([t["fecha"], t["caja"], t["empleado"], t["diferencia"]])
            return response

        return Response({
            "periodo": {"desde": desde, "hasta": hasta},
            "resumen": {
                "total_diferencia": total_diferencia,
                "n_cierres": len(tendencia),
                "n_positivos": n_positivos,
                "n_negativos": n_negativos,
                "n_cero": n_cero,
            },
            "por_empleado": por_empleado,
            "tendencia": tendencia,
        })
