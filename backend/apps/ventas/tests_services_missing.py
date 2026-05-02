"""
Tests targeting missing lines in apps/ventas/services.py.

Missing ranges:
  47-99   — PromocionService.obtener_promociones_aplicables
  189-210 — PromocionService.aplicar_promociones_a_venta
  410-558 — DevolucionService.crear_nota_credito
  580-615 — DevolucionService.anular_nota_credito
"""

from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.ventas.models import (
    DetallesNotaCredito,
    DetallesVenta,
    NotasCreditoCliente,
    Promociones,
    PromocionesAplicadas,
    Ventas,
)
from apps.ventas.services import DevolucionService, PromocionService

# ---------------------------------------------------------------------------
# Shared fixture helper (same pattern as tests_models_missing.py)
# ---------------------------------------------------------------------------


def _make_base_fixtures():
    """Create minimum DB objects needed across all tests."""
    from apps.clientes.models import Clientes, TiposCliente
    from apps.contabilidad.models import Impuestos
    from apps.core.models import MediosPago
    from apps.productos.models import Categorias, ListasPrecios, Productos, UnidadesMedida
    from apps.usuarios.models import Empleados, Roles

    lista, _ = ListasPrecios.objects.get_or_create(
        nombre_lista="SVC_General",
        defaults={"moneda": "PYG", "estado": True},
    )
    tipo_cliente, _ = TiposCliente.objects.get_or_create(nombre_tipo="SVC_Regular", defaults={"estado": True})
    cliente, _ = Clientes.objects.get_or_create(
        ruc_ci="SVC0000001",
        defaults={
            "nombres": "SVC",
            "apellidos": "Test",
            "limite_credito": Decimal("0"),
            "estado": True,
            "id_lista": lista,
            "id_tipo_cliente": tipo_cliente,
        },
    )
    Roles.objects.get_or_create(nombre_rol="SVC_Cajero", defaults={"estado": True})
    empleado, _ = Empleados.objects.get_or_create(
        email="svc_cajero@test.com",
        defaults={
            "nombre": "SVC",
            "apellido": "Cajero",
            "contrasena_hash": "",
            "fecha_ingreso": timezone.now(),
        },
    )
    medio_pago, _ = MediosPago.objects.get_or_create(
        descripcion="SVC_Efectivo",
        defaults={"genera_comision": False, "requiere_validacion": False, "estado": True},
    )
    impuesto = Impuestos.objects.create(
        nombre_impuesto=f"IVA_SVC_{timezone.now().timestamp()}",
        porcentaje=Decimal("10.00"),
        vigente_desde=timezone.now().date(),
        estado=True,
    )
    categoria, _ = Categorias.objects.get_or_create(nombre="SVC_Cat", defaults={"estado": True})
    unidad, _ = UnidadesMedida.objects.get_or_create(nombre="SVC_UN", defaults={"abreviatura": "UN", "estado": True})
    producto = Productos.objects.create(
        descripcion=f"SVC_Prod_{timezone.now().timestamp()}",
        estado=True,
        id_categoria=categoria,
        id_impuesto=impuesto,
        id_unidad_medida=unidad,
    )
    return dict(
        lista=lista,
        tipo_cliente=tipo_cliente,
        cliente=cliente,
        empleado=empleado,
        medio_pago=medio_pago,
        impuesto=impuesto,
        categoria=categoria,
        producto=producto,
    )


def _make_promo(**overrides):
    """Create a simple active Promocion with sensible defaults."""
    defaults = dict(
        nombre=f"Promo_{timezone.now().timestamp()}",
        tipo_promocion="porcentaje",
        valor_descuento=Decimal("10.00"),
        fecha_inicio=timezone.now().date(),
        fecha_fin=None,
        hora_inicio=None,
        hora_fin=None,
        dias_semana=None,
        aplica_a="total",
        min_cantidad=1,
        monto_minimo=Decimal("0.00"),
        max_usos_cliente=None,
        max_usos_total=None,
        usos_actuales=0,
        requiere_codigo=False,
        codigo_promocion=None,
        prioridad=1,
        estado=True,
        fecha_creacion=timezone.now(),
    )
    defaults.update(overrides)
    return Promociones.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Lines 47-99: PromocionService.obtener_promociones_aplicables
