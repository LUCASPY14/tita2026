"""
Tests de vistas de clientes.
Cubre: ClienteViewSet (reset_pin, cambiar_pin), HijoViewSet (CLIENTE_WEB filter),
RestriccionHijoViewSet, AlumnoResponsableViewSet (perform_create, destroy, set_titular),
ReporteCuentaCorrienteView, y ViewSets simples.
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
def hijo_fixture(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Pedro",
        apellido="López",
        cliente_responsable=cliente,
    )


@pytest.fixture
def alumno_responsable(db, hijo_fixture, cliente, usuario_admin):
    from apps.clientes.models import AlumnoResponsable
    return AlumnoResponsable.objects.create(
        hijo=hijo_fixture,
        cliente=cliente,
        parentesco="PADRE",
        es_titular=True,
        orden_cobro=1,
        agregado_por=usuario_admin,
    )


@pytest.fixture
def usuario_cliente_web(db, cliente):
    from apps.usuarios.models import Usuario
    return Usuario.objects.create_user(
        email="web@clientes.test",
        password="test1234",
        nombre="Web",
        apellido="Cliente",
        rol=Usuario.Rol.CLIENTE_WEB,
        cliente=cliente,
    )


@pytest.fixture
def api_cliente_web(api_client, usuario_cliente_web):
    api_client.force_authenticate(user=usuario_cliente_web)
    return api_client


@pytest.fixture
def cuenta_con_deuda(db, cliente, usuario_cajero):
    from apps.clientes.models import CuentaCorrienteCliente
    return CuentaCorrienteCliente.objects.create(
        cliente=cliente,
        tipo=CuentaCorrienteCliente.Tipo.DEBITO,
        monto=Decimal("50000"),
        saldo_anterior=Decimal("0"),
        saldo_resultante=Decimal("50000"),
        descripcion="Venta fiado test",
        creado_por=usuario_cajero,
    )


# ── ViewSets simples ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestViewSetsSimples:

    def test_clientes_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/clientes/clientes/")
        assert resp.status_code == 200

    def test_tipos_cliente_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/clientes/tipos-cliente/")
        assert resp.status_code == 200

    def test_hijos_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/clientes/hijos/")
        assert resp.status_code == 200

    def test_grados_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/clientes/grados/")
        assert resp.status_code == 200

    def test_historial_grados_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/clientes/historial-grados/")
        assert resp.status_code == 200

    def test_restricciones_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/clientes/restricciones/")
        assert resp.status_code == 200

    def test_autorizaciones_saldo_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/clientes/autorizaciones-saldo/")
        assert resp.status_code == 200

    def test_paises_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/clientes/paises/")
        assert resp.status_code == 200

    def test_ciudades_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/clientes/ciudades/")
        assert resp.status_code == 200

    def test_cuentas_corrientes_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/clientes/cuentas-corrientes/")
        assert resp.status_code == 200

    def test_responsables_list(self, api_admin):
        resp = api_admin.get("/api/v1/clientes/responsables/")
        assert resp.status_code == 200

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/clientes/clientes/")
        assert resp.status_code in (401, 403)


# ── ClienteViewSet — reset_pin ────────────────────────────────────────────────

@pytest.mark.django_db
class TestResetPin:

    def test_admin_puede_resetear(self, api_admin, cliente):
        resp = api_admin.post(f"/api/v1/clientes/clientes/{cliente.pk}/reset-pin/")
        assert resp.status_code == 200
        assert resp.data["ok"] is True

    def test_cajero_no_puede_resetear(self, api_cajero, cliente):
        resp = api_cajero.post(f"/api/v1/clientes/clientes/{cliente.pk}/reset-pin/")
        assert resp.status_code == 403


# ── ClienteViewSet — cambiar_pin ──────────────────────────────────────────────

@pytest.mark.django_db
class TestCambiarPin:

    def test_admin_cambia_sin_pin_actual(self, api_admin, cliente):
        resp = api_admin.post(
            f"/api/v1/clientes/clientes/{cliente.pk}/cambiar-pin/",
            {"pin_nuevo": "9876"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["ok"] is True

    def test_pin_nuevo_invalido_falla(self, api_admin, cliente):
        resp = api_admin.post(
            f"/api/v1/clientes/clientes/{cliente.pk}/cambiar-pin/",
            {"pin_nuevo": "abc"},
            format="json",
        )
        assert resp.status_code == 400

    def test_pin_nuevo_corto_falla(self, api_admin, cliente):
        resp = api_admin.post(
            f"/api/v1/clientes/clientes/{cliente.pk}/cambiar-pin/",
            {"pin_nuevo": "12"},
            format="json",
        )
        assert resp.status_code == 400

    def test_no_admin_no_puede_cambiar_pin(self, api_cajero, cliente):
        # cambiar_pin usa IsAuthenticated; cajero puede llamarlo pero
        # sin pin_actual recibe 400 (PIN actual incorrecto)
        resp = api_cajero.post(
            f"/api/v1/clientes/clientes/{cliente.pk}/cambiar-pin/",
            {"pin_nuevo": "5678"},
            format="json",
        )
        assert resp.status_code in (400, 403)

    def test_cliente_web_no_puede_cambiar_pin_ajeno(self, api_cliente_web, tipo_cliente, lista_precio):
        from apps.clientes.models import Cliente
        otro = Cliente.objects.create(
            nombres="Otro",
            apellidos="Cliente",
            ruc_ci="9999999",
            tipo_cliente=tipo_cliente,
            lista_precio=lista_precio,
        )
        resp = api_cliente_web.post(
            f"/api/v1/clientes/clientes/{otro.pk}/cambiar-pin/",
            {"pin_nuevo": "1111"},
            format="json",
        )
        assert resp.status_code == 403


# ── HijoViewSet — CLIENTE_WEB filter ─────────────────────────────────────────

@pytest.mark.django_db
class TestHijoViewSetClienteWeb:

    def test_cliente_web_ve_solo_sus_hijos(self, api_cliente_web, hijo_fixture):
        resp = api_cliente_web.get("/api/v1/clientes/hijos/")
        assert resp.status_code == 200
        ids = [h["id"] for h in resp.data["results"]] if "results" in resp.data else [h["id"] for h in resp.data]
        assert hijo_fixture.pk in ids

    def test_cliente_web_sin_cliente_ve_nada(self, api_client, db):
        from apps.usuarios.models import Usuario
        user = Usuario.objects.create_user(
            email="sincliente@test.com", password="x",
            nombre="Sin", apellido="Cliente",
            rol=Usuario.Rol.CLIENTE_WEB,
        )
        api_client.force_authenticate(user=user)
        resp = api_client.get("/api/v1/clientes/hijos/")
        assert resp.status_code == 200
        data = resp.data.get("results", resp.data)
        assert len(data) == 0


# ── RestriccionHijoViewSet — CLIENTE_WEB filter ───────────────────────────────

@pytest.mark.django_db
class TestRestriccionClienteWeb:

    def test_cliente_web_sin_cliente_ve_nada(self, api_client, db):
        from apps.usuarios.models import Usuario
        user = Usuario.objects.create_user(
            email="sincliente2@test.com", password="x",
            nombre="Sin", apellido="Cliente",
            rol=Usuario.Rol.CLIENTE_WEB,
        )
        api_client.force_authenticate(user=user)
        resp = api_client.get("/api/v1/clientes/restricciones/")
        assert resp.status_code == 200
        data = resp.data.get("results", resp.data)
        assert len(data) == 0

    def test_cliente_web_con_cliente_lista_sus_restricciones(self, api_cliente_web):
        resp = api_cliente_web.get("/api/v1/clientes/restricciones/")
        assert resp.status_code == 200


# ── AlumnoResponsableViewSet ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestAlumnoResponsable:

    def test_create_asigna_agregado_por(self, api_admin, hijo_fixture, cliente):
        resp = api_admin.post(
            "/api/v1/clientes/responsables/",
            {
                "hijo": hijo_fixture.pk,
                "cliente": cliente.pk,
                "parentesco": "MADRE",
                "es_titular": False,
                "orden_cobro": 2,
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_destroy_ultimo_titular_falla(self, api_admin, alumno_responsable):
        resp = api_admin.delete(f"/api/v1/clientes/responsables/{alumno_responsable.pk}/")
        assert resp.status_code == 400

    def test_destroy_no_unico_ok(self, api_admin, hijo_fixture, cliente, usuario_admin):
        from apps.clientes.models import AlumnoResponsable
        # Crear un segundo responsable para que el primero no sea el único
        otro = AlumnoResponsable.objects.create(
            hijo=hijo_fixture, cliente=cliente, parentesco="MADRE",
            es_titular=False, orden_cobro=2, agregado_por=usuario_admin,
        )
        resp = api_admin.delete(f"/api/v1/clientes/responsables/{otro.pk}/")
        assert resp.status_code == 204

    def test_set_titular_ok(self, api_admin, alumno_responsable):
        resp = api_admin.post(
            f"/api/v1/clientes/responsables/{alumno_responsable.pk}/set_titular/"
        )
        assert resp.status_code == 200


# ── ReporteCuentaCorrienteView ────────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteCuentaCorriente:

    def test_json_sin_deudas(self, api_admin):
        resp = api_admin.get("/api/v1/clientes/reporte-cuenta-corriente/")
        assert resp.status_code == 200
        assert "resumen" in resp.data
        assert "detalle" in resp.data

    def test_json_con_deuda(self, api_admin, cuenta_con_deuda):
        resp = api_admin.get("/api/v1/clientes/reporte-cuenta-corriente/")
        assert resp.status_code == 200
        assert resp.data["resumen"]["clientes_con_deuda"] >= 1

    def test_csv_format(self, api_admin):
        resp = api_admin.get(
            "/api/v1/clientes/reporte-cuenta-corriente/",
            {"formato": "csv"},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]
        assert b"REPORTE CUENTA CORRIENTE" in resp.content

    def test_csv_con_deuda_incluye_cliente(self, api_admin, cuenta_con_deuda):
        resp = api_admin.get(
            "/api/v1/clientes/reporte-cuenta-corriente/",
            {"formato": "csv"},
        )
        assert resp.status_code == 200
        assert b"Juan" in resp.content

    def test_aging_buckets_31_60(self, api_admin, cliente, usuario_cajero):
        from apps.clientes.models import CuentaCorrienteCliente
        from django.utils import timezone
        import datetime
        fecha_vieja = timezone.now() - datetime.timedelta(days=45)
        CuentaCorrienteCliente.objects.create(
            cliente=cliente, tipo=CuentaCorrienteCliente.Tipo.DEBITO,
            monto=Decimal("10000"), saldo_anterior=Decimal("0"),
            saldo_resultante=Decimal("10000"), descripcion="Deuda 45d",
            creado_por=usuario_cajero, fecha=fecha_vieja,
        )
        resp = api_admin.get("/api/v1/clientes/reporte-cuenta-corriente/")
        assert resp.status_code == 200
        detalle = resp.data.get("detalle", [])
        assert any(d.get("aging") == "31-60" for d in detalle)

    def test_aging_buckets_61_90(self, api_admin, cliente, usuario_cajero):
        from apps.clientes.models import CuentaCorrienteCliente
        from django.utils import timezone
        import datetime
        fecha_vieja = timezone.now() - datetime.timedelta(days=75)
        CuentaCorrienteCliente.objects.create(
            cliente=cliente, tipo=CuentaCorrienteCliente.Tipo.DEBITO,
            monto=Decimal("10000"), saldo_anterior=Decimal("0"),
            saldo_resultante=Decimal("10000"), descripcion="Deuda 75d",
            creado_por=usuario_cajero, fecha=fecha_vieja,
        )
        resp = api_admin.get("/api/v1/clientes/reporte-cuenta-corriente/")
        assert resp.status_code == 200
        detalle = resp.data.get("detalle", [])
        assert any(d.get("aging") == "61-90" for d in detalle)

    def test_aging_buckets_90_plus(self, api_admin, cliente, usuario_cajero):
        from apps.clientes.models import CuentaCorrienteCliente
        from django.utils import timezone
        import datetime
        fecha_vieja = timezone.now() - datetime.timedelta(days=120)
        CuentaCorrienteCliente.objects.create(
            cliente=cliente, tipo=CuentaCorrienteCliente.Tipo.DEBITO,
            monto=Decimal("10000"), saldo_anterior=Decimal("0"),
            saldo_resultante=Decimal("10000"), descripcion="Deuda 120d",
            creado_por=usuario_cajero, fecha=fecha_vieja,
        )
        resp = api_admin.get("/api/v1/clientes/reporte-cuenta-corriente/")
        assert resp.status_code == 200
        detalle = resp.data.get("detalle", [])
        assert any(d.get("aging") == "90+" for d in detalle)

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/clientes/reporte-cuenta-corriente/")
        assert resp.status_code in (401, 403)
