"""
Modelos de la app clientes
Gestión de clientes, hijos, grados y restricciones
"""

from django.db import models
from django.core.validators import EmailValidator
from decimal import Decimal


class ClientesManager(models.Manager):
    def create(self, **kwargs):
        if "id_lista" not in kwargs and "id_lista_id" not in kwargs:
            from apps.productos.models import ListasPrecios

            lista, _ = ListasPrecios.objects.get_or_create(
                nombre_lista="General",
                defaults={"estado": True},
            )
            kwargs["id_lista"] = lista
        if "id_tipo_cliente" not in kwargs and "id_tipo_cliente_id" not in kwargs:
            tipo, _ = TiposCliente.objects.get_or_create(
                nombre_tipo="Regular",
                defaults={"estado": True},
            )
            kwargs["id_tipo_cliente"] = tipo
        return super().create(**kwargs)


class Clientes(models.Model):
    """
    Modelo de clientes (padres/tutores) que compran en la cantina.
    Incluye información de contacto, límites de crédito y relación con listas de precios.
    """

    id_cliente = models.AutoField(primary_key=True)
    nombres = models.CharField(max_length=100, help_text="Nombres del cliente")
    apellidos = models.CharField(max_length=100, help_text="Apellidos del cliente")
    razon_social = models.CharField(max_length=255, blank=True, null=True, help_text="Razón social si es empresa")
    ruc_ci = models.CharField(unique=True, max_length=20, help_text="RUC o Cédula de Identidad")
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    id_ciudad = models.ForeignKey(
        "Ciudad",
        models.SET_NULL,
        db_column="id_ciudad",
        blank=True,
        null=True,
        help_text="Ciudad del catálogo (opcional)",
    )
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=254, blank=True, null=True, validators=[EmailValidator()])
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, default=0)
    estado = models.BooleanField(default=True, help_text="1=estado, 0=Inactivo")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    id_lista = models.ForeignKey("productos.ListasPrecios", models.DO_NOTHING, db_column="id_lista")
    id_tipo_cliente = models.ForeignKey("TiposCliente", models.DO_NOTHING, db_column="id_tipo_cliente")

    objects = ClientesManager()

    class Meta:
        managed = True
        db_table = "clientes"
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["apellidos", "nombres"]
        indexes = [
            models.Index(fields=["email"], name="idx_clientes_email"),
            models.Index(fields=["estado", "fecha_registro"], name="idx_clientes_estado_fecha"),
            models.Index(fields=["apellidos", "nombres"], name="idx_clientes_nombre"),
            models.Index(fields=["ciudad"], name="idx_clientes_ciudad"),
        ]

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del cliente"""
        return f"{self.nombres} {self.apellidos}"

    @property
    def credito_utilizado(self):
        """
        Calcula el crédito utilizado (suma de saldos pendientes de todas las ventas).

        Returns:
            Decimal: Monto total de ventas pendientes de pago
        """
        from apps.ventas.models import Ventas
        from django.db.models import Sum

        total = Ventas.objects.filter(id_cliente=self.id_cliente, saldo_pendiente__gt=0).aggregate(
            total=Sum("saldo_pendiente")
        )["total"]

        return total or Decimal("0.00")

    @property
    def credito_disponible(self):
        """
        Calcula el crédito disponible del cliente.

        Formula: credito_disponible = limite_credito - credito_utilizado

        Returns:
            Decimal: Crédito disponible para nuevas ventas
        """
        if self.limite_credito:
            return self.limite_credito - self.credito_utilizado
        return Decimal("0.00")

    @property
    def tiene_credito_disponible(self):
        """
        Verifica si el cliente tiene crédito disponible.

        Returns:
            bool: True si tiene crédito > 0
        """
        return self.credito_disponible > 0

    @property
    def porcentaje_credito_usado(self):
        """
        Calcula el porcentaje de crédito utilizado.

        Returns:
            Decimal: Porcentaje de uso (0-100)
        """
        if self.limite_credito and self.limite_credito > 0:
            return (self.credito_utilizado / self.limite_credito) * 100
        return Decimal("0.00")

    @property
    def cuenta_corriente(self):
        """
        Obtiene el estado de cuenta corriente del cliente.

        Returns:
            dict: Resumen de cuenta corriente con saldos y límites
        """
        from apps.ventas.models import Ventas, NotasCreditoCliente
        from django.db.models import Sum

        # Total de ventas pendientes
        ventas_pendientes = Ventas.objects.filter(id_cliente=self.id_cliente, saldo_pendiente__gt=0)

        total_debe = ventas_pendientes.aggregate(total=Sum("saldo_pendiente"))["total"] or Decimal("0.00")

        # Notas de crédito emitidas sin aplicar
        notas_credito = NotasCreditoCliente.objects.filter(id_cliente=self.id_cliente, estado="Emitida")

        total_haber = notas_credito.aggregate(total=Sum("monto_total"))["total"] or Decimal("0.00")

        saldo_neto = total_debe - total_haber

        return {
            "total_debe": total_debe,
            "total_haber": total_haber,
            "saldo_neto": saldo_neto,
            "limite_credito": self.limite_credito or Decimal("0.00"),
            "credito_disponible": self.credito_disponible,
            "porcentaje_usado": self.porcentaje_credito_usado,
            "cantidad_facturas_pendientes": ventas_pendientes.count(),
            "cantidad_notas_credito": notas_credito.count(),
        }

    @property
    def esta_activo(self):
        """Retorna True si el cliente está estado"""
        return self.estado == 1


class TiposCliente(models.Model):
    """
    Tipos de clientes (Ej: Mayorista, Minorista, Estudiante, Profesor)
    """

    id_tipo_cliente = models.AutoField(primary_key=True)
    nombre_tipo = models.CharField(unique=True, max_length=50)
    estado = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = "tipos_cliente"
        verbose_name = "Tipo de Cliente"
        verbose_name_plural = "Tipos de Cliente"
        verbose_name = "Tipo de Cliente"
        verbose_name_plural = "Tipos de Cliente"
        verbose_name = "Tipo de Cliente"
        verbose_name_plural = "Tipos de Cliente"
        ordering = ["nombre_tipo"]

    def __str__(self):
        return self.nombre_tipo


class Hijos(models.Model):
    """
    Hijos/estudiantes asociados a un cliente (padre/tutor).
    Cada hijo puede tener su propia tarjeta de consumo.
    """

    id_hijo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, help_text="Nombre del estudiante")
    apellido = models.CharField(max_length=100, help_text="Apellido del estudiante")
    fecha_nacimiento = models.DateField(blank=True, null=True)
    grado = models.CharField(max_length=50, blank=True, null=True)
    foto_perfil = models.ImageField(
        upload_to="fotos_estudiantes/", blank=True, null=True, help_text="Foto de perfil del estudiante"
    )
    fecha_foto = models.DateTimeField(blank=True, null=True)
    estado = models.BooleanField(default=True, help_text="1=estado, 0=Inactivo")
    id_cliente_responsable = models.ForeignKey(
        "Clientes", models.DO_NOTHING, db_column="id_cliente_responsable", related_name="hijos"
    )

    class Meta:
        managed = True
        db_table = "hijos"
        verbose_name = "Hijo/Estudiante"
        verbose_name_plural = "Hijos/Estudiantes"
        verbose_name = "Hijo/Estudiante"
        verbose_name_plural = "Hijos/Estudiantes"
        verbose_name = "Hijo/Estudiante"
        verbose_name_plural = "Hijos/Estudiantes"
        ordering = ["apellido", "nombre"]

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.grado or 'Sin grado'})"

    @property
    def nombre_completo(self):
        """Retorna el nombre completo del hijo"""
        return f"{self.nombre} {self.apellido}"

    @property
    def edad(self):
        """Calcula la edad del hijo si tiene fecha de nacimiento"""
        if self.fecha_nacimiento:
            from datetime import date

            today = date.today()
            return (
                today.year
                - self.fecha_nacimiento.year
                - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
            )
        return None


class Grados(models.Model):
    """
    Grados escolares disponibles en la institución.
    """

    id_grado = models.AutoField(primary_key=True)
    nombre_grado = models.CharField(unique=True, max_length=50)
    nivel = models.IntegerField(help_text="Nivel numérico del grado (1-12)")
    orden_visualizacion = models.IntegerField()
    es_ultimo_grado = models.BooleanField(default=False, help_text="1 si es el último grado")
    estado = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = "grados"
        verbose_name = "Grado"
        verbose_name_plural = "Grados"
        verbose_name = "Grado"
        verbose_name_plural = "Grados"
        verbose_name = "Grado"
        verbose_name_plural = "Grados"
        ordering = ["orden_visualizacion"]

    def __str__(self):
        return self.nombre_grado


class HistorialGradosHijos(models.Model):
    """
    Historial de cambios de grado de los estudiantes.
    Permite rastrear avances y cambios de nivel.
    """

    id_historial = models.AutoField(primary_key=True)
    grado_anterior = models.CharField(max_length=50, blank=True, null=True)
    grado_nuevo = models.CharField(max_length=50)
    anio_escolar = models.IntegerField()
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=20)
    usuario_registro = models.CharField(max_length=100, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    id_hijo = models.ForeignKey("Hijos", models.DO_NOTHING, db_column="id_hijo", related_name="historial_grados")

    class Meta:
        managed = True
        db_table = "historial_grados_hijos"
        verbose_name = "Historial de Grado"
        verbose_name_plural = "Historial de Grados"
        verbose_name = "Historial de Grado"
        verbose_name_plural = "Historial de Grados"
        verbose_name = "Historial de Grado"
        verbose_name_plural = "Historial de Grados"
        ordering = ["-fecha_cambio"]

    def __str__(self):
        return f"{self.id_hijo} - {self.grado_anterior or 'N/A'} → {self.grado_nuevo} ({self.anio_escolar})"


class RestriccionesHijos(models.Model):
    """
    Restricciones alimenticias, médicas o de otro tipo para estudiantes.
    """

    id_restriccion = models.AutoField(primary_key=True)
    tipo_restriccion = models.CharField(max_length=100, help_text="Ej: Alergia, Intolerancia, Médica")
    descripcion = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    severidad = models.CharField(max_length=20, help_text="Ej: Baja, Media, Alta, Crítica")
    requiere_autorizacion = models.BooleanField(default=False, help_text="1 si requiere autorización para excepciones")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_ultima_actualizacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)
    id_hijo = models.ForeignKey("Hijos", models.DO_NOTHING, db_column="id_hijo", related_name="restricciones")

    class Meta:
        managed = True
        db_table = "restricciones_hijos"
        verbose_name = "Restricción de Hijo"
        verbose_name_plural = "Restricciones de Hijos"
        verbose_name = "Restricción de Hijo"
        verbose_name_plural = "Restricciones de Hijos"
        verbose_name = "Restricción de Hijo"
        verbose_name_plural = "Restricciones de Hijos"
        ordering = ["-severidad", "-estado"]

    def __str__(self):
        return f"{self.tipo_restriccion} - {self.id_hijo} ({self.severidad})"

    @property
    def es_critica(self):
        """Retorna True si la restricción es crítica"""
        return self.severidad.lower() == "crítica" or self.severidad.lower() == "critica"


class AutorizacionesSaldoNegativo(models.Model):
    """
    Autorizaciones especiales para permitir ventas con saldo negativo.
    """

    id_autorizacion = models.BigAutoField(primary_key=True)
    monto_autorizado = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Monto máximo autorizado en negativo"
    )
    saldo_anterior = models.DecimalField(max_digits=12, decimal_places=2)
    saldo_resultante = models.DecimalField(max_digits=12, decimal_places=2)
    motivo = models.TextField(help_text="Justificación de la autorización")
    fecha_autorizacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=10, help_text="Ej: Aprobada, Usada, Cancelada")
    id_venta = models.ForeignKey(
        "ventas.Ventas",
        models.DO_NOTHING,
        db_column="id_venta",
        related_name="autorizaciones_saldo",
    )
    id_cliente = models.ForeignKey(
        "Clientes", models.DO_NOTHING, db_column="id_cliente", related_name="autorizaciones_saldo"
    )
    id_empleado_autoriza = models.ForeignKey(
        "usuarios.Empleados",
        models.DO_NOTHING,
        db_column="id_empleado_autoriza",
        related_name="autorizaciones_realizadas",
    )

    class Meta:
        managed = True
        db_table = "autorizaciones_saldo_negativo"
        verbose_name = "Autorización de Saldo Negativo"
        verbose_name_plural = "Autorizaciones de Saldo Negativo"
        verbose_name = "Autorización de Saldo Negativo"
        verbose_name_plural = "Autorizaciones de Saldo Negativo"
        verbose_name = "Autorización de Saldo Negativo"
        verbose_name_plural = "Autorizaciones de Saldo Negativo"
        ordering = ["-fecha_autorizacion"]

    def __str__(self):
        return f"Autorización {self.id_autorizacion} - {self.id_cliente} (${self.monto_autorizado})"


class LogsAutorizaciones(models.Model):
    """
    Registro de auditoría de autorizaciones realizadas con tarjetas.
    """

    id_log = models.BigAutoField(primary_key=True)
    codigo_barra = models.CharField(max_length=50)
    tipo_operacion = models.CharField(max_length=20, help_text="Ej: Lectura, Autorización, Validación")
    id_registro_afectado = models.BigIntegerField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    id_usuario = models.IntegerField(blank=True, null=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    ip_origen = models.CharField(max_length=45, blank=True, null=True)
    resultado = models.CharField(max_length=15, help_text="Ej: Exitoso, Fallido, Denegado")
    id_tarjeta_autorizacion = models.ForeignKey(
        "core.TarjetasAutorizacion",
        models.DO_NOTHING,
        db_column="id_tarjeta_autorizacion",
        related_name="logs",
    )

    class Meta:
        managed = True
        db_table = "logs_autorizaciones"
        verbose_name = "Log de Autorización"
        verbose_name_plural = "Logs de Autorizaciones"
        verbose_name = "Log de Autorización"
        verbose_name_plural = "Logs de Autorizaciones"
        verbose_name = "Log de Autorización"
        verbose_name_plural = "Logs de Autorizaciones"
        ordering = ["-fecha_hora"]

    def __str__(self):
        return f"Log {self.id_log} - {self.tipo_operacion} ({self.resultado})"


class Pais(models.Model):
    id_pais = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        managed = True
        db_table = "pais"
        verbose_name = "País"
        verbose_name_plural = "Países"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Ciudad(models.Model):
    id_ciudad = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)

    class Meta:
        managed = True
        db_table = "ciudad"
        verbose_name = "Ciudad"
        verbose_name_plural = "Ciudades"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
