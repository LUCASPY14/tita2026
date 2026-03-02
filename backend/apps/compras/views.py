from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Proveedores, Compras, DetallesCompra, PagosProveedores, NotasCreditoProveedor
from .serializers import ProveedoresSerializer, ComprasSerializer, DetallesCompraSerializer, PagosProveedoresSerializer, NotasCreditoProveedorSerializer
from .services import CompraService


class ProveedoresViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar proveedores.
    
    Incluye acciones para obtener cuenta corriente.
    """
    queryset = Proveedores.objects.all()
    serializer_class = ProveedoresSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['activo', 'ciudad']
    search_fields = ['razon_social', 'ruc', 'email']
    ordering_fields = ['razon_social']
    ordering = ['razon_social']
    
    @action(detail=True, methods=['get'])
    def cuenta_corriente(self, request, pk=None):
        """
        Obtiene el estado de cuenta corriente con el proveedor.
        
        GET /api/proveedores/{id}/cuenta_corriente/
        
        Returns:
            - total_compras: Monto total de compras
            - total_pagado: Monto total pagado
            - saldo_pendiente: Saldo por pagar
            - compras_pendientes: Lista de facturas pendientes
        """
        proveedor = self.get_object()
        
        cuenta = CompraService.obtener_cuenta_corriente_proveedor(
            id_proveedor=proveedor.id_proveedor
        )
        
        # Agregar info del proveedor
        cuenta['proveedor'] = {
            'id': proveedor.id_proveedor,
            'razon_social': proveedor.razon_social,
            'ruc': proveedor.ruc
        }
        
        return Response(cuenta)


class ComprasViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar compras.
    
    Incluye validaciones automáticas y acciones personalizadas para:
    - Confirmar compras
    - Obtener compras pendientes
    - Calcular totales
    """
    queryset = Compras.objects.all()
    serializer_class = ComprasSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado_pago', 'id_proveedor', 'estado']
    search_fields = ['nro_factura_compra', 'id_proveedor__razon_social']
    ordering_fields = ['fecha_compra', 'monto_total']
    ordering = ['-fecha_compra']

    def perform_create(self, serializer):
        """
        Valida la compra antes de crearla.
        
        Validaciones:
        - Detalles deben tener cantidad > 0
        - Detalles deben tener precio > 0
        - No hay productos duplicados
        """
        # Obtener detalles del request
        detalles = self.request.data.get('detalles', [])
        
        if detalles:
            # Validar compra
            validacion = CompraService.validar_compra(detalles)
            
            if not validacion['valido']:
                raise ValidationError({
                    'error': 'La compra contiene errores',
                    'errores': validacion['errores'],
                    'warnings': validacion['warnings']
                })
            
            # Calcular totales
            totales = CompraService.calcular_totales_compra(detalles)
            
            # Guardar con totales calculados
            serializer.save(
                monto_total=totales['total'],
                saldo_pendiente=totales['total'],
                estado='Pendiente'
            )
        else:
            # Sin detalles, guardar como está
            serializer.save(estado='Pendiente')
    
    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        """
        Confirma una compra y actualiza el inventario.
        
        POST /api/compras/{id}/confirmar/
        
        Returns:
            - Compra confirmada
            - Mensaje de éxito
        """
        compra = self.get_object()
        
        # Obtener empleado del request
        empleado = getattr(request.user, 'empleado', None)
        
        if not empleado:
            return Response(
                {'error': 'Usuario no tiene empleado asociado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            compra_confirmada = CompraService.confirmar_compra(
                id_compra=compra.id_compra,
                empleado=empleado
            )
            
            serializer = self.get_serializer(compra_confirmada)
            
            return Response({
                'mensaje': 'Compra confirmada exitosamente',
                'compra': serializer.data
            })
            
        except ValidationError as e:
            return Response(
                e.detail,
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """
        Lista compras pendientes de confirmación.
        
        GET /api/compras/pendientes/
        """
        compras = CompraService.obtener_compras_pendientes_confirmacion()
        serializer = self.get_serializer(compras, many=True)
        
        return Response({
            'count': compras.count(),
            'compras': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def calcular_totales(self, request):
        """
        Calcula los totales de una compra (sin guardarla).
        
        POST /api/compras/calcular_totales/
        Body: {
            "detalles": [
                {"id_producto": 1, "cantidad": 10, "precio_unitario": 5000},
                ...
            ]
        }
        """
        detalles = request.data.get('detalles', [])
        
        if not detalles:
            return Response(
                {'error': 'Debe proporcionar detalles'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar primero
        validacion = CompraService.validar_compra(detalles)
        
        if not validacion['valido']:
            return Response({
                'error': 'La compra contiene errores',
                'errores': validacion['errores'],
                'warnings': validacion['warnings']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calcular totales
        totales = CompraService.calcular_totales_compra(detalles)
        
        return Response({
            'totales': totales,
            'warnings': validacion['warnings']
        })


class DetallesCompraViewSet(viewsets.ModelViewSet):
    queryset = DetallesCompra.objects.all()
    serializer_class = DetallesCompraSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id_compra', 'id_producto']


class PagosProveedoresViewSet(viewsets.ModelViewSet):
    queryset = PagosProveedores.objects.all()
    serializer_class = PagosProveedoresSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['id_medio_pago']
    ordering = ['-fecha_creacion']


class NotasCreditoProveedorViewSet(viewsets.ModelViewSet):
    queryset = NotasCreditoProveedor.objects.all()
    serializer_class = NotasCreditoProveedorSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['estado', 'id_proveedor']
    ordering = ['-fecha']
