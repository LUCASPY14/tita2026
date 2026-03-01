"""
Modelos de la app core
Auto-generados desde la base de datos y organizados por funcionalidad
"""
from django.db import models


class Tarjetas(models.Model):
    nro_tarjeta = models.CharField(primary_key=True, max_length=20)
    saldo_actual = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    saldo_alerta = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_creacion = models.DateTimeField()
    permite_saldo_negativo = models.BooleanField(default=False, help_text="Permite realizar compras con saldo negativo (requiere autorización)")
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2)
    notificar_saldo_bajo = models.BooleanField(default=True, help_text="Enviar notificación cuando el saldo esté bajo")
    ultima_notificacion_saldo = models.DateTimeField(blank=True, null=True)
    id_hijo = models.OneToOneField('clientes.Hijos', models.DO_NOTHING, db_column='id_hijo')
    codigo_barras = models.CharField(unique=True, max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Tarjeta {self.nro_tarjeta} - {self.id_hijo}"

    @property
    def saldo_disponible(self):
        """Calcula el saldo disponible considerando límite de crédito"""
        if self.permite_saldo_negativo:
            return self.saldo_actual + self.limite_credito
        return max(self.saldo_actual, 0)

    @property
    def esta_en_alerta(self):
        """Verifica si el saldo está por debajo del nivel de alerta"""
        if self.saldo_alerta:
            return self.saldo_actual <= self.saldo_alerta
        return False

    @property
    def requiere_notificacion(self):
        """Determina si debe enviarse notificación de saldo bajo"""
        return self.notificar_saldo_bajo and self.esta_en_alerta

    def clean(self):
        """Validar que el hijo no tenga otra tarjeta activa"""
        from django.core.exceptions import ValidationError
        
        if self.id_hijo:
            # Verificar si ya existe otra tarjeta para este hijo
            tarjetas_existentes = Tarjetas.objects.filter(
                id_hijo=self.id_hijo
            ).exclude(nro_tarjeta=self.nro_tarjeta)
            
            if tarjetas_existentes.exists():
                raise ValidationError({
                    'id_hijo': 'Este hijo ya tiene una tarjeta asociada. Solo se permite una tarjeta por hijo.'
                })

    class Meta:
        managed = True
        db_table = 'tarjetas'
        verbose_name = 'Tarjeta'
        verbose_name_plural = 'Tarjetas'

class TarjetasAutorizacion(models.Model):
    id_tarjeta_autorizacion = models.AutoField(primary_key=True)
    codigo_barra = models.CharField(unique=True, max_length=50)
    tipo_autorizacion = models.CharField(max_length=15)
    puede_anular_almuerzos = models.BooleanField(default=False, help_text="Permite anular registros de almuerzo")
    puede_anular_ventas = models.BooleanField(default=False, help_text="Permite anular ventas")
    puede_anular_recargas = models.BooleanField(default=False, help_text="Permite anular recargas de saldo")
    puede_modificar_precios = models.BooleanField(default=False, help_text="Permite modificar precios en punto de venta")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField()
    fecha_vencimiento = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    id_empleado = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='id_empleado', blank=True, null=True)

    def __str__(self):
        return f"Tarjeta Autorización {self.codigo_barra} - {self.tipo_autorizacion}"

    class Meta:
        managed = True
        db_table = 'tarjetas_autorizacion'
        verbose_name = 'Tarjeta de Autorización'
        verbose_name_plural = 'Tarjetas de Autorización'

class CargasSaldo(models.Model):
    id_carga = models.BigAutoField(primary_key=True)
    fecha_carga = models.DateTimeField()
    monto_cargado = models.DecimalField(max_digits=12, decimal_places=2)
    referencia = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=20)
    pay_request_id = models.CharField(max_length=100, blank=True, null=True)
    tx_id = models.CharField(max_length=100, blank=True, null=True)
    fecha_confirmacion = models.DateTimeField(blank=True, null=True)
    custom_identifier = models.CharField(max_length=100, blank=True, null=True)
    id_cliente_origen = models.ForeignKey('clientes.Clientes', models.DO_NOTHING, db_column='id_cliente_origen', blank=True, null=True)
    id_nota = models.BigIntegerField(blank=True, null=True)
    nro_tarjeta = models.ForeignKey('Tarjetas', models.DO_NOTHING, db_column='nro_tarjeta')

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'cargas_saldo'

