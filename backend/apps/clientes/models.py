"""
Modelos de la app clientes
Auto-generados desde la base de datos y organizados por funcionalidad
"""
from django.db import models


class Clientes(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    razon_social = models.CharField(max_length=255, blank=True, null=True)
    ruc_ci = models.CharField(unique=True, max_length=20)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=254, blank=True, null=True)
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    activo = models.IntegerField()
    fecha_registro = models.DateTimeField()
    id_lista = models.ForeignKey('productos.ListasPrecios', models.DO_NOTHING, db_column='id_lista')
    id_tipo_cliente = models.ForeignKey('TiposCliente', models.DO_NOTHING, db_column='id_tipo_cliente')

    class Meta:
        managed = True
        db_table = 'clientes'

class TiposCliente(models.Model):
    id_tipo_cliente = models.AutoField(primary_key=True)
    nombre_tipo = models.CharField(unique=True, max_length=50)
    activo = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'tipos_cliente'

class Hijos(models.Model):
    id_hijo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    grado = models.CharField(max_length=50, blank=True, null=True)
    foto_perfil = models.CharField(max_length=255, blank=True, null=True)
    fecha_foto = models.DateTimeField(blank=True, null=True)
    activo = models.IntegerField()
    id_cliente_responsable = models.ForeignKey('Clientes', models.DO_NOTHING, db_column='id_cliente_responsable')

    class Meta:
        managed = True
        db_table = 'hijos'

class Grados(models.Model):
    id_grado = models.AutoField(primary_key=True)
    nombre_grado = models.CharField(unique=True, max_length=50)
    nivel = models.IntegerField()
    orden_visualizacion = models.IntegerField()
    es_ultimo_grado = models.IntegerField()
    activo = models.IntegerField()
    fecha_creacion = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'grados'

class HistorialGradosHijos(models.Model):
    id_historial = models.AutoField(primary_key=True)
    grado_anterior = models.CharField(max_length=50, blank=True, null=True)
    grado_nuevo = models.CharField(max_length=50)
    anio_escolar = models.IntegerField()
    fecha_cambio = models.DateTimeField()
    motivo = models.CharField(max_length=20)
    usuario_registro = models.CharField(max_length=100, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    id_hijo = models.ForeignKey('Hijos', models.DO_NOTHING, db_column='id_hijo')

    class Meta:
        managed = True
        db_table = 'historial_grados_hijos'

class RestriccionesHijos(models.Model):
    id_restriccion = models.AutoField(primary_key=True)
    tipo_restriccion = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    severidad = models.CharField(max_length=20)
    requiere_autorizacion = models.IntegerField()
    fecha_registro = models.DateTimeField()
    fecha_ultima_actualizacion = models.DateTimeField()
    activo = models.IntegerField()
    id_hijo = models.ForeignKey('Hijos', models.DO_NOTHING, db_column='id_hijo')

    class Meta:
        managed = True
        db_table = 'restricciones_hijos'

class AutorizacionesSaldoNegativo(models.Model):
    id_autorizacion = models.BigAutoField(primary_key=True)
    monto_autorizado = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_resultante = models.DecimalField(max_digits=12, decimal_places=2)
    motivo = models.TextField()
    fecha_autorizacion = models.DateTimeField()
    estado = models.CharField(max_length=10)
    id_venta = models.ForeignKey('ventas.Ventas', models.DO_NOTHING, db_column='id_venta')
    id_cliente = models.ForeignKey('Clientes', models.DO_NOTHING, db_column='id_cliente')
    id_empleado_autoriza = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='id_empleado_autoriza')

    class Meta:
        managed = True
        db_table = 'autorizaciones_saldo_negativo'

class LogsAutorizaciones(models.Model):
    id_log = models.BigAutoField(primary_key=True)
    codigo_barra = models.CharField(max_length=50)
    tipo_operacion = models.CharField(max_length=20)
    id_registro_afectado = models.BigIntegerField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    id_usuario = models.IntegerField(blank=True, null=True)
    fecha_hora = models.DateTimeField()
    ip_origen = models.CharField(max_length=45, blank=True, null=True)
    resultado = models.CharField(max_length=15)
    id_tarjeta_autorizacion = models.ForeignKey('core.TarjetasAutorizacion', models.DO_NOTHING, db_column='id_tarjeta_autorizacion')

    class Meta:
        managed = True
        db_table = 'logs_autorizaciones'
