"""Tests para apps.inventario.tasks — alertar_stock_minimo, verificar_vencimientos, generar_resumen_diario_stock."""
import pytest
from decimal import Decimal
from datetime import date, timedelta


@pytest.fixture
def producto_con_minimo(db, categoria, unidad_medida):
    """Producto con stock_minimo=10."""
    from apps.productos.models import Producto
    return Producto.objects.create(
        descripcion="Producto Alerta Test",
        categoria=categoria,
        unidad_medida=unidad_medida,
        activo=True,
        requiere_stock=True,
        permite_stock_negativo=False,
        stock_minimo=Decimal("10"),
    )


@pytest.fixture
def stock_bajo(db, producto_con_minimo):
    """Stock = 8 (< stock_minimo=10, > 50% de 10=5) → STOCK_MINIMO."""
    from apps.inventario.models import Stock
    return Stock.objects.create(producto=producto_con_minimo, cantidad=Decimal("8"))


@pytest.fixture
def stock_cero(db, producto_con_minimo):
    from apps.inventario.models import Stock
    return Stock.objects.create(producto=producto_con_minimo, cantidad=Decimal("0"))


@pytest.fixture
def stock_critico(db, producto_con_minimo):
    """Stock = 3 (< 50% de stock_minimo=10 = 5) → STOCK_CRITICO."""
    from apps.inventario.models import Stock
    return Stock.objects.create(producto=producto_con_minimo, cantidad=Decimal("3"))


@pytest.fixture
def stock_normal(db, producto_con_minimo):
    """Stock > stock_minimo → no requiere reposición."""
    from apps.inventario.models import Stock
    return Stock.objects.create(producto=producto_con_minimo, cantidad=Decimal("20"))


@pytest.fixture
def lote_vencido(db, producto):
    from apps.inventario.models import LoteProducto
    return LoteProducto.objects.create(
        producto=producto,
        numero_lote="LOTE-VENC-01",
        fecha_vencimiento=date.today() - timedelta(days=5),
        cantidad_inicial=Decimal("10"),
        cantidad_disponible=Decimal("10"),
    )


@pytest.fixture
def lote_por_vencer_7d(db, producto):
    from apps.inventario.models import LoteProducto
    return LoteProducto.objects.create(
        producto=producto,
        numero_lote="LOTE-7D-01",
        fecha_vencimiento=date.today() + timedelta(days=5),
        cantidad_inicial=Decimal("10"),
        cantidad_disponible=Decimal("10"),
    )


@pytest.fixture
def lote_por_vencer_30d(db, producto):
    from apps.inventario.models import LoteProducto
    return LoteProducto.objects.create(
        producto=producto,
        numero_lote="LOTE-30D-01",
        fecha_vencimiento=date.today() + timedelta(days=25),
        cantidad_inicial=Decimal("10"),
        cantidad_disponible=Decimal("10"),
    )


