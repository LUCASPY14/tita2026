"""
Servicios de autorización y control de límites
Lógica centralizada para verificar autorizaciones de operaciones
"""
from django.core.exceptions import ValidationError
from decimal import Decimal
from typing import Dict

from .models import LimitesTransaccion, RegistroAutorizaciones


class AutorizacionService:
    """
    Servicio centralizado para validar autorizaciones de operaciones.
    
    Uso:
        # En VentasViewSet.perform_create():
        validacion = AutorizacionService.validar_operacion(
            empleado=request.user.empleado,
            tipo_operacion='venta',
            monto=monto_total,
            autorizador=request.data.get('autorizado_por')
        )
        
        if validacion['requiere_autorizacion'] and not validacion['autorizado']:
            raise ValidationError(validacion)
    """
    
    @staticmethod
    def validar_operacion(empleado, tipo_operacion: str, monto: Decimal, 
                         autorizador=None, autorizador_2=None, motivo: str = None) -> Dict:
        """
        Valida si una operación puede ejecutarse o requiere autorización.
        
        Args:
            empleado: Empleado que intenta realizar la operación
            tipo_operacion: 'venta', 'descuento', 'nota_credito_cliente', etc.
            monto: Monto de la operación
            autorizador: Empleado que autoriza (opcional)
            autorizador_2: Segundo autorizador (para doble autorización)
            motivo: Justificación de la autorización
        
        Returns:
            dict con:
                - puede_ejecutar: bool
                - requiere_autorizacion: bool
                - autorizado: bool
                - limite: Decimal o None
                - mensaje: str
                - errores: lista de errores
        
        Raises:
            ValidationError: Si la autorización es inválida
        """
        errores = []
        
        # Obtener rol del empleado
        if not hasattr(empleado, 'id_rol') or not empleado.id_rol:
            raise ValidationError({
                'error': 'El empleado no tiene rol asignado',
                'empleado': str(empleado)
            })
        
        rol = empleado.id_rol
        
        # Verificar si existe límite configurado para este rol
        verificacion = LimitesTransaccion.requiere_autorizacion(
            rol=rol,
            tipo_operacion=tipo_operacion,
            monto=monto
        )
        
        # Si no requiere autorización, permitir
        if not verificacion['requiere']:
            return {
                'puede_ejecutar': True,
                'requiere_autorizacion': False,
                'autorizado': True,
                'limite': verificacion['limite'],
                'mensaje': 'Operación dentro del límite permitido',
                'errores': []
            }
        
        # Requiere autorización
        autorizado = False
        
        # Validar que se proporcionó autorizador
        if not autorizador:
            return {
                'puede_ejecutar': False,
                'requiere_autorizacion': True,
                'autorizado': False,
                'limite': verificacion['limite'],
                'excedente': verificacion['excedente'],
                'mensaje': f'Se requiere autorización de supervisor. El monto excede el límite de Gs. {verificacion["limite"]:,.0f}',
                'doble_autorizacion': verificacion['doble_autorizacion'],
                'errores': ['Debe proporcionar autorizador']
            }
        
        # Validar que autorizador no sea el mismo que solicitante
        if autorizador.id_empleado == empleado.id_empleado:
            errores.append('El autorizador no puede ser el mismo que realiza la operación')
        
        # Validar que autorizador tenga rol con permisos suficientes
        limite_obj = LimitesTransaccion.obtener_limite(rol, tipo_operacion)
        
        if limite_obj and limite_obj.roles_autorizadores.exists():
            # Hay roles específicos configurados
            if autorizador.id_rol not in limite_obj.roles_autorizadores.all():
                errores.append(
                    f'El rol {autorizador.id_rol.nombre_rol} no puede autorizar esta operación'
                )
        
        # Si requiere doble autorización
        if verificacion['doble_autorizacion']:
            if not autorizador_2:
                errores.append('Esta operación requiere autorización de dos supervisores')
            elif autorizador_2.id_empleado == empleado.id_empleado:
                errores.append('El segundo autorizador no puede ser el solicitante')
            elif autorizador_2.id_empleado == autorizador.id_empleado:
                errores.append('Los dos autorizadores deben ser diferentes')
        
        # Si no hay errores, está autorizado
        autorizado = len(errores) == 0
        
        return {
            'puede_ejecutar': autorizado,
            'requiere_autorizacion': True,
            'autorizado': autorizado,
            'limite': verificacion['limite'],
            'excedente': verificacion['excedente'],
            'mensaje': 'Autorización válida' if autorizado else 'Autorización inválida',
            'doble_autorizacion': verificacion['doble_autorizacion'],
            'errores': errores
        }
    
    @staticmethod
    def registrar_autorizacion(tipo_operacion: str, monto: Decimal, 
                               solicitante, autorizador, motivo: str,
                               autorizador_2=None, ip_address: str = None,
                               id_venta=None, id_compra=None, id_ajuste=None) -> RegistroAutorizaciones:
        """
        Registra una autorización en el sistema para auditoría.
        
        Args:
            tipo_operacion: Tipo de operación autorizada
            monto: Monto de la operación
            solicitante: Empleado que solicitó
            autorizador: Empleado que autorizó
            motivo: Justificación
            autorizador_2: Segundo autorizador (opcional)
            ip_address: IP desde donde se autorizó
            id_venta: ID de venta relacionada (opcional)
            id_compra: ID de compra relacionada (opcional)
            id_ajuste: ID de ajuste relacionado (opcional)
        
        Returns:
            RegistroAutorizaciones: Registro creado
        """
        return RegistroAutorizaciones.objects.create(
            tipo_operacion=tipo_operacion,
            monto=monto,
            motivo=motivo or 'Sin justificación específica',
            id_empleado_solicitante=solicitante,
            id_empleado_autorizador=autorizador,
            id_empleado_autorizador_2=autorizador_2,
            ip_address=ip_address,
            id_venta=id_venta,
            id_compra=id_compra,
            id_ajuste=id_ajuste
        )
    
    @staticmethod
    def obtener_historial_autorizaciones(empleado=None, tipo_operacion=None, 
                                         fecha_desde=None, fecha_hasta=None) -> list:
        """
        Obtiene historial de autorizaciones con filtros opcionales.
        
        Args:
            empleado: Filtrar por empleado (solicitante o autorizador)
            tipo_operacion: Filtrar por tipo
            fecha_desde: Filtrar desde fecha
            fecha_hasta: Filtrar hasta fecha
        
        Returns:
            QuerySet de RegistroAutorizaciones
        """
        from django.db.models import Q
        
        filtros = Q()
        
        if empleado:
            filtros &= (
                Q(id_empleado_solicitante=empleado) |
                Q(id_empleado_autorizador=empleado) |
                Q(id_empleado_autorizador_2=empleado)
            )
        
        if tipo_operacion:
            filtros &= Q(tipo_operacion=tipo_operacion)
        
        if fecha_desde:
            filtros &= Q(fecha_autorizacion__gte=fecha_desde)
        
        if fecha_hasta:
            filtros &= Q(fecha_autorizacion__lte=fecha_hasta)
        
        return RegistroAutorizaciones.objects.filter(filtros).select_related(
            'id_empleado_solicitante',
            'id_empleado_autorizador',
            'id_empleado_autorizador_2'
        ).order_by('-fecha_autorizacion')


