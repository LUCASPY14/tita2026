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
    
    @action(detail=False, methods=['post'])
    def generar_qr_sipap(self, request):
        """
        Genera un QR SIPAP para pago de deuda de cliente.
        
        POST /api/v1/cobros/generar_qr_sipap/
        
        Body:
        {
            "id_cliente": 1,
            "monto": 14402000,  // Monto a pagar en Guaraníes (opcional, si no se envía usa total deuda)
            "descripcion": "Pago de 92 facturas"  // Opcional
        }
        
        Response:
        {
            "success": true,
            "qr_data": {
                "qr_image": "data:image/png;base64,...",
                "qr_string": "00020126...",
                "txn_id": "COB-123-1713308400",
                "expira_en": 900,
                "expira_at": "2026-04-16T15:30:00Z",
                "banco": "continental",
                "ambiente": "sandbox"
            },
            "cliente": {
                "id_cliente": 1,
                "nombre_completo": "Juan Garcia",
                "total_deuda": 14402000,
                "cantidad_facturas": 92
            }
        }
        """
        # Validar datos
        id_cliente = request.data.get('id_cliente')
        monto = request.data.get('monto')
        descripcion = request.data.get('descripcion', '')
        
        if not id_cliente:
            return Response(
                {'detail': 'id_cliente es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que el cliente existe
        try:
            cliente = Clientes.objects.get(id_cliente=id_cliente)
        except Clientes.DoesNotExist:
            return Response(
                {'detail': 'Cliente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener facturas pendientes
        facturas_pendientes = Ventas.objects.filter(
            id_cliente=cliente,
            saldo_pendiente__gt=0
        ).order_by('fecha')
        
        total_deuda = sum(f.saldo_pendiente for f in facturas_pendientes)
        
        if total_deuda <= 0:
            return Response(
                {'detail': 'Cliente no tiene deuda pendiente'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Si no se especificó monto, usar total de deuda
        if not monto:
            monto = total_deuda
        else:
            monto = Decimal(str(monto))
        
        # Validar que el monto sea positivo
        if monto <= 0:
            return Response(
                {'detail': 'El monto debe ser mayor a cero'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generar descripción si no se proporcionó
        if not descripcion:
            cantidad_facturas = facturas_pendientes.count()
            if cantidad_facturas == 1:
                descripcion = f"Pago factura #{facturas_pendientes.first().id_venta}"
            else:
                descripcion = f"Pago de {cantidad_facturas} facturas"
        
        # Crear registro temporal de cobro (lo completaremos con el webhook)
        pago_pendiente = PagosClientes.objects.create(
            id_cliente=cliente,
            monto_total=monto,
            estado='Pendiente',
            observaciones=f'QR SIPAP generado - {descripcion}'
        )
        
        # Generar QR SIPAP
        try:
            from apps.api_integrations.services.sipap_service import SIPAPService
            
            sipap = SIPAPService()
            qr_data = sipap.generar_qr_dinamico(
                id_cobro=pago_pendiente.id_pago_cliente,
                monto=monto,
                descripcion=descripcion,
                id_cliente=id_cliente
            )
            
            # Actualizar referencia del pago con el txn_id
            pago_pendiente.referencia = qr_data['txn_id']
            pago_pendiente.save(update_fields=['referencia'])
            
            return Response({
                'success': True,
                'qr_data': qr_data,
                'cliente': {
                    'id_cliente': cliente.id_cliente,
                    'nombre_completo': cliente.nombre_completo,
                    'ruc_ci': cliente.ruc_ci,
                    'total_deuda': float(total_deuda),
                    'cantidad_facturas': facturas_pendientes.count(),
                    'monto_a_pagar': float(monto)
                },
                'id_pago_pendiente': pago_pendiente.id_pago_cliente
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Si falla la generación del QR, eliminar el pago pendiente
            pago_pendiente.delete()
            
            return Response(
                {'detail': f'Error al generar QR SIPAP: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

