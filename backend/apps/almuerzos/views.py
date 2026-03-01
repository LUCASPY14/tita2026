from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from django.db.models import F
from datetime import datetime
from .models import (
    PlanesAlmuerzo, TiposAlmuerzo, SuscripcionesAlmuerzo, 
    RegistrosConsumoAlmuerzo, Alergenos, CuentasAlmuerzoMensual
)
from .serializers import (
    PlanesAlmuerzoSerializer, TiposAlmuerzoSerializer, SuscripcionesAlmuerzoSerializer, 
    RegistrosConsumoAlmuerzoSerializer, AlergenosSerializer
)


class PlanesAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = PlanesAlmuerzo.objects.all()
    serializer_class = PlanesAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['activo']
    search_fields = ['nombre_plan']


class TiposAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = TiposAlmuerzo.objects.all()
    serializer_class = TiposAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['activo']
    search_fields = ['nombre']


class SuscripcionesAlmuerzoViewSet(viewsets.ModelViewSet):
    queryset = SuscripcionesAlmuerzo.objects.all()
    serializer_class = SuscripcionesAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['estado', 'id_hijo', 'id_plan_almuerzo']
    ordering = ['-fecha_inicio']


class RegistrosConsumoAlmuerzoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para registrar consumos de almuerzo.
    
    IMPORTANTE: Este módulo es INDEPENDIENTE del saldo de cantina.
    - NO descuenta saldo de la tarjeta prepago
    - La facturación es mensual y separada
    - Solo usa la tarjeta para identificación del hijo
    """
    queryset = RegistrosConsumoAlmuerzo.objects.all()
    serializer_class = RegistrosConsumoAlmuerzoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['estado', 'id_hijo', 'fecha_consumo']
    ordering = ['-fecha_consumo']

    def perform_create(self, serializer):
        """
        Registra el consumo de almuerzo sin afectar el saldo de cantina.
        Calcula el costo según suscripción o tipo de almuerzo.
        """
        registro_data = serializer.validated_data
        id_suscripcion = registro_data.get('id_suscripcion')
        id_tipo_almuerzo = registro_data.get('id_tipo_almuerzo')
        
        # Validar que tenga suscripción O tipo de almuerzo
        if not id_suscripcion and not id_tipo_almuerzo:
            raise ValidationError({
                'error': 'Debe especificar una suscripción o un tipo de almuerzo'
            })
        
        # Si tiene suscripción, validar que esté activa
        if id_suscripcion:
            if id_suscripcion.estado != 'activo':
                raise ValidationError({
                    'error': 'La suscripción no está activa',
                    'estado_suscripcion': id_suscripcion.estado,
                    'mensaje': 'Solo se pueden registrar consumos con suscripciones activas'
                })
            
            # Con suscripción activa, el costo es 0 (ya pagado mensualmente)
            costo_calculado = 0
        else:
            # Sin suscripción: se cobra el precio unitario del tipo de almuerzo
            if id_tipo_almuerzo:
                costo_calculado = id_tipo_almuerzo.precio_unitario
            else:
                raise ValidationError({
                    'error': 'Debe especificar el tipo de almuerzo para consumos sin suscripción'
                })
        
        # Guardar el registro con el costo calculado
        with transaction.atomic():
            registro = serializer.save(costo_almuerzo=costo_calculado)
            
            # Si tiene costo, agregar a cuenta mensual del almuerzo
            # NOTA: Esto NO afecta el saldo de la tarjeta de cantina
            if costo_calculado > 0:
                self._agregar_a_cuenta_mensual(registro)
                registro.marcado_en_cuenta = True
                registro.save()

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
                'cantidad_almuerzos': 0,
                'monto_total': 0,
                'monto_pagado': 0,
                'forma_cobro': 'mensual',
                'estado': 'pendiente',
                'fecha_generacion': datetime.now().date(),
                'fecha_actualizacion': datetime.now()
            }
        )
        
        # Actualizar cuenta mensual
        cuenta.cantidad_almuerzos = F('cantidad_almuerzos') + 1
        cuenta.monto_total = F('monto_total') + registro.costo_almuerzo
        cuenta.fecha_actualizacion = datetime.now()
        cuenta.save()
        
        # Refrescar para obtener los valores actualizados
        cuenta.refresh_from_db()


class AlergenosViewSet(viewsets.ModelViewSet):
    queryset = Alergenos.objects.all()
    serializer_class = AlergenosSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['activo', 'nivel_severidad']
    search_fields = ['nombre']
