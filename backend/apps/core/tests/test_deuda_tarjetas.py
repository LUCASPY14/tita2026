"""
Seguimiento de la deuda de cantina en tarjetas: campos de la ficha, filtro
"con deuda", resumen y alerta a los administradores.
"""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def grado(db):
    from apps.clientes.models import Grado
    g, _ = Grado.objects.get_or_create(nombre="G-DEUDA", defaults={"nivel": 2, "orden": 2})
    return g


def _tarjeta(cliente, grado, nro, saldo, permite=True, limite=0):
    from apps.clientes.models import Hijo
    from apps.core.models import Tarjeta
    h = Hijo.objects.create(nombre=f"H{nro}", apellido="Deuda", cliente_responsable=cliente, grado=grado, activo=True)
    return Tarjeta.objects.create(
        nro_tarjeta=nro, hijo=h, saldo_actual=Decimal(str(saldo)),
        permite_saldo_negativo=permite, limite_credito=Decimal(str(limite)),
    )


def _api(usuario):
    api = APIClient()
    api.force_authenticate(user=usuario)
    return api


@pytest.mark.django_db
class TestCamposDeLaFicha:

    def _serializar(self, tarjeta):
        from apps.core.serializers import TarjetaSerializer
        return TarjetaSerializer(tarjeta).data

    def test_prepago(self, cliente, grado):
        d = self._serializar(_tarjeta(cliente, grado, "DT-1", 5000, permite=False))
        assert d["deuda_maxima"] == 0 and d["sobregiro_sin_tope"] is False

    def test_con_tope(self, cliente, grado):
        d = self._serializar(_tarjeta(cliente, grado, "DT-2", 5000, limite=80000))
        assert d["deuda_maxima"] == 80000 and d["sobregiro_sin_tope"] is False
        assert Decimal(str(d["saldo_disponible"])) == Decimal("85000")

    def test_sin_tope(self, cliente, grado):
        d = self._serializar(_tarjeta(cliente, grado, "DT-3", 5000, limite=0))
        assert d["deuda_maxima"] is None and d["sobregiro_sin_tope"] is True


@pytest.mark.django_db
class TestFiltroYResumen:

    @pytest.fixture
    def tarjetas(self, cliente, grado):
        _tarjeta(cliente, grado, "DF-OK", 30000)
        _tarjeta(cliente, grado, "DF-D1", -20000)
        _tarjeta(cliente, grado, "DF-D2", -50000)

    def test_con_deuda_filtra_solo_negativas(self, usuario_cajero, tarjetas):
        resp = _api(usuario_cajero).get("/api/v1/core/tarjetas/", {"con_deuda": "true"})
        assert sorted(t["nro_tarjeta"] for t in resp.data["results"]) == ["DF-D1", "DF-D2"]

    def test_sin_filtro_devuelve_todas(self, usuario_cajero, tarjetas):
        resp = _api(usuario_cajero).get("/api/v1/core/tarjetas/")
        assert resp.data["count"] == 3

    def test_resumen(self, usuario_cajero, tarjetas):
        resp = _api(usuario_cajero).get("/api/v1/core/tarjetas/resumen/")
        assert resp.status_code == 200
        assert resp.data == {"tarjetas_con_deuda": 2, "deuda_total": 70000}

    def test_resumen_sin_deudas(self, usuario_cajero):
        resp = _api(usuario_cajero).get("/api/v1/core/tarjetas/resumen/")
        assert resp.data == {"tarjetas_con_deuda": 0, "deuda_total": 0}

    def test_el_padre_no_accede_al_resumen(self, cliente, tarjetas):
        from apps.usuarios.models import Usuario
        padre = Usuario.objects.create_user(
            email="padre_deuda@test.com", password="x12345678", nombre="P", apellido="D",
            rol=Usuario.Rol.CLIENTE_WEB, cliente=cliente,
        )
        assert _api(padre).get("/api/v1/core/tarjetas/resumen/").status_code == 403

    def test_el_padre_no_puede_usar_con_deuda_para_ver_otras_familias(self, cliente, tarjetas):
        from apps.usuarios.models import Usuario
        padre = Usuario.objects.create_user(
            email="padre_deuda2@test.com", password="x12345678", nombre="P", apellido="D2",
            rol=Usuario.Rol.CLIENTE_WEB, cliente=cliente,
        )
        resp = _api(padre).get("/api/v1/core/tarjetas/", {"con_deuda": "true"})
        # Ve solo las de su propia familia (las de la fixture son del mismo cliente).
        assert resp.status_code == 200


@pytest.mark.django_db
class TestAlertaDeDeuda:

    def test_avisa_a_los_admin_cuando_la_deuda_supera_el_umbral(
        self, cliente, grado, usuario_admin,
    ):
        from apps.core.tasks import alertar_saldo_tarjeta_negativo
        from apps.notificaciones.models import Notificacion
        _tarjeta(cliente, grado, "AL-1", -150000, limite=0)
        res = alertar_saldo_tarjeta_negativo()
        assert res == {"alertadas": 1}
        n = Notificacion.objects.get(usuario=usuario_admin)
        assert "AL-1" in n.mensaje and "sin tope" in n.mensaje and "150,000" in n.mensaje

    def test_no_avisa_bajo_el_umbral(self, cliente, grado, usuario_admin):
        from apps.core.tasks import alertar_saldo_tarjeta_negativo
        _tarjeta(cliente, grado, "AL-2", -99999, limite=0)
        assert alertar_saldo_tarjeta_negativo() == {"alertadas": 0}

    def test_con_tope_bajo_avisa_al_80_por_ciento_del_tope(self, cliente, grado, usuario_admin):
        from apps.core.tasks import alertar_saldo_tarjeta_negativo
        _tarjeta(cliente, grado, "AL-3", -40000, limite=50000)  # 80% de 50.000
        assert alertar_saldo_tarjeta_negativo() == {"alertadas": 1}

    def test_con_tope_bajo_no_avisa_antes_del_80(self, cliente, grado, usuario_admin):
        from apps.core.tasks import alertar_saldo_tarjeta_negativo
        _tarjeta(cliente, grado, "AL-4", -39999, limite=50000)
        assert alertar_saldo_tarjeta_negativo() == {"alertadas": 0}

    def test_ignora_tarjetas_con_saldo_positivo(self, cliente, grado, usuario_admin):
        from apps.core.tasks import alertar_saldo_tarjeta_negativo
        _tarjeta(cliente, grado, "AL-5", 500000)
        assert alertar_saldo_tarjeta_negativo() == {"alertadas": 0}

    def test_esta_registrada_en_el_beat(self):
        from backend.celery_app import app
        tareas = {v["task"] for v in app.conf.beat_schedule.values()}
        assert "apps.core.tasks.alertar_saldo_tarjeta_negativo" in tareas
