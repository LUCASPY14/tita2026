"""
Modelos de la app almuerzos
Gestión de almuerzos escolares: precios, planes, suscripciones y consumo
"""

from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils import timezone


def hora_actual():
    """Retorna la hora actual para usar como default en TimeField."""
    return timezone.localtime().time()


# ==============================================================================
# PRECIO DE ALMUERZO (HISTÓRICO)
# ==============================================================================

class PrecioAlmuerzo(models.Model):
    """Historial de precios unitarios del almuerzo con vigencia."""

    precio_unitario = models.DecimalField(
        max_digits=12, decimal_places=0,
        help_text="Precio por almuerzo en Guaraníes",
    )
    fecha_inicio_vigencia = models.DateField()
    fecha_fin_vigencia = models.DateField(
        blank=True, null=True,
        help_text="Vacío = sin vencimiento",
    )
    descripcion = models.CharField(
        max_length=200, blank=True,
        help_text="Ej: Ajuste por inflación 2026",
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Precio de Almuerzo"
        verbose_name_plural = "Precios de Almuerzo"
        ordering = ["-fecha_inicio_vigencia"]

    def clean(self):
        qs = PrecioAlmuerzo.objects.exclude(pk=self.pk or 0)
        # Solo un precio puede tener fecha_fin_vigencia NULL (el vigente actual)
        if self.fecha_fin_vigencia is None:
            if qs.filter(fecha_fin_vigencia__isnull=True).exists():
                raise ValidationError(
                    "Ya existe un precio sin fecha de fin. Cerrá el precio anterior antes de crear uno nuevo."
                )
        # Verificar solapamiento de rangos con el resto
        if self.fecha_inicio_vigencia:
            fin_self = self.fecha_fin_vigencia or date.max
            for p in qs:
                fin_p = p.fecha_fin_vigencia or date.max
                if max(self.fecha_inicio_vigencia, p.fecha_inicio_vigencia) <= min(fin_self, fin_p):
                    raise ValidationError(
                        f"El período se solapa con '₲{p.precio_unitario:,.0f}' "
                        f"({p.fecha_inicio_vigencia} – {p.fecha_fin_vigencia or 'indefinido'})."
                    )

    def __str__(self):
        return f"₲{self.precio_unitario:,.0f} (desde {self.fecha_inicio_vigencia})"


# ==============================================================================
# TIPO DE ALMUERZO
# ==============================================================================

class TipoAlmuerzo(models.Model):
    """Tipo de almuerzo (plato principal, postre, bebida, etc.)."""

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    precio_unitario = models.DecimalField(
        max_digits=12, decimal_places=0,
        help_text="Precio en Guaraníes",
    )
    incluye_plato_principal = models.BooleanField(default=True)
    incluye_postre = models.BooleanField(default=False)
    incluye_bebida = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tipo de Almuerzo"
        verbose_name_plural = "Tipos de Almuerzo"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} - ₲{self.precio_unitario:,.0f}"


# ==============================================================================
# PLAN DE ALMUERZO
# ==============================================================================

