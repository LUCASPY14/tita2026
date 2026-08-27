"""
Tests para apps.core.serializers — TarjetaSerializer.
Cubre los SerializerMethodField que dependen de hijo vs cliente_directo.
"""
import pytest
from decimal import Decimal


# ── fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def grado(db):
    from apps.clientes.models import Grado
    return Grado.objects.create(nombre="3er grado", nivel=3, orden=3)


@pytest.fixture
def hijo(db, cliente, grado):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Lucía",
        apellido="Pérez",
        cliente_responsable=cliente,
        grado=grado,
        activo=True,
    )


@pytest.fixture
def tarjeta_alumno(db, hijo):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="T001",
        hijo=hijo,
        saldo_actual=Decimal("15000"),
    )


@pytest.fixture
def tarjeta_docente(db, cliente):
    """Tarjeta directa (docente/funcionario) — sin hijo."""
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="T002",
        cliente_directo=cliente,
        saldo_actual=Decimal("5000"),
    )


@pytest.fixture
def tarjeta_sin_titular():
    """Mock de tarjeta sin hijo ni cliente_directo — para testear los except del serializer."""
    from unittest.mock import MagicMock
    t = MagicMock()
    t.nro_tarjeta = "T999"
    t.hijo_id = None
    t.cliente_directo = None
    t.cliente_directo_id = None
    # saldo_disponible no existe en el mock, no nos importa para estos tests
    return t


def _serialize(tarjeta, request=None):
    from apps.core.serializers import TarjetaSerializer
    ctx = {"request": request} if request else {}
    return TarjetaSerializer(tarjeta, context=ctx).data


# ── TarjetaSerializer: tarjeta de alumno ──────────────────────────────────────

@pytest.mark.django_db
class TestTarjetaSerializerAlumno:

    def test_es_alumno_true(self, tarjeta_alumno):
        data = _serialize(tarjeta_alumno)
        assert data["es_alumno"] is True

    def test_hijo_nombre(self, tarjeta_alumno, hijo):
        data = _serialize(tarjeta_alumno)
        assert data["hijo_nombre"] == hijo.nombre_completo

    def test_hijo_foto_none_sin_foto(self, tarjeta_alumno):
        data = _serialize(tarjeta_alumno)
        assert data["hijo_foto"] is None

    def test_hijo_grado(self, tarjeta_alumno, grado):
        data = _serialize(tarjeta_alumno)
        assert data["hijo_grado"] == grado.nombre

    def test_hijo_restricciones_vacio(self, tarjeta_alumno):
        data = _serialize(tarjeta_alumno)
        assert data["hijo_restricciones"] == []

    def test_hijo_cumple_hoy_false_sin_fecha_nacimiento(self, tarjeta_alumno):
        data = _serialize(tarjeta_alumno)
        assert data["hijo_cumple_hoy"] is False

    def test_hijo_cumple_hoy_true_si_coincide_mes_y_dia(self, tarjeta_alumno, hijo):
        from datetime import date
        from freezegun import freeze_time
        hijo.fecha_nacimiento = date(2015, 5, 15)
        hijo.save(update_fields=["fecha_nacimiento"])
        with freeze_time("2026-05-15"):
            data = _serialize(tarjeta_alumno)
        assert data["hijo_cumple_hoy"] is True

    def test_hijo_cumple_hoy_false_otro_dia(self, tarjeta_alumno, hijo):
        from datetime import date
        from freezegun import freeze_time
        hijo.fecha_nacimiento = date(2015, 5, 15)
        hijo.save(update_fields=["fecha_nacimiento"])
        with freeze_time("2026-05-16"):
            data = _serialize(tarjeta_alumno)
        assert data["hijo_cumple_hoy"] is False

    def test_hijo_restricciones_con_datos(self, tarjeta_alumno, hijo):
        from apps.clientes.models import RestriccionHijo
        RestriccionHijo.objects.create(
            hijo=hijo,
            tipo="ALERGIA",
            descripcion="Maní",
            severidad="ALTA",
            activo=True,
        )
        data = _serialize(tarjeta_alumno)
        assert len(data["hijo_restricciones"]) == 1
        r = data["hijo_restricciones"][0]
        assert r["tipo"] == "ALERGIA"
        assert r["severidad"] == "ALTA"

    def test_cliente_id_del_responsable(self, tarjeta_alumno, cliente):
        data = _serialize(tarjeta_alumno)
        assert data["cliente_id"] == cliente.pk

    def test_cliente_nombre(self, tarjeta_alumno, cliente):
        data = _serialize(tarjeta_alumno)
        assert data["cliente_nombre"] == cliente.nombre_completo

    def test_cliente_ruc(self, tarjeta_alumno, cliente):
        data = _serialize(tarjeta_alumno)
        assert data["cliente_ruc"] == cliente.ruc_ci

    def test_cliente_saldo_cc(self, tarjeta_alumno):
        data = _serialize(tarjeta_alumno)
        assert isinstance(data["cliente_saldo_cc"], int)

    def test_cliente_limite_credito(self, tarjeta_alumno, cliente):
        data = _serialize(tarjeta_alumno)
        assert data["cliente_limite_credito"] == int(cliente.limite_credito)

    def test_lista_precio_id(self, tarjeta_alumno, cliente, lista_precio):
        data = _serialize(tarjeta_alumno)
        assert data["lista_precio_id"] == lista_precio.pk

    def test_lista_es_default_false(self, tarjeta_alumno):
        # lista_precio del fixture global tiene es_por_defecto=False
        data = _serialize(tarjeta_alumno)
        assert data["lista_es_default"] is False


