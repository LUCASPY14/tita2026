"""
Modelos de la app core
Tarjetas, movimientos de tarjeta, medios de pago, límites de transacción y autorizaciones
"""

from decimal import Decimal
from django.db import models
from django.utils import timezone


# ==============================================================================
# TARJETA
# ==============================================================================

class Tarjeta(models.Model):
    """Tarjeta RFID/código de barras asociada a un estudiante."""

    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        BLOQUEADA = "BLOQUEADA", "Bloqueada"
        VENCIDA = "VENCIDA", "Vencida"
        CANCELADA = "CANCELADA", "Cancelada"

    nro_tarjeta = models.CharField(primary_key=True, max_length=20)
    codigo_barras = models.CharField(
        max_length=50, unique=True, blank=True, null=True
    )
    hijo = models.OneToOneField(
        "clientes.Hijo",
        models.PROTECT,
        related_name="tarjeta",
        help_text="Estudiante dueño de la tarjeta",
    )
    saldo_actual = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        help_text="Saldo en Guaraníes",
    )
    limite_credito = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        help_text="Límite de crédito en Guaraníes",
    )
    permite_saldo_negativo = models.BooleanField(default=False)
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.ACTIVA
    )
    fecha_vencimiento = models.DateField(blank=True, null=True)
    saldo_alerta = models.DecimalField(
        max_digits=12, decimal_places=0, blank=True, null=True,
        help_text="Umbral para notificación de saldo bajo",
    )
    notificar_saldo_bajo = models.BooleanField(default=True)
    ultima_notificacion_saldo = models.DateTimeField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tarjeta"
        verbose_name_plural = "Tarjetas"

    def __str__(self):
        return f"Tarjeta {self.nro_tarjeta} - {self.hijo}"

    @property
    def saldo_disponible(self):
        """Saldo disponible considerando límite de crédito."""
        if self.permite_saldo_negativo:
            return self.saldo_actual + self.limite_credito
        return max(self.saldo_actual, Decimal("0"))

    @property
    def esta_en_alerta(self):
        if self.saldo_alerta is not None:
            return self.saldo_actual <= self.saldo_alerta
        return False

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.hijo_id:
            existente = Tarjeta.objects.filter(hijo=self.hijo).exclude(
                nro_tarjeta=self.nro_tarjeta
            ).first()
            if existente:
                raise ValidationError({
                    "hijo": "Este estudiante ya tiene una tarjeta asociada."
                })


# ==============================================================================
# MOVIMIENTO DE TARJETA
# ==============================================================================

