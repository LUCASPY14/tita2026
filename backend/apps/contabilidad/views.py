"""
Views para la app contabilidad
"""

import csv
import logging
from datetime import timedelta
from decimal import Decimal

from django.http import HttpResponse
from django.template.loader import render_to_string

from .numero_a_letras import monto_a_letras

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.usuarios.auditoria import registrar_auditoria

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
    EmitirLoteSerializer,
    PendienteItemSerializer,
)
from .services import CajaService, FacturacionService

logger = logging.getLogger(__name__)


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
        registrar_auditoria(
            request=request,
            operacion="ABRIR_CAJA",
            tabla="contabilidad_cierrecaja",
            id_registro=cierre.id,
            descripcion=f"Caja '{cierre.caja}' abierta con {cierre.monto_inicial} Gs.",
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
        registrar_auditoria(
            request=request,
            operacion="CONCILIAR_CAJA",
            tabla="contabilidad_cierrecaja",
            id_registro=cierre.id,
            descripcion=f"Caja '{cierre.caja}' conciliada",
        )
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
        registrar_auditoria(
            request=request,
            operacion="CERRAR_CAJA",
            tabla="contabilidad_cierrecaja",
            id_registro=cierre.id,
            descripcion=(
                f"Caja '{cierre.caja}' cerrada — contado={monto_contado} Gs."
                f" diferencia={cierre.diferencia_efectivo} Gs."
            ),
        )
        return Response(CierreCajaSerializer(cierre).data)

    @action(detail=True, methods=["get"], url_path="arqueo")
    def arqueo(self, request, pk=None):
        """
        GET /api/contabilidad/cierres-caja/{id}/arqueo/
        Devuelve el arqueo separado en:
          - efectivo: billetes en cajón (medio_pago EFECTIVO)
          - prepago:  ventas pagadas con el saldo de la tarjeta del alumno —
                      esa plata ya entró cuando se cargó el saldo, no es
                      efectivo ni movimiento bancario del día
          - medios_pago_totales: un total por cada medio de pago real usado
                      (POS Crédito, POS Débito, Transferencia, etc.) — dinámico,
                      no una lista fija, para no romper si se agregan medios nuevos
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

        # ── Prepago (venta pagada con saldo de tarjeta — no es plata a rendir) ─
        prepago_total = int(
            ing.filter(venta__tarjeta__isnull=False).aggregate(t=DSum("monto"))["t"] or 0
        )

        # ── Resto de medios de pago (POS Crédito, POS Débito, Transferencia...) ─
        # Se agrupa dinámicamente por medio_pago real en vez de adivinar por
        # nombre — así no se rompe si cambia el catálogo de medios de pago.
        otros_ingresos = ing.exclude(venta__tarjeta__isnull=False).exclude(
            medio_pago__descripcion__iexact="efectivo"
        )
        medios_pago_totales = [
            {"medio": r["medio_pago__descripcion"] or "Sin clasificar", "total": int(r["total"] or 0)}
            for r in otros_ingresos.values("medio_pago__descripcion")
                                    .annotate(total=DSum("monto"))
                                    .order_by("-total")
        ]

        # ── Egresos agrupados por medio (desglose visual) ─────────────────────
        egresos_por_medio = [
            {"medio": r["medio_pago__descripcion"] or "Efectivo", "total": int(r["total"] or 0)}
            for r in egr.values("medio_pago__descripcion")
                        .annotate(total=DSum("monto"))
                        .order_by("-total")
        ]

        return Response({
            "monto_inicial":        int(cierre.monto_inicial),
            "efectivo_esperado":    efectivo_esperado,
            "efectivo_ingresos":    efectivo_ingresos,
            "efectivo_egresos":     efectivo_egresos,
            "prepago_total":        prepago_total,
            "ingresos_total":       ingresos_total,
            "egresos_total":        egresos_total,
            "medios_pago_totales":  medios_pago_totales,
            "egresos_por_medio":    egresos_por_medio,
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
            logger.warning("DatosEmpresa no disponible (cierre print)", exc_info=True)

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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["estado", "cliente"]
    search_fields = ["nro_factura", "cliente__nombres", "cliente__apellidos", "cliente__razon_social"]
    ordering_fields = ["fecha_emision", "monto_total", "nro_factura"]
    ordering = ["-fecha_emision"]

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
            cliente = c.cliente_origen or (
                c.tarjeta.hijo.cliente_responsable if c.tarjeta and c.tarjeta.hijo else None
            )
            nombre = cliente.nombre_completo if cliente else "—"
            cliente_id = cliente.pk if cliente else None
            modalidad = cliente.modalidad_facturacion if cliente else "INMEDIATA"
            items.append({
                "tipo": "CARGA_SALDO",
                "id": c.pk,
                "cliente_id": cliente_id,
                "cliente_nombre": nombre,
                "modalidad_facturacion": modalidad,
                "descripcion": f"Carga de saldo tarjeta {c.tarjeta_id or '-'}",
                "monto": int(c.monto_cargado),
                "fecha": c.fecha_carga,
            })

        for p in data["pagos"]:
            cuenta = p.cuenta
            cliente = cuenta.hijo.cliente_responsable
            items.append({
                "tipo": "PAGO_ALMUERZO",
                "id": p.pk,
                "cliente_id": cliente.pk,
                "cliente_nombre": cliente.nombre_completo,
                "modalidad_facturacion": cliente.modalidad_facturacion,
                "descripcion": f"Pago almuerzo {cuenta.hijo.nombre_completo} — {cuenta.mes}/{cuenta.anio}",
                "monto": int(p.monto),
                "fecha": p.fecha_pago,
            })

        for v in data["ventas"]:
            cliente = v.cliente
            items.append({
                "tipo": "VENTA",
                "id": v.pk,
                "cliente_id": cliente.pk if cliente else None,
                "cliente_nombre": cliente.nombre_completo if cliente else "—",
                "modalidad_facturacion": cliente.modalidad_facturacion if cliente else "INMEDIATA",
                "descripcion": f"Venta #{v.pk} — {v.get_tipo_display()} — {int(v.monto_total):,} Gs.",
                "monto": int(v.monto_total),
                "fecha": v.fecha,
            })

        for pc in data["pagos_credito"]:
            cliente = pc.cliente
            items.append({
                "tipo": "PAGO_CREDITO",
                "id": pc.pk,
                "cliente_id": cliente.pk if cliente else None,
                "cliente_nombre": cliente.nombre_completo if cliente else "—",
                "modalidad_facturacion": cliente.modalidad_facturacion if cliente else "INMEDIATA",
                "descripcion": f"Cobro crédito #{pc.pk} — {int(pc.monto):,} Gs.",
                "monto": int(pc.monto),
                "fecha": pc.fecha,
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

    @action(detail=False, methods=["post"], url_path="emitir-lote")
    def emitir_lote(self, request):
        """Emite una factura agrupando varios ítems del mismo cliente."""
        serializer = EmitirLoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        factura = FacturacionService.emitir_lote(
            tipo=serializer.validated_data["tipo"],
            ids=serializer.validated_data["ids"],
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
        cargas = list(factura.cargas_saldo.all()[:5])
        pagos_almuerzo = list(factura.pagos_cuenta_almuerzo.all()[:1])
        if cargas:
            if len(cargas) == 1:
                concepto = f"Carga de saldo tarjeta {cargas[0].tarjeta_id}"
            else:
                concepto = f"Cargas de saldo — {len(cargas)} recargas"
        elif pagos_almuerzo:
            pago = pagos_almuerzo[0]
            cuenta = pago.cuenta
            concepto = (
                f"Pago almuerzo — {cuenta.hijo.nombre_completo} "
                f"({cuenta.mes}/{cuenta.anio})"
            )

        empresa = None
        try:
            empresa = DatosEmpresa.objects.first()
        except Exception:
            logger.warning("DatosEmpresa no disponible (factura print)", exc_info=True)

        # Condición de venta real (el papel exige marcar CONTADO o CRÉDITO)
        if factura.venta_id:
            condicion_venta = factura.venta.get_tipo_display().upper()
        elif cargas and cargas[0].metodo_pago == "CUENTA_CORRIENTE":
            condicion_venta = "CRÉDITO"
        else:
            condicion_venta = "CONTADO"

        # Líneas de detalle: si la factura viene de una venta del POS, se
        # imprime cada producto en su fila (como pide el papel); si viene de
        # una carga de saldo o pago de almuerzo (sin líneas de producto), se
        # imprime una sola fila con el concepto.
        lineas = []
        if factura.venta_id:
            for detalle in factura.venta.detalles.select_related("producto").all():
                if detalle.monto_gravada_10 or detalle.iva_10:
                    columna = "10"
                elif detalle.monto_gravada_5 or detalle.iva_5:
                    columna = "5"
                else:
                    columna = "exenta"
                lineas.append({
                    "cantidad": detalle.cantidad,
                    "descripcion": detalle.producto.descripcion,
                    "precio_unitario": detalle.precio_unitario,
                    "columna": columna,
                    "valor_venta": detalle.subtotal,
                })
        else:
            if factura.iva_10:
                columna = "10"
            elif factura.iva_5:
                columna = "5"
            else:
                columna = "exenta"
            lineas.append({
                "cantidad": 1,
                "descripcion": concepto,
                "precio_unitario": factura.monto_total,
                "columna": columna,
                "valor_venta": factura.monto_total,
            })

        totales_columna = {"exenta": Decimal(0), "5": Decimal(0), "10": Decimal(0)}
        for linea in lineas:
            totales_columna[linea["columna"]] += linea["valor_venta"]

        html = render_to_string("contabilidad/factura_print.html", {
            "factura": factura,
            "concepto": concepto,
            "empresa": empresa,
            "condicion_venta": condicion_venta,
            "lineas": lineas,
            "totales_columna": totales_columna,
            "total_iva": (factura.iva_5 or 0) + (factura.iva_10 or 0),
            "monto_en_letras": monto_a_letras(factura.monto_total),
        })
        return HttpResponse(html, content_type="text/html; charset=utf-8")


class DatosEmpresaViewSet(viewsets.ModelViewSet):
    queryset = DatosEmpresa.objects.all()
    serializer_class = DatosEmpresaSerializer
    permission_classes = [IsAdmin]

    def get_permissions(self):
        if self.action == "publico":
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=["get"], url_path="publico")
    def publico(self, request):
        """
        GET /api/v1/contabilidad/datos-empresa/publico/
        Razón social, RUC, email y teléfono — datos públicos (van en toda
        factura), usados en la página de Términos y Condiciones y en el
        footer del portal, sin requerir sesión.
        """
        empresa = DatosEmpresa.objects.filter(activo=True).first()
        if not empresa:
            return Response({"razon_social": "", "ruc": "", "email": "", "telefono": ""})
        return Response({
            "razon_social": empresa.razon_social,
            "ruc": empresa.ruc,
            "email": empresa.email or "",
            "telefono": empresa.telefono or "",
        })


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
                return Response(
                    {"error": "Formato de fecha inválido (YYYY-MM-DD)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
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
        from django.db.models import Count, Sum, Max, Avg

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
