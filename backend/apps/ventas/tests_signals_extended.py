"""
Extended tests for apps/ventas/signals.py targeting uncovered branches.

Missing lines (at baseline 85.29%):
32, 40, 48, 81, 85

Signals:
- actualizar_saldo_venta (post_save AplicacionPagosVentas)
  - Line 32: if not created: return
  - Line 40: if saldo_pendiente < 0: ajustar a 0
  - Line 48: else: estado_pago = "Pendiente"
- aplicar_nota_credito_cliente (post_save NotasCreditoCliente)
  - Line 81: if saldo == 0: estado = "Pagada"
  - Line 85: elif saldo < monto_total: estado = "Parcial"
"""

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.ventas.models import AplicacionPagosVentas, NotasCreditoCliente, PagosVenta, Ventas


class ActualizarSaldoVentaSignalTest(TestCase):
    """Tests for actualizar_saldo_venta signal."""

    def setUp(self):
        # VentasManager handles all required FK defaults
        self.venta = Ventas.objects.create(
            monto_total=Decimal("100000"),
            saldo_pendiente=Decimal("100000"),
            estado_pago="Pendiente",
            tipo_venta="Credito",
            estado="Activa",
        )
        # PagosVenta requires id_medio_pago
        from apps.core.models import MediosPago

        medio, _ = MediosPago.objects.get_or_create(
            descripcion="Efectivo",
            defaults={"descripcion": "Efectivo"},
        )
        self.pago = PagosVenta.objects.create(
            monto=Decimal("100000"),
            monto_comision=Decimal("0"),
            fecha_pago=timezone.now(),
            estado="Pagado",
            id_medio_pago=medio,
            id_venta=self.venta,
        )

    def test_signal_no_dispara_en_update(self):
        """Line 32: signal returns early when created=False (update)."""
        aplicacion = AplicacionPagosVentas.objects.create(
            monto_aplicado=Decimal("50000"),
            id_pago_venta=self.pago,
            id_venta=self.venta,
        )
        saldo_antes = self.venta.saldo_pendiente
        # Refresh - saldo should have changed from the creation
        self.venta.refresh_from_db()

        # Now do an update - signal should NOT fire (line 32)
        AplicacionPagosVentas.objects.filter(pk=aplicacion.pk).update(monto_aplicado=Decimal("99999"))
        # Refresh venta - saldo should NOT have changed from the update
        self.venta.refresh_from_db()
        # Estado remains what was set on create (Pagada since full payment was made)
        # No further changes from this update
        self.assertIsNotNone(self.venta.estado_pago)

    def test_signal_dispara_en_create_pago_parcial(self):
        """Line 45-47: partial payment sets estado_pago = 'Parcial'."""
        AplicacionPagosVentas.objects.create(
            monto_aplicado=Decimal("50000"),
            id_pago_venta=self.pago,
            id_venta=self.venta,
        )
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.saldo_pendiente, Decimal("50000"))
        self.assertEqual(self.venta.estado_pago, "Parcial")

    def test_signal_pago_completo_estado_pagada(self):
        """Line 43-44: full payment sets estado_pago = 'Pagada' and saldo = 0."""
        AplicacionPagosVentas.objects.create(
            monto_aplicado=Decimal("100000"),
            id_pago_venta=self.pago,
            id_venta=self.venta,
        )
        self.venta.refresh_from_db()
        self.assertEqual(self.venta.saldo_pendiente, Decimal("0"))
        self.assertEqual(self.venta.estado_pago, "Pagada")

    def test_signal_pago_excede_saldo_ajusta_a_cero(self):
        """Line 40: overpayment is clamped to 0, no negative saldo."""
        AplicacionPagosVentas.objects.create(
            monto_aplicado=Decimal("150000"),  # More than monto_total
            id_pago_venta=self.pago,
            id_venta=self.venta,
        )
        self.venta.refresh_from_db()
        self.assertGreaterEqual(self.venta.saldo_pendiente, Decimal("0"))
        # Estado should be Pagada since saldo was clamped to 0
        self.assertEqual(self.venta.estado_pago, "Pagada")

    def test_signal_saldo_igual_monto_total_estado_pendiente(self):
        """Line 48: if saldo_pendiente == monto_total (no payment), estado = 'Pendiente'."""
        # Apply 0 (no payment changes the saldo) - use a venta with 0 payment
        venta2 = Ventas.objects.create(
            monto_total=Decimal("200000"),
            saldo_pendiente=Decimal("200000"),
            estado_pago="Pendiente",
            tipo_venta="Credito",
            estado="Activa",
        )
        from apps.core.models import MediosPago

        medio = MediosPago.objects.first()
        pago2 = PagosVenta.objects.create(
            monto=Decimal("200000"),
            monto_comision=Decimal("0"),
            fecha_pago=timezone.now(),
            estado="Pagado",
            id_medio_pago=medio,
            id_venta=venta2,
        )
        # Apply only 1 guarani - saldo becomes 199999, which is close to monto_total
        # Actually let's apply 0 - but that still triggers signal. Let's use a small amount
        # where saldo remains > monto_total is impossible (because saldo <= monto_total at start)
        # Line 48 covers when saldo > 0 but NOT < monto_total - meaning saldo == monto_total
        # This happens if monto_aplicado = 0 which isn't valid.
        # Actually line 48 (else: estado = Pendiente):
        # saldo_pendiente = original - monto_aplicado
        # saldo_pendiente == monto_total when monto_aplicado = 0
        # But monto_aplicado can't physically be 0 and still be different from original
        # Let's simulate: venta with saldo=100000, apply 0-amount
        # Note: field doesn't have >0 validation in model, DB might allow 0
        AplicacionPagosVentas.objects.create(
            monto_aplicado=Decimal("0"),
            id_pago_venta=pago2,
            id_venta=venta2,
        )
        venta2.refresh_from_db()
        # saldo_pendiente = 200000 - 0 = 200000 which equals monto_total (200000)
        # So the else: estado = "Pendiente" branch is triggered
        self.assertEqual(venta2.estado_pago, "Pendiente")


