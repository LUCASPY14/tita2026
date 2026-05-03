"""
Tests extendidos para apps/compras/signals.py
Cubre líneas faltantes:
32 (if not created: return en actualizar_saldo_compra),
40 (saldo negativo → 0 en actualizar_saldo_compra),
48 (saldo parcial en actualizar_saldo_compra),
69 (if nota not aplicada → return en aplicar_nota_credito_proveedor),
79 (saldo negativo → 0 en aplicar_nota_credito_proveedor),
83 (saldo parcial en aplicar_nota_credito_proveedor)
"""

from decimal import Decimal

from django.test import TransactionTestCase
from django.utils import timezone

from apps.compras.models import (
    AplicacionPagosCompras,
    Compras,
    NotasCreditoProveedor,
    PagosProveedores,
    Proveedores,
)
from apps.core.models import MediosPago
from apps.usuarios.models import Empleados, Roles


def make_proveedor():
    return Proveedores.objects.create(
        razon_social="Proveedor Signals Test",
        ruc="99887-1",
        fecha_registro=timezone.now(),
        estado=True,
    )


def make_empleado():
    rol = Roles.objects.create(nombre_rol="RolSignals", estado=True)
    return Empleados.objects.create(
        nombre="EmpSignals",
        apellido="Test",
        usuario="emp_signals_test",
        contrasena_hash="hash",
        fecha_ingreso=timezone.now(),
        email="emp_signals@test.com",
        estado=True,
        id_rol=rol,
    )


def make_compra(proveedor, monto_total=Decimal("100000.00"), saldo=None, estado_pago="Pendiente"):
    return Compras.objects.create(
        id_proveedor=proveedor,
        fecha=timezone.now(),
        nro_factura=f"001-001-SIG{Compras.objects.count():04d}",
        estado_pago=estado_pago,
        monto_total=monto_total,
        saldo_pendiente=saldo if saldo is not None else monto_total,
    )


def make_pago_proveedor():
    medio = MediosPago.objects.create(descripcion="Efectivo Signals", estado=True)
    return PagosProveedores.objects.create(
        fecha_creacion=timezone.now(),
        id_medio_pago=medio,
    )


# =============================================================================
# actualizar_saldo_compra signal - líneas 32, 40, 48
# =============================================================================


class ActualizarSaldoCompraSignalTest(TransactionTestCase):
    """Tests para signal actualizar_saldo_compra"""

    def setUp(self):
        self.proveedor = make_proveedor()

    def test_update_no_dispara_signal(self):
        """Línea 32: created=False → signal retorna sin modificar"""
        compra = make_compra(self.proveedor)
        pago = make_pago_proveedor()
        # Crear la aplicación
        aplicacion = AplicacionPagosCompras.objects.create(
            monto_aplicado=Decimal("50000.00"),
            id_compra=compra,
            id_pago_proveedor=pago,
        )
        saldo_antes = compra.monto_total - Decimal("50000.00")

        # Modificar y guardar (created=False → signal no actúa)
        aplicacion.monto_aplicado = Decimal("60000.00")
        aplicacion.save()

        compra.refresh_from_db()
        # El saldo fue reducido solo en la primera creación, no en el update
        self.assertEqual(compra.saldo_pendiente, saldo_antes)

    def test_pago_mas_grande_que_saldo_ajusta_a_cero(self):
        """Línea 40: saldo < 0 → ajustar a 0"""
        compra = make_compra(self.proveedor, monto_total=Decimal("10000.00"), saldo=Decimal("5000.00"))
        pago = make_pago_proveedor()

        # Pago mayor al saldo
        AplicacionPagosCompras.objects.create(
            monto_aplicado=Decimal("8000.00"),  # > saldo actual de 5000
            id_compra=compra,
            id_pago_proveedor=pago,
        )

        compra.refresh_from_db()
        # Saldo quedó negativo → ajustado a 0
        self.assertEqual(compra.saldo_pendiente, Decimal("0.00"))
        self.assertEqual(compra.estado_pago, "Pagada")

    def test_pago_parcial_actualiza_estado_parcial(self):
        """Línea 48: saldo > 0 y < monto_total → estado='Parcial'"""
        compra = make_compra(self.proveedor, monto_total=Decimal("100000.00"))
        pago = make_pago_proveedor()

        # Pago parcial
        AplicacionPagosCompras.objects.create(
            monto_aplicado=Decimal("40000.00"),
            id_compra=compra,
            id_pago_proveedor=pago,
        )

        compra.refresh_from_db()
        self.assertEqual(compra.saldo_pendiente, Decimal("60000.00"))
        self.assertEqual(compra.estado_pago, "Parcial")

    def test_pago_completo_actualiza_estado_pagada(self):
        """Pago total → estado='Pagada'"""
        compra = make_compra(self.proveedor, monto_total=Decimal("50000.00"))
        pago = make_pago_proveedor()

        AplicacionPagosCompras.objects.create(
            monto_aplicado=Decimal("50000.00"),
            id_compra=compra,
            id_pago_proveedor=pago,
        )

        compra.refresh_from_db()
        self.assertEqual(compra.saldo_pendiente, Decimal("0.00"))
        self.assertEqual(compra.estado_pago, "Pagada")