# ---------------------------------------------------------------------------


class ObtenerPromocionesAplicablesTest(TestCase):
    """Lines 47-99: PromocionService.obtener_promociones_aplicables."""

    def setUp(self):
        f = _make_base_fixtures()
        self.cliente = f["cliente"]
        self.empleado = f["empleado"]
        self.medio_pago = f["medio_pago"]
        self.producto = f["producto"]

        # Active promo without required code
        self.promo_sin_codigo = _make_promo(requiere_codigo=False, prioridad=1)

        # Active promo that requires a specific code
        self.promo_con_codigo = _make_promo(
            tipo_promocion="monto_fijo",
            valor_descuento=Decimal("5000.00"),
            requiere_codigo=True,
            codigo_promocion="TESTCODE99",
            prioridad=2,
        )

    def _items(self):
        return [{"id_producto": self.producto.pk, "cantidad": Decimal("1"), "precio": Decimal("10000")}]

    def test_fecha_hora_none_defaults_to_now(self):
        """Lines 47-48: fecha_hora=None triggers default."""
        result = PromocionService.obtener_promociones_aplicables(
            items=self._items(), monto_total=Decimal("10000"), fecha_hora=None
        )
        self.assertIsInstance(result, list)

    def test_promo_sin_codigo_aparece_sin_code(self):
        """Lines 62-64: promo without code appears when no code given."""
        result = PromocionService.obtener_promociones_aplicables(items=self._items(), monto_total=Decimal("10000"))
        ids = [r["promocion"].pk for r in result]
        self.assertIn(self.promo_sin_codigo.pk, ids)
        self.assertNotIn(self.promo_con_codigo.pk, ids)

    def test_promo_con_codigo_aparece_con_code(self):
        """Lines 55-58: code filter returns code-based promo."""
        result = PromocionService.obtener_promociones_aplicables(
            items=self._items(),
            monto_total=Decimal("10000"),
            codigo_promocion="TESTCODE99",
        )
        ids = [r["promocion"].pk for r in result]
        self.assertIn(self.promo_con_codigo.pk, ids)

    def test_monto_minimo_excluye_promo(self):
        """Line 71-72: promo with monto_minimo > monto_total excluded."""
        self.promo_sin_codigo.monto_minimo = Decimal("999999.00")
        self.promo_sin_codigo.save()
        result = PromocionService.obtener_promociones_aplicables(items=self._items(), monto_total=Decimal("10000"))
        ids = [r["promocion"].pk for r in result]
        self.assertNotIn(self.promo_sin_codigo.pk, ids)

    def test_max_usos_total_excluye_promo(self):
        """Lines 74-75: usos_actuales >= max_usos_total excluded."""
        self.promo_sin_codigo.max_usos_total = 1
        self.promo_sin_codigo.usos_actuales = 1
        self.promo_sin_codigo.save()
        result = PromocionService.obtener_promociones_aplicables(items=self._items(), monto_total=Decimal("10000"))
        ids = [r["promocion"].pk for r in result]
        self.assertNotIn(self.promo_sin_codigo.pk, ids)

    def test_max_usos_cliente_excluye_promo(self):
        """Lines 77-82: client has used max_usos_cliente times → excluded."""
        venta = Ventas.objects.create(
            monto_total=Decimal("10000"),
            estado_pago="pagada",
            tipo_venta="contado",
            estado="Activa",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )
        self.promo_sin_codigo.max_usos_cliente = 1
        self.promo_sin_codigo.save()
        PromocionesAplicadas.objects.create(
            monto_descontado=Decimal("1000"),
            fecha_aplicacion=timezone.now(),
            id_promocion=self.promo_sin_codigo,
            id_venta=venta,
        )
        result = PromocionService.obtener_promociones_aplicables(
            items=self._items(),
            monto_total=Decimal("10000"),
            cliente_id=self.cliente.pk,
        )
        ids = [r["promocion"].pk for r in result]
        self.assertNotIn(self.promo_sin_codigo.pk, ids)

    def test_resultado_ordenado_por_prioridad(self):
        """Line 97: results sorted by prioridad ascending."""
        _make_promo(requiere_codigo=False, prioridad=9)
        result = PromocionService.obtener_promociones_aplicables(items=self._items(), monto_total=Decimal("10000"))
        prios = [r["prioridad"] for r in result]
        self.assertEqual(prios, sorted(prios))

    def test_promo_dia_semana_invalido_excluida(self):
        """Lines 66-69: promo not valid today (wrong day) is excluded."""
        # isoweekday: 1=Mon...7=Sun. Set dias_semana to a day that is NOT today.
        today_dow = timezone.now().isoweekday()
        # Pick a day that is NOT today
        other_day = (today_dow % 7) + 1  # shifts by 1, wraps around 1-7
        promo_day = _make_promo(requiere_codigo=False, dias_semana=[other_day], prioridad=5)
        result = PromocionService.obtener_promociones_aplicables(items=self._items(), monto_total=Decimal("10000"))
        ids = [r["promocion"].pk for r in result]
        self.assertNotIn(promo_day.pk, ids)

    def test_con_fecha_hora_explicita(self):
        """Branch 49->53: fecha_hora provided (non-None) skips the default assignment."""
        import datetime as dt

        fecha_explicita = dt.datetime(2099, 6, 15, 12, 0, 0, tzinfo=dt.timezone.utc)
        promo_futuro = _make_promo(
            requiere_codigo=False,
            prioridad=1,
            fecha_inicio=dt.date(2099, 1, 1),
        )
        result = PromocionService.obtener_promociones_aplicables(
            items=self._items(),
            monto_total=Decimal("10000"),
            fecha_hora=fecha_explicita,
        )
        # promo_futuro has fecha_inicio 2099-01-01 <= 2099-06-15 → should appear
        ids = [r["promocion"].pk for r in result]
        self.assertIn(promo_futuro.pk, ids)

    def test_promo_horario_invalido_excluida(self):
        """Line 69: _validar_horario returns False → promo excluded via continue."""
        from datetime import time as dt_time

        # Create a promo with hora_inicio very far in the future (e.g., 23:59)
        # and hora_fin also at 23:59, so that current time is before it
        promo_horario = _make_promo(
            requiere_codigo=False,
            hora_inicio=dt_time(23, 58),
            hora_fin=dt_time(23, 59),
            prioridad=5,
        )
        # Call without specifying time; if current time < 23:58, promo is excluded
        import datetime as dt

        now = timezone.now()
        if now.hour < 23:
            result = PromocionService.obtener_promociones_aplicables(items=self._items(), monto_total=Decimal("10000"))
            ids = [r["promocion"].pk for r in result]
            self.assertNotIn(promo_horario.pk, ids)

    def test_cliente_no_excede_usos_max_promo_incluida(self):
        """Lines 89->93: client_id provided, max_usos_cliente set, but usage < limit → included."""
        venta = Ventas.objects.create(
            monto_total=Decimal("10000"),
            estado_pago="pagada",
            tipo_venta="contado",
            estado="Activa",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )
        self.promo_sin_codigo.max_usos_cliente = 5  # limit is 5
        self.promo_sin_codigo.save()
        # Client has used it 0 times → below limit → promo should be INCLUDED
        result = PromocionService.obtener_promociones_aplicables(
            items=self._items(),
            monto_total=Decimal("10000"),
            cliente_id=self.cliente.pk,
        )
        ids = [r["promocion"].pk for r in result]
        self.assertIn(self.promo_sin_codigo.pk, ids)

    def test_alcance_producto_no_coincidente_excluye_promo(self):
        """Line 94: aplica_a='producto' with no matching product → _validar_alcance False → continue."""
        # Create promo with aplica_a='producto' but NO ProductosPromocion records
        promo_prod = _make_promo(requiere_codigo=False, aplica_a="producto", prioridad=3)
        # No ProductosPromocion added → set is empty → intersection with items is empty → excluded
        result = PromocionService.obtener_promociones_aplicables(items=self._items(), monto_total=Decimal("10000"))
        ids = [r["promocion"].pk for r in result]
        self.assertNotIn(promo_prod.pk, ids)


