"""
Modelos de la app usuarios
Auto-generados desde la base de datos y organizados por funcionalidad
"""
from django.db import models


class Empleados(models.Model):
    id_empleado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    usuario = models.CharField(unique=True, max_length=50)
    contrasena_hash = models.CharField(max_length=60)
    fecha_ingreso = models.DateTimeField()
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=254, blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_baja = models.DateTimeField(blank=True, null=True)
    id_rol = models.ForeignKey('Roles', models.DO_NOTHING, db_column='id_rol')

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'empleados'
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'

class Roles(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=100, blank=True, null=True)
    activo = models.BooleanField(default=True)

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'roles'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

class PerfilesUsuario(models.Model):
    id_perfil = models.AutoField(primary_key=True)
    tema = models.CharField(max_length=20)
    idioma = models.CharField(max_length=10)
    timezone = models.CharField(max_length=50)
    dashboard_config = models.JSONField()
    menu_colapsado = models.IntegerField()
    notif_email = models.IntegerField()
    notif_push = models.IntegerField()
    notif_desktop = models.IntegerField()
    formato_fecha = models.CharField(max_length=20)
    moneda = models.CharField(max_length=10)
    config_adicional = models.JSONField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    id_empleado = models.OneToOneField('Empleados', models.DO_NOTHING, db_column='id_empleado')

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'perfiles_usuario'

class Autenticacion2Fa(models.Model):
    id_2fa = models.AutoField(primary_key=True)
    usuario = models.CharField(max_length=100)
    tipo_usuario = models.CharField(max_length=20)
    secret_key = models.CharField(max_length=32)
    backup_codes = models.TextField(blank=True, null=True)
    habilitado = models.BooleanField(default=True)
    fecha_activacion = models.DateTimeField(blank=True, null=True)
    ultima_verificacion = models.DateTimeField(blank=True, null=True)
    fecha_creacion = models.DateTimeField()

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'autenticacion_2fa'
        unique_together = (('usuario', 'tipo_usuario'),)

class Intentos2Fa(models.Model):
    id_intento = models.AutoField(primary_key=True)
    usuario = models.CharField(max_length=100)
    tipo_usuario = models.CharField(max_length=20)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    codigo_ingresado = models.CharField(max_length=10, blank=True, null=True)
    exitoso = models.IntegerField()
    tipo_codigo = models.CharField(max_length=10, blank=True, null=True)
    fecha_intento = models.DateTimeField()

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'intentos_2fa'

class IntentosLogin(models.Model):
    id_intento = models.AutoField(primary_key=True)
    usuario = models.CharField(max_length=100)
    ip_address = models.CharField(max_length=45)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    fecha_intento = models.DateTimeField()
    exitoso = models.IntegerField()
    motivo_fallo = models.CharField(max_length=100, blank=True, null=True)

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'intentos_login'

class SesionesActivas(models.Model):
    id_sesion = models.AutoField(primary_key=True)
    usuario = models.CharField(max_length=100)
    tipo_usuario = models.CharField(max_length=20)
    session_key = models.CharField(unique=True, max_length=255)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateTimeField()
    ultima_actividad = models.DateTimeField()
    activa = models.BooleanField(default=True)

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'sesiones_activas'

class RenovacionesSesion(models.Model):
    id_renovacion = models.AutoField(primary_key=True)
    usuario = models.CharField(max_length=100)
    session_key_anterior = models.CharField(max_length=255, blank=True, null=True)
    session_key_nuevo = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    fecha_renovacion = models.DateTimeField()

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'renovaciones_sesion'

class TokensRecuperacion(models.Model):
    id_token = models.AutoField(primary_key=True)
    token = models.CharField(unique=True, max_length=64)
    fecha_creacion = models.DateTimeField()
    fecha_expiracion = models.DateTimeField()
    usado = models.IntegerField()
    fecha_uso = models.DateTimeField(blank=True, null=True)
    ip_solicitud = models.CharField(max_length=45, blank=True, null=True)
    id_cliente = models.ForeignKey('clientes.Clientes', models.DO_NOTHING, db_column='id_cliente')

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'tokens_recuperacion'

