"""
Signals para el módulo de ventas
Automatización de actualización de saldos y aplicación de notas de crédito
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal

from .models import AplicacionPagosVentas, NotasCreditoCliente


@receiver(post_save, sender=AplicacionPagosVentas)
def actualizar_saldo_venta(sender, instance, created, **kwargs):
    """
    Actualiza el saldo_pendiente de la venta cuando se registra un pago.
    
    Reglas:
    - Reduce saldo_pendiente por el monto aplicado
    - Si saldo llega a 0 → estado_pago = 'Pagada'
    - Si saldo > 0 y < monto_total → estado_pago = 'Parcial'
    - Usa transaction.atomic() para garantizar consistencia
    
    Ejemplo:
        Venta de Gs. 100,000 con 3 pagos:
        - Pago 1: 40,000 → saldo_pendiente = 60,000 (Parcial)
        - Pago 2: 30,000 → saldo_pendiente = 30,000 (Parcial)
        - Pago 3: 30,000 → saldo_pendiente = 0 (Pagada)
    """
    if not created:
        return
    
    with transaction.atomic():
        venta = instance.id_venta
        venta.saldo_pendiente = venta.saldo_pendiente - instance.monto_aplicado
        
        # Prevenir saldo negativo por error
        if venta.saldo_pendiente < 0:
            venta.saldo_pendiente = Decimal('0.00')
        
        # Actualizar estado de pago
        if venta.saldo_pendiente == 0:
            venta.estado_pago = 'Pagada'
        elif venta.saldo_pendiente < venta.monto_total:
            venta.estado_pago = 'Parcial'
        else:
            venta.estado_pago = 'Pendiente'
        
        venta.save(update_fields=['saldo_pendiente', 'estado_pago'])


@receiver(post_save, sender=NotasCreditoCliente)
def aplicar_nota_credito_cliente(sender, instance, created, **kwargs):
    """
    Aplica la nota de crédito a la venta origen cuando cambia a estado 'Aplicada'.
    
    Reglas:
    - Si estado = 'Aplicada' y tiene venta origen → reduce saldo_pendiente
    - Si nota > saldo_pendiente → ajusta saldo a 0 (el excedente queda como crédito)
    - Actualiza estado_pago de la venta según saldo resultante
    
    Ejemplo:
        Venta: monto_total = 150,000, saldo_pendiente = 100,000
        Nota de crédito: 40,000
        Resultado: saldo_pendiente = 60,000, estado_pago = 'Parcial'
    """
    # Solo procesar si está en estado 'Aplicada' y tiene venta origen
    if instance.estado != 'Aplicada' or not instance.id_venta_origen:
        return
    
    with transaction.atomic():
        venta = instance.id_venta_origen
        
        # Reducir saldo pendiente
        venta.saldo_pendiente = venta.saldo_pendiente - instance.monto_total
        
        # Si la nota es mayor al saldo, ajustar a 0
        # (el excedente se maneja en un modelo de saldos a favor - futura implementación)
        if venta.saldo_pendiente < 0:
            venta.saldo_pendiente = Decimal('0.00')
        
        # Actualizar estado de pago
        if venta.saldo_pendiente == 0:
            venta.estado_pago = 'Pagada'
        elif venta.saldo_pendiente < venta.monto_total:
            venta.estado_pago = 'Parcial'
        
        venta.save(update_fields=['saldo_pendiente', 'estado_pago'])
