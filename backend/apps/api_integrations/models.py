"""
Modelos de la app api_integrations
Gestión de APIs externas, webhooks, credenciales y logs
"""

from django.db import models
from django.utils import timezone


# ==============================================================================
# PROVEEDOR DE API
# ==============================================================================

class ProveedorApi(models.Model):
    """Proveedor de servicios API externo (SIPAP, banco, etc.)."""

    class TipoServicio(models.TextChoices):
        PAGOS_QR = "PAGOS_QR", "Pagos QR (SIPAP)"
        BANCO = "BANCO", "Banco"
        NOTIFICACIONES = "NOTIFICACIONES", "Notificaciones"
        OTRO = "OTRO", "Otro"

    class TipoAuth(models.TextChoices):
        API_KEY = "API_KEY", "API Key"
        BEARER = "BEARER", "Bearer Token"
        BASIC = "BASIC", "Basic Auth"
        OAUTH2 = "OAUTH2", "OAuth 2.0"

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, default="")
    tipo_servicio = models.CharField(max_length=20, choices=TipoServicio.choices)
    url_base = models.CharField(max_length=200)
    version = models.CharField(max_length=20, blank=True, null=True)
    documentacion = models.URLField(max_length=200, blank=True, null=True)
    tipo_auth = models.CharField(max_length=10, choices=TipoAuth.choices)
    config_auth = models.JSONField(default=dict)
    timeout = models.IntegerField(default=30, help_text="Timeout en segundos")
    max_reintentos = models.IntegerField(default=3)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proveedor de API"
        verbose_name_plural = "Proveedores de API"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_servicio_display()})"


# ==============================================================================
# ENDPOINT DE API
# ==============================================================================

class EndpointApi(models.Model):
    """Endpoint específico de un proveedor de API."""

    class Metodo(models.TextChoices):
        GET = "GET", "GET"
        POST = "POST", "POST"
        PUT = "PUT", "PUT"
        PATCH = "PATCH", "PATCH"
        DELETE = "DELETE", "DELETE"

    proveedor = models.ForeignKey(
        ProveedorApi, models.CASCADE, related_name="endpoints"
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, default="")
    path = models.CharField(max_length=200)
    metodo = models.CharField(max_length=6, choices=Metodo.choices)
    headers = models.JSONField(default=dict, help_text="Headers por defecto")
    parametros = models.JSONField(default=dict, help_text="Parámetros por defecto")
    schema_request = models.JSONField(default=dict, help_text="Schema esperado del request")
    schema_response = models.JSONField(default=dict, help_text="Schema esperado del response")
    cache_segundos = models.IntegerField(default=0, help_text="0 = sin caché")
    requiere_auth = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Endpoint de API"
        verbose_name_plural = "Endpoints de API"
        unique_together = [("proveedor", "path", "metodo")]

    def __str__(self):
        return f"{self.get_metodo_display()} {self.path} ({self.proveedor})"


# ==============================================================================
# CREDENCIALES DE API
# ==============================================================================

class CredencialApi(models.Model):
    """Credenciales por ambiente (sandbox/producción) para un proveedor."""

    class Ambiente(models.TextChoices):
        SANDBOX = "SANDBOX", "Sandbox"
        PRODUCCION = "PRODUCCION", "Producción"

    proveedor = models.ForeignKey(
        ProveedorApi, models.CASCADE, related_name="credenciales"
    )
    ambiente = models.CharField(max_length=15, choices=Ambiente.choices)
    api_key = models.TextField(blank=True, null=True)
    secret = models.TextField(blank=True, null=True)
    token = models.TextField(blank=True, null=True)
    configuracion = models.JSONField(default=dict)
    fecha_expiracion = models.DateTimeField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Credencial de API"
        verbose_name_plural = "Credenciales de API"
        unique_together = [("proveedor", "ambiente")]

    def __str__(self):
        return f"{self.proveedor} - {self.get_ambiente_display()}"


# ==============================================================================
# WEBHOOK ENDPOINT
# ==============================================================================

class WebhookEndpoint(models.Model):
    """Webhook entrante (para recibir notificaciones de SIPAP, bancos, etc.)."""

    proveedor = models.ForeignKey(
        ProveedorApi, models.CASCADE, related_name="webhooks"
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, default="")
    path = models.CharField(max_length=200, help_text="Ruta del webhook (ej: /api/webhooks/sipap/)")
    requiere_verificacion = models.BooleanField(default=True)
    secret_key = models.CharField(
        max_length=255, help_text="Clave secreta para validar firma"
    )
    header_verificacion = models.CharField(
        max_length=100, help_text="Nombre del header que contiene la firma"
    )
    eventos = models.JSONField(default=list, help_text="Eventos que acepta este webhook")
    handler = models.CharField(
        max_length=200, help_text="Función o ruta que procesa el webhook"
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Webhook Endpoint"
        verbose_name_plural = "Webhook Endpoints"
        unique_together = [("proveedor", "path")]

    def __str__(self):
        return f"Webhook {self.path} ({self.proveedor})"


# ==============================================================================
# LOGS
# ==============================================================================

class LogLlamadaApi(models.Model):
    """Registro de llamada a API externa (auditoría y debugging)."""

    endpoint = models.ForeignKey(
        EndpointApi, models.SET_NULL, null=True, blank=True, related_name="logs"
    )
    usuario = models.ForeignKey(
        "usuarios.Usuario",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs_api",
    )
    timestamp = models.DateTimeField(default=timezone.now)
    metodo = models.CharField(max_length=10)
    url = models.CharField(max_length=500)
    headers_req = models.JSONField(default=dict)
    payload_req = models.TextField(blank=True, null=True)
    status_code = models.IntegerField()
    headers_res = models.JSONField(default=dict)
    payload_res = models.TextField(blank=True, null=True)
    tiempo_ms = models.IntegerField()
    bytes_sent = models.IntegerField(blank=True, null=True)
    bytes_received = models.IntegerField(blank=True, null=True)
    exitoso = models.BooleanField(default=True)
    error_msg = models.TextField(blank=True, null=True)
    intento = models.IntegerField(default=1)
    ip_origen = models.GenericIPAddressField(blank=True, null=True)
    contexto = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Log de Llamada API"
        verbose_name_plural = "Logs de Llamadas API"
        ordering = ["-timestamp"]

    def __str__(self):
        resultado = "✓" if self.exitoso else "✗"
        return f"[{resultado}] {self.metodo} {self.url} ({self.tiempo_ms}ms)"


class LogWebhook(models.Model):
    """Registro de webhook recibido (auditoría)."""

    webhook = models.ForeignKey(
        WebhookEndpoint, models.SET_NULL, null=True, blank=True, related_name="logs"
    )
    timestamp = models.DateTimeField(default=timezone.now)
    headers = models.JSONField(default=dict)
    payload = models.TextField()
    evento_tipo = models.CharField(max_length=100)
    verificacion_ok = models.BooleanField(default=False)
    procesado_ok = models.BooleanField(default=False)
    tiempo_proc_ms = models.IntegerField(blank=True, null=True)
    error_msg = models.TextField(blank=True, null=True)
    ip_origen = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Log de Webhook"
        verbose_name_plural = "Logs de Webhooks"
        ordering = ["-timestamp"]

    def __str__(self):
        resultado = "✓" if self.procesado_ok else "✗"
        return f"Webhook {self.evento_tipo} [{resultado}]"