class PlanAlmuerzo(models.Model):
    """Plan de almuerzo mensual o por cantidad."""

    class TipoPlan(models.TextChoices):
        CANTIDAD = "CANTIDAD", "Mensual con cantidad fija"
        SIN_LIMITE = "SIN_LIMITE", "Mensual sin límite (cuenta corriente)"

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(
        max_length=15, choices=TipoPlan.choices, default=TipoPlan.SIN_LIMITE,
    )
    precio_mensual = models.DecimalField(
        max_digits=12, decimal_places=0,
        help_text="Precio mensual fijo de referencia en Guaraníes",
    )
    cantidad_almuerzos_mes = models.IntegerField(
        blank=True, null=True,
        help_text="Solo para tipo=CANTIDAD: máximo de almuerzos por mes",
    )
    limite_credito_mensual = models.DecimalField(
        max_digits=12, decimal_places=0,
        blank=True, null=True,
        help_text="Monto máximo acumulable por mes. Vacío = sin límite",
    )
    dias_semana_incluidos = models.CharField(
        max_length=60,
        help_text="Días de la semana incluidos (ej: LUN,MAR,MIE,JUE,VIE)",
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Plan de Almuerzo"
        verbose_name_plural = "Planes de Almuerzo"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


# ==============================================================================
# SUSCRIPCIÓN DE ALMUERZO
# ==============================================================================

class SuscripcionAlmuerzo(models.Model):
    """Suscripción de un hijo a un plan de almuerzo."""

    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        SUSPENDIDA = "SUSPENDIDA", "Suspendida"
        CANCELADA = "CANCELADA", "Cancelada"

    class TipoCobro(models.TextChoices):
        CUENTA = "CUENTA", "Por consumo (cuenta corriente)"
        MENSUAL = "MENSUAL", "Cuota mensual fija"

    hijo = models.ForeignKey(
        "clientes.Hijo", models.PROTECT, related_name="suscripciones_almuerzo"
    )
    plan = models.ForeignKey(
        PlanAlmuerzo, models.PROTECT, related_name="suscripciones"
    )
    tipo_cobro = models.CharField(
        max_length=10,
        choices=TipoCobro.choices,
        default=TipoCobro.CUENTA,
        help_text="CUENTA = padre paga al final del mes según consumo real. MENSUAL = cuota fija por adelantado.",
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.ACTIVA
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Suscripción de Almuerzo"
        verbose_name_plural = "Suscripciones de Almuerzo"
        constraints = [
            UniqueConstraint(
                fields=["hijo", "plan"],
                condition=Q(estado="ACTIVA"),
                name="unique_suscripcion_activa_por_hijo_plan",
            )
        ]

    def __str__(self):
        return f"{self.hijo} - {self.plan} ({self.get_estado_display()})"


# ==============================================================================
# REGISTRO DE CONSUMO DE ALMUERZO
# ==============================================================================

class RegistroConsumoAlmuerzo(models.Model):
    """Consumo diario de almuerzo por un estudiante."""

    class Estado(models.TextChoices):
        REGISTRADO = "REGISTRADO", "Registrado"
        RECHAZADO = "RECHAZADO", "Rechazado"
        ANULADO = "ANULADO", "Anulado"

    hijo = models.ForeignKey(
        "clientes.Hijo", models.PROTECT, related_name="consumos_almuerzo"
    )
    suscripcion = models.ForeignKey(
        SuscripcionAlmuerzo,
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="consumos",
    )
    tipo_almuerzo = models.ForeignKey(
        TipoAlmuerzo,
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="consumos",
    )
    fecha_consumo = models.DateField()
    hora_registro = models.TimeField(default=hora_actual)
    costo_almuerzo = models.DecimalField(
        max_digits=12, decimal_places=0,
        blank=True, null=True,
        help_text="Costo en Guaraníes al momento del consumo",
    )
    ya_cobrado = models.BooleanField(
        default=True,
        db_index=True,
        help_text="El primer registro del día cobra (True), siguientes no (False)",
    )
    marcado_en_cuenta = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Si se agregó a la cuenta mensual de almuerzo",
    )
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.REGISTRADO
    )
    motivo_rechazo = models.CharField(max_length=255, blank=True, null=True)
    nro_tarjeta = models.ForeignKey(
        "core.Tarjeta",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="consumos_almuerzo",
        help_text="Tarjeta usada al momento del consumo",
    )
    registrado_por = models.ForeignKey(
        "usuarios.Usuario",
        models.PROTECT,
        related_name="consumos_almuerzo_registrados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Consumo"
        verbose_name_plural = "Registros de Consumo"
        ordering = ["-fecha_consumo", "-hora_registro"]
        indexes = [
            models.Index(fields=["hijo", "fecha_consumo"]),
            models.Index(fields=["fecha_consumo"]),
            models.Index(fields=["estado"]),
        ]

    def save(self, *args, **kwargs):
        if self.costo_almuerzo is None:
            if self.tipo_almuerzo_id and self.tipo_almuerzo and self.tipo_almuerzo.precio_unitario:
                self.costo_almuerzo = self.tipo_almuerzo.precio_unitario
            elif self.fecha_consumo:
                precio = PrecioAlmuerzo.objects.filter(
                    fecha_inicio_vigencia__lte=self.fecha_consumo
                ).filter(
                    Q(fecha_fin_vigencia__gte=self.fecha_consumo) | Q(fecha_fin_vigencia__isnull=True)
                ).order_by("-fecha_inicio_vigencia").first()
                if precio:
                    self.costo_almuerzo = precio.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.hijo} - {self.fecha_consumo} ({self.get_estado_display()})"