# ---------------------------------------------------------------------------
# Lines 189-210: PromocionService.aplicar_promociones_a_venta
# ---------------------------------------------------------------------------


class AplicarPromocionesAVentaTest(TestCase):
    """Lines 189-210: PromocionService.aplicar_promociones_a_venta."""

    def setUp(self):
        f = _make_base_fixtures()
        self.cliente = f["cliente"]
        self.empleado = f["empleado"]
        self.medio_pago = f["medio_pago"]

        self.venta = Ventas.objects.create(
            monto_total=Decimal("50000"),
            estado_pago="pagada",
            tipo_venta="contado",
            estado="Activa",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )
        self.promo = _make_promo(usos_actuales=0)

    def test_crea_registro_y_incrementa_usos(self):
        """Lines 195-210: crear PromocionesAplicadas, increment usos, return dict."""
        descuento_info = {"monto_descuento": Decimal("5000.00")}
        result = PromocionService.aplicar_promociones_a_venta(
            venta=self.venta,
            promociones_seleccionadas=[(self.promo, descuento_info)],
            empleado=self.empleado,
        )
        self.assertEqual(result["monto_total_descuentos"], Decimal("5000.00"))
        self.assertEqual(len(result["promociones_aplicadas"]), 1)
        self.promo.refresh_from_db()
        self.assertEqual(self.promo.usos_actuales, 1)
        self.assertIn("1 promoción(es) aplicada(s)", result["detalle"])

    def test_multiples_promociones(self):
        """Lines 193-209: loop over multiple promos."""
        promo2 = _make_promo(prioridad=2)
        result = PromocionService.aplicar_promociones_a_venta(
            venta=self.venta,
            promociones_seleccionadas=[
                (self.promo, {"monto_descuento": Decimal("1000.00")}),
                (promo2, {"monto_descuento": Decimal("2000.00")}),
            ],
            empleado=self.empleado,
        )
        self.assertEqual(result["monto_total_descuentos"], Decimal("3000.00"))
        self.assertEqual(len(result["promociones_aplicadas"]), 2)


