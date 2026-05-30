"""
Views para la app inventario
"""

from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdmin, IsStaffUser
from common.mixins import ExportCSVMixin

from django_filters.rest_framework import DjangoFilterBackend
from .filters import MovimientoStockFilter, AlertaStockFilter, LoteProductoFilter, AlertaVencimientoFilter

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
    queryset = AlertaStock.objects.select_related("producto").all()
    serializer_class = AlertaStockSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AlertaStockFilter
    search_fields = ["producto__descripcion"]
    ordering_fields = ["id"]
    ordering = ["-id"]


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
    queryset = AlertaVencimiento.objects.select_related("lote").all()
    serializer_class = AlertaVencimientoSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AlertaVencimientoFilter
    search_fields = ["lote__numero_lote", "lote__producto__descripcion"]
    ordering_fields = ["id"]
    ordering = ["-id"]


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