# ==============================================================================
# CUENTA MENSUAL DE ALMUERZO
# ==============================================================================

class CuentaAlmuerzoMensual(models.Model):
    """Cuenta mensual que agrupa los consumos de almuerzo de un hijo."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        VALIDACION = "VALIDACION", "Validación Pendiente"
        PAGADO = "PAGADO", "Pagado"
        PARCIAL = "PARCIAL", "Parcial"
        ANULADO = "ANULADO", "Anulado"

    class FormaCobro(models.TextChoices):
        EFECTIVO = "EFECTIVO", "Efectivo"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia bancaria"
        ONLINE = "ONLINE", "Pago online"
        DEBITO_AUTOMATICO = "DEBITO_AUTOMATICO", "Débito automático"

    hijo = models.ForeignKey(
        "clientes.Hijo", models.PROTECT, related_name="cuentas_almuerzo"
    )
    anio = models.IntegerField()
    mes = models.SmallIntegerField()
    cantidad_almuerzos = models.IntegerField()
    monto_total = models.DecimalField(max_digits=12, decimal_places=0)
    forma_cobro = models.CharField(max_length=20, choices=FormaCobro.choices)
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.PENDIENTE
    )
    fecha_generacion = models.DateField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_pago = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    comprobante_pago = models.TextField(
        blank=True, help_text="Referencia o URL del comprobante"
    )
    nro_comprobante = models.CharField(
        max_length=30, blank=True,
        help_text="Número de comprobante (ej: 001-001-0000001)",
    )
    factura = models.ForeignKey(
        "contabilidad.Factura",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="cuentas_almuerzo",
        help_text="Factura preimpresa asociada",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cuenta Mensual de Almuerzo"
        verbose_name_plural = "Cuentas Mensuales de Almuerzo"
        constraints = [
            UniqueConstraint(fields=["hijo", "anio", "mes"], name="unique_cuenta_almuerzo_mensual")
        ]
        ordering = ["-anio", "-mes"]

    def __str__(self):
        return f"{self.hijo} - {self.mes:02d}/{self.anio} - ₲{self.monto_total:,.0f}"

    @property
    def saldo_pendiente(self):
        return self.monto_total - self.monto_pagado

    def _calcular_estado(self):
        """Actualiza estado y fecha_pago en la instancia sin guardar."""
        if self.monto_pagado >= self.monto_total:
            self.estado = self.Estado.PAGADO
            if not self.fecha_pago:
                self.fecha_pago = timezone.now().date()
        elif self.monto_pagado > 0:
            self.estado = self.Estado.PARCIAL
        else:
            self.estado = self.Estado.PENDIENTE

    def actualizar_estado(self):
        """Recalcula el estado según los montos actuales y persiste."""
        self._calcular_estado()
        self.save(update_fields=["estado", "fecha_pago"])

    def registrar_pago(self, monto):
        """Incrementa monto_pagado, recalcula estado y persiste todo en un solo save."""
        nuevo_pagado = self.monto_pagado + monto
        if nuevo_pagado > self.monto_total:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                {"monto": f"El pago (₲{monto:,.0f}) supera el saldo pendiente (₲{self.saldo_pendiente:,.0f})."}
            )
        self.monto_pagado = nuevo_pagado
        self._calcular_estado()
        self.save(update_fields=["monto_pagado", "estado", "fecha_pago"])


# ==============================================================================
# PAGO DE CUENTA DE ALMUERZO
# ==============================================================================

class PagoCuentaAlmuerzo(models.Model):
    """
    Pago de la cuenta mensual de consumo (pay-as-you-eat).
    Liquida una CuentaAlmuerzoMensual generada por consumos reales del mes.
    No confundir con PagoAlmuerzoMensual, que es la cuota fija de un plan.
    """

    cuenta = models.ForeignKey(
        CuentaAlmuerzoMensual, models.PROTECT, related_name="pagos"
    )
    monto = models.DecimalField(max_digits=12, decimal_places=0)
    fecha_pago = models.DateTimeField(default=timezone.now)
    medio_pago = models.CharField(max_length=15)
    referencia = models.CharField(max_length=50, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    registrado_por = models.ForeignKey(
        "usuarios.Usuario",
        models.PROTECT,
        related_name="pagos_almuerzo_registrados",
    )
    factura = models.OneToOneField(
        "contabilidad.Factura",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="pago_cuenta_almuerzo",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pago de Cuenta de Almuerzo"
        verbose_name_plural = "Pagos de Cuentas de Almuerzo"
        ordering = ["-fecha_pago"]

    def __str__(self):
        return f"Pago #{self.pk} - {self.cuenta} - ₲{self.monto:,.0f}"

    def clean(self):
        if self.cuenta_id and self.monto is not None:
            if self.monto <= 0:
                raise ValidationError({"monto": "El monto debe ser mayor a cero."})
            saldo = self.cuenta.saldo_pendiente
            if self.monto > saldo:
                raise ValidationError(
                    {"monto": f"El monto (₲{self.monto:,.0f}) supera el saldo pendiente (₲{saldo:,.0f})."}
                )


# ==============================================================================
# PAGO MENSUAL DE SUSCRIPCIÓN
# ==============================================================================

class PagoAlmuerzoMensual(models.Model):
    """
    Cuota mensual de un plan de almuerzo (suscripción fija).
    Liquida la SuscripcionAlmuerzo del mes, independientemente del consumo real.
    No confundir con PagoCuentaAlmuerzo, que liquida consumos por cuenta corriente.
    """

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        CONFIRMADO = "CONFIRMADO", "Confirmado"
        RECHAZADO = "RECHAZADO", "Rechazado"

    suscripcion = models.ForeignKey(
        SuscripcionAlmuerzo, models.PROTECT, related_name="pagos_mensuales"
    )
    venta = models.OneToOneField(
        "ventas.Venta",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="pago_almuerzo",
    )
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=0)
    mes_pagado = models.DateField(help_text="Mes al que corresponde el pago")
    fecha_pago = models.DateTimeField(default=timezone.now)
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.PENDIENTE
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pago Mensual de Almuerzo"
        verbose_name_plural = "Pagos Mensuales de Almuerzo"
        constraints = [
            UniqueConstraint(fields=["suscripcion", "mes_pagado"], name="unique_pago_mensual_suscripcion")
        ]
        ordering = ["-fecha_pago"]

    def clean(self):
        if self.mes_pagado:
            if self.mes_pagado.day != 1:
                raise ValidationError({"mes_pagado": "Debe ser el primer día del mes (ej: 2026-05-01)."})
            if self.mes_pagado > date.today().replace(day=1):
                raise ValidationError({"mes_pagado": "No se puede registrar un pago de un mes futuro."})

    def __str__(self):
        return f"Pago {self.suscripcion} - {self.mes_pagado}"


# ==============================================================================
# ALÉRGENOS
# ==============================================================================

class Alergeno(models.Model):
    """Alérgeno que puede estar presente en productos."""

    class Severidad(models.TextChoices):
        BAJA = "BAJA", "Baja"
        MEDIA = "MEDIA", "Media"
        ALTA = "ALTA", "Alta"
        CRITICA = "CRITICA", "Crítica"

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    palabras_clave = models.JSONField(
        default=list,
        help_text="Lista de palabras clave para detectar el alérgeno en descripciones",
    )
    severidad = models.CharField(
        max_length=10, choices=Severidad.choices, default=Severidad.MEDIA
    )
    icono = models.CharField(max_length=10, blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        "usuarios.Usuario",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="alergenos_creados",
    )

    class Meta:
        verbose_name = "Alérgeno"
        verbose_name_plural = "Alérgenos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class ProductoAlergeno(models.Model):
    """Relación producto-alérgeno."""

    producto = models.ForeignKey(
        "productos.Producto", models.CASCADE, related_name="alergenos"
    )
    alergeno = models.ForeignKey(
        Alergeno, models.CASCADE, related_name="productos"
    )
    contiene = models.BooleanField(
        default=True,
        help_text="True=Contiene el alérgeno, False=Puede contener trazas",
    )
    observaciones = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(
        "usuarios.Usuario",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="alergenos_productos_registrados",
    )

    class Meta:
        verbose_name = "Producto-Alérgeno"
        verbose_name_plural = "Productos-Alérgenos"
        constraints = [
            UniqueConstraint(fields=["producto", "alergeno"], name="unique_producto_alergeno")
        ]

    def __str__(self):
        verbo = "Contiene" if self.contiene else "Trazas de"
        return f"{self.producto} {verbo} {self.alergeno}"


# ==============================================================================
# MENÚ DIARIO
# ==============================================================================

class MenuDiario(models.Model):
    """Menú del día visible para padres en el portal."""

    fecha = models.DateField(unique=True)
    plato_principal = models.CharField(max_length=255)
    guarnicion = models.CharField(max_length=255, blank=True)
    postre = models.CharField(max_length=255, blank=True)
    bebida = models.CharField(max_length=100, blank=True)
    descripcion = models.TextField(blank=True, help_text="Descripción adicional o notas")
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(
        "usuarios.Usuario",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="menus_creados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Menú Diario"
        verbose_name_plural = "Menús Diarios"
        ordering = ["-fecha"]

    def __str__(self):
        return f"Menú {self.fecha} — {self.plato_principal}"

    @property
    def tiene_alergenos(self):
        """True si algún producto del menú tiene alérgenos registrados."""
        return self.detalles.filter(
            producto__alergenos__isnull=False
        ).exists()


class DetalleMenuDiario(models.Model):
    """
    Relaciona un menú del día con los productos del catálogo que lo componen.
    Permite calcular costo, alérgenos y descontar stock automáticamente.
    """

    class Curso(models.TextChoices):
        ENTRADA       = "ENTRADA",       "Entrada"
        PLATO_PRINCIPAL = "PLATO_PRINCIPAL", "Plato principal"
        GUARNICION    = "GUARNICION",    "Guarnición"
        POSTRE        = "POSTRE",        "Postre"
        BEBIDA        = "BEBIDA",        "Bebida"
        EXTRA         = "EXTRA",         "Extra"

    menu = models.ForeignKey(
        MenuDiario,
        models.CASCADE,
        related_name="detalles",
    )
    producto = models.ForeignKey(
        "productos.Producto",
        models.PROTECT,
        related_name="apariciones_menu",
        help_text="Producto del catálogo que compone este plato",
    )
    curso = models.CharField(
        max_length=20,
        choices=Curso.choices,
        default=Curso.PLATO_PRINCIPAL,
        help_text="Parte del menú a la que pertenece este ítem",
    )
    cantidad = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        default=1,
        help_text="Cantidad de producto por porción (en la unidad de medida del producto)",
    )
    es_opcional = models.BooleanField(
        default=False,
        help_text="El alumno puede elegir si lo consume o no",
    )
    observaciones = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Detalle de Menú Diario"
        verbose_name_plural = "Detalles de Menú Diario"
        ordering = ["menu", "curso"]
        constraints = [
            models.UniqueConstraint(
                fields=["menu", "producto", "curso"],
                name="uq_menu_producto_curso",
            ),
            models.CheckConstraint(
                check=models.Q(cantidad__gt=0),
                name="chk_detalle_menu_cantidad_positiva",
            ),
        ]

    def __str__(self):
        return f"{self.menu.fecha} | {self.get_curso_display()} | {self.producto}"