# ---------------------------------------------------------------------------
# Lines 410-558: DevolucionService.crear_nota_credito
# ---------------------------------------------------------------------------


class CrearNotaCreditoTest(TestCase):
    """Lines 410-558: DevolucionService.crear_nota_credito."""

    def setUp(self):
        from apps.inventario.models import StockUnico

        f = _make_base_fixtures()
        self.cliente = f["cliente"]
        self.empleado = f["empleado"]
        self.medio_pago = f["medio_pago"]
        self.producto = f["producto"]

        # Must create stock before DetallesVenta (inventario signal checks it)
        self.stock, _ = StockUnico.objects.get_or_create(
            id_producto=self.producto,
            defaults={"cantidad": Decimal("100.000")},
        )

        self.venta = Ventas.objects.create(
            monto_total=Decimal("10000"),
            estado_pago="pagada",
            tipo_venta="contado",
            estado="Activa",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )
        # Creating with explicit subtotal avoids auto-compute and satisfies the signal
        self.detalle = DetallesVenta.objects.create(
            id_venta=self.venta,
            id_producto=self.producto,
            cantidad=Decimal("5"),
            precio_unitario=Decimal("2000"),
            subtotal=Decimal("10000"),
        )

    def test_venta_no_encontrada_raises(self):
        """Lines 413-416: venta not found → DRFValidationError."""
        with self.assertRaises(DRFValidationError):
            DevolucionService.crear_nota_credito(
                id_venta=999999,
                productos_devolucion=[],
                motivo="test",
                empleado_autoriza=self.empleado,
            )

    def test_fuera_de_plazo_raises(self):
        """Lines 421-427: dias_transcurridos > DIAS_LIMITE → DRFValidationError."""
        old_fecha = timezone.now() - timedelta(days=8)
        Ventas.objects.filter(pk=self.venta.pk).update(fecha=old_fecha)
        with self.assertRaises(DRFValidationError):
            DevolucionService.crear_nota_credito(
                id_venta=self.venta.pk,
                productos_devolucion=[{"id_producto": self.producto.pk, "cantidad": 1}],
                motivo="test",
                empleado_autoriza=self.empleado,
            )

    def test_estado_invalido_raises(self):
        """Lines 429-432: venta.estado != 'Activa' → DRFValidationError."""
        Ventas.objects.filter(pk=self.venta.pk).update(estado="Anulada")
        with self.assertRaises(DRFValidationError):
            DevolucionService.crear_nota_credito(
                id_venta=self.venta.pk,
                productos_devolucion=[{"id_producto": self.producto.pk, "cantidad": 1}],
                motivo="test",
                empleado_autoriza=self.empleado,
            )

    def test_producto_no_en_venta_raises(self):
        """Lines 449-455: producto not in original venta → DRFValidationError."""
        with self.assertRaises(DRFValidationError):
            DevolucionService.crear_nota_credito(
                id_venta=self.venta.pk,
                productos_devolucion=[{"id_producto": 999999, "cantidad": 1}],
                motivo="test",
                empleado_autoriza=self.empleado,
            )

    def test_cantidad_excede_comprada_raises(self):
        """Lines 457-463: cantidad_devolucion > cantidad_comprada → DRFValidationError."""
        with self.assertRaises(DRFValidationError):
            DevolucionService.crear_nota_credito(
                id_venta=self.venta.pk,
                productos_devolucion=[{"id_producto": self.producto.pk, "cantidad": 999}],
                motivo="test",
                empleado_autoriza=self.empleado,
            )

    def test_success_contado_crea_nota(self):
        """Lines 466-558: success path creates NotasCreditoCliente and DetallesNotaCredito."""
        result = DevolucionService.crear_nota_credito(
            id_venta=self.venta.pk,
            productos_devolucion=[
                {
                    "id_producto": self.producto.pk,
                    "cantidad": 1,
                    "motivo_item": "defecto",
                }
            ],
            motivo="Devolución TEST",
            empleado_autoriza=self.empleado,
        )
        self.assertTrue(result["exito"])
        self.assertIsNotNone(result["nota_credito"])
        self.assertEqual(result["monto_devuelto"], Decimal("2000.00"))
        self.assertTrue(result["stock_actualizado"])
        self.assertIn("Nota de crédito #", result["mensaje"])

    def test_success_credito_actualiza_saldo(self):
        """Lines 549-556: tipo_venta='Crédito' → updates saldo_pendiente and estado_pago."""
        # Create a credit venta (stock already set up from setUp)
        venta_credito = Ventas.objects.create(
            monto_total=Decimal("2000"),
            estado_pago="pendiente",
            tipo_venta="Crédito",
            estado="Activa",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )
        DetallesVenta.objects.create(
            id_venta=venta_credito,
            id_producto=self.producto,
            cantidad=Decimal("1"),
            precio_unitario=Decimal("2000"),
            subtotal=Decimal("2000"),
        )
        result = DevolucionService.crear_nota_credito(
            id_venta=venta_credito.pk,
            productos_devolucion=[
                {
                    "id_producto": self.producto.pk,
                    "cantidad": 1,
                    "motivo_item": "",
                }
            ],
            motivo="Devolución credito",
            empleado_autoriza=self.empleado,
        )
        self.assertTrue(result["exito"])
        venta_credito.refresh_from_db()
        # saldo_pendiente was None → 0 - 2000 = -2000 ≤ 0 → estado_pago = "Pagada"
        self.assertEqual(venta_credito.estado_pago, "Pagada")

    def test_success_credito_saldo_positivo_no_cambia_estado(self):
        """Branch 553->556: saldo_pendiente remains > 0 → estado_pago not set to 'Pagada'."""
        # Create a credit venta with large saldo_pendiente
        venta_credito = Ventas.objects.create(
            monto_total=Decimal("100000"),
            estado_pago="pendiente",
            tipo_venta="Crédito",
            estado="Activa",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )
        Ventas.objects.filter(pk=venta_credito.pk).update(saldo_pendiente=Decimal("100000"))
        DetallesVenta.objects.create(
            id_venta=venta_credito,
            id_producto=self.producto,
            cantidad=Decimal("1"),
            precio_unitario=Decimal("2000"),
            subtotal=Decimal("2000"),
        )
        result = DevolucionService.crear_nota_credito(
            id_venta=venta_credito.pk,
            productos_devolucion=[
                {
                    "id_producto": self.producto.pk,
                    "cantidad": 1,
                    "motivo_item": "",
                }
            ],
            motivo="Devolución parcial credito",
            empleado_autoriza=self.empleado,
        )
        self.assertTrue(result["exito"])
        venta_credito.refresh_from_db()
        # 100000 - 2000 = 98000 > 0 → estado_pago stays "pendiente"
        self.assertNotEqual(venta_credito.estado_pago, "Pagada")