class ConsumosTarjeta(models.Model):
    id_consumo = models.BigAutoField(primary_key=True)
    fecha_consumo = models.DateTimeField()
    monto_consumido = models.DecimalField(max_digits=12, decimal_places=2)
    detalle = models.CharField(max_length=200, blank=True, null=True)
    saldo_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_posterior = models.DecimalField(max_digits=12, decimal_places=2)
    id_empleado_registro = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='id_empleado_registro', blank=True, null=True)
    nro_tarjeta = models.ForeignKey('Tarjetas', models.DO_NOTHING, db_column='nro_tarjeta')

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'consumos_tarjeta'

class TransaccionesOnline(models.Model):
    id_transaccion = models.AutoField(primary_key=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=20)
    estado = models.CharField(max_length=20)
    referencia_pago = models.CharField(max_length=255, blank=True, null=True)
    id_transaccion_externa = models.CharField(max_length=255, blank=True, null=True)
    datos_extra = models.TextField(blank=True, null=True)
    fecha_transaccion = models.DateTimeField()
    creado_en = models.DateTimeField()
    actualizado_en = models.DateTimeField()
    nro_tarjeta = models.ForeignKey('Tarjetas', models.DO_NOTHING, db_column='nro_tarjeta', blank=True, null=True)
    id_usuario_portal = models.ForeignKey('usuarios.UsuariosPortal', models.DO_NOTHING, db_column='id_usuario_portal', blank=True, null=True)

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'transacciones_online'

class MediosPago(models.Model):
    id_medio_pago = models.AutoField(primary_key=True)
    descripcion = models.CharField(unique=True, max_length=50)
    genera_comision = models.BooleanField(default=False, help_text="Si este medio de pago cobra comisión")
    requiere_validacion = models.BooleanField(default=False, help_text="Requiere validación externa (ej: tarjeta crédito)")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.descripcion

    class Meta:
        managed = True
        db_table = 'medios_pago'
        verbose_name = 'Medio de Pago'
        verbose_name_plural = 'Medios de Pago'

class ConfiguracionSistema(models.Model):
    id_config = models.AutoField(primary_key=True)
    clave = models.CharField(unique=True, max_length=100)
    valor = models.TextField()
    tipo = models.CharField(max_length=20)
    categoria = models.CharField(max_length=50)
    descripcion = models.TextField()
    valor_defecto = models.TextField()
    requerido = models.BooleanField(default=False, help_text="Configuración obligatoria")
    validacion = models.CharField(max_length=500)
    valores_permitidos = models.JSONField()
    valor_min = models.CharField(max_length=100)
    valor_max = models.CharField(max_length=100)
    requiere_reinicio = models.BooleanField(default=False, help_text="Requiere reiniciar el sistema al cambiar")
    solo_superuser = models.BooleanField(default=False, help_text="Solo superusuarios pueden modificar")
    activo = models.BooleanField(default=True)
    updated_at = models.DateTimeField()
    updated_by = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='updated_by', blank=True, null=True)

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'configuracion_sistema'

class CacheConfiguracion(models.Model):
    id_cache = models.AutoField(primary_key=True)
    clave = models.CharField(unique=True, max_length=100)
    descripcion = models.TextField()
    ttl_segundos = models.IntegerField()
    max_size_mb = models.IntegerField()
    tipo_cache = models.CharField(max_length=20)
    auto_invalidate = models.BooleanField(default=True, help_text="Invalidar automáticamente el caché")
    eventos_invalid = models.JSONField()
    activo = models.BooleanField(default=True)
    hits = models.BigIntegerField()
    misses = models.BigIntegerField()
    ultima_limpieza = models.DateTimeField(blank=True, null=True)

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'cache_configuracion'