# ── alertar_stock_minimo ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAlertarStockMinimo:

    def test_sin_stocks_retorna_cero(self, db):
        from apps.inventario.tasks import alertar_stock_minimo
        result = alertar_stock_minimo()
        assert result == {"alertas_creadas": 0}

    def test_stock_bajo_crea_alerta_stock_minimo(self, stock_bajo):
        from apps.inventario.models import AlertaStock
        from apps.inventario.tasks import alertar_stock_minimo
        result = alertar_stock_minimo()
        assert result["alertas_creadas"] >= 1
        assert AlertaStock.objects.filter(
            producto=stock_bajo.producto,
            tipo=AlertaStock.TipoAlerta.STOCK_MINIMO,
            activa=True,
        ).exists()

    def test_stock_cero_crea_alerta_stock_cero(self, stock_cero):
        from apps.inventario.models import AlertaStock
        from apps.inventario.tasks import alertar_stock_minimo
        result = alertar_stock_minimo()
        assert result["alertas_creadas"] >= 1
        assert AlertaStock.objects.filter(
            producto=stock_cero.producto,
            tipo=AlertaStock.TipoAlerta.STOCK_CERO,
            activa=True,
        ).exists()

    def test_stock_critico_crea_alerta_critica(self, stock_critico):
        from apps.inventario.models import AlertaStock
        from apps.inventario.tasks import alertar_stock_minimo
        result = alertar_stock_minimo()
        assert result["alertas_creadas"] >= 1
        assert AlertaStock.objects.filter(
            producto=stock_critico.producto,
            tipo=AlertaStock.TipoAlerta.STOCK_CRITICO,
            activa=True,
        ).exists()

    def test_stock_normal_resuelve_alerta_previa(self, stock_normal):
        from apps.inventario.models import AlertaStock
        # Crear alerta previa activa
        AlertaStock.objects.create(
            producto=stock_normal.producto,
            tipo=AlertaStock.TipoAlerta.STOCK_MINIMO,
            stock_actual=Decimal("5"),
            stock_minimo=Decimal("10"),
            activa=True,
        )
        from apps.inventario.tasks import alertar_stock_minimo
        result = alertar_stock_minimo()
        assert result["alertas_creadas"] == 0
        assert not AlertaStock.objects.filter(
            producto=stock_normal.producto, activa=True
        ).exists()

    def test_no_duplica_alerta_del_mismo_tipo(self, stock_bajo):
        from apps.inventario.models import AlertaStock
        from apps.inventario.tasks import alertar_stock_minimo
        # Primera ejecución
        alertar_stock_minimo()
        count1 = AlertaStock.objects.filter(producto=stock_bajo.producto, activa=True).count()
        # Segunda ejecución — no debe duplicar
        result = alertar_stock_minimo()
        count2 = AlertaStock.objects.filter(producto=stock_bajo.producto, activa=True).count()
        assert result["alertas_creadas"] == 0
        assert count2 == count1


# ── verificar_vencimientos ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestVerificarVencimientos:

    def test_sin_lotes_retorna_cero(self, db):
        from apps.inventario.tasks import verificar_vencimientos
        result = verificar_vencimientos()
        assert result == {"alertas_creadas": 0}

    def test_lote_vencido_crea_alerta_vencido(self, lote_vencido):
        from apps.inventario.models import AlertaVencimiento
        from apps.inventario.tasks import verificar_vencimientos
        result = verificar_vencimientos()
        assert result["alertas_creadas"] >= 1
        assert AlertaVencimiento.objects.filter(
            lote=lote_vencido, tipo=AlertaVencimiento.TipoAlerta.VENCIDO
        ).exists()

    def test_lote_a_7_dias_crea_alerta_dias7(self, lote_por_vencer_7d):
        from apps.inventario.models import AlertaVencimiento
        from apps.inventario.tasks import verificar_vencimientos
        result = verificar_vencimientos()
        assert result["alertas_creadas"] >= 1
        assert AlertaVencimiento.objects.filter(lote=lote_por_vencer_7d).exists()

    def test_lote_a_30_dias_crea_alerta_dias30(self, lote_por_vencer_30d):
        from apps.inventario.models import AlertaVencimiento
        from apps.inventario.tasks import verificar_vencimientos
        result = verificar_vencimientos()
        assert result["alertas_creadas"] >= 1
        assert AlertaVencimiento.objects.filter(lote=lote_por_vencer_30d).exists()

    def test_no_duplica_alerta_existente(self, lote_vencido):
        from apps.inventario.models import AlertaVencimiento
        from apps.inventario.tasks import verificar_vencimientos
        verificar_vencimientos()
        result = verificar_vencimientos()
        count = AlertaVencimiento.objects.filter(
            lote=lote_vencido, tipo=AlertaVencimiento.TipoAlerta.VENCIDO
        ).count()
        assert count == 1
        assert result["alertas_creadas"] == 0


# ── generar_resumen_diario_stock ───────────────────────────────────────────────

@pytest.mark.django_db
class TestGenerarResumenDiarioStock:

    def test_retorna_estructura_correcta(self, db):
        from apps.inventario.tasks import generar_resumen_diario_stock
        result = generar_resumen_diario_stock()
        assert "fecha" in result
        assert "total_productos_en_stock" in result
        assert "productos_sin_stock" in result
        assert "alertas_activas" in result

    def test_con_stock_cuenta_productos(self, stock_producto):
        from apps.inventario.tasks import generar_resumen_diario_stock
        result = generar_resumen_diario_stock()
        assert result["total_productos_en_stock"] >= 1
        assert result["productos_sin_stock"] == 0
