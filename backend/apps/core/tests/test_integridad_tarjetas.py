"""
Fase 0 — integridad de saldos.

El saldo de una tarjeta solo cambia por operaciones que dejan movimiento
(carga, venta, reverso, ajuste). Los campos con impacto económico (sobregiro,
límite, vencimiento, titular) solo los cambian ADMIN/SUPERVISOR, y el libro
mayor y las cargas registradas no se editan ni se borran por la API genérica.
"""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient


def _api(usuario):
    api = APIClient()
    api.force_authenticate(user=usuario)
    return api


@pytest.fixture
def usuario_supervisor(db):
    from apps.usuarios.models import Usuario
    return Usuario.objects.create_user(
        email="sup_integridad@test.com", password="test1234",
        nombre="Sup", apellido="Test", rol=Usuario.Rol.SUPERVISOR,
    )


@pytest.fixture
def tarjeta(db, cliente):
    from apps.clientes.models import Grado, Hijo
    from apps.core.models import Tarjeta
    grado, _ = Grado.objects.get_or_create(nombre="G-INT", defaults={"nivel": 2, "orden": 2})
    hijo = Hijo.objects.create(
        nombre="Int", apellido="Egridad", cliente_responsable=cliente, grado=grado, activo=True,
    )
    return Tarjeta.objects.create(nro_tarjeta="INT-1", hijo=hijo, saldo_actual=Decimal("1000"))


def _url(t):
    return f"/api/v1/core/tarjetas/{t.nro_tarjeta}/"


@pytest.mark.django_db
class TestSaldoNoEditable:

    def test_patch_de_saldo_actual_se_ignora(self, usuario_cajero, tarjeta):
        resp = _api(usuario_cajero).patch(_url(tarjeta), {"saldo_actual": 999999}, format="json")
        tarjeta.refresh_from_db()
        assert resp.status_code == 200
        assert tarjeta.saldo_actual == Decimal("1000")

    def test_ni_el_admin_puede_editar_el_saldo_a_mano(self, usuario_admin, tarjeta):
        _api(usuario_admin).patch(_url(tarjeta), {"saldo_actual": 5}, format="json")
        tarjeta.refresh_from_db()
        assert tarjeta.saldo_actual == Decimal("1000")

    def test_crear_tarjeta_no_permite_fijar_un_saldo_inicial(self, usuario_admin, cliente):
        from apps.clientes.models import Grado, Hijo
        from apps.core.models import Tarjeta
        grado, _ = Grado.objects.get_or_create(nombre="G-INT", defaults={"nivel": 2, "orden": 2})
        h = Hijo.objects.create(nombre="Nuevo", apellido="X", cliente_responsable=cliente, grado=grado, activo=True)
        resp = _api(usuario_admin).post(
            "/api/v1/core/tarjetas/", {"nro_tarjeta": "INT-NEW", "hijo": h.pk, "saldo_actual": 500000}, format="json",
        )
        assert resp.status_code == 201
        assert Tarjeta.objects.get(pk="INT-NEW").saldo_actual == Decimal("0")