class RecargaService:
    """
    Servicio centralizado para gestión de recargas de saldo prepago.
    
    Maneja:
    - Cálculo de comisiones
    - Validación de idempotencia
    - Acreditación de saldo
    - Generación de facturas
    - Flujos de Bancard, efectivo, transferencia
    """
    
    # Configuración de comisiones por método de pago
    COMISIONES = {
        'efectivo': Decimal('0.00'),          # Sin comisión
        'bancard': Decimal('3.40'),           # 3.4% pasarela
        'tarjeta_pos': Decimal('3.40'),       # 3.4% POS
        'transferencia': Decimal('0.00'),     # Sin comisión
    }
    
    # Umbral para doble validación (configurable)
    UMBRAL_DOBLE_VALIDACION = Decimal('500000.00')  # ₲500,000
    
    @classmethod
    def calcular_montos(cls, monto_recarga: Decimal, metodo_pago: str) -> Dict:
        """
        Calcula montos de la recarga considerando comisiones.
        
        Args:
            monto_recarga: Monto que se acreditará al hijo
            metodo_pago: efectivo, bancard, tarjeta_pos, transferencia
        
        Returns:
            dict con:
                - monto_recarga: Decimal (saldo a acreditar)
                - comision_porcentaje: Decimal
                - comision_monto: Decimal
                - total_cobrado: Decimal (lo que paga el cliente)
        """
        porcentaje_comision = cls.COMISIONES.get(metodo_pago, Decimal('0.00'))
        comision_monto = (monto_recarga * porcentaje_comision / 100).quantize(Decimal('0.01'))
        total_cobrado = monto_recarga + comision_monto
        
        return {
            'monto_recarga': monto_recarga,
            'comision_porcentaje': porcentaje_comision,
            'comision_monto': comision_monto,
            'total_cobrado': total_cobrado,
        }
    
    @classmethod
    def generar_codigo_referencia(cls) -> str:
        """
        Genera código de referencia único para transferencias.
        Formato: REF-YYYYMMDD-NNNNN
        """
        from django.utils import timezone
        from apps.core.models import CargasSaldo
        import random
        
        fecha_str = timezone.now().strftime('%Y%m%d')
        
        # Buscar último número del día
        ultimo_codigo = CargasSaldo.objects.filter(
            codigo_referencia_interno__startswith=f'REF-{fecha_str}'
        ).order_by('-codigo_referencia_interno').first()
        
        if ultimo_codigo:
            # Extraer número y sumar 1
            ultimo_num = int(ultimo_codigo.codigo_referencia_interno.split('-')[-1])
            nuevo_num = ultimo_num + 1
        else:
            nuevo_num = 1
        
        return f'REF-{fecha_str}-{nuevo_num:05d}'
    
    @classmethod
    def validar_idempotencia(cls, numero_comprobante: str = None, 
                            referencia_externa: str = None) -> bool:
        """
        Valida que no exista previamente el comprobante o referencia externa.
        
        Args:
            numero_comprobante: Número de comprobante bancario
            referencia_externa: ID de transacción de Bancard
        
        Returns:
            True si ya existe (duplicado), False si es nuevo
        """
        from apps.core.models import CargasSaldo
        from django.db.models import Q
        
        filtro = Q()
        
        if numero_comprobante:
            filtro |= Q(numero_comprobante_externo=numero_comprobante)
        
        if referencia_externa:
            filtro |= Q(referencia_externa=referencia_externa)
        
        if not filtro:
            return False
        
        return CargasSaldo.objects.filter(filtro).exists()
    
    @classmethod
    def acreditar_saldo(cls, recarga) -> Dict:
        """
        Acredita el saldo a la tarjeta y registra en historial.
        
        Args:
            recarga: Instancia de CargasSaldo
        
        Returns:
            dict con resultado de la operación
        """
        from django.db import transaction
        from apps.core.models import Tarjetas, ConsumosTarjeta
        from django.utils import timezone
        
        with transaction.atomic():
            # Obtener tarjeta con lock
            tarjeta = Tarjetas.objects.select_for_update().get(
                nro_tarjeta=recarga.nro_tarjeta.nro_tarjeta
            )
            
            saldo_anterior = tarjeta.saldo_actual
            tarjeta.saldo_actual += recarga.monto_cargado
            tarjeta.save(update_fields=['saldo_actual'])
            
            # Registrar en historial
            consumo = ConsumosTarjeta.objects.create(
                nro_tarjeta=tarjeta,
                fecha_consumo=recarga.fecha_confirmacion or timezone.now(),
                monto_consumido=-recarga.monto_cargado,  # Negativo = ingreso
                detalle=f'Recarga #{recarga.id_carga} - {recarga.metodo_pago.upper()} - {recarga.referencia or ""}',
                saldo_anterior=saldo_anterior,
                saldo_posterior=tarjeta.saldo_actual,
                id_empleado_registro=recarga.usuario_responsable
            )
            
            return {
                'success': True,
                'saldo_anterior': saldo_anterior,
                'saldo_nuevo': tarjeta.saldo_actual,
                'monto_acreditado': recarga.monto_cargado,
                'id_consumo': consumo.id_consumo
            }
    
    @classmethod
    def generar_factura(cls, recarga) -> Dict:
        """
        Genera factura fiscal por la recarga de saldo.
        
        La factura se emite por el monto_cargado (saldo acreditado),
        NO por el total_cobrado (que incluye comisión).
        
        Args:
            recarga: Instancia de CargasSaldo
        
        Returns:
            dict con información de la factura generada
        """
        from apps.ventas.models import Ventas, DetallesVenta
        from apps.productos.models import Productos
        from django.utils import timezone
        
        # Buscar o crear producto "Recarga de Saldo"
        producto_recarga, created = Productos.objects.get_or_create(
            codigo='RECARGA-SALDO',
            defaults={
                'nombre_producto': 'Recarga de Saldo Prepago',
                'precio_venta': Decimal('1.00'),  # Precio unitario simbólico
                'activo': True,
                'requiere_stock': False,
                'es_servicio': True,
            }
        )
        
        # Obtener tarjeta y cliente
        tarjeta = recarga.nro_tarjeta
        cliente = tarjeta.id_hijo.id_cliente_responsable
        
        # Crear venta (factura)
        venta = Ventas.objects.create(
            id_cliente=cliente,
            fecha_venta=recarga.fecha_confirmacion or timezone.now(),
            total_venta=recarga.monto_cargado,
            descuento=Decimal('0.00'),
            total_final=recarga.monto_cargado,
            estado='completada',
            metodo_pago='recarga_saldo',
            observaciones=f'Recarga #{recarga.id_carga} - Tarjeta {tarjeta.nro_tarjeta} - Hijo: {tarjeta.id_hijo.nombre}'
        )
        
        # Crear detalle de venta
        DetallesVenta.objects.create(
            id_venta=venta,
            id_producto=producto_recarga,
            cantidad=recarga.monto_cargado,  # Cantidad = monto (es un servicio)
            precio_unitario=Decimal('1.00'),
            subtotal=recarga.monto_cargado
        )
        
        # Asociar factura a recarga
        recarga.id_factura = venta
        recarga.save(update_fields=['id_factura'])
        
        return {
            'success': True,
            'id_factura': venta.id_venta,
            'numero_factura': venta.id_venta,
            'monto_facturado': recarga.monto_cargado,
        }
    
    @classmethod
    def procesar_recarga_caja(cls, hijo_id: int, monto: Decimal, metodo_pago: str,
                              empleado_id: int, referencia: str = None) -> Dict:
        """
        Procesa recarga en caja (efectivo o tarjeta POS).
        Flujo inmediato sin validaciones externas.
        
        Args:
            hijo_id: ID del hijo
            monto: Monto a recargar (saldo neto)
            metodo_pago: 'efectivo' o 'tarjeta_pos'
            empleado_id: ID del cajero
            referencia: Referencia opcional
        
        Returns:
            dict con resultado completo
        """
        from apps.core.models import CargasSaldo, Tarjetas
        from apps.clientes.models import Hijos
        from apps.usuarios.models import Empleados
        from django.utils import timezone
        from django.db import transaction
        
        # Calcular montos
        montos = cls.calcular_montos(monto, metodo_pago)
        
        # Obtener relaciones
        hijo = Hijos.objects.get(id_hijo=hijo_id)
        tarjeta = Tarjetas.objects.get(id_hijo=hijo)
        empleado = Empleados.objects.get(id_empleado=empleado_id)
        
        with transaction.atomic():
            # Crear recarga COMPLETADA
            recarga = CargasSaldo.objects.create(
                nro_tarjeta=tarjeta,
                id_cliente_origen=hijo.id_cliente_responsable,
                fecha_carga=timezone.now(),
                monto_cargado=montos['monto_recarga'],
                total_cobrado=montos['total_cobrado'],
                comision_aplicada=montos['comision_monto'],
                porcentaje_comision=montos['comision_porcentaje'],
                metodo_pago=metodo_pago,
                estado='completada',
                fecha_confirmacion=timezone.now(),
                referencia=referencia or f'CAJA-{timezone.now().strftime("%Y%m%d%H%M%S")}',
                usuario_responsable=empleado
            )
            
            # Acreditar saldo
            resultado_saldo = cls.acreditar_saldo(recarga)
            
            # Generar factura
            resultado_factura = cls.generar_factura(recarga)
            
            return {
                'success': True,
                'id_recarga': recarga.id_carga,
                'estado': recarga.estado,
                'monto_acreditado': recarga.monto_cargado,
                'total_cobrado': recarga.total_cobrado,
                'comision': recarga.comision_aplicada,
                'saldo_nuevo': resultado_saldo['saldo_nuevo'],
                'id_factura': resultado_factura['id_factura'],
                'mensaje': f'Recarga procesada exitosamente. Nuevo saldo: ₲{resultado_saldo["saldo_nuevo"]:,.2f}'
            }
    
    @classmethod
    def iniciar_recarga_transferencia(cls, hijo_id: int, monto: Decimal) -> Dict:
        """
        Genera código de referencia para transferencia bancaria.
        Crea recarga en estado PENDIENTE_VALIDACION.
        
        Args:
            hijo_id: ID del hijo
            monto: Monto a recargar
        
        Returns:
            dict con código de referencia y datos bancarios
        """
        from apps.core.models import CargasSaldo, Tarjetas
        from apps.clientes.models import Hijos
        from django.utils import timezone
        
        # Generar código único
        codigo_ref = cls.generar_codigo_referencia()
        
        # Calcular montos (transferencia sin comisión)
        montos = cls.calcular_montos(monto, 'transferencia')
        
        # Obtener relaciones
        hijo = Hijos.objects.get(id_hijo=hijo_id)
        tarjeta = Tarjetas.objects.get(id_hijo=hijo)
        
        # Crear recarga pendiente
        recarga = CargasSaldo.objects.create(
            nro_tarjeta=tarjeta,
            id_cliente_origen=hijo.id_cliente_responsable,
            fecha_carga=timezone.now(),
            monto_cargado=montos['monto_recarga'],
            total_cobrado=montos['total_cobrado'],
            comision_aplicada=montos['comision_monto'],
            porcentaje_comision=montos['comision_porcentaje'],
            metodo_pago='transferencia',
            estado='pendiente_validacion',
            codigo_referencia_interno=codigo_ref,
            referencia=codigo_ref
        )
        
        return {
            'success': True,
            'id_recarga': recarga.id_carga,
            'codigo_referencia': codigo_ref,
            'monto_transferir': montos['total_cobrado'],
            'datos_bancarios': {
                'banco': 'Banco Nacional de Fomento',
                'titular': 'CANTINA TITA S.A.',
                'cuenta': '1234567890',
                'ruc': '80012345-6',
            },
            'instrucciones': f'Transferir ₲{montos["total_cobrado"]:,.2f} e incluir el código {codigo_ref} en el concepto',
            'mensaje': 'Código de referencia generado. Presente el comprobante en caja para validar.'
        }
    
    @classmethod
    def validar_transferencia(cls, codigo_referencia: str = None, numero_comprobante: str = None,
                             empleado_id: int = None, hijo_id: int = None, monto: Decimal = None,
                             imagen_path: str = None) -> Dict:
        """
        Valida y completa recarga por transferencia bancaria.
        Soporta flujo con código de referencia O sin código (manual).
        
        Args:
            codigo_referencia: Código REF-XXXXX (opcional)
            numero_comprobante: Número de comprobante bancario (requerido)
            empleado_id: ID cajero que valida
            hijo_id: ID hijo (solo si manual sin código)
            monto: Monto del comprobante (solo si manual)
            imagen_path: Ruta a imagen del comprobante
        
        Returns:
            dict con resultado de validación
        """
        from apps.core.models import CargasSaldo, Tarjetas
        from apps.clientes.models import Hijos
        from apps.usuarios.models import Empleados
        from django.utils import timezone
        from django.db import transaction
        
        # Validar idempotencia
        if cls.validar_idempotencia(numero_comprobante=numero_comprobante):
            raise ValidationError(
                f'El comprobante {numero_comprobante} ya fue registrado previamente'
            )
        
        empleado = Empleados.objects.get(id_empleado=empleado_id)
        
        with transaction.atomic():
            # Flujo A: Con código de referencia
            if codigo_referencia:
                recarga = CargasSaldo.objects.select_for_update().get(
                    codigo_referencia_interno=codigo_referencia,
                    estado='pendiente_validacion'
                )
                
                # Actualizar con datos de validación
                recarga.numero_comprobante_externo = numero_comprobante
                recarga.usuario_responsable = empleado
                recarga.fecha_confirmacion = timezone.now()
                recarga.imagen_comprobante = imagen_path
                
                # Verificar si requiere doble validación
                if recarga.monto_cargado > cls.UMBRAL_DOBLE_VALIDACION:
                    recarga.estado = 'validacion_pendiente'
                    recarga.requiere_validacion_supervisor = True
                    recarga.save()
                    
                    return {
                        'success': True,
                        'requiere_aprobacion': True,
                        'id_recarga': recarga.id_carga,
                        'monto': recarga.monto_cargado,
                        'mensaje': f'Monto elevado (₲{recarga.monto_cargado:,.2f}). Requiere aprobación de supervisor.'
                    }
                
                # Completar recarga
                recarga.estado = 'completada'
                recarga.save()
                
            # Flujo B: Sin código (manual)
            else:
                if not hijo_id or not monto:
                    raise ValidationError('Se requiere hijo_id y monto para registro manual')
                
                hijo = Hijos.objects.get(id_hijo=hijo_id)
                tarjeta = Tarjetas.objects.get(id_hijo=hijo)
                montos = cls.calcular_montos(monto, 'transferencia')
                
                # Crear recarga directamente
                recarga = CargasSaldo.objects.create(
                    nro_tarjeta=tarjeta,
                    id_cliente_origen=hijo.id_cliente_responsable,
                    fecha_carga=timezone.now(),
                    monto_cargado=montos['monto_recarga'],
                    total_cobrado=montos['total_cobrado'],
                    comision_aplicada=montos['comision_monto'],
                    porcentaje_comision=montos['comision_porcentaje'],
                    metodo_pago='transferencia',
                    estado='completada' if monto <= cls.UMBRAL_DOBLE_VALIDACION else 'validacion_pendiente',
                    numero_comprobante_externo=numero_comprobante,
                    usuario_responsable=empleado,
                    fecha_confirmacion=timezone.now(),
                    imagen_comprobante=imagen_path,
                    referencia=f'TRANSF-{numero_comprobante}',
                    requiere_validacion_supervisor=(monto > cls.UMBRAL_DOBLE_VALIDACION)
                )
                
                if recarga.requiere_validacion_supervisor:
                    return {
                        'success': True,
                        'requiere_aprobacion': True,
                        'id_recarga': recarga.id_carga,
                        'monto': recarga.monto_cargado,
                        'mensaje': f'Monto elevado. Requiere aprobación de supervisor.'
                    }
            
            # Acreditar saldo y generar factura
            resultado_saldo = cls.acreditar_saldo(recarga)
            resultado_factura = cls.generar_factura(recarga)
            
            return {
                'success': True,
                'requiere_aprobacion': False,
                'id_recarga': recarga.id_carga,
                'estado': recarga.estado,
                'monto_acreditado': recarga.monto_cargado,
                'saldo_nuevo': resultado_saldo['saldo_nuevo'],
                'id_factura': resultado_factura['id_factura'],
                'mensaje': f'Transferencia validada. Saldo acreditado: ₲{recarga.monto_cargado:,.2f}'
            }
    
    @classmethod
    def aprobar_recarga_supervisor(cls, recarga_id: int, supervisor_id: int) -> Dict:
        """
        Aprueba recarga pendiente de validación por supervisor.
        
        Args:
            recarga_id: ID de la recarga
            supervisor_id: ID del supervisor
        
        Returns:
            dict con resultado
        """
        from apps.core.models import CargasSaldo
        from apps.usuarios.models import Empleados
        from django.utils import timezone
        from django.db import transaction
        
        supervisor = Empleados.objects.get(id_empleado=supervisor_id)
        
        # Verificar permisos de supervisor (TODO: integrar con sistema de roles)
        # if not supervisor.es_supervisor:
        #     raise ValidationError('El empleado no tiene permisos de supervisor')
        
        with transaction.atomic():
            recarga = CargasSaldo.objects.select_for_update().get(
                id_carga=recarga_id,
                estado='validacion_pendiente'
            )
            
            recarga.supervisor_aprobador = supervisor
            recarga.fecha_aprobacion = timezone.now()
            recarga.estado = 'completada'
            recarga.fecha_confirmacion = recarga.fecha_confirmacion or timezone.now()
            recarga.save()
            
            # Acreditar saldo y generar factura
            resultado_saldo = cls.acreditar_saldo(recarga)
            resultado_factura = cls.generar_factura(recarga)
            
            return {
                'success': True,
                'id_recarga': recarga.id_carga,
                'monto_acreditado': recarga.monto_cargado,
                'saldo_nuevo': resultado_saldo['saldo_nuevo'],
                'id_factura': resultado_factura['id_factura'],
                'mensaje': f'Recarga aprobada y procesada por supervisor {supervisor.nombre}'
            }

