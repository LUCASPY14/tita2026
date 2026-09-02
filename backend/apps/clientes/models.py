"""
Modelos de la app clientes
Gestión de clientes, hijos, cuentas corrientes y restricciones
"""

from decimal import Decimal

from django.core.validators import EmailValidator
from django.db import models, transaction
from django.utils import timezone
from simple_history.models import HistoricalRecords


# ==============================================================================
# CLIENTE
# ==============================================================================

class Cliente(models.Model):
    """
    Cliente (padre/tutor) que compra en la cantina.
    """

    nombres = models.CharField(max_length=100, help_text="Nombres del cliente")
    apellidos = models.CharField(max_length=100, help_text="Apellidos del cliente")
    razon_social = models.CharField(
        max_length=255, blank=True, null=True, help_text="Razón social si es empresa"
    )
    ruc_ci = models.CharField(
        unique=True, max_length=20, help_text="RUC o Cédula de Identidad"
    )
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    ciudad_catalogo = models.ForeignKey(
        "Ciudad",
        models.SET_NULL,
        blank=True,
        null=True,
        related_name="clientes",
    )
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(
        max_length=254, blank=True, null=True, validators=[EmailValidator()]
    )
    limite_credito = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        help_text="Límite de crédito en Guaraníes. 0 = sin límite (solo aplica si permite_cuenta_corriente está activo).",
    )
    permite_cuenta_corriente = models.BooleanField(
        default=False,
        help_text="Si está desactivado, el cliente no puede acumular deuda "
                   "(ventas al fiado ni recargas por cuenta corriente), sin importar limite_credito.",
    )
    activo = models.BooleanField(default=True, help_text="False si el cliente está inactivo")
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class ModalidadFacturacion(models.TextChoices):
        INMEDIATA = "INMEDIATA", "Factura por transacción"
        MENSUAL   = "MENSUAL",   "Factura mensual agrupada"

    modalidad_facturacion = models.CharField(
        max_length=10,
        choices=ModalidadFacturacion.choices,
        default=ModalidadFacturacion.INMEDIATA,
        help_text="Cuándo se emite la factura: al momento o acumulada mensual",
    )
    lista_precio = models.ForeignKey(
        "productos.ListaPrecio",
        models.PROTECT,
        related_name="clientes",
    )
    tipo_cliente = models.ForeignKey(
        "TipoCliente",
        models.PROTECT,
        related_name="clientes",
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["apellidos", "nombres"]
        indexes = [
            models.Index(fields=["ruc_ci"], name="idx_cliente_ruc"),
            models.Index(fields=["email"], name="idx_cliente_email"),
            models.Index(fields=["activo"], name="idx_cliente_activo"),
            models.Index(fields=["apellidos", "nombres"], name="idx_cliente_nombre"),
        ]

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def saldo_cuenta_corriente(self):
        """Saldo actual de la cuenta corriente. Positivo = deuda."""
        ultimo = self.movimientos_cuenta.order_by("-id").first()
        return ultimo.saldo_resultante if ultimo else Decimal("0")

    def _saldo_cc_por_origen(self, origen):
        """Deuda de una categoría (CANTINA/ALMUERZO): suma directa, no una
        segunda cadena de saldo_resultante — el saldo_resultante corrido
        sigue siendo solo el total combinado (limite_credito no cambia)."""
        from django.db.models import Sum, Q
        agg = self.movimientos_cuenta.filter(origen=origen).aggregate(
            debitos=Sum("monto", filter=Q(tipo=CuentaCorrienteCliente.Tipo.DEBITO)),
            creditos=Sum("monto", filter=~Q(tipo=CuentaCorrienteCliente.Tipo.DEBITO)),
        )
        return (agg["debitos"] or Decimal("0")) - (agg["creditos"] or Decimal("0"))

    @property
    def saldo_cc_cantina(self):
        return self._saldo_cc_por_origen(CuentaCorrienteCliente.Origen.CANTINA)

    @property
    def saldo_cc_almuerzo(self):
        return self._saldo_cc_por_origen(CuentaCorrienteCliente.Origen.ALMUERZO)


# ==============================================================================
# CUENTA CORRIENTE DE CLIENTES
# ==============================================================================

class CuentaCorrienteCliente(models.Model):
    """
    Movimientos de cuenta corriente de clientes.
    Débito = venta al fiado (aumenta la deuda).
    Crédito = pago o nota de crédito (reduce la deuda).
    """

    class Tipo(models.TextChoices):
        DEBITO = "DEBITO", "Débito"
        CREDITO = "CREDITO", "Crédito"
        AJUSTE = "AJUSTE", "Ajuste"

    class Origen(models.TextChoices):
        CANTINA = "CANTINA", "Cantina"
        ALMUERZO = "ALMUERZO", "Almuerzo"
        GENERAL = "GENERAL", "General"

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="movimientos_cuenta",
        help_text="Cliente titular de la cuenta",
    )
    fecha = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    monto = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Monto en Guaraníes"
    )
    saldo_anterior = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Saldo antes del movimiento"
    )
    saldo_resultante = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Saldo después del movimiento"
    )
    descripcion = models.CharField(
        max_length=255, blank=True, null=True, help_text="Detalle del movimiento"
    )
    origen = models.CharField(
        max_length=10, choices=Origen.choices, default=Origen.GENERAL,
        help_text="Categoría de deuda que generó el movimiento — no afecta saldo_resultante ni limite_credito, solo reporte.",
    )

    # Referencias a documentos origen
    venta = models.ForeignKey(
        "ventas.Venta",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_cuenta",
    )
    pago = models.ForeignKey(
        "ventas.PagoVenta",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_cuenta",
        help_text="Pago que generó este movimiento",
    )
    nota_credito = models.ForeignKey(
        "ventas.NotaCredito",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_cuenta",
    )

    # Facturación — solo aplica a movimientos tipo CREDITO (cobros)
    factura = models.ForeignKey(
        "contabilidad.Factura",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_cuenta",
    )
    genera_factura_legal = models.BooleanField(default=False)

    # Auditoría
    creado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="movimientos_cuenta_creados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de Cuenta Corriente"
        verbose_name_plural = "Cuentas Corrientes de Clientes"
        ordering = ["-fecha", "-id"]
        indexes = [
            models.Index(fields=["cliente", "fecha"], name="idx_cc_cli_fecha"),
            models.Index(fields=["cliente", "tipo"], name="idx_cc_cli_tipo"),
            models.Index(fields=["venta"], name="idx_cc_cli_venta"),
            models.Index(fields=["cliente", "origen"], name="idx_cc_cli_origen"),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cliente} - ₲{self.monto:,.0f}"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.saldo_anterior is None:
                # Lock the client row so concurrent movements can't read the same saldo_anterior.
                Cliente.objects.select_for_update().get(pk=self.cliente_id)
                ultimo = (
                    CuentaCorrienteCliente.objects
                    .filter(cliente_id=self.cliente_id)
                    .order_by("-id")
                    .first()
                )
                self.saldo_anterior = ultimo.saldo_resultante if ultimo else Decimal("0")

            if self.tipo == self.Tipo.DEBITO:
                self.saldo_resultante = self.saldo_anterior + self.monto
            elif self.tipo in (self.Tipo.CREDITO, self.Tipo.AJUSTE):
                self.saldo_resultante = self.saldo_anterior - self.monto

            super().save(*args, **kwargs)