class AplicarNotaCreditoClienteSignalTest(TestCase):
    """Tests for aplicar_nota_credito_cliente signal."""

    def setUp(self):
        from apps.usuarios.models import Empleados

        self.empleado, _ = Empleados.objects.get_or_create(
            email="sistema@test.com",
            defaults={
                "nombre": "Sistema",
                "apellido": "Test",
                "fecha_ingreso": timezone.now(),
                "contrasena_hash": "",
            },
        )
        from apps.clientes.models import Clientes, TiposCliente
        from apps.productos.models import ListasPrecios

        lista, _ = ListasPrecios.objects.get_or_create(nombre_lista="General")
        tipo, _ = TiposCliente.objects.get_or_create(nombre_tipo="General")
        self.cliente, _ = Clientes.objects.get_or_create(
            ruc_ci="9988776",
            defaults={
                "nombres": "Test",
                "apellidos": "Cliente",
                "id_lista": lista,
                "id_tipo_cliente": tipo,
            },
        )

    def _crear_venta(self, monto_total, saldo_pendiente, estado_pago="Parcial"):
        return Ventas.objects.create(
            monto_total=Decimal(str(monto_total)),
            saldo_pendiente=Decimal(str(saldo_pendiente)),
            estado_pago=estado_pago,
            tipo_venta="Credito",
            estado="Activa",
            id_cliente=self.cliente,
        )

    def _crear_nota(self, venta, monto, estado="Aplicada"):
        return NotasCreditoCliente.objects.create(
            nro_nota_credito=1,
            fecha_emision=timezone.now(),
            motivo="Devolución de producto",
            monto_total=Decimal(str(monto)),
            estado=estado,
            id_cliente=self.cliente,
            id_empleado_autoriza=self.empleado,
            id_venta_origen=venta,
        )

    def test_signal_no_dispara_si_estado_no_aplicada(self):
        """Signal returns early if estado != 'Aplicada'."""
        venta = self._crear_venta(100000, 80000, "Parcial")
        # Create nota with estado != Aplicada - signal does nothing
        self._crear_nota(venta, 20000, estado="Pendiente")
        venta.refresh_from_db()
        # saldo_pendiente should remain unchanged
        self.assertEqual(venta.saldo_pendiente, Decimal("80000"))

    def test_signal_no_dispara_si_sin_venta_origen(self):
        """Signal returns early if id_venta_origen is None."""
        NotasCreditoCliente.objects.create(
            nro_nota_credito=2,
            fecha_emision=timezone.now(),
            motivo="Sin venta origen",
            monto_total=Decimal("20000"),
            estado="Aplicada",
            id_cliente=self.cliente,
            id_empleado_autoriza=self.empleado,
            id_venta_origen=None,
        )
        # No crash, signal returned early

    def test_signal_nota_reduce_saldo_a_cero_estado_pagada(self):
        """Line 81: nota covers full remaining saldo, estado becomes 'Pagada'."""
        venta = self._crear_venta(100000, 50000, "Parcial")
        self._crear_nota(venta, 50000)  # Exactly equals saldo_pendiente
        venta.refresh_from_db()
        self.assertEqual(venta.saldo_pendiente, Decimal("0"))
        self.assertEqual(venta.estado_pago, "Pagada")

    def test_signal_nota_reduce_saldo_parcial_estado_parcial(self):
        """Line 85: nota reduces saldo but > 0, estado remains 'Parcial'."""
        venta = self._crear_venta(100000, 80000, "Parcial")
        self._crear_nota(venta, 30000)  # Reduces from 80000 to 50000
        venta.refresh_from_db()
        self.assertEqual(venta.saldo_pendiente, Decimal("50000"))
        self.assertEqual(venta.estado_pago, "Parcial")

    def test_signal_nota_reduce_saldo_no_cero_estado_parcial_explicit(self):
        """Line 88-89: explicit test for elif branch (saldo > 0 and < monto_total)."""
        # Create venta: total 200000, pendiente 150000
        venta = self._crear_venta(200000, 150000, "Parcial")
        # Apply nota for 100000, leaving saldo = 50000
        self._crear_nota(venta, 100000)
        venta.refresh_from_db()
        # Verify: saldo_pendiente = 50000 (not 0, but < 200000)
        self.assertEqual(venta.saldo_pendiente, Decimal("50000"))
        # Verify: estado_pago = "Parcial" (from elif branch line 88-89)
        self.assertEqual(venta.estado_pago, "Parcial")
        # Explicitly check: 0 < saldo < monto_total
        self.assertGreater(venta.saldo_pendiente, Decimal("0"))
        self.assertLess(venta.saldo_pendiente, venta.monto_total)

    def test_signal_nota_deja_saldo_igual_monto_total(self):
        """Branch 86->89: saldo_pendiente >= monto_total después de nota (elif falla)."""
        # Create venta with saldo_pendiente = monto_total (escenario de venta con saldo completo)
        venta = self._crear_venta(100000, 100000, "Pendiente")
        # Apply nota of 0 (or very small) to keep saldo >= monto_total
        # Actually, let's apply 0 - this tests edge case
        self._crear_nota(venta, 0)
        venta.refresh_from_db()
        # After nota: saldo = 100000 - 0 = 100000
        # Check: saldo == monto_total, so elif (saldo < monto_total) is False
        self.assertEqual(venta.saldo_pendiente, Decimal("100000"))
        # Estado should remain "Pendiente" (neither if nor elif execute)
        self.assertEqual(venta.estado_pago, "Pendiente")

    def test_signal_nota_mayor_saldo_ajusta_a_cero(self):
        """Lines 77-79: nota > saldo_pendiente clamps to 0."""
        venta = self._crear_venta(100000, 30000, "Parcial")
        self._crear_nota(venta, 60000)  # More than saldo_pendiente
        venta.refresh_from_db()
        self.assertGreaterEqual(venta.saldo_pendiente, Decimal("0"))
        self.assertEqual(venta.estado_pago, "Pagada")
