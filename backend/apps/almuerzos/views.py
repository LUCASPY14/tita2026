"""
Views para la app almuerzos
"""

from datetime import date, datetime
from decimal import Decimal

from django.db import models, transaction
from django.db.models import F

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    PrecioAlmuerzo,
    TipoAlmuerzo,
    PlanAlmuerzo,
    SuscripcionAlmuerzo,
    RegistroConsumoAlmuerzo,
    CuentaAlmuerzoMensual,
    PagoCuentaAlmuerzo,
    PagoAlmuerzoMensual,
    Alergeno,
    ProductoAlergeno,
)
from .serializers import (
    PrecioAlmuerzoSerializer,
    TipoAlmuerzoSerializer,
    PlanAlmuerzoSerializer,
    SuscripcionAlmuerzoSerializer,
    RegistroConsumoAlmuerzoSerializer,
    CuentaAlmuerzoMensualSerializer,
    PagoCuentaAlmuerzoSerializer,
    PagoAlmuerzoMensualSerializer,
    AlergenoSerializer,
    ProductoAlergenoSerializer,
)
from .validators import validar_limite_registros_diarios


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
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["activo"]
    ordering = ["-fecha_inicio_vigencia"]

    @action(detail=False, methods=["get"], url_path="precio-actual")
    def precio_actual(self, request):
        precio = get_precio_almuerzo_activo()
        if precio:
            return Response(PrecioAlmuerzoSerializer(precio).data)
        return Response({
            "precio_unitario": 25000,
            "mensaje": "Sin precio configurado - usando valor predeterminado"
        })


# ==============================================================================
# TIPO ALMUERZO
# ==============================================================================

class TipoAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = TipoAlmuerzo.objects.all()
    serializer_class = TipoAlmuerzoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["activo"]
    search_fields = ["nombre"]


# ==============================================================================
# PLAN ALMUERZO
# ==============================================================================

class PlanAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = PlanAlmuerzo.objects.all()
    serializer_class = PlanAlmuerzoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["activo", "tipo"]
    search_fields = ["nombre"]


# ==============================================================================
# SUSCRIPCION ALMUERZO
# ==============================================================================

class SuscripcionAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = SuscripcionAlmuerzo.objects.select_related("hijo", "plan").all()
    serializer_class = SuscripcionAlmuerzoSerializer
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado", "hijo", "fecha_consumo", "ya_cobrado"]
    search_fields = ["hijo__nombre", "hijo__apellido"]
    ordering = ["-fecha_consumo", "-hora_registro"]

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
            )
            if es_primer_registro:
                self._agregar_a_cuenta_mensual(registro)

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

        cuenta.cantidad_almuerzos = F("cantidad_almuerzos") + 1
        cuenta.monto_total = F("monto_total") + registro.costo_almuerzo
        cuenta.save()
        cuenta.refresh_from_db()


# ==============================================================================
# CUENTA ALMUERZO MENSUAL
# ==============================================================================

class CuentaAlmuerzoMensualViewSet(viewsets.ModelViewSet):
    queryset = CuentaAlmuerzoMensual.objects.select_related("hijo").all()
    serializer_class = CuentaAlmuerzoMensualSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["hijo", "anio", "mes", "estado"]
    ordering = ["-anio", "-mes"]


# ==============================================================================
# PAGO CUENTA ALMUERZO
# ==============================================================================

class PagoCuentaAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = PagoCuentaAlmuerzo.objects.select_related("cuenta").all()
    serializer_class = PagoCuentaAlmuerzoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["cuenta"]
    ordering = ["-fecha_pago"]

    def perform_create(self, serializer):
        with transaction.atomic():
            pago = serializer.save()
            cuenta = pago.cuenta
            cuenta.monto_pagado = F("monto_pagado") + pago.monto
            if cuenta.monto_pagado + pago.monto >= cuenta.monto_total:
                cuenta.estado = CuentaAlmuerzoMensual.Estado.PAGADO
            elif cuenta.monto_pagado + pago.monto > 0:
                cuenta.estado = CuentaAlmuerzoMensual.Estado.PARCIAL
            cuenta.save()


# ==============================================================================
# PAGO ALMUERZO MENSUAL
# ==============================================================================

class PagoAlmuerzoMensualViewSet(viewsets.ModelViewSet):
    queryset = PagoAlmuerzoMensual.objects.select_related("suscripcion").all()
    serializer_class = PagoAlmuerzoMensualSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["suscripcion", "estado"]
    ordering = ["-fecha_pago"]


# ==============================================================================
# ALERGENO
# ==============================================================================

class AlergenoViewSet(viewsets.ModelViewSet):
    queryset = Alergeno.objects.all()
    serializer_class = AlergenoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["activo", "severidad"]
    search_fields = ["nombre"]


# ==============================================================================
# PRODUCTO ALERGENO
# ==============================================================================

class ProductoAlergenoViewSet(viewsets.ModelViewSet):
    queryset = ProductoAlergeno.objects.select_related("producto", "alergeno").all()
    serializer_class = ProductoAlergenoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["producto", "alergeno", "contiene"]