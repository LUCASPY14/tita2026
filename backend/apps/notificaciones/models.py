"""
Modelos de la app notificaciones
Notificaciones a clientes y preferencias
"""

from django.db import models
from django.utils import timezone


# ==============================================================================
# NOTIFICACIÓN (UNIFICADA)
# ==============================================================================

class PushSubscription(models.Model):
    """Suscripción Web Push de un usuario (por dispositivo/navegador)."""

    id_push = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(
        "usuarios.Usuario",
        models.CASCADE,
        related_name="push_subscriptions",
    )
    endpoint = models.URLField(max_length=2000, unique=True)
    p256dh   = models.CharField(max_length=500)
    auth     = models.CharField(max_length=200)
    activa   = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Suscripción Push"
        verbose_name_plural = "Suscripciones Push"
        ordering = ["-fecha_creacion"]
        indexes = [models.Index(fields=["usuario", "activa"])]

    def __str__(self):
        return f"Push {self.usuario} [{self.endpoint[:60]}…]"


class Notificacion(models.Model):
    """Notificación enviada a un usuario del sistema."""

    class Tipo(models.TextChoices):
        SALDO_BAJO  = "SALDO_BAJO",  "Saldo bajo"
        RECARGA     = "RECARGA",     "Recarga exitosa"
        CONSUMO     = "CONSUMO",     "Consumo registrado"
        VENCIMIENTO = "VENCIMIENTO", "Vencimiento de tarjeta"
        ALMUERZO    = "ALMUERZO",    "Cuenta de almuerzo"
        SISTEMA     = "SISTEMA",     "Alerta del sistema"
        VENTA_DEUDA = "VENTA_DEUDA", "Venta con saldo negativo"

    class Destino(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        SISTEMA = "SISTEMA", "En sistema"
        WHATSAPP = "WHATSAPP", "WhatsApp"

    id_notificacion = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(
        "usuarios.Usuario",
        models.CASCADE,
        related_name="notificaciones",
        help_text="Usuario destinatario",
    )
    tipo = models.CharField(max_length=15, choices=Tipo.choices)
    titulo = models.CharField(max_length=255)
    mensaje = models.TextField()
    destino = models.CharField(
        max_length=10, choices=Destino.choices, default=Destino.SISTEMA
    )
    leida = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(default=timezone.now)
    fecha_lectura = models.DateTimeField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    email_intentos = models.PositiveSmallIntegerField(
        default=0,
        help_text="Intentos de envío por email realizados (máx. 3 antes de descartar).",
    )

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-fecha_envio"]
        indexes = [
            models.Index(fields=["usuario", "leida"]),
            models.Index(fields=["tipo"]),
            models.Index(fields=["-fecha_envio"]),
        ]

    def __str__(self):
        return f"[{self.get_tipo_display()}] {self.titulo} - {self.usuario}"


# ==============================================================================
# PREFERENCIA DE NOTIFICACIÓN
# ==============================================================================

class PreferenciaNotificacion(models.Model):
    """Preferencias de notificación por usuario y tipo."""

    id_preferencia = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(
        "usuarios.Usuario",
        models.CASCADE,
        related_name="preferencias_notificacion",
    )
    tipo_notificacion = models.CharField(max_length=50)
    email_activo = models.BooleanField(default=True)
    sistema_activo = models.BooleanField(default=True)
    whatsapp_activo = models.BooleanField(default=False, help_text="Recibir alertas por WhatsApp")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Preferencia de Notificación"
        verbose_name_plural = "Preferencias de Notificaciones"
        ordering = ["usuario", "tipo_notificacion"]
        unique_together = [("usuario", "tipo_notificacion")]

    def __str__(self):
        return f"{self.usuario} - {self.tipo_notificacion}"


# ==============================================================================
# EMAIL ENVIADO
# ==============================================================================

class EmailEnviado(models.Model):
    """Registro de email enviado (auditoría)."""

    class Estado(models.TextChoices):
        ENVIADO = "ENVIADO", "Enviado"
        ENTREGADO = "ENTREGADO", "Entregado"
        ABIERTO = "ABIERTO", "Abierto"
        REBOTADO = "REBOTADO", "Rebotado"
        ERROR = "ERROR", "Error"

    id_email = models.BigAutoField(primary_key=True)
    destinatario_email = models.EmailField(max_length=254)
    destinatario_nombre = models.CharField(max_length=100)
    asunto = models.CharField(max_length=200)
    cuerpo = models.TextField()
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.ENVIADO
    )
    fecha_envio = models.DateTimeField(default=timezone.now)
    fecha_entrega = models.DateTimeField(blank=True, null=True)
    fecha_apertura = models.DateTimeField(blank=True, null=True)
    mensaje_error = models.TextField(blank=True, null=True)
    intentos = models.IntegerField(default=1)
    cliente = models.ForeignKey(
        "clientes.Cliente",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="emails_recibidos",
    )
    enviado_por = models.ForeignKey(
        "usuarios.Usuario",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="emails_enviados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Email Enviado"
        verbose_name_plural = "Emails Enviados"
        ordering = ["-fecha_envio"]

    def __str__(self):
        return f"Email: {self.asunto} - {self.destinatario_email} ({self.get_estado_display()})"


# ==============================================================================
# SOLICITUD DE NOTIFICACIÓN
# ==============================================================================

class SolicitudNotificacion(models.Model):
    """Solicitud de envío de notificación (procesada por Celery o servicio)."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        ENVIADA = "ENVIADA", "Enviada"
        FALLIDA = "FALLIDA", "Fallida"

    id_solicitud_notif = models.BigAutoField(primary_key=True)
    cliente = models.ForeignKey(
        "clientes.Cliente", models.CASCADE, related_name="solicitudes_notificacion"
    )
    tipo = models.CharField(max_length=50)
    mensaje = models.CharField(max_length=255)
    destino = models.CharField(
        max_length=10, choices=Notificacion.Destino.choices
    )
    estado = models.CharField(
        max_length=10, choices=Estado.choices, default=Estado.PENDIENTE
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Solicitud de Notificación"
        verbose_name_plural = "Solicitudes de Notificaciones"
        ordering = ["-fecha_solicitud"]

    def __str__(self):
        return f"Solicitud {self.tipo} - {self.cliente} ({self.get_estado_display()})"
