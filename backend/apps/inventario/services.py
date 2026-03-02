"""
Servicios de dominio para inventario
Lógica de negocio centralizada y reutilizable
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from typing import List, Dict, Tuple

from .models import StockUnico, MovimientosStock
from apps.productos.models import Productos


class StockService:
    """
    Servicio centralizado para operaciones de stock.
    
    Ventajas:
    - Lógica reutilizable desde cualquier punto (API, admin, scripts)
    - Validaciones consistentes
    - Manejo de concurrencia con select_for_update()
    - Transacciones ACID garantizadas
    """
    
    @staticmethod
    def validar_disponibilidad(producto_id: int, cantidad_solicitada: Decimal) -> Dict:
        """
        Valida si hay stock disponible para una operación.
        
        Args:
            producto_id: ID del producto
            cantidad_solicitada: Cantidad que se desea vender/usar
            
        Returns:
            dict con:
                - disponible: bool
                - stock_actual: Decimal
                - faltante: Decimal (si no hay stock suficiente)
                - mensaje: str
        
        Raises:
            ValidationError: Si el producto no existe
        """
        try:
            producto = Productos.objects.get(id_producto=producto_id)
        except Productos.DoesNotExist:
            raise ValidationError(f"Producto ID {producto_id} no existe")
        
        try:
            stock = StockUnico.objects.get(id_producto=producto)
            stock_actual = stock.cantidad
        except StockUnico.DoesNotExist:
            stock_actual = Decimal('0.000')
        
        # Si permite stock negativo, siempre está disponible
        if producto.permite_stock_negativo:
            return {
                'disponible': True,
                'stock_actual': stock_actual,
                'faltante': Decimal('0.000'),
                'mensaje': 'Stock disponible (permite negativo)',
                'permite_negativo': True
            }
        
        # Validar stock suficiente
        disponible = stock_actual >= cantidad_solicitada
        faltante = max(cantidad_solicitada - stock_actual, Decimal('0.000'))
        
        return {
            'disponible': disponible,
            'stock_actual': stock_actual,
            'faltante': faltante,
            'mensaje': 'Stock disponible' if disponible else f'Stock insuficiente. Faltan {faltante} unidades',
            'permite_negativo': False
        }
    
    @staticmethod
    def validar_disponibilidad_multiple(items: List[Dict]) -> Dict:
        """
        Valida disponibilidad para múltiples productos (venta con varios ítems).
        
        Args:
            items: Lista de dict con {'id_producto': int, 'cantidad': Decimal}
            
        Returns:
            dict con:
                - todo_disponible: bool
                - items: lista con resultado por producto
                - productos_faltantes: lista de productos sin stock
        
        Ejemplo:
            >>> items = [
            ...     {'id_producto': 1, 'cantidad': Decimal('5')},
            ...     {'id_producto': 2, 'cantidad': Decimal('10')}
            ... ]
            >>> result = StockService.validar_disponibilidad_multiple(items)
            >>> result['todo_disponible']
            False
        """
        resultados = []
        productos_faltantes = []
        
        for item in items:
            resultado = StockService.validar_disponibilidad(
                item['id_producto'],
                item['cantidad']
            )
            
            # Agregar info del producto
            producto = Productos.objects.get(id_producto=item['id_producto'])
            resultado['producto'] = {
                'id': producto.id_producto,
                'descripcion': producto.descripcion,
                'codigo_barra': producto.codigo_barra
            }
            
            resultados.append(resultado)
            
            if not resultado['disponible']:
                productos_faltantes.append(resultado)
        
        return {
            'todo_disponible': len(productos_faltantes) == 0,
            'items': resultados,
            'productos_faltantes': productos_faltantes
        }
    
    @staticmethod
    @transaction.atomic
    def reservar_stock(producto_id: int, cantidad: Decimal, empleado, motivo='venta') -> StockUnico:
        """
        Reserva stock para una operación (con bloqueo pesimista).
        
        IMPORTANTE: Usa select_for_update() para evitar condiciones de carrera.
        
        Args:
            producto_id: ID del producto
            cantidad: Cantidad a reservar
            empleado: Empleado que autoriza
            motivo: Razón de la reserva
            
        Returns:
            StockUnico actualizado
            
        Raises:
            ValidationError: Si no hay stock disponible o cantidad inválida
        """
        # Validar cantidad > 0
        if cantidad <= 0:
            raise ValidationError({
                'error': 'La cantidad debe ser mayor a 0',
                'cantidad': str(cantidad)
            })
        
        # Validar primero (sin bloqueo)
        validacion = StockService.validar_disponibilidad(producto_id, cantidad)
        
        if not validacion['disponible']:
            raise ValidationError({
                'error': 'Stock insuficiente',
                'producto_id': producto_id,
                'stock_actual': str(validacion['stock_actual']),
                'cantidad_solicitada': str(cantidad),
                'faltante': str(validacion['faltante'])
            })
        
        # BLOQUEO PESIMISTA: select_for_update() garantiza exclusividad
        producto = Productos.objects.get(id_producto=producto_id)
        
        try:
            stock = StockUnico.objects.select_for_update().get(id_producto=producto)
        except StockUnico.DoesNotExist:
            stock = StockUnico.objects.create(
                id_producto=producto,
                cantidad=Decimal('0.000')
            )
        
        # Validar nuevamente con el lock adquirido (por si cambió)
        if not producto.permite_stock_negativo and stock.cantidad < cantidad:
            raise ValidationError({
                'error': 'Stock insuficiente (verificación con lock)',
                'stock_actual': str(stock.cantidad),
                'cantidad_solicitada': str(cantidad)
            })
        
        # Descontar stock
        stock_anterior = stock.cantidad
        stock.cantidad -= cantidad
        stock.save()
        
        # Registrar movimiento de stock
        MovimientosStock.objects.create(
            id_producto=producto,
            tipo_movimiento='Egreso',
            cantidad=cantidad,
            motivo=motivo,
            stock_resultante=stock.cantidad,
            id_empleado_autoriza=empleado
        )
        
        return stock
    
    @staticmethod
    def obtener_productos_bajo_stock() -> List[Dict]:
        """
        Retorna lista de productos que requieren reposición.
        
        Returns:
            Lista de dict con info de productos con stock < stock_minimo
        """
        from django.db.models import F
        
        productos = Productos.objects.filter(
            stock__cantidad__lte=F('stock_minimo'),
            activo=True
        ).select_related('stock').order_by('stock__cantidad')
        
        resultado = []
        for producto in productos:
            try:
                stock = producto.stock.cantidad
            except:
                stock = Decimal('0.000')
            
            resultado.append({
                'id_producto': producto.id_producto,
                'descripcion': producto.descripcion,
                'codigo_barra': producto.codigo_barra,
                'stock_actual': stock,
                'stock_minimo': producto.stock_minimo,
                'faltante': producto.stock_minimo - stock,
                'critico': stock == 0
            })
        
        return resultado
    
    @staticmethod
    def calcular_valor_inventario() -> Dict:
        """
        Calcula el valor total del inventario.
        
        Returns:
            dict con:
                - valor_total: Decimal
                - cantidad_productos: int
                - productos: lista con detalle por producto
        """
        stocks = StockUnico.objects.select_related('id_producto').all()
        
        valor_total = Decimal('0.00')
        productos_detalle = []
        
        for stock in stocks:
            valor_producto = stock.valor_inventario
            valor_total += valor_producto
            
            productos_detalle.append({
                'producto': stock.id_producto.descripcion,
                'cantidad': stock.cantidad,
                'costo_promedio': stock.costo_promedio_ponderado,
                'valor_total': valor_producto
            })
        
        return {
            'valor_total': valor_total,
            'cantidad_productos': len(productos_detalle),
            'productos': sorted(productos_detalle, key=lambda x: x['valor_total'], reverse=True)
        }
    
    @staticmethod
    def obtener_rotacion_inventario(dias=30) -> List[Dict]:
        """
        Calcula la rotación de inventario de los últimos N días.
        
        Formula: Rotación = Ventas / Stock Promedio
        
        Args:
            dias: Periodo a analizar (default 30)
            
        Returns:
            Lista de productos ordenados por rotación (mayor a menor)
        """
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Sum, Avg
        
        fecha_desde = timezone.now() - timedelta(days=dias)
        
        # Obtener ventas por producto
        movimientos_venta = MovimientosStock.objects.filter(
            tipo_movimiento='Egreso',
            motivo='venta',
            fecha_hora__gte=fecha_desde
        ).values('id_producto').annotate(
            total_vendido=Sum('cantidad'),
            stock_promedio=Avg('stock_resultante')
        )
        
        resultado = []
        for mov in movimientos_venta:
            try:
                producto = Productos.objects.get(id_producto=mov['id_producto'])
                stock_promedio = mov['stock_promedio'] or Decimal('1.000')
                
                # Evitar división por cero
                if stock_promedio > 0:
                    rotacion = mov['total_vendido'] / stock_promedio
                else:
                    rotacion = Decimal('0.00')
                
                resultado.append({
                    'producto': producto.descripcion,
                    'total_vendido': mov['total_vendido'],
                    'stock_promedio': stock_promedio,
                    'rotacion': rotacion,
                    'dias_stock': int(stock_promedio / (mov['total_vendido'] / dias)) if mov['total_vendido'] > 0 else 999
                })
            except Productos.DoesNotExist:
                continue
        
        return sorted(resultado, key=lambda x: x['rotacion'], reverse=True)


class AjusteInventarioService:
    """
    Servicio para gestionar ajustes de inventario.
    """
    
    @staticmethod
    @transaction.atomic
    def crear_ajuste(tipo_ajuste, motivo, detalles, empleado_solicita):
        """
        Crea un ajuste de inventario con sus detalles.
        
        Args:
            tipo_ajuste: 'Aumento' o 'Merma'
            motivo: Razón del ajuste
            detalles: Lista de {'id_producto': int, 'cantidad': Decimal}
            empleado_solicita: Empleado que solicita
            
        Returns:
            AjustesInventario creado
        """
        from .models import AjustesInventario, DetallesAjuste
        
        ajuste = AjustesInventario.objects.create(
            tipo_ajuste=tipo_ajuste,
            motivo=motivo,
            estado='Pendiente',
            id_empleado_solicita=empleado_solicita
        )
        
        for detalle in detalles:
            DetallesAjuste.objects.create(
                cantidad_ajustada=detalle['cantidad'],
                id_ajuste=ajuste,
                id_producto_id=detalle['id_producto']
            )
        
        return ajuste
