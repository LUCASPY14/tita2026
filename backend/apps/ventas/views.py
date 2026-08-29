"""
Views para la app ventas
"""

import csv

from django.http import HttpResponse

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from common.object_permissions import IsCajaOwnerOrAdmin
from common.permissions import IsCajeroOrAdmin, IsAdmin, IsStaffUser
from common.throttling import SensitiveEndpointThrottle
from .filters import VentaFilter
from apps.usuarios.auditoria import registrar_auditoria

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
    permission_classes = [IsCajeroOrAdmin, IsCajaOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = VentaFilter
    search_fields = ["cliente__nombres", "cliente__apellidos", "cliente__ruc_ci"]
    ordering_fields = ["fecha", "monto_total"]
    ordering = ["-fecha"]

    def get_queryset(self):
        from django.db.models import DecimalField, Sum, Value
        from django.db.models.functions import Coalesce
        qs = (
            Venta.objects
            .select_related("cliente", "cajero", "hijo", "hijo__grado")
            .prefetch_related("detalles", "detalles__producto")
            .annotate(
                _total_pagado=Coalesce(
                    Sum("aplicaciones_pago__monto_aplicado"),
                    Value(0, output_field=DecimalField(max_digits=12, decimal_places=0)),
                )
            )
        )
        # Cajeros solo ven sus propias ventas
        user = self.request.user
        if getattr(user, "rol", None) == "CAJERO":
            qs = qs.filter(cajero=user)
        return qs

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
        registrar_auditoria(
            request=request,
            operacion="CREAR_VENTA",
            tabla="ventas_venta",
            id_registro=venta.id,
            descripcion=f"Venta #{venta.id} {venta.tipo} {venta.monto_total} Gs.",
        )
        resp_data = VentaSerializer(venta).data
        headers = self.get_success_headers(resp_data)
        if advertencias:
            resp_data = dict(resp_data)
            resp_data["advertencias_alergenos"] = advertencias
        return Response(resp_data, status=status.HTTP_201_CREATED, headers=headers)

    @action(
        detail=True, methods=["post"], url_path="anular",
        permission_classes=[IsAdmin], throttle_classes=[SensitiveEndpointThrottle],
    )
    def anular(self, request, pk=None):
        """Anula una venta activa revirtiendo stock, tarjeta y cuenta corriente."""
        venta = self.get_object()
        try:
            venta = VentaService.anular_venta(venta, anulado_por=request.user)
        except Exception as e:
            registrar_auditoria(
                request=request,
                operacion="ANULAR_VENTA",
                tabla="ventas_venta",
                id_registro=venta.id,
                descripcion=f"Intento fallido de anular venta #{venta.id}",
                resultado="FALLA",
                mensaje_error=str(e),
            )
            if hasattr(e, "detail"):
                return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        registrar_auditoria(
            request=request,
            operacion="ANULAR_VENTA",
            tabla="ventas_venta",
            id_registro=venta.id,
            descripcion=f"Venta #{venta.id} anulada ({venta.monto_total} Gs.)",
        )
        return Response(VentaSerializer(venta).data)

    def _registrar(self, serializer):
        from decimal import Decimal
        from apps.productos.models import Producto
        from apps.contabilidad.models import CierreCaja
        from rest_framework.exceptions import ValidationError as DRFValidationError

        data = serializer.validated_data
        raw_items = self.request.data.get("items", [])

        # Verificar caja abierta — obligatorio para registrar ventas
        cierre_caja = CierreCaja.objects.filter(
            empleado=self.request.user, estado=CierreCaja.Estado.ABIERTO
        ).select_related("caja").first()
        if not cierre_caja:
            raise DRFValidationError({
                "error": "No hay una caja abierta. Abrí una caja antes de registrar ventas."
            })

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
            })

        return VentaService.registrar_venta(
            cliente=data.get("cliente"),
            cajero=self.request.user,
            tipo=data.get("tipo", "CONTADO"),
            medio_pago=data.get("medio_pago"),
            tarjeta=data.get("tarjeta"),
            hijo=data.get("hijo"),
            items=items,
            referencia=data.get("referencia", ""),
            cierre_caja=cierre_caja,
            genera_factura_legal=bool(self.request.data.get("genera_factura_legal", False)),
            nro_factura=str(self.request.data.get("nro_factura", "") or "").strip(),
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

    def perform_create(self, serializer):
        nc = serializer.save()
        registrar_auditoria(
            request=self.request,
            operacion="EMITIR_NOTA_CREDITO",
            tabla="ventas_notacredito",
            id_registro=nc.id,
            descripcion=f"Nota de crédito #{nc.id} por {nc.monto_total} Gs. cliente={nc.cliente_id}",
        )


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

        fmt = request.query_params.get("formato")
        if fmt == "csv":
            return self._exportar_csv(filas, desde, hasta, total_general)
        if fmt == "pdf":
            return self._exportar_pdf(filas, desde, hasta, total_general)

        return Response({
            "periodo": {"desde": desde, "hasta": hasta},
            "total_monto": total_general,
            "productos": filas,
        })

    def _exportar_pdf(self, filas, desde, hasta, total_general):
        from common.pdf_report import pdf_response

        def fmt_gs(n):
            return f"{int(n):,} Gs.".replace(",", ".")
        rows = [
            [i + 1, f["descripcion"], f["categoria"] or "—",
             f["total_cantidad"], f["num_ventas"], fmt_gs(f["total_monto"])]
            for i, f in enumerate(filas)
        ]
        return pdf_response(
            filename=f"ventas_productos_{desde}_{hasta}.pdf",
            title="Productos más vendidos",
            subtitle=f"Período: {desde} al {hasta}",
            headers=["#", "Producto", "Categoría", "Cantidad", "N° Ventas", "Total (Gs.)"],
            rows=rows,
            totals=["TOTAL", "", "", "", "", fmt_gs(total_general)],
        )

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


class ReporteVentasCajeroView(APIView):
    """
    GET /api/ventas/reporte-cajeros/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
    Ventas agrupadas por cajero: cantidad, monto total y ticket promedio.
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
            Venta.objects
            .filter(
                fecha__date__gte=desde,
                fecha__date__lte=hasta,
                estado=Venta.Estado.ACTIVA,
            )
            .values("cajero__id", "cajero__nombre", "cajero__apellido", "cajero__email")
            .annotate(
                cantidad_ventas=Count("id"),
                total_monto=Sum("monto_total"),
            )
            .order_by("-total_monto")
        )

        filas = []
        for r in qs:
            nombre = f"{r['cajero__nombre'] or ''} {r['cajero__apellido'] or ''}".strip()
            filas.append({
                "cajero_id": r["cajero__id"],
                "username": r["cajero__email"] or "",
                "nombre": nombre or r["cajero__email"] or "—",
                "cantidad_ventas": r["cantidad_ventas"],
                "monto_total": int(r["total_monto"] or 0),
                "ticket_promedio": int((r["total_monto"] or 0) / r["cantidad_ventas"]) if r["cantidad_ventas"] else 0,
            })

        total_general = sum(f["monto_total"] for f in filas)

        fmt = request.query_params.get("formato")
        if fmt == "csv":
            return self._exportar_csv(filas, desde, hasta, total_general)
        if fmt == "pdf":
            return self._exportar_pdf(filas, desde, hasta, total_general)

        return Response({
            "periodo": {"desde": desde, "hasta": hasta},
            "total_monto": total_general,
            "cajeros": filas,
        })

    def _exportar_pdf(self, filas, desde, hasta, total_general):
        from common.pdf_report import pdf_response
        def fmt_gs(n):
            return f"{int(n):,} Gs.".replace(",", ".")
        rows = [
            [f["nombre"], f["username"], f["cantidad_ventas"],
             fmt_gs(f["monto_total"]), fmt_gs(f["ticket_promedio"])]
            for f in filas
        ]
        return pdf_response(
            filename=f"ventas_cajeros_{desde}_{hasta}.pdf",
            title="Ventas por Cajero",
            subtitle=f"Período: {desde} al {hasta}",
            headers=["Cajero", "Usuario", "N° Ventas", "Total (Gs.)", "Ticket Prom."],
            rows=rows,
            totals=["TOTAL", "", "", fmt_gs(total_general), ""],
        )

    def _exportar_csv(self, filas, desde, hasta, total_general):
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = (
            f'attachment; filename="ventas_cajero_{desde}_{hasta}.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(["REPORTE DE VENTAS POR CAJERO", f"{desde} al {hasta}"])
        writer.writerow([])
        writer.writerow(["Cajero", "Usuario", "Nro Ventas", "Total (Gs)", "Ticket Promedio (Gs)"])
        for f in filas:
            writer.writerow([f["nombre"], f["username"], f["cantidad_ventas"], f["monto_total"], f["ticket_promedio"]])
        writer.writerow([])
        writer.writerow(["TOTAL GENERAL", "", "", total_general, ""])
        return response


class ReporteMediosPagoView(APIView):
    """
    GET /api/ventas/reporte-medios-pago/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
    Pagos agrupados por medio de pago: cantidad, monto y estado de conciliación.
    Opcional: ?formato=csv
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        from django.db.models import Count, Sum, Q

        desde = request.query_params.get("desde")
        hasta = request.query_params.get("hasta")

        if not desde or not hasta:
            return Response(
                {"error": "Se requieren los parámetros desde y hasta (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .models import PagoVenta
        qs = (
            PagoVenta.objects
            .filter(
                fecha__date__gte=desde,
                fecha__date__lte=hasta,
                estado__in=["PENDIENTE", "CONCILIADO"],
            )
            .values("medio_pago__id", "medio_pago__descripcion")
            .annotate(
                n_pagos=Count("id"),
                monto_total=Sum("monto"),
                n_conciliados=Count("id", filter=Q(estado="CONCILIADO")),
                monto_conciliado=Sum("monto", filter=Q(estado="CONCILIADO")),
                n_pendientes=Count("id", filter=Q(estado="PENDIENTE")),
                monto_pendiente=Sum("monto", filter=Q(estado="PENDIENTE")),
            )
            .order_by("-monto_total")
        )

        filas = [
            {
                "medio_pago_id": r["medio_pago__id"],
                "descripcion": r["medio_pago__descripcion"] or "Sin medio",
                "n_pagos": r["n_pagos"],
                "monto_total": int(r["monto_total"] or 0),
                "n_conciliados": r["n_conciliados"],
                "monto_conciliado": int(r["monto_conciliado"] or 0),
                "n_pendientes": r["n_pendientes"],
                "monto_pendiente": int(r["monto_pendiente"] or 0),
            }
            for r in qs
        ]

        total_pagos = sum(f["n_pagos"] for f in filas)
        monto_total = sum(f["monto_total"] for f in filas)

        if request.query_params.get("formato") == "csv":
            response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
            response["Content-Disposition"] = (
                f'attachment; filename="medios_pago_{desde}_{hasta}.csv"'
            )
            writer = csv.writer(response)
            writer.writerow(["REPORTE MEDIOS DE PAGO", f"{desde} al {hasta}"])
            writer.writerow([])
            writer.writerow([
                "Medio de Pago", "N° Pagos", "Monto Total (Gs)",
                "Conciliados", "Monto Conciliado", "Pendientes", "Monto Pendiente",
            ])
            for f in filas:
                writer.writerow([f["descripcion"], f["n_pagos"], f["monto_total"],
                                  f["n_conciliados"], f["monto_conciliado"],
                                  f["n_pendientes"], f["monto_pendiente"]])
            writer.writerow([])
            writer.writerow(["TOTAL", total_pagos, monto_total])
            return response

        return Response({
            "periodo": {"desde": desde, "hasta": hasta},
            "resumen": {
                "total_pagos": total_pagos,
                "monto_total": monto_total,
                "n_medios": len(filas),
            },
            "por_medio_pago": filas,
        })


class ReporteNotasCreditoVentaView(APIView):
    """
    GET /api/ventas/reporte-notas-credito/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD[&estado=]
    Notas de crédito emitidas a clientes: volumen, montos y quién las autoriza.
    Opcional: ?formato=csv
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        desde = request.query_params.get("desde")
        hasta = request.query_params.get("hasta")
        estado_filtro = request.query_params.get("estado")

        if not desde or not hasta:
            return Response(
                {"error": "Se requieren los parámetros desde y hasta (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = NotaCredito.objects.filter(
            fecha_emision__date__gte=desde,
            fecha_emision__date__lte=hasta,
        ).select_related("cliente", "venta_origen", "empleado_autoriza")

        if estado_filtro:
            qs = qs.filter(estado=estado_filtro)

        filas = []
        for nc in qs.order_by("-fecha_emision"):
            cliente = nc.cliente
            autorizador = nc.empleado_autoriza
            filas.append({
                "id": nc.pk,
                "nro_nota_credito": nc.nro_nota_credito,
                "fecha_emision": nc.fecha_emision.strftime("%Y-%m-%d %H:%M"),
                "cliente_id": cliente.pk if cliente else None,
                "cliente": cliente.nombre_completo if cliente else "",
                "ruc_ci": getattr(cliente, "ruc_ci", "") or "",
                "estado": nc.estado,
                "motivo": nc.motivo,
                "monto_total": int(nc.monto_total),
                "empleado_autoriza_id": autorizador.pk if autorizador else None,
                "empleado_autoriza": (
                    f"{autorizador.nombre} {autorizador.apellido}".strip()
                    if autorizador else ""
                ),
                "venta_origen_id": nc.venta_origen_id,
            })

        resumen = {
            "total_emitidas": sum(1 for f in filas if f["estado"] == "EMITIDA"),
            "total_aplicadas": sum(1 for f in filas if f["estado"] == "APLICADA"),
            "total_anuladas": sum(1 for f in filas if f["estado"] == "ANULADA"),
            "monto_emitidas": sum(f["monto_total"] for f in filas if f["estado"] == "EMITIDA"),
            "monto_aplicadas": sum(f["monto_total"] for f in filas if f["estado"] == "APLICADA"),
            "monto_anuladas": sum(f["monto_total"] for f in filas if f["estado"] == "ANULADA"),
            "monto_total": sum(f["monto_total"] for f in filas if f["estado"] != "ANULADA"),
        }

        if request.query_params.get("formato") == "csv":
            response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
            response["Content-Disposition"] = (
                f'attachment; filename="notas_credito_ventas_{desde}_{hasta}.csv"'
            )
            writer = csv.writer(response)
            writer.writerow(["NOTAS DE CRÉDITO - VENTAS", f"{desde} al {hasta}"])
            writer.writerow([])
            writer.writerow(["N° NC", "Fecha", "Cliente", "RUC/CI", "Estado", "Motivo", "Monto (Gs)", "Autorizado por"])
            for f in filas:
                writer.writerow([
                    f["nro_nota_credito"], f["fecha_emision"], f["cliente"],
                    f["ruc_ci"], f["estado"], f["motivo"],
                    f["monto_total"], f["empleado_autoriza"],
                ])
            writer.writerow([])
            writer.writerow(["RESUMEN"])
            writer.writerow(["Emitidas", resumen["total_emitidas"], resumen["monto_emitidas"]])
            writer.writerow(["Aplicadas", resumen["total_aplicadas"], resumen["monto_aplicadas"]])
            writer.writerow(["Anuladas", resumen["total_anuladas"], resumen["monto_anuladas"]])
            return response

        return Response({
            "periodo": {"desde": desde, "hasta": hasta},
            "resumen": resumen,
            "detalle": filas,
        })
