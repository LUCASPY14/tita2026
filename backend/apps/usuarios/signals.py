"""
Signals para auditoría automática de cambios en modelos
Registra automáticamente todas las operaciones CRUD
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
import json

from apps.usuarios.models import (
    Empleados,
    AuditoriaEmpleados,
    AuditoriaOperaciones,
    Roles,
    PerfilesUsuario,
    SesionesActivas,
    BloqueosCuenta
)


# ==================== HELPER FUNCTIONS ====================

def obtener_empleado_actual():
    """
    Obtiene el empleado actual del contexto (thread-local).
    Requiere middleware que establezca el empleado en el thread.
    """
    from threading import current_thread
    return getattr(current_thread(), 'current_empleado', None)


def obtener_ip_actual():
    """
    Obtiene la IP actual del contexto (thread-local).
    """
    from threading import current_thread
    return getattr(current_thread(), 'current_ip', None)


def serializar_modelo(instancia, campos_excluir=None):
    """
    Serializa una instancia de modelo a diccionario JSON-serializable.
    
    Args:
        instancia: Instancia del modelo
        campos_excluir: Lista de campos a excluir (ej: ['contrasena_hash'])
        
    Returns:
        Diccionario con los datos del modelo
    """
    if campos_excluir is None:
        campos_excluir = ['contrasena_hash', 'password', 'secret_key']
    
    datos = {}
    
    for field in instancia._meta.fields:
        if field.name not in campos_excluir:
            valor = getattr(instancia, field.name)
            
            # Convertir ForeignKey a ID
            if field.is_relation:
                if valor:
                    datos[field.name] = valor.pk
                else:
                    datos[field.name] = None
            else:
                # Convertir datetime a string
                if hasattr(valor, 'isoformat'):
                    datos[field.name] = valor.isoformat()
                else:
                    datos[field.name] = valor
    
    return datos


# ==================== SIGNALS PARA EMPLEADOS ====================

@receiver(pre_save, sender=Empleados)
def empleado_pre_save(sender, instance, **kwargs):
    """
    Captura el estado anterior del empleado antes de guardar.
    Guarda en una variable temporal para comparar después.
    """
    if instance.pk:  # Solo si es actualización, no creación
        try:
            instance._estado_anterior = Empleados.objects.get(pk=instance.pk)
        except Empleados.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None


@receiver(post_save, sender=Empleados)
def empleado_post_save(sender, instance, created, **kwargs):
    """
    Audita cambios en empleados (creación y actualización).
    """
    try:
        empleado_actual = obtener_empleado_actual()
        ip_actual = obtener_ip_actual() or '127.0.0.1'
        
        if created:
            # Empleado creado
            AuditoriaOperaciones.objects.create(
                usuario=empleado_actual.usuario if empleado_actual else 'sistema',
                tipo_usuario='empleado',
                id_usuario=empleado_actual.id_empleado if empleado_actual else None,
                operacion='CREAR_EMPLEADO',
                tabla_afectada='Empleados',
                id_registro=instance.id_empleado,
                ip_address=ip_actual,
                datos_nuevos=serializar_modelo(instance),
                fecha_operacion=timezone.now(),
                resultado='OK'
            )
        else:
            # Empleado actualizado - registrar cambios específicos
            if hasattr(instance, '_estado_anterior') and instance._estado_anterior:
                estado_anterior = instance._estado_anterior
                
                # Campos a auditar específicamente
                campos_importantes = [
                    'nombre', 'apellido', 'usuario', 'email', 
                    'activo', 'id_rol', 'telefono', 'direccion'
                ]
                
                for campo in campos_importantes:
                    valor_anterior = getattr(estado_anterior, campo, None)
                    valor_nuevo = getattr(instance, campo, None)
                    
                    # Convertir ForeignKey a ID para comparación
                    if hasattr(valor_anterior, 'pk'):
                        valor_anterior = valor_anterior.pk
                    if hasattr(valor_nuevo, 'pk'):
                        valor_nuevo = valor_nuevo.pk
                    
                    if valor_anterior != valor_nuevo:
                        # Registrar cambio en AuditoriaEmpleados
                        AuditoriaEmpleados.objects.create(
                            id_empleado=instance,
                            campo_modificado=campo,
                            valor_anterior=str(valor_anterior) if valor_anterior else None,
                            valor_nuevo=str(valor_nuevo) if valor_nuevo else None,
                            modificado_por=empleado_actual,
                            ip_origen=ip_actual,
                            fecha_modificacion=timezone.now()
                        )
                
                # Registrar operación general
                AuditoriaOperaciones.objects.create(
                    usuario=empleado_actual.usuario if empleado_actual else 'sistema',
                    tipo_usuario='empleado',
                    id_usuario=empleado_actual.id_empleado if empleado_actual else None,
                    operacion='ACTUALIZAR_EMPLEADO',
                    tabla_afectada='Empleados',
                    id_registro=instance.id_empleado,
                    ip_address=ip_actual,
                    datos_anteriores=serializar_modelo(estado_anterior),
                    datos_nuevos=serializar_modelo(instance),
                    fecha_operacion=timezone.now(),
                    resultado='OK'
                )
                
                # Limpiar estado anterior
                delattr(instance, '_estado_anterior')
    
    except Exception as e:
        # No fallar la operación por errores de auditoría
        print(f"Error en auditoría de empleado: {str(e)}")


@receiver(post_delete, sender=Empleados)
def empleado_post_delete(sender, instance, **kwargs):
    """
    Audita eliminación de empleados.
    """
    try:
        empleado_actual = obtener_empleado_actual()
        ip_actual = obtener_ip_actual() or '127.0.0.1'
        
        AuditoriaOperaciones.objects.create(
            usuario=empleado_actual.usuario if empleado_actual else 'sistema',
            tipo_usuario='empleado',
            id_usuario=empleado_actual.id_empleado if empleado_actual else None,
            operacion='ELIMINAR_EMPLEADO',
            tabla_afectada='Empleados',
            id_registro=instance.id_empleado,
            ip_address=ip_actual,
            datos_anteriores=serializar_modelo(instance),
            fecha_operacion=timezone.now(),
            resultado='OK'
        )
    
    except Exception as e:
        print(f"Error en auditoría de eliminación: {str(e)}")


# ==================== SIGNALS PARA ROLES ====================

@receiver(post_save, sender=Roles)
def rol_post_save(sender, instance, created, **kwargs):
    """
    Audita cambios en roles.
    """
    try:
        empleado_actual = obtener_empleado_actual()
        ip_actual = obtener_ip_actual() or '127.0.0.1'
        
        operacion = 'CREAR_ROL' if created else 'ACTUALIZAR_ROL'
        
        AuditoriaOperaciones.objects.create(
            usuario=empleado_actual.usuario if empleado_actual else 'sistema',
            tipo_usuario='empleado',
            id_usuario=empleado_actual.id_empleado if empleado_actual else None,
            operacion=operacion,
            tabla_afectada='Roles',
            id_registro=instance.id_rol,
            ip_address=ip_actual,
            datos_nuevos={
                'id_rol': instance.id_rol,
                'nombre_rol': instance.nombre_rol,
                'descripcion': instance.descripcion,
                'activo': instance.activo
            },
            fecha_operacion=timezone.now(),
            resultado='OK'
        )
    
    except Exception as e:
        print(f"Error en auditoría de rol: {str(e)}")


@receiver(post_delete, sender=Roles)
def rol_post_delete(sender, instance, **kwargs):
    """
    Audita eliminación de roles.
    """
    try:
        empleado_actual = obtener_empleado_actual()
        ip_actual = obtener_ip_actual() or '127.0.0.1'
        
        AuditoriaOperaciones.objects.create(
            usuario=empleado_actual.usuario if empleado_actual else 'sistema',
            tipo_usuario='empleado',
            id_usuario=empleado_actual.id_empleado if empleado_actual else None,
            operacion='ELIMINAR_ROL',
            tabla_afectada='Roles',
            id_registro=instance.id_rol,
            ip_address=ip_actual,
            datos_anteriores={
                'nombre_rol': instance.nombre_rol,
                'descripcion': instance.descripcion
            },
            fecha_operacion=timezone.now(),
            resultado='OK'
        )
    
    except Exception as e:
        print(f"Error en auditoría de eliminación de rol: {str(e)}")


# ==================== SIGNALS PARA SESIONES ====================

@receiver(post_save, sender=SesionesActivas)
def sesion_post_save(sender, instance, created, **kwargs):
    """
    Audita eventos de sesión.
    """
    try:
        if created:
            # NO registrar creación de sesión aquí porque ya se hace en SessionService
            pass
        else:
            # Sesión actualizada/cerrada
            if not instance.activa and instance.fecha_cierre:
                # Sesión cerrada - NO auditar aquí porque se hace en SessionService
                pass
    
    except Exception as e:
        print(f"Error en auditoría de sesión: {str(e)}")


# ==================== SIGNALS PARA BLOQUEOS ====================

@receiver(post_save, sender=BloqueosCuenta)
def bloqueo_post_save(sender, instance, created, **kwargs):
    """
    Audita bloqueos de cuenta.
    """
    try:
        if created:
            # Bloqueo creado - ya se registra en AuthenticationService
            pass
        else:
            # Bloqueo actualizado (desbloqueo)
            if not instance.activo:
                empleado_actual = obtener_empleado_actual()
                ip_actual = obtener_ip_actual() or '127.0.0.1'
                
                AuditoriaOperaciones.objects.create(
                    usuario=empleado_actual.usuario if empleado_actual else 'sistema',
                    tipo_usuario='empleado',
                    id_usuario=empleado_actual.id_empleado if empleado_actual else None,
                    operacion='DESBLOQUEAR_CUENTA',
                    tabla_afectada='BloqueosCuenta',
                    id_registro=instance.id,
                    ip_address=ip_actual,
                    datos_nuevos={
                        'id_empleado': instance.id_empleado.id_empleado,
                        'motivo_original': instance.motivo,
                        'desbloqueado_en': str(timezone.now())
                    },
                    fecha_operacion=timezone.now(),
                    resultado='OK'
                )
    
    except Exception as e:
        print(f"Error en auditoría de bloqueo: {str(e)}")


# ==================== SIGNALS PARA PERFILES ====================

@receiver(post_save, sender=PerfilesUsuario)
def perfil_post_save(sender, instance, created, **kwargs):
    """
    Audita cambios en perfiles de usuario.
    """
    try:
        empleado_actual = obtener_empleado_actual()
        ip_actual = obtener_ip_actual() or '127.0.0.1'
        
        operacion = 'CREAR_PERFIL' if created else 'ACTUALIZAR_PERFIL'
        
        AuditoriaOperaciones.objects.create(
            usuario=empleado_actual.usuario if empleado_actual else instance.id_empleado.usuario,
            tipo_usuario='empleado',
            id_usuario=empleado_actual.id_empleado if empleado_actual else instance.id_empleado.id_empleado,
            operacion=operacion,
            tabla_afectada='PerfilesUsuario',
            id_registro=instance.id,
            ip_address=ip_actual,
            datos_nuevos={
                'id_empleado': instance.id_empleado.id_empleado,
                'tema': instance.tema,
                'idioma': instance.idioma,
                'timezone': instance.timezone
            },
            fecha_operacion=timezone.now(),
            resultado='OK'
        )
    
    except Exception as e:
        print(f"Error en auditoría de perfil: {str(e)}")


# ==================== CONFIGURACIÓN DE SIGNALS ====================

def conectar_signals():
    """
    Conecta todas las signals de auditoría.
    Esta función se llama automáticamente cuando se importa el módulo.
    """
    # Las signals ya están conectadas con @receiver
    pass


# Autoconectar signals al importar
conectar_signals()