# =============================================================================
# aplicar_nota_credito_proveedor signal - líneas 69, 79, 83
# =============================================================================


class AplicarNotaCreditoSignalTest(TransactionTestCase):
    """Tests para signal aplicar_nota_credito_proveedor"""

    def setUp(self):
        self.proveedor = make_proveedor()

    def test_nota_no_aplicada_no_modifica_compra(self):
        """Línea 69 (primera parte): nota con estado != 'Aplicada' → return"""
        compra = make_compra(self.proveedor, monto_total=Decimal("80000.00"))
        saldo_original = compra.saldo_pendiente

        # Crear nota con estado Pendiente (no Aplicada)
        NotasCreditoProveedor.objects.create(
            fecha=timezone.now(),
            fecha_creacion=timezone.now(),
            monto_total=Decimal("10000.00"),
            estado="Pendiente",
            id_compra_original=compra,
            id_proveedor=self.proveedor,
        )

        compra.refresh_from_db()
        # No se modificó el saldo
        self.assertEqual(compra.saldo_pendiente, saldo_original)

    def test_nota_aplicada_sin_compra_original_no_actua(self):
        """Línea 69 (segunda parte): nota Aplicada pero sin id_compra_original → return"""
        compra = make_compra(self.proveedor, monto_total=Decimal("80000.00"))
        saldo_original = compra.saldo_pendiente

        # Nota aplicada pero sin compra original
        NotasCreditoProveedor.objects.create(
            fecha=timezone.now(),
            fecha_creacion=timezone.now(),
            monto_total=Decimal("10000.00"),
            estado="Aplicada",
            id_compra_original=None,  # sin compra → sale
            id_proveedor=self.proveedor,
        )

        compra.refresh_from_db()
        # No se modificó el saldo
        self.assertEqual(compra.saldo_pendiente, saldo_original)

    def test_nota_supera_saldo_ajusta_a_cero(self):
        """Línea 79: nota > saldo → ajusta saldo a 0"""
        compra = make_compra(self.proveedor, monto_total=Decimal("10000.00"), saldo=Decimal("5000.00"))

        # Nota mayor al saldo
        NotasCreditoProveedor.objects.create(
            fecha=timezone.now(),
            fecha_creacion=timezone.now(),
            monto_total=Decimal("8000.00"),  # > saldo de 5000
            estado="Aplicada",
            id_compra_original=compra,
            id_proveedor=self.proveedor,
        )

        compra.refresh_from_db()
        self.assertEqual(compra.saldo_pendiente, Decimal("0.00"))
        self.assertEqual(compra.estado_pago, "Pagada")

    def test_nota_parcial_actualiza_estado_parcial(self):
        """Línea 83: nota < saldo → estado='Parcial'"""
        compra = make_compra(self.proveedor, monto_total=Decimal("100000.00"))

        NotasCreditoProveedor.objects.create(
            fecha=timezone.now(),
            fecha_creacion=timezone.now(),
            monto_total=Decimal("30000.00"),  # parcial
            estado="Aplicada",
            id_compra_original=compra,
            id_proveedor=self.proveedor,
        )

        compra.refresh_from_db()
        self.assertEqual(compra.saldo_pendiente, Decimal("70000.00"))
        self.assertEqual(compra.estado_pago, "Parcial")

    def test_nota_exacta_actualiza_estado_pagada(self):
        """Nota igual al saldo → estado='Pagada'"""
        compra = make_compra(self.proveedor, monto_total=Decimal("50000.00"))

        NotasCreditoProveedor.objects.create(
            fecha=timezone.now(),
            fecha_creacion=timezone.now(),
            monto_total=Decimal("50000.00"),
            estado="Aplicada",
            id_compra_original=compra,
            id_proveedor=self.proveedor,
        )

        compra.refresh_from_db()
        self.assertEqual(compra.saldo_pendiente, Decimal("0.00"))
        self.assertEqual(compra.estado_pago, "Pagada")

    def test_nota_deja_saldo_igual_monto_total(self):
        """Branch 84->87: nota deja saldo >= monto_total (elif falla, no cambia estado)"""
        # Create compra with saldo_pendiente = monto_total (full pending)
        compra = make_compra(self.proveedor, monto_total=Decimal("100000.00"), saldo=Decimal("100000.00"))

        # Apply nota of 0 to keep saldo = monto_total
        NotasCreditoProveedor.objects.create(
            fecha=timezone.now(),
            fecha_creacion=timezone.now(),
            monto_total=Decimal("0.00"),  # no reduction
            estado="Aplicada",
            id_compra_original=compra,
            id_proveedor=self.proveedor,
        )

        compra.refresh_from_db()
        # saldo = 100000 - 0 = 100000 (== monto_total)
        # Neither if (saldo == 0) nor elif (saldo < monto_total) execute
        self.assertEqual(compra.saldo_pendiente, Decimal("100000.00"))
        # estado_pago remains unchanged (no if/elif match)
        self.assertIn(compra.estado_pago, ["Pendiente", "Parcial"])