@pytest.mark.django_db
class TestCamposSensibles:

    @pytest.mark.parametrize("payload", [
        {"permite_saldo_negativo": True},
        {"limite_credito": 5000000},
        {"fecha_vencimiento": "2030-01-01"},
    ])
    def test_cajero_no_puede_cambiarlos(self, usuario_cajero, tarjeta, payload):
        resp = _api(usuario_cajero).patch(_url(tarjeta), payload, format="json")
        assert resp.status_code == 403
        tarjeta.refresh_from_db()
        assert tarjeta.permite_saldo_negativo is False
        assert tarjeta.limite_credito == Decimal("0")
        assert tarjeta.fecha_vencimiento is None

    def test_cajero_no_puede_reasignar_la_tarjeta_a_otro_alumno(self, usuario_cajero, tarjeta, cliente):
        from apps.clientes.models import Hijo
        otro = Hijo.objects.create(
            nombre="Otro", apellido="Alumno", cliente_responsable=cliente, grado=tarjeta.hijo.grado, activo=True,
        )
        resp = _api(usuario_cajero).patch(_url(tarjeta), {"hijo": otro.pk}, format="json")
        assert resp.status_code == 403
        tarjeta.refresh_from_db()
        assert tarjeta.hijo_id != otro.pk

    def test_reenviar_los_mismos_valores_no_es_un_cambio(self, usuario_cajero, tarjeta):
        # ModalEditar reenvía todo el formulario; sin cambios reales no debe dar 403.
        resp = _api(usuario_cajero).patch(
            _url(tarjeta),
            {"limite_credito": 0, "permite_saldo_negativo": False, "fecha_vencimiento": None, "saldo_alerta": 10000},
            format="json",
        )
        assert resp.status_code == 200
        tarjeta.refresh_from_db()
        assert tarjeta.saldo_alerta == Decimal("10000")

    def test_cajero_puede_crear_una_tarjeta_sin_sobregiro(self, usuario_cajero, cliente):
        from apps.clientes.models import Grado, Hijo
        grado, _ = Grado.objects.get_or_create(nombre="G-INT", defaults={"nivel": 2, "orden": 2})
        h = Hijo.objects.create(nombre="Nu", apellido="Evo", cliente_responsable=cliente, grado=grado, activo=True)
        resp = _api(usuario_cajero).post(
            "/api/v1/core/tarjetas/",
            {"nro_tarjeta": "INT-C1", "hijo": h.pk, "limite_credito": 0, "permite_saldo_negativo": False},
            format="json",
        )
        assert resp.status_code == 201

    def test_cajero_no_puede_crear_una_tarjeta_con_sobregiro(self, usuario_cajero, cliente):
        from apps.clientes.models import Grado, Hijo
        grado, _ = Grado.objects.get_or_create(nombre="G-INT", defaults={"nivel": 2, "orden": 2})
        h = Hijo.objects.create(nombre="Nu", apellido="Dos", cliente_responsable=cliente, grado=grado, activo=True)
        resp = _api(usuario_cajero).post(
            "/api/v1/core/tarjetas/",
            {"nro_tarjeta": "INT-C2", "hijo": h.pk, "permite_saldo_negativo": True},
            format="json",
        )
        assert resp.status_code == 403

    @pytest.mark.parametrize("rol_fixture", ["usuario_admin", "usuario_supervisor"])
    def test_admin_y_supervisor_si_pueden_y_queda_auditado(self, request, rol_fixture, tarjeta):
        from apps.usuarios.models import AuditoriaOperacion
        usuario = request.getfixturevalue(rol_fixture)
        resp = _api(usuario).patch(
            _url(tarjeta), {"permite_saldo_negativo": True, "limite_credito": 200000}, format="json",
        )
        assert resp.status_code == 200
        tarjeta.refresh_from_db()
        assert tarjeta.permite_saldo_negativo is True
        assert tarjeta.limite_credito == Decimal("200000")
        auditoria = AuditoriaOperacion.objects.filter(operacion="EDITAR_TARJETA").first()
        assert auditoria is not None
        assert "INT-1" in auditoria.descripcion and "limite_credito" in auditoria.descripcion


@pytest.mark.django_db
class TestEliminarTarjeta:

    def test_cajero_no_puede_eliminar(self, usuario_cajero, tarjeta):
        assert _api(usuario_cajero).delete(_url(tarjeta)).status_code == 403

    def test_admin_puede_eliminar_una_tarjeta_sin_movimientos(self, usuario_admin, tarjeta):
        from apps.core.models import Tarjeta
        assert _api(usuario_admin).delete(_url(tarjeta)).status_code == 204
        assert not Tarjeta.objects.filter(pk="INT-1").exists()


@pytest.mark.django_db
class TestLibroMayorYCargasInmutables:

    @pytest.fixture
    def movimiento(self, tarjeta):
        from apps.core.models import MovimientoTarjeta
        return MovimientoTarjeta.objects.create(
            tarjeta=tarjeta, tipo="RECARGA", monto=Decimal("500"),
            saldo_anterior=Decimal("1000"), saldo_resultante=Decimal("1500"),
        )

    def test_movimientos_solo_lectura(self, usuario_admin, movimiento):
        api = _api(usuario_admin)
        base = "/api/v1/core/movimientos-tarjeta/"
        assert api.get(base).status_code == 200
        assert api.post(base, {"tarjeta": "INT-1", "tipo": "RECARGA", "monto": 1}, format="json").status_code == 405
        assert api.patch(f"{base}{movimiento.pk}/", {"monto": 1}, format="json").status_code == 405
        assert api.delete(f"{base}{movimiento.pk}/").status_code == 405

    @pytest.fixture
    def carga(self, tarjeta, usuario_cajero):
        from apps.core.models import CargaSaldo
        return CargaSaldo.objects.create(
            tarjeta=tarjeta, monto_cargado=Decimal("20000"), metodo_pago="TRANSFERENCIA",
            responsable=usuario_cajero,
        )

    def test_carga_no_se_edita_ni_se_borra(self, usuario_admin, carga):
        api = _api(usuario_admin)
        url = f"/api/v1/core/cargas-saldo/{carga.pk}/"
        assert api.patch(url, {"estado": "CONFIRMADA", "monto_cargado": 1}, format="json").status_code == 405
        assert api.put(url, {}, format="json").status_code == 405
        assert api.delete(url).status_code == 405
        carga.refresh_from_db()
        assert carga.estado == "PENDIENTE" and carga.monto_cargado == Decimal("20000")

    def test_no_se_puede_crear_una_carga_ya_confirmada(self, usuario_cajero, tarjeta):
        resp = _api(usuario_cajero).post(
            "/api/v1/core/cargas-saldo/",
            {"tarjeta": tarjeta.nro_tarjeta, "monto_cargado": 50000, "metodo_pago": "TRANSFERENCIA", "estado": "CONFIRMADA"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["estado"] == "PENDIENTE"
        tarjeta.refresh_from_db()
        assert tarjeta.saldo_actual == Decimal("1000")
