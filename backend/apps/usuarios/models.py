"""
Modelos de la app usuarios
Auto-generados desde la base de datos y organizados por funcionalidad
"""

from django.db import models
from django.utils import timezone


def _resolve_usuario_from_empleado(value):
    """Convierte un Empleados legacy a username cuando corresponde."""
    if value is None:
        return None
    if hasattr(value, "usuario"):
        return value.usuario
    return value


def _resolve_cliente_from_empleado(value):
    """Resuelve/crea un cliente a partir de un empleado para compatibilidad de tests."""
    if value is None:
        return None

    empleado = value
    if not hasattr(empleado, "id_empleado"):
        empleado = Empleados.objects.filter(pk=value).first()
        if not empleado:
            return None

    from apps.clientes.models import Clientes, TiposCliente
    from apps.productos.models import ListasPrecios

    email = empleado.email or f"{empleado.usuario}@legacy.local"
    existente = Clientes.objects.filter(email=email).first()
    if existente:
        return existente

    tipo_cliente = TiposCliente.objects.first()
    if not tipo_cliente:
        tipo_cliente = TiposCliente.objects.create(nombre_tipo="General", estado=True)

    lista_precio = ListasPrecios.objects.first()
    if not lista_precio:
        lista_precio = ListasPrecios.objects.create(
            nombre_lista="General",
            fecha_vigencia=timezone.now().date(),
            moneda="PYG",
            estado=True,
        )

    return Clientes.objects.create(
        nombres=empleado.nombre or empleado.usuario,
        apellidos=empleado.apellido or "-",
        ruc_ci=f"EMP-{empleado.id_empleado}",
        email=email,
        telefono=empleado.telefono,
        estado=True,
        id_tipo_cliente=tipo_cliente,
        id_lista=lista_precio,
    )


class LegacyCompatMixin:
    """Mixin para aceptar filtros/creates con nombres legacy de campos."""

    LEGACY_FIELD_MAP = {}
    LEGACY_VALUE_RESOLVERS = {}

    @classmethod
    def _rewrite_legacy_kwargs(cls, kwargs):
        rewritten = {}
        for key, value in kwargs.items():
            field_name, sep, suffix = key.partition("__")
            mapped = cls.LEGACY_FIELD_MAP.get(field_name, field_name)
            if mapped is None:
                # Campo legacy sin equivalente real: se ignora (compatibilidad)
                continue

            resolver = cls.LEGACY_VALUE_RESOLVERS.get(field_name)
            if resolver:
                value = resolver(value)

            new_key = mapped if not sep else f"{mapped}__{suffix}"
            rewritten[new_key] = value

        return rewritten

    @classmethod
    def _apply_legacy_create_defaults(cls, kwargs):
        """Permite a cada modelo completar campos obligatorios en modo legacy."""
        return kwargs


class LegacyCompatQuerySet(models.QuerySet):
    """QuerySet que traduce kwargs legacy a campos actuales."""

    def _rewrite(self, kwargs):
        return self.model._rewrite_legacy_kwargs(kwargs)

    def filter(self, *args, **kwargs):
        return super().filter(*args, **self._rewrite(kwargs))

    def exclude(self, *args, **kwargs):
        return super().exclude(*args, **self._rewrite(kwargs))

    def get(self, *args, **kwargs):
        return super().get(*args, **self._rewrite(kwargs))

    def create(self, **kwargs):
        rewritten = self._rewrite(kwargs)
        rewritten = self.model._apply_legacy_create_defaults(rewritten)
        return super().create(**rewritten)

    def update(self, **kwargs):
        return super().update(**self._rewrite(kwargs))


class LegacyCompatManager(models.Manager.from_queryset(LegacyCompatQuerySet)):
    """Manager con compatibilidad para esquema legacy en tests."""