# ==============================================================================
# TIPO DE CLIENTE
# ==============================================================================

class TipoCliente(models.Model):
    """Tipos de clientes (Regular, Mayorista, Estudiante, Profesor, etc.)."""

    nombre = models.CharField(unique=True, max_length=50)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tipo de Cliente"
        verbose_name_plural = "Tipos de Cliente"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


# ==============================================================================
# HIJOS / ESTUDIANTES
# ==============================================================================

class Hijo(models.Model):
    """Hijo/estudiante asociado a un cliente (padre/tutor)."""

    nombre = models.CharField(max_length=100, help_text="Nombre del estudiante")
    apellido = models.CharField(max_length=100, help_text="Apellido del estudiante")
    fecha_nacimiento = models.DateField(blank=True, null=True)
    grado = models.ForeignKey(
        "Grado",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="hijos",
    )
    foto_perfil = models.ImageField(
        upload_to="hijos/fotos/%Y/%m/",
        blank=True,
        null=True,
        help_text="Foto de perfil del estudiante",
    )
    fecha_foto = models.DateTimeField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_baja = models.DateTimeField(
        blank=True, null=True,
        help_text="Fecha en que el alumno fue dado de baja (manual o automática al terminar el último curso)",
    )
    purga_solicitada_en = models.DateTimeField(
        blank=True, null=True,
        help_text="Fecha en que se marcó como pendiente de purga de datos sensibles (esperando aprobación de un ADMIN)",
    )
    datos_purgados = models.BooleanField(
        default=False,
        help_text="True si ya se ejecutó la anonimización de datos sensibles (restricciones, foto, nombre)",
    )
    cliente_responsable = models.ForeignKey(
        Cliente,
        models.PROTECT,
        related_name="hijos",
    )

    class Meta:
        verbose_name = "Hijo/Estudiante"
        verbose_name_plural = "Hijos/Estudiantes"
        ordering = ["apellido", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["cliente_responsable", "nombre", "apellido"],
                name="uq_hijo_cliente_nombre_apellido",
            )
        ]

    def __str__(self):
        return f"{self.apellido}, {self.nombre} ({self.grado.nombre if self.grado else 'Sin grado'})"

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    @property
    def grado_nombre(self):
        return self.grado.nombre if self.grado else None

    @property
    def edad(self):
        if self.fecha_nacimiento:
            from datetime import date
            today = date.today()
            return (
                today.year
                - self.fecha_nacimiento.year
                - (
                    (today.month, today.day)
                    < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
                )
            )
        return None


