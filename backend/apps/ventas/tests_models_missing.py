"""
Tests targeting remaining missing lines in apps/ventas/models.py

Missing lines:
  16, 18   — VentasManager.create: total_venta → monto_total mapping branches
  63, 66, 69 — VentasManager.create: defaults for tipo_venta, estado, monto_total
  168      — Ventas.total_venta property
  183-186  — DetallesVentaManager.create inner block (no subtotal provided)
  203      — DetallesVenta.__str__
  250      — PagosVenta.porcentaje_comision_aplicado early return (monto == 0)
  253      — PagosVenta.__str__
  269      — (another property/str line in PagosVenta section)
  296      — AplicacionPagosVentas.__str__
  318      — NotasCreditoCliente.__str__
  354      — DetallesNotaCredito.__str__
  373      — Promociones.__str__
  393      — CategoriasPromocion.__str__
  413      — ProductosPromocion.__str__
"""
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.ventas.models import (
    AplicacionPagosVentas,
    CategoriasPromocion,
    DetallesNotaCredito,
    DetallesVenta,
    NotasCreditoCliente,
    PagosVenta,
    ProductosPromocion,
    Promociones,
    PromocionesAplicadas,
    Ventas,
)


def _make_base_fixtures():
    """Create and return all fixtures needed across tests.

    Returns a dict with: lista, tipo_cliente, cliente, rol, empleado,
    medio_pago, impuesto, categoria, producto.
    """
    from apps.clientes.models import Clientes, TiposCliente
    from apps.contabilidad.models import Impuestos
    from apps.core.models import MediosPago
    from apps.productos.models import Categorias, Productos, UnidadesMedida
    from apps.productos.models import ListasPrecios
    from apps.usuarios.models import Empleados, Roles

    lista, _ = ListasPrecios.objects.get_or_create(
        nombre_lista="General_vm",
        defaults={"moneda": "PYG", "estado": True},
    )
    tipo_cliente, _ = TiposCliente.objects.get_or_create(
        nombre_tipo="VM_Regular",
        defaults={"estado": True},
    )
    cliente, _ = Clientes.objects.get_or_create(
        ruc_ci="VM0000001",
        defaults={
            "nombres": "VM",
            "apellidos": "Test",
            "limite_credito": Decimal("0"),
            "estado": True,
            "id_lista": lista,
            "id_tipo_cliente": tipo_cliente,
        },
    )
    rol, _ = Roles.objects.get_or_create(
        nombre_rol="VM_Cajero", defaults={"estado": True}
    )
    empleado, _ = Empleados.objects.get_or_create(
        email="vm_cajero@test.com",
        defaults={
            "nombre": "VM",
            "apellido": "Cajero",
            "contrasena_hash": "",
            "fecha_ingreso": timezone.now(),
        },
    )
    medio_pago, _ = MediosPago.objects.get_or_create(
        descripcion="VM_Efectivo",
        defaults={"genera_comision": False, "requiere_validacion": False, "estado": True},
    )
    impuesto = Impuestos.objects.create(
        nombre_impuesto=f"IVA_VM_{timezone.now().timestamp()}",
        porcentaje=Decimal("10.00"),
        vigente_desde=timezone.now().date(),
        estado=True,
    )
    categoria, _ = Categorias.objects.get_or_create(
        nombre="VM_Cat", defaults={"estado": True}
    )
    unidad, _ = UnidadesMedida.objects.get_or_create(
        nombre="VM_UN", defaults={"abreviatura": "UN", "estado": True}
    )
    producto = Productos.objects.create(
        descripcion=f"VM_Prod_{timezone.now().timestamp()}",
        estado=True,
        id_categoria=categoria,
        id_impuesto=impuesto,
        id_unidad_medida=unidad,
    )
    return dict(
        lista=lista,
        tipo_cliente=tipo_cliente,
        cliente=cliente,
        rol=rol,
        empleado=empleado,
        medio_pago=medio_pago,
        impuesto=impuesto,
        categoria=categoria,
        producto=producto,
    )


