"""
Fase 0 — edición de alumnos.

Cambiar el grado, dar de alta/baja o cambiar el responsable tiene impacto
administrativo y económico: no lo hace cualquier usuario interno. Todo cambio
de grado deja historial y auditoría.
"""
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
        email="sup_hijo@test.com", password="test1234",
        nombre="Sup", apellido="Hijo", rol=Usuario.Rol.SUPERVISOR,
    )


@pytest.fixture
def grados(db):
    from apps.clientes.models import Grado
    a = Grado.objects.create(nombre="Grado A", nivel=2, orden=2)
    b = Grado.objects.create(nombre="Grado B", nivel=2, orden=3)
    return a, b


@pytest.fixture
def hijo(db, cliente, grados):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Ana", apellido="Perm", cliente_responsable=cliente, grado=grados[0], activo=True,
    )


def _url(h):
    return f"/api/v1/clientes/hijos/{h.pk}/"


@pytest.mark.django_db
class TestCambioDeGrado:

    def test_cajero_no_puede_cambiar_el_grado(self, usuario_cajero, hijo, grados):
        resp = _api(usuario_cajero).patch(_url(hijo), {"grado": grados[1].pk}, format="json")
        assert resp.status_code == 403
        hijo.refresh_from_db()
        assert hijo.grado_id == grados[0].pk

    def test_supervisor_tampoco_solo_admin(self, usuario_supervisor, hijo, grados):
        resp = _api(usuario_supervisor).patch(_url(hijo), {"grado": grados[1].pk}, format="json")
        assert resp.status_code == 403

    def test_admin_cambia_el_grado_y_queda_historial_y_auditoria(self, usuario_admin, hijo, grados):
        from datetime import date
        from apps.clientes.models import HistorialGrado
        from apps.usuarios.models import AuditoriaOperacion
        resp = _api(usuario_admin).patch(_url(hijo), {"grado": grados[1].pk}, format="json")
        assert resp.status_code == 200
        hijo.refresh_from_db()
        assert hijo.grado_id == grados[1].pk
        h = HistorialGrado.objects.get(hijo=hijo)
        assert (h.grado_anterior, h.grado_nuevo, h.anio_escolar) == ("Grado A", "Grado B", date.today().year)
        assert AuditoriaOperacion.objects.filter(operacion="CAMBIAR_GRADO").exists()

    def test_reenviar_el_mismo_grado_no_es_un_cambio(self, usuario_cajero, hijo, grados):
        from apps.clientes.models import HistorialGrado
        resp = _api(usuario_cajero).patch(
            _url(hijo), {"grado": grados[0].pk, "nombre": "Ana Maria"}, format="json",
        )
        assert resp.status_code == 200
        assert not HistorialGrado.objects.filter(hijo=hijo).exists()

    def test_el_alumno_repite_el_admin_puede_dejarlo_en_el_mismo_grado_con_historial(
        self, usuario_admin, hijo, grados,
    ):
        # Repetir = no cambia el grado: no genera fila (no hubo cambio). Corregir un
        # error de carga (A -> B) y volver (B -> A) sí queda registrado.
        api = _api(usuario_admin)
        api.patch(_url(hijo), {"grado": grados[1].pk}, format="json")
        api.patch(_url(hijo), {"grado": grados[0].pk}, format="json")
        from apps.clientes.models import HistorialGrado
        assert HistorialGrado.objects.filter(hijo=hijo).count() == 2


@pytest.mark.django_db
class TestAltaBajaYResponsable:

    def test_cajero_no_puede_dar_de_baja(self, usuario_cajero, hijo):
        resp = _api(usuario_cajero).patch(_url(hijo), {"activo": False}, format="json")
        assert resp.status_code == 403
        hijo.refresh_from_db()
        assert hijo.activo is True

    def test_supervisor_puede_dar_de_baja_y_se_completa_fecha_baja(self, usuario_supervisor, hijo):
        resp = _api(usuario_supervisor).patch(_url(hijo), {"activo": False}, format="json")
        assert resp.status_code == 200
        hijo.refresh_from_db()
        assert hijo.activo is False and hijo.fecha_baja is not None

    def test_cajero_no_puede_cambiar_el_responsable(self, usuario_cajero, hijo, cliente):
        from apps.clientes.models import Cliente
        otro = Cliente.objects.create(
            nombres="Otro", apellidos="Resp", ruc_ci="6660001", tipo_cliente=cliente.tipo_cliente,
            lista_precio=cliente.lista_precio,
        )
        resp = _api(usuario_cajero).patch(_url(hijo), {"cliente_responsable": otro.pk}, format="json")
        assert resp.status_code == 403

    def test_cajero_si_puede_editar_datos_basicos(self, usuario_cajero, hijo):
        resp = _api(usuario_cajero).patch(_url(hijo), {"nombre": "Anita"}, format="json")
        assert resp.status_code == 200
        hijo.refresh_from_db()
        assert hijo.nombre == "Anita"

    def test_campos_de_purga_y_baja_no_se_editan_por_la_api(self, usuario_admin, hijo):
        resp = _api(usuario_admin).patch(
            _url(hijo),
            {"datos_purgados": True, "fecha_baja": "2020-01-01T00:00:00Z", "purga_solicitada_en": "2020-01-01T00:00:00Z"},
            format="json",
        )
        assert resp.status_code == 200
        hijo.refresh_from_db()
        assert hijo.datos_purgados is False
        assert hijo.fecha_baja is None and hijo.purga_solicitada_en is None

    def test_solo_admin_elimina_alumnos(self, usuario_supervisor, usuario_admin, hijo):
        hijo.activo = False
        hijo.save(update_fields=["activo"])
        assert _api(usuario_supervisor).delete(_url(hijo)).status_code == 403
        assert _api(usuario_admin).delete(_url(hijo)).status_code == 204


@pytest.mark.django_db
class TestHistorialGradoSoloLectura:

    def test_no_se_escribe_por_la_api(self, usuario_admin, hijo):
        api = _api(usuario_admin)
        base = "/api/v1/clientes/historial-grados/"
        assert api.get(base).status_code == 200
        resp = api.post(base, {"hijo": hijo.pk, "grado_nuevo": "X", "anio_escolar": 2026}, format="json")
        assert resp.status_code == 405
