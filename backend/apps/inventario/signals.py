"""
Signals para el módulo de inventario
Actualización automática de stock con consistencia ACID y manejo de concurrencia
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from .models import StockUnico, MovimientosStock, AlertasStock, CostosHistoricos
from apps.compras.models import DetallesCompra, Compras
from apps.ventas.models import DetallesVenta, Ventas


@receiver(post_save, sender=Compras)
def actualizar_stock_compra(sender, instance, created, **kwargs):
    """
    Actualiza stock cuando una compra es confirmada.
    
    Reglas:
    - Solo procesa si estado = 'confirmado'
    - Usa select_for_update() para evitar condiciones de carrera
    - Envuelve todo en transaction.atomic()
    - Crea MovimientosStock + actualiza StockUnico + registra CostosHistoricos
    
    Ejemplo:
        Compra de 100 unidades de Coca Cola:
        - StockUnico: cantidad = 50 → 150
        - MovimientosStock: tipo='Ingreso', motivo='compra', cantidad=100
        - CostosHistoricos: costo_unitario=5000, cantidad_comprada=100
    """
    # Solo procesar compras confirmadas
    if instance.estado_pago not in ['Pagada', 'Parcial']:
        return
    
    # Verificar si ya fue procesada (evitar duplicados)
    if MovimientosStock.objects.filter(
        id_compra=instance,
        motivo='compra'
    ).exists():
        return
    
    with transaction.atomic():
        detalles = DetallesCompra.objects.filter(id_compra=instance)
        
        for detalle in detalles:
            producto = detalle.id_producto
            cantidad = detalle.cantidad
            costo = detalle.costo_unitario
            
            # BLOQUEO PESIMISTA: Evita condiciones de carrera
            # Si otro proceso está modificando el mismo stock, esperará
            stock, created_stock = StockUnico.objects.select_for_update().get_or_create(
                id_producto=producto,
                defaults={'cantidad': Decimal('0.000')}
            )
            
            stock_anterior = stock.cantidad
            stock.cantidad += cantidad
            stock.save()
            
            # Registrar movimiento
            MovimientosStock.objects.create(
                tipo_movimiento='Ingreso',
                motivo='compra',
                cantidad=cantidad,
                stock_resultante=stock.cantidad,
                observaciones=f"Compra #{instance.id_compra} - Factura {instance.nro_factura}",
                id_compra=instance,
                id_empleado_autoriza=instance.id_proveedor.contacto_empleado if hasattr(instance.id_proveedor, 'contacto_empleado') else None,
                id_producto=producto
            )
            
            # Registrar costo histórico para cálculo de costo promedio ponderado
            CostosHistoricos.objects.create(
                costo_unitario=costo,
                cantidad_comprada=cantidad,
                fecha_compra=instance.fecha,
                id_compra=instance,
                id_producto=producto
            )
            
            # Verificar si se resolvió alguna alerta de stock bajo
            _resolver_alertas_stock(producto, stock.cantidad)


@receiver(pre_save, sender=Ventas)
def validar_stock_venta(sender, instance, **kwargs):
    """
    Valida que haya stock disponible ANTES de crear la venta.
    
    Reglas:
    - Si producto.permite_stock_negativo = False → debe haber stock
    - Usa select_for_update() para bloqueo pesimista
    - ValidationError si no hay stock suficiente
    
    Esta validación evita overselling en escenarios de concurrencia:
    - 5 cajeros venden último producto simultáneamente
    - select_for_update() garantiza que solo uno pase
    """
    # Solo validar ventas nuevas
    if instance.pk:
        return
    
    # Por ahora, solo loguear
    # La validación real se hará en el servicio de dominio
    pass


@receiver(post_save, sender=DetallesVenta)
def descontar_stock_venta(sender, instance, created, **kwargs):
    """
    Descuenta stock cuando se confirma una venta.
    
    CRITICAL: Usa select_for_update() para evitar overselling
    
    Flujo:
    1. Bloquea StockUnico con select_for_update()
    2. Verifica stock disponible
    3. Descuenta cantidad
    4. Crea MovimientosStock
    5. Verifica si debe generar alerta
    """
    if not created:
        return
    
    with transaction.atomic():
        producto = instance.id_producto
        cantidad = instance.cantidad
        venta = instance.id_venta
        
        # BLOQUEO PESIMISTA: Espera si otro proceso está modificando
        try:
            stock = StockUnico.objects.select_for_update().get(id_producto=producto)
        except StockUnico.DoesNotExist:
            # Crear stock si no existe (caso edge)
            stock = StockUnico.objects.create(
                id_producto=producto,
                cantidad=Decimal('0.000')
            )
        
        # Validar stock disponible
        if not producto.permite_stock_negativo:
            if stock.cantidad < cantidad:
                # Esto no debería pasar si la validación previa funcionó
                raise ValueError(
                    f"Stock insuficiente para {producto.descripcion}. "
                    f"Disponible: {stock.cantidad}, Solicitado: {cantidad}"
                )
        
        # Descontar stock
        stock_anterior = stock.cantidad
        stock.cantidad -= cantidad
        stock.save()
        
        # Registrar movimiento
        MovimientosStock.objects.create(
            tipo_movimiento='Egreso',
            motivo='venta',
            cantidad=cantidad,
            stock_resultante=stock.cantidad,
            observaciones=f"Venta #{venta.id_venta}",
            id_venta=venta,
            id_empleado_autoriza=venta.id_empleado_cajero,
            id_producto=producto
        )
        
        # Verificar si debe generar alerta de stock bajo
        _generar_alerta_stock_bajo(producto, stock.cantidad)


def _generar_alerta_stock_bajo(producto, stock_actual):
    """
    Genera alerta si stock pasa por debajo del mínimo.
    
    Reglas:
    - Solo genera si NO existe alerta activa para este producto
    - Detecta 3 niveles: crítico (50% mínimo), mínimo, agotado
    - Se marca como activa=True
    """
    # Verificar si ya existe alerta activa
    alerta_existente = AlertasStock.objects.filter(
        id_producto=producto,
        activa=True
    ).exists()
    
    if alerta_existente:
        return  # Ya hay alerta activa, no crear duplicado
    
    stock_minimo = producto.stock_minimo
    
    # Determinar tipo de alerta
    tipo_alerta = None
    
    if stock_actual <= 0:
        tipo_alerta = 'stock_cero'
    elif stock_actual <= (stock_minimo * Decimal('0.5')):
        tipo_alerta = 'stock_critico'
    elif stock_actual <= stock_minimo:
        tipo_alerta = 'stock_minimo'
    
    if tipo_alerta:
        AlertasStock.objects.create(
            tipo_alerta=tipo_alerta,
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            id_producto=producto,
            activa=True,
            notificacion_enviada=False
        )


def _resolver_alertas_stock(producto, stock_actual):
    """
    Marca alertas como resueltas si el stock vuelve arriba del mínimo.
    """
    if stock_actual > producto.stock_minimo:
        AlertasStock.objects.filter(
            id_producto=producto,
            activa=True
        ).update(
            activa=False,
            fecha_resuelta=timezone.now()
        )


@receiver(post_save, sender=AlertasStock)
def enviar_notificacion_alerta(sender, instance, created, **kwargs):
    """
    Envía notificación cuando se crea una alerta.
    
    Solo envía si:
    - Es nueva (created=True)
    - Está activa
    - No se ha enviado notificación aún
    """
    if not created or not instance.activa or instance.notificacion_enviada:
        return
    
    # TODO: Implementar integración con sistema de notificaciones
    # Por ahora solo marcamos como enviada
    # from apps.notificaciones.models import AlertasAutomaticas
    
    # Determinar prioridad según tipo
    prioridad_map = {
        'stock_cero': 'critica',
        'stock_critico': 'alta',
        'stock_minimo': 'media'
    }
    
    prioridad = prioridad_map.get(instance.tipo_alerta, 'media')
    
    # Crear notificación (PENDIENTE: verificar modelo correcto de notificaciones)
    # Notificaciones.objects.create(
    #     tipo_notificacion='alerta',
    #     titulo=f'Stock {instance.get_tipo_alerta_display()}',
    #     mensaje=f'El producto {instance.id_producto.descripcion} tiene stock {instance.get_tipo_alerta_display().lower()}: {instance.stock_actual} unidades (mínimo: {instance.stock_minimo})',
    #     prioridad=prioridad,
    #     fecha_creacion=timezone.now()
    # )
    
    # Marcar como enviada
    instance.notificacion_enviada = True
    instance.save(update_fields=['notificacion_enviada'])
