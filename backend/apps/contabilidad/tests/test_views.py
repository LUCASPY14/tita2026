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
        url = f"/api/v1/contabilidad/cierres-caja/{cierre_abierto.pk}/cerrar/"
        resp = api_cajero.post(url, {"monto_contado_fisico": 105000}, format="json")
        assert resp.status_code == 200
        assert resp.data["estado"] == "CERRADO"
        assert resp.data["monto_contado_fisico"] == "105000"

    def test_cerrar_dos_veces_falla(self, api_cajero, cierre_abierto):
        url = f"/api/v1/contabilidad/cierres-caja/{cierre_abierto.pk}/cerrar/"
        api_cajero.post(url, {"monto_contado_fisico": 100000}, format="json")
        resp = api_cajero.post(url, {"monto_contado_fisico": 100000}, format="json")
        assert resp.status_code == 400

    def test_sin_autenticacion_falla(self, api_client, cierre_abierto):
        url = f"/api/v1/contabilidad/cierres-caja/{cierre_abierto.pk}/cerrar/"
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
        url = f"/api/v1/contabilidad/cierres-caja/{cierre_abierto.pk}/cerrar/"
        resp = api_cajero.post(url, {"monto_contado_fisico": 115000}, format="json")
        assert resp.status_code == 200
        # monto_esperado = 100000 + 20000 = 120000; contado = 115000 → diferencia = -5000
        assert int(resp.data["diferencia_efectivo"]) == -5000


@pytest.mark.django_db
class TestConciliarCaja:

    def test_admin_puede_conciliar(self, api_admin, cierre_cerrado):
        url = f"/api/v1/contabilidad/cierres-caja/{cierre_cerrado.pk}/conciliar/"
        resp = api_admin.post(url, {"observaciones": "Todo en orden"}, format="json")
        assert resp.status_code == 200
        assert resp.data["estado"] == "CONCILIADO"

    def test_cajero_puede_conciliar(self, api_cajero, cierre_cerrado):
        url = f"/api/v1/contabilidad/cierres-caja/{cierre_cerrado.pk}/conciliar/"
        resp = api_cajero.post(url, {}, format="json")
        assert resp.status_code == 200

    def test_conciliar_caja_abierta_falla(self, api_admin, cierre_abierto):
        url = f"/api/v1/contabilidad/cierres-caja/{cierre_abierto.pk}/conciliar/"
        resp = api_admin.post(url, {}, format="json")
        assert resp.status_code == 400

    def test_observaciones_guardadas(self, api_admin, cierre_cerrado):
        url = f"/api/v1/contabilidad/cierres-caja/{cierre_cerrado.pk}/conciliar/"
        api_admin.post(url, {"observaciones": "Diferencia justificada"}, format="json")
        cierre_cerrado.refresh_from_db()
        assert cierre_cerrado.observaciones_conciliacion == "Diferencia justificada"


@pytest.mark.django_db
class TestCierrePDF:

    def test_pdf_retorna_html(self, api_admin, cierre_cerrado):
        url = f"/api/v1/contabilidad/cierres-caja/{cierre_cerrado.pk}/pdf/"
        resp = api_admin.get(url)
        assert resp.status_code == 200
        assert "text/html" in resp["Content-Type"]
        assert b"Cierre de Caja" in resp.content

    def test_pdf_sin_autenticacion_falla(self, api_client, cierre_cerrado):
        url = f"/api/v1/contabilidad/cierres-caja/{cierre_cerrado.pk}/pdf/"
        resp = api_client.get(url)
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestCajaPermissions:

    def test_anonimo_no_puede_listar_cierres(self, api_client):
        resp = api_client.get("/api/v1/contabilidad/cierres-caja/")
        assert resp.status_code in (401, 403)

    def test_cajero_puede_listar_cierres(self, api_cajero):
        resp = api_cajero.get("/api/v1/contabilidad/cierres-caja/")
        assert resp.status_code == 200

    def test_cajero_puede_crear_cierre(self, api_cajero, caja, usuario_cajero):
        resp = api_cajero.post("/api/v1/contabilidad/cierres-caja/", {
            "caja": caja.pk,
            "empleado": usuario_cajero.pk,
            "monto_inicial": 50000,
        }, format="json")
        assert resp.status_code == 201


@pytest.mark.django_db
class TestCierrePDFEmpresaError:
    """Lines 262-263: except Exception: pass when DatosEmpresa.objects.first() raises."""

    def test_pdf_empresa_error_aun_retorna_html(self, api_admin, cierre_cerrado):
        from unittest.mock import patch
        url = f"/api/v1/contabilidad/cierres-caja/{cierre_cerrado.pk}/pdf/"
        with patch("apps.contabilidad.views.DatosEmpresa.objects") as mock_mgr:
            mock_mgr.first.side_effect = Exception("DB error")
            resp = api_admin.get(url)
        assert resp.status_code == 200
        assert "text/html" in resp["Content-Type"]


