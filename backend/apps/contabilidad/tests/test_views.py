"""
Tests de vistas de contabilidad — cierre de caja y permisos.
"""
import pytest
from decimal import Decimal
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_admin(api_client, usuario_admin):
    api_client.force_authenticate(user=usuario_admin)
    return api_client


@pytest.fixture
def api_cajero(api_client, usuario_cajero):
    api_client.force_authenticate(user=usuario_cajero)
    return api_client


@pytest.fixture
def caja(db):
    from apps.contabilidad.models import Caja
    return Caja.objects.create(nombre="Caja Principal", activo=True)


@pytest.fixture
def cierre_abierto(db, caja, usuario_cajero):
    from apps.contabilidad.models import CierreCaja
    return CierreCaja.objects.create(
        caja=caja,
        empleado=usuario_cajero,
        monto_inicial=Decimal("100000"),
        estado=CierreCaja.Estado.ABIERTO,
    )


@pytest.fixture
def cierre_cerrado(db, caja, usuario_cajero):
    from django.utils import timezone
    from apps.contabilidad.models import CierreCaja
    return CierreCaja.objects.create(
        caja=caja,
        empleado=usuario_cajero,
        monto_inicial=Decimal("100000"),
        monto_contado_fisico=Decimal("105000"),
        diferencia_efectivo=Decimal("5000"),
        fecha_cierre=timezone.now(),
        estado=CierreCaja.Estado.CERRADO,
    )


@pytest.mark.django_db
class TestCerrarCaja:

    def test_cajero_puede_cerrar(self, api_cajero, cierre_abierto):
        url = f"/api/contabilidad/cierres-caja/{cierre_abierto.pk}/cerrar/"
        resp = api_cajero.post(url, {"monto_contado_fisico": 105000}, format="json")
        assert resp.status_code == 200
        assert resp.data["estado"] == "CERRADO"
        assert resp.data["monto_contado_fisico"] == "105000"

    def test_cerrar_dos_veces_falla(self, api_cajero, cierre_abierto):
        url = f"/api/contabilidad/cierres-caja/{cierre_abierto.pk}/cerrar/"
        api_cajero.post(url, {"monto_contado_fisico": 100000}, format="json")
        resp = api_cajero.post(url, {"monto_contado_fisico": 100000}, format="json")
        assert resp.status_code == 400

    def test_sin_autenticacion_falla(self, api_client, cierre_abierto):
        url = f"/api/contabilidad/cierres-caja/{cierre_abierto.pk}/cerrar/"
        resp = api_client.post(url, {"monto_contado_fisico": 100000}, format="json")
        assert resp.status_code in (401, 403)

    def test_diferencia_calculada(self, api_cajero, cierre_abierto, medio_pago_efectivo):
        from apps.contabilidad.models import MovimientoCaja
        MovimientoCaja.objects.create(
            cierre=cierre_abierto,
            tipo=MovimientoCaja.Tipo.INGRESO,
            monto=Decimal("20000"),
            medio_pago=medio_pago_efectivo,
        )
        url = f"/api/contabilidad/cierres-caja/{cierre_abierto.pk}/cerrar/"
        resp = api_cajero.post(url, {"monto_contado_fisico": 115000}, format="json")
        assert resp.status_code == 200
        # monto_esperado = 100000 + 20000 = 120000; contado = 115000 → diferencia = -5000
        assert int(resp.data["diferencia_efectivo"]) == -5000


@pytest.mark.django_db
class TestConciliarCaja:

    def test_admin_puede_conciliar(self, api_admin, cierre_cerrado):
        url = f"/api/contabilidad/cierres-caja/{cierre_cerrado.pk}/conciliar/"
        resp = api_admin.post(url, {"observaciones": "Todo en orden"}, format="json")
        assert resp.status_code == 200
        assert resp.data["estado"] == "CONCILIADO"

    def test_cajero_puede_conciliar(self, api_cajero, cierre_cerrado):
        url = f"/api/contabilidad/cierres-caja/{cierre_cerrado.pk}/conciliar/"
        resp = api_cajero.post(url, {}, format="json")
        assert resp.status_code == 200

    def test_conciliar_caja_abierta_falla(self, api_admin, cierre_abierto):
        url = f"/api/contabilidad/cierres-caja/{cierre_abierto.pk}/conciliar/"
        resp = api_admin.post(url, {}, format="json")
        assert resp.status_code == 400

    def test_observaciones_guardadas(self, api_admin, cierre_cerrado):
        from apps.contabilidad.models import CierreCaja
        url = f"/api/contabilidad/cierres-caja/{cierre_cerrado.pk}/conciliar/"
        api_admin.post(url, {"observaciones": "Diferencia justificada"}, format="json")
        cierre_cerrado.refresh_from_db()
        assert cierre_cerrado.observaciones_conciliacion == "Diferencia justificada"


@pytest.mark.django_db
class TestCierrePDF:

    def test_pdf_retorna_html(self, api_admin, cierre_cerrado):
        url = f"/api/contabilidad/cierres-caja/{cierre_cerrado.pk}/pdf/"
        resp = api_admin.get(url)
        assert resp.status_code == 200
        assert "text/html" in resp["Content-Type"]
        assert b"Cierre de Caja" in resp.content

    def test_pdf_sin_autenticacion_falla(self, api_client, cierre_cerrado):
        url = f"/api/contabilidad/cierres-caja/{cierre_cerrado.pk}/pdf/"
        resp = api_client.get(url)
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestCajaPermissions:

    def test_anonimo_no_puede_listar_cierres(self, api_client):
        resp = api_client.get("/api/contabilidad/cierres-caja/")
        assert resp.status_code in (401, 403)

    def test_cajero_puede_listar_cierres(self, api_cajero):
        resp = api_cajero.get("/api/contabilidad/cierres-caja/")
        assert resp.status_code == 200

    def test_cajero_puede_crear_cierre(self, api_cajero, caja, usuario_cajero):
        resp = api_cajero.post("/api/contabilidad/cierres-caja/", {
            "caja": caja.pk,
            "empleado": usuario_cajero.pk,
            "monto_inicial": 50000,
        }, format="json")
        assert resp.status_code == 201