class TokensVerificacion(models.Model):
    id_token = models.AutoField(primary_key=True)
    token = models.CharField(unique=True, max_length=100)
    tipo = models.CharField(max_length=50)
    expira_en = models.DateTimeField()
    usado = models.IntegerField()
    fecha_creacion = models.DateTimeField()
    fecha_uso = models.DateTimeField(blank=True, null=True)
    id_usuario_portal = models.ForeignKey('UsuariosPortal', models.DO_NOTHING, db_column='id_usuario_portal')

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'tokens_verificacion'

class PatronesAcceso(models.Model):
    id_patron = models.AutoField(primary_key=True)
    usuario = models.CharField(max_length=100)
    tipo_usuario = models.CharField(max_length=20)
    ip_address = models.CharField(max_length=45)
    horario_inicio = models.TimeField(blank=True, null=True)
    horario_fin = models.TimeField(blank=True, null=True)
    dias_semana = models.CharField(max_length=50, blank=True, null=True)
    primera_deteccion = models.DateTimeField()
    ultima_deteccion = models.DateTimeField()
    frecuencia_accesos = models.IntegerField()
    es_habitual = models.IntegerField()

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'patrones_acceso'

class BloqueosCuenta(models.Model):
    id_bloqueo = models.AutoField(primary_key=True)
    usuario = models.CharField(max_length=100)
    tipo_usuario = models.CharField(max_length=20)
    motivo = models.CharField(max_length=255)
    fecha_bloqueo = models.DateTimeField()
    fecha_desbloqueo = models.DateTimeField(blank=True, null=True)
    bloqueado_por = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    activo = models.BooleanField(default=True)

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'bloqueos_cuenta'

class UsuariosPortal(models.Model):
    id_usuario_portal = models.AutoField(primary_key=True)
    email = models.CharField(unique=True, max_length=255)
    password_hash = models.CharField(max_length=255)
    email_verificado = models.IntegerField()
    fecha_registro = models.DateTimeField()
    ultimo_acceso = models.DateTimeField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    id_cliente = models.OneToOneField('clientes.Clientes', models.DO_NOTHING, db_column='id_cliente')

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'usuarios_portal'

class UsuariosWebClientes(models.Model):
    id_cliente = models.OneToOneField('clientes.Clientes', models.DO_NOTHING, db_column='id_cliente', primary_key=True)
    usuario = models.CharField(unique=True, max_length=50)
    contrasena_hash = models.CharField(max_length=128)
    ultimo_acceso = models.DateTimeField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'usuarios_web_clientes'

class AuditoriaEmpleados(models.Model):
    id_auditoria = models.BigAutoField(primary_key=True)
    fecha_cambio = models.DateTimeField()
    campo_modificado = models.CharField(max_length=50)
    valor_anterior = models.TextField(blank=True, null=True)
    valor_nuevo = models.TextField(blank=True, null=True)
    ip_origen = models.CharField(max_length=45, blank=True, null=True)
    id_empleado = models.ForeignKey('Empleados', models.DO_NOTHING, db_column='id_empleado', blank=True, null=True)

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'auditoria_empleados'

class AuditoriaOperaciones(models.Model):
    id_auditoria = models.AutoField(primary_key=True)
    usuario = models.CharField(max_length=100)
    tipo_usuario = models.CharField(max_length=20)
    id_usuario = models.IntegerField(blank=True, null=True)
    operacion = models.CharField(max_length=100)
    tabla_afectada = models.CharField(max_length=100, blank=True, null=True)
    id_registro = models.IntegerField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    datos_anteriores = models.JSONField(blank=True, null=True)
    datos_nuevos = models.JSONField(blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    fecha_operacion = models.DateTimeField()
    resultado = models.CharField(max_length=20)
    mensaje_error = models.TextField(blank=True, null=True)

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'auditoria_operaciones'

class AuditoriaUsuariosWeb(models.Model):
    id_auditoria = models.BigAutoField(primary_key=True)
    fecha_cambio = models.DateTimeField()
    campo_modificado = models.CharField(max_length=50)
    valor_anterior = models.TextField(blank=True, null=True)
    valor_nuevo = models.TextField(blank=True, null=True)
    ip_origen = models.CharField(max_length=45, blank=True, null=True)
    id_cliente = models.ForeignKey('clientes.Clientes', models.DO_NOTHING, db_column='id_cliente', blank=True, null=True)

    

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = 'auditoria_usuarios_web'
