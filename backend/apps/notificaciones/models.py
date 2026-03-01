"""
Modelos de la app notificaciones
Auto-generados desde la base de datos y organizados por funcionalidad
"""
from django.db import models


class NotificacionesPortal(models.Model):
    id_notificacion = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=50)
    titulo = models.CharField(max_length=255)
    mensaje = models.TextField()
    leida = models.IntegerField()
    fecha_envio = models.DateTimeField()
    fecha_lectura = models.DateTimeField(blank=True, null=True)
    creado_en = models.DateTimeField()
    id_usuario_portal = models.ForeignKey('usuarios.UsuariosPortal', models.DO_NOTHING, db_column='id_usuario_portal')

    class Meta:
        managed = True
        db_table = 'notificaciones_portal'

class NotificacionesSaldo(models.Model):
    id_notificacion = models.BigAutoField(primary_key=True)
    tipo_notificacion = models.CharField(max_length=50)
    saldo_actual = models.DecimalField(max_digits=12, decimal_places=2)
    mensaje = models.TextField()
    enviada_email = models.IntegerField()
    enviada_sms = models.IntegerField()
    leida = models.IntegerField()
    email_destinatario = models.CharField(max_length=254, blank=True, null=True)
    fecha_creacion = models.DateTimeField()
    fecha_envio = models.DateTimeField(blank=True, null=True)
    nro_tarjeta = models.ForeignKey('core.Tarjetas', models.DO_NOTHING, db_column='nro_tarjeta')

    class Meta:
        managed = True
        db_table = 'notificaciones_saldo'

class SolicitudesNotificacion(models.Model):
    id_solicitud = models.BigAutoField(primary_key=True)
    saldo_alerta = models.DecimalField(max_digits=10, decimal_places=2)
    mensaje = models.CharField(max_length=255)
    destino = models.CharField(max_length=8)
    estado = models.CharField(max_length=9, blank=True, null=True)
    fecha_solicitud = models.DateTimeField()
    fecha_envio = models.DateTimeField(blank=True, null=True)
    id_cliente = models.ForeignKey('clientes.Clientes', models.DO_NOTHING, db_column='id_cliente')
    nro_tarjeta = models.ForeignKey('core.Tarjetas', models.DO_NOTHING, db_column='nro_tarjeta')

    class Meta:
        managed = True
        db_table = 'solicitudes_notificacion'

class PreferenciasNotificacion(models.Model):
    id_preferencia = models.AutoField(primary_key=True)
    tipo_notificacion = models.CharField(max_length=50)
    email_activo = models.IntegerField()
    push_activo = models.IntegerField()
    creado_en = models.DateTimeField()
    actualizado_en = models.DateTimeField()
    id_usuario_portal = models.ForeignKey('usuarios.UsuariosPortal', models.DO_NOTHING, db_column='id_usuario_portal')

    class Meta:
        managed = True
        db_table = 'preferencias_notificacion'
        unique_together = (('id_usuario_portal', 'tipo_notificacion'),)

