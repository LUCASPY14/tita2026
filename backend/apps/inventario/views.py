"""
Views para la app inventario
"""

from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import CursorResultsSetPagination
from common.permissions import IsAdmin, IsStaffUser
from common.mixins import ExportCSVMixin

from django_filters.rest_framework import DjangoFilterBackend
from .filters import MovimientoStockFilter, LoteProductoFilter, AlertaVencimientoFilter

from .models import (
    Stock,
    MovimientoStock,
    AjusteInventario,
    DetalleAjuste,
    CostoHistorico,
    AlertaStock,
    LoteProducto,
    AlertaVencimiento,
)
from .serializers import (
    StockSerializer,
    MovimientoStockSerializer,
    AjusteInventarioSerializer,
    DetalleAjusteSerializer,
    CostoHistoricoSerializer,
    AlertaStockSerializer,
    LoteProductoSerializer,
    AlertaVencimientoSerializer,
)


class StockViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Stock.objects.select_related("producto").all()
    serializer_class = StockSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["producto__descripcion", "producto__codigo_barra"]
    ordering_fields = ["cantidad", "fecha_actualizacion"]
    ordering = ["-fecha_actualizacion"]


class MovimientoStockViewSet(ExportCSVMixin, viewsets.ReadOnlyModelViewSet):
    queryset = MovimientoStock.objects.select_related("producto").all()
    serializer_class = MovimientoStockSerializer
    permission_classes = [IsStaffUser]
    pagination_class = CursorResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MovimientoStockFilter
    search_fields = ["producto__descripcion", "observaciones"]
    ordering_fields = ["fecha", "cantidad"]
    ordering = ["-fecha"]
    export_filename = "movimientos_stock"
    export_fields = [
        ("Fecha", lambda o: str(o.fecha)[:19]),
        ("Producto", "producto__descripcion"),
        ("Tipo", "tipo"),
        ("Motivo", "motivo"),
        ("Cantidad", "cantidad"),
        ("Stock Resultante", "stock_resultante"),
        ("Observaciones", "observaciones"),
    ]


