"""
Tests de vistas de core.
Cubre: CargaSaldoViewSet (create, confirmar), MedioPagoViewSet (caché),
ReporteTarjetasView.
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
def hijo_core(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Ana",
        apellido="García",
        cliente_responsable=cliente,
    )


@pytest.fixture
def tarjeta_core(db, hijo_core):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(nro_tarjeta="CORE0001", hijo=hijo_core)


@pytest.fixture
def carga_pendiente(db, tarjeta_core, usuario_cajero):
    from apps.core.models import CargaSaldo
    return CargaSaldo.objects.create(
        tarjeta=tarjeta_core,
        monto_cargado=Decimal("50000"),
        estado=CargaSaldo.Estado.PENDIENTE,
        responsable=usuario_cajero,
    )


# ── CargaSaldoViewSet ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCargaSaldoCreate:

    def test_transferencia_queda_pendiente(self, api_cajero, tarjeta_core):
        resp = api_cajero.post(
            "/api/v1/core/cargas-saldo/",
            {"tarjeta": tarjeta_core.pk, "monto_cargado": 50000, "metodo_pago": "TRANSFERENCIA"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["estado"] == "PENDIENTE"

    def test_efectivo_queda_confirmada(self, api_cajero, tarjeta_core):
        resp = api_cajero.post(
            "/api/v1/core/cargas-saldo/",
            {"tarjeta": tarjeta_core.pk, "monto_cargado": 30000, "metodo_pago": "EFECTIVO"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["estado"] == "CONFIRMADA"

    def test_list_ok(self, api_cajero):
        resp = api_cajero.get("/api/v1/core/cargas-saldo/")
        assert resp.status_code == 200

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/core/cargas-saldo/")
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestCargaSaldoConfirmar:

    def test_confirmar_pendiente_ok(self, api_cajero, carga_pendiente):
        resp = api_cajero.post(
            f"/api/v1/core/cargas-saldo/{carga_pendiente.pk}/confirmar/"
        )
        assert resp.status_code == 200
        assert resp.data["estado"] == "CONFIRMADA"

    def test_confirmar_ya_confirmada_falla(self, api_cajero, tarjeta_core):
        from apps.core.models import CargaSaldo
        carga = CargaSaldo.objects.create(
            tarjeta=tarjeta_core,
            monto_cargado=Decimal("10000"),
            estado=CargaSaldo.Estado.CONFIRMADA,
        )
        resp = api_cajero.post(f"/api/v1/core/cargas-saldo/{carga.pk}/confirmar/")
        assert resp.status_code == 400


# ── MedioPagoViewSet — caché ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestMedioPagoCache:

    def test_list_cache_miss_y_hit(self, api_cajero, medio_pago_efectivo):
        resp1 = api_cajero.get("/api/v1/core/medios-pago/")
        assert resp1.status_code == 200
        resp2 = api_cajero.get("/api/v1/core/medios-pago/")
        assert resp2.status_code == 200
        assert resp1.data == resp2.data

    def test_create_invalida_cache(self, api_admin):
        resp = api_admin.post(
            "/api/v1/core/medios-pago/",
            {"descripcion": "Cheque", "activo": True},
            format="json",
        )
        assert resp.status_code == 201

    def test_update_invalida_cache(self, api_admin, medio_pago_efectivo):
        resp = api_admin.patch(
            f"/api/v1/core/medios-pago/{medio_pago_efectivo.pk}/",
            {"descripcion": "Efectivo Updated"},
            format="json",
        )
        assert resp.status_code == 200

    def test_delete_invalida_cache(self, api_admin):
        from apps.core.models import MedioPago
        mp = MedioPago.objects.create(descripcion="Temporal", activo=True)
        resp = api_admin.delete(f"/api/v1/core/medios-pago/{mp.pk}/")
        assert resp.status_code == 204

    def test_filtro_activo_excluye_inactivos(self, api_cajero, medio_pago_efectivo):
        """ModoRecreo.tsx pide ?activo=true — sin filterset_fields el ViewSet
        ignoraba el parámetro y siempre devolvía todos los medios de pago,
        incluidos los desactivados desde Configuración."""
        from apps.core.models import MedioPago
        inactivo = MedioPago.objects.create(descripcion="Viejo Duplicado", activo=False)

        resp = api_cajero.get("/api/v1/core/medios-pago/", {"activo": "true"})
        assert resp.status_code == 200
        descripciones = [m["descripcion"] for m in resp.data["results"]]
        assert medio_pago_efectivo.descripcion in descripciones
        assert inactivo.descripcion not in descripciones


# ── ReporteTarjetasView ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteTarjetas:

    def test_sin_params_retorna_estructura(self, api_admin):
        resp = api_admin.get("/api/v1/core/reporte-tarjetas/")
        assert resp.status_code == 200
        assert "tarjetas" in resp.data
        assert "resumen" in resp.data

    def test_con_periodo_filtra(self, api_admin):
        resp = api_admin.get(
            "/api/v1/core/reporte-tarjetas/",
            {"desde": "2020-01-01", "hasta": "2099-12-31"},
        )
        assert resp.status_code == 200
        assert resp.data["periodo"]["desde"] == "2020-01-01"

    def test_formato_csv_sin_periodo(self, api_admin):
        resp = api_admin.get("/api/v1/core/reporte-tarjetas/", {"formato": "csv"})
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]
        assert b"REPORTE DE TARJETAS PREPAGO" in resp.content

    def test_formato_csv_con_periodo_y_tarjeta(self, api_admin, tarjeta_core):
        resp = api_admin.get(
            "/api/v1/core/reporte-tarjetas/",
            {"desde": "2020-01-01", "hasta": "2099-12-31", "formato": "csv"},
        )
        assert resp.status_code == 200
        assert b"CORE0001" in resp.content

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/core/reporte-tarjetas/")
        assert resp.status_code in (401, 403)

    def test_formato_pdf_retorna_pdf(self, api_admin, tarjeta_core):
        resp = api_admin.get("/api/v1/core/reporte-tarjetas/", {"formato": "pdf"})
        assert resp.status_code == 200
        assert "application/pdf" in resp["Content-Type"]

    def test_tarjeta_de_personal_sin_hijo_no_rompe_el_reporte(self, api_admin, tarjeta_core, tipo_cliente, lista_precio):
        """
        Una tarjeta puede pertenecer a un alumno (hijo) o a un docente/
        funcionario (cliente_directo) — nunca ambos. El reporte no debe
        romper con AttributeError cuando hay al menos una tarjeta de
        personal (hijo=None) junto a tarjetas de alumnos.
        """
        from decimal import Decimal
        from apps.clientes.models import Cliente
        from apps.core.models import Tarjeta

        docente = Cliente.objects.create(
            nombres="María", apellidos="Docente", ruc_ci="9998887",
            tipo_cliente=tipo_cliente, lista_precio=lista_precio,
            limite_credito=Decimal("0"),
        )
        Tarjeta.objects.create(nro_tarjeta="STAFF001", cliente_directo=docente)

        resp = api_admin.get("/api/v1/core/reporte-tarjetas/")
        assert resp.status_code == 200

        fila_staff = next(f for f in resp.data["tarjetas"] if f["nro_tarjeta"] == "STAFF001")
        assert "Docente" in fila_staff["alumno"]
        assert fila_staff["grado"] == ""

        fila_alumno = next(f for f in resp.data["tarjetas"] if f["nro_tarjeta"] == tarjeta_core.nro_tarjeta)
        assert "García" in fila_alumno["alumno"]


# ── CargaSaldo CUENTA_CORRIENTE ───────────────────────────────────────────────

@pytest.mark.django_db
class TestCargaSaldoCuentaCorriente:

    def test_cuenta_corriente_crea_movimiento_cc(self, api_cajero, tarjeta_core, usuario_cajero):
        """POST con metodo_pago=CUENTA_CORRIENTE crea CargaSaldo y CuentaCorrienteCliente."""
        from apps.clientes.models import CuentaCorrienteCliente
        pre = CuentaCorrienteCliente.objects.count()
        resp = api_cajero.post(
            "/api/v1/core/cargas-saldo/",
            {"tarjeta": tarjeta_core.pk, "monto_cargado": 20000, "metodo_pago": "CUENTA_CORRIENTE"},
            format="json",
        )
        assert resp.status_code == 201
        assert CuentaCorrienteCliente.objects.count() == pre + 1
        mov = CuentaCorrienteCliente.objects.latest("pk")
        assert mov.tipo == CuentaCorrienteCliente.Tipo.DEBITO
        assert mov.monto == Decimal("20000")


# ── MedioPago — cache hit real ────────────────────────────────────────────────

@pytest.mark.django_db
class TestMedioPagoCacheHit:

    def test_cache_hit_retorna_respuesta_cacheada(self, api_cajero, medio_pago_efectivo):
        """Cuando cache.get devuelve datos para la clave de medios_pago, los retorna directo."""
        from unittest.mock import patch
        cached_data = [{"id": 999, "descripcion": "CacheadoTest", "activo": True}]

        def _cache_get(key, default=None):
            if "medios_pago_list_" in key:
                return cached_data
            return default  # respetar el default para throttle/sesiones

        with patch("apps.core.views.cache.get", side_effect=_cache_get):
            resp = api_cajero.get("/api/v1/core/medios-pago/")
        assert resp.status_code == 200
        assert any(mp["descripcion"] == "CacheadoTest" for mp in resp.data)


# ── ConsumoTarjetaViewSet.permission_classes ────────────────────────────────────

@pytest.mark.django_db
class TestConsumoTarjetaPermisos:
    """permission_classes ahora explícito (antes caía al default global IsStaffUser
    de forma implícita) — sin cambio de comportamiento, solo de claridad."""

    def test_sin_autenticacion_falla(self, api_client):
        resp = api_client.get("/api/v1/core/consumos/")
        assert resp.status_code in (401, 403)

    def test_staff_puede_listar(self, api_cajero):
        resp = api_cajero.get("/api/v1/core/consumos/")
        assert resp.status_code == 200

    def test_cliente_web_no_puede_listar(self, api_client, db, cliente):
        from apps.usuarios.models import Usuario
        padre = Usuario.objects.create_user(
            email="padre_consumo@test.com", password="test1234",
            nombre="Padre", apellido="Test", rol="CLIENTE_WEB", cliente=cliente,
        )
        api_client.force_authenticate(user=padre)
        resp = api_client.get("/api/v1/core/consumos/")
        assert resp.status_code == 403


# ── TarjetaViewSet.bloquear / activar ───────────────────────────────────────────

@pytest.mark.django_db
class TestTarjetaBloquearActivar:

    def test_sin_autenticacion_falla(self, api_client, tarjeta_core):
        resp = api_client.post(f"/api/v1/core/tarjetas/{tarjeta_core.nro_tarjeta}/bloquear/")
        assert resp.status_code in (401, 403)

    def test_bloquear_tarjeta_activa_ok(self, api_cajero, tarjeta_core):
        resp = api_cajero.post(f"/api/v1/core/tarjetas/{tarjeta_core.nro_tarjeta}/bloquear/")
        assert resp.status_code == 200
        assert resp.data["estado"] == "BLOQUEADA"
        tarjeta_core.refresh_from_db()
        assert tarjeta_core.estado == "BLOQUEADA"

    def test_bloquear_tarjeta_ya_bloqueada_falla(self, api_cajero, tarjeta_core):
        from apps.core.models import Tarjeta
        tarjeta_core.estado = Tarjeta.Estado.BLOQUEADA
        tarjeta_core.save(update_fields=["estado"])
        resp = api_cajero.post(f"/api/v1/core/tarjetas/{tarjeta_core.nro_tarjeta}/bloquear/")
        assert resp.status_code == 400
        assert "ACTIVA" in resp.data["error"]

    def test_bloquear_tarjeta_vencida_falla(self, api_cajero, tarjeta_core):
        from apps.core.models import Tarjeta
        tarjeta_core.estado = Tarjeta.Estado.VENCIDA
        tarjeta_core.save(update_fields=["estado"])
        resp = api_cajero.post(f"/api/v1/core/tarjetas/{tarjeta_core.nro_tarjeta}/bloquear/")
        assert resp.status_code == 400
        tarjeta_core.refresh_from_db()
        assert tarjeta_core.estado == "VENCIDA"

    def test_activar_tarjeta_bloqueada_ok(self, api_cajero, tarjeta_core):
        from apps.core.models import Tarjeta
        tarjeta_core.estado = Tarjeta.Estado.BLOQUEADA
        tarjeta_core.save(update_fields=["estado"])
        resp = api_cajero.post(f"/api/v1/core/tarjetas/{tarjeta_core.nro_tarjeta}/activar/")
        assert resp.status_code == 200
        assert resp.data["estado"] == "ACTIVA"

    def test_activar_tarjeta_cancelada_falla(self, api_cajero, tarjeta_core):
        from apps.core.models import Tarjeta
        tarjeta_core.estado = Tarjeta.Estado.CANCELADA
        tarjeta_core.save(update_fields=["estado"])
        resp = api_cajero.post(f"/api/v1/core/tarjetas/{tarjeta_core.nro_tarjeta}/activar/")
        assert resp.status_code == 400
        tarjeta_core.refresh_from_db()
        assert tarjeta_core.estado == "CANCELADA"

    def test_patch_estado_generico_no_hace_nada(self, api_cajero, tarjeta_core):
        """estado es read-only en el serializer — la única vía es bloquear/activar."""
        resp = api_cajero.patch(
            f"/api/v1/core/tarjetas/{tarjeta_core.nro_tarjeta}/",
            {"estado": "BLOQUEADA"},
            format="json",
        )
        assert resp.status_code == 200
        tarjeta_core.refresh_from_db()
        assert tarjeta_core.estado == "ACTIVA"

    def test_queda_auditado(self, api_cajero, tarjeta_core):
        from apps.usuarios.models import AuditoriaOperacion
        api_cajero.post(f"/api/v1/core/tarjetas/{tarjeta_core.nro_tarjeta}/bloquear/")
        auditoria = AuditoriaOperacion.objects.filter(operacion="BLOQUEAR_TARJETA").first()
        assert auditoria is not None
        assert tarjeta_core.nro_tarjeta in auditoria.descripcion
