from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import CanManageCompras, IsAdminOrReadOnly

from .models import Compras, DetallesCompra, NotasCreditoProveedor, PagosProveedores, Proveedores
from .serializers import (
    ComprasSerializer,
    DetallesCompraSerializer,
    NotasCreditoProveedorSerializer,
    PagosProveedoresSerializer,
    ProveedoresSerializer,
)
from .services import CompraService


class ProveedoresViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar proveedores.

    Incluye acciones para obtener cuenta corriente.
    """

    queryset = Proveedores.objects.all()
    serializer_class = ProveedoresSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado", "ciudad"]
    search_fields = ["razon_social", "ruc", "email"]
    ordering_fields = ["razon_social"]
    ordering = ["razon_social"]

    @action(detail=True, methods=["get"])
    def cuenta_corriente(self, request, pk=None):
        """
        Obtiene el estado de cuenta corriente con el proveedor.

        GET /api/proveedores/{id}/cuenta_corriente/

        Returns:
            - total_compras: Monto total de compras
            - total_pagado: Monto total pagado
            - saldo_pendiente: Saldo por pagar
            - compras_pendientes: Lista de facturas pendientes
        """
        proveedor = self.get_object()

        cuenta = CompraService.obtener_cuenta_corriente_proveedor(id_proveedor=proveedor.id_proveedor)

        # Agregar info del proveedor
        cuenta["proveedor"] = {
            "id": proveedor.id_proveedor,
            "razon_social": proveedor.razon_social,
            "ruc": proveedor.ruc,
        }

        return Response(cuenta)


class ComprasViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar compras.

    Incluye validaciones automáticas y acciones personalizadas para:
    - Confirmar compras
    - Obtener compras pendientes
    - Calcular totales
    """

    queryset = Compras.objects.all()
    serializer_class = ComprasSerializer
    permission_classes = [IsAuthenticated, CanManageCompras]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado_pago", "id_proveedor"]
    search_fields = ["nro_factura", "id_proveedor__razon_social"]
    ordering_fields = ["fecha", "monto_total"]
    ordering = ["-fecha"]

    def perform_create(self, serializer):
        """
        Valida la compra antes de crearla y crea los detalles.
        """
        from decimal import Decimal

        # Obtener detalles del request
        detalles = self.request.data.get("detalles", [])

        if detalles:
            # Validar compra
            validacion = CompraService.validar_compra(detalles)

            if not validacion["valido"]:
                raise ValidationError(
                    {
                        "error": "La compra contiene errores",
                        "errores": validacion["errores"],
                        "warnings": validacion["warnings"],
                    }
                )

            # Calcular totales
            totales = CompraService.calcular_totales_compra(detalles)

            # Guardar la compra con totales calculados
            compra = serializer.save(
                monto_total=totales["total"], saldo_pendiente=totales["total"], estado_pago="Pendiente"
            )

            # Crear los registros DetallesCompra
            from apps.productos.models import Productos

            for detalle in detalles:
                costo = Decimal(str(detalle.get("costo_unitario") or detalle.get("precio_unitario", 0)))
                cantidad = Decimal(str(detalle.get("cantidad", 0)))
                subtotal = costo * cantidad
                producto = Productos.objects.get(id_producto=detalle["id_producto"])

                # Calcular IVA del detalle
                monto_iva = Decimal("0.00")
                try:
                    porcentaje = producto.id_impuesto.porcentaje
                    monto_iva = subtotal * porcentaje / Decimal("100")
                except Exception:
                    pass

                DetallesCompra.objects.create(
                    id_compra=compra,
                    id_producto=producto,
                    cantidad=cantidad,
                    costo_unitario=costo,
                    subtotal=subtotal,
                    monto_iva=monto_iva,
                )
        else:
            # Sin detalles, guardar como está
            serializer.save(estado_pago="Pendiente")

    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        """
        Confirma una compra.

        POST /api/compras/{id}/confirmar/
        """
        compra = self.get_object()

        try:
            resultado = CompraService.confirmar_compra(id_compra=compra.id_compra, empleado=None)

            if isinstance(resultado, dict):
                if not resultado.get("exito", False):
                    return Response(
                        {"error": resultado.get("error", "No se pudo confirmar la compra")},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                # Recargar la compra desde la base de datos
                compra.refresh_from_db()
            else:
                compra = resultado

            serializer = self.get_serializer(compra)
            return Response({"mensaje": "Compra confirmada exitosamente", "compra": serializer.data})

        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def pendientes(self, request):
        """
        Lista compras pendientes de confirmación.

        GET /api/compras/pendientes/
        """
        compras = CompraService.obtener_compras_pendientes_confirmacion()
        serializer = self.get_serializer(compras, many=True)

        return Response({"count": compras.count(), "compras": serializer.data})

    @action(detail=False, methods=["post"])
    def calcular_totales(self, request):
        """
        Calcula los totales de una compra (sin guardarla).

        POST /api/compras/calcular_totales/
        Body: {
            "detalles": [
                {"id_producto": 1, "cantidad": 10, "precio_unitario": 5000},
                ...
            ]
        }
        """
        detalles = request.data.get("detalles", [])

        if not detalles:
            return Response({"error": "Debe proporcionar detalles"}, status=status.HTTP_400_BAD_REQUEST)

        # Validar primero
        validacion = CompraService.validar_compra(detalles)

        if not validacion["valido"]:
            return Response(
                {
                    "error": "La compra contiene errores",
                    "errores": validacion["errores"],
                    "warnings": validacion["warnings"],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calcular totales
        totales = CompraService.calcular_totales_compra(detalles)

        return Response({"totales": totales, "warnings": validacion["warnings"]})

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """
        Resumen estadístico de compras.

        GET /api/v1/compras/estadisticas/
        """
        from django.db.models import Sum

        total_compras = Compras.objects.count()
        compras_pendientes = Compras.objects.filter(estado_pago="Pendiente").count()
        monto_total = Compras.objects.aggregate(total=Sum("monto_total"))["total"] or 0
        saldo_pendiente = (
            Compras.objects.filter(estado_pago="Pendiente").aggregate(total=Sum("saldo_pendiente"))["total"] or 0
        )

        return Response(
            {
                "total_compras": total_compras,
                "compras_pendientes": compras_pendientes,
                "monto_total": str(monto_total),
                "saldo_pendiente": str(saldo_pendiente),
            }
        )


class DetallesCompraViewSet(viewsets.ModelViewSet):
    queryset = DetallesCompra.objects.all().order_by("pk")
    serializer_class = DetallesCompraSerializer
    permission_classes = [IsAuthenticated, CanManageCompras]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id_compra", "id_producto"]


class PagosProveedoresViewSet(viewsets.ModelViewSet):
    queryset = PagosProveedores.objects.all()
    serializer_class = PagosProveedoresSerializer
    permission_classes = [IsAuthenticated, CanManageCompras]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["id_medio_pago"]
    ordering = ["-fecha_creacion"]


class NotasCreditoProveedorViewSet(viewsets.ModelViewSet):
    queryset = NotasCreditoProveedor.objects.all()
    serializer_class = NotasCreditoProveedorSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["estado", "id_proveedor"]
    ordering = ["-fecha"]
