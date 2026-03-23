from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from django.db.models import F
from datetime import datetime, date
from .models import (
    PlanesAlmuerzo,
    TiposAlmuerzo,
    SuscripcionesAlmuerzo,
    RegistrosConsumoAlmuerzo,
    Alergenos,
    CuentasAlmuerzoMensual,
)
from .serializers import (
    PlanesAlmuerzoSerializer,
    TiposAlmuerzoSerializer,
    SuscripcionesAlmuerzoSerializer,
    RegistrosConsumoAlmuerzoSerializer,
    AlergenosSerializer,
    CuentasAlmuerzoMensualSerializer,
)


class PlanesAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = PlanesAlmuerzo.objects.all()
    serializer_class = PlanesAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["estado"]
    search_fields = ["nombre_plan"]


class TiposAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = TiposAlmuerzo.objects.all()
    serializer_class = TiposAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["estado"]
    search_fields = ["nombre"]


class SuscripcionesAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = SuscripcionesAlmuerzo.objects.all()
    serializer_class = SuscripcionesAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["estado", "id_hijo", "id_plan_almuerzo"]
    ordering = ["-fecha_inicio"]


class RegistrosConsumoAlmuerzoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para registrar consumos de almuerzo.

    REGLA DE NEGOCIO:
    - La tarjeta se usa SOLO como identificación de acceso al comedor.
    - NO se descuenta saldo de la tarjeta (el saldo es exclusivo para la cantina/POS).
    - El costo del almuerzo se acumula en CuentasAlmuerzoMensual para facturación mensual.
    - Máximo 2 registros por alumno por día:
        · Primer registro: ya_cobrado=True (se contabiliza en la cuenta mensual)
        · Segundo registro: ya_cobrado=False, costo=0 (solo operativo, e.g. postre/reingreso)
        · Tercer intento: BLOQUEADO
    """

    queryset = RegistrosConsumoAlmuerzo.objects.select_related("id_hijo").all()
    serializer_class = RegistrosConsumoAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["estado", "id_hijo", "fecha_consumo", "ya_cobrado"]
    search_fields = ["id_hijo__nombre", "id_hijo__apellido", "nro_tarjeta"]
    ordering = ["-fecha_consumo", "-hora_registro"]

    def perform_create(self, serializer):
        """
        Registra el ingreso al almuerzo.

        La tarjeta identifica al alumno pero NO se descuenta saldo.
        El costo se acumula en la cuenta mensual del hijo.
        """
        from .validators import validar_limite_registros_diarios, determinar_si_cobra

        registro_data = serializer.validated_data
        id_hijo = registro_data.get("id_hijo")
        fecha_consumo = registro_data.get("fecha_consumo")
        nro_tarjeta = registro_data.get("nro_tarjeta")
        id_tipo_almuerzo = registro_data.get("id_tipo_almuerzo")
        id_suscripcion = registro_data.get("id_suscripcion")

        # Tarjeta requerida como identificación
        if not nro_tarjeta:
            raise ValidationError(
                {"error": "Debe especificar la tarjeta para registrar el ingreso al almuerzo"}
            )

        # Validar límite de 2 registros por día (lanza excepción si excede)
        validar_limite_registros_diarios(id_hijo, fecha_consumo)

        # Determinar si este registro se contabiliza en cuenta mensual
        debe_contabilizar = determinar_si_cobra(id_hijo, fecha_consumo)

        # Calcular costo según suscripción o tipo de almuerzo (para cuenta mensual)
        if id_suscripcion:
            if id_suscripcion.estado != "Activa":
                raise ValidationError(
                    {
                        "error": "La suscripción no está activa",
                        "estado_suscripcion": id_suscripcion.estado,
                    }
                )
            costo_calculado = id_suscripcion.id_plan_almuerzo.precio_mensual
        elif id_tipo_almuerzo:
            costo_calculado = id_tipo_almuerzo.precio_unitario
        else:
            raise ValidationError(
                {"error": "Debe especificar una suscripción o un tipo de almuerzo"}
            )

        hora_ahora = datetime.now().time()

        with transaction.atomic():
            if debe_contabilizar:
                # Primer ingreso del día: registrar con costo para facturación mensual
                registro = serializer.save(
                    hora_registro=hora_ahora,
                    costo_almuerzo=costo_calculado,
                    ya_cobrado=True,
                    estado="Confirmado",
                )
                self._agregar_a_cuenta_mensual(registro)
            else:
                # Segundo ingreso del día: sin costo (postre, reingreso, etc.)
                registro = serializer.save(
                    hora_registro=hora_ahora,
                    costo_almuerzo=0,
                    ya_cobrado=False,
                    estado="Confirmado",
                )
                self._agregar_a_cuenta_mensual(registro)

    def _agregar_a_cuenta_mensual(self, registro):
        """
        Agrega el consumo a la cuenta mensual de almuerzo del hijo.
        IMPORTANTE: Esta cuenta es INDEPENDIENTE del saldo de cantina.
        """
        fecha = registro.fecha_consumo

        cuenta, created = CuentasAlmuerzoMensual.objects.get_or_create(
            id_hijo=registro.id_hijo,
            anio=fecha.year,
            mes=fecha.month,
            defaults={
                "cantidad_almuerzos": 0,
                "monto_total": 0,
                "monto_pagado": 0,
                "forma_cobro": "mensual",
                "estado": "pendiente",
                "fecha_generacion": datetime.now().date(),
                "fecha_actualizacion": datetime.now(),
            },
        )

        # Actualizar cuenta mensual
        cuenta.cantidad_almuerzos = F("cantidad_almuerzos") + 1
        cuenta.monto_total = F("monto_total") + registro.costo_almuerzo
        cuenta.fecha_actualizacion = datetime.now()
        cuenta.save()

        # Refrescar para obtener los valores actualizados
        cuenta.refresh_from_db()


class AlergenosViewSet(viewsets.ModelViewSet):
    queryset = Alergenos.objects.all()
    serializer_class = AlergenosSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["estado", "nivel_severidad"]
    search_fields = ["nombre"]


class CuentasAlmuerzoMensualViewSet(viewsets.ModelViewSet):
    queryset = CuentasAlmuerzoMensual.objects.select_related("id_hijo").all()
    serializer_class = CuentasAlmuerzoMensualSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["id_hijo", "anio", "mes", "estado"]
    ordering_fields = ["anio", "mes", "monto_total"]
    ordering = ["-anio", "-mes"]
