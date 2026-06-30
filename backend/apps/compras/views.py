"""
Views para la app compras
"""

from django.db import models, transaction
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from common.permissions import IsCajeroOrAdmin, IsStaffUser
from common.mixins import ExportCSVMixin
from .filters import CompraFilter

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Proveedor,
    CuentaCorrienteProveedor,
    Compra,
    DetalleCompra,
    PagoProveedor,
    AplicacionPagoCompra,
    NotaCreditoProveedor,
    DetalleNotaCreditoProveedor,
    OrdenCompra,
    ProductoProveedor,
)
from .services import CompraService
from .serializers import (
    ProveedorSerializer,
    CuentaCorrienteProveedorSerializer,
    CompraSerializer,
    CompraWriteSerializer,
    DetalleCompraSerializer,
    PagoProveedorSerializer,
    PagoProveedorWriteSerializer,
    AplicacionPagoCompraSerializer,
    NotaCreditoProveedorSerializer,
    DetalleNotaCreditoProveedorSerializer,
    OrdenCompraSerializer,
    ProductoProveedorSerializer,
)


class ProveedorViewSet(ExportCSVMixin, viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["activo"]
    search_fields = ["ruc", "razon_social"]
    ordering_fields = ["razon_social", "ruc"]
    ordering = ["razon_social"]
    export_filename = "proveedores"
    export_fields = [
        ("RUC", "ruc"),
        ("Razón Social", "razon_social"),
        ("Teléfono", "telefono"),
        ("Email", "email"),
        ("Activo", "activo"),
    ]


class CuentaCorrienteProveedorViewSet(viewsets.ModelViewSet):
    queryset = CuentaCorrienteProveedor.objects.select_related("proveedor").all()
    serializer_class = CuentaCorrienteProveedorSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["proveedor", "tipo"]


class CompraViewSet(ExportCSVMixin, viewsets.ModelViewSet):
    serializer_class = CompraSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CompraFilter
    search_fields = ["proveedor__razon_social", "nro_factura_proveedor"]
    ordering_fields = ["fecha", "monto_total"]
    ordering = ["-fecha"]
    export_filename = "compras"
    export_fields = [
        ("Fecha", lambda o: str(o.fecha)[:10]),
        ("Proveedor", "proveedor__razon_social"),
        ("Nro. Factura", "nro_factura_proveedor"),
        ("Monto Total", "monto_total"),
        ("Estado Pago", "estado_pago"),
    ]

    def get_queryset(self):
        return (
            Compra.objects
            .select_related("proveedor")
            .prefetch_related("detalles")
            .annotate(
                _total_pagado=Coalesce(
                    Sum("aplicaciones_pago__monto_aplicado"),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=0)),
                )
            )
        )

    def _resolve_items(self, items_data):
        from apps.productos.models import Producto
        resolved = []
        for item in items_data:
            producto = Producto.objects.get(pk=item["producto"])
            resolved.append({
                "producto": producto,
                "cantidad": item["cantidad"],
                "costo_unitario": item["costo_unitario"],
            })
        return resolved

    def create(self, request, *args, **kwargs):
        write_ser = CompraWriteSerializer(data=request.data)
        write_ser.is_valid(raise_exception=True)
        data = write_ser.validated_data
        try:
            proveedor = Proveedor.objects.get(pk=data["proveedor"])
        except Proveedor.DoesNotExist:
            return Response({"proveedor": ["Proveedor no encontrado."]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            items = self._resolve_items(data["items"])
            compra = CompraService.registrar_compra(
                proveedor=proveedor,
                creado_por=request.user,
                tipo_pago=data["tipo_pago"],
                items=items,
                nro_factura_proveedor=data.get("nro_factura_proveedor", ""),
                observaciones=data.get("observaciones", ""),
            )
        except ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        compra_data = self.get_queryset().get(pk=compra.pk)
        return Response(CompraSerializer(compra_data).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        write_ser = CompraWriteSerializer(data=request.data, partial=partial)
        write_ser.is_valid(raise_exception=True)
        data = write_ser.validated_data
        try:
            proveedor = Proveedor.objects.get(pk=data["proveedor"])
        except Proveedor.DoesNotExist:
            return Response({"proveedor": ["Proveedor no encontrado."]}, status=status.HTTP_400_BAD_REQUEST)
        from decimal import Decimal
        from apps.productos.models import Producto as ProdModel
        items = self._resolve_items(data.get("items", []))
        instance.proveedor = proveedor
        instance.tipo_pago = data.get("tipo_pago", instance.tipo_pago)
        instance.nro_factura_proveedor = data.get("nro_factura_proveedor", instance.nro_factura_proveedor)
        instance.observaciones = data.get("observaciones", instance.observaciones)
        if items:
            instance.detalles.all().delete()
            monto_total = Decimal("0")
            for item in items:
                subtotal = item["cantidad"] * item["costo_unitario"]
                monto_total += subtotal
                DetalleCompra.objects.create(
                    compra=instance,
                    producto=item["producto"],
                    cantidad=item["cantidad"],
                    costo_unitario=item["costo_unitario"],
                    subtotal=subtotal,
                )
            instance.monto_total = monto_total
        instance.save()
        compra_data = self.get_queryset().get(pk=instance.pk)
        return Response(CompraSerializer(compra_data).data)

    @action(detail=True, methods=["post"], url_path="confirmar-entrega")
    def confirmar_entrega(self, request, pk=None):
        """Confirma la recepción de mercadería de una compra a crédito pendiente."""
        compra = self.get_object()
        if compra.tipo_pago != Compra.TipoPago.CREDITO:
            return Response(
                {"error": "Solo se pueden confirmar entregas de compras a crédito."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            compra = CompraService.confirmar_compra(compra=compra, autorizado_por=request.user)
        except ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        return Response(CompraSerializer(compra).data)


class DetalleCompraViewSet(viewsets.ModelViewSet):
    queryset = DetalleCompra.objects.select_related("compra", "producto").order_by("-compra__fecha", "-id")
    serializer_class = DetalleCompraSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["producto", "compra"]
    ordering_fields = ["compra__fecha"]


class PagoProveedorViewSet(viewsets.ModelViewSet):
    queryset = PagoProveedor.objects.select_related("proveedor", "medio_pago").prefetch_related("aplicaciones").all()
    serializer_class = PagoProveedorSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["proveedor", "estado", "medio_pago"]

    def create(self, request, *args, **kwargs):
        from decimal import Decimal
        from apps.core.models import MedioPago
        write_ser = PagoProveedorWriteSerializer(data=request.data)
        write_ser.is_valid(raise_exception=True)
        data = write_ser.validated_data
        try:
            compra = Compra.objects.get(pk=data["compra"])
        except Compra.DoesNotExist:
            return Response({"compra": ["Compra no encontrada."]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            medio_pago = MedioPago.objects.get(pk=data["medio_pago"])
        except MedioPago.DoesNotExist:
            return Response({"medio_pago": ["Medio de pago no encontrado."]}, status=status.HTTP_400_BAD_REQUEST)
        monto = Decimal(str(data["monto"]))
        with transaction.atomic():
            pago = PagoProveedor.objects.create(
                proveedor=compra.proveedor,
                monto_total=monto,
                medio_pago=medio_pago,
                observaciones=data.get("observaciones") or "",
                creado_por=request.user,
                estado=PagoProveedor.Estado.CONCILIADO,
            )
            AplicacionPagoCompra.objects.create(
                pago=pago,
                compra=compra,
                monto_aplicado=monto,
            )
            # Recalcular estado_pago de la compra
            total_pagado = AplicacionPagoCompra.objects.filter(compra=compra).aggregate(
                total=models.Sum("monto_aplicado")
            )["total"] or Decimal("0")
            if total_pagado >= compra.monto_total:
                compra.estado_pago = "PAGADO"
            elif total_pagado > 0:
                compra.estado_pago = "PARCIAL"
            compra.save(update_fields=["estado_pago"])
        return Response(PagoProveedorSerializer(pago).data, status=status.HTTP_201_CREATED)


class AplicacionPagoCompraViewSet(viewsets.ModelViewSet):
    queryset = AplicacionPagoCompra.objects.select_related("pago", "compra").all()
    serializer_class = AplicacionPagoCompraSerializer
    permission_classes = [IsCajeroOrAdmin]


class NotaCreditoProveedorViewSet(viewsets.ModelViewSet):
    queryset = NotaCreditoProveedor.objects.select_related("proveedor").prefetch_related("detalles").all()
    serializer_class = NotaCreditoProveedorSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["proveedor", "estado"]


class DetalleNotaCreditoProveedorViewSet(viewsets.ModelViewSet):
    queryset = DetalleNotaCreditoProveedor.objects.select_related("nota_credito", "producto").all()
    serializer_class = DetalleNotaCreditoProveedorSerializer
    permission_classes = [IsCajeroOrAdmin]


class ProductoProveedorViewSet(viewsets.ModelViewSet):
    queryset = ProductoProveedor.objects.select_related("proveedor", "producto").all()
    serializer_class = ProductoProveedorSerializer
    permission_classes = [IsStaffUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["proveedor", "producto"]
    search_fields = ["producto__descripcion"]
    ordering_fields = ["producto__descripcion", "precio_compra", "fecha_ultima_compra"]
    ordering = ["producto__descripcion"]


class OrdenCompraViewSet(viewsets.ModelViewSet):
    serializer_class = OrdenCompraSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["estado", "tipo_pago", "proveedor"]
    search_fields = ["proveedor__razon_social", "nro_factura_esperada"]
    ordering_fields = ["fecha_creacion", "monto_total"]
    ordering = ["-fecha_creacion"]

    def get_queryset(self):
        return (
            OrdenCompra.objects
            .select_related("proveedor", "creado_por", "aprobado_por")
            .prefetch_related("detalles__producto")
        )

    def _require_approver(self, request):
        """Sólo ADMIN y SUPERVISOR pueden aprobar/rechazar/convertir."""
        rol = getattr(request.user, "rol", None)
        if rol not in ("ADMIN", "SUPERVISOR"):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Solo ADMIN o SUPERVISOR pueden realizar esta acción.")

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """Envía la OC a revisión: BORRADOR → PENDIENTE."""
        orden = self.get_object()
        if orden.estado != OrdenCompra.Estado.BORRADOR:
            return Response(
                {"error": "Solo se puede enviar a revisión una OC en estado Borrador."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not orden.detalles.exists():
            return Response(
                {"error": "La OC debe tener al menos un producto."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        orden.estado = OrdenCompra.Estado.PENDIENTE
        orden.save(update_fields=["estado", "fecha_actualizacion"])
        return Response(OrdenCompraSerializer(orden).data)

    @action(detail=True, methods=["post"])
    def aprobar(self, request, pk=None):
        """Aprueba la OC: PENDIENTE → APROBADA."""
        self._require_approver(request)
        orden = self.get_object()
        if orden.estado != OrdenCompra.Estado.PENDIENTE:
            return Response(
                {"error": "Solo se puede aprobar una OC en estado Pendiente."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from django.utils import timezone
        orden.estado = OrdenCompra.Estado.APROBADA
        orden.aprobado_por = request.user
        orden.fecha_aprobacion = timezone.now()
        orden.motivo_rechazo = None
        orden.save(update_fields=["estado", "aprobado_por", "fecha_aprobacion", "motivo_rechazo", "fecha_actualizacion"])
        return Response(OrdenCompraSerializer(orden).data)

    @action(detail=True, methods=["post"])
    def rechazar(self, request, pk=None):
        """Rechaza la OC: PENDIENTE → RECHAZADA."""
        self._require_approver(request)
        orden = self.get_object()
        if orden.estado != OrdenCompra.Estado.PENDIENTE:
            return Response(
                {"error": "Solo se puede rechazar una OC en estado Pendiente."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        motivo = request.data.get("motivo", "").strip()
        if not motivo:
            return Response({"error": "Debe indicar el motivo del rechazo."}, status=status.HTTP_400_BAD_REQUEST)
        orden.estado = OrdenCompra.Estado.RECHAZADA
        orden.motivo_rechazo = motivo
        orden.save(update_fields=["estado", "motivo_rechazo", "fecha_actualizacion"])
        return Response(OrdenCompraSerializer(orden).data)

    @action(detail=True, methods=["post"])
    def convertir(self, request, pk=None):
        """Convierte la OC aprobada en una Compra real: APROBADA → CONVERTIDA."""
        self._require_approver(request)
        orden = self.get_object()
        if orden.estado != OrdenCompra.Estado.APROBADA:
            return Response(
                {"error": "Solo se puede convertir una OC en estado Aprobada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        items = [
            {
                "producto": det.producto,
                "cantidad": det.cantidad,
                "costo_unitario": det.costo_unitario,
            }
            for det in orden.detalles.select_related("producto").all()
        ]
        try:
            compra = CompraService.registrar_compra(
                proveedor=orden.proveedor,
                creado_por=request.user,
                tipo_pago=orden.tipo_pago,
                items=items,
                nro_factura_proveedor=orden.nro_factura_esperada or "",
                observaciones=orden.observaciones or "",
            )
        except ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

        orden.estado = OrdenCompra.Estado.CONVERTIDA
        orden.compra_generada = compra
        orden.save(update_fields=["estado", "compra_generada", "fecha_actualizacion"])
        return Response({
            "orden": OrdenCompraSerializer(orden).data,
            "compra_id": compra.pk,
        })