class VentasManagerTotalVentaBranchesTest(TestCase):
    """Lines 16, 18: VentasManager.create handles ``total_venta`` kwarg."""

    def setUp(self):
        f = _make_base_fixtures()
        self.cliente = f["cliente"]
        self.empleado = f["empleado"]
        self.medio_pago = f["medio_pago"]

    def _base_kwargs(self):
        return dict(
            estado_pago="pagada",
            tipo_venta="contado",
            estado="Activa",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )

    def test_total_venta_mapped_to_monto_total_when_absent(self):
        """Line 16: total_venta passed without monto_total → assigned to monto_total."""
        kwargs = self._base_kwargs()
        kwargs["total_venta"] = Decimal("50000")
        # monto_total NOT in kwargs → enters line 16 branch
        venta = Ventas.objects.create(**kwargs)
        self.assertEqual(venta.monto_total, Decimal("50000"))

    def test_total_venta_dropped_when_monto_total_present(self):
        """Line 18: when both total_venta and monto_total given, total_venta is popped."""
        kwargs = self._base_kwargs()
        kwargs["total_venta"] = Decimal("99999")
        kwargs["monto_total"] = Decimal("20000")
        # monto_total IS in kwargs → enters line 18 elif branch (total_venta is discarded)
        venta = Ventas.objects.create(**kwargs)
        self.assertEqual(venta.monto_total, Decimal("20000"))


class VentasManagerDefaultsTest(TestCase):
    """Lines 63, 66, 69: VentasManager provides defaults when keys are absent."""

    def setUp(self):
        f = _make_base_fixtures()
        self.cliente = f["cliente"]
        self.empleado = f["empleado"]
        self.medio_pago = f["medio_pago"]

    def _minimal_kwargs(self):
        """Kwargs without tipo_venta, estado, or monto_total."""
        return dict(
            estado_pago="pagada",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=self.medio_pago,
        )

    def test_tipo_venta_default_contado(self):
        """Line 63: tipo_venta defaults to 'contado'."""
        venta = Ventas.objects.create(**self._minimal_kwargs())
        self.assertEqual(venta.tipo_venta, "contado")

    def test_estado_default_activa(self):
        """Line 66: estado defaults to 'Activa'."""
        venta = Ventas.objects.create(**self._minimal_kwargs())
        self.assertEqual(venta.estado, "Activa")

    def test_monto_total_default_zero(self):
        """Line 69: monto_total defaults to 0."""
        venta = Ventas.objects.create(**self._minimal_kwargs())
        self.assertEqual(venta.monto_total, 0)


class VentasTotalVentaPropertyTest(TestCase):
    """Line 168: Ventas.total_venta is an alias for monto_total."""

    def setUp(self):
        f = _make_base_fixtures()
        self.venta = Ventas.objects.create(
            monto_total=Decimal("75000"),
            estado_pago="pagada",
            tipo_venta="contado",
            estado="Activa",
            id_cliente=f["cliente"],
            id_empleado_cajero=f["empleado"],
            id_medio_pago=f["medio_pago"],
        )

    def test_total_venta_returns_monto_total(self):
        """Line 168: accessing .total_venta triggers the property's return."""
        self.assertEqual(self.venta.total_venta, Decimal("75000"))


class VentasManagerIdClienteDefaultTest(TestCase):
    """Lines 30-43: VentasManager provides a default id_cliente when absent."""

    def test_create_without_id_cliente_uses_default(self):
        """Lines 30-43: get-or-create generic client when id_cliente not given."""
        venta = Ventas.objects.create(
            # Omit id_cliente and id_cliente_id entirely
            estado_pago="pagada",
            tipo_venta="contado",
            estado="Activa",
            monto_total=Decimal("1000"),
        )
        # The manager should have filled in the generic client (ruc_ci='0000000')
        self.assertIsNotNone(venta.id_cliente)


