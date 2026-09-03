"""Tests para apps.inventario.tasks — alertar_stock_minimo, generar_resumen_diario_stock."""
import pytest
from decimal import Decimal


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
def stock_normal(db, producto_con_minimo):
    """Stock > stock_minimo → no requiere reposición."""
    from apps.inventario.models import Stock
    return Stock.objects.create(producto=producto_con_minimo, cantidad=Decimal("20"))


@pytest.fixture
def usuario_admin2(db):
    from apps.usuarios.models import Usuario
    return Usuario.objects.create_user(
        email="admin2@test.com",
        password="test1234",
        nombre="Admin2",
        apellido="Test",
        rol=Usuario.Rol.ADMIN,
    )


# ── alertar_stock_minimo ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAlertarStockMinimo:

    def test_sin_stocks_retorna_cero(self, db):
        from apps.inventario.tasks import alertar_stock_minimo
        result = alertar_stock_minimo()
        assert result == {"alertas_creadas": 0}

    def test_stock_bajo_notifica_a_admins_activos(self, stock_bajo, usuario_admin):
        from apps.notificaciones.models import Notificacion
        from apps.inventario.tasks import alertar_stock_minimo
        result = alertar_stock_minimo()
        assert result["alertas_creadas"] == 1
        notif = Notificacion.objects.get(usuario=usuario_admin)
        assert stock_bajo.producto.descripcion in notif.mensaje

    def test_notifica_a_cada_admin_activo(self, stock_bajo, usuario_admin, usuario_admin2):
        from apps.notificaciones.models import Notificacion
        from apps.inventario.tasks import alertar_stock_minimo
        result = alertar_stock_minimo()
        assert result["alertas_creadas"] == 2
        assert Notificacion.objects.filter(usuario=usuario_admin).exists()
        assert Notificacion.objects.filter(usuario=usuario_admin2).exists()

    def test_sin_admins_activos_no_notifica(self, stock_bajo):
        from apps.notificaciones.models import Notificacion
        from apps.inventario.tasks import alertar_stock_minimo
        result = alertar_stock_minimo()
        assert result == {"alertas_creadas": 0}
        assert not Notificacion.objects.exists()

    def test_stock_normal_no_notifica(self, stock_normal, usuario_admin):
        from apps.notificaciones.models import Notificacion
        from apps.inventario.tasks import alertar_stock_minimo
        result = alertar_stock_minimo()
        assert result == {"alertas_creadas": 0}
        assert not Notificacion.objects.exists()


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
