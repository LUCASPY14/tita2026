"""
Modelos para el módulo de cobros y pagos de clientes.
Gestión de pagos de cuenta corriente y aplicación a facturas pendientes.
"""

from decimal import Decimal

from django.db import models


class PagosClientes(models.Model):
    """
    Registro de pagos realizados por clientes para saldar su cuenta corriente.
    """

    id_pago_cliente = models.BigAutoField(primary_key=True)
    id_cliente = models.ForeignKey(
        "clientes.Clientes",
        on_delete=models.PROTECT,
        db_column="id_cliente",
        related_name="pagos_realizados",
        help_text="Cliente que realiza el pago",
    )
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, help_text="Monto total del pago")
    fecha_pago = models.DateTimeField(auto_now_add=True, help_text="Fecha y hora del pago")
    id_medio_pago = models.ForeignKey(
        "core.MediosPago", on_delete=models.PROTECT, db_column="id_medio_pago", help_text="Medio de pago utilizado"
    )
    referencia = models.CharField(max_length=100, blank=True, null=True, help_text="Número de referencia/comprobante")
    banco_emisor = models.CharField(
        max_length=100, blank=True, null=True, help_text="Banco emisor (transferencia/cheque)"
    )
    observaciones = models.TextField(blank=True, null=True, help_text="Observaciones del pago")
    id_empleado_cajero = models.ForeignKey(
        "usuarios.Empleados",
        on_delete=models.PROTECT,
        db_column="id_empleado_cajero",
        help_text="Empleado que registró el pago",
    )
    estado = models.CharField(max_length=20, default="Confirmado", help_text="Estado del pago: Confirmado, Anulado")
    id_cierre = models.BigIntegerField(blank=True, null=True, help_text="ID del cierre de caja asociado")

    class Meta:
        managed = True
        db_table = "pagos_clientes"
        verbose_name = "Pago de Cliente"
        verbose_name_plural = "Pagos de Clientes"
        ordering = ["-fecha_pago"]
        indexes = [
            models.Index(fields=["id_cliente", "fecha_pago"], name="idx_pagos_cli_cliente"),
            models.Index(fields=["fecha_pago"], name="idx_pagos_cli_fecha"),
            models.Index(fields=["estado"], name="idx_pagos_cli_estado"),
            models.Index(fields=["id_empleado_cajero", "fecha_pago"], name="idx_pagos_cli_cajero"),
        ]

    def __str__(self):
        return f"Pago #{self.id_pago_cliente} - {self.id_cliente.nombre_completo} - Gs. {self.monto_total:,.0f}"

    @property
    def monto_aplicado(self):
        """Calcula el monto total aplicado a facturas"""
        total = self.aplicaciones.aggregate(total=models.Sum("monto_aplicado"))["total"]
        return total or Decimal("0.00")

    @property
    def monto_pendiente_aplicar(self):
        """Calcula el monto que falta aplicar a facturas"""
        return self.monto_total - self.monto_aplicado


class AplicacionPagosClientes(models.Model):
    """
    Aplicación de un pago de cliente a una factura específica.
    Permite distribuir un pago entre múltiples facturas.
    """

    id_aplicacion = models.BigAutoField(primary_key=True)
    id_pago_cliente = models.ForeignKey(
        "PagosClientes",
        on_delete=models.CASCADE,
        db_column="id_pago_cliente",
        related_name="aplicaciones",
        help_text="Pago al que pertenece esta aplicación",
    )
    id_venta = models.ForeignKey(
        "ventas.Ventas",
        on_delete=models.PROTECT,
        db_column="id_venta",
        related_name="pagos_aplicados",
        help_text="Venta a la que se aplica el pago",
    )
    monto_aplicado = models.DecimalField(max_digits=12, decimal_places=2, help_text="Monto aplicado a esta factura")
    fecha_aplicacion = models.DateTimeField(auto_now_add=True, help_text="Fecha de aplicación")

    class Meta:
        managed = True
        db_table = "aplicacion_pagos_clientes"
        verbose_name = "Aplicación de Pago"
        verbose_name_plural = "Aplicaciones de Pagos"
        ordering = ["-fecha_aplicacion"]
        indexes = [
            models.Index(fields=["id_pago_cliente"], name="idx_aplic_pago_cli"),
            models.Index(fields=["id_venta"], name="idx_aplic_venta"),
        ]

    def __str__(self):
        return f"Aplicación #{self.id_aplicacion} - Factura {self.id_venta_id} - Gs. {self.monto_aplicado:,.0f}"