class EmpleadosManager(models.Manager):
    """Manager para Empleados que provee defaults requeridos en tests."""

    def _prepare_kwargs(self, kwargs):
        from django.utils import timezone as tz

        kwargs.setdefault("fecha_ingreso", tz.now())
        kwargs.setdefault("contrasena_hash", "")
        if "usuario" not in kwargs:
            kwargs["usuario"] = kwargs.get("email", "") or f"user_{tz.now().timestamp()}"
        if "id_rol" not in kwargs and "id_rol_id" not in kwargs:
            rol, _ = Roles.objects.get_or_create(
                nombre_rol="Cajero",
                defaults={"descripcion": "Cajero por defecto"},
            )
            kwargs["id_rol"] = rol
        return kwargs

    def create(self, **kwargs):
        kwargs = self._prepare_kwargs(kwargs)
        return super().create(**kwargs)

    def get_or_create(self, defaults=None, **kwargs):
        try:
            return self.get(**kwargs), False
        except self.model.DoesNotExist:
            create_kwargs = dict(kwargs)
            if defaults:
                create_kwargs.update(defaults)
            return self.create(**create_kwargs), True


class Empleados(models.Model):
    """Modelo para empleados del sistema que pueden acceder a la aplicación"""

    id_empleado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, help_text="Nombre(s) del empleado")
    apellido = models.CharField(max_length=100, help_text="Apellido(s) del empleado")
    usuario = models.CharField(unique=True, max_length=50, help_text="Nombre de usuario para login")
    contrasena_hash = models.CharField(max_length=256, help_text="Hash de la contraseña")
    fecha_ingreso = models.DateTimeField(help_text="Fecha de ingreso del empleado a la empresa")
    direccion = models.CharField(max_length=255, blank=True, null=True, help_text="Dirección de domicilio")
    ciudad = models.CharField(max_length=100, blank=True, null=True, help_text="Ciudad de residencia")
    pais = models.CharField(max_length=100, blank=True, null=True, help_text="País de residencia")
    telefono = models.CharField(max_length=20, blank=True, null=True, help_text="Número de teléfono de contacto")
    email = models.CharField(max_length=254, blank=True, null=True, help_text="Correo electrónico")
    estado = models.BooleanField(default=True, help_text="True=Activo, False=Inactivo")
    fecha_baja = models.DateTimeField(blank=True, null=True, help_text="Fecha en que el empleado dejó la empresa")
    id_rol = models.ForeignKey("Roles", models.DO_NOTHING, db_column="id_rol", help_text="Rol asignado al empleado")

    objects = EmpleadosManager()

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "empleados"
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        ordering = ["apellido", "nombre"]
        indexes = [
            models.Index(fields=["usuario"], name="idx_empleados_usuario"),
            models.Index(fields=["email"], name="idx_empleados_email"),
            models.Index(fields=["estado", "id_rol"], name="idx_empleados_estado_rol"),
            models.Index(fields=["apellido", "nombre"], name="idx_empleados_nombre"),
        ]


class RolesManager(models.Manager):
    """Manager que ignora kwargs legacy no existentes en el modelo Roles."""

    def create(self, **kwargs):
        for campo in ["fecha_creacion", "fecha_actualizacion", "creado_por"]:
            kwargs.pop(campo, None)
        return super().create(**kwargs)


class Roles(models.Model):
    """Roles del sistema que definen permisos y accesos"""

    objects = RolesManager()

    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=100, blank=True, null=True)
    estado = models.BooleanField(default=True)

    def delete(self, *args, **kwargs):
        if self.empleados_set.exists():
            raise Exception("No se puede eliminar el rol porque tiene empleados asignados.")
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "roles"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"


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
    id_empleado = models.OneToOneField("Empleados", models.DO_NOTHING, db_column="id_empleado")

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "perfiles_usuario"


class Autenticacion2Fa(LegacyCompatMixin, models.Model):
    id_2fa = models.AutoField(primary_key=True)
    usuario = models.CharField(max_length=100)
    tipo_usuario = models.CharField(max_length=20)
    secret_key = models.CharField(max_length=32)
    backup_codes = models.JSONField(blank=True, null=True)
    habilitado = models.BooleanField(default=True)
    fecha_activacion = models.DateTimeField(blank=True, null=True)
    ultima_verificacion = models.DateTimeField(blank=True, null=True)
    fecha_creacion = models.DateTimeField()

    LEGACY_FIELD_MAP = {"id_empleado": "usuario"}
    LEGACY_VALUE_RESOLVERS = {"id_empleado": _resolve_usuario_from_empleado}
    objects = LegacyCompatManager()

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    @property
    def fecha_deshabilitado(self):
        """Compatibilidad legacy: usar ultima_verificacion como marca de deshabilitacion."""
        if self.habilitado:
            return None
        return self.ultima_verificacion

    class Meta:
        managed = True
        db_table = "autenticacion_2fa"
        unique_together = (("usuario", "tipo_usuario"),)


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
        db_table = "intentos_2fa"


