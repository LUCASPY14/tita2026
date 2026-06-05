"""
Views para la app ventas
"""

import csv

from django.db import models, transaction
from django.http import HttpResponse

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsCajeroOrAdmin, IsAdmin, IsStaffUser
from .filters import VentaFilter

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .services import VentaService

from .models import (
    Venta,
    DetalleVenta,
    PagoVenta,
    AplicacionPago,
    NotaCredito,
    DetalleNotaCredito,
    CondicionVenta,
)
from .serializers import (
    VentaSerializer,
    DetalleVentaSerializer,
    PagoVentaSerializer,
    AplicacionPagoSerializer,
    NotaCreditoSerializer,
    DetalleNotaCreditoSerializer,
    CondicionVentaSerializer,
)


class VentaViewSet(viewsets.ModelViewSet):
    serializer_class = VentaSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = VentaFilter
    search_fields = ["cliente__nombres", "cliente__apellidos", "cliente__ruc_ci"]
    ordering_fields = ["fecha", "monto_total"]
    ordering = ["-fecha"]

    def get_queryset(self):
        from django.db.models import DecimalField, Sum, Value
        from django.db.models.functions import Coalesce
        return (
            Venta.objects
            .select_related("cliente", "cajero")
            .prefetch_related("detalles")
            .annotate(
                _total_pagado=Coalesce(
                    Sum("aplicaciones_pago__monto_aplicado"),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=0)),
                )
            )
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Pre-save: verificar alérgenos antes de crear la venta
        advertencias = []
        hijo = serializer.validated_data.get("hijo")
        if hijo:
            from apps.almuerzos.validators import verificar_alergenos_venta
            from apps.productos.models import Producto
            items = request.data.get("items", [])
            ids = [i.get("producto") for i in items if i.get("producto")]
            productos = list(Producto.objects.filter(pk__in=ids))
            advertencias = verificar_alergenos_venta(hijo, productos)

        venta = self._registrar(serializer)
        headers = self.get_success_headers(serializer.data)

        resp_data = VentaSerializer(venta).data
        if advertencias:
            resp_data = dict(resp_data)
            resp_data["advertencias_alergenos"] = advertencias
        return Response(resp_data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"], url_path="anular", permission_classes=[IsAdmin])
    def anular(self, request, pk=None):
        """Anula una venta activa revirtiendo stock, tarjeta y cuenta corriente."""
        venta = self.get_object()
        try:
            venta = VentaService.anular_venta(venta, anulado_por=request.user)
        except Exception as e:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            if hasattr(e, "detail"):
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(VentaSerializer(venta).data)

    def _registrar(self, serializer):
        from decimal import Decimal
        from apps.productos.models import Producto

        data = serializer.validated_data
        raw_items = self.request.data.get("items", [])

        # Resolver IDs de producto a objetos Django (el servicio los necesita como modelos)
        product_ids = [i.get("producto") for i in raw_items if i.get("producto")]
        productos_map = {p.pk: p for p in Producto.objects.filter(pk__in=product_ids)}

        items = []
        for raw in raw_items:
            producto = productos_map.get(raw.get("producto"))
            if not producto:
                continue
            items.append({
                "producto": producto,
                "cantidad": Decimal(str(raw.get("cantidad", 1))),
                "precio_unitario": Decimal(str(raw.get("precio_unitario", 0))),
                "iva_10": Decimal(str(raw.get("iva_10", 0))),
                "iva_5": Decimal(str(raw.get("iva_5", 0))),
                "monto_exenta": Decimal(str(raw.get("monto_exenta", 0))),
            })

        return VentaService.registrar_venta(
            cliente=data.get("cliente"),
            cajero=self.request.user,
            tipo=data.get("tipo", "CONTADO"),
            medio_pago=data.get("medio_pago"),
            tarjeta=data.get("tarjeta"),
            hijo=data.get("hijo"),
            items=items,
        )

class DetalleVentaViewSet(viewsets.ModelViewSet):
    queryset = DetalleVenta.objects.select_related("venta", "producto").all()
    serializer_class = DetalleVentaSerializer
    permission_classes = [IsCajeroOrAdmin]


class PagoVentaViewSet(viewsets.ModelViewSet):
    queryset = PagoVenta.objects.select_related("cliente", "venta", "medio_pago").all()
    serializer_class = PagoVentaSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["estado", "medio_pago", "cliente", "venta"]

    _ESTADOS_FINALES = (PagoVenta.Estado.CONCILIADO, PagoVenta.Estado.ANULADO)

    def perform_update(self, serializer):
        if serializer.instance.estado in self._ESTADOS_FINALES:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError(
                f"No se puede modificar un pago en estado {serializer.instance.estado}."
            )
        serializer.save()

    def perform_destroy(self, instance):
        if instance.estado in self._ESTADOS_FINALES:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError(
                f"No se puede eliminar un pago en estado {instance.estado}."
            )
        super().perform_destroy(instance)


class AplicacionPagoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AplicacionPago.objects.select_related("pago", "venta").all()
    serializer_class = AplicacionPagoSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["pago", "venta"]


class NotaCreditoViewSet(viewsets.ModelViewSet):
    queryset = NotaCredito.objects.select_related("cliente", "empleado_autoriza").prefetch_related("detalles").all()
    serializer_class = NotaCreditoSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["estado", "cliente"]


class DetalleNotaCreditoViewSet(viewsets.ModelViewSet):
    queryset = DetalleNotaCredito.objects.select_related("nota_credito", "producto").all()
    serializer_class = DetalleNotaCreditoSerializer
    permission_classes = [IsCajeroOrAdmin]


class CondicionVentaViewSet(viewsets.ModelViewSet):
    queryset = CondicionVenta.objects.all()
    serializer_class = CondicionVentaSerializer
    permission_classes = [IsCajeroOrAdmin]


class ReporteVentasProductoView(APIView):
    """
    GET /api/ventas/reporte-productos/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
    Retorna resumen de ventas agrupado por producto para el período.
    Opcional: ?formato=csv
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        from django.db.models import Count, Sum
        desde = request.query_params.get("desde")
        hasta = request.query_params.get("hasta")

        if not desde or not hasta:
            return Response(
                {"error": "Se requieren los parámetros desde y hasta (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = (
            DetalleVenta.objects
            .filter(
                venta__fecha__date__gte=desde,
                venta__fecha__date__lte=hasta,
                venta__estado=Venta.Estado.ACTIVA,
            )
            .values("producto__id", "producto__descripcion", "producto__categoria__nombre")
            .annotate(
                total_cantidad=Sum("cantidad"),
                total_monto=Sum("subtotal"),
                num_ventas=Count("venta", distinct=True),
            )
            .order_by("-total_monto")
        )

        filas = [
            {
                "producto_id": r["producto__id"],
                "descripcion": r["producto__descripcion"],
                "categoria": r["producto__categoria__nombre"] or "",
                "total_cantidad": r["total_cantidad"] or 0,
                "total_monto": int(r["total_monto"] or 0),
                "num_ventas": r["num_ventas"],
            }
            for r in qs
        ]

        total_general = sum(f["total_monto"] for f in filas)

        if request.query_params.get("formato") == "csv":
            return self._exportar_csv(filas, desde, hasta, total_general)

        return Response({
            "periodo": {"desde": desde, "hasta": hasta},
            "total_monto": total_general,
            "productos": filas,
        })

    def _exportar_csv(self, filas, desde, hasta, total_general):
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = (
            f'attachment; filename="ventas_producto_{desde}_{hasta}.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(["REPORTE DE VENTAS POR PRODUCTO", f"{desde} al {hasta}"])
        writer.writerow([])
        writer.writerow(["Producto", "Categoría", "Cantidad Vendida", "N° Ventas", "Total (Gs)"])
        for f in filas:
            writer.writerow([f["descripcion"], f["categoria"], f["total_cantidad"], f["num_ventas"], f["total_monto"]])
        writer.writerow([])
        writer.writerow(["TOTAL GENERAL", "", "", "", total_general])
        return response