@pytest.mark.django_db
class TestDatosEmpresaPublico:

    def test_sin_autenticacion_devuelve_datos_publicos(self, api_client):
        from apps.contabilidad.models import DatosEmpresa
        DatosEmpresa.objects.create(
            ruc="80012345-6", razon_social="Cantina Tita S.A.",
            email="administracion@cantinatita.com", telefono="+595981410938",
            activo=True,
        )

        resp = api_client.get("/api/v1/contabilidad/datos-empresa/publico/")
        assert resp.status_code == 200
        assert resp.data == {
            "razon_social": "Cantina Tita S.A.",
            "ruc": "80012345-6",
            "email": "administracion@cantinatita.com",
            "telefono": "+595981410938",
        }

    def test_email_y_telefono_vacios_si_no_estan_cargados(self, api_client):
        from apps.contabilidad.models import DatosEmpresa
        DatosEmpresa.objects.create(ruc="80012345-6", razon_social="Cantina Tita S.A.", activo=True)

        resp = api_client.get("/api/v1/contabilidad/datos-empresa/publico/")
        assert resp.status_code == 200
        assert resp.data["email"] == ""
        assert resp.data["telefono"] == ""

    def test_sin_datos_empresa_devuelve_vacio(self, api_client):
        resp = api_client.get("/api/v1/contabilidad/datos-empresa/publico/")
        assert resp.status_code == 200
        assert resp.data == {"razon_social": "", "ruc": "", "email": "", "telefono": ""}

    def test_ignora_empresa_inactiva(self, api_client):
        from apps.contabilidad.models import DatosEmpresa
        DatosEmpresa.objects.create(ruc="1-1", razon_social="Vieja S.A.", activo=False)

        resp = api_client.get("/api/v1/contabilidad/datos-empresa/publico/")
        assert resp.status_code == 200
        assert resp.data == {"razon_social": "", "ruc": "", "email": "", "telefono": ""}

    def test_endpoint_admin_normal_sigue_protegido(self, api_client):
        resp = api_client.get("/api/v1/contabilidad/datos-empresa/")
        assert resp.status_code in (401, 403)


@pytest.fixture
def factura(db, cliente):
    from apps.contabilidad.models import Factura
    return Factura.objects.create(
        nro_factura="001-001-0000001",
        monto_total=Decimal("50000"),
        cliente=cliente,
    )


@pytest.mark.django_db
class TestFacturaPDF:
    """Lines 390-391: FacturaViewSet.pdf action including DatosEmpresa error branch."""

    def test_pdf_retorna_html(self, api_admin, factura):
        resp = api_admin.get(f"/api/v1/contabilidad/facturas/{factura.pk}/pdf/")
        assert resp.status_code == 200
        assert "text/html" in resp["Content-Type"]

    def test_pdf_empresa_error_aun_retorna_html(self, api_admin, factura):
        from unittest.mock import patch
        with patch("apps.contabilidad.views.DatosEmpresa.objects") as mock_mgr:
            mock_mgr.first.side_effect = Exception("DB error")
            resp = api_admin.get(f"/api/v1/contabilidad/facturas/{factura.pk}/pdf/")
        assert resp.status_code == 200
        assert "text/html" in resp["Content-Type"]

    def test_pdf_sin_autenticacion_falla(self, api_client, factura):
        resp = api_client.get(f"/api/v1/contabilidad/facturas/{factura.pk}/pdf/")
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestDashboardTendenciaFechaInvalida:
    """Lines 571-575: ValueError on invalid date format."""

    def test_fecha_invalida_retorna_400(self, api_admin):
        resp = api_admin.get(
            "/api/v1/contabilidad/dashboard/tendencia/",
            {"desde": "no-es-fecha", "hasta": "2026-12-31"},
        )
        assert resp.status_code == 400
        assert "inválido" in resp.data["error"].lower()

    def test_sin_params_usa_defaults(self, api_admin):
        resp = api_admin.get("/api/v1/contabilidad/dashboard/tendencia/")
        assert resp.status_code == 200
        assert "data" in resp.data

    def test_con_fechas_validas_retorna_rango(self, api_admin):
        resp = api_admin.get(
            "/api/v1/contabilidad/dashboard/tendencia/",
            {"desde": "2026-01-01", "hasta": "2026-01-07"},
        )
        assert resp.status_code == 200
        assert resp.data["dias"] == 7


@pytest.mark.django_db
class TestReporteDiferenciasCaja:
    """Lines 621-713: ReporteDiferenciasCajaView.get full coverage."""

    def test_sin_params_retorna_400(self, api_admin):
        resp = api_admin.get("/api/v1/contabilidad/reporte-diferencias-caja/")
        assert resp.status_code == 400

    def test_con_fechas_retorna_estructura(self, api_admin):
        resp = api_admin.get(
            "/api/v1/contabilidad/reporte-diferencias-caja/",
            {"desde": "2026-01-01", "hasta": "2026-12-31"},
        )
        assert resp.status_code == 200
        assert "periodo" in resp.data
        assert "resumen" in resp.data
        assert "tendencia" in resp.data
        assert "por_empleado" in resp.data

    def test_con_cierre_incluye_datos(self, api_admin, cierre_cerrado):
        resp = api_admin.get(
            "/api/v1/contabilidad/reporte-diferencias-caja/",
            {"desde": "2026-01-01", "hasta": "2099-12-31"},
        )
        assert resp.status_code == 200
        assert resp.data["resumen"]["n_cierres"] >= 1
        assert resp.data["resumen"]["total_diferencia"] == int(cierre_cerrado.diferencia_efectivo)

    def test_csv_retorna_csv(self, api_admin, cierre_cerrado):
        resp = api_admin.get(
            "/api/v1/contabilidad/reporte-diferencias-caja/",
            {"desde": "2026-01-01", "hasta": "2099-12-31", "formato": "csv"},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]
        assert b"DIFERENCIAS DE CAJA" in resp.content

    def test_anonimo_no_puede_acceder(self, api_client):
        resp = api_client.get(
            "/api/v1/contabilidad/reporte-diferencias-caja/",
            {"desde": "2026-01-01", "hasta": "2026-12-31"},
        )
        assert resp.status_code in (401, 403)
