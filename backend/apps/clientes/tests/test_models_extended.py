"""
Tests extendidos de modelos de la app clientes.
Cubre: HistorialGrado (__str__, campos), RestriccionHijo (es_critica property),
       Grado (activo default).
"""
import pytest
from django.utils import timezone


@pytest.fixture
def grado(db):
    from apps.clientes.models import Grado
    return Grado.objects.create(nombre="1er Grado", nivel=1, orden=1, activo=True)


@pytest.fixture
def hijo(db, cliente, grado):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Ana",
        apellido="Martinez",
        cliente_responsable=cliente,
        grado=grado,
        activo=True,
    )


@pytest.mark.django_db
class TestHistorialGrado:

    def test_str_con_grado_anterior(self, hijo):
        from apps.clientes.models import HistorialGrado
        h = HistorialGrado.objects.create(
            hijo=hijo,
            grado_anterior="Jardin",
            grado_nuevo="1er Grado",
            anio_escolar=2026,
            motivo="PROMOCION",
        )
        assert "Jardin" in str(h)
        assert "1er Grado" in str(h)

    def test_str_sin_grado_anterior(self, hijo):
        from apps.clientes.models import HistorialGrado
        h = HistorialGrado.objects.create(
            hijo=hijo,
            grado_anterior=None,
            grado_nuevo="1er Grado",
            anio_escolar=2026,
            motivo="INGRESO",
        )
        assert "N/A" in str(h)
        assert "1er Grado" in str(h)

    def test_fecha_cambio_auto_set(self, hijo):
        from apps.clientes.models import HistorialGrado
        antes = timezone.now()
        h = HistorialGrado.objects.create(
            hijo=hijo,
            grado_nuevo="2do Grado",
            anio_escolar=2026,
            motivo="PROMOCION",
        )
        assert h.fecha_cambio >= antes

    def test_campos_opcionales(self, hijo):
        from apps.clientes.models import HistorialGrado
        h = HistorialGrado.objects.create(
            hijo=hijo,
            grado_nuevo="3er Grado",
            anio_escolar=2026,
            motivo="REPITENCIA",
            observaciones="Repitio por inasistencias",
            usuario_registro="admin@cantina.test",
        )
        assert h.observaciones == "Repitio por inasistencias"
        assert h.usuario_registro == "admin@cantina.test"


@pytest.mark.django_db
class TestRestriccionHijo:

    def test_es_critica_cuando_severidad_critica(self, hijo):
        from apps.clientes.models import RestriccionHijo
        r = RestriccionHijo.objects.create(
            hijo=hijo,
            tipo="Alergia",
            severidad=RestriccionHijo.Severidad.CRITICA,
        )
        assert r.es_critica is True

    def test_no_es_critica_cuando_severidad_alta(self, hijo):
        from apps.clientes.models import RestriccionHijo
        r = RestriccionHijo.objects.create(
            hijo=hijo,
            tipo="Intolerancia",
            severidad=RestriccionHijo.Severidad.ALTA,
        )
        assert r.es_critica is False

    def test_str_incluye_tipo_y_severidad(self, hijo):
        from apps.clientes.models import RestriccionHijo
        r = RestriccionHijo.objects.create(
            hijo=hijo,
            tipo="Celiaquia",
            severidad=RestriccionHijo.Severidad.CRITICA,
        )
        assert "Celiaquia" in str(r)
        assert r.get_severidad_display() in str(r)

    def test_requiere_autorizacion_default_false(self, hijo):
        from apps.clientes.models import RestriccionHijo
        r = RestriccionHijo.objects.create(
            hijo=hijo,
            tipo="Intolerancia lactosa",
        )
        assert r.requiere_autorizacion is False


@pytest.mark.django_db
class TestGrado:

    def test_str(self, grado):
        assert str(grado) == "1er Grado"

    def test_activo_por_defecto(self, db):
        from apps.clientes.models import Grado
        g = Grado.objects.create(nombre="Preescolar", nivel=0, orden=0)
        assert g.activo is True