class VentasManagerIdEmpleadoDefaultTest(TestCase):
    """Lines 46-57: VentasManager provides a default id_empleado_cajero when absent."""

    def setUp(self):
        # Ensure we have id_cliente so only empleado uses the default path
        from apps.clientes.models import Clientes, TiposCliente
        from apps.productos.models import ListasPrecios
        lista, _ = ListasPrecios.objects.get_or_create(
            nombre_lista="General", defaults={"moneda": "PYG", "estado": True}
        )
        tipo, _ = TiposCliente.objects.get_or_create(
            nombre_tipo="General", defaults={"estado": True}
        )
        self.cliente, _ = Clientes.objects.get_or_create(
            ruc_ci="0000000",
            defaults={
                "nombres": "Cliente",
                "apellidos": "Genérico",
                "limite_credito": Decimal("0"),
                "id_lista": lista,
                "id_tipo_cliente": tipo,
            },
        )

    def test_create_without_id_empleado_cajero_uses_default(self):
        """Lines 46-57: get-or-create generic cajero when id_empleado_cajero not given."""
        venta = Ventas.objects.create(
            id_cliente=self.cliente,
            # omit id_empleado_cajero and id_empleado_cajero_id
            estado_pago="pagada",
            tipo_venta="contado",
            estado="Activa",
            monto_total=Decimal("1000"),
        )
        self.assertIsNotNone(venta.id_empleado_cajero)


class VentasManagerEstadoPagoDefaultTest(TestCase):
    """Line 60: VentasManager provides estado_pago='pagada' when absent."""

    def setUp(self):
        f = _make_base_fixtures()
        self.cliente = f["cliente"]
        self.empleado = f["empleado"]
        self.medio_pago = f["medio_pago"]

    def test_create_without_estado_pago_uses_default(self):
        """Line 60: estado_pago defaults to 'pagada'."""
        venta = Ventas.objects.create(
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            # omit estado_pago
            tipo_venta="contado",
            estado="Activa",
            monto_total=Decimal("1000"),
        )
        self.assertEqual(venta.estado_pago, "pagada")


class DetallesVentaManagerAutoSubtotalTest(TestCase):
    """Lines 183-186: DetallesVentaManager computes subtotal when absent."""

    def setUp(self):
        f = _make_base_fixtures()
        self.producto = f["producto"]
        self.venta = Ventas.objects.create(
            monto_total=Decimal("10000"),
            estado_pago="pagada",
            tipo_venta="contado",
            estado="Activa",
            id_cliente=f["cliente"],
            id_empleado_cajero=f["empleado"],
            id_medio_pago=f["medio_pago"],
        )
        # Create stock so the inventario signal doesn't raise ValueError
        from apps.inventario.models import StockUnico
        StockUnico.objects.get_or_create(
            id_producto=self.producto,
            defaults={"cantidad": Decimal("100.000")},
        )

    def test_subtotal_computed_automatically(self):
        """Lines 183-186: when subtotal is absent, manager computes cantidad * precio."""
        detalle = DetallesVenta.objects.create(
            id_venta=self.venta,
            id_producto=self.producto,
            cantidad=Decimal("3"),
            precio_unitario=Decimal("1000"),
            # subtotal intentionally omitted → manager must compute it
        )
        self.assertEqual(detalle.subtotal, Decimal("3000"))

    def test_subtotal_provided_skips_auto_compute(self):
        """Branch 182->187: when subtotal IS provided, manager skips the auto-compute block."""
        detalle = DetallesVenta.objects.create(
            id_venta=self.venta,
            id_producto=self.producto,
            cantidad=Decimal("2"),
            precio_unitario=Decimal("500"),
            subtotal=Decimal("999"),  # explicit subtotal → branch 182->187
        )
        self.assertEqual(detalle.subtotal, Decimal("999"))

    def test_detalles_venta_str(self):
        """Line 203: DetallesVenta.__str__ is called."""
        detalle = DetallesVenta.objects.create(
            id_venta=self.venta,
            id_producto=self.producto,
            cantidad=Decimal("2"),
            precio_unitario=Decimal("500"),
        )
        result = str(detalle)
        self.assertIn("DetallesVenta", result)
        self.assertIn(str(detalle.pk), result)