# ==============================================================================
# GRADOS
# ==============================================================================

class Grado(models.Model):
    """Grados escolares de la institución."""

    nombre = models.CharField(unique=True, max_length=50)
    nivel = models.IntegerField(help_text="Nivel numérico (1-12)")
    orden = models.IntegerField(help_text="Orden de visualización")
    es_ultimo = models.BooleanField(default=False, help_text="True si es el último grado")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Grado"
        verbose_name_plural = "Grados"
        ordering = ["orden"]

    def __str__(self):
        return self.nombre


class HistorialGrado(models.Model):
    """Historial de cambios de grado de estudiantes."""

    hijo = models.ForeignKey(
        Hijo, models.PROTECT, related_name="historial_grados"
    )
    grado_anterior = models.CharField(max_length=50, blank=True, null=True)
    grado_nuevo = models.CharField(max_length=50)
    anio_escolar = models.IntegerField()
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(max_length=20)
    usuario_registro = models.CharField(max_length=100, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Historial de Grado"
        verbose_name_plural = "Historial de Grados"
        ordering = ["-fecha_cambio"]

    def __str__(self):
        return f"{self.hijo} - {self.grado_anterior or 'N/A'} → {self.grado_nuevo}"


# ==============================================================================
# RESTRICCIONES
# ==============================================================================

class RestriccionHijo(models.Model):
    """Restricciones alimenticias o médicas de estudiantes."""

    class Severidad(models.TextChoices):
        BAJA = "BAJA", "Baja"
        MEDIA = "MEDIA", "Media"
        ALTA = "ALTA", "Alta"
        CRITICA = "CRITICA", "Crítica"

    hijo = models.ForeignKey(
        Hijo, models.PROTECT, related_name="restricciones"
    )
    tipo = models.CharField(max_length=100, help_text="Ej: Alergia, Intolerancia, Médica")
    descripcion = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    severidad = models.CharField(
        max_length=10, choices=Severidad.choices, default=Severidad.MEDIA
    )
    requiere_autorizacion = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Restricción de Hijo"
        verbose_name_plural = "Restricciones de Hijos"
        ordering = ["-severidad"]

    def __str__(self):
        return f"{self.tipo} - {self.hijo} ({self.get_severidad_display()})"

    @property
    def es_critica(self):
        return self.severidad == self.Severidad.CRITICA


# ==============================================================================
# AUTORIZACIONES DE SALDO NEGATIVO
# ==============================================================================

class AutorizacionSaldoNegativo(models.Model):
    """Autorizaciones para permitir ventas con saldo negativo."""

    class Estado(models.TextChoices):
        APROBADA = "APROBADA", "Aprobada"
        USADA = "USADA", "Usada"
        CANCELADA = "CANCELADA", "Cancelada"

    cliente = models.ForeignKey(
        Cliente, models.PROTECT, related_name="autorizaciones_saldo"
    )
    venta = models.ForeignKey(
        "ventas.Venta", models.PROTECT, related_name="autorizaciones_saldo"
    )
    empleado_autoriza = models.ForeignKey(
        "usuarios.Empleado", models.PROTECT, related_name="autorizaciones_realizadas"
    )
    monto_autorizado = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Monto en Guaraníes"
    )
    saldo_anterior = models.DecimalField(max_digits=12, decimal_places=0)
    saldo_resultante = models.DecimalField(max_digits=12, decimal_places=0)
    motivo = models.TextField(help_text="Justificación")
    fecha_autorizacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=10, choices=Estado.choices, default=Estado.APROBADA
    )

    class Meta:
        verbose_name = "Autorización de Saldo Negativo"
        verbose_name_plural = "Autorizaciones de Saldo Negativo"
        ordering = ["-fecha_autorizacion"]

    def __str__(self):
        return f"Autorización #{self.pk} - {self.cliente} (₲{self.monto_autorizado:,.0f})"


