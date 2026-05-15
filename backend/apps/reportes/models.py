"""
Modelos de la app reportes
Plantillas de reportes predefinidos
"""

from django.db import models
from django.utils import timezone


class PlantillaReporte(models.Model):
    """Reporte predefinido con parámetros configurables."""

    class Tipo(models.TextChoices):
        VENTAS = "VENTAS", "Ventas"
        COMPRAS = "COMPRAS", "Compras"
        INVENTARIO = "INVENTARIO", "Inventario"
        CUENTA_CORRIENTE = "CUENTA_CORRIENTE", "Cuenta Corriente"
        ALMUERZOS = "ALMUERZOS", "Almuerzos"
        CAJA = "CAJA", "Caja"
        TRIBUTARIO = "TRIBUTARIO", "Tributario"

    class Frecuencia(models.TextChoices):
        DIARIO = "DIARIO", "Diario"
        SEMANAL = "SEMANAL", "Semanal"
        MENSUAL = "MENSUAL", "Mensual"
        ANUAL = "ANUAL", "Anual"
        PERSONALIZADO = "PERSONALIZADO", "Personalizado"

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    frecuencia = models.CharField(max_length=15, choices=Frecuencia.choices)
    query_sql = models.TextField(
        help_text="Consulta SQL base del reporte"
    )
    parametros = models.JSONField(
        default=dict,
        help_text="Parámetros configurables (fechas, filtros, etc.)",
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        "usuarios.Usuario",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="reportes_creados",
    )

    class Meta:
        verbose_name = "Plantilla de Reporte"
        verbose_name_plural = "Plantillas de Reportes"
        ordering = ["tipo", "nombre"]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.nombre}"