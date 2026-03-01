"""
Modelos de la app inventario
Gestión de stock, movimientos y costos con consistencia ACID
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal


class StockUnico(models.Model):
    """
    Inventario actual de cada producto.
    
    Reglas de negocio:
    - Un solo registro por producto (OneToOne)
    - Stock nunca puede ser negativo (excepto si producto permite_stock_negativo)
    - Toda actualización debe estar respaldada por MovimientosStock
    - Se usa select_for_update() para evitar condiciones de carrera
    """
    id_stock = models.AutoField(primary_key=True)
    cantidad = models.DecimalField(
        max_digits=10, 
        decimal_places=3,
        help_text="Stock actual disponible"
    )
    fecha_ultima_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text="Última modificación del stock"
    )
    id_producto = models.OneToOneField(
        'productos.Productos', 
        models.DO_NOTHING, 
        db_column='id_producto',
        related_name='stock'
    )

    class Meta:
        managed = True
        db_table = 'stock_unico'
        verbose_name = 'Stock'
        verbose_name_plural = 'Stocks'
        indexes = [
            models.Index(fields=['id_producto']),
            models.Index(fields=['-fecha_ultima_actualizacion']),
        ]

    def __str__(self):
        return f"{self.id_producto.descripcion}: {self.cantidad} unidades"
    
    @property
    def costo_promedio_ponderado(self):
        """
        Calcula el costo promedio ponderado basado en las últimas compras.
        
        Fórmula: Σ(costo_unitario × cantidad) / Σ(cantidad)
        
        Returns:
            Decimal: Costo promedio o 0 si no hay compras
        """
        from django.db.models import Sum, F
        
        costos = CostosHistoricos.objects.filter(
            id_producto=self.id_producto
        ).aggregate(
            total_monto=Sum(F('costo_unitario') * F('cantidad_comprada')),
            total_cantidad=Sum('cantidad_comprada')
        )
        
        if costos['total_cantidad'] and costos['total_cantidad'] > 0:
            return (costos['total_monto'] / costos['total_cantidad']).quantize(Decimal('0.01'))
        return Decimal('0.00')
    
    @property
    def valor_inventario(self):
        """
        Calcula el valor total del inventario de este producto.
        
        Returns:
            Decimal: cantidad × costo_promedio_ponderado
        """
        return (self.cantidad * self.costo_promedio_ponderado).quantize(Decimal('0.01'))
    
    @property
    def requiere_reposicion(self):
        """Verifica si el stock está por debajo del mínimo"""
        return self.cantidad <= self.id_producto.stock_minimo
    
    @property
    def dias_stock_disponible(self):
        """
        Calcula cuántos días durará el stock actual según venta promedio.
        
        Returns:
            int: Días estimados o None si no hay ventas
        """
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Sum
        
        # Ventas de últimos 30 días
        hace_30_dias = timezone.now() - timedelta(days=30)
        
        ventas_mes = MovimientosStock.objects.filter(
            id_producto=self.id_producto,
            tipo_movimiento='Egreso',
            fecha_hora__gte=hace_30_dias
        ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0')
        
        if ventas_mes > 0:
            venta_promedio_diaria = ventas_mes / 30
            return int(self.cantidad / venta_promedio_diaria)
        
        return None
    
    def clean(self):
        """
        Validaciones del modelo.
        
        Regla de oro: No permitir stock negativo excepto si producto lo permite
        """
        if self.cantidad < 0 and not self.id_producto.permite_stock_negativo:
            raise ValidationError({
                'cantidad': f'El producto {self.id_producto.descripcion} no permite stock negativo. Stock actual: {self.cantidad}'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class MovimientosStock(models.Model):
    """
    Historial de todos los movimientos de inventario.
    
    Reglas críticas:
    - NUNCA eliminar movimientos (auditoría)
    - Cada movimiento debe tener un motivo específico
    - stock_resultante debe coincidir con StockUnico.cantidad
    - Se registra quién autorizó cada movimiento
    
    Tipos de movimiento:
    - Ingreso: Aumenta stock (compras, devoluciones cliente, ajustes positivos)
    - Egreso: Disminuye stock (ventas, devoluciones proveedor, mermas)
    """
    
    TIPO_MOVIMIENTO_CHOICES = [
        ('Ingreso', 'Ingreso'),
        ('Egreso', 'Egreso'),
    ]
    
    MOTIVO_CHOICES = [
        ('compra', 'Compra a proveedor'),
        ('venta', 'Venta a cliente'),
        ('ajuste_aumento', 'Ajuste de inventario (aumento)'),
        ('ajuste_merma', 'Ajuste de inventario (merma)'),
        ('devolucion_cliente', 'Devolución de cliente'),
        ('devolucion_proveedor', 'Devolución a proveedor'),
        ('correccion_manual', 'Corrección manual'),
        ('transferencia', 'Transferencia entre sucursales'),
        ('producto_vencido', 'Baja por vencimiento'),
        ('producto_danado', 'Baja por daño físico'),
        ('inventario_inicial', 'Inventario inicial'),
    ]
    
    id_movimiento_stock = models.BigAutoField(primary_key=True)
    fecha_hora = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora del movimiento"
    )
    tipo_movimiento = models.CharField(
        max_length=7,
        choices=TIPO_MOVIMIENTO_CHOICES,
        help_text="Ingreso o Egreso"
    )
    motivo = models.CharField(
        max_length=50,
        choices=MOTIVO_CHOICES,
        default='correccion_manual',
        help_text="Razón específica del movimiento"
    )
    cantidad = models.DecimalField(
        max_digits=10, 
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        help_text="Cantidad del movimiento (siempre positiva)"
    )
    stock_resultante = models.DecimalField(
        max_digits=10, 
        decimal_places=3,
        help_text="Stock después del movimiento"
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        help_text="Notas adicionales sobre el movimiento"
    )
    id_compra = models.ForeignKey(
        'compras.Compras', 
        models.DO_NOTHING, 
        db_column='id_compra', 
        blank=True, 
        null=True,
        related_name='movimientos_stock'
    )
    id_venta = models.ForeignKey(
        'ventas.Ventas', 
        models.DO_NOTHING, 
        db_column='id_venta', 
        blank=True, 
        null=True,
        related_name='movimientos_stock'
    )
    id_ajuste = models.BigIntegerField(
        blank=True, 
        null=True,
        help_text="ID del ajuste de inventario asociado"
    )
    id_empleado_autoriza = models.ForeignKey(
        'usuarios.Empleados', 
        models.DO_NOTHING, 
        db_column='id_empleado_autoriza',
        related_name='movimientos_autorizados'
    )
    id_producto = models.ForeignKey(
        'productos.Productos', 
        models.DO_NOTHING, 
        db_column='id_producto',
        related_name='movimientos_stock'
    )

    class Meta:
        managed = True
        db_table = 'movimientos_stock'
        verbose_name = 'Movimiento de Stock'
        verbose_name_plural = 'Movimientos de Stock'
        ordering = ['-fecha_hora']
        indexes = [
            models.Index(fields=['id_producto', '-fecha_hora']),
            models.Index(fields=['tipo_movimiento', 'motivo']),
            models.Index(fields=['-fecha_hora']),
        ]

    def __str__(self):
        signo = '+' if self.tipo_movimiento == 'Ingreso' else '-'
        return f"{self.id_producto.descripcion}: {signo}{self.cantidad} ({self.get_motivo_display()})"
    
    def clean(self):
        """Validaciones de consistencia"""
        # La cantidad siempre debe ser positiva
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a cero'})
        
        # Validar coherencia tipo_movimiento y motivo
        motivos_ingreso = ['compra', 'ajuste_aumento', 'devolucion_cliente', 'inventario_inicial', 'transferencia']
        motivos_egreso = ['venta', 'ajuste_merma', 'devolucion_proveedor', 'producto_vencido', 'producto_danado']
        
        if self.tipo_movimiento == 'Ingreso' and self.motivo in motivos_egreso:
            raise ValidationError({
                'motivo': f'El motivo "{self.get_motivo_display()}" no es válido para un Ingreso'
            })
        
        if self.tipo_movimiento == 'Egreso' and self.motivo in motivos_ingreso:
            raise ValidationError({
                'motivo': f'El motivo "{self.get_motivo_display()}" no es válido para un Egreso'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class AjustesInventario(models.Model):
    """
    Ajustes manuales de inventario (aumentos o mermas).
    
    Flujo:
    1. Se crea con estado='Pendiente'
    2. Supervisor revisa y cambia a 'Aprobado' o 'Rechazado'
    3. Si se aprueba, signal crea MovimientosStock y actualiza StockUnico
    """
    
    TIPO_AJUSTE_CHOICES = [
        ('Aumento', 'Aumento de stock'),
        ('Merma', 'Disminución de stock'),
    ]
    
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente de aprobación'),
        ('Aprobado', 'Aprobado y aplicado'),
        ('Rechazado', 'Rechazado'),
    ]
    
    id_ajuste = models.BigAutoField(primary_key=True)
    fecha_hora = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de creación del ajuste"
    )
    tipo_ajuste = models.CharField(
        max_length=8,
        choices=TIPO_AJUSTE_CHOICES,
        help_text="Aumento o Merma"
    )
    motivo = models.CharField(
        max_length=255,
        help_text="Razón del ajuste"
    )
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='Pendiente',
        help_text="Estado del ajuste"
    )
    fecha_aprobacion = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Cuándo fue aprobado/rechazado"
    )
    id_empleado_solicita = models.ForeignKey(
        'usuarios.Empleados',
        models.DO_NOTHING,
        db_column='id_empleado_solicita',
        blank=True,
        null=True,
        related_name='ajustes_solicitados',
        help_text="Empleado que solicita el ajuste"
    )
    id_empleado_aprueba = models.ForeignKey(
        'usuarios.Empleados',
        models.DO_NOTHING,
        db_column='id_empleado_aprueba',
        blank=True,
        null=True,
        related_name='ajustes_aprobados',
        help_text="Supervisor que aprueba/rechaza"
    )

    class Meta:
        managed = True
        db_table = 'ajustes_inventario'
        verbose_name = 'Ajuste de Inventario'
        verbose_name_plural = 'Ajustes de Inventario'
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"Ajuste #{self.id_ajuste} - {self.tipo_ajuste} ({self.estado})"


class DetallesAjuste(models.Model):
    """
    Detalles de cada producto en un ajuste de inventario.
    """
    id_detalle = models.BigAutoField(primary_key=True)
    cantidad_ajustada = models.DecimalField(
        max_digits=8, 
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        help_text="Cantidad a ajustar (siempre positiva)"
    )
    id_ajuste = models.ForeignKey(
        'AjustesInventario', 
        models.DO_NOTHING, 
        db_column='id_ajuste',
        related_name='detalles'
    )
    id_movimiento_stock = models.OneToOneField(
        'MovimientosStock', 
        models.DO_NOTHING, 
        db_column='id_movimiento_stock',
        blank=True,
        null=True,
        help_text="Movimiento creado al aprobar"
    )
    id_producto = models.ForeignKey(
        'productos.Productos', 
        models.DO_NOTHING, 
        db_column='id_producto'
    )

    class Meta:
        managed = True
        db_table = 'detalles_ajuste'
        unique_together = (('id_ajuste', 'id_producto'),)
        verbose_name = 'Detalle de Ajuste'
        verbose_name_plural = 'Detalles de Ajustes'

    def __str__(self):
        return f"{self.id_producto.descripcion}: {self.cantidad_ajustada}"


class CostosHistoricos(models.Model):
    """
    Historial de costos de compra para calcular costo promedio ponderado.
    
    Se registra cada vez que se recibe una compra.
    """
    id_costo_historico = models.BigAutoField(primary_key=True)
    costo_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Costo de compra por unidad"
    )
    cantidad_comprada = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=Decimal('1.000'),
        help_text="Cantidad comprada a este costo"
    )
    fecha_compra = models.DateTimeField(
        help_text="Fecha de la compra"
    )
    id_compra = models.ForeignKey(
        'compras.Compras', 
        models.DO_NOTHING, 
        db_column='id_compra', 
        blank=True, 
        null=True,
        related_name='costos_productos'
    )
    id_producto = models.ForeignKey(
        'productos.Productos', 
        models.DO_NOTHING, 
        db_column='id_producto',
        related_name='costos_historicos'
    )

    class Meta:
        managed = True
        db_table = 'costos_historicos'
        verbose_name = 'Costo Histórico'
        verbose_name_plural = 'Costos Históricos'
        ordering = ['-fecha_compra']
        indexes = [
            models.Index(fields=['id_producto', '-fecha_compra']),
        ]

    def __str__(self):
        return f"{self.id_producto.descripcion}: Gs. {self.costo_unitario:,.0f} ({self.fecha_compra.date()})"
    
    @property
    def costo_total(self):
        """Costo total de esta compra"""
        return (self.costo_unitario * self.cantidad_comprada).quantize(Decimal('0.01'))


class AlertasStock(models.Model):
    """
    Alertas de stock mínimo para evitar disparar notificaciones duplicadas.
    
    Reglas:
    - Se crea cuando stock pasa por debajo del mínimo
    - Se marca como resuelta cuando stock vuelve arriba del mínimo
    - No se crean alertas duplicadas mientras esté activa
    """
    
    TIPO_ALERTA_CHOICES = [
        ('stock_minimo', 'Stock por debajo del mínimo'),
        ('stock_cero', 'Stock agotado'),
        ('stock_critico', 'Stock crítico (50% del mínimo)'),
    ]
    
    id_alerta = models.BigAutoField(primary_key=True)
    tipo_alerta = models.CharField(
        max_length=20,
        choices=TIPO_ALERTA_CHOICES,
        default='stock_minimo'
    )
    stock_actual = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text="Stock cuando se generó la alerta"
    )
    stock_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        help_text="Stock mínimo configurado"
    )
    fecha_generada = models.DateTimeField(
        auto_now_add=True
    )
    fecha_resuelta = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Cuándo se resolvió (stock volvió arriba del mínimo)"
    )
    activa = models.BooleanField(
        default=True,
        help_text="False cuando se resuelve"
    )
    notificacion_enviada = models.BooleanField(
        default=False,
        help_text="Si ya se envió notificación"
    )
    id_producto = models.ForeignKey(
        'productos.Productos',
        models.DO_NOTHING,
        db_column='id_producto',
        related_name='alertas_stock'
    )
    
    class Meta:
        managed = True
        db_table = 'alertas_stock'
        verbose_name = 'Alerta de Stock'
        verbose_name_plural = 'Alertas de Stock'
        ordering = ['-fecha_generada']
        indexes = [
            models.Index(fields=['id_producto', 'activa']),
            models.Index(fields=['-fecha_generada']),
        ]
    
    def __str__(self):
        estado = "Activa" if self.activa else "Resuelta"
        return f"{self.id_producto.descripcion}: {self.get_tipo_alerta_display()} - {estado}"
