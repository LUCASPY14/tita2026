from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.core.exceptions import ValidationError as DjangoValidationError
from decimal import Decimal
from .models import Tarjetas, CargasSaldo, ConsumosTarjeta, MediosPago, ConfiguracionSistema
from .serializers import TarjetasSerializer, CargasSaldoSerializer, ConsumosTarjetaSerializer, MediosPagoSerializer, ConfiguracionSistemaSerializer
from .services import RecargaService


class TarjetasViewSet(viewsets.ModelViewSet):
    queryset = Tarjetas.objects.all()
    serializer_class = TarjetasSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'id_hijo']
    search_fields = ['nro_tarjeta', 'codigo_barras']
    ordering_fields = ['fecha_creacion']
    ordering = ['nro_tarjeta']


class CargasSaldoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de recargas de saldo prepago.
    
    Endpoints personalizados:
    - POST /recargas/init/ - Inicia recarga por pasarela Bancard
    - POST /recargas/caja/ - Registra recarga en efectivo/POS
    - POST /recargas/transferencia/referencia/ - Genera código para transferencia
    - POST /recargas/transferencia/validar/ - Valida transferencia bancaria
    - POST /recargas/{id}/aprobar/ - Aprueba recarga (supervisor)
    """
    queryset = CargasSaldo.objects.all()
    serializer_class = CargasSaldoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['estado', 'nro_tarjeta', 'metodo_pago', 'usuario_responsable']
    search_fields = ['referencia', 'codigo_referencia_interno', 'numero_comprobante_externo']
    ordering_fields = ['fecha_carga', 'fecha_confirmacion']
    ordering = ['-fecha_carga']
    
    @action(detail=False, methods=['post'], url_path='caja')
    def recarga_caja(self, request):
        """
        Registra recarga en efectivo o tarjeta POS (cajero).
        
        Body:
        {
            "hijo_id": 123,
            "monto": 100000,
            "metodo_pago": "efectivo",  // o "tarjeta_pos"
            "referencia": "CAJA-001" (opcional)
        }
        """
        try:
            hijo_id = request.data.get('hijo_id')
            monto = Decimal(str(request.data.get('monto')))
            metodo_pago = request.data.get('metodo_pago', 'efectivo')
            referencia = request.data.get('referencia')
            
            # Obtener empleado del request (asumiendo autenticación)
            # empleado_id = request.user.empleado.id_empleado
            # Por ahora, usamos un valor de prueba
            empleado_id = request.data.get('empleado_id', 1)
            
            resultado = RecargaService.procesar_recarga_caja(
                hijo_id=hijo_id,
                monto=monto,
                metodo_pago=metodo_pago,
                empleado_id=empleado_id,
                referencia=referencia
            )
            
            return Response(resultado, status=status.HTTP_201_CREATED)
            
        except (DjangoValidationError, Exception) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], url_path='transferencia/referencia')
    def generar_referencia_transferencia(self, request):
        """
        Genera código de referencia para transferencia bancaria.
        
        Body:
        {
            "hijo_id": 123,
            "monto": 100000
        }
        
        Response:
        {
            "codigo_referencia": "REF-20260302-00001",
            "monto_transferir": 100000,
            "datos_bancarios": {...},
            "instrucciones": "..."
        }
        """
        try:
            hijo_id = request.data.get('hijo_id')
            monto = Decimal(str(request.data.get('monto')))
            
            resultado = RecargaService.iniciar_recarga_transferencia(
                hijo_id=hijo_id,
                monto=monto
            )
            
            return Response(resultado, status=status.HTTP_201_CREATED)
            
        except (DjangoValidationError, Exception) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], url_path='transferencia/validar')
    def validar_transferencia(self, request):
        """
        Valida y registra transferencia bancaria.
        
        Flujo A - Con código de referencia:
        {
            "codigo_referencia": "REF-20260302-00001",
            "numero_comprobante": "COMP-555",
            "empleado_id": 5,
            "imagen_comprobante": "/path/to/image.jpg" (opcional)
        }
        
        Flujo B - Sin código (manual):
        {
            "hijo_id": 123,
            "monto": 103400,
            "numero_comprobante": "COMP-555",
            "empleado_id": 5,
            "imagen_comprobante": "/path/to/image.jpg" (opcional)
        }
        """
        try:
            codigo_referencia = request.data.get('codigo_referencia')
            numero_comprobante = request.data.get('numero_comprobante')
            imagen_path = request.data.get('imagen_comprobante')
            
            # Obtener empleado del request
            # empleado_id = request.user.empleado.id_empleado
            empleado_id = request.data.get('empleado_id', 1)
            
            # Flujo manual (sin código)
            hijo_id = request.data.get('hijo_id')
            monto = Decimal(str(request.data.get('monto'))) if request.data.get('monto') else None
            
            resultado = RecargaService.validar_transferencia(
                codigo_referencia=codigo_referencia,
                numero_comprobante=numero_comprobante,
                empleado_id=empleado_id,
                hijo_id=hijo_id,
                monto=monto,
                imagen_path=imagen_path
            )
            
            return Response(resultado, status=status.HTTP_200_OK)
            
        except (DjangoValidationError, Exception) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], url_path='aprobar')
    def aprobar_supervisor(self, request, pk=None):
        """
        Aprueba recarga pendiente de validación (supervisor).
        
        Body:
        {
            "supervisor_id": 10
        }
        """
        try:
            recarga_id = int(pk)
            
            # Obtener supervisor del request
            # supervisor_id = request.user.empleado.id_empleado
            supervisor_id = request.data.get('supervisor_id', 2)
            
            resultado = RecargaService.aprobar_recarga_supervisor(
                recarga_id=recarga_id,
                supervisor_id=supervisor_id
            )
            
            return Response(resultado, status=status.HTTP_200_OK)
            
        except (DjangoValidationError, Exception) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], url_path='init')
    def iniciar_recarga_bancard(self, request):
        """
        Inicia recarga por pasarela de pago Bancard.
        
        Body:
        {
            "hijo_id": 123,
            "monto": 100000,
            "redirect_url": "https://app.cantinatita.com/recarga/callback"
        }
        
        Response:
        {
            "id_recarga": 456,
            "payment_url": "https://vpos.infonet.com.py/...",
            "total_cobrado": 103400,
            "comision": 3400
        }
        """
        return Response(
            {
                'info': 'Endpoint pendiente de integración con Bancard API',
                'status': 'not_implemented'
            },
            status=status.HTTP_501_NOT_IMPLEMENTED
        )


class ConsumosTarjetaViewSet(viewsets.ModelViewSet):
    queryset = ConsumosTarjeta.objects.all()
    serializer_class = ConsumosTarjetaSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['nro_tarjeta']
    ordering_fields = ['fecha_consumo']
    ordering = ['-fecha_consumo']


class MediosPagoViewSet(viewsets.ModelViewSet):
    queryset = MediosPago.objects.all()
    serializer_class = MediosPagoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['activo']
    search_fields = ['descripcion']


class ConfiguracionSistemaViewSet(viewsets.ModelViewSet):
    queryset = ConfiguracionSistema.objects.all()
    serializer_class = ConfiguracionSistemaSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['tipo', 'categoria']
    search_fields = ['clave', 'descripcion']
