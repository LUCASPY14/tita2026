"""
Views para la app almuerzos
"""

from datetime import date
from decimal import Decimal

from django.db import models, transaction
from django.db.models import F

import csv

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework import serializers as drf_serializers

from common.permissions import IsAdmin, IsAdminOrReadOnly, IsCajeroOrAdmin, IsStaffOrClienteWeb, IsStaffUser

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Alergeno,
    CuentaAlmuerzoMensual,
    DetalleMenuDiario,
    MenuDiario,
    PagoCuentaAlmuerzo,
    PagoAlmuerzoMensual,
    PlanAlmuerzo,
    PrecioAlmuerzo,
    ProductoAlergeno,
    RegistroConsumoAlmuerzo,
    SuscripcionAlmuerzo,
    TipoAlmuerzo,
)
from .serializers import (
    AlergenoSerializer,
    CuentaAlmuerzoMensualSerializer,
    DetalleMenuDiarioSerializer,
    MenuDiarioSerializer,
    PagoCuentaAlmuerzoSerializer,
    PagoAlmuerzoMensualSerializer,
    PlanAlmuerzoSerializer,
    PrecioAlmuerzoSerializer,
    ProductoAlergenoSerializer,
    RegistroConsumoAlmuerzoSerializer,
    SuscripcionAlmuerzoSerializer,
    TipoAlmuerzoSerializer,
)
from .filters import RegistroConsumoFilter
from .validators import validar_limite_registros_diarios, validar_restricciones_alergenicas


# ==============================================================================
# HELPERS
# ==============================================================================

def get_precio_almuerzo_activo(fecha=None):
    """Retorna el PrecioAlmuerzo vigente para la fecha dada."""
    if fecha is None:
        fecha = date.today()
    return (
        PrecioAlmuerzo.objects.filter(
            fecha_inicio_vigencia__lte=fecha,
            activo=True,
        )
        .filter(
            models.Q(fecha_fin_vigencia__isnull=True) |
            models.Q(fecha_fin_vigencia__gte=fecha)
        )
        .order_by("-fecha_inicio_vigencia")
        .first()
    )


# ==============================================================================
# PRECIO ALMUERZO
# ==============================================================================

class PrecioAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = PrecioAlmuerzo.objects.all()
    serializer_class = PrecioAlmuerzoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["activo"]
    ordering = ["-fecha_inicio_vigencia"]

    @action(detail=False, methods=["get"], url_path="precio-actual")
    def precio_actual(self, request):
        precio = get_precio_almuerzo_activo()
        if precio:
            return Response(PrecioAlmuerzoSerializer(precio).data)
        return Response(
            {"error": "No hay un precio de almuerzo vigente configurado. Configure uno en el admin."},
            status=status.HTTP_404_NOT_FOUND,
        )


# ==============================================================================
# TIPO ALMUERZO
# ==============================================================================

class TipoAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = TipoAlmuerzo.objects.all()
    serializer_class = TipoAlmuerzoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["activo"]
    search_fields = ["nombre"]


# ==============================================================================
# PLAN ALMUERZO
# ==============================================================================

class PlanAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = PlanAlmuerzo.objects.all()
    serializer_class = PlanAlmuerzoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["activo", "tipo"]
    search_fields = ["nombre"]


# ==============================================================================
# SUSCRIPCION ALMUERZO
# ==============================================================================

class SuscripcionAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = SuscripcionAlmuerzo.objects.select_related("hijo", "plan").all()
    serializer_class = SuscripcionAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["estado", "hijo", "plan"]
    ordering = ["-fecha_inicio"]


# ==============================================================================
# REGISTRO CONSUMO ALMUERZO
# ==============================================================================

class RegistroConsumoAlmuerzoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para registrar consumos de almuerzo.

    REGLA DE NEGOCIO:
    - La tarjeta se usa SOLO como identificacion de acceso al comedor.
    - NO se descuenta saldo de la tarjeta.
    - Maximo 2 registros por alumno por dia, pero se factura como 1 ALMUERZO por dia:
        1er registro del dia: ya_cobrado=True  -> se agrega el costo a la cuenta mensual
        2do registro del dia: ya_cobrado=False -> costo=0, solo trazabilidad
    - Limite de credito mensual: si el plan tiene limite_credito_mensual, se bloquea
      cuando el monto acumulado en CuentaAlmuerzoMensual alcanza ese tope.
    """

    queryset = RegistroConsumoAlmuerzo.objects.select_related(
        "hijo", "suscripcion", "tipo_almuerzo", "nro_tarjeta"
    ).all()
    serializer_class = RegistroConsumoAlmuerzoSerializer
    permission_classes = [IsStaffOrClienteWeb]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsCajeroOrAdmin()]
        return [IsStaffOrClienteWeb()]

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"error": "Los registros de consumo no pueden eliminarse. Use el estado ANULADO."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    filterset_class = RegistroConsumoFilter
    search_fields = ["hijo__nombre", "hijo__apellido"]
    ordering = ["-fecha_consumo", "-hora_registro"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        advertencias = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        data = dict(serializer.data)
        if advertencias:
            data["advertencias"] = advertencias
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        registro_data = serializer.validated_data
        hijo = registro_data.get("hijo")
        fecha_consumo = registro_data.get("fecha_consumo")
        nro_tarjeta = registro_data.get("nro_tarjeta")
        tipo_almuerzo = registro_data.get("tipo_almuerzo")
        suscripcion = registro_data.get("suscripcion")

        # Tarjeta requerida como identificacion
        if not nro_tarjeta:
            raise ValidationError({"error": "Debe especificar la tarjeta para registrar el ingreso al almuerzo"})

        # Validar que la tarjeta pertenece al hijo y está activa
        if nro_tarjeta.hijo_id != hijo.pk:
            raise ValidationError({"error": "La tarjeta no pertenece al estudiante indicado."})
        if nro_tarjeta.estado != "ACTIVA":
            raise ValidationError({
                "error": f"La tarjeta está {nro_tarjeta.get_estado_display().lower()} y no puede usarse para ingresar."
            })

        # Validar restricciones alérgénicas del hijo
        forzar = self.request.data.get("forzar_restriccion", False)
        advertencias = validar_restricciones_alergenicas(hijo, forzar=bool(forzar))

        # Validar limite de 2 registros por dia
        es_primer_registro = validar_limite_registros_diarios(hijo, fecha_consumo)

        # Validar suscripcion si se provee
        if suscripcion and suscripcion.estado != SuscripcionAlmuerzo.Estado.ACTIVA:
            raise ValidationError({
                "error": "La suscripcion no esta activa",
                "estado_suscripcion": suscripcion.estado,
            })

        # Determinar costo
        if es_primer_registro:
            precio_obj = get_precio_almuerzo_activo(fecha_consumo)
            if precio_obj:
                costo_calculado = precio_obj.precio_unitario
            elif tipo_almuerzo:
                costo_calculado = tipo_almuerzo.precio_unitario
            else:
                raise ValidationError({
                    "error": "No hay precio de almuerzo configurado. Configure un precio vigente primero."
                })

            # Verificar limite de credito mensual
            if suscripcion and suscripcion.plan.limite_credito_mensual:
                cuenta_mes = CuentaAlmuerzoMensual.objects.filter(
                    hijo=hijo,
                    anio=fecha_consumo.year,
                    mes=fecha_consumo.month,
                ).first()
                saldo_pendiente = (
                    (cuenta_mes.monto_total - cuenta_mes.monto_pagado)
                    if cuenta_mes else Decimal("0")
                )
                if saldo_pendiente + costo_calculado > suscripcion.plan.limite_credito_mensual:
                    raise ValidationError({
                        "error": "Limite de credito mensual alcanzado.",
                        "saldo_pendiente": str(saldo_pendiente),
                        "limite_credito": str(suscripcion.plan.limite_credito_mensual),
                    })
        else:
            costo_calculado = Decimal("0")

        with transaction.atomic():
            registro = serializer.save(
                costo_almuerzo=costo_calculado,
                ya_cobrado=es_primer_registro,
                estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
                registrado_por=self.request.user,
            )
            if es_primer_registro:
                self._agregar_a_cuenta_mensual(registro)

        if es_primer_registro:
            try:
                from apps.notificaciones.services import _whatsapp_cliente
                cliente_resp = registro.hijo.cliente_responsable
                _whatsapp_cliente(
                    cliente_resp,
                    f"{registro.hijo.nombre_completo} almuerzo hoy "
                    f"{registro.fecha_consumo.strftime('%d/%m/%Y')}. "
                    f"Costo: Gs. {int(registro.costo_almuerzo):,}."
                )
            except Exception:
                pass

        return advertencias

    def _agregar_a_cuenta_mensual(self, registro):
        """Agrega el consumo a la cuenta mensual de almuerzo del hijo."""
        fecha = registro.fecha_consumo
        forma_cobro = registro.suscripcion.plan.tipo if registro.suscripcion else "SIN_LIMITE"

        cuenta, _ = CuentaAlmuerzoMensual.objects.get_or_create(
            hijo=registro.hijo,
            anio=fecha.year,
            mes=fecha.month,
            defaults={
                "cantidad_almuerzos": 0,
                "monto_total": 0,
                "monto_pagado": 0,
                "forma_cobro": forma_cobro,
                "estado": CuentaAlmuerzoMensual.Estado.PENDIENTE,
            },
        )

        # Lock para evitar race conditions en actualizaciones concurrentes
        cuenta = CuentaAlmuerzoMensual.objects.select_for_update().get(pk=cuenta.pk)
        cuenta.cantidad_almuerzos = F("cantidad_almuerzos") + 1
        cuenta.monto_total = F("monto_total") + registro.costo_almuerzo
        cuenta.save(update_fields=["cantidad_almuerzos", "monto_total"])


# ==============================================================================
# CUENTA ALMUERZO MENSUAL
# ==============================================================================

class CuentaAlmuerzoMensualViewSet(viewsets.ModelViewSet):
    queryset = CuentaAlmuerzoMensual.objects.select_related("hijo").all()
    serializer_class = CuentaAlmuerzoMensualSerializer
    permission_classes = [IsStaffOrClienteWeb]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["hijo", "anio", "mes", "estado"]
    ordering = ["-anio", "-mes"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if hasattr(user, "rol") and user.rol == "CLIENTE_WEB":
            qs = qs.filter(hijo__cliente_responsable=user.cliente)
        return qs

    @action(detail=False, methods=["post"], url_path="generar", permission_classes=[IsAdmin])
    def generar(self, request):
        """
        POST /api/almuerzos/cuentas-mensuales/generar/
        Body: {anio: 2026, mes: 5}
        Genera cuentas para todas las suscripciones activas del mes indicado.
        """
        class _Serializer(drf_serializers.Serializer):
            anio = drf_serializers.IntegerField(min_value=2020, max_value=2099)
            mes = drf_serializers.IntegerField(min_value=1, max_value=12)

        serializer = _Serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        anio = serializer.validated_data["anio"]
        mes = serializer.validated_data["mes"]

        suscripciones = SuscripcionAlmuerzo.objects.filter(
            estado=SuscripcionAlmuerzo.Estado.ACTIVA
        ).select_related("hijo")

        creadas = 0
        for suscripcion in suscripciones:
            _, fue_creada = CuentaAlmuerzoMensual.objects.get_or_create(
                hijo=suscripcion.hijo,
                anio=anio,
                mes=mes,
                defaults={
                    "cantidad_almuerzos": 0,
                    "monto_total": 0,
                    "monto_pagado": 0,
                    "forma_cobro": CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
                    "estado": CuentaAlmuerzoMensual.Estado.PENDIENTE,
                },
            )
            if fue_creada:
                creadas += 1

        return Response({
            "cuentas_creadas": creadas,
            "mes": mes,
            "anio": anio,
        })


# ==============================================================================
# PAGO CUENTA ALMUERZO
# ==============================================================================

class PagoCuentaAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = PagoCuentaAlmuerzo.objects.select_related("cuenta").all()
    serializer_class = PagoCuentaAlmuerzoSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["cuenta"]
    ordering = ["-fecha_pago"]

    def perform_create(self, serializer):
        with transaction.atomic():
            pago = serializer.save()
            cuenta = (
                CuentaAlmuerzoMensual.objects
                .select_for_update()
                .get(pk=pago.cuenta_id)
            )
            cuenta.registrar_pago(pago.monto)


# ==============================================================================
# PAGO ALMUERZO MENSUAL
# ==============================================================================

class PagoAlmuerzoMensualViewSet(viewsets.ModelViewSet):
    queryset = PagoAlmuerzoMensual.objects.select_related("suscripcion").all()
    serializer_class = PagoAlmuerzoMensualSerializer
    permission_classes = [IsCajeroOrAdmin]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["suscripcion", "estado"]
    ordering = ["-fecha_pago"]

    def perform_create(self, serializer):
        pago = serializer.save(estado=PagoAlmuerzoMensual.Estado.CONFIRMADO)
        try:
            from apps.notificaciones.services import _whatsapp_cliente
            hijo = pago.suscripcion.hijo
            cliente_resp = hijo.cliente_responsable
            mes = pago.mes_pagado
            _whatsapp_cliente(
                cliente_resp,
                f"Pago de almuerzo confirmado para {hijo.nombre_completo}: "
                f"Gs. {int(pago.monto_pagado):,} correspondiente a "
                f"{mes.strftime('%m/%Y')}. Gracias."
            )
        except Exception:
            pass


# ==============================================================================
# ALERGENO
# ==============================================================================

class AlergenoViewSet(viewsets.ModelViewSet):
    queryset = Alergeno.objects.all()
    serializer_class = AlergenoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["activo", "severidad"]
    search_fields = ["nombre"]


# ==============================================================================
# PRODUCTO ALERGENO
# ==============================================================================

class ProductoAlergenoViewSet(viewsets.ModelViewSet):
    queryset = ProductoAlergeno.objects.select_related("producto", "alergeno").all()
    serializer_class = ProductoAlergenoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto", "alergeno", "contiene"]


# ==============================================================================
# MENÚ DIARIO
# ==============================================================================

class MenuDiarioViewSet(viewsets.ModelViewSet):
    """
    CRUD de menú del día. Staff puede crear/editar; CLIENTE_WEB puede leer.
    GET /api/almuerzos/menu/?fecha=YYYY-MM-DD
    GET /api/almuerzos/menu/hoy/  → menú del día actual
    """
    queryset = MenuDiario.objects.filter(activo=True)
    serializer_class = MenuDiarioSerializer
    permission_classes = [IsStaffOrClienteWeb]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["fecha", "activo"]
    ordering = ["-fecha"]

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

    @action(detail=False, methods=["get"], url_path="hoy")
    def hoy(self, request):
        """Retorna el menú del día actual (fecha de hoy)."""
        menu = MenuDiario.objects.filter(fecha=date.today(), activo=True).first()
        if menu is None:
            return Response({"detail": "No hay menú publicado para hoy."}, status=404)
        return Response(MenuDiarioSerializer(menu).data)


# ==============================================================================
# DETALLE MENÚ DIARIO
# ==============================================================================

class DetalleMenuDiarioViewSet(viewsets.ModelViewSet):
    """
    CRUD de ítems de un menú diario.
    GET  /api/almuerzos/detalle-menu/?menu={id}   → ítems del menú
    GET  /api/almuerzos/detalle-menu/?menu={id}&curso=PLATO_PRINCIPAL
    POST /api/almuerzos/detalle-menu/             → agregar ítem (staff)
    PATCH/DELETE /api/almuerzos/detalle-menu/{id}/
    """
    serializer_class = DetalleMenuDiarioSerializer
    permission_classes = [IsStaffOrClienteWeb]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["menu", "curso", "es_opcional"]

    def get_queryset(self):
        return (
            DetalleMenuDiario.objects
            .select_related("producto", "producto__unidad_medida")
            .order_by("curso", "producto__descripcion")
        )

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsStaffOrClienteWeb()]
        return [IsAdminOrReadOnly()]


# ==============================================================================
# REPORTE DE ALMUERZOS
# ==============================================================================

class ReporteAlmuerzosView(APIView):
    """
    GET /api/almuerzos/reportes/?anio=2026&mes=5
    Parámetros opcionales: hijo=<id>, grado=<str>, formato=csv
    Retorna resumen por hijo: cantidad de almuerzos, monto total, pendiente.
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        from django.http import HttpResponse

        anio = request.query_params.get("anio")
        mes = request.query_params.get("mes")
        hijo_id = request.query_params.get("hijo")
        grado = request.query_params.get("grado")

        if not anio or not mes:
            return Response(
                {"error": "Se requieren los parámetros anio y mes."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = CuentaAlmuerzoMensual.objects.filter(
            anio=anio, mes=mes
        ).select_related("hijo__grado")

        if hijo_id:
            qs = qs.filter(hijo_id=hijo_id)
        if grado:
            qs = qs.filter(hijo__grado__nombre__icontains=grado)

        filas = []
        for c in qs.order_by("hijo__apellido", "hijo__nombre"):
            filas.append({
                "hijo_id": c.hijo_id,
                "hijo": c.hijo.nombre_completo,
                "grado": c.hijo.grado.nombre if c.hijo.grado else "",
                "cantidad_almuerzos": c.cantidad_almuerzos,
                "monto_total": int(c.monto_total),
                "monto_pagado": int(c.monto_pagado),
                "monto_pendiente": int(c.monto_total - c.monto_pagado),
                "estado": c.estado,
            })

        totales = {
            "cantidad_almuerzos": sum(f["cantidad_almuerzos"] for f in filas),
            "monto_total": sum(f["monto_total"] for f in filas),
            "monto_pagado": sum(f["monto_pagado"] for f in filas),
            "monto_pendiente": sum(f["monto_pendiente"] for f in filas),
            "alumnos": len(filas),
            "con_deuda": sum(1 for f in filas if f["monto_pendiente"] > 0),
        }

        if request.query_params.get("formato") == "csv":
            resp = HttpResponse(content_type="text/csv; charset=utf-8-sig")
            resp["Content-Disposition"] = (
                f'attachment; filename="almuerzos_{anio}_{mes}.csv"'
            )
            writer = csv.writer(resp)
            writer.writerow(["REPORTE DE ALMUERZOS", f"{mes}/{anio}"])
            writer.writerow([])
            writer.writerow(["Alumno", "Grado", "Almuerzos", "Total (Gs)", "Pagado (Gs)", "Pendiente (Gs)", "Estado"])
            for f in filas:
                writer.writerow([f["hijo"], f["grado"], f["cantidad_almuerzos"],
                                  f["monto_total"], f["monto_pagado"], f["monto_pendiente"], f["estado"]])
            writer.writerow([])
            writer.writerow(["TOTALES", "", totales["cantidad_almuerzos"],
                              totales["monto_total"], totales["monto_pagado"], totales["monto_pendiente"], ""])
            return resp

        return Response({
            "periodo": {"anio": int(anio), "mes": int(mes)},
            "totales": totales,
            "detalle": filas,
        })