class AjusteInventarioViewSet(viewsets.ModelViewSet):
    queryset = AjusteInventario.objects.select_related("solicitado_por").prefetch_related("detalles").all()
    serializer_class = AjusteInventarioSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo", "estado"]

    def create(self, request, *args, **kwargs):
        from apps.productos.models import Producto
        from rest_framework.exceptions import ValidationError as DRFValidationError

        detalles_raw = request.data.get("detalles", [])
        if not detalles_raw:
            raise DRFValidationError({"detalles": "Debe incluir al menos un producto."})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            ajuste = AjusteInventario.objects.create(
                tipo=serializer.validated_data["tipo"],
                motivo=serializer.validated_data.get("motivo", ""),
                solicitado_por=request.user,
                estado=AjusteInventario.Estado.PENDIENTE,
            )
            for item in detalles_raw:
                try:
                    producto = Producto.objects.get(pk=item["producto"])
                except (Producto.DoesNotExist, KeyError):
                    raise DRFValidationError({"detalles": f"Producto {item.get('producto')} no encontrado."})
                DetalleAjuste.objects.create(
                    ajuste=ajuste,
                    producto=producto,
                    cantidad=Decimal(str(item.get("cantidad", 1))),
                )

        headers = self.get_success_headers(serializer.data)
        return Response(AjusteInventarioSerializer(ajuste).data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"], url_path="aprobar", permission_classes=[IsAdmin])
    def aprobar(self, request, pk=None):
        """Aprueba un ajuste PENDIENTE y aplica los cambios de stock."""
        ajuste = self.get_object()
        if ajuste.estado != AjusteInventario.Estado.PENDIENTE:
            return Response(
                {"error": f"Solo se pueden aprobar ajustes PENDIENTES. Estado actual: {ajuste.estado}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            ajuste = AjusteInventario.objects.select_for_update().get(pk=ajuste.pk)
            if ajuste.estado != AjusteInventario.Estado.PENDIENTE:
                return Response({"error": "El ajuste ya fue procesado."}, status=status.HTTP_400_BAD_REQUEST)

            es_ingreso = ajuste.tipo == AjusteInventario.TipoAjuste.AUMENTO
            tipo_mov = MovimientoStock.Tipo.INGRESO if es_ingreso else MovimientoStock.Tipo.EGRESO
            motivo_mov = MovimientoStock.Motivo.AJUSTE_AUMENTO if es_ingreso else MovimientoStock.Motivo.AJUSTE_MERMA

            # Paso 1: bloquear todos los stocks y validar disponibilidad para MERMA.
            # Se hace antes de modificar cualquier fila para un rechazo limpio.
            detalles_con_stock = []
            for detalle in ajuste.detalles.select_related("producto").all():
                stock, _ = Stock.objects.get_or_create(
                    producto=detalle.producto,
                    defaults={"cantidad": Decimal("0")},
                )
                stock = Stock.objects.select_for_update().get(pk=stock.pk)

                if not es_ingreso and not detalle.producto.permite_stock_negativo:
                    if stock.cantidad < detalle.cantidad:
                        return Response(
                            {
                                "error": f"Stock insuficiente para {detalle.producto.descripcion}.",
                                "disponible": str(stock.cantidad),
                                "requerido": str(detalle.cantidad),
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                detalles_con_stock.append((detalle, stock))

            # Paso 2: aplicar todos los cambios (validaciones ya superadas).
            for detalle, stock in detalles_con_stock:
                if es_ingreso:
                    stock.cantidad += detalle.cantidad
                else:
                    stock.cantidad -= detalle.cantidad
                stock.save()

                movimiento = MovimientoStock.objects.create(
                    producto=detalle.producto,
                    tipo=tipo_mov,
                    motivo=motivo_mov,
                    cantidad=detalle.cantidad,
                    stock_resultante=stock.cantidad,
                    ajuste=ajuste,
                    autorizado_por=request.user,
                    observaciones=f"Ajuste #{ajuste.pk} — {ajuste.motivo}",
                )
                detalle.movimiento_stock = movimiento
                detalle.save(update_fields=["movimiento_stock"])

            ajuste.estado = AjusteInventario.Estado.APROBADO
            ajuste.aprobado_por = request.user
            ajuste.fecha_aprobacion = timezone.now()
            ajuste.save(update_fields=["estado", "aprobado_por", "fecha_aprobacion"])

        return Response(AjusteInventarioSerializer(ajuste).data)

    @action(detail=True, methods=["post"], url_path="rechazar", permission_classes=[IsAdmin])
    def rechazar(self, request, pk=None):
        """Rechaza un ajuste PENDIENTE sin modificar stock."""
        ajuste = self.get_object()
        if ajuste.estado != AjusteInventario.Estado.PENDIENTE:
            return Response(
                {"error": f"Solo se pueden rechazar ajustes PENDIENTES. Estado actual: {ajuste.estado}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ajuste.estado = AjusteInventario.Estado.RECHAZADO
        ajuste.aprobado_por = request.user
        ajuste.fecha_aprobacion = timezone.now()
        ajuste.save(update_fields=["estado", "aprobado_por", "fecha_aprobacion"])
        return Response(AjusteInventarioSerializer(ajuste).data)


class DetalleAjusteViewSet(viewsets.ModelViewSet):
    queryset = DetalleAjuste.objects.select_related("ajuste", "producto").all()
    serializer_class = DetalleAjusteSerializer
    permission_classes = [IsStaffUser]


class CostoHistoricoViewSet(viewsets.ModelViewSet):
    queryset = CostoHistorico.objects.select_related("producto").all()
    serializer_class = CostoHistoricoSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto"]


class AlertaStockViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Calcula alertas de stock en tiempo real desde la tabla Stock,
    sin depender de que la tarea Celery haya corrido.
    """
    serializer_class = AlertaStockSerializer
    permission_classes = [IsStaffUser]

    def get_queryset(self):
        stocks = (
            Stock.objects
            .select_related("producto")
            .filter(
                producto__stock_minimo__gt=0,
                producto__requiere_stock=True,
                cantidad__lte=models.F("producto__stock_minimo"),
            )
        )
        search = self.request.query_params.get("search")
        if search:
            stocks = stocks.filter(producto__descripcion__icontains=search)

        # Construimos AlertaStock virtuales (sin guardar en BD)
        alertas = []
        for s in stocks:
            minimo = s.producto.stock_minimo
            if s.cantidad <= 0:
                tipo = AlertaStock.TipoAlerta.STOCK_CERO
            elif minimo and s.cantidad <= minimo * Decimal("0.5"):
                tipo = AlertaStock.TipoAlerta.STOCK_CRITICO
            else:
                tipo = AlertaStock.TipoAlerta.STOCK_MINIMO

            alerta = AlertaStock(
                producto=s.producto,
                tipo=tipo,
                stock_actual=s.cantidad,
                stock_minimo=minimo,
                activa=True,
                fecha_generada=timezone.now(),
            )
            alertas.append(alerta)
        return alertas

    def list(self, request, *args, **kwargs):
        alertas = self.get_queryset()
        data = [
            {
                "id": i + 1,
                "producto": a.producto_id,
                "producto_nombre": a.producto.descripcion,
                "tipo": a.tipo,
                "stock_actual": str(a.stock_actual),
                "stock_minimo": str(a.stock_minimo),
                "activa": True,
                "notificacion_enviada": False,
                "fecha_generada": a.fecha_generada.isoformat(),
                "fecha_resuelta": None,
            }
            for i, a in enumerate(alertas)
        ]
        return Response({"count": len(data), "results": data})


class LoteProductoViewSet(viewsets.ModelViewSet):
    queryset = LoteProducto.objects.select_related("producto").all()
    serializer_class = LoteProductoSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = LoteProductoFilter
    search_fields = ["producto__descripcion", "numero_lote"]
    ordering_fields = ["fecha_vencimiento", "fecha_creacion"]
    ordering = ["fecha_vencimiento"]


class AlertaVencimientoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AlertaVencimiento.objects.select_related("lote__producto").all()
    serializer_class = AlertaVencimientoSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AlertaVencimientoFilter
    search_fields = ["lote__numero_lote", "lote__producto__descripcion"]
    ordering_fields = ["id"]
    ordering = ["-id"]

    @action(detail=True, methods=["post"], url_path="registrar-accion")
    def registrar_accion(self, request, pk=None):
        """Registra la acción tomada sobre un lote próximo a vencer o vencido."""
        alerta = self.get_object()
        accion = request.data.get("accion_tomada")
        opciones_validas = AlertaVencimiento.Accion.values
        if accion not in opciones_validas:
            return Response(
                {"detail": f"Acción inválida. Opciones: {opciones_validas}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        alerta.accion_tomada = accion
        alerta.fecha_accion = timezone.now()
        alerta.responsable = request.user
        alerta.save(update_fields=["accion_tomada", "fecha_accion", "responsable"])
        return Response(AlertaVencimientoSerializer(alerta).data)


class ReporteStockView(APIView):
    """
    GET /api/inventario/reporte-stock/
    Inventario completo: stock actual, costo promedio, valor y alertas.
    Opcional: ?solo_activos=1 (default) ?formato=csv
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        from datetime import timedelta
        from django.db.models import Sum

        solo_activos = request.query_params.get("solo_activos", "1") != "0"

        qs = (
            Stock.objects
            .select_related("producto", "producto__categoria", "producto__unidad_medida")
            .prefetch_related("producto__costos_historicos")
            .filter(producto__activo=solo_activos)
            .order_by("producto__descripcion")
        )

        # Anotar ventas de los últimos 30 días para calcular días de stock
        hace_30_dias = timezone.now() - timedelta(days=30)
        ventas_mes_map = dict(
            MovimientoStock.objects
            .filter(tipo=MovimientoStock.Tipo.EGRESO, fecha__gte=hace_30_dias)
            .values("producto_id")
            .annotate(total=Sum("cantidad"))
            .values_list("producto_id", "total")
        )

        filas = []
        for s in qs:
            costos = list(s.producto.costos_historicos.all())
            total_monto = sum(c.costo_unitario * c.cantidad_comprada for c in costos)
            total_cant = sum(c.cantidad_comprada for c in costos)
            costo_prom = int(total_monto / total_cant) if total_cant else 0
            valor_inv = int(float(s.cantidad) * costo_prom)

            ventas_mes = ventas_mes_map.get(s.producto_id, Decimal("0"))
            if ventas_mes and ventas_mes > 0:
                venta_diaria = float(ventas_mes) / 30
                dias_stock = int(float(s.cantidad) / venta_diaria) if venta_diaria > 0 else None
            else:
                dias_stock = None

            filas.append({
                "producto_id": s.producto_id,
                "descripcion": s.producto.descripcion,
                "categoria": s.producto.categoria.nombre if s.producto.categoria else "",
                "unidad": s.producto.unidad_medida.nombre if s.producto.unidad_medida else "",
                "stock_actual": float(s.cantidad),
                "stock_minimo": float(s.producto.stock_minimo),
                "requiere_reposicion": bool(s.requiere_reposicion),
                "costo_promedio": costo_prom,
                "valor_inventario": valor_inv,
                "dias_stock": dias_stock,
            })

        total_valor = sum(f["valor_inventario"] for f in filas)
        productos_bajo_minimo = sum(1 for f in filas if f["requiere_reposicion"])

        fmt = request.query_params.get("formato")
        if fmt == "csv":
            return self._exportar_csv(filas, total_valor)
        if fmt == "pdf":
            return self._exportar_pdf(filas, total_valor, productos_bajo_minimo)

        return Response({
            "resumen": {
                "total_productos": len(filas),
                "productos_bajo_minimo": productos_bajo_minimo,
                "valor_total_inventario": total_valor,
            },
            "productos": filas,
        })

    def _exportar_pdf(self, filas, total_valor, productos_bajo_minimo):
        from common.pdf_report import pdf_response
        from datetime import date
        def fmt_gs(n):
            return f"{int(n):,} Gs.".replace(",", ".")
        rows = [
            [
                f["descripcion"],
                f["categoria"] or "—",
                f["unidad"] or "—",
                f["stock_actual"],
                f["stock_minimo"],
                "⚠ Bajo" if f["requiere_reposicion"] else "OK",
                fmt_gs(f["costo_promedio"]),
                fmt_gs(f["valor_inventario"]),
                f"{f['dias_stock']}d" if f["dias_stock"] is not None else "—",
            ]
            for f in filas
        ]
        return pdf_response(
            filename=f"reporte_stock_{date.today()}.pdf",
            title="Reporte de Inventario / Stock",
            subtitle=f"Total: {len(filas)} productos | {productos_bajo_minimo} bajo mínimo",
            headers=[
                "Producto", "Categoría", "Unidad", "Stock", "Mínimo",
                "Estado", "Costo Prom.", "Valor Inv.", "Días Stock",
            ],
            rows=rows,
            totals=["TOTAL", "", "", "", "", "", "", fmt_gs(total_valor), ""],
            landscape=True,
        )

    def _exportar_csv(self, filas, total_valor):
        import csv as csv_mod
        from django.http import HttpResponse as HR
        response = HR(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = 'attachment; filename="reporte_stock.csv"'
        writer = csv_mod.writer(response)
        writer.writerow(["REPORTE DE INVENTARIO / STOCK"])
        writer.writerow([])
        writer.writerow([
            "Producto", "Categoría", "Unidad", "Stock Actual", "Stock Mínimo",
            "Estado", "Costo Prom. (Gs)", "Valor Inv. (Gs)", "Días Stock"
        ])
        for f in filas:
            estado = "BAJO MÍNIMO" if f["requiere_reposicion"] else "OK"
            writer.writerow([
                f["descripcion"], f["categoria"], f["unidad"],
                f["stock_actual"], f["stock_minimo"], estado,
                f["costo_promedio"], f["valor_inventario"],
                f["dias_stock"] if f["dias_stock"] is not None else "—",
            ])
        writer.writerow([])
        writer.writerow(["VALOR TOTAL INVENTARIO", "", "", "", "", "", "", total_valor, ""])
        return response


class StockCriticoView(APIView):
    """
    GET /api/inventario/stock-critico/
    Retorna productos cuyo stock actual es <= stock_minimo del producto.
    Opcional: ?sin_stock=1 para solo los que tienen stock=0.
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        solo_sin_stock = request.query_params.get("sin_stock") == "1"

        qs = (
            Stock.objects
            .select_related("producto", "producto__categoria", "producto__unidad_medida")
            .filter(
                producto__activo=True,
                producto__requiere_stock=True,
                cantidad__lte=models.F("producto__stock_minimo"),
            )
            .order_by("cantidad")
        )

        if solo_sin_stock:
            qs = qs.filter(cantidad__lte=0)

        filas = []
        for s in qs:
            filas.append({
                "producto_id": s.producto_id,
                "descripcion": s.producto.descripcion,
                "categoria": s.producto.categoria.nombre if s.producto.categoria else None,
                "stock_actual": s.cantidad,
                "stock_minimo": s.producto.stock_minimo,
                "diferencia": s.cantidad - s.producto.stock_minimo,
                "dias_stock": s.dias_stock_disponible,
            })

        return Response({
            "total": len(filas),
            "productos": filas,
        })
