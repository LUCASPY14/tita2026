from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from apps.common.permissions import CanManageVentas, IsAdminOrReadOnly
from apps.common.throttling import VentasRateThrottle, BurstRateThrottle
from .models import Ventas, DetallesVenta, PagosVenta, NotasCreditoCliente, Promociones
from .serializers import VentasSerializer, DetallesVentaSerializer, PagosVentaSerializer, NotasCreditoClienteSerializer, PromocionesSerializer


class VentasViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar ventas.
    
    Permisos:
    - Admin, Gerentes y Cajeros: Acceso total
    - Otros: Sin acceso
    """
    queryset = Ventas.objects.all()
    serializer_class = VentasSerializer
    permission_classes = [IsAuthenticated, CanManageVentas]
    throttle_classes = [VentasRateThrottle, BurstRateThrottle]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado_pago', 'estado', 'tipo_venta', 'id_cliente', 'fecha']
    search_fields = ['nro_factura_venta', 'id_cliente__nombres', 'id_cliente__apellidos']
    ordering_fields = ['fecha', 'monto_total']
    ordering = ['-fecha']

    def perform_create(self, serializer):
        """
        Valida saldo de tarjeta antes de crear venta.
        Aplica las reglas de negocio:
        - NO permite saldo negativo sin autorización
        - Descuenta el saldo de la tarjeta del hijo
        - Registra el consumo en ConsumosTarjeta
        """
        venta_data = serializer.validated_data
        id_hijo = venta_data.get('id_hijo')
        monto_total = venta_data.get('monto_total')
        
        # Solo validar si la venta está asociada a un hijo (compra con tarjeta)
        if id_hijo:
            from apps.core.models import Tarjetas
            
            try:
                tarjeta = Tarjetas.objects.select_for_update().get(id_hijo=id_hijo)
                
                # Validar saldo disponible
                if tarjeta.saldo_actual < monto_total:
                    if not tarjeta.permite_saldo_negativo:
                        raise ValidationError({
                            'error': 'Saldo insuficiente en la tarjeta',
                            'saldo_actual': str(tarjeta.saldo_actual),
                            'monto_requerido': str(monto_total),
                            'faltante': str(monto_total - tarjeta.saldo_actual),
                            'requiere_autorizacion': True,
                            'mensaje': 'Se requiere autorización con tarjeta de supervisor para permitir saldo negativo'
                        })
                    else:
                        # Validar límite de crédito
                        saldo_negativo_proyectado = monto_total - tarjeta.saldo_actual
                        if saldo_negativo_proyectado > tarjeta.limite_credito:
                            raise ValidationError({
                                'error': 'Excede el límite de crédito permitido',
                                'limite_credito': str(tarjeta.limite_credito),
                                'saldo_negativo_proyectado': str(saldo_negativo_proyectado),
                                'excedente': str(saldo_negativo_proyectado - tarjeta.limite_credito)
                            })
                
                # Guardar venta y descontar saldo en transacción atómica
                with transaction.atomic():
                    venta_obj = serializer.save()
                    self._descontar_saldo_tarjeta(tarjeta, monto_total, venta_obj)
                
            except Tarjetas.DoesNotExist:
                raise ValidationError({
                    'error': 'El hijo no tiene tarjeta asociada',
                    'id_hijo': id_hijo
                })
        else:
            # Venta sin tarjeta (pago directo)
            venta_obj = serializer.save()

    def _descontar_saldo_tarjeta(self, tarjeta, monto, venta):
        """
        Descuenta el saldo de la tarjeta y registra el consumo.
        Este método garantiza la integridad transaccional.
        """
        from apps.core.models import ConsumosTarjeta
        from django.utils import timezone
        
        # Registrar saldo anterior
        saldo_anterior = tarjeta.saldo_actual
        
        # Descontar saldo
        tarjeta.saldo_actual -= monto
        tarjeta.save()
        
        # Registrar consumo en historial
        ConsumosTarjeta.objects.create(
            nro_tarjeta=tarjeta,
            fecha_consumo=venta.fecha,
            monto_consumido=monto,
            detalle=f"Venta #{venta.id_venta} - Cantina",
            saldo_anterior=saldo_anterior,
            saldo_posterior=tarjeta.saldo_actual,
            id_empleado_registro=venta.id_empleado_cajero
        )


class DetallesVentaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para detalles de venta.
    """
    queryset = DetallesVenta.objects.all()
    serializer_class = DetallesVentaSerializer
    permission_classes = [IsAuthenticated, CanManageVentas]
    throttle_classes = [VentasRateThrottle]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id_venta', 'id_producto']


class PagosVentaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar pagos de ventas.
    """
    queryset = PagosVenta.objects.all()
    serializer_class = PagosVentaSerializer
    permission_classes = [IsAuthenticated, CanManageVentas]
    throttle_classes = [VentasRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['estado', 'id_venta', 'id_medio_pago']
    ordering_fields = ['fecha_pago']
    ordering = ['-fecha_pago']


class NotasCreditoClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar notas de crédito.
    """
    queryset = NotasCreditoCliente.objects.all()
    serializer_class = NotasCreditoClienteSerializer
    permission_classes = [IsAuthenticated, CanManageVentas]
    throttle_classes = [BurstRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['estado', 'id_cliente']
    ordering = ['-fecha_emision']


class PromocionesViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar promociones.
    
    Permisos:
    - Admin: CRUD completo
    - Otros autenticados: Solo lectura
    """
    queryset = Promociones.objects.all()
    serializer_class = PromocionesSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    throttle_classes = [BurstRateThrottle]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['activo', 'tipo_promocion']
    search_fields = ['nombre', 'codigo_promocion']
