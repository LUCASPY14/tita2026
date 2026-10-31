"""
Tests de ConfiguracionAlmuerzo: el rango de grados habilitados para cargar
saldo de almuerzo, su endpoint de administración y la validación que bloquea
la recarga (panel interno y Bancard) cuando el grado del alumno queda afuera.
"""

import pytest
from rest_framework.test import APIClient

from apps.almuerzos.validators import motivo_grado_no_habilitado_almuerzo


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
def grado_inicial(db):
    from apps.clientes.models import Grado
    return Grado.objects.create(nombre="1° Grado Config", nivel=1, orden=1, activo=True)


@pytest.fixture
def grado_medio(db):
    from apps.clientes.models import Grado
    return Grado.objects.create(nombre="5° Grado Config", nivel=5, orden=5, activo=True)


@pytest.fixture
def grado_final(db):
    from apps.clientes.models import Grado
    return Grado.objects.create(nombre="9° Grado Config", nivel=9, orden=9, activo=True)


@pytest.fixture
def hijo_grado_medio(db, cliente, grado_medio):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Lucía", apellido="Medio", cliente_responsable=cliente,
        grado=grado_medio, activo=True,
    )


@pytest.fixture
def hijo_grado_final(db, cliente, grado_final):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Bruno", apellido="Final", cliente_responsable=cliente,
        grado=grado_final, activo=True,
    )


@pytest.fixture
def hijo_sin_grado(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Noa", apellido="SinGrado", cliente_responsable=cliente, activo=True,
    )


@pytest.mark.django_db
class TestMotivoGradoNoHabilitadoAlmuerzo:

    def test_sin_configuracion_no_restringe(self, hijo_grado_medio):
        assert motivo_grado_no_habilitado_almuerzo(hijo_grado_medio) is None

    def test_grado_dentro_del_rango(self, hijo_grado_medio, grado_inicial, grado_final):
        from apps.almuerzos.models import ConfiguracionAlmuerzo
        ConfiguracionAlmuerzo.objects.create(grado_desde=grado_inicial, grado_hasta=grado_final)
        assert motivo_grado_no_habilitado_almuerzo(hijo_grado_medio) is None

    def test_grado_fuera_del_rango(self, hijo_grado_final, grado_inicial, grado_medio):
        from apps.almuerzos.models import ConfiguracionAlmuerzo
        ConfiguracionAlmuerzo.objects.create(grado_desde=grado_inicial, grado_hasta=grado_medio)
        motivo = motivo_grado_no_habilitado_almuerzo(hijo_grado_final)
        assert motivo is not None
        assert "9° Grado Config" in motivo

    def test_hijo_sin_grado_no_se_bloquea(self, hijo_sin_grado, grado_inicial, grado_medio):
        from apps.almuerzos.models import ConfiguracionAlmuerzo
        ConfiguracionAlmuerzo.objects.create(grado_desde=grado_inicial, grado_hasta=grado_medio)
        assert motivo_grado_no_habilitado_almuerzo(hijo_sin_grado) is None

    def test_configuracion_con_un_solo_extremo_no_restringe(self, hijo_grado_final, grado_inicial):
        from apps.almuerzos.models import ConfiguracionAlmuerzo
        ConfiguracionAlmuerzo.objects.create(grado_desde=grado_inicial, grado_hasta=None)
        assert motivo_grado_no_habilitado_almuerzo(hijo_grado_final) is None


@pytest.mark.django_db
class TestConfiguracionAlmuerzoEndpoint:

    def test_admin_puede_crear_el_rango(self, api_admin, grado_inicial, grado_final):
        resp = api_admin.post(
            "/api/v1/almuerzos/configuracion/",
            {"grado_desde": grado_inicial.pk, "grado_hasta": grado_final.pk},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["grado_desde_nombre"] == grado_inicial.nombre
        assert resp.data["grado_hasta_nombre"] == grado_final.nombre

    def test_cajero_no_puede_editar(self, api_cajero, grado_inicial, grado_final):
        resp = api_cajero.post(
            "/api/v1/almuerzos/configuracion/",
            {"grado_desde": grado_inicial.pk, "grado_hasta": grado_final.pk},
            format="json",
        )
        assert resp.status_code == 403

    def test_cajero_puede_leer(self, api_cajero):
        resp = api_cajero.get("/api/v1/almuerzos/configuracion/")
        assert resp.status_code == 200

    def test_rechaza_desde_posterior_a_hasta(self, api_admin, grado_inicial, grado_final):
        resp = api_admin.post(
            "/api/v1/almuerzos/configuracion/",
            {"grado_desde": grado_final.pk, "grado_hasta": grado_inicial.pk},
            format="json",
        )
        assert resp.status_code == 400

    def test_rechaza_un_solo_extremo(self, api_admin, grado_inicial):
        resp = api_admin.post(
            "/api/v1/almuerzos/configuracion/",
            {"grado_desde": grado_inicial.pk},
            format="json",
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestRecargaSaldoAlmuerzoBloqueadaPorGrado:

    def test_bloquea_la_recarga_si_el_grado_esta_fuera_de_rango(
        self, api_cajero, hijo_grado_final, grado_inicial, grado_medio,
    ):
        from apps.almuerzos.models import ConfiguracionAlmuerzo, SaldoAlmuerzo
        ConfiguracionAlmuerzo.objects.create(grado_desde=grado_inicial, grado_hasta=grado_medio)

        resp = api_cajero.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo_grado_final.pk, "monto_cargado": "10000", "metodo_pago": "EFECTIVO"},
            format="json",
        )
        assert resp.status_code == 400
        assert "no está habilitado" in resp.data["detail"]
        assert not SaldoAlmuerzo.objects.filter(hijo=hijo_grado_final).exists()

    def test_permite_la_recarga_si_el_grado_esta_dentro_de_rango(
        self, api_cajero, hijo_grado_medio, grado_inicial, grado_final,
    ):
        from apps.almuerzos.models import ConfiguracionAlmuerzo
        ConfiguracionAlmuerzo.objects.create(grado_desde=grado_inicial, grado_hasta=grado_final)

        resp = api_cajero.post(
            "/api/v1/almuerzos/recargas-saldo/",
            {"hijo": hijo_grado_medio.pk, "monto_cargado": "10000", "metodo_pago": "EFECTIVO"},
            format="json",
        )
        assert resp.status_code == 201
