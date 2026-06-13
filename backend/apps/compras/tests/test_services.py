"""Tests para apps.compras.services — CompraService."""
import pytest
from decimal import Decimal


@pytest.fixture
def proveedor(db):
    from apps.compras.models import Proveedor
    return Proveedor.objects.create(ruc="80001001-1", razon_social="Prov. Service Test")


@pytest.fixture
def producto_activo(db, categoria, unidad_medida):
    from apps.productos.models import Producto
    return Producto.objects.create(
        descripcion="Producto Compra",
        categoria=categoria,
        unidad_medida=unidad_medida,
        activo=True,
        requiere_stock=True,
        permite_stock_negativo=False,
    )


@pytest.fixture
def producto_inactivo(db, categoria, unidad_medida):
    from apps.productos.models import Producto
    return Producto.objects.create(
        descripcion="Inactivo",
        categoria=categoria,
        unidad_medida=unidad_medida,
        activo=False,
    )


def _item(producto, cantidad=10, costo=5000):
    return {"producto": producto, "cantidad": Decimal(str(cantidad)), "costo_unitario": Decimal(str(costo))}


# ── validar_items ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestValidarItems:
    def test_lista_vacia_retorna_error(self):
        from apps.compras.services import CompraService
        errores = CompraService.validar_items([])
        assert any("al menos" in e.get("error", "") for e in errores)

    def test_sin_producto_retorna_error(self):
        from apps.compras.services import CompraService
        errores = CompraService.validar_items([{"producto": None, "cantidad": 1, "costo_unitario": 1}])
        assert any("Producto no especificado" in e.get("error", "") for e in errores)

    def test_producto_inactivo_retorna_error(self, producto_inactivo):
        from apps.compras.services import CompraService
        errores = CompraService.validar_items([_item(producto_inactivo)])
        assert any("inactivo" in e.get("error", "") for e in errores)

    def test_cantidad_cero_retorna_error(self, producto_activo):
        from apps.compras.services import CompraService
        errores = CompraService.validar_items([_item(producto_activo, cantidad=0)])
        assert any("mayor a 0" in e.get("error", "") for e in errores)

    def test_costo_cero_retorna_error(self, producto_activo):
        from apps.compras.services import CompraService
        errores = CompraService.validar_items([_item(producto_activo, costo=0)])
        assert any("mayor a 0" in e.get("error", "") for e in errores)

    def test_producto_duplicado_retorna_error(self, producto_activo):
        from apps.compras.services import CompraService
        errores = CompraService.validar_items([
            _item(producto_activo),
            _item(producto_activo),
        ])
        assert any("duplicado" in e.get("error", "") for e in errores)

    def test_items_validos_sin_errores(self, producto_activo):
        from apps.compras.services import CompraService
        errores = CompraService.validar_items([_item(producto_activo)])
        assert errores == []


# ── registrar_compra ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRegistrarCompra:
    def test_contado_actualiza_stock_y_marca_pagado(self, proveedor, usuario_cajero, producto_activo):
        from apps.compras.services import CompraService
        from apps.compras.models import Compra
        from apps.inventario.models import Stock

        compra = CompraService.registrar_compra(
            proveedor=proveedor,
            creado_por=usuario_cajero,
            tipo_pago="CONTADO",
            items=[_item(producto_activo, cantidad=5, costo=10000)],
        )

        assert compra.tipo_pago == Compra.TipoPago.CONTADO
        assert compra.estado_pago == Compra.EstadoPago.PAGADO
        assert compra.estado_entrega == Compra.EstadoEntrega.RECIBIDA
        assert compra.monto_total == Decimal("50000")
        stock = Stock.objects.get(producto=producto_activo)
        assert stock.cantidad == Decimal("5")

    def test_credito_no_actualiza_stock_y_crea_cuenta_corriente(
        self, proveedor, usuario_cajero, producto_activo
    ):
        from apps.compras.services import CompraService
        from apps.compras.models import Compra, CuentaCorrienteProveedor
        from apps.inventario.models import Stock

        compra = CompraService.registrar_compra(
            proveedor=proveedor,
            creado_por=usuario_cajero,
            tipo_pago="CREDITO",
            items=[_item(producto_activo, cantidad=3, costo=20000)],
        )

        assert compra.tipo_pago == Compra.TipoPago.CREDITO
        assert compra.estado_pago == Compra.EstadoPago.PENDIENTE
        assert compra.estado_entrega == Compra.EstadoEntrega.PENDIENTE
        assert not Stock.objects.filter(producto=producto_activo).exists()
        assert CuentaCorrienteProveedor.objects.filter(
            proveedor=proveedor, tipo=CuentaCorrienteProveedor.Tipo.DEBITO
        ).exists()

    def test_items_invalidos_lanza_validation_error(self, proveedor, usuario_cajero):
        from apps.compras.services import CompraService
        from rest_framework.exceptions import ValidationError
        with pytest.raises(ValidationError):
            CompraService.registrar_compra(
                proveedor=proveedor,
                creado_por=usuario_cajero,
                tipo_pago="CONTADO",
                items=[],
            )


# ── confirmar_compra ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestConfirmarCompra:
    def test_compra_credito_pendiente_se_confirma(self, proveedor, usuario_cajero, producto_activo):
        from apps.compras.services import CompraService
        from apps.compras.models import Compra
        from apps.inventario.models import Stock

        compra = CompraService.registrar_compra(
            proveedor=proveedor,
            creado_por=usuario_cajero,
            tipo_pago="CREDITO",
            items=[_item(producto_activo, cantidad=4, costo=15000)],
        )
        assert compra.estado_entrega == Compra.EstadoEntrega.PENDIENTE

        compra_confirmada = CompraService.confirmar_compra(compra=compra, autorizado_por=usuario_cajero)

        assert compra_confirmada.estado_entrega == Compra.EstadoEntrega.RECIBIDA
        stock = Stock.objects.get(producto=producto_activo)
        assert stock.cantidad == Decimal("4")

    def test_compra_ya_recibida_lanza_error(self, proveedor, usuario_cajero, producto_activo):
        from apps.compras.services import CompraService
        from rest_framework.exceptions import ValidationError

        compra = CompraService.registrar_compra(
            proveedor=proveedor,
            creado_por=usuario_cajero,
            tipo_pago="CONTADO",
            items=[_item(producto_activo, cantidad=1, costo=5000)],
        )
        with pytest.raises(ValidationError) as exc_info:
            CompraService.confirmar_compra(compra=compra, autorizado_por=usuario_cajero)
        assert "ya fue recibida" in str(exc_info.value.detail)

    def test_sin_detalles_lanza_error(self, proveedor, usuario_cajero):
        from apps.compras.models import Compra
        from apps.compras.services import CompraService
        from rest_framework.exceptions import ValidationError

        compra = Compra.objects.create(
            proveedor=proveedor,
            creado_por=usuario_cajero,
            tipo_pago=Compra.TipoPago.CREDITO,
            monto_total=Decimal("0"),
            estado_pago=Compra.EstadoPago.PENDIENTE,
            estado_entrega=Compra.EstadoEntrega.PENDIENTE,
        )
        with pytest.raises(ValidationError):
            CompraService._actualizar_stock_y_costos(compra, usuario_cajero)
