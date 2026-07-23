"""
Views para la app almuerzos
"""

import logging
from datetime import date

logger = logging.getLogger(__name__)
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
from apps.usuarios.auditoria import registrar_auditoria

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
        if not (request.user and request.user.is_authenticated and request.user.rol == "ADMIN"):
            return Response(
                {"error": "Solo el Administrador puede eliminar registros de consumo."},
                status=status.HTTP_403_FORBIDDEN,
            )
        registro = self.get_object()
        if registro.estado != RegistroConsumoAlmuerzo.Estado.ANULADO:
            return Response(
                {"error": "Solo se pueden eliminar registros en estado ANULADO. Anulá el registro primero."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            # Revertir el costo de la cuenta mensual si el registro fue cobrado
            if registro.ya_cobrado and registro.costo_almuerzo:
                cuenta = CuentaAlmuerzoMensual.objects.select_for_update().filter(
                    hijo=registro.hijo,
                    anio=registro.fecha_consumo.year,
                    mes=registro.fecha_consumo.month,
                ).first()
                if cuenta:
                    cuenta.cantidad_almuerzos = max(0, cuenta.cantidad_almuerzos - 1)
                    cuenta.monto_total = max(0, cuenta.monto_total - registro.costo_almuerzo)
                    cuenta._calcular_estado()
                    cuenta.save(update_fields=["cantidad_almuerzos", "monto_total", "estado", "fecha_pago"])
            registro.delete()
        registrar_auditoria(
            request=request,
            operacion="ELIMINAR_REGISTRO_ALMUERZO",
            tabla="almuerzos_registroconsumoalmuerzo",
            descripcion=f"Registro ANULADO eliminado — hijo={registro.hijo_id} fecha={registro.fecha_consumo}",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_update(self, serializer):
        registro_anterior = self.get_object()
        estado_anterior = registro_anterior.estado
        registro = serializer.save()

        # Si se anuló un registro que estaba cobrado → descontar de la cuenta mensual
        if (
            estado_anterior == RegistroConsumoAlmuerzo.Estado.REGISTRADO
            and registro.estado == RegistroConsumoAlmuerzo.Estado.ANULADO
            and registro.ya_cobrado
            and registro.costo_almuerzo
        ):
            with transaction.atomic():
                cuenta = CuentaAlmuerzoMensual.objects.select_for_update().filter(
                    hijo=registro.hijo,
                    anio=registro.fecha_consumo.year,
                    mes=registro.fecha_consumo.month,
                ).first()
                if cuenta:
                    cuenta.cantidad_almuerzos = max(0, cuenta.cantidad_almuerzos - 1)
                    cuenta.monto_total = max(0, cuenta.monto_total - registro.costo_almuerzo)
                    cuenta._calcular_estado()
                    cuenta.save(update_fields=["cantidad_almuerzos", "monto_total", "estado", "fecha_pago"])
            registrar_auditoria(
                request=self.request,
                operacion="ANULAR_REGISTRO_ALMUERZO",
                tabla="almuerzos_registroconsumoalmuerzo",
                id_registro=registro.id,
                descripcion=f"Consumo anulado — hijo={registro.hijo_id} fecha={registro.fecha_consumo} costo={registro.costo_almuerzo} Gs.",
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
                from apps.notificaciones.services import whatsapp_cliente
                cliente_resp = registro.hijo.cliente_responsable
                whatsapp_cliente(
                    cliente_resp,
                    f"{registro.hijo.nombre_completo} almuerzo hoy "
                    f"{registro.fecha_consumo.strftime('%d/%m/%Y')}. "
                    f"Costo: Gs. {int(registro.costo_almuerzo):,}."
                )
            except Exception:
                logger.warning("WhatsApp: fallo al notificar almuerzo de %s", registro.hijo.pk, exc_info=True)

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
        # Recalcular estado: monto_total cambió, puede haber salido de PAGADO
        cuenta.refresh_from_db(fields=["monto_total", "monto_pagado", "estado", "fecha_pago"])
        cuenta.actualizar_estado()


# ==============================================================================
# CUENTA ALMUERZO MENSUAL
# ==============================================================================

class CuentaAlmuerzoMensualViewSet(viewsets.ModelViewSet):
    queryset = CuentaAlmuerzoMensual.objects.select_related("hijo__grado", "hijo__tarjeta").all()
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
        nro_factura = (self.request.data.get("nro_factura") or "").strip()
        with transaction.atomic():
            pago = serializer.save(registrado_por=self.request.user)
            cuenta = (
                CuentaAlmuerzoMensual.objects
                .select_for_update()
                .get(pk=pago.cuenta_id)
            )
            cuenta.registrar_pago(pago.monto)
            if nro_factura:
                from apps.contabilidad.services import FacturacionService
                FacturacionService.emitir_para_origen(
                    tipo="PAGO_ALMUERZO",
                    origen_id=pago.id,
                    nro_factura=nro_factura,
                )
        registrar_auditoria(
            request=self.request,
            operacion="PAGO_CUENTA_ALMUERZO",
            tabla="almuerzos_pagocuentaalmuerzo",
            id_registro=pago.id,
            descripcion=f"Pago {pago.monto} Gs. en cuenta almuerzo #{pago.cuenta_id}",
        )


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
            from apps.notificaciones.services import whatsapp_cliente
            hijo = pago.suscripcion.hijo
            cliente_resp = hijo.cliente_responsable
            mes = pago.mes_pagado
            whatsapp_cliente(
                cliente_resp,
                f"Pago de almuerzo confirmado para {hijo.nombre_completo}: "
                f"Gs. {int(pago.monto_pagado):,} correspondiente a "
                f"{mes.strftime('%m/%Y')}. Gracias."
            )
        except Exception:
            logger.warning("WhatsApp: fallo al notificar pago de almuerzo pk=%s", pago.pk, exc_info=True)


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

        tarjeta_filter = request.query_params.get("tarjeta")

        qs = CuentaAlmuerzoMensual.objects.filter(
            anio=anio, mes=mes
        ).select_related("hijo__grado", "hijo__tarjeta")

        if hijo_id:
            qs = qs.filter(hijo_id=hijo_id)
        if grado:
            qs = qs.filter(hijo__grado__nombre__icontains=grado)
        if tarjeta_filter:
            qs = qs.filter(hijo__tarjeta__nro_tarjeta__icontains=tarjeta_filter)

        filas = []
        for c in qs.order_by("hijo__apellido", "hijo__nombre"):
            tarjeta = getattr(c.hijo, "tarjeta", None)
            filas.append({
                "hijo_id": c.hijo_id,
                "hijo": c.hijo.nombre_completo,
                "grado": c.hijo.grado.nombre if c.hijo.grado else "",
                "nro_tarjeta": tarjeta.nro_tarjeta if tarjeta else "",
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
            "filas": filas,
        })


class ReporteConsumoGradoView(APIView):
    """
    GET /api/almuerzos/reporte-consumo-grado/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
    Consumos agrupados por grado: cantidad, tasa de rechazo y distribución horaria.
    Opcional: ?formato=csv
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        from django.http import HttpResponse
        from django.db.models import Count, Sum, Q
        from django.db.models.functions import ExtractHour

        desde = request.query_params.get("desde")
        hasta = request.query_params.get("hasta")
        if not desde or not hasta:
            return Response(
                {"error": "Se requieren los parámetros desde y hasta (YYYY-MM-DD)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        base_qs = RegistroConsumoAlmuerzo.objects.filter(
            fecha_consumo__gte=desde,
            fecha_consumo__lte=hasta,
        )

        # Agrupación por grado
        por_grado_qs = (
            base_qs
            .values(
                "hijo__grado__nombre",
                "hijo__grado__nivel",
                "hijo__grado__orden",
            )
            .annotate(
                n_consumos=Count("id", filter=Q(estado="REGISTRADO")),
                n_rechazados=Count("id", filter=Q(estado="RECHAZADO")),
                n_anulados=Count("id", filter=Q(estado="ANULADO")),
                monto_total=Sum("costo_almuerzo", filter=Q(estado="REGISTRADO")),
            )
            .order_by("hijo__grado__nivel", "hijo__grado__orden")
        )

        por_grado = []
        for r in por_grado_qs:
            total_registros = (r["n_consumos"] or 0) + (r["n_rechazados"] or 0)
            tasa_rechazo = (
                round(r["n_rechazados"] / total_registros * 100, 1)
                if total_registros > 0 else 0.0
            )
            por_grado.append({
                "grado": r["hijo__grado__nombre"] or "Sin grado",
                "nivel": r["hijo__grado__nivel"],
                "n_consumos": r["n_consumos"] or 0,
                "n_rechazados": r["n_rechazados"] or 0,
                "n_anulados": r["n_anulados"] or 0,
                "tasa_rechazo": tasa_rechazo,
                "monto_total": int(r["monto_total"] or 0),
            })

        # Distribución horaria (solo REGISTRADO)
        horas_qs = (
            base_qs
            .filter(estado="REGISTRADO")
            .annotate(hora=ExtractHour("hora_registro"))
            .values("hora")
            .annotate(n=Count("id"))
            .order_by("hora")
        )
        horarios = [{"hora": r["hora"], "n": r["n"]} for r in horas_qs]

        total_consumos = sum(r["n_consumos"] for r in por_grado)
        total_rechazados = sum(r["n_rechazados"] for r in por_grado)
        total_registros = total_consumos + total_rechazados
        tasa_global = round(total_rechazados / total_registros * 100, 1) if total_registros > 0 else 0.0

        if request.query_params.get("formato") == "csv":
            resp = HttpResponse(content_type="text/csv; charset=utf-8-sig")
            resp["Content-Disposition"] = (
                f'attachment; filename="consumo_grado_{desde}_{hasta}.csv"'
            )
            writer = csv.writer(resp)
            writer.writerow(["CONSUMO POR GRADO", f"{desde} al {hasta}"])
            writer.writerow([])
            writer.writerow(["Grado", "Consumos", "Rechazados", "Anulados", "% Rechazo", "Monto (Gs)"])
            for r in por_grado:
                writer.writerow([r["grado"], r["n_consumos"], r["n_rechazados"],
                                  r["n_anulados"], r["tasa_rechazo"], r["monto_total"]])
            writer.writerow([])
            writer.writerow(["Distribución horaria"])
            writer.writerow(["Hora", "Consumos"])
            for h in horarios:
                writer.writerow([f"{h['hora']:02d}:00", h["n"]])
            return resp

        return Response({
            "periodo": {"desde": desde, "hasta": hasta},
            "resumen": {
                "total_consumos": total_consumos,
                "total_rechazados": total_rechazados,
                "tasa_rechazo_global": tasa_global,
            },
            "por_grado": por_grado,
            "horarios_pico": horarios,
        })


class ReporteCobranzaAlmuerzosView(APIView):
    """
    GET /api/almuerzos/reporte-cobranza/?anio=YYYY
    Cobranza mensual de almuerzos: estado por mes, forma de cobro y tendencia de recupero.
    Opcional: ?formato=csv
    """
    permission_classes = [IsStaffUser]

    def get(self, request):
        from django.http import HttpResponse
        from django.db.models import Count, Sum, Q
        import calendar

        anio_raw = request.query_params.get("anio")
        if not anio_raw:
            return Response(
                {"error": "Se requiere el parámetro anio (YYYY)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            anio = int(anio_raw)
        except ValueError:
            return Response({"error": "El parámetro anio debe ser un número."}, status=status.HTTP_400_BAD_REQUEST)

        qs = CuentaAlmuerzoMensual.objects.filter(anio=anio).exclude(estado="ANULADO")

        # Por mes
        por_mes_qs = (
            qs.values("mes")
            .annotate(
                n_alumnos=Count("id"),
                pagados=Count("id", filter=Q(estado="PAGADO")),
                parciales=Count("id", filter=Q(estado="PARCIAL")),
                pendientes=Count("id", filter=Q(estado__in=["PENDIENTE", "VALIDACION"])),
                monto_total=Sum("monto_total"),
                monto_cobrado=Sum("monto_pagado"),
            )
            .order_by("mes")
        )

        MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

        por_mes = []
        for r in por_mes_qs:
            mt = int(r["monto_total"] or 0)
            mc = int(r["monto_cobrado"] or 0)
            tasa = round(mc / mt * 100, 1) if mt > 0 else 0.0
            por_mes.append({
                "mes": r["mes"],
                "mes_nombre": MESES[r["mes"]],
                "n_alumnos": r["n_alumnos"],
                "pagados": r["pagados"],
                "parciales": r["parciales"],
                "pendientes": r["pendientes"],
                "monto_total": mt,
                "monto_cobrado": mc,
                "monto_pendiente": mt - mc,
                "tasa_cobro": tasa,
            })

        # Por forma de cobro
        forma_qs = (
            qs.values("forma_cobro")
            .annotate(
                n_cuentas=Count("id"),
                monto_total=Sum("monto_total"),
                monto_cobrado=Sum("monto_pagado"),
            )
            .order_by("-monto_total")
        )
        por_forma = [
            {
                "forma_cobro": r["forma_cobro"],
                "n_cuentas": r["n_cuentas"],
                "monto_total": int(r["monto_total"] or 0),
                "monto_cobrado": int(r["monto_cobrado"] or 0),
            }
            for r in forma_qs
        ]

        monto_anual = sum(m["monto_total"] for m in por_mes)
        cobrado_anual = sum(m["monto_cobrado"] for m in por_mes)
        tasa_anual = round(cobrado_anual / monto_anual * 100, 1) if monto_anual > 0 else 0.0

        formato = request.query_params.get("formato")

        if formato == "csv":
            resp = HttpResponse(content_type="text/csv; charset=utf-8-sig")
            resp["Content-Disposition"] = (
                f'attachment; filename="cobranza_almuerzos_{anio}.csv"'
            )
            writer = csv.writer(resp)
            writer.writerow(["COBRANZA ALMUERZOS", str(anio)])
            writer.writerow([])
            writer.writerow(["Mes", "Alumnos", "Pagados", "Parciales", "Pendientes",
                              "Monto Total (Gs)", "Cobrado (Gs)", "Pendiente (Gs)", "% Cobro"])
            for m in por_mes:
                writer.writerow([m["mes_nombre"], m["n_alumnos"], m["pagados"],
                                  m["parciales"], m["pendientes"], m["monto_total"],
                                  m["monto_cobrado"], m["monto_pendiente"], m["tasa_cobro"]])
            writer.writerow([])
            writer.writerow(["TOTAL ANUAL", "", "", "", "",
                              monto_anual, cobrado_anual, monto_anual - cobrado_anual, tasa_anual])
            return resp

        if formato == "excel":
            import io
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment

            wb = Workbook()
            ws = wb.active
            ws.title = "Cobranza Almuerzos"

            header_fill = PatternFill("solid", fgColor="1E3A5F")
            header_font = Font(bold=True, color="FFFFFF")
            total_font = Font(bold=True)
            totals_fill = PatternFill("solid", fgColor="E8F0FE")

            ws.append([f"COBRANZA ALMUERZOS — {anio}"])
            ws["A1"].font = Font(bold=True, size=13)
            ws.append([])

            headers = ["Mes", "Alumnos", "Pagados", "Parciales", "Pendientes",
                       "Monto Total (Gs)", "Cobrado (Gs)", "Pendiente (Gs)", "% Cobro"]
            ws.append(headers)
            for cell in ws[ws.max_row]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")

            for m in por_mes:
                ws.append([m["mes_nombre"], m["n_alumnos"], m["pagados"],
                            m["parciales"], m["pendientes"], m["monto_total"],
                            m["monto_cobrado"], m["monto_pendiente"], m["tasa_cobro"]])

            ws.append([])
            total_row = ["TOTAL ANUAL", "", "", "", "",
                         monto_anual, cobrado_anual, monto_anual - cobrado_anual, tasa_anual]
            ws.append(total_row)
            for cell in ws[ws.max_row]:
                cell.font = total_font
                cell.fill = totals_fill

            col_widths = [14, 10, 10, 10, 12, 18, 16, 18, 10]
            for i, w in enumerate(col_widths, 1):
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w

            buf = io.BytesIO()
            wb.save(buf)
            buf.seek(0)
            resp = HttpResponse(
                buf.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            resp["Content-Disposition"] = f'attachment; filename="cobranza_almuerzos_{anio}.xlsx"'
            return resp

        return Response({
            "anio": anio,
            "resumen": {
                "monto_anual": monto_anual,
                "cobrado_anual": cobrado_anual,
                "pendiente_anual": monto_anual - cobrado_anual,
                "tasa_cobro_anual": tasa_anual,
                "meses_con_datos": len(por_mes),
            },
            "por_mes": por_mes,
            "por_forma_cobro": por_forma,
        })
