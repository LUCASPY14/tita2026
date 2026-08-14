"""
Tests para almuerzos/validators.py.
Cubre: validar_restricciones_alergenicas, verificar_alergenos_venta,
validar_limite_registros_diarios (edge cases).
"""
import pytest
from decimal import Decimal
from datetime import date


@pytest.fixture
def hijo_con_restriccion_critica(db, cliente):
    from apps.clientes.models import Hijo, Grado, RestriccionHijo
    grado, _ = Grado.objects.get_or_create(
        nombre="2do grado val", defaults={"nivel": 2, "orden": 2, "activo": True}
    )
    hijo = Hijo.objects.create(
        nombre="Alergico", apellido="Test",
        cliente_responsable=cliente, grado=grado, activo=True,
    )
    RestriccionHijo.objects.create(
        hijo=hijo,
        tipo="ALERGICO_MANI",
        severidad=RestriccionHijo.Severidad.CRITICA,
        descripcion="Alérgico al maní",
        requiere_autorizacion=True,
        activo=True,
    )
    return hijo


@pytest.fixture
def hijo_con_restriccion_leve(db, cliente):
    from apps.clientes.models import Hijo, Grado, RestriccionHijo
    grado, _ = Grado.objects.get_or_create(
        nombre="3er grado val", defaults={"nivel": 3, "orden": 3, "activo": True}
    )
    hijo = Hijo.objects.create(
        nombre="Leve", apellido="Test",
        cliente_responsable=cliente, grado=grado, activo=True,
    )
    RestriccionHijo.objects.create(
        hijo=hijo,
        tipo="INTOLERANCIA_LACTOSA",
        severidad=RestriccionHijo.Severidad.MEDIA,
        descripcion="Intolerancia a la lactosa",
        requiere_autorizacion=False,
        activo=True,
    )
    return hijo


@pytest.fixture
def alergeno_mani(db):
    from apps.almuerzos.models import Alergeno
    return Alergeno.objects.create(
        nombre="Maní",
        palabras_clave=["mani", "cacahuete", "alergico_mani"],
        severidad=Alergeno.Severidad.ALTA,
    )


@pytest.fixture
def producto_con_alergeno(db, producto, alergeno_mani):
    from apps.almuerzos.models import ProductoAlergeno
    ProductoAlergeno.objects.create(producto=producto, alergeno=alergeno_mani, contiene=True)
    return producto


# ── validar_restricciones_alergenicas ─────────────────────────────────────────

@pytest.mark.django_db
class TestValidarRestriccionesAlergenicas:

    def test_restriccion_critica_bloquea(self, hijo_con_restriccion_critica):
        from apps.almuerzos.validators import validar_restricciones_alergenicas
        from rest_framework.exceptions import ValidationError

        with pytest.raises(ValidationError, match="[Cc]ríticas"):
            validar_restricciones_alergenicas(hijo_con_restriccion_critica)

    def test_restriccion_critica_con_forzar_permite(self, hijo_con_restriccion_critica):
        from apps.almuerzos.validators import validar_restricciones_alergenicas

        resultado = validar_restricciones_alergenicas(hijo_con_restriccion_critica, forzar=True)
        assert len(resultado) >= 1
        assert any(r["severidad"] == "CRITICA" for r in resultado)

    def test_restriccion_leve_devuelve_advertencias(self, hijo_con_restriccion_leve):
        from apps.almuerzos.validators import validar_restricciones_alergenicas

        resultado = validar_restricciones_alergenicas(hijo_con_restriccion_leve)
        assert len(resultado) == 1
        assert resultado[0]["severidad"] == "MEDIA"

    def test_sin_restricciones_retorna_lista_vacia(self, db, cliente):
        from apps.clientes.models import Hijo, Grado
        from apps.almuerzos.validators import validar_restricciones_alergenicas

        grado, _ = Grado.objects.get_or_create(
            nombre="4to grado val", defaults={"nivel": 4, "orden": 4, "activo": True}
        )
        hijo = Hijo.objects.create(
            nombre="Sano", apellido="Test",
            cliente_responsable=cliente, grado=grado, activo=True,
        )
        assert validar_restricciones_alergenicas(hijo) == []


# ── verificar_alergenos_venta ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestVerificarAlergenosVenta:

    def test_sin_hijo_retorna_vacio(self, producto):
        from apps.almuerzos.validators import verificar_alergenos_venta
        assert verificar_alergenos_venta(None, [producto]) == []

    def test_sin_productos_retorna_vacio(self, hijo_con_restriccion_critica):
        from apps.almuerzos.validators import verificar_alergenos_venta
        assert verificar_alergenos_venta(hijo_con_restriccion_critica, []) == []

    def test_producto_sin_alergenos_retorna_vacio(self, hijo_con_restriccion_critica, producto):
        from apps.almuerzos.validators import verificar_alergenos_venta
        assert verificar_alergenos_venta(hijo_con_restriccion_critica, [producto]) == []

    def test_hijo_sin_restricciones_retorna_vacio(self, db, cliente, producto_con_alergeno):
        from apps.clientes.models import Hijo, Grado
        from apps.almuerzos.validators import verificar_alergenos_venta

        grado, _ = Grado.objects.get_or_create(
            nombre="5to grado val", defaults={"nivel": 5, "orden": 5, "activo": True}
        )
        hijo = Hijo.objects.create(
            nombre="Libre", apellido="Alerg",
            cliente_responsable=cliente, grado=grado, activo=True,
        )
        assert verificar_alergenos_venta(hijo, [producto_con_alergeno]) == []

    def test_cruce_alergeno_con_restriccion_devuelve_advertencia(
        self, hijo_con_restriccion_critica, producto_con_alergeno
    ):
        from apps.almuerzos.validators import verificar_alergenos_venta

        resultado = verificar_alergenos_venta(
            hijo_con_restriccion_critica, [producto_con_alergeno]
        )
        assert len(resultado) >= 1
        assert resultado[0]["alergeno"] == "Maní"