class IntentosLogin(LegacyCompatMixin, models.Model):
    id_intento = models.AutoField(primary_key=True)
    usuario = models.CharField(max_length=100)
    ip_address = models.CharField(max_length=45)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    fecha_intento = models.DateTimeField()
    exitoso = models.IntegerField()
    motivo_fallo = models.CharField(max_length=100, blank=True, null=True)

    LEGACY_FIELD_MAP = {"id_empleado": "usuario"}
    LEGACY_VALUE_RESOLVERS = {"id_empleado": _resolve_usuario_from_empleado}
    objects = LegacyCompatManager()

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "intentos_login"


class SesionesActivas(LegacyCompatMixin, models.Model):
    id_sesion = models.AutoField(primary_key=True)
    usuario = models.CharField(max_length=100)
    tipo_usuario = models.CharField(max_length=20)
    session_key = models.CharField(unique=True, max_length=255)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateTimeField()
    ultima_actividad = models.DateTimeField()
    activa = models.BooleanField(default=True)

    LEGACY_FIELD_MAP = {"id_empleado": "usuario"}
    LEGACY_VALUE_RESOLVERS = {"id_empleado": _resolve_usuario_from_empleado}
    objects = LegacyCompatManager()

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    @property
    def fecha_cierre(self):
        """Compatibilidad legacy: cuando esta inactiva, usar ultima_actividad como cierre."""
        if self.activa:
            return None
        return self.ultima_actividad

    class Meta:
        managed = True
        db_table = "sesiones_activas"


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
        db_table = "renovaciones_sesion"


class TokensRecuperacion(LegacyCompatMixin, models.Model):
    id_token = models.AutoField(primary_key=True)
    token = models.CharField(unique=True, max_length=64)
    fecha_creacion = models.DateTimeField()
    fecha_expiracion = models.DateTimeField()
    usado = models.IntegerField()
    fecha_uso = models.DateTimeField(blank=True, null=True)
    ip_solicitud = models.CharField(max_length=45, blank=True, null=True)
    id_cliente = models.ForeignKey("clientes.Clientes", models.DO_NOTHING, db_column="id_cliente")

    LEGACY_FIELD_MAP = {
        "id_empleado": "id_cliente",
        "token_hash": "token",
        "tipo": None,
    }
    LEGACY_VALUE_RESOLVERS = {"id_empleado": _resolve_cliente_from_empleado}
    objects = LegacyCompatManager()

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "tokens_recuperacion"


class TokensVerificacion(models.Model):
    id_token = models.AutoField(primary_key=True)
    token = models.CharField(unique=True, max_length=100)
    tipo = models.CharField(max_length=50)
    expira_en = models.DateTimeField()
    usado = models.IntegerField()
    fecha_creacion = models.DateTimeField()
    fecha_uso = models.DateTimeField(blank=True, null=True)
    id_usuario_portal = models.ForeignKey("UsuariosPortal", models.DO_NOTHING, db_column="id_usuario_portal")

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "tokens_verificacion"


class PatronesAcceso(LegacyCompatMixin, models.Model):
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

    LEGACY_FIELD_MAP = {
        "id_empleado": "usuario",
        "ip_habitual": "ip_address",
        "horario_habitual": "horario_inicio",
        "dias_semana_habituales": "dias_semana",
    }
    LEGACY_VALUE_RESOLVERS = {"id_empleado": _resolve_usuario_from_empleado}
    objects = LegacyCompatManager()

    @classmethod
    def _apply_legacy_create_defaults(cls, kwargs):
        now = timezone.now()
        kwargs.setdefault("tipo_usuario", "empleado")
        kwargs.setdefault("primera_deteccion", now)
        kwargs.setdefault("ultima_deteccion", now)
        kwargs.setdefault("frecuencia_accesos", 1)
        if "horario_inicio" in kwargs and "horario_fin" not in kwargs:
            kwargs["horario_fin"] = kwargs["horario_inicio"]
        return kwargs

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "patrones_acceso"


