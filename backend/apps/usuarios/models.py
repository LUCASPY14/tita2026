"""
Modelos de la app usuarios
Sistema unificado de autenticación para La Cantina de Tita
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


# ==============================================================================
# USUARIO PRINCIPAL — Modelo de autenticación unificado
# ==============================================================================

class UsuarioManager(BaseUserManager):
    """Manager personalizado para el modelo Usuario."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("rol", Usuario.Rol.ADMIN)
        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuario unificado para:
    - Administradores del sistema
    - Cajeros y personal de cocina
    - Clientes del portal web (padres/madres)
    """

    class Rol(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        CAJERO = "CAJERO", "Cajero"
        SUPERVISOR = "SUPERVISOR", "Supervisor"
        COBRADOR = "COBRADOR", "Cobrador"
        COCINA = "COCINA", "Cocina"
        CLIENTE_WEB = "CLIENTE_WEB", "Cliente Portal Web"

    email = models.EmailField(
        unique=True,
        max_length=255,
        help_text="Correo electrónico (usado como nombre de usuario)",
    )
    nombre = models.CharField(max_length=200, help_text="Nombre(s)")
    apellido = models.CharField(max_length=200, help_text="Apellido(s)")
    ci_ruc = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text="CI o RUC — usado para el login del personal interno (roles no CLIENTE_WEB)",
    )
    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.CAJERO,
        help_text="Rol del usuario en el sistema",
    )

    # Relación opcional con Cliente (solo para CLIENTE_WEB)
    cliente = models.OneToOneField(
        "clientes.Cliente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuario_portal",
        help_text="Cliente asociado (solo para usuarios del portal web)",
    )

    # Relación opcional con Empleado (para mantener datos de personal)
    empleado_legacy = models.OneToOneField(
        "Empleado",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuario_django",
        help_text="Registro de empleado asociado (datos de personal)",
    )

    # Campos de estado
    is_active = models.BooleanField(default=True, help_text="False si el usuario está deshabilitado")
    is_staff = models.BooleanField(default=False, help_text="Puede acceder al admin de Django")
    email_verificado = models.BooleanField(default=False, help_text="Email verificado")
    debe_cambiar_contrasena = models.BooleanField(
        default=False,
        help_text="Obliga al usuario a cambiar su contraseña en el próximo ingreso",
    )

    # Campos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    fecha_baja = models.DateTimeField(null=True, blank=True, help_text="Fecha de desactivación")

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre", "apellido"]

    class Meta:
        db_table = "usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["apellido", "nombre"]
        indexes = [
            models.Index(fields=["email"], name="idx_usuarios_email"),
            models.Index(fields=["rol"], name="idx_usuarios_rol"),
            models.Index(fields=["is_active"], name="idx_usuarios_activo"),
            models.Index(fields=["apellido", "nombre"], name="idx_usuarios_nombre"),
        ]

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.get_rol_display()})"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    @property
    def es_cliente_web(self):
        return self.rol == self.Rol.CLIENTE_WEB

    @property
    def es_empleado(self):
        return self.rol in [
            self.Rol.ADMIN, self.Rol.CAJERO, self.Rol.SUPERVISOR,
            self.Rol.COBRADOR, self.Rol.COCINA,
        ]

    def save(self, *args, **kwargs):
        # is_superuser solo tiene sentido para ADMIN; evita escalada de privilegios en el admin Django.
        if self.is_superuser and self.rol != self.Rol.ADMIN:
            raise ValueError(
                f"is_superuser=True solo está permitido para rol ADMIN (rol actual: {self.rol})."
            )
        super().save(*args, **kwargs)


# ==============================================================================
# EMPLEADO — Datos de personal (ya no para autenticación)
# ==============================================================================

class Empleado(models.Model):
    """
    Datos del personal de la cantina.
    La autenticación se maneja con el modelo Usuario.
    Este modelo almacena información laboral.
    """

    id_empleado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, help_text="Nombre(s)")
    apellido = models.CharField(max_length=100, help_text="Apellido(s)")
    fecha_ingreso = models.DateTimeField(default=timezone.now, help_text="Fecha de ingreso")
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True, default="Paraguay")
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    fecha_baja = models.DateTimeField(blank=True, null=True)
    estado = models.BooleanField(default=True, help_text="True=Activo, False=Inactivo")
    id_rol = models.ForeignKey(
        "Rol",
        models.PROTECT,
        db_column="id_rol",
        related_name="empleados",
        help_text="Rol asignado",
    )

    class Meta:
        managed = True
        db_table = "empleados"
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        ordering = ["apellido", "nombre"]
        indexes = [
            models.Index(fields=["email"], name="idx_empleados_email"),
            models.Index(fields=["estado", "id_rol"], name="idx_empleados_estado_rol"),
            models.Index(fields=["apellido", "nombre"], name="idx_empleados_nombre"),
        ]

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


# ==============================================================================
# ROL Y PERMISOS
# ==============================================================================

class Rol(models.Model):
    """Roles del sistema que agrupan permisos."""

    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=100, blank=True, null=True)
    estado = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = "roles"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ["nombre_rol"]

    def __str__(self):
        return self.nombre_rol



class Permiso(models.Model):
    """Permisos individuales del sistema."""

    id = models.AutoField(primary_key=True)
    codigo_permiso = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=100)
    modulo = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = "permisos"
        verbose_name = "Permiso"
        verbose_name_plural = "Permisos"
        ordering = ["modulo", "codigo_permiso"]

    def __str__(self):
        return f"{self.codigo_permiso} - {self.nombre}"


class RolPermiso(models.Model):
    """Relación muchos a muchos entre Roles y Permisos."""

    id = models.AutoField(primary_key=True)
    id_rol = models.ForeignKey(Rol, on_delete=models.CASCADE, db_column="id_rol")
    id_permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE, db_column="id_permiso")
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    asignado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="asignado_por",
    )

    class Meta:
        managed = True
        db_table = "roles_permisos"
        verbose_name = "Rol-Permiso"
        verbose_name_plural = "Roles-Permisos"
        ordering = ["id_rol", "id_permiso"]
        unique_together = [["id_rol", "id_permiso"]]

    def __str__(self):
        return f"{self.id_rol.nombre_rol} - {self.id_permiso.codigo_permiso}"


# ==============================================================================
# PERFIL DE USUARIO
# ==============================================================================

class PerfilUsuario(models.Model):
    """Configuración y preferencias de cada usuario."""

    id_perfil = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name="perfil")
    tema = models.CharField(max_length=20, default="claro")
    idioma = models.CharField(max_length=10, default="es")
    timezone = models.CharField(max_length=50, default="America/Asuncion")
    formato_fecha = models.CharField(max_length=20, default="d/m/Y")
    moneda = models.CharField(max_length=10, default="PYG")
    notif_email = models.BooleanField(default=True)
    notif_push = models.BooleanField(default=True)
    notif_desktop = models.BooleanField(default=False)
    dashboard_config = models.JSONField(default=dict, blank=True)
    menu_colapsado = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "perfiles_usuario"
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"
        ordering = ["id_perfil"]

    def __str__(self):
        return f"Perfil de {self.usuario.nombre_completo}"


# ==============================================================================
# AUTENTICACIÓN 2FA
# ==============================================================================

class Autenticacion2FA(models.Model):
    """Autenticación de dos factores para usuarios."""

    id_2fa = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="auth_2fa",
        unique=True,
    )
    secret_key = models.CharField(max_length=64)
    backup_codes = models.JSONField(default=list, blank=True)
    habilitado = models.BooleanField(default=False)
    fecha_activacion = models.DateTimeField(null=True, blank=True)
    ultima_verificacion = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "autenticacion_2fa"
        verbose_name = "Autenticación 2FA"
        verbose_name_plural = "Autenticaciones 2FA"

    def __str__(self):
        return f"2FA de {self.usuario.email}"


class Intento2FA(models.Model):
    """Registro de intentos de verificación 2FA."""

    id_intento = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="intentos_2fa")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    codigo_ingresado = models.CharField(max_length=10, blank=True, null=True)
    exitoso = models.BooleanField(default=False)
    fecha_intento = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "intentos_2fa"
        verbose_name = "Intento 2FA"
        verbose_name_plural = "Intentos 2FA"

    def __str__(self):
        resultado = "exitoso" if self.exitoso else "fallido"
        return f"Intento {resultado} - {self.usuario.email}"


class CredencialWebAuthn(models.Model):
    """
    Credencial de huella/Face ID (WebAuthn) — un usuario puede tener varias
    (celular, tablet), a diferencia de Autenticacion2FA que es una por usuario.
    """

    id_credencial = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="credenciales_webauthn")
    credential_id = models.CharField(max_length=255, unique=True)
    public_key = models.TextField()
    sign_count = models.PositiveIntegerField(default=0)
    nombre_dispositivo = models.CharField(max_length=100, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultimo_uso = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "credenciales_webauthn"
        verbose_name = "Credencial WebAuthn"
        verbose_name_plural = "Credenciales WebAuthn"

    def __str__(self):
        return f"WebAuthn de {self.usuario.email} ({self.nombre_dispositivo or self.credential_id[:8]})"


# ==============================================================================
# AUDITORÍA Y SEGURIDAD
# ==============================================================================

class IntentoLogin(models.Model):
    """Registro de intentos de inicio de sesión."""

    id_intento = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=255, help_text="Email ingresado en el intento")
    ip_address = models.GenericIPAddressField()
    fecha_intento = models.DateTimeField(auto_now_add=True)
    exitoso = models.BooleanField(default=False)
    motivo_fallo = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "intentos_login"
        verbose_name = "Intento de Login"
        verbose_name_plural = "Intentos de Login"

    def __str__(self):
        resultado = "OK" if self.exitoso else "FAIL"
        return f"[{resultado}] {self.email} - {self.fecha_intento}"


class SesionActiva(models.Model):
    """Sesiones activas de usuarios."""

    id_sesion = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="sesiones")
    session_key = models.CharField(unique=True, max_length=255)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    ultima_actividad = models.DateTimeField(auto_now=True)
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = "sesiones_activas"
        verbose_name = "Sesión Activa"
        verbose_name_plural = "Sesiones Activas"

    def __str__(self):
        return f"Sesión {self.usuario.email} - {'Activa' if self.activa else 'Cerrada'}"


class RenovacionSesion(models.Model):
    """Registro de renovaciones de sesión."""

    id_renovacion = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="renovaciones")
    session_key_anterior = models.CharField(max_length=255, blank=True, null=True)
    session_key_nuevo = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    fecha_renovacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "renovaciones_sesion"
        verbose_name = "Renovación de Sesión"
        verbose_name_plural = "Renovaciones de Sesión"

    def __str__(self):
        return f"Renovación: {self.usuario.email}"


class PatronAcceso(models.Model):
    """Patrones de acceso de usuarios para detección de anomalías."""

    id_patron = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="patrones_acceso")
    ip_address = models.GenericIPAddressField()
    horario_inicio = models.TimeField(blank=True, null=True)
    horario_fin = models.TimeField(blank=True, null=True)
    dias_semana = models.CharField(max_length=50, blank=True, null=True)
    primera_deteccion = models.DateTimeField(auto_now_add=True)
    ultima_deteccion = models.DateTimeField(auto_now=True)
    frecuencia_accesos = models.IntegerField(default=1)
    es_habitual = models.BooleanField(default=False)

    class Meta:
        db_table = "patrones_acceso"
        verbose_name = "Patrón de Acceso"
        verbose_name_plural = "Patrones de Acceso"

    def __str__(self):
        return f"Patrón: {self.usuario.email}"


class BloqueoCuenta(models.Model):
    """Registro de bloqueos de cuenta por seguridad."""

    id_bloqueo = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="bloqueos")
    motivo = models.CharField(max_length=255)
    fecha_bloqueo = models.DateTimeField(auto_now_add=True)
    fecha_desbloqueo = models.DateTimeField(null=True, blank=True)
    bloqueado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bloqueos_realizados",
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    estado = models.BooleanField(default=True, help_text="True si sigue bloqueado")

    class Meta:
        db_table = "bloqueos_cuenta"
        verbose_name = "Bloqueo de Cuenta"
        verbose_name_plural = "Bloqueos de Cuentas"

    def __str__(self):
        return f"Bloqueo: {self.usuario.email} - {self.motivo}"


# ==============================================================================
# TOKENS
# ==============================================================================

class TokenRecuperacion(models.Model):
    """Tokens para recuperación de contraseña."""

    id_token = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="tokens_recuperacion")
    token = models.CharField(unique=True, max_length=64)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    usado = models.BooleanField(default=False)
    fecha_uso = models.DateTimeField(null=True, blank=True)
    ip_solicitud = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        db_table = "tokens_recuperacion"
        verbose_name = "Token de Recuperación"
        verbose_name_plural = "Tokens de Recuperación"

    def __str__(self):
        return f"Token: {self.usuario.email} - {'Usado' if self.usado else 'Válido'}"

    @property
    def es_valido(self):
        return not self.usado and self.fecha_expiracion > timezone.now()


class TokenVerificacion(models.Model):
    """Tokens para verificación de email."""

    id_token = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="tokens_verificacion")
    token = models.CharField(unique=True, max_length=100)
    tipo = models.CharField(max_length=50, default="email_verification")
    expira_en = models.DateTimeField()
    usado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_uso = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "tokens_verificacion"
        verbose_name = "Token de Verificación"
        verbose_name_plural = "Tokens de Verificación"

    def __str__(self):
        return f"Verificación: {self.usuario.email} - {self.tipo}"

    @property
    def es_valido(self):
        return not self.usado and self.expira_en > timezone.now()


# ==============================================================================
# AUDITORÍA DE CAMBIOS
# ==============================================================================

class AuditoriaEmpleado(models.Model):
    """Registro de cambios en datos de empleados."""

    id_auditoria = models.BigAutoField(primary_key=True)
    empleado = models.ForeignKey(
        Empleado, models.SET_NULL, null=True, blank=True, related_name="auditorias"
    )
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    campo_modificado = models.CharField(max_length=50)
    valor_anterior = models.TextField(blank=True, null=True)
    valor_nuevo = models.TextField(blank=True, null=True)
    ip_origen = models.GenericIPAddressField(blank=True, null=True)
    modificado_por = models.ForeignKey(
        Usuario, models.SET_NULL, null=True, blank=True, related_name="auditorias_realizadas"
    )

    class Meta:
        db_table = "auditoria_empleados"
        verbose_name = "Auditoría de Empleado"
        verbose_name_plural = "Auditorías de Empleados"

    def __str__(self):
        return f"Cambio en {self.empleado} - {self.campo_modificado}"


class AuditoriaOperacion(models.Model):
    """Registro de operaciones importantes en el sistema."""

    id_auditoria = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, models.SET_NULL, null=True, blank=True, related_name="operaciones")
    operacion = models.CharField(max_length=100)
    tabla_afectada = models.CharField(max_length=100, blank=True, null=True)
    id_registro = models.IntegerField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    datos_anteriores = models.JSONField(blank=True, null=True)
    datos_nuevos = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    fecha_operacion = models.DateTimeField(auto_now_add=True)
    resultado = models.CharField(max_length=20, default="EXITO")
    mensaje_error = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "auditoria_operaciones"
        verbose_name = "Auditoría de Operación"
        verbose_name_plural = "Auditorías de Operaciones"

    def __str__(self):
        return f"{self.operacion} por {self.usuario} - {self.resultado}"


class AuditoriaUsuarioWeb(models.Model):
    """Auditoría de cambios en usuarios del portal web."""

    id_auditoria = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(
        "clientes.Cliente",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditorias_web",
    )
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    campo_modificado = models.CharField(max_length=50)
    valor_anterior = models.TextField(blank=True, null=True)
    valor_nuevo = models.TextField(blank=True, null=True)
    ip_origen = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        db_table = "auditoria_usuarios_web"
        verbose_name = "Auditoría de Usuario Web"
        verbose_name_plural = "Auditorías de Usuarios Web"

    def __str__(self):
        return f"Cambio web en {self.cliente} - {self.campo_modificado}"