# ── validar_limite_registros_diarios — edge cases ─────────────────────────────

@pytest.mark.django_db
class TestValidarLimiteRegistrosDiarios:

    def test_hijo_none_retorna_true(self, db):
        from apps.almuerzos.validators import validar_limite_registros_diarios
        assert validar_limite_registros_diarios(None, date.today()) is True

    def test_fecha_none_retorna_true(self, db, cliente):
        from apps.clientes.models import Hijo, Grado
        from apps.almuerzos.validators import validar_limite_registros_diarios

        grado, _ = Grado.objects.get_or_create(
            nombre="6to grado val", defaults={"nivel": 6, "orden": 6, "activo": True}
        )
        hijo = Hijo.objects.create(
            nombre="FechaNull", apellido="Test",
            cliente_responsable=cliente, grado=grado, activo=True,
        )
        assert validar_limite_registros_diarios(hijo, None) is True

    def test_con_registro_actual_excluye_en_conteo(self, db, cliente, usuario_cajero):
        from apps.clientes.models import Hijo, Grado
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        from apps.almuerzos.validators import validar_limite_registros_diarios

        grado, _ = Grado.objects.get_or_create(
            nombre="7mo grado val", defaults={"nivel": 7, "orden": 7, "activo": True}
        )
        hijo = Hijo.objects.create(
            nombre="Excluir", apellido="Test",
            cliente_responsable=cliente, grado=grado, activo=True,
        )
        hoy = date.today()
        reg = RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo,
            fecha_consumo=hoy,
            costo_almuerzo=Decimal("10000"),
            ya_cobrado=True,
            registrado_por=usuario_cajero,
        )
        resultado = validar_limite_registros_diarios(hijo, hoy, registro_actual=reg)
        assert resultado is True

    def _crear_hijo(self, cliente, nombre, nivel):
        from apps.clientes.models import Hijo, Grado
        grado, _ = Grado.objects.get_or_create(
            nombre=f"grado-val-{nivel}", defaults={"nivel": nivel, "orden": nivel, "activo": True}
        )
        return Hijo.objects.create(
            nombre=nombre, apellido="Test",
            cliente_responsable=cliente, grado=grado, activo=True,
        )

    def test_segundo_registro_antes_del_umbral_lanza_error(self, db, cliente, usuario_cajero):
        from rest_framework.exceptions import ValidationError
        from django.utils import timezone
        from datetime import timedelta
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        from apps.almuerzos.validators import validar_limite_registros_diarios

        hijo = self._crear_hijo(cliente, "MuyPronto", 8)
        ahora = timezone.localtime()
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo, fecha_consumo=ahora.date(), hora_registro=(ahora - timedelta(seconds=30)).time(),
            costo_almuerzo=Decimal("10000"), ya_cobrado=True, registrado_por=usuario_cajero,
        )
        with pytest.raises(ValidationError, match="Todavia es muy pronto"):
            validar_limite_registros_diarios(hijo, ahora.date())

    def test_segundo_registro_despues_del_umbral_no_cobra(self, db, cliente, usuario_cajero):
        from django.utils import timezone
        from datetime import timedelta
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        from apps.almuerzos.validators import validar_limite_registros_diarios

        hijo = self._crear_hijo(cliente, "VolvioAComer", 9)
        ahora = timezone.localtime()
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo, fecha_consumo=ahora.date(), hora_registro=(ahora - timedelta(seconds=241)).time(),
            costo_almuerzo=Decimal("10000"), ya_cobrado=True, registrado_por=usuario_cajero,
        )
        resultado = validar_limite_registros_diarios(hijo, ahora.date())
        assert resultado is False

    def test_tercer_intento_lanza_limite_alcanzado(self, db, cliente, usuario_cajero):
        from rest_framework.exceptions import ValidationError
        from django.utils import timezone
        from datetime import timedelta
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        from apps.almuerzos.validators import validar_limite_registros_diarios

        hijo = self._crear_hijo(cliente, "TercerIntento", 10)
        ahora = timezone.localtime()
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo, fecha_consumo=ahora.date(), hora_registro=(ahora - timedelta(seconds=600)).time(),
            costo_almuerzo=Decimal("10000"), ya_cobrado=True, registrado_por=usuario_cajero,
        )
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo, fecha_consumo=ahora.date(), hora_registro=(ahora - timedelta(seconds=300)).time(),
            costo_almuerzo=Decimal("0"), ya_cobrado=False, registrado_por=usuario_cajero,
        )
        with pytest.raises(ValidationError, match="Limite alcanzado"):
            validar_limite_registros_diarios(hijo, ahora.date())