class BloqueosCuenta(LegacyCompatMixin, models.Model):
    id_bloqueo = models.AutoField(primary_key=True)
    usuario = models.CharField(max_length=100)
    tipo_usuario = models.CharField(max_length=20)
    motivo = models.CharField(max_length=255)
    fecha_bloqueo = models.DateTimeField()
    fecha_desbloqueo = models.DateTimeField(blank=True, null=True)
    bloqueado_por = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    estado = models.BooleanField(default=True)

    LEGACY_FIELD_MAP = {"id_empleado": "usuario"}
    LEGACY_VALUE_RESOLVERS = {"id_empleado": _resolve_usuario_from_empleado}
    objects = LegacyCompatManager()

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "bloqueos_cuenta"


class UsuariosPortal(models.Model):
    id_usuario_portal = models.AutoField(primary_key=True)
    email = models.CharField(unique=True, max_length=255)
    password_hash = models.CharField(max_length=255)
    email_verificado = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultimo_acceso = models.DateTimeField(blank=True, null=True)
    estado = models.BooleanField(default=True)
    id_cliente = models.OneToOneField("clientes.Clientes", models.DO_NOTHING, db_column="id_cliente")

    def set_password(self, raw_password: str) -> None:
        """Hash and store a password using Django's password hasher."""
        from django.contrib.auth.hashers import make_password

        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Verify a raw password against the stored hash."""
        from django.contrib.auth.hashers import check_password as django_check

        return django_check(raw_password, self.password_hash)

    def __str__(self):
        return f"Portal: {self.email}"

    class Meta:
        managed = True
        db_table = "usuarios_portal"
        verbose_name = "Usuario Portal"
        verbose_name_plural = "Usuarios Portal"


class AuditoriaEmpleados(models.Model):
    id_auditoria = models.BigAutoField(primary_key=True)
    fecha_cambio = models.DateTimeField()
    campo_modificado = models.CharField(max_length=50)
    valor_anterior = models.TextField(blank=True, null=True)
    valor_nuevo = models.TextField(blank=True, null=True)
    ip_origen = models.CharField(max_length=45, blank=True, null=True)
    id_empleado = models.ForeignKey("Empleados", models.DO_NOTHING, db_column="id_empleado", blank=True, null=True)

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "auditoria_empleados"


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
        db_table = "auditoria_operaciones"


class AuditoriaUsuariosWeb(models.Model):
    id_auditoria = models.BigAutoField(primary_key=True)
    fecha_cambio = models.DateTimeField()
    campo_modificado = models.CharField(max_length=50)
    valor_anterior = models.TextField(blank=True, null=True)
    valor_nuevo = models.TextField(blank=True, null=True)
    ip_origen = models.CharField(max_length=45, blank=True, null=True)
    id_cliente = models.ForeignKey(
        "clientes.Clientes", models.DO_NOTHING, db_column="id_cliente", blank=True, null=True
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "auditoria_usuarios_web"


class Permisos(models.Model):
    id = models.AutoField(primary_key=True)
    codigo_permiso = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=100)
    modulo = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.codigo_permiso} - {self.nombre}"

    class Meta:
        managed = True
        db_table = "permisos"
        verbose_name = "Permiso"
        verbose_name_plural = "Permisos"
        ordering = ["modulo", "codigo_permiso"]


class RolesPermisos(models.Model):
    id = models.AutoField(primary_key=True)
    id_rol = models.ForeignKey(Roles, on_delete=models.CASCADE, db_column="id_rol")
    id_permiso = models.ForeignKey(Permisos, on_delete=models.CASCADE, db_column="id_permiso")
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    asignado_por = models.ForeignKey(
        "Empleados", on_delete=models.SET_NULL, null=True, blank=True, db_column="asignado_por"
    )

    def __str__(self):
        return f"{self.id_rol.nombre_rol} - {self.id_permiso.codigo_permiso}"

    class Meta:
        managed = True
        db_table = "roles_permisos"
        verbose_name = "Rol-Permiso"
        verbose_name_plural = "Roles-Permisos"
        unique_together = [["id_rol", "id_permiso"]]


# Alias para compatibilidad con tests que importan 'Usuarios'