class MovimientoTarjeta(models.Model):
    """
    Historial de movimientos de saldo de tarjeta.
    Débito = consumo (reduce el saldo).
    Crédito = recarga o reverso (aumenta el saldo).
    """

    class Tipo(models.TextChoices):
        RECARGA = "RECARGA", "Recarga"
        CONSUMO = "CONSUMO", "Consumo"
        AJUSTE = "AJUSTE", "Ajuste"
        REVERSO = "REVERSO", "Reverso"

    tarjeta = models.ForeignKey(
        Tarjeta,
        models.PROTECT,
        related_name="movimientos",
    )
    fecha = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    monto = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Monto en Guaraníes"
    )
    saldo_anterior = models.DecimalField(max_digits=12, decimal_places=0)
    saldo_resultante = models.DecimalField(max_digits=12, decimal_places=0)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    # Referencias a documentos origen
    carga = models.ForeignKey(
        "CargaSaldo",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_tarjeta",
    )
    consumo = models.ForeignKey(
        "ConsumoTarjeta",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_tarjeta",
    )

    # Auditoría
    creado_por = models.ForeignKey(
        "usuarios.Usuario",
        models.PROTECT,
        related_name="movimientos_tarjeta_creados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de Tarjeta"
        verbose_name_plural = "Movimientos de Tarjetas"
        ordering = ["-fecha", "-id"]
        indexes = [
            models.Index(fields=["tarjeta", "fecha"], name="idx_mov_tarj_fecha"),
            models.Index(fields=["tarjeta", "tipo"], name="idx_mov_tarj_tipo"),
        ]

    def __str__(self):
        signo = "+" if self.tipo in (self.Tipo.RECARGA, self.Tipo.REVERSO) else "-"
        return f"{self.get_tipo_display()} - {self.tarjeta} - {signo}₲{self.monto:,.0f}"

    def save(self, *args, **kwargs):
        """Calcula automáticamente el saldo resultante."""
        if self.saldo_anterior is None:
            ultimo = (
                MovimientoTarjeta.objects
                .filter(tarjeta=self.tarjeta)
                .order_by("-id")
                .first()
            )
            self.saldo_anterior = ultimo.saldo_resultante if ultimo else Decimal("0")

        if self.tipo in (self.Tipo.RECARGA, self.Tipo.REVERSO):
            self.saldo_resultante = self.saldo_anterior + self.monto
        else:
            self.saldo_resultante = self.saldo_anterior - self.monto

        super().save(*args, **kwargs)


# ==============================================================================
# TARJETA DE AUTORIZACIÓN
# ==============================================================================

class TarjetaAutorizacion(models.Model):
    """Tarjeta para autorizar operaciones especiales (supervisores)."""

    codigo_barra = models.CharField(max_length=50, unique=True)
    tipo_autorizacion = models.CharField(max_length=15)
    puede_anular_almuerzos = models.BooleanField(default=False)
    puede_anular_ventas = models.BooleanField(default=False)
    puede_anular_recargas = models.BooleanField(default=False)
    puede_modificar_precios = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    empleado = models.ForeignKey(
        "usuarios.Usuario",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="tarjetas_autorizacion",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tarjeta de Autorización"
        verbose_name_plural = "Tarjetas de Autorización"

    def __str__(self):
        return f"Tarjeta Auth {self.codigo_barra} - {self.tipo_autorizacion}"


# ==============================================================================
# CARGA DE SALDO
# ==============================================================================

class CargaSaldo(models.Model):
    """Recarga de saldo a una tarjeta."""

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        RECHAZADA = "RECHAZADA", "Rechazada"

    tarjeta = models.ForeignKey(
        Tarjeta,
        models.PROTECT,
        null=True,
        blank=True,
        related_name="cargas",
    )
    cliente_origen = models.ForeignKey(
        "clientes.Cliente",
        models.PROTECT,
        null=True,
        blank=True,
        related_name="cargas_saldo",
    )
    monto_cargado = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Monto en Guaraníes"
    )
    fecha_carga = models.DateTimeField(default=timezone.now)
    estado = models.CharField(
        max_length=15, choices=Estado.choices, default=Estado.PENDIENTE
    )
    referencia = models.CharField(max_length=100, blank=True, null=True)
    metodo_pago = models.CharField(max_length=50, blank=True, null=True)
    comision = models.DecimalField(
        max_digits=12, decimal_places=0, default=0,
        help_text="Comisión cobrada en Guaraníes",
    )
    total_cobrado = models.DecimalField(
        max_digits=12, decimal_places=0, blank=True, null=True,
        help_text="Total cobrado (monto + comisión)",
    )
    venta = models.ForeignKey(
        "ventas.Venta",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="cargas_saldo",
    )
    responsable = models.ForeignKey(
        "usuarios.Usuario",
        models.PROTECT,
        null=True,
        blank=True,
        related_name="cargas_procesadas",
    )
    supervisor_aprobador = models.ForeignKey(
        "usuarios.Usuario",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="cargas_aprobadas",
    )
    fecha_aprobacion = models.DateTimeField(blank=True, null=True)
    fecha_confirmacion = models.DateTimeField(blank=True, null=True)
    pay_request_id = models.CharField(max_length=100, blank=True, null=True)
    tx_id = models.CharField(max_length=100, blank=True, null=True)
    custom_identifier = models.CharField(max_length=100, blank=True, null=True)
    numero_comprobante_externo = models.CharField(
        max_length=100, blank=True, null=True
    )
    referencia_externa = models.CharField(
        max_length=200, blank=True, null=True
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Carga de Saldo"
        verbose_name_plural = "Cargas de Saldo"
        ordering = ["-fecha_carga"]

    def __str__(self):
        return f"Carga #{self.pk} - {self.tarjeta} - ₲{self.monto_cargado:,.0f}"


# ==============================================================================
# CONSUMO DE TARJETA
# ==============================================================================

class ConsumoTarjeta(models.Model):
    """Registro de consumo realizado con una tarjeta."""

    tarjeta = models.ForeignKey(
        Tarjeta, models.PROTECT, related_name="consumos"
    )
    fecha_consumo = models.DateTimeField(default=timezone.now)
    monto_consumido = models.DecimalField(
        max_digits=12, decimal_places=0, help_text="Monto en Guaraníes"
    )
    saldo_anterior = models.DecimalField(max_digits=12, decimal_places=0)
    saldo_posterior = models.DecimalField(max_digits=12, decimal_places=0)
    detalle = models.CharField(max_length=200, blank=True, null=True)
    registrado_por = models.ForeignKey(
        "usuarios.Usuario",
        models.PROTECT,
        null=True,
        blank=True,
        related_name="consumos_tarjeta_registrados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Consumo de Tarjeta"
        verbose_name_plural = "Consumos de Tarjetas"
        ordering = ["-fecha_consumo"]

    def __str__(self):
        return f"Consumo {self.tarjeta} - ₲{self.monto_consumido:,.0f}"


# ==============================================================================
# MEDIO DE PAGO
# ==============================================================================

class MedioPago(models.Model):
    """Medio de pago aceptado (efectivo, POS, transferencia, QR)."""

    descripcion = models.CharField(max_length=50, unique=True)
    requiere_validacion = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Medio de Pago"
        verbose_name_plural = "Medios de Pago"

    def __str__(self):
        return self.descripcion


# ==============================================================================
# LÍMITE DE TRANSACCIÓN
# ==============================================================================

class LimiteTransaccion(models.Model):
    """Límite de autorización por rol para operaciones críticas."""

    class TipoOperacion(models.TextChoices):
        VENTA = "VENTA", "Venta"
        DESCUENTO = "DESCUENTO", "Aplicar descuento"
        NOTA_CREDITO_CLIENTE = "NOTA_CREDITO_CLIENTE", "Nota de crédito a cliente"
        NOTA_CREDITO_PROVEEDOR = "NOTA_CREDITO_PROVEEDOR", "Nota de crédito de proveedor"
        AJUSTE_INVENTARIO = "AJUSTE_INVENTARIO", "Ajuste de inventario"
        EXCEDER_CREDITO = "EXCEDER_CREDITO", "Exceder límite de crédito"
        ANULAR_VENTA = "ANULAR_VENTA", "Anular venta"
        RETIRO_CAJA = "RETIRO_CAJA", "Retiro de caja"
        DEVOLUCION = "DEVOLUCION", "Procesar devolución"

    rol = models.ForeignKey(
        "usuarios.Rol",
        models.PROTECT,
        related_name="limites_transaccion",
    )
    tipo_operacion = models.CharField(max_length=30, choices=TipoOperacion.choices)
    monto_maximo = models.DecimalField(
        max_digits=12, decimal_places=0,
        help_text="Monto máximo en Guaraníes sin autorización",
    )
    requiere_autorizacion_doble = models.BooleanField(default=False)
    roles_autorizadores = models.ManyToManyField(
        "usuarios.Rol",
        related_name="limites_autorizables",
        blank=True,
    )
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True, null=True)
    configurado_por = models.ForeignKey(
        "usuarios.Usuario",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="limites_configurados",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Límite de Transacción"
        verbose_name_plural = "Límites de Transacciones"
        unique_together = [("rol", "tipo_operacion")]
        indexes = [
            models.Index(fields=["rol", "tipo_operacion"]),
            models.Index(fields=["tipo_operacion", "activo"]),
        ]

    def __str__(self):
        return f"{self.rol} - {self.get_tipo_operacion_display()}: ₲{self.monto_maximo:,.0f}"


# ==============================================================================
# REGISTRO DE AUTORIZACIÓN
# ==============================================================================

class RegistroAutorizacion(models.Model):
    """Registro de autorizaciones otorgadas (auditoría)."""

    tipo_operacion = models.CharField(max_length=50)
    monto = models.DecimalField(max_digits=12, decimal_places=0)
    motivo = models.TextField()
    fecha_autorizacion = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    solicitante = models.ForeignKey(
        "usuarios.Usuario",
        models.PROTECT,
        related_name="autorizaciones_solicitadas",
    )
    autorizador = models.ForeignKey(
        "usuarios.Usuario",
        models.PROTECT,
        related_name="autorizaciones_otorgadas",
    )
    autorizador_2 = models.ForeignKey(
        "usuarios.Usuario",
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="autorizaciones_dobles",
    )
    venta = models.ForeignKey(
        "ventas.Venta", models.SET_NULL, null=True, blank=True
    )
    compra = models.ForeignKey(
        "compras.Compra", models.SET_NULL, null=True, blank=True
    )
    ajuste = models.ForeignKey(
        "inventario.AjusteInventario", models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = "Registro de Autorización"
        verbose_name_plural = "Registro de Autorizaciones"
        ordering = ["-fecha_autorizacion"]
        indexes = [
            models.Index(fields=["solicitante", "-fecha_autorizacion"]),
            models.Index(fields=["autorizador", "-fecha_autorizacion"]),
            models.Index(fields=["tipo_operacion", "-fecha_autorizacion"]),
        ]

    def __str__(self):
        return f"{self.tipo_operacion} - ₲{self.monto:,.0f} - {self.fecha_autorizacion:%d/%m/%Y %H:%M}"