# ==============================================================================
# PAÍS Y CIUDAD
# ==============================================================================

class Pais(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "País"
        verbose_name_plural = "Países"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Ciudad(models.Model):
    nombre = models.CharField(max_length=100)
    pais = models.ForeignKey(
        Pais,
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="ciudades",
    )

    class Meta:
        verbose_name = "Ciudad"
        verbose_name_plural = "Ciudades"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


# ==============================================================================
# ALUMNO ↔ RESPONSABLE (N:M)
# ==============================================================================

class AlumnoResponsable(models.Model):
    """
    Relación entre un alumno y sus responsables financieros (padre, madre, tutor, etc.).
    Permite múltiples contactos de cobro con orden de escalamiento.

    Reglas de negocio:
    - Cada alumno debe tener exactamente un titular activo (es_titular=True, activo=True).
    - El titular es quien figura en ventas, facturas y recargas (sincronizado con
      Hijo.cliente_responsable para no romper el modelo financiero existente).
    - orden_cobro define el orden de contacto ante deudas (1 = primero).
    """

    class Parentesco(models.TextChoices):
        PADRE  = "PADRE",  "Padre"
        MADRE  = "MADRE",  "Madre"
        ABUELO = "ABUELO", "Abuelo"
        ABUELA = "ABUELA", "Abuela"
        TIO    = "TIO",    "Tío"
        TIA    = "TIA",    "Tía"
        TUTOR  = "TUTOR",  "Tutor/a Legal"
        OTRO   = "OTRO",   "Otro"

    hijo = models.ForeignKey(
        Hijo,
        models.CASCADE,
        related_name="responsables",
    )
    cliente = models.ForeignKey(
        Cliente,
        models.RESTRICT,
        related_name="hijos_asignados",
        help_text="Responsable financiero",
    )
    parentesco = models.CharField(max_length=20, choices=Parentesco.choices)
    es_titular = models.BooleanField(
        default=False,
        help_text="Responsable financiero principal. Sincronizado con Hijo.cliente_responsable.",
    )
    orden_cobro = models.PositiveSmallIntegerField(
        default=1,
        help_text="Orden de contacto para escalamiento de cobro (1 = primero).",
    )
    recibe_notificaciones = models.BooleanField(
        default=False,
        help_text="Recibe alertas de deuda y saldo bajo.",
    )
    puede_ver_saldo = models.BooleanField(
        default=False,
        help_text="Puede consultar el saldo y consumos del alumno en el portal.",
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    agregado_por = models.ForeignKey(
        "usuarios.Usuario",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="responsables_registrados",
    )

    class Meta:
        verbose_name = "Responsable de Alumno"
        verbose_name_plural = "Responsables de Alumnos"
        ordering = ["hijo", "orden_cobro"]
        constraints = [
            # Un cliente no puede ser responsable del mismo alumno dos veces
            models.UniqueConstraint(
                fields=["hijo", "cliente"],
                name="uq_alumno_responsable",
            ),
            # Cada alumno tiene a lo sumo un titular activo — garantizado por la BD
            models.UniqueConstraint(
                fields=["hijo"],
                condition=models.Q(es_titular=True, activo=True),
                name="uq_alumno_titular_activo",
            ),
        ]
        indexes = [
            models.Index(
                fields=["hijo", "activo", "orden_cobro"],
                name="idx_ar_hijo_cobro",
            ),
            models.Index(
                fields=["cliente", "activo"],
                name="idx_ar_cliente_activo",
            ),
        ]

    def __str__(self):
        titular = " [TITULAR]" if self.es_titular else ""
        return f"{self.hijo} ← {self.cliente} ({self.get_parentesco_display()}){titular}"
