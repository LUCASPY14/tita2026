"""
Modelos de la app api_integrations
Auto-generados desde la base de datos y organizados por funcionalidad
"""

from django.db import models
from django.utils import timezone


class ProveedoresApiManager(models.Manager):
    def create(self, **kwargs):
        kwargs.setdefault("config_auth", {})
        kwargs.setdefault("timeout", 30)
        kwargs.setdefault("max_reintentos", 3)
        kwargs.setdefault("created_at", timezone.now())
        return super().create(**kwargs)


class ProveedoresApi(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    tipo_servicio = models.CharField(max_length=30)
    url_base = models.CharField(max_length=200)
    version = models.CharField(max_length=20)
    documentacion = models.CharField(max_length=200, blank=True, null=True)
    tipo_auth = models.CharField(max_length=20)
    config_auth = models.JSONField()
    timeout = models.IntegerField()
    max_reintentos = models.IntegerField()
    estado = models.BooleanField(default=True)
    created_at = models.DateTimeField()

    objects = ProveedoresApiManager()

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "proveedores_api"


class EndpointsApiManager(models.Manager):
    def create(self, **kwargs):
        kwargs.setdefault("headers", {})
        kwargs.setdefault("parametros", {})
        kwargs.setdefault("schema_request", {})
        kwargs.setdefault("schema_response", {})
        kwargs.setdefault("cache_segundos", 0)
        kwargs.setdefault("requiere_auth", 1)
        return super().create(**kwargs)


class EndpointsApi(models.Model):
    id_endpoint = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    path = models.CharField(max_length=200)
    metodo = models.CharField(max_length=10)
    headers = models.JSONField()
    parametros = models.JSONField()
    schema_request = models.JSONField()
    schema_response = models.JSONField()
    cache_segundos = models.IntegerField()
    requiere_auth = models.IntegerField()
    estado = models.BooleanField(default=True)
    id_proveedor = models.ForeignKey("ProveedoresApi", models.DO_NOTHING, db_column="id_proveedor")

    objects = EndpointsApiManager()

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "endpoints_api"


class LogsLlamadasApiManager(models.Manager):
    def create(self, **kwargs):
        kwargs.setdefault("timestamp", timezone.now())
        kwargs.setdefault("metodo", "GET")
        kwargs.setdefault("url", "")
        kwargs.setdefault("headers_req", {})
        kwargs.setdefault("status_code", 200)
        kwargs.setdefault("headers_res", {})
        kwargs.setdefault("tiempo_ms", 0)
        kwargs.setdefault("exitoso", 1)
        kwargs.setdefault("intento", 1)
        kwargs.setdefault("contexto", {})
        return super().create(**kwargs)


class LogsLlamadasApi(models.Model):
    id_log = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    metodo = models.CharField(max_length=10)
    url = models.CharField(max_length=500)
    headers_req = models.JSONField()
    payload_req = models.TextField(blank=True, null=True)
    status_code = models.IntegerField()
    headers_res = models.JSONField()
    payload_res = models.TextField(blank=True, null=True)
    tiempo_ms = models.IntegerField()
    bytes_sent = models.IntegerField(blank=True, null=True)
    bytes_received = models.IntegerField(blank=True, null=True)
    exitoso = models.IntegerField()
    error_msg = models.TextField(blank=True, null=True)
    intento = models.IntegerField()
    ip_origen = models.CharField(max_length=39, blank=True, null=True)
    contexto = models.JSONField()
    id_endpoint = models.ForeignKey("EndpointsApi", models.DO_NOTHING, db_column="id_endpoint", blank=True, null=True)
    id_empleado = models.ForeignKey(
        "usuarios.Empleados", models.DO_NOTHING, db_column="id_empleado", blank=True, null=True
    )

    objects = LogsLlamadasApiManager()

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "logs_llamadas_api"


class CredencialesApi(models.Model):
    id_credencial = models.AutoField(primary_key=True)
    ambiente = models.CharField(max_length=20)
    api_key = models.TextField(blank=True, null=True)
    secret = models.TextField(blank=True, null=True)
    token = models.TextField(blank=True, null=True)
    configuracion = models.JSONField()
    fecha_expiracion = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField()
    estado = models.BooleanField(default=True)
    id_proveedor = models.ForeignKey("ProveedoresApi", models.DO_NOTHING, db_column="id_proveedor")

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "credenciales_api"
        unique_together = (("id_proveedor", "ambiente"),)


class LogsWebhooks(models.Model):
    id_log = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    headers = models.JSONField()
    payload = models.TextField()
    evento_tipo = models.CharField(max_length=100)
    verificacion_ok = models.IntegerField()
    procesado_ok = models.IntegerField()
    tiempo_proc_ms = models.IntegerField(blank=True, null=True)
    error_msg = models.TextField(blank=True, null=True)
    ip_origen = models.CharField(max_length=39)
    user_agent = models.TextField(blank=True, null=True)
    id_webhook = models.ForeignKey("WebhookEndpoints", models.DO_NOTHING, db_column="id_webhook", blank=True, null=True)

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "logs_webhooks"


class WebhookEndpoints(models.Model):
    id_webhook = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    path = models.CharField(max_length=200)
    requiere_verificacion = models.IntegerField()
    secret_key = models.CharField(max_length=255)
    header_verificacion = models.CharField(max_length=100)
    eventos = models.JSONField()
    handler_func = models.CharField(max_length=200)
    estado = models.BooleanField(default=True)
    created_at = models.DateTimeField()
    id_proveedor = models.ForeignKey("ProveedoresApi", models.DO_NOTHING, db_column="id_proveedor")

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "webhook_endpoints"
        unique_together = (("id_proveedor", "path"),)
