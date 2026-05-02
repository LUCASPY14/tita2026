"""
Tests targeting missing __str__ methods in apps/compras/models.py.

Missing lines:
  73  — DetallesCompra.__str__
  93  — PagosProveedores.__str__
  113 — AplicacionPagosCompras.__str__
  138 — NotasCreditoProveedor.__str__
  162 — DetallesNotaCreditoProveedor.__str__
"""

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.compras.models import (
    AplicacionPagosCompras,
    Compras,
    DetallesCompra,
    DetallesNotaCreditoProveedor,
    NotasCreditoProveedor,
    PagosProveedores,
    Proveedores,
)


def _make_compras_fixtures():
    """Create base objects needed to build compras model instances."""
    from apps.contabilidad.models import Impuestos
    from apps.core.models import MediosPago
    from apps.productos.models import Categorias, Productos, UnidadesMedida

    proveedor, _ = Proveedores.objects.get_or_create(
        ruc="CM9999999-0",
        defaults={
            "razon_social": "CM Proveedor Test",
            "estado": True,
            "fecha_registro": timezone.now(),
        },
    )
    medio_pago, _ = MediosPago.objects.get_or_create(
        descripcion="CM_Efectivo",
        defaults={"genera_comision": False, "requiere_validacion": False, "estado": True},
    )
    impuesto = Impuestos.objects.create(
        nombre_impuesto=f"IVA_CM_{timezone.now().timestamp()}",
        porcentaje=Decimal("10.00"),
        vigente_desde=timezone.now().date(),
        estado=True,
    )
    categoria, _ = Categorias.objects.get_or_create(nombre="CM_Cat", defaults={"estado": True})
    unidad, _ = Categorias.objects.get_or_create(nombre="CM_UN_Cat", defaults={"estado": True})
    from apps.productos.models import UnidadesMedida

    unidad_medida, _ = UnidadesMedida.objects.get_or_create(
        nombre="CM_UN", defaults={"abreviatura": "UN", "estado": True}
    )
    producto = Productos.objects.create(
        descripcion=f"CM_Prod_{timezone.now().timestamp()}",
        estado=True,
        id_categoria=categoria,
        id_impuesto=impuesto,
        id_unidad_medida=unidad_medida,
    )
    return dict(
        proveedor=proveedor,
        medio_pago=medio_pago,
        producto=producto,
    )


def _make_compra(proveedor):
    """Create a Compras instance with 'pendiente' state (avoids stock signal processing)."""
    return Compras.objects.create(
        fecha=timezone.now(),
        monto_total=Decimal("10000"),
        saldo_pendiente=Decimal("10000"),
        estado_pago="pendiente",
        id_proveedor=proveedor,
    )


class DetallesCompraStrTest(TestCase):
    """Line 73: DetallesCompra.__str__."""

    def test_str_method(self):
        f = _make_compras_fixtures()
        compra = _make_compra(f["proveedor"])
        detalle = DetallesCompra.objects.create(
            id_compra=compra,
            id_producto=f["producto"],
            costo_unitario=Decimal("1000"),
            cantidad=Decimal("5"),
            subtotal=Decimal("5000"),
        )
        result = str(detalle)
        self.assertIn("DetallesCompra", result)
        self.assertIn(str(detalle.pk), result)


class PagosProveedoresStrTest(TestCase):
    """Line 93: PagosProveedores.__str__."""

    def test_str_method(self):
        f = _make_compras_fixtures()
        pago = PagosProveedores.objects.create(
            fecha_creacion=timezone.now(),
            id_medio_pago=f["medio_pago"],
        )
        result = str(pago)
        self.assertIn("PagosProveedores", result)
        self.assertIn(str(pago.pk), result)


class AplicacionPagosComprasStrTest(TestCase):
    """Line 113: AplicacionPagosCompras.__str__."""

    def test_str_method(self):
        f = _make_compras_fixtures()
        compra = _make_compra(f["proveedor"])
        pago = PagosProveedores.objects.create(
            fecha_creacion=timezone.now(),
            id_medio_pago=f["medio_pago"],
        )
        aplicacion = AplicacionPagosCompras.objects.create(
            monto_aplicado=Decimal("5000"),
            id_compra=compra,
            id_pago_proveedor=pago,
        )
        result = str(aplicacion)
        self.assertIn("AplicacionPagosCompras", result)
        self.assertIn(str(aplicacion.pk), result)


class NotasCreditoProveedorStrTest(TestCase):
    """Line 138: NotasCreditoProveedor.__str__."""

    def test_str_method(self):
        f = _make_compras_fixtures()
        nota = NotasCreditoProveedor.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("2000"),
            estado="Emitida",
            fecha_creacion=timezone.now(),
            id_proveedor=f["proveedor"],
        )
        result = str(nota)
        self.assertIn("NotasCreditoProveedor", result)
        self.assertIn(str(nota.pk), result)


class DetallesNotaCreditoProveedorStrTest(TestCase):
    """Line 162: DetallesNotaCreditoProveedor.__str__."""

    def test_str_method(self):
        f = _make_compras_fixtures()
        nota = NotasCreditoProveedor.objects.create(
            fecha=timezone.now(),
            monto_total=Decimal("2000"),
            estado="Emitida",
            fecha_creacion=timezone.now(),
            id_proveedor=f["proveedor"],
        )
        detalle = DetallesNotaCreditoProveedor.objects.create(
            cantidad=Decimal("1"),
            precio_unitario=Decimal("2000"),
            subtotal=Decimal("2000"),
            id_nota_proveedor=nota,
            id_producto=f["producto"],
        )
        result = str(detalle)
        self.assertIn("DetallesNotaCreditoProveedor", result)
        self.assertIn(str(detalle.pk), result)
