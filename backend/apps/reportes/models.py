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
    nombre_kpi = models.CharField(max_length=100, blank=True, default='')
    descripcion = models.TextField()
    formula = models.TextField(blank=True, default='')
    query_sql = models.TextField(blank=True, default='')
    unidad = models.CharField(max_length=20, blank=True, default='')
    unidad_medida = models.CharField(max_length=20, blank=True, default='')
    valor_objetivo = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    meta_valor = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    categoria = models.CharField(max_length=30)
    frecuencia = models.CharField(max_length=20, blank=True, default='')
    frecuencia_actualizacion = models.CharField(max_length=20, blank=True, default='')
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(null=True, blank=True)
    id_empleado = models.ForeignKey(
        "usuarios.Empleados", models.DO_NOTHING, db_column="kpi_id_empleado", blank=True, null=True
    )

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
    descripcion = models.TextField(blank=True, default='')
    tipo_tarea = models.CharField(max_length=30, blank=True, default='')
    comando = models.TextField(blank=True, default='')
    parametros = models.JSONField(default=dict)
    frecuencia = models.CharField(max_length=20, blank=True, default='')
    cron = models.CharField(max_length=100, blank=True, default='')
    timeout = models.IntegerField(default=0)
    max_reintentos = models.IntegerField(default=0)
    notif_exito = models.IntegerField(default=0)
    notif_error = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField()
    created_by = models.ForeignKey(
        "usuarios.Empleados", models.DO_NOTHING, db_column="created_by", blank=True, null=True
    )
    configuracion_programacion = models.JSONField(null=True, blank=True)
    configuracion_envio = models.JSONField(null=True, blank=True)

    def id_empleado_setter(self, value):
        self.created_by = value

    @property
    def id_empleado(self):
        return self.created_by

    @id_empleado.setter
    def id_empleado(self, value):
        self.created_by = value

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "plantillas_tarea"


class EjecucionesTareaManager(models.Manager):
    """Manager que acepta kwargs alternativos en create()"""

    def create(self, **kwargs):
        if 'id_plantilla_tarea' in kwargs:
            kwargs['id_plantilla'] = kwargs.pop('id_plantilla_tarea')
        if 'id_empleado' in kwargs:
            kwargs['ejecutado_por'] = kwargs.pop('id_empleado')
        return super().create(**kwargs)


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
    servidor = models.CharField(max_length=100, blank=True, default="")
    parametros = models.JSONField(default=dict)
    ejecutado_por = models.ForeignKey(
        "usuarios.Empleados", models.DO_NOTHING, db_column="ejecutado_por", blank=True, null=True
    )
    id_plantilla = models.ForeignKey("PlantillasTarea", models.DO_NOTHING, db_column="id_plantilla")

    objects = EjecucionesTareaManager()

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "ejecuciones_tarea"


class DestinatariosTareaManager(models.Manager):
    """Manager que acepta kwargs alternativos en create()"""

    def create(self, **kwargs):
        if 'id_plantilla_tarea' in kwargs:
            kwargs['id_plantilla'] = kwargs.pop('id_plantilla_tarea')
        if 'notificar_inicio' in kwargs:
            kwargs['notif_inicio'] = 1 if kwargs.pop('notificar_inicio') else 0
        if 'notificar_fin' in kwargs:
            kwargs['notif_fin'] = 1 if kwargs.pop('notificar_fin') else 0
        if 'notificar_exito' in kwargs:
            kwargs['notif_fin'] = 1 if kwargs.pop('notificar_exito') else 0
        if 'notificar_error' in kwargs:
            kwargs['notif_error'] = 1 if kwargs.pop('notificar_error') else 0
        return super().create(**kwargs)


class DestinatariosTarea(models.Model):
    id_destinatario = models.AutoField(primary_key=True)
    notif_inicio = models.IntegerField(default=0)
    notif_fin = models.IntegerField(default=0)
    notif_error = models.IntegerField(default=0)
    tipo_destinatario = models.CharField(max_length=30, blank=True, default="")
    id_empleado = models.ForeignKey(
        "usuarios.Empleados", models.DO_NOTHING, db_column="id_empleado"
    )
    id_plantilla = models.ForeignKey("PlantillasTarea", models.DO_NOTHING, db_column="id_plantilla")

    objects = DestinatariosTareaManager()

    # Propiedades alias para compatibilidad con tests
    @property
    def notificar_inicio(self):
        return bool(self.notif_inicio)

    @notificar_inicio.setter
    def notificar_inicio(self, value):
        self.notif_inicio = 1 if value else 0

    @property
    def notificar_fin(self):
        return bool(self.notif_fin)

    @notificar_fin.setter
    def notificar_fin(self, value):
        self.notif_fin = 1 if value else 0

    @property
    def notificar_exito(self):
        return bool(self.notif_fin)

    @notificar_exito.setter
    def notificar_exito(self, value):
        self.notif_fin = 1 if value else 0

    @property
    def notificar_error(self):
        return bool(self.notif_error)

    @notificar_error.setter
    def notificar_error(self, value):
        self.notif_error = 1 if value else 0

    @property
    def id_plantilla_tarea(self):
        return self.id_plantilla

    @id_plantilla_tarea.setter
    def id_plantilla_tarea(self, value):
        self.id_plantilla = value

    def __str__(self):
        return f"{self.__class__.__name__} #{self.pk}"

    class Meta:
        managed = True
        db_table = "destinatarios_tarea"
        unique_together = (("id_plantilla", "id_empleado"),)
