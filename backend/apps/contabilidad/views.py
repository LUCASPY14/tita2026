from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum
from .models import (
    Impuestos,
    DatosEmpresa,
    Timbrados,
    DocumentosTributarios,
    PuntosExpedicion,
    Cajas,
    CierresCaja,
    MovimientosCaja,
)
from .serializers import (
    ImpuestosSerializer,
    DatosEmpresaSerializer,
    TimbradoSerializer,
    DocumentosTributariosSerializer,
    PuntosExpedicionSerializer,
    CajaSerializer,
    CierresCajaSerializer,
    MovimientosCajaSerializer,
    AbrirCajaSerializer,
    CerrarCajaSerializer,
)
from datetime import date
from decimal import Decimal


class ImpuestosViewSet(viewsets.ModelViewSet):
    """CRUD de impuestos/tasas (IVA 10%, IVA 5%, Exenta)."""

    queryset = Impuestos.objects.all().order_by("nombre_impuesto")
    serializer_class = ImpuestosSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        qs = Impuestos.objects.all().order_by("nombre_impuesto")
        solo_activos = self.request.query_params.get("activos", None)
        if solo_activos is not None:
            qs = qs.filter(estado=solo_activos.lower() != "false")
        return qs

    def destroy(self, request, *args, **kwargs):
        """Soft-delete: marca estado=False en lugar de eliminar."""
        instance = self.get_object()
        instance.estado = False
        instance.save(update_fields=["estado"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class DatosEmpresaViewSet(viewsets.ModelViewSet):
    """Datos de la empresa emisora (RUC, razón social, dirección)."""

    queryset = DatosEmpresa.objects.filter(estado=True)
    serializer_class = DatosEmpresaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    @action(detail=False, methods=["get"], url_path="activa")
    def activa(self, request):
        """Devuelve los datos de la empresa activa."""
        empresa = DatosEmpresa.objects.filter(estado=True).first()
        if not empresa:
            return Response({"detail": "No hay datos de empresa configurados."}, status=404)
        return Response(DatosEmpresaSerializer(empresa).data)


class PuntosExpedicionViewSet(viewsets.ModelViewSet):
    """CRUD de puntos de expedición (establecimiento + punto)."""

    queryset = PuntosExpedicion.objects.filter(estado=True).order_by("codigo_establecimiento")
    serializer_class = PuntosExpedicionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class TimbradosViewSet(viewsets.ModelViewSet):
    """Timbrados registrados ante la SET (lectura y alta)."""

    queryset = Timbrados.objects.order_by("-fecha_inicio")
    serializer_class = TimbradoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    @action(detail=False, methods=["get"], url_path="vigente")
    def vigente(self, request):
        """Devuelve el timbrado vigente a hoy."""
        hoy = date.today()
        timbrado = (
            Timbrados.objects.filter(
                estado=True,
                fecha_inicio__lte=hoy,
                fecha_fin__gte=hoy,
            )
            .order_by("-fecha_inicio")
            .first()
        )
        if not timbrado:
            return Response({"detail": "No hay timbrado vigente configurado."}, status=404)
        return Response(TimbradoSerializer(timbrado).data)


class DocumentosTributariosViewSet(viewsets.ModelViewSet):
    """Documentos tributarios emitidos (facturas físicas)."""

    queryset = DocumentosTributarios.objects.select_related("nro_timbrado", "id_cliente").order_by("-fecha_emision")
    serializer_class = DocumentosTributariosSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["tipo_documento", "condicion_venta", "id_cliente"]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        fecha_desde = params.get("fecha_desde")
        fecha_hasta = params.get("fecha_hasta")
        if fecha_desde:
            qs = qs.filter(fecha_emision__date__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha_emision__date__lte=fecha_hasta)
        return qs


# ─── Cajas ────────────────────────────────────────────────────────────────────


class CajasViewSet(viewsets.ModelViewSet):
    """CRUD de cajas registradoras."""

    queryset = Cajas.objects.all().order_by("nombre_caja")
    serializer_class = CajaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class CierresCajaViewSet(viewsets.ModelViewSet):
    """
    Gestión de turnos de caja (apertura y cierre).

    Acciones especiales:
      POST /cierres-caja/abrir/           → abre un nuevo turno
      POST /cierres-caja/{id}/cerrar/     → cierra el turno activo
      GET  /cierres-caja/turno-activo/    → turno abierto del cajero en sesión
      GET  /cierres-caja/{id}/resumen/    → detalle con movimientos y totales
    """

    queryset = CierresCaja.objects.select_related("id_caja", "id_empleado").order_by("-fecha_hora_apertura")
    serializer_class = CierresCajaSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["estado", "id_caja"]

    @action(detail=False, methods=["post"], url_path="abrir")
    def abrir(self, request):
        """Abre un nuevo turno de caja.

        Usa SELECT FOR UPDATE dentro de una transacción atómica para evitar
        que dos requests simultáneos sobre la misma caja creen dos turnos abiertos.
        """
        ser = AbrirCajaSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        with transaction.atomic():
            # Lock a nivel de fila: si otro request llega al mismo tiempo para
            # la misma caja, esperará hasta que esta transacción termine.
            turno_existente = (
                CierresCaja.objects.select_for_update().filter(id_caja=data["id_caja"], estado="abierto").first()
            )
            if turno_existente:
                return Response(
                    {"detail": f"La caja ya tiene un turno abierto (ID {turno_existente.pk})."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            turno = CierresCaja.objects.create(
                id_caja_id=data["id_caja"],
                id_empleado_id=data["id_empleado"],
                monto_inicial=data["monto_inicial"],
                fecha_hora_apertura=timezone.now(),
                estado="abierto",
            )
            # Registrar movimiento de fondo inicial
            from apps.core.models import MediosPago

            efectivo = MediosPago.objects.filter(descripcion__icontains="efectivo").first()
            if efectivo and data["monto_inicial"] > 0:
                MovimientosCaja.objects.create(
                    id_cierre=turno,
                    tipo_movimiento="Ingreso",
                    monto=data["monto_inicial"],
                    fecha_movimiento=timezone.now(),
                    descripcion="Fondo inicial de caja",
                    id_medio_pago=efectivo,
                )
        return Response(CierresCajaSerializer(turno).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cerrar")
    def cerrar(self, request, pk=None):
        """Cierra el turno activo calculando diferencia de efectivo."""
        turno = self.get_object()
        if turno.estado != "abierto":
            return Response(
                {"detail": "El turno ya está cerrado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ser = CerrarCajaSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        # Calcular total efectivo esperado
        total_ingresos = turno.movimientoscaja_set.filter(tipo_movimiento__in=["Ingreso", "VentaEfectivo"]).aggregate(
            t=Sum("monto")
        )["t"] or Decimal("0")
        total_egresos = turno.movimientoscaja_set.filter(tipo_movimiento="Egreso").aggregate(t=Sum("monto"))[
            "t"
        ] or Decimal("0")
        efectivo_esperado = total_ingresos - total_egresos

        turno.fecha_hora_cierre = timezone.now()
        turno.monto_contado_fisico = data["monto_contado_fisico"]
        turno.diferencia_efectivo = data["monto_contado_fisico"] - efectivo_esperado
        turno.estado = "cerrado"
        turno.save()

        return Response(CierresCajaSerializer(turno).data)

    @action(detail=False, methods=["get"], url_path="turno-activo")
    def turno_activo(self, request):
        """Devuelve el turno abierto de UNA caja específica.

        Query param obligatorio: ?id_caja=<int>
        Sin él devuelve el turno más reciente de cualquier caja (compatibilidad).
        """
        qs = CierresCaja.objects.filter(estado="abierto").order_by("-fecha_hora_apertura")

        id_caja = request.query_params.get("id_caja")
        if id_caja:
            try:
                qs = qs.filter(id_caja=int(id_caja))
            except (ValueError, TypeError):
                return Response({"detail": "id_caja debe ser un número entero."}, status=400)

        turno = qs.first()
        if not turno:
            return Response({"detail": "No hay turno activo."}, status=404)
        return Response(CierresCajaSerializer(turno).data)

    @action(detail=True, methods=["get"], url_path="resumen")
    def resumen(self, request, pk=None):
        """Detalle completo del turno con movimientos y totales por medio de pago."""
        turno = self.get_object()
        movimientos = (
            MovimientosCaja.objects.filter(id_cierre=turno)
            .values("tipo_movimiento", "id_medio_pago__descripcion")
            .annotate(total=Sum("monto"))
            .order_by("tipo_movimiento")
        )

        return Response(
            {
                "turno": CierresCajaSerializer(turno).data,
                "resumen_medios_pago": list(movimientos),
            }
        )


class MovimientosCajaViewSet(viewsets.ModelViewSet):
    """Ingresos y egresos manuales de caja (fondos, gastos, etc.)."""

    queryset = MovimientosCaja.objects.select_related("id_cierre", "id_medio_pago", "id_venta").order_by(
        "-fecha_movimiento"
    )
    serializer_class = MovimientosCajaSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["tipo_movimiento", "id_cierre"]


# ─── Facturación física ───────────────────────────────────────────────────────


class FacturacionViewSet(viewsets.ViewSet):
    """
    Cola de facturación y emisión de facturas físicas preimpresas.

    GET  /facturacion/cola/           → items pagados sin factura, por cliente
    POST /facturacion/emitir/         → emite factura vinculando ventas/almuerzos
    GET  /facturacion/{id}/imprimir/  → texto 80 col para Epson LX-50
    POST /facturacion/{id}/anular/    → anula factura y devuelve items a la cola
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="cola")
    def cola(self, request):
        """Items pagados sin facturar, agrupados por cliente."""
        from .facturacion_service import FacturacionService

        return Response(FacturacionService.get_cola())

    @action(detail=False, methods=["post"], url_path="emitir")
    def emitir(self, request):
        """Emite una factura física vinculando las ventas/almuerzos seleccionados."""
        from .facturacion_service import FacturacionService
        from .serializers import EmitirFacturaSerializer

        ser = EmitirFacturaSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        try:
            doc = FacturacionService.emitir(
                id_cliente=d["id_cliente"],
                nro_preimpreso=d["nro_preimpreso"],
                ventas_ids=d.get("ventas_ids", []),
                almuerzos_ids=d.get("almuerzos_ids", []),
                condicion_venta=d.get("condicion_venta", "CONTADO"),
                plazo_dias=d.get("plazo_dias"),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            DocumentosTributariosSerializer(doc).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="imprimir")
    def imprimir(self, request, pk=None):
        """Texto 80 columnas para Epson LX-50 (Content-Type: text/plain)."""
        from .facturacion_service import FacturacionService
        from django.http import HttpResponse

        try:
            texto = FacturacionService.texto_impresion(int(pk))
        except DocumentosTributarios.DoesNotExist:
            return Response({"detail": "Documento no encontrado."}, status=404)

        return HttpResponse(texto, content_type="text/plain; charset=utf-8")

    @action(detail=True, methods=["post"], url_path="anular")
    def anular(self, request, pk=None):
        """Anula una factura y devuelve los items a la cola de pendientes."""
        from .facturacion_service import FacturacionService

        try:
            FacturacionService.anular(int(pk))
        except DocumentosTributarios.DoesNotExist:
            return Response({"detail": "Documento no encontrado."}, status=404)

        return Response({"detail": "Factura anulada correctamente."})
