"""
Modelos de la app reportes
Auto-generados desde la base de datos y organizados por funcionalidad
"""

from django.db import models


class PlantillasReporte(models.Model):
    id_template = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    query_sql = models.TextField()
    parametros = models.JSONField()
    tipo_reporte = models.CharField(max_length=20)
    frecuencia = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField()
    created_by = models.ForeignKey(
        "usuarios.Empleados", models.DO_NOTHING, db_column="created_by", blank=True, null=True
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "plantillas_reporte"
        verbose_name = "Plantilla de Reporte"
        verbose_name_plural = "Plantillas de Reportes"


class Dashboards(models.Model):
    id_dashboard = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    configuracion = models.JSONField()
    es_publico = models.IntegerField()
    predeterminado = models.IntegerField()
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    id_empleado = models.ForeignKey(
        "usuarios.Empleados", models.DO_NOTHING, db_column="id_empleado"
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "dashboards"


class KpiMetricas(models.Model):
    id_kpi = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    formula = models.TextField()
    unidad = models.CharField(max_length=20)
    valor_objetivo = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    categoria = models.CharField(max_length=30)
    frecuencia = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "kpi_metricas"


class ValoresKpi(models.Model):
    id_valor = models.AutoField(primary_key=True)
    fecha = models.DateField()
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    notas = models.TextField(blank=True, null=True)
    auto_calc = models.IntegerField()
    created_at = models.DateTimeField()
    id_kpi = models.ForeignKey("KpiMetricas", models.DO_NOTHING, db_column="id_kpi")

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "valores_kpi"
        unique_together = (("id_kpi", "fecha"),)


class PlantillasTarea(models.Model):
    id_plantilla = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    tipo_tarea = models.CharField(max_length=30)
    comando = models.TextField()
    parametros = models.JSONField()
    frecuencia = models.CharField(max_length=20)
    cron = models.CharField(max_length=100)
    timeout = models.IntegerField()
    max_reintentos = models.IntegerField()
    notif_exito = models.IntegerField()
    notif_error = models.IntegerField()
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField()
    created_by = models.ForeignKey(
        "usuarios.Empleados", models.DO_NOTHING, db_column="created_by", blank=True, null=True
    )

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "plantillas_tarea"


class EjecucionesTarea(models.Model):
    id_ejecucion = models.AutoField(primary_key=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(blank=True, null=True)
    duracion_seg = models.IntegerField(blank=True, null=True)
    estado = models.CharField(max_length=20)
    resultado = models.TextField(blank=True, null=True)
    error_msg = models.TextField(blank=True, null=True)
    logs = models.TextField(blank=True, null=True)
    pid = models.IntegerField(blank=True, null=True)
    servidor = models.CharField(max_length=100)
    parametros = models.JSONField()
    ejecutado_por = models.ForeignKey(
        "usuarios.Empleados", models.DO_NOTHING, db_column="ejecutado_por", blank=True, null=True
    )
    id_plantilla = models.ForeignKey("PlantillasTarea", models.DO_NOTHING, db_column="id_plantilla")

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "ejecuciones_tarea"


class DestinatariosTarea(models.Model):
    id_destinatario = models.AutoField(primary_key=True)
    notif_inicio = models.IntegerField()
    notif_fin = models.IntegerField()
    notif_error = models.IntegerField()
    id_empleado = models.ForeignKey(
        "usuarios.Empleados", models.DO_NOTHING, db_column="id_empleado"
    )
    id_plantilla = models.ForeignKey("PlantillasTarea", models.DO_NOTHING, db_column="id_plantilla")

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "destinatarios_tarea"
        unique_together = (("id_plantilla", "id_empleado"),)
