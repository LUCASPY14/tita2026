"""
Smoke tests — verifican que los endpoints criticos responden correctamente.

Cubren la ruta dorada de cada dominio: auth, productos, clientes, tarjetas,
ventas, contabilidad, inventario, notificaciones y el health check.
Ejecutar solo smoke: pytest -m smoke
"""
import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.smoke


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def auth_admin(client, usuario_admin):
    client.force_authenticate(user=usuario_admin)
    return client


@pytest.fixture
def auth_cajero(client, usuario_cajero):
    client.force_authenticate(user=usuario_cajero)
    return client


# ── Health ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestHealthSmoke:

    def test_health_ready_responde(self, client):
        """Liveness: acepta 200 (todo ok) o 503 (sin Redis/Celery en CI)."""
        res = client.get("/api/health/ready/")
        assert res.status_code in (200, 503)
        data = res.json()
        assert "status" in data
        assert "checks" in data
        assert "db" in data["checks"]

    def test_health_ready_db_ok(self, client):
        """La DB debe estar disponible en cualquier entorno de test."""
        res = client.get("/api/health/ready/")
        data = res.json()
        assert data["checks"]["db"] == "ok"

    def test_health_version_presente(self, client):
        res = client.get("/api/health/")
        assert "version" in res.json()


# ── Auth ──────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAuthSmoke:

    def test_login_valido_retorna_tokens(self, client, usuario_admin):
        res = client.post(
            "/api/token/",
            {"email": "admin@test.com", "password": "test1234"},
            format="json",
        )
        assert res.status_code == 200
        data = res.json()
        assert "access" in data
        assert "refresh" in data

    def test_login_credenciales_incorrectas(self, client):
        res = client.post(
            "/api/token/",
            {"email": "nadie@test.com", "password": "wrong"},
            format="json",
        )
        assert res.status_code == 401

    def test_sin_token_retorna_401(self, client):
        res = client.get("/api/v1/productos/productos/")
        assert res.status_code == 401


# ── Productos ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProductosSmoke:

    def test_list_productos(self, auth_admin, producto):
        res = auth_admin.get("/api/v1/productos/productos/")
        assert res.status_code == 200
        assert res.json()["count"] >= 1

    def test_list_categorias(self, auth_admin, categoria):
        res = auth_admin.get("/api/v1/productos/categorias/")
        assert res.status_code == 200
        assert res.json()["count"] >= 1

    def test_list_listas_precio(self, auth_admin, lista_precio):
        res = auth_admin.get("/api/v1/productos/listas-precio/")
        assert res.status_code == 200


# ── Clientes ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestClientesSmoke:

    def test_list_clientes(self, auth_admin, cliente):
        res = auth_admin.get("/api/v1/clientes/clientes/")
        assert res.status_code == 200
        assert res.json()["count"] >= 1

    def test_list_tipos_cliente(self, auth_admin, tipo_cliente):
        res = auth_admin.get("/api/v1/clientes/tipos-cliente/")
        assert res.status_code == 200


# ── Core / Tarjetas ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCoreSmoke:

    def test_list_tarjetas(self, auth_admin):
        res = auth_admin.get("/api/v1/core/tarjetas/")
        assert res.status_code == 200

    def test_list_medios_pago(self, auth_admin, medio_pago_efectivo):
        res = auth_admin.get("/api/v1/core/medios-pago/")
        assert res.status_code == 200
        assert res.json()["count"] >= 1


# ── Ventas ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestVentasSmoke:

    def test_list_ventas_cajero(self, auth_cajero):
        res = auth_cajero.get("/api/v1/ventas/ventas/")
        assert res.status_code == 200

    def test_list_ventas_admin(self, auth_admin):
        res = auth_admin.get("/api/v1/ventas/ventas/")
        assert res.status_code == 200


# ── Contabilidad ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestContabilidadSmoke:

    def test_list_cajas(self, auth_admin):
        res = auth_admin.get("/api/v1/contabilidad/cajas/")
        assert res.status_code == 200


# ── Inventario ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestInventarioSmoke:

    def test_list_stock(self, auth_admin, stock_producto):
        res = auth_admin.get("/api/v1/inventario/stock/")
        assert res.status_code == 200
        assert res.json()["count"] >= 1


# ── Notificaciones ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestNotificacionesSmoke:

    def test_list_notificaciones(self, auth_admin):
        res = auth_admin.get("/api/v1/notificaciones/notificaciones/")
        assert res.status_code == 200

    def test_preferencias_notificacion(self, auth_admin):
        res = auth_admin.get("/api/v1/notificaciones/preferencias/")
        assert res.status_code == 200


# ── Usuarios ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestUsuariosSmoke:

    def test_list_usuarios_admin(self, auth_admin):
        res = auth_admin.get("/api/v1/usuarios/usuarios/")
        assert res.status_code == 200

    def test_cajero_no_puede_listar_usuarios(self, auth_cajero):
        res = auth_cajero.get("/api/v1/usuarios/usuarios/")
        assert res.status_code in (403, 404)