"""
Signals para el módulo de compras
Automatización de actualización de saldos a proveedores
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal

from .models import AplicacionPagosCompras, NotasCreditoProveedor


@receiver(post_save, sender=AplicacionPagosCompras)
def actualizar_saldo_compra(sender, instance, created, **kwargs):
    """
    Actualiza el saldo_pendiente de la compra cuando se registra un pago a proveedor.
    
    Reglas:
    - Reduce saldo_pendiente por el monto aplicado
    - Si saldo llega a 0 → estado_pago = 'Pagada'
    - Si saldo > 0 y < monto_total → estado_pago = 'Parcial'
    - Permite aplicar un pago a múltiples facturas
    
    Ejemplo:
        Pago de Gs. 5,000,000 distribuido en:
        - Factura 001: aplicar 2,000,000
        - Factura 002: aplicar 2,000,000
        - Factura 003: aplicar 1,000,000
    """
    if not created:
        return
    
    with transaction.atomic():
        compra = instance.id_compra
        compra.saldo_pendiente = compra.saldo_pendiente - instance.monto_aplicado
        
        # Prevenir saldo negativo
        if compra.saldo_pendiente < 0:
            compra.saldo_pendiente = Decimal('0.00')
        
        # Actualizar estado de pago
        if compra.saldo_pendiente == 0:
            compra.estado_pago = 'Pagada'
        elif compra.saldo_pendiente < compra.monto_total:
            compra.estado_pago = 'Parcial'
        else:
            compra.estado_pago = 'Pendiente'
        
        compra.save(update_fields=['saldo_pendiente', 'estado_pago'])


@receiver(post_save, sender=NotasCreditoProveedor)
def aplicar_nota_credito_proveedor(sender, instance, created, **kwargs):
    """
    Aplica la nota de crédito del proveedor a la compra origen.
    
    Reglas:
    - Si estado = 'Aplicada' y tiene compra origen → reduce saldo_pendiente
    - Si nota > saldo_pendiente → ajusta saldo a 0
    - Actualiza estado_pago de la compra
    
    Uso:
    - Devoluciones a proveedor
    - Descuentos post-factura
    - Ajustes de precio
    """
    if instance.estado != 'Aplicada' or not instance.id_compra_original:
        return
    
    with transaction.atomic():
        compra = instance.id_compra_original
        
        # Reducir saldo pendiente
        compra.saldo_pendiente = compra.saldo_pendiente - instance.monto_total
        
        # Ajustar si queda negativo
        if compra.saldo_pendiente < 0:
            compra.saldo_pendiente = Decimal('0.00')
        
        # Actualizar estado
        if compra.saldo_pendiente == 0:
            compra.estado_pago = 'Pagada'
        elif compra.saldo_pendiente < compra.monto_total:
            compra.estado_pago = 'Parcial'
        
        compra.save(update_fields=['saldo_pendiente', 'estado_pago'])