# ---------------------------------------------------------------------------
# Lines 580-615: DevolucionService.anular_nota_credito
# ---------------------------------------------------------------------------


class AnularNotaCreditoTest(TestCase):
    """Lines 580-615: DevolucionService.anular_nota_credito."""

    def setUp(self):
        from apps.inventario.models import StockUnico

        f = _make_base_fixtures()
        self.cliente = f["cliente"]
        self.empleado = f["empleado"]
        self.medio_pago = f["medio_pago"]
        self.producto = f["producto"]

        self.stock, _ = StockUnico.objects.get_or_create(
            id_producto=self.producto,
            defaults={"cantidad": Decimal("100.000")},
        )

        self.venta = Ventas.objects.create(
            monto_total=Decimal("10000"),
            estado_pago="pagada",
            tipo_venta="contado",
            estado="Activa",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )
        self.nota = NotasCreditoCliente.objects.create(
            nro_nota_credito=9901,
            fecha_emision=timezone.now(),
            motivo="Test anulacion",
            monto_total=Decimal("2000"),
            estado="Emitida",
            id_cliente=self.cliente,
            id_empleado_autoriza=self.empleado,
            id_venta_origen=self.venta,
        )
        self.detalle_nota = DetallesNotaCredito.objects.create(
            cantidad=Decimal("1"),
            precio_unitario=Decimal("2000"),
            subtotal=Decimal("2000"),
            id_nota=self.nota,
            id_producto=self.producto,
        )

    def test_nota_no_encontrada_raises(self):
        """Lines 585-586: nota not found → DRFValidationError."""
        with self.assertRaises(DRFValidationError):
            DevolucionService.anular_nota_credito(
                id_nota=999999,
                empleado_autoriza=self.empleado,
                motivo_anulacion="test",
            )

    def test_ya_anulada_raises(self):
        """Line 589: nota already Anulada → DRFValidationError."""
        self.nota.estado = "Anulada"
        self.nota.save()
        with self.assertRaises(DRFValidationError):
            DevolucionService.anular_nota_credito(
                id_nota=self.nota.pk,
                empleado_autoriza=self.empleado,
                motivo_anulacion="test",
            )

    def test_success_anula_nota_y_revierte_stock(self):
        """Lines 591-615: success anula nota and creates MovimientosStock."""
        result = DevolucionService.anular_nota_credito(
            id_nota=self.nota.pk,
            empleado_autoriza=self.empleado,
            motivo_anulacion="Error de registro",
        )
        self.assertTrue(result["exito"])
        self.assertIn(str(self.nota.nro_nota_credito), result["mensaje"])
        self.nota.refresh_from_db()
        self.assertEqual(self.nota.estado, "Anulada")