class PagosVentaPropertiesAndStrTest(TestCase):
    """Lines 250, 253, 269: PagosVenta properties and __str__."""

    def setUp(self):
        f = _make_base_fixtures()
        self.venta = Ventas.objects.create(
            monto_total=Decimal("20000"),
            estado_pago="pagada",
            tipo_venta="contado",
            estado="Activa",
            id_cliente=f["cliente"],
            id_empleado_cajero=f["empleado"],
            id_medio_pago=f["medio_pago"],
        )
        self.medio_pago = f["medio_pago"]

    def _make_pago(self, monto, monto_comision=Decimal("0")):
        return PagosVenta.objects.create(
            id_venta=self.venta,
            id_medio_pago=self.medio_pago,
            monto=monto,
            monto_comision=monto_comision,
            fecha_pago=timezone.now(),
            estado="pagado",
        )

    def test_porcentaje_comision_zero_when_monto_is_zero(self):
        """Line 250: porcentaje_comision_aplicado returns 0 when monto == 0."""
        pago = self._make_pago(Decimal("0"), Decimal("0"))
        result = pago.porcentaje_comision_aplicado
        self.assertEqual(result, Decimal("0.00"))

    def test_total_cobrado_and_str(self):
        """Lines 253, 269: total_cobrado property and __str__ are called."""
        pago = self._make_pago(Decimal("10000"), Decimal("500"))
        # total_cobrado (line ~243) — also exercises __str__ which calls it
        self.assertEqual(pago.total_cobrado, Decimal("10500"))
        # __str__ (line 253 in coverage context)
        result = str(pago)
        self.assertIn("Pago #", result)
        self.assertIn("10,500", result)

    def test_porcentaje_comision_nonzero(self):
        """Lines 248-249: porcentaje_comision_aplicado when monto > 0."""
        pago = self._make_pago(Decimal("10000"), Decimal("1000"))
        result = pago.porcentaje_comision_aplicado
        self.assertEqual(result, Decimal("10"))


class AplicacionPagosVentasStrTest(TestCase):
    """Line 296: AplicacionPagosVentas.__str__."""

    def setUp(self):
        f = _make_base_fixtures()
        self.venta = Ventas.objects.create(
            monto_total=Decimal("5000"),
            estado_pago="pagada",
            tipo_venta="contado",
            estado="Activa",
            id_cliente=f["cliente"],
            id_empleado_cajero=f["empleado"],
            id_medio_pago=f["medio_pago"],
        )
        self.pago = PagosVenta.objects.create(
            id_venta=self.venta,
            id_medio_pago=f["medio_pago"],
            monto=Decimal("5000"),
            monto_comision=Decimal("0"),
            fecha_pago=timezone.now(),
            estado="pagado",
        )

    def test_str_method(self):
        """Line 296: __str__ returns class name and pk."""
        aplicacion = AplicacionPagosVentas.objects.create(
            id_pago_venta=self.pago,
            id_venta=self.venta,
            monto_aplicado=Decimal("5000"),
        )
        result = str(aplicacion)
        self.assertIn("AplicacionPagosVentas", result)
        self.assertIn(str(aplicacion.pk), result)


class NotasCreditoClienteStrTest(TestCase):
    """Line 318: NotasCreditoCliente.__str__."""

    def setUp(self):
        f = _make_base_fixtures()
        self.cliente = f["cliente"]
        self.empleado = f["empleado"]
        self.venta = Ventas.objects.create(
            monto_total=Decimal("10000"),
            estado_pago="pagada",
            tipo_venta="contado",
            estado="Activa",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=f["medio_pago"],
        )

    def test_str_method(self):
        """Line 318: __str__ returns class name and pk."""
        nota = NotasCreditoCliente.objects.create(
            nro_nota_credito=1001,
            fecha_emision=timezone.now(),
            motivo="Devolución de prueba",
            monto_total=Decimal("5000"),
            estado="pendiente",
            id_cliente=self.cliente,
            id_empleado_autoriza=self.empleado,
            id_venta_origen=self.venta,
        )
        result = str(nota)
        self.assertIn("NotasCreditoCliente", result)
        self.assertIn(str(nota.pk), result)