# ── TarjetaSerializer: tarjeta de docente ────────────────────────────────────

@pytest.mark.django_db
class TestTarjetaSerializerDocente:

    def test_es_alumno_false(self, tarjeta_docente):
        data = _serialize(tarjeta_docente)
        assert data["es_alumno"] is False

    def test_hijo_nombre_usa_cliente_directo(self, tarjeta_docente, cliente):
        data = _serialize(tarjeta_docente)
        assert data["hijo_nombre"] == cliente.nombre_completo

    def test_hijo_foto_none(self, tarjeta_docente):
        data = _serialize(tarjeta_docente)
        assert data["hijo_foto"] is None

    def test_hijo_grado_none(self, tarjeta_docente):
        data = _serialize(tarjeta_docente)
        assert data["hijo_grado"] is None

    def test_hijo_cumple_hoy_false(self, tarjeta_docente):
        data = _serialize(tarjeta_docente)
        assert data["hijo_cumple_hoy"] is False

    def test_hijo_restricciones_vacio(self, tarjeta_docente):
        data = _serialize(tarjeta_docente)
        assert data["hijo_restricciones"] == []

    def test_cliente_id_directo(self, tarjeta_docente, cliente):
        data = _serialize(tarjeta_docente)
        assert data["cliente_id"] == cliente.pk

    def test_lista_precio_id_directo(self, tarjeta_docente, lista_precio):
        data = _serialize(tarjeta_docente)
        assert data["lista_precio_id"] == lista_precio.pk


# ── TarjetaSerializer: sin titular (fallback a None/0) ───────────────────────
# Usamos los métodos directamente para evitar que __all__ intente serializar
# campos Decimal del mock (que no tienen valores válidos).

class TestTarjetaSerializerSinTitular:

    def _s(self):
        from apps.core.serializers import TarjetaSerializer
        return TarjetaSerializer()

    def test_cliente_id_none_cuando_sin_titular(self, tarjeta_sin_titular):
        assert self._s().get_cliente_id(tarjeta_sin_titular) is None

    def test_cliente_nombre_none(self, tarjeta_sin_titular):
        assert self._s().get_cliente_nombre(tarjeta_sin_titular) is None

    def test_cliente_ruc_none(self, tarjeta_sin_titular):
        assert self._s().get_cliente_ruc(tarjeta_sin_titular) is None

    def test_cliente_saldo_cc_cero(self, tarjeta_sin_titular):
        assert self._s().get_cliente_saldo_cc(tarjeta_sin_titular) == 0

    def test_cliente_limite_credito_cero(self, tarjeta_sin_titular):
        assert self._s().get_cliente_limite_credito(tarjeta_sin_titular) == 0

    def test_lista_precio_id_none(self, tarjeta_sin_titular):
        assert self._s().get_lista_precio_id(tarjeta_sin_titular) is None

    def test_lista_es_default_true_fallback(self, tarjeta_sin_titular):
        assert self._s().get_lista_es_default(tarjeta_sin_titular) is True

    def test_hijo_nombre_none_sin_hijo_ni_titular(self, tarjeta_sin_titular):
        assert self._s().get_hijo_nombre(tarjeta_sin_titular) is None


# ── TarjetaSerializer: hijo con foto_perfil ───────────────────────────────────

class TestTarjetaSerializerHijoFoto:
    """get_hijo_foto cuando hay foto: devuelve el endpoint protegido de
    clientes (ADMIN/CAJERO), nunca la URL cruda de /media/ — con o sin
    request en el contexto, la ruta es la misma."""

    def _mock_tarjeta_con_foto(self):
        from unittest.mock import MagicMock
        foto = MagicMock()
        foto.url = "/media/test.jpg"
        hijo = MagicMock()
        hijo.foto_perfil = foto
        tarjeta = MagicMock()
        tarjeta.hijo_id = 1
        tarjeta.hijo = hijo
        return tarjeta

    def test_hijo_foto_retorna_endpoint_protegido_con_request(self):
        from unittest.mock import MagicMock
        from apps.core.serializers import TarjetaSerializer
        req = MagicMock()
        s = TarjetaSerializer(context={"request": req})
        result = s.get_hijo_foto(self._mock_tarjeta_con_foto())
        assert result == "/clientes/hijos/1/foto/"

    def test_hijo_foto_retorna_endpoint_protegido_sin_request(self):
        from apps.core.serializers import TarjetaSerializer
        s = TarjetaSerializer()
        result = s.get_hijo_foto(self._mock_tarjeta_con_foto())
        assert result == "/clientes/hijos/1/foto/"
