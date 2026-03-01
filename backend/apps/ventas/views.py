from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from django.db import models
from django.utils import timezone
from decimal import Decimal
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

    def _calcular_comision(self, medio_pago, monto_base):
        """
        Calcula la comisión según el medio de pago y tarifa vigente.
        
        Args:
            medio_pago: Instancia de MediosPago
            monto_base: Monto de la venta (sin comisión)
        
        Returns:
            tuple: (monto_comision, tarifa_aplicada)
            
        Ejemplo:
            >>> medio_pago = MediosPago('Tarjeta Débito Bancard')
            >>> comision, tarifa = _calcular_comision(medio_pago, Decimal('10000'))
            >>> print(comision)  # 340.00 (3.4%)
        """
        from apps.contabilidad.models import TarifasComision
        
        # Si no genera comisión, retornar 0
        if not medio_pago.genera_comision:
            return Decimal('0.00'), None
        
        # Buscar tarifa vigente
        now = timezone.now()
        tarifa = TarifasComision.objects.filter(
            id_medio_pago=medio_pago,
            activo=True,
            fecha_inicio_vigencia__lte=now
        ).filter(
            models.Q(fecha_fin_vigencia__isnull=True) | 
            models.Q(fecha_fin_vigencia__gte=now)
        ).order_by('-fecha_inicio_vigencia').first()
        
        if not tarifa:
            # No hay tarifa configurada
            return Decimal('0.00'), None
        
        # Calcular comisión porcentual
        comision = monto_base * tarifa.porcentaje_comision
        
        # Agregar monto fijo si existe
        if tarifa.monto_fijo_comision:
            comision += tarifa.monto_fijo_comision
        
        # Redondear a 2 decimales
        return comision.quantize(Decimal('0.01')), tarifa
    
    def _registrar_pago_con_comision(self, venta, medio_pago, monto_base):
        """
        Registra el pago con comisión separada.
        
        Reglas Bancard:
        - La factura solo incluye el monto base (productos)
        - La comisión es un recargo aparte (trasladado al cliente)
        - No afecta la base imponible para IVA
        - Se registra en MovimientosCaja como conceptos separados
        
        Args:
            venta: Instancia de Ventas
            medio_pago: Instancia de MediosPago
            monto_base: Monto de productos (sin comisión)
            
        Returns:
            PagosVenta: Instancia del pago creado
        """
        from apps.contabilidad.models import MovimientosCaja
        
        # Calcular comisión
        monto_comision, tarifa = self._calcular_comision(medio_pago, monto_base)
        
        # Crear registro de pago
        pago = PagosVenta.objects.create(
            monto=monto_base,
            monto_comision=monto_comision,
            fecha_pago=timezone.now(),
            estado='confirmado',
            id_medio_pago=medio_pago,
            id_venta=venta,
            referencia_transaccion=f"POS-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        )
        
        # Registrar en MovimientosCaja
        # Movimiento 1: Ingreso por venta de productos
        MovimientosCaja.objects.create(
            tipo_movimiento='ingreso',
            monto=monto_base,
            monto_comision=Decimal('0.00'),
            fecha_movimiento=timezone.now(),
            descripcion=f"Venta #{venta.id_venta} - Productos",
            id_medio_pago=medio_pago,
            id_venta=venta,
            id_cierre=None  # Se asigna al cerrar caja
        )
        
        # Movimiento 2: Ingreso por recargo POS (si aplica)
        if monto_comision > 0 and tarifa:
            MovimientosCaja.objects.create(
                tipo_movimiento='ingreso',
                monto=Decimal('0.00'),
                monto_comision=monto_comision,
                fecha_movimiento=timezone.now(),
                descripcion=f"Venta #{venta.id_venta} - Recargo POS ({tarifa.porcentaje_comision * 100}%)",
                id_medio_pago=medio_pago,
                id_venta=venta,
                id_cierre=None
            )
        
        return pago

    def perform_create(self, serializer):
        """
        Valida saldo de tarjeta antes de crear venta.
        Calcula y registra comisión según medio de pago.
        Valida límite de crédito para ventas a crédito.
        
        Aplica las reglas de negocio:
        - NO permite saldo negativo sin autorización (tarjetas)
        - Descuenta el saldo de la tarjeta del hijo
        - Registra el consumo en ConsumosTarjeta
        - Calcula comisión POS Bancard (si aplica)
        - Separa monto facturado vs recargo POS
        - Valida límite de crédito para ventas a crédito
        """
        venta_data = serializer.validated_data
        id_hijo = venta_data.get('id_hijo')
        id_cliente = venta_data.get('id_cliente')
        monto_total = venta_data.get('monto_total')
        id_medio_pago = venta_data.get('id_medio_pago')
        tipo_venta = venta_data.get('tipo_venta', 'Contado')
        autorizado_por = venta_data.get('autorizado_por')
        
        # VALIDACIÓN 1: Límite de crédito para ventas a crédito
        if tipo_venta and tipo_venta.lower() == 'crédito':
            from apps.clientes.models import Clientes
            
            try:
                cliente = Clientes.objects.get(id_cliente=id_cliente.id_cliente)
                
                # Verificar si tiene límite de crédito configurado
                if not cliente.limite_credito or cliente.limite_credito == 0:
                    raise ValidationError({
                        'error': 'Cliente no tiene límite de crédito configurado',
                        'cliente': cliente.nombre_completo,
                        'ruc_ci': cliente.ruc_ci,
                        'mensaje': 'Este cliente no puede realizar compras a crédito. Configure un límite de crédito primero.'
                    })
                
                # Calcular crédito disponible
                credito_usado = cliente.credito_utilizado
                credito_disponible = cliente.credito_disponible
                
                # Validar si hay crédito suficiente
                if monto_total > credito_disponible:
                    # Si tiene autorización de supervisor, permitir
                    if not autorizado_por:
                        raise ValidationError({
                            'error': 'Excede el límite de crédito del cliente',
                            'cliente': cliente.nombre_completo,
                            'limite_credito': str(cliente.limite_credito),
                            'credito_usado': str(credito_usado),
                            'credito_disponible': str(credito_disponible),
                            'monto_solicitado': str(monto_total),
                            'excedente': str(monto_total - credito_disponible),
                            'requiere_autorizacion': True,
                            'mensaje': 'Se requiere autorización de supervisor para exceder el límite de crédito'
                        })
                
                # Si está autorizado, inicializar saldo_pendiente
                venta_data['saldo_pendiente'] = monto_total
                venta_data['estado_pago'] = 'Pendiente'
                
            except Clientes.DoesNotExist:
                raise ValidationError({
                    'error': 'Cliente no encontrado',
                    'id_cliente': id_cliente
                })
        
        # VALIDACIÓN 2: Saldo de tarjeta (para compras con tarjeta de hijo)
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
                    
                    # Registrar pago con comisión (si tiene medio de pago)
                    if id_medio_pago:
                        self._registrar_pago_con_comision(venta_obj, id_medio_pago, monto_total)
                
            except Tarjetas.DoesNotExist:
                raise ValidationError({
                    'error': 'El hijo no tiene tarjeta asociada',
                    'id_hijo': id_hijo
                })
        else:
            # Venta sin tarjeta (pago directo)
            with transaction.atomic():
                venta_obj = serializer.save()
                
                # Registrar pago con comisión (si tiene medio de pago)
                if id_medio_pago:
                    self._registrar_pago_con_comision(venta_obj, id_medio_pago, monto_total)

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
