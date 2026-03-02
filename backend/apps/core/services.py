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
