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
    permite_saldo_negativo = models.IntegerField()
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2)
    notificar_saldo_bajo = models.IntegerField()
    ultima_notificacion_saldo = models.DateTimeField(blank=True, null=True)
    id_hijo = models.OneToOneField('clientes.Hijos', models.DO_NOTHING, db_column='id_hijo')
    codigo_barras = models.CharField(unique=True, max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'tarjetas'

class TarjetasAutorizacion(models.Model):
    id_tarjeta_autorizacion = models.AutoField(primary_key=True)
    codigo_barra = models.CharField(unique=True, max_length=50)
    tipo_autorizacion = models.CharField(max_length=15)
    puede_anular_almuerzos = models.IntegerField()
    puede_anular_ventas = models.IntegerField()
    puede_anular_recargas = models.IntegerField()
    puede_modificar_precios = models.IntegerField()
    activo = models.IntegerField()
    fecha_creacion = models.DateTimeField()
    fecha_vencimiento = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    id_empleado = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='id_empleado', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'tarjetas_autorizacion'

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

    class Meta:
        managed = True
        db_table = 'transacciones_online'

class MediosPago(models.Model):
    id_medio_pago = models.AutoField(primary_key=True)
    descripcion = models.CharField(unique=True, max_length=50)
    genera_comision = models.IntegerField()
    requiere_validacion = models.IntegerField()
    activo = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'medios_pago'

class ConfiguracionSistema(models.Model):
    id_config = models.AutoField(primary_key=True)
    clave = models.CharField(unique=True, max_length=100)
    valor = models.TextField()
    tipo = models.CharField(max_length=20)
    categoria = models.CharField(max_length=50)
    descripcion = models.TextField()
    valor_defecto = models.TextField()
    requerido = models.IntegerField()
    validacion = models.CharField(max_length=500)
    valores_permitidos = models.JSONField()
    valor_min = models.CharField(max_length=100)
    valor_max = models.CharField(max_length=100)
    requiere_reinicio = models.IntegerField()
    solo_superuser = models.IntegerField()
    activo = models.IntegerField()
    updated_at = models.DateTimeField()
    updated_by = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='updated_by', blank=True, null=True)

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
    auto_invalidate = models.IntegerField()
    eventos_invalid = models.JSONField()
    activo = models.IntegerField()
    hits = models.BigIntegerField()
    misses = models.BigIntegerField()
    ultima_limpieza = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'cache_configuracion'
