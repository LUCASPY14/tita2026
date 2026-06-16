"""
Smoke test parametrizado de permisos a nivel de objeto.

Verifica que:
- Cajero A solo ve sus propios recursos en LIST.
- Cajero A recibe 404 al intentar acceder al recurso de Cajero B en DETAIL.
- Admin ve todo (ambos cajeros) en LIST.

Cubre: VentaViewSet y CierreCajaViewSet (ambos heredan CajaOwnerQuerysetMixin).
"""
import pytest
from decimal import Decimal
from rest_framework.test import APIClient

from apps.usuarios.models import Usuario


# ── Fixtures locales ──────────────────────────────────────────────────────────

@pytest.fixture
def cajero_a(db):
    return Usuario.objects.create_user(
        email="cajero_a@perms.test",
        password="Test1234!",
        nombre="Cajero",
        apellido="Alfa",
        rol=Usuario.Rol.CAJERO,
    )


@pytest.fixture
def cajero_b(db):
    return Usuario.objects.create_user(
        email="cajero_b@perms.test",
        password="Test1234!",
        nombre="Cajero",
        apellido="Beta",
        rol=Usuario.Rol.CAJERO,
    )


@pytest.fixture
def caja_a(db):
    from apps.contabilidad.models import Caja
    return Caja.objects.create(nombre="Caja Alfa", activo=True)


@pytest.fixture
def caja_b(db):
    from apps.contabilidad.models import Caja
    return Caja.objects.create(nombre="Caja Beta", activo=True)


@pytest.fixture
def cierre_a(db, caja_a, cajero_a):
    from apps.contabilidad.models import CierreCaja
    return CierreCaja.objects.create(
        caja=caja_a,
        empleado=cajero_a,
        monto_inicial=Decimal("100000"),
        estado=CierreCaja.Estado.ABIERTO,
    )


@pytest.fixture
def cierre_b(db, caja_b, cajero_b):
    from apps.contabilidad.models import CierreCaja
    return CierreCaja.objects.create(
        caja=caja_b,
        empleado=cajero_b,
        monto_inicial=Decimal("100000"),
        estado=CierreCaja.Estado.ABIERTO,
    )


@pytest.fixture
def venta_a(db, cliente, cajero_a, medio_pago_efectivo, producto, stock_producto, cierre_a):
    from apps.ventas.services import VentaService
    return VentaService.registrar_venta(
        cliente=cliente,
        cajero=cajero_a,
        tipo="CONTADO",
        medio_pago=medio_pago_efectivo,
        items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}],
        cierre_caja=cierre_a,
    )


@pytest.fixture
def venta_b(db, cliente, cajero_b, medio_pago_efectivo, producto, stock_producto, cierre_b):
    from apps.ventas.services import VentaService
    return VentaService.registrar_venta(
        cliente=cliente,
        cajero=cajero_b,
        tipo="CONTADO",
        medio_pago=medio_pago_efectivo,
        items=[{"producto": producto, "cantidad": Decimal("1"), "precio_unitario": Decimal("3000")}],
        cierre_caja=cierre_b,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def auth_client(user: Usuario) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=user)
    return c


# ── Tests parametrizados ──────────────────────────────────────────────────────

RESOURCES = [
    pytest.param("/api/v1/ventas/ventas/", "venta_a", "venta_b", id="ventas"),
    pytest.param("/api/v1/contabilidad/cierres-caja/", "cierre_a", "cierre_b", id="cierres_caja"),
]


@pytest.mark.django_db
@pytest.mark.parametrize("url,fixture_a,fixture_b", RESOURCES)
def test_cajero_list_sees_only_own(
    url, fixture_a, fixture_b,
    cajero_a, cajero_b, request,
):
    """Cajero A lista el endpoint y ve exactamente 1 resultado (el suyo)."""
    request.getfixturevalue(fixture_a)
    request.getfixturevalue(fixture_b)

    resp = auth_client(cajero_a).get(url)

    assert resp.status_code == 200
    assert resp.data["count"] == 1, (
        f"Cajero A debería ver solo 1 registro en {url}, "
        f"pero vio {resp.data['count']}"
    )


@pytest.mark.django_db
@pytest.mark.parametrize("url,fixture_a,fixture_b", RESOURCES)
def test_cajero_detail_cannot_access_others(
    url, fixture_a, fixture_b,
    cajero_a, cajero_b, request,
):
    """Cajero A recibe 404 al pedir el recurso de Cajero B por su PK."""
    request.getfixturevalue(fixture_a)
    obj_b = request.getfixturevalue(fixture_b)

    resp = auth_client(cajero_a).get(f"{url}{obj_b.pk}/")

    assert resp.status_code == 404, (
        f"Cajero A debería recibir 404 al acceder al {fixture_b} de Cajero B, "
        f"pero recibió {resp.status_code}"
    )


@pytest.mark.django_db
@pytest.mark.parametrize("url,fixture_a,fixture_b", RESOURCES)
def test_admin_list_sees_all(
    url, fixture_a, fixture_b,
    usuario_admin, request,
):
    """Admin ve todos los registros de ambos cajeros en el endpoint de lista."""
    request.getfixturevalue(fixture_a)
    request.getfixturevalue(fixture_b)

    resp = auth_client(usuario_admin).get(url)

    assert resp.status_code == 200
    assert resp.data["count"] == 2, (
        f"Admin debería ver 2 registros en {url}, "
        f"pero vio {resp.data['count']}"
    )