class EmailsEnviados(models.Model):
    id_email = models.AutoField(primary_key=True)
    email_destinatario = models.CharField(max_length=254)
    nombre_destinatario = models.CharField(max_length=100)
    asunto = models.CharField(max_length=200)
    cuerpo = models.TextField()
    estado = models.CharField(max_length=20)
    fecha_envio = models.DateTimeField()
    fecha_entrega = models.DateTimeField(blank=True, null=True)
    fecha_apertura = models.DateTimeField(blank=True, null=True)
    mensaje_error = models.TextField(blank=True, null=True)
    intentos = models.IntegerField()
    id_cliente = models.ForeignKey('clientes.Clientes', models.DO_NOTHING, db_column='id_cliente', blank=True, null=True)
    enviado_por = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='enviado_por', blank=True, null=True)
    id_template = models.ForeignKey('PlantillasEmail', models.DO_NOTHING, db_column='id_template', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'emails_enviados'

class SmsEnviados(models.Model):
    id_sms = models.AutoField(primary_key=True)
    telefono = models.CharField(max_length=20)
    mensaje = models.CharField(max_length=160)
    estado = models.CharField(max_length=20)
    fecha_envio = models.DateTimeField()
    fecha_entrega = models.DateTimeField(blank=True, null=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    id_cliente = models.ForeignKey('clientes.Clientes', models.DO_NOTHING, db_column='id_cliente', blank=True, null=True)
    enviado_por = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='enviado_por', blank=True, null=True)
    id_template = models.ForeignKey('PlantillasSms', models.DO_NOTHING, db_column='id_template', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'sms_enviados'

class PlantillasEmail(models.Model):
    id_template = models.AutoField(primary_key=True)
    codigo = models.CharField(unique=True, max_length=50)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    asunto = models.CharField(max_length=200)
    cuerpo_html = models.TextField()
    cuerpo_texto = models.TextField(blank=True, null=True)
    variables = models.JSONField()
    categoria = models.CharField(max_length=30)
    activo = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='created_by', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'plantillas_email'

class PlantillasSms(models.Model):
    id_template = models.AutoField(primary_key=True)
    codigo = models.CharField(unique=True, max_length=50)
    nombre = models.CharField(max_length=100)
    mensaje = models.CharField(max_length=160)
    variables = models.JSONField()
    categoria = models.CharField(max_length=30)
    activo = models.IntegerField()
    created_at = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'plantillas_sms'

class CampanasComunicacion(models.Model):
    id_campana = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=20)
    segmentacion = models.TextField()
    fecha_programada = models.DateTimeField(blank=True, null=True)
    fecha_enviada = models.DateTimeField(blank=True, null=True)
    estado = models.CharField(max_length=20)
    total_destinatarios = models.IntegerField()
    total_enviados = models.IntegerField()
    total_entregados = models.IntegerField()
    created_at = models.DateTimeField()
    created_by = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='created_by', blank=True, null=True)
    id_email_template = models.ForeignKey('PlantillasEmail', models.DO_NOTHING, db_column='id_email_template', blank=True, null=True)
    id_sms_template = models.ForeignKey('PlantillasSms', models.DO_NOTHING, db_column='id_sms_template', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'campanas_comunicacion'

class AlertasAutomaticas(models.Model):
    id_alerta = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    condicion = models.TextField()
    tipo_alerta = models.CharField(max_length=20)
    criticidad = models.CharField(max_length=10)
    frecuencia_min = models.IntegerField()
    activo = models.IntegerField()
    ultima_verificacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'alertas_automaticas'

class AlertaDestinatarios(models.Model):
    id_destinatario = models.AutoField(primary_key=True)
    via_email = models.IntegerField()
    via_sistema = models.IntegerField()
    activo = models.IntegerField()
    id_alerta = models.ForeignKey('AlertasAutomaticas', models.DO_NOTHING, db_column='id_alerta')
    id_empleado = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='id_empleado')

    class Meta:
        managed = True
        db_table = 'alerta_destinatarios'
        unique_together = (('id_alerta', 'id_empleado'),)

class AlertasSistema(models.Model):
    id_alerta = models.BigAutoField(primary_key=True)
    tipo = models.CharField(max_length=30)
    mensaje = models.CharField(max_length=500)
    fecha_creacion = models.DateTimeField()
    fecha_leida = models.DateTimeField(blank=True, null=True)
    estado = models.CharField(max_length=9, blank=True, null=True)
    id_empleado_resuelve = models.IntegerField(blank=True, null=True)
    fecha_resolucion = models.DateTimeField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'alertas_sistema'

class HistorialAlertas(models.Model):
    id_historial = models.AutoField(primary_key=True)
    fecha_disparada = models.DateTimeField()
    mensaje = models.TextField()
    datos_contexto = models.JSONField()
    resuelto = models.IntegerField()
    fecha_resolucion = models.DateTimeField(blank=True, null=True)
    id_alerta = models.ForeignKey('AlertasAutomaticas', models.DO_NOTHING, db_column='id_alerta')
    resuelto_por = models.ForeignKey('usuarios.Empleados', models.DO_NOTHING, db_column='resuelto_por', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'historial_alertas'

class AnomaliasDetectadas(models.Model):
    id_anomalia = models.AutoField(primary_key=True)
    usuario = models.CharField(max_length=100)
    tipo_anomalia = models.CharField(max_length=30)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    fecha_deteccion = models.DateTimeField()
    descripcion = models.TextField(blank=True, null=True)
    nivel_riesgo = models.CharField(max_length=10)
    notificado = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'anomalias_detectadas'

class RestriccionesHorarias(models.Model):
    id_restriccion = models.AutoField(primary_key=True)
    usuario = models.CharField(max_length=100, blank=True, null=True)
    tipo_usuario = models.CharField(max_length=20)
    dia_semana = models.CharField(max_length=20)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    activo = models.IntegerField()
    fecha_creacion = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'restricciones_horarias'
