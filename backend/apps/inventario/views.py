"""
Views para la app inventario
"""

from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdmin, IsStaffUser

from django_filters.rest_framework import DjangoFilterBackend

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


class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.select_related("producto").all()
    serializer_class = StockSerializer

    search_fields = ["producto__descripcion", "producto__codigo_barra"]


class MovimientoStockViewSet(viewsets.ModelViewSet):
    queryset = MovimientoStock.objects.select_related("producto").all()
    serializer_class = MovimientoStockSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto", "tipo", "motivo"]


class AjusteInventarioViewSet(viewsets.ModelViewSet):
    queryset = AjusteInventario.objects.select_related("solicitado_por").prefetch_related("detalles").all()
    serializer_class = AjusteInventarioSerializer
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

            for detalle in ajuste.detalles.select_related("producto").all():
                stock, _ = Stock.objects.get_or_create(
                    producto=detalle.producto,
                    defaults={"cantidad": Decimal("0")},
                )
                stock = Stock.objects.select_for_update().get(pk=stock.pk)
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



class CostoHistoricoViewSet(viewsets.ModelViewSet):
    queryset = CostoHistorico.objects.select_related("producto").all()
    serializer_class = CostoHistoricoSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto"]


class AlertaStockViewSet(viewsets.ModelViewSet):
    queryset = AlertaStock.objects.select_related("producto").all()
    serializer_class = AlertaStockSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto", "tipo", "activa"]


class LoteProductoViewSet(viewsets.ModelViewSet):
    queryset = LoteProducto.objects.select_related("producto").all()
    serializer_class = LoteProductoSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto", "bloqueado"]


class AlertaVencimientoViewSet(viewsets.ModelViewSet):
    queryset = AlertaVencimiento.objects.select_related("lote").all()
    serializer_class = AlertaVencimientoSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["lote", "tipo"]


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
                "stock_actual": float(s.cantidad),
                "stock_minimo": float(s.producto.stock_minimo),
                "diferencia": float(s.cantidad - s.producto.stock_minimo),
                "dias_stock": s.dias_stock_disponible,
            })

        return Response({
            "total": len(filas),
            "productos": filas,
        })