class DetallesNotaCreditoStrTest(TestCase):
    """Line 354: DetallesNotaCredito.__str__."""

    def setUp(self):
        f = _make_base_fixtures()
        self.producto = f["producto"]
        self.cliente = f["cliente"]
        self.empleado = f["empleado"]
        self.venta = Ventas.objects.create(
            monto_total=Decimal("10000"),
            estado_pago="pagada",
            tipo_venta="contado",
            estado="Activa",
            id_cliente=self.cliente,
            id_empleado_cajero=self.empleado,
            id_medio_pago=f["medio_pago"],
        )
        self.nota = NotasCreditoCliente.objects.create(
            nro_nota_credito=1002,
            fecha_emision=timezone.now(),
            motivo="Devolución",
            monto_total=Decimal("2000"),
            estado="pendiente",
            id_cliente=self.cliente,
            id_empleado_autoriza=self.empleado,
            id_venta_origen=self.venta,
        )

    def test_str_method(self):
        """Line 354: __str__ returns class name and pk."""
        detalle = DetallesNotaCredito.objects.create(
            id_nota=self.nota,
            id_producto=self.producto,
            cantidad=Decimal("1"),
            precio_unitario=Decimal("2000"),
            subtotal=Decimal("2000"),
        )
        result = str(detalle)
        self.assertIn("DetallesNotaCredito", result)
        self.assertIn(str(detalle.pk), result)


class PromocionesStrTest(TestCase):
    """Line 373: Promociones.__str__."""

    def test_str_method(self):
        """Line 373: __str__ returns class name and pk."""
        promo = Promociones.objects.create(
            nombre="VM Promo Test",
            tipo_promocion="porcentaje",
            valor_descuento=Decimal("10.00"),
            fecha_inicio=timezone.now().date(),
            aplica_a="todos",
            min_cantidad=1,
            monto_minimo=Decimal("0"),
            usos_actuales=0,
            prioridad=1,
            estado=True,
            fecha_creacion=timezone.now(),
        )
        result = str(promo)
        self.assertIn("Promociones", result)
        self.assertIn(str(promo.pk), result)


class _PromoFixtureMixin:
    """Shared fixture for CategoriasPromocion and ProductosPromocion tests."""

    def _make_promo(self):
        return Promociones.objects.create(
            nombre=f"PromoMixin_{timezone.now().timestamp()}",
            tipo_promocion="porcentaje",
            valor_descuento=Decimal("5.00"),
            fecha_inicio=timezone.now().date(),
            aplica_a="todos",
            min_cantidad=1,
            monto_minimo=Decimal("0"),
            usos_actuales=0,
            prioridad=1,
            estado=True,
            fecha_creacion=timezone.now(),
        )


class CategoriasPromocionStrTest(_PromoFixtureMixin, TestCase):
    """Line 393: CategoriasPromocion.__str__."""

    def test_str_method(self):
        """Line 393: __str__ returns class name and pk."""
        from apps.productos.models import Categorias

        cat, _ = Categorias.objects.get_or_create(
            nombre="VM_CatPromo", defaults={"estado": True}
        )
        promo = self._make_promo()
        cat_promo = CategoriasPromocion.objects.create(
            id_categoria=cat,
            id_promocion=promo,
        )
        result = str(cat_promo)
        self.assertIn("CategoriasPromocion", result)
        self.assertIn(str(cat_promo.pk), result)


class ProductosPromocionStrTest(_PromoFixtureMixin, TestCase):
    """Line 413: ProductosPromocion.__str__."""

    def test_str_method(self):
        """Line 413: __str__ returns class name and pk."""
        f = _make_base_fixtures()
        promo = self._make_promo()
        prod_promo = ProductosPromocion.objects.create(
            id_producto=f["producto"],
            id_promocion=promo,
        )
        result = str(prod_promo)
        self.assertIn("ProductosPromocion", result)
        self.assertIn(str(prod_promo.pk), result)


class PromocionesAplicadasStrTest(_PromoFixtureMixin, TestCase):
    """PromocionesAplicadas.__str__ — ensure it stays covered."""

    def test_str_method(self):
        f = _make_base_fixtures()
        venta = Ventas.objects.create(
            monto_total=Decimal("10000"),
            estado_pago="pagada",
            tipo_venta="contado",
            estado="Activa",
            id_cliente=f["cliente"],
            id_empleado_cajero=f["empleado"],
            id_medio_pago=f["medio_pago"],
        )
        promo = self._make_promo()
        aplicada = PromocionesAplicadas.objects.create(
            id_promocion=promo,
            id_venta=venta,
            monto_descontado=Decimal("500"),
            fecha_aplicacion=timezone.now(),
        )
        result = str(aplicada)
        self.assertIn("PromocionesAplicadas", result)
