from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
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
    filterset_fields = ["activo"]
    search_fields = ["nombre_plan"]


class TiposAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = TiposAlmuerzo.objects.all()
    serializer_class = TiposAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["activo"]
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

    REGLA DE NEGOCIO (Nuevo sistema con saldo prepago):
    - Máximo 2 registros por alumno por día
    - Primer registro: desccuenta saldo (ya_cobrado=True)
    - Segundo registro: NO descuenta saldo (ya_cobrado=False, solo operativo)
    - Tercer intento: BLOQUEADO

    El cobro se realiza con saldo prepago de la tarjeta (como cantina).
    La facturación ya fue realizada al recargar la tarjeta.
    """

    queryset = RegistrosConsumoAlmuerzo.objects.all()
    serializer_class = RegistrosConsumoAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["estado", "id_hijo", "fecha_consumo", "ya_cobrado"]
    ordering = ["-fecha_consumo", "-hora_registro"]

    def perform_create(self, serializer):
        """
        Registra el consumo de almuerzo con lógica de doble registro.

        - Valida límite de 2 registros por día
        - Determina si el registro debe generar cobro (ya_cobrado)
        - Descuenta saldo de la tarjeta solo en el primer registro del día
        """
        from .validators import validar_limite_registros_diarios, determinar_si_cobra

        registro_data = serializer.validated_data
        id_hijo = registro_data.get("id_hijo")
        fecha_consumo = registro_data.get("fecha_consumo")
        nro_tarjeta = registro_data.get("nro_tarjeta")
        id_tipo_almuerzo = registro_data.get("id_tipo_almuerzo")
        id_suscripcion = registro_data.get("id_suscripcion")

        # Validar tarjeta presente
        if not nro_tarjeta:
            raise ValidationError(
                {"error": "Debe especificar la tarjeta para registrar el almuerzo"}
            )

        # Validar límite de 2 registros por día (lanza excepción si excede)
        validar_limite_registros_diarios(id_hijo, fecha_consumo)

        # Determinar si este registro debe cobrar
        debe_cobrar = determinar_si_cobra(id_hijo, fecha_consumo)

        # Calcular costo según suscripción o tipo de almuerzo
        if id_suscripcion:
            # Con suscripción: validar que esté activa
            if id_suscripcion.estado != "Activa":
                raise ValidationError(
                    {
                        "error": "La suscripción no está activa",
                        "estado_suscripcion": id_suscripcion.estado,
                    }
                )
            # Suscripción activa: usar precio del plan mensual
            costo_calculado = id_suscripcion.id_plan_almuerzo.precio_mensual / 30  # Aproximado  # pragma: no cover
        elif id_tipo_almuerzo:
            # Sin suscripción: precio unitario
            costo_calculado = id_tipo_almuerzo.precio_unitario
        else:
            raise ValidationError(
                {"error": "Debe especificar una suscripción o un tipo de almuerzo"}
            )

        # Guardar el registro
        with transaction.atomic():
            # Si debe cobrar, descontar saldo de la tarjeta
            if debe_cobrar:
                # Verificar saldo suficiente
                if nro_tarjeta.saldo_actual < costo_calculado:
                    raise ValidationError(
                        {
                            "error": "Saldo insuficiente en la tarjeta",
                            "saldo_actual": float(nro_tarjeta.saldo_actual),
                            "costo_almuerzo": float(costo_calculado),
                            "faltante": float(costo_calculado - nro_tarjeta.saldo_actual),
                        }
                    )

                # Descontar saldo
                nro_tarjeta.saldo_actual = F("saldo_actual") - costo_calculado
                nro_tarjeta.save(update_fields=["saldo_actual"])
                nro_tarjeta.refresh_from_db()

                # Guardar registro con ya_cobrado=True
                registro = serializer.save(
                    costo_almuerzo=costo_calculado, ya_cobrado=True, estado="Confirmado"
                )

                # Actualizar cuenta mensual
                self._agregar_a_cuenta_mensual(registro)

                # Registrar movimiento en historial de tarjeta
                from apps.core.models import ConsumosTarjeta
                saldo_anterior = nro_tarjeta.saldo_actual + costo_calculado
                ConsumosTarjeta.objects.create(
                    fecha_consumo=timezone.now(),
                    monto_consumido=costo_calculado,
                    detalle=f"Almuerzo registrado (ID {registro.pk})",
                    saldo_anterior=saldo_anterior,
                    saldo_posterior=nro_tarjeta.saldo_actual,
                    nro_tarjeta=nro_tarjeta,
                )

            else:
                # Segundo registro del día: NO cobrar
                registro = serializer.save(
                    costo_almuerzo=0,  # No genera costo
                    ya_cobrado=False,  # Marcado como NO cobrado
                    estado="Confirmado",
                )
                registro.save()

                # Actualizar cuenta mensual (aunque sea con costo 0)
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
    filterset_fields = ["activo", "nivel_severidad"]
    search_fields = ["nombre"]


class CuentasAlmuerzoMensualViewSet(viewsets.ModelViewSet):
    queryset = CuentasAlmuerzoMensual.objects.select_related("id_hijo").all()
    serializer_class = CuentasAlmuerzoMensualSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["id_hijo", "anio", "mes", "estado"]
    ordering_fields = ["anio", "mes", "monto_total"]
    ordering = ["-anio", "-mes"]
