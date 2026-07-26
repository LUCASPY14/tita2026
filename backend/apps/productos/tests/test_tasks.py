"""Tests para apps.productos.tasks — sincronizar_costos_desde_compras."""
import pytest
from decimal import Decimal


# ── fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def proveedor(db):
    from apps.compras.models import Proveedor
    return Proveedor.objects.create(
        razon_social="Proveedor Test",
        ruc="80000001-1",
        activo=True,
    )


@pytest.fixture
def producto2(db, categoria, unidad_medida, lista_precio):
    """Segundo producto para tests con múltiples ítems."""
    from apps.productos.models import Producto
    return Producto.objects.create(
        descripcion="Galleta surtida",
        categoria=categoria,
        unidad_medida=unidad_medida,
        requiere_stock=True,
        permite_stock_negativo=False,
        activo=True,
    )


def _compra(proveedor, usuario, detalles, estado_entrega="RECIBIDA"):
    """
    Crea una Compra con sus DetalleCompra.
    detalles: list of (producto, cantidad, costo_unitario)
    """
    from apps.compras.models import Compra, DetalleCompra
    total = sum(Decimal(str(cu)) * Decimal(str(cant)) for _, cant, cu in detalles)
    compra = Compra.objects.create(
        proveedor=proveedor,
        monto_total=total,
        estado_entrega=estado_entrega,
        creado_por=usuario,
    )
    for prod, cant, cu in detalles:
        DetalleCompra.objects.create(
            compra=compra,
            producto=prod,
            cantidad=Decimal(str(cant)),
            costo_unitario=Decimal(str(cu)),
            subtotal=(Decimal(str(cant)) * Decimal(str(cu))).quantize(Decimal("1")),
        )
    return compra


# ── sincronizar_costos_desde_compras ──────────────────────────────────────────

@pytest.mark.django_db
class TestSincronizarCostosDesdeCompras:

    def test_sin_compras_retorna_cero(self, db):
        from apps.productos.tasks import sincronizar_costos_desde_compras
        result = sincronizar_costos_desde_compras()
        assert result == {"compras_procesadas": 0, "costos_registrados": 0}

    def test_compra_pendiente_no_se_procesa(self, proveedor, usuario_admin, producto):
        from apps.inventario.models import CostoHistorico
        from apps.productos.tasks import sincronizar_costos_desde_compras
        _compra(proveedor, usuario_admin, [(producto, 10, 2000)], estado_entrega="PENDIENTE")
        result = sincronizar_costos_desde_compras()
        assert result["costos_registrados"] == 0
        assert not CostoHistorico.objects.exists()

    def test_compra_recibida_crea_costo_historico(self, proveedor, usuario_admin, producto):
        from apps.inventario.models import CostoHistorico
        from apps.productos.tasks import sincronizar_costos_desde_compras
        compra = _compra(proveedor, usuario_admin, [(producto, 5, 1500)])
        result = sincronizar_costos_desde_compras()
        assert result == {"compras_procesadas": 1, "costos_registrados": 1}
        assert CostoHistorico.objects.filter(compra=compra, producto=producto).exists()

    def test_costo_historico_tiene_valores_correctos(self, proveedor, usuario_admin, producto):
        from apps.inventario.models import CostoHistorico
        from apps.productos.tasks import sincronizar_costos_desde_compras
        compra = _compra(proveedor, usuario_admin, [(producto, Decimal("3.500"), 4000)])
        sincronizar_costos_desde_compras()
        costo = CostoHistorico.objects.get(compra=compra, producto=producto)
        assert costo.costo_unitario == Decimal("4000")
        assert costo.cantidad_comprada == Decimal("3.500")
        assert costo.fecha_compra == compra.fecha

    def test_compra_con_multiples_productos(self, proveedor, usuario_admin, producto, producto2):
        from apps.inventario.models import CostoHistorico
        from apps.productos.tasks import sincronizar_costos_desde_compras
        compra = _compra(
            proveedor, usuario_admin,
            [(producto, 10, 2000), (producto2, 5, 3000)],
        )
        result = sincronizar_costos_desde_compras()
        assert result == {"compras_procesadas": 1, "costos_registrados": 2}
        assert CostoHistorico.objects.filter(compra=compra).count() == 2

    def test_idempotente_no_duplica_costos(self, proveedor, usuario_admin, producto):
        """Ejecutar la tarea dos veces no crea registros duplicados."""
        from apps.inventario.models import CostoHistorico
        from apps.productos.tasks import sincronizar_costos_desde_compras
        _compra(proveedor, usuario_admin, [(producto, 10, 2000)])
        sincronizar_costos_desde_compras()
        result2 = sincronizar_costos_desde_compras()
        assert result2 == {"compras_procesadas": 0, "costos_registrados": 0}
        assert CostoHistorico.objects.count() == 1

    def test_compra_parcialmente_recibida_no_se_procesa(
        self, proveedor, usuario_admin, producto,
    ):
        from apps.inventario.models import CostoHistorico
        from apps.productos.tasks import sincronizar_costos_desde_compras
        _compra(proveedor, usuario_admin, [(producto, 10, 2000)], estado_entrega="PARCIAL")
        result = sincronizar_costos_desde_compras()
        assert result["costos_registrados"] == 0
        assert not CostoHistorico.objects.exists()

    def test_multiples_compras_solo_recibidas_procesadas(
        self, proveedor, usuario_admin, producto, producto2,
    ):
        from apps.productos.tasks import sincronizar_costos_desde_compras
        _compra(proveedor, usuario_admin, [(producto, 5, 1000)], estado_entrega="RECIBIDA")
        _compra(proveedor, usuario_admin, [(producto2, 3, 2000)], estado_entrega="PENDIENTE")
        result = sincronizar_costos_desde_compras()
        assert result["compras_procesadas"] == 1
        assert result["costos_registrados"] == 1

    def test_costo_promedio_actualizado_tras_sincronizacion(
        self, proveedor, usuario_admin, producto,
    ):
        """
        Después de sincronizar, Stock.costo_promedio refleja los costos registrados.
        Crea dos compras recibidas y verifica que costo_promedio sea el promedio ponderado.
        """
        from apps.inventario.models import Stock
        from apps.productos.tasks import sincronizar_costos_desde_compras

        Stock.objects.get_or_create(producto=producto, defaults={"cantidad": Decimal("20")})

        # Compra 1: 10 unidades a 2000
        _compra(proveedor, usuario_admin, [(producto, 10, 2000)])
        # Compra 2: 10 unidades a 4000
        _compra(proveedor, usuario_admin, [(producto, 10, 4000)])

        sincronizar_costos_desde_compras()

        stock = Stock.objects.get(producto=producto)
        # costo_promedio = (10×2000 + 10×4000) / 20 = 60000/20 = 3000
        assert stock.costo_promedio == Decimal("3000")
