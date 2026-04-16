"""
Views para el módulo de cobros.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from decimal import Decimal

from .models import PagosClientes, AplicacionPagosClientes
from .serializers import (
    PagosClientesSerializer,
    RegistrarPagoSerializer,
    FacturaPendienteSerializer
)
from apps.clientes.models import Clientes
from apps.ventas.models import Ventas
from apps.usuarios.models import Empleados


class PagosClientesViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar pagos de clientes.
    
    Endpoints:
    - GET /cobros/ - Lista de pagos
    - POST /cobros/ - Registrar nuevo pago (usar /cobros/registrar_pago/)
    - GET /cobros/{id}/ - Detalle de un pago
    - GET /cobros/facturas_pendientes/?id_cliente=X - Lista facturas pendientes
    - POST /cobros/registrar_pago/ - Registrar pago con aplicaciones
    """
    
    queryset = PagosClientes.objects.all()
    serializer_class = PagosClientesSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id_cliente', 'estado', 'id_medio_pago']
    
    @action(detail=False, methods=['get'])
    def facturas_pendientes(self, request):
        """
        Lista las facturas pendientes de un cliente.
        
        Query params:
        - id_cliente: ID del cliente (requerido)
        
        GET /api/v1/cobros/facturas_pendientes/?id_cliente=1
        """
        id_cliente = request.query_params.get('id_cliente')
        
        if not id_cliente:
            return Response(
                {'detail': 'Parámetro id_cliente es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cliente = Clientes.objects.get(id_cliente=id_cliente)
        except Clientes.DoesNotExist:
            return Response(
                {'detail': 'Cliente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener facturas con saldo pendiente
        facturas = Ventas.objects.filter(
            id_cliente=cliente,
            saldo_pendiente__gt=0
        ).order_by('fecha')
        
        serializer = FacturaPendienteSerializer(facturas, many=True)
        
        # Agregar resumen
        total_pendiente = sum(f.saldo_pendiente for f in facturas)
        
        return Response({
            'cliente': {
                'id_cliente': cliente.id_cliente,
                'nombre_completo': cliente.nombre_completo,
                'ruc_ci': cliente.ruc_ci,
                'limite_credito': cliente.limite_credito,
                'credito_disponible': cliente.credito_disponible
            },
            'facturas': serializer.data,
            'resumen': {
                'cantidad_facturas': facturas.count(),
                'total_pendiente': total_pendiente
            }
        })
    
    @action(detail=False, methods=['post'])
    @transaction.atomic
    def registrar_pago(self, request):
        """
        Registra un pago de cliente con aplicación a facturas.
        
        POST /api/v1/cobros/registrar_pago/
        
        Body:
        {
            "id_cliente": 1,
            "monto_total": 500000,
            "id_medio_pago": 1,
            "referencia": "TRANSFERENCIA-12345",
            "banco_emisor": "Banco Nacional",
            "observaciones": "Pago parcial",
            "aplicaciones": [
                {"id_venta": 101, "monto_aplicado": 250000},
                {"id_venta": 102, "monto_aplicado": 250000}
            ]
        }
        """
        serializer = RegistrarPagoSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        # Obtener el empleado cajero actual (del request.user)
        try:
            empleado = Empleados.objects.get(email=request.user.email)
        except Empleados.DoesNotExist:
            return Response(
                {'detail': 'Usuario no tiene empleado asociado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear el pago
        pago = PagosClientes.objects.create(
            id_cliente_id=data['id_cliente'],
            monto_total=data['monto_total'],
            id_medio_pago_id=data['id_medio_pago'],
            referencia=data.get('referencia', ''),
            banco_emisor=data.get('banco_emisor', ''),
            observaciones=data.get('observaciones', ''),
            id_empleado_cajero=empleado,
            estado='Confirmado'
        )
        
        # Aplicar a facturas
        aplicaciones = data.get('aplicaciones', [])
        
        if not aplicaciones:
            # Si no hay aplicaciones específicas, aplicar automáticamente (FIFO)
            aplicaciones = self._aplicar_automatico(
                data['id_cliente'],
                data['monto_total']
            )
        
        # Crear aplicaciones y actualizar saldos
        for app_data in aplicaciones:
            venta = Ventas.objects.select_for_update().get(
                id_venta=app_data['id_venta']
            )
            monto_aplicado = Decimal(str(app_data['monto_aplicado']))
            
            # Crear aplicación
            AplicacionPagosClientes.objects.create(
                id_pago_cliente=pago,
                id_venta=venta,
                monto_aplicado=monto_aplicado
            )
            
            # Actualizar saldo de la venta
            venta.saldo_pendiente -= monto_aplicado
            if venta.saldo_pendiente < Decimal('0.01'):
                venta.saldo_pendiente = Decimal('0.00')
                venta.estado_pago = 'pagada'
            venta.save(update_fields=['saldo_pendiente', 'estado_pago'])
        
        # Serializar respuesta
        response_serializer = PagosClientesSerializer(pago)
        
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    def _aplicar_automatico(self, id_cliente, monto_total):
        """
        Aplica el pago automáticamente a las facturas más antiguas (FIFO).
        """
        aplicaciones = []
        monto_restante = Decimal(str(monto_total))
        
        # Obtener facturas pendientes ordenadas por fecha
        facturas = Ventas.objects.filter(
            id_cliente_id=id_cliente,
            saldo_pendiente__gt=0
        ).order_by('fecha')
        
        for factura in facturas:
            if monto_restante <= 0:
                break
            
            # Aplicar lo que se pueda a esta factura
            monto_a_aplicar = min(monto_restante, factura.saldo_pendiente)
            
            aplicaciones.append({
                'id_venta': factura.id_venta,
                'monto_aplicado': float(monto_a_aplicar)
            })
            
            monto_restante -= monto_a_aplicar
        
        return aplicaciones
