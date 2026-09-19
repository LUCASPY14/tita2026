"""
Cierre de cuentas de alumnos que egresan (o se retiran).

Cada alumno tiene, como máximo, un expediente por año (CierreCuentaAlumno) con los
saldos que tenía al abrirlo y todas las resoluciones tomadas (ResolucionSaldo):
devolución, traspaso a un hermano, compensación entre bolsillos, cobro, traslado
a la cuenta corriente familiar o condonación.

Nada se edita a mano: cada resolución ejecutada genera movimientos en el libro
mayor de la tarjeta / del saldo de almuerzo (y en caja cuando entra o sale
dinero). Los ids de movimientos de tarjeta se guardan como enteros porque esa
tabla está particionada por año y no admite claves foráneas.
"""
from django.db import models
from django.db.models import Q


class CierreCuentaAlumno(models.Model):
    class Estado(models.TextChoices):
        ABIERTO = "ABIERTO", "Abierto"
        PARCIAL = "PARCIAL", "Parcial"
        RESUELTO = "RESUELTO", "Resuelto"
        CERRADO_CON_SALDO = "CERRADO_CON_SALDO", "Cerrado con saldo pendiente"

    id_cierre_cuenta = models.BigAutoField(primary_key=True)
    hijo = models.ForeignKey("clientes.Hijo", models.PROTECT, related_name="cierres_cuenta")
    anio = models.IntegerField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ABIERTO)

    # Saldos al abrir el expediente (referencia; los saldos vigentes se leen en vivo).
    saldo_cantina_inicial = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    saldo_almuerzo_inicial = models.DecimalField(max_digits=12, decimal_places=0, default=0)

    fecha_apertura = models.DateTimeField(auto_now_add=True)
    abierto_por = models.ForeignKey(
        "usuarios.Usuario", models.SET_NULL, null=True, blank=True, related_name="+",
    )

    fecha_cierre = models.DateTimeField(null=True, blank=True)
    cerrado_por = models.ForeignKey(
        "usuarios.Usuario", models.SET_NULL, null=True, blank=True, related_name="+",
    )
    motivo_cierre = models.TextField(blank=True)
    saldo_cantina_final = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    saldo_almuerzo_final = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)

    class Meta:
        verbose_name = "Cierre de cuenta de alumno"
        verbose_name_plural = "Cierres de cuenta de alumnos"
        ordering = ["-anio", "hijo__apellido", "hijo__nombre"]
        constraints = [
            models.UniqueConstraint(fields=["hijo", "anio"], name="unique_cierre_cuenta_hijo_anio"),
        ]

    def __str__(self):
        return f"Cierre {self.anio} — {self.hijo}"


class ResolucionSaldo(models.Model):
    class Tipo(models.TextChoices):
        DEVOLUCION = "DEVOLUCION", "Devolución"
        TRASPASO_HERMANO = "TRASPASO_HERMANO", "Traspaso a hermano"
        COMPENSACION = "COMPENSACION", "Compensación entre bolsillos"
        COBRO = "COBRO", "Cobro de deuda"
        TRASLADO_CC = "TRASLADO_CC", "Traslado a cuenta corriente familiar"
        CONDONACION = "CONDONACION", "Condonación"

    class Bolsillo(models.TextChoices):
        CANTINA = "CANTINA", "Cantina (tarjeta)"
        ALMUERZO = "ALMUERZO", "Almuerzo"

    class Estado(models.TextChoices):
        SOLICITADA = "SOLICITADA", "Pendiente de aprobación"
        EJECUTADA = "EJECUTADA", "Ejecutada"
        RECHAZADA = "RECHAZADA", "Rechazada"

    id_resolucion = models.BigAutoField(primary_key=True)
    cierre = models.ForeignKey(CierreCuentaAlumno, models.PROTECT, related_name="resoluciones")
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.SOLICITADA)

    bolsillo_origen = models.CharField(max_length=10, choices=Bolsillo.choices)
    bolsillo_destino = models.CharField(max_length=10, choices=Bolsillo.choices, blank=True)
    hijo_destino = models.ForeignKey(
        "clientes.Hijo", models.PROTECT, null=True, blank=True, related_name="resoluciones_recibidas",
    )
    monto = models.DecimalField(max_digits=12, decimal_places=0)

    metodo_pago = models.CharField(max_length=50, blank=True)
    referencia = models.CharField(max_length=100, blank=True)
    motivo = models.TextField(blank=True)

    solicitado_por = models.ForeignKey("usuarios.Usuario", models.PROTECT, related_name="+")
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    decidido_por = models.ForeignKey(
        "usuarios.Usuario", models.PROTECT, null=True, blank=True, related_name="+",
    )
    fecha_decision = models.DateTimeField(null=True, blank=True)
    motivo_rechazo = models.TextField(blank=True)
    fecha_ejecucion = models.DateTimeField(null=True, blank=True)

    # Rastro en el libro mayor. Tarjeta: entero (tabla particionada, sin FK).
    movimiento_tarjeta_origen_id = models.BigIntegerField(null=True, blank=True)
    movimiento_tarjeta_destino_id = models.BigIntegerField(null=True, blank=True)
    movimiento_almuerzo_origen = models.ForeignKey(
        "almuerzos.MovimientoSaldoAlmuerzo", models.PROTECT, null=True, blank=True, related_name="+",
    )
    movimiento_almuerzo_destino = models.ForeignKey(
        "almuerzos.MovimientoSaldoAlmuerzo", models.PROTECT, null=True, blank=True, related_name="+",
    )
    movimiento_caja = models.ForeignKey(
        "contabilidad.MovimientoCaja", models.PROTECT, null=True, blank=True, related_name="+",
    )
    movimiento_cc = models.ForeignKey(
        "clientes.CuentaCorrienteCliente", models.PROTECT, null=True, blank=True, related_name="+",
    )
    carga_saldo = models.ForeignKey(
        "core.CargaSaldo", models.PROTECT, null=True, blank=True, related_name="+",
    )
    recarga_almuerzo = models.ForeignKey(
        "almuerzos.RecargaSaldoAlmuerzo", models.PROTECT, null=True, blank=True, related_name="+",
    )

    class Meta:
        verbose_name = "Resolución de saldo"
        verbose_name_plural = "Resoluciones de saldo"
        ordering = ["-fecha_solicitud", "-id_resolucion"]
        constraints = [
            models.CheckConstraint(condition=Q(monto__gt=0), name="resolucion_monto_positivo"),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} Gs. {self.monto:,.0f} ({self.get_estado_display()})"
