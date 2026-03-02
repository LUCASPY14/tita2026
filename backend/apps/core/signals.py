"""
Signals para la app core
Garantiza la integridad transaccional y automatización de procesos
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from .models import CargasSaldo, ConsumosTarjeta, Tarjetas


@receiver(post_save, sender=CargasSaldo)
def actualizar_saldo_recarga(sender, instance, created, **kwargs):
    """
    Actualiza el saldo de la tarjeta cuando se confirma una recarga.
    Solo se ejecuta cuando el estado cambia a 'completada'.
    
    IMPORTANTE: Este signal está deshabilitado porque la lógica de acreditación
    se maneja ahora en RecargaService.acreditar_saldo() para mayor control.
    
    Se mantiene el código por compatibilidad pero no se ejecuta.
    """
    # DESHABILITADO - La acreditación se hace en el servicio
    return
    
    # Código original (comentado):
    # if instance.estado == 'completada':
    #     if not hasattr(instance, '_saldo_actualizado'):
    #         with transaction.atomic():
    #             tarjeta = Tarjetas.objects.select_for_update().get(nro_tarjeta=instance.nro_tarjeta.nro_tarjeta)
    #             saldo_anterior = tarjeta.saldo_actual
    #             
    #             consumo_existe = ConsumosTarjeta.objects.filter(
    #                 detalle__contains=f"Recarga #{instance.id_carga}"
    #             ).exists()
    #             
    #             if not consumo_existe:
    #                 tarjeta.saldo_actual += instance.monto_cargado
    #                 tarjeta.save()
    #                 
    #                 ConsumosTarjeta.objects.create(
    #                     nro_tarjeta=tarjeta,
    #                     fecha_consumo=instance.fecha_confirmacion or instance.fecha_carga,
    #                     monto_consumido=-instance.monto_cargado,
    #                     detalle=f"Recarga #{instance.id_carga} - {instance.referencia or 'Sin referencia'}",
    #                     saldo_anterior=saldo_anterior,
    #                     saldo_posterior=tarjeta.saldo_actual
    #                 )
    #                 
    #                 instance._saldo_actualizado = True


@receiver(post_save, sender=ConsumosTarjeta)
def notificar_saldo_bajo(sender, instance, created, **kwargs):
    """
    Envía notificación si el saldo está bajo después de un consumo.
    Respeta la configuración de la tarjeta.
    """
    if created:
        tarjeta = instance.nro_tarjeta
        
        # Verificar si requiere notificación
        if tarjeta.requiere_notificacion:
            from apps.notificaciones.models import Notificaciones
            from django.utils import timezone
            
            try:
                # Crear notificación de saldo bajo
                Notificaciones.objects.create(
                    tipo='saldo_bajo',
                    titulo='Saldo Bajo en Tarjeta',
                    mensaje=f'La tarjeta {tarjeta.nro_tarjeta} del hijo {tarjeta.id_hijo} tiene un saldo bajo: ${tarjeta.saldo_actual}. Saldo de alerta: ${tarjeta.saldo_alerta}',
                    prioridad='media',
                    destinatario_tipo='cliente',
                    id_destinatario=tarjeta.id_hijo.id_cliente_responsable.id_cliente,
                    fecha_envio=timezone.now(),
                    estado='pendiente'
                )
                
                # Actualizar última notificación
                tarjeta.ultima_notificacion_saldo = timezone.now()
                tarjeta.save(update_fields=['ultima_notificacion_saldo'])
                
            except Exception as e:
                # No fallar la transacción si falla la notificación
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error al crear notificación de saldo bajo: {e}")


@receiver(pre_save, sender=Tarjetas)
def validar_tarjeta_unica(sender, instance, **kwargs):
    """
    Valida que el hijo no tenga otra tarjeta activa.
    Se ejecuta antes de guardar la tarjeta.
    """
    if instance.id_hijo:
        # Verificar si ya existe otra tarjeta para este hijo
        tarjetas_existentes = Tarjetas.objects.filter(
            id_hijo=instance.id_hijo
        ).exclude(nro_tarjeta=instance.nro_tarjeta)
        
        if tarjetas_existentes.exists():
            from django.core.exceptions import ValidationError
            raise ValidationError(
                f'El hijo {instance.id_hijo} ya tiene una tarjeta asociada ({tarjetas_existentes.first().nro_tarjeta}). '
                'Solo se permite una tarjeta por hijo.'
            )


@receiver(post_save, sender=ConsumosTarjeta)
def validar_integridad_saldo(sender, instance, created, **kwargs):
    """
    Valida que el saldo registrado en el consumo coincida con el saldo real de la tarjeta.
    Esto ayuda a detectar inconsistencias.
    """
    if created:
        tarjeta = instance.nro_tarjeta
        
        # Verificar coherencia del saldo
        if instance.saldo_posterior != tarjeta.saldo_actual:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"INCONSISTENCIA DE SALDO detectada en tarjeta {tarjeta.nro_tarjeta}: "
                f"Consumo registra saldo_posterior={instance.saldo_posterior}, "
                f"pero tarjeta tiene saldo_actual={tarjeta.saldo_actual}"
            )
