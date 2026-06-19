"""
Tests de modelos de la app clientes.
Cubre: Cliente (save, pin, nombre_completo, saldo_cuenta_corriente),
       CuentaCorrienteCliente (save con DEBITO/CREDITO/AJUSTE),
       Hijo (nombre_completo, grado_nombre, edad),
       RestriccionHijo (es_critica), Grado, TipoCliente, AlumnoResponsable.
"""
import datetime
import pytest
from decimal import Decimal


# ── Fixtures locales ──────────────────────────────────────────────────────────

@pytest.fixture
def grado(db):
    from apps.clientes.models import Grado
    return Grado.objects.create(nombre="1er Grado", nivel=1, orden=1, activo=True)


@pytest.fixture
def hijo(db, cliente, grado):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Carlos",
        apellido="García",
        cliente_responsable=cliente,
        grado=grado,
        activo=True,
    )


@pytest.fixture
def hijo_sin_grado(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="María",
        apellido="López",
        cliente_responsable=cliente,
        activo=True,
    )


# ── TipoCliente ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTipoClienteModel:

    def test_str(self, tipo_cliente):
        assert str(tipo_cliente) == "Padre"

    def test_activo_default(self, tipo_cliente):
        assert tipo_cliente.activo is True


# ── Grado ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGradoModel:

    def test_str(self, grado):
        assert str(grado) == "1er Grado"

    def test_ordering_por_orden(self, db):
        from apps.clientes.models import Grado
        Grado.objects.create(nombre="6to Grado", nivel=6, orden=6)
        Grado.objects.create(nombre="2do Grado", nivel=2, orden=2)
        Grado.objects.create(nombre="3er Grado", nivel=3, orden=3)
        grados = list(Grado.objects.values_list("nombre", flat=True))
        indices = {g: i for i, g in enumerate(grados)}
        assert indices["2do Grado"] < indices["3er Grado"] < indices["6to Grado"]


# ── Cliente ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestClienteModel:

    def test_str(self, cliente):
        assert str(cliente) == "Pérez, Juan"

    def test_nombre_completo(self, cliente):
        assert cliente.nombre_completo == "Juan Pérez"

    def test_save_inicializa_pin_autorizacion(self, cliente):
        """save() hashea '0000' como PIN por defecto al crear (líneas 87-90)."""
        assert cliente.pin_autorizacion != ""

    def test_check_pin_por_defecto_es_0000(self, cliente):
        assert cliente.check_pin("0000") is True

    def test_check_pin_incorrecto_retorna_false(self, cliente):
        assert cliente.check_pin("9999") is False

    def test_check_pin_vacio_retorna_false(self, tipo_cliente, lista_precio):
        from apps.clientes.models import Cliente
        c = Cliente(pin_autorizacion="")
        assert c.check_pin("0000") is False

    def test_set_pin_cambia_el_pin(self, cliente):
        cliente.set_pin("5678")
        assert cliente.check_pin("5678") is True
        assert cliente.check_pin("0000") is False

    def test_tiene_pin_true(self, cliente):
        assert cliente.tiene_pin is True

    def test_tiene_pin_false_cuando_vacio(self, tipo_cliente, lista_precio):
        from apps.clientes.models import Cliente
        c = Cliente(pin_autorizacion="")
        assert c.tiene_pin is False

    def test_saldo_cuenta_corriente_sin_movimientos(self, cliente):
        """Sin movimientos → saldo=0 (línea 111)."""
        assert cliente.saldo_cuenta_corriente == Decimal("0")

    def test_saldo_cuenta_corriente_retorna_ultimo_saldo(self, cliente, usuario_cajero):
        from apps.clientes.models import CuentaCorrienteCliente
        CuentaCorrienteCliente.objects.create(
            cliente=cliente,
            tipo=CuentaCorrienteCliente.Tipo.DEBITO,
            monto=Decimal("30000"),
            saldo_anterior=Decimal("0"),
            saldo_resultante=Decimal("30000"),
            creado_por=usuario_cajero,
        )
        assert cliente.saldo_cuenta_corriente == Decimal("30000")


# ── CuentaCorrienteCliente ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCuentaCorrienteClienteModel:

    def test_str(self, cliente, usuario_cajero):
        from apps.clientes.models import CuentaCorrienteCliente
        mov = CuentaCorrienteCliente.objects.create(
            cliente=cliente,
            tipo=CuentaCorrienteCliente.Tipo.DEBITO,
            monto=Decimal("20000"),
            saldo_anterior=Decimal("0"),
            saldo_resultante=Decimal("20000"),
            creado_por=usuario_cajero,
        )
        assert "Débito" in str(mov)

    def test_debito_calcula_saldo_resultante(self, cliente, usuario_cajero):
        """DEBITO: saldo_resultante = saldo_anterior + monto (línea 209-210)."""
        from apps.clientes.models import CuentaCorrienteCliente
        mov = CuentaCorrienteCliente.objects.create(
            cliente=cliente,
            tipo=CuentaCorrienteCliente.Tipo.DEBITO,
            monto=Decimal("15000"),
            saldo_anterior=Decimal("0"),
            saldo_resultante=Decimal("0"),
            creado_por=usuario_cajero,
        )
        mov.refresh_from_db()
        assert mov.saldo_resultante == Decimal("15000")

    def test_credito_calcula_saldo_resultante(self, cliente, usuario_cajero):
        """CREDITO: saldo_resultante = saldo_anterior - monto (línea 211-212)."""
        from apps.clientes.models import CuentaCorrienteCliente
        CuentaCorrienteCliente.objects.create(
            cliente=cliente, tipo=CuentaCorrienteCliente.Tipo.DEBITO,
            monto=Decimal("50000"), saldo_anterior=Decimal("0"),
            saldo_resultante=Decimal("50000"), creado_por=usuario_cajero,
        )
        pago = CuentaCorrienteCliente.objects.create(
            cliente=cliente, tipo=CuentaCorrienteCliente.Tipo.CREDITO,
            monto=Decimal("20000"), saldo_anterior=Decimal("50000"),
            saldo_resultante=Decimal("0"),
            creado_por=usuario_cajero,
        )
        pago.refresh_from_db()
        assert pago.saldo_resultante == Decimal("30000")

    def test_ajuste_calcula_saldo_resultante(self, cliente, usuario_cajero):
        """AJUSTE: mismo cálculo que CREDITO — reduce el saldo (línea 212)."""
        from apps.clientes.models import CuentaCorrienteCliente
        ajuste = CuentaCorrienteCliente.objects.create(
            cliente=cliente, tipo=CuentaCorrienteCliente.Tipo.AJUSTE,
            monto=Decimal("5000"), saldo_anterior=Decimal("10000"),
            saldo_resultante=Decimal("0"),
            creado_por=usuario_cajero,
        )
        ajuste.refresh_from_db()
        assert ajuste.saldo_resultante == Decimal("5000")

    def test_saldo_anterior_auto_desde_ultimo_movimiento(self, cliente, usuario_cajero):
        """Si saldo_anterior=None, el save() lo obtiene del último movimiento (líneas 198-207)."""
        from apps.clientes.models import CuentaCorrienteCliente
        CuentaCorrienteCliente.objects.create(
            cliente=cliente, tipo=CuentaCorrienteCliente.Tipo.DEBITO,
            monto=Decimal("40000"), saldo_anterior=Decimal("0"),
            saldo_resultante=Decimal("40000"), creado_por=usuario_cajero,
        )
        # Segundo movimiento sin saldo_anterior
        segundo = CuentaCorrienteCliente(
            cliente=cliente, tipo=CuentaCorrienteCliente.Tipo.DEBITO,
            monto=Decimal("10000"), saldo_anterior=None,
            saldo_resultante=Decimal("0"), creado_por=usuario_cajero,
        )
        segundo.save()
        segundo.refresh_from_db()
        assert segundo.saldo_anterior == Decimal("40000")
        assert segundo.saldo_resultante == Decimal("50000")


# ── Hijo ──────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestHijoModel:

    def test_str_con_grado(self, hijo, grado):
        s = str(hijo)
        assert "García" in s
        assert "Carlos" in s
        assert grado.nombre in s

    def test_str_sin_grado(self, hijo_sin_grado):
        assert "Sin grado" in str(hijo_sin_grado)

    def test_nombre_completo(self, hijo):
        assert hijo.nombre_completo == "Carlos García"

    def test_grado_nombre_con_grado(self, hijo, grado):
        assert hijo.grado_nombre == grado.nombre

    def test_grado_nombre_sin_grado(self, hijo_sin_grado):
        assert hijo_sin_grado.grado_nombre is None

    def test_edad_cumpleanos_hoy(self, cliente):
        from apps.clientes.models import Hijo
        hoy = datetime.date.today()
        h = Hijo.objects.create(
            nombre="Edadito", apellido="Test",
            cliente_responsable=cliente,
            fecha_nacimiento=datetime.date(hoy.year - 8, hoy.month, hoy.day),
        )
        assert h.edad == 8

    def test_edad_sin_fecha_nacimiento(self, hijo_sin_grado):
        assert hijo_sin_grado.edad is None

    def test_edad_antes_de_cumpleanos(self, cliente):
        from apps.clientes.models import Hijo
        hoy = datetime.date.today()
        cumple_mes = hoy.month + 1 if hoy.month < 12 else 1
        cumple_anio = hoy.year if hoy.month < 12 else hoy.year + 1
        h = Hijo.objects.create(
            nombre="Pronto", apellido="Cumple",
            cliente_responsable=cliente,
            fecha_nacimiento=datetime.date(cumple_anio - 10, cumple_mes, hoy.day),
        )
        assert h.edad == 9


# ── RestriccionHijo ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRestriccionHijoModel:

    def test_es_critica_true(self, hijo):
        from apps.clientes.models import RestriccionHijo
        r = RestriccionHijo.objects.create(
            hijo=hijo, tipo="Alergia",
            severidad=RestriccionHijo.Severidad.CRITICA,
        )
        assert r.es_critica is True

    def test_es_critica_false_cuando_alta(self, hijo):
        from apps.clientes.models import RestriccionHijo
        r = RestriccionHijo.objects.create(
            hijo=hijo, tipo="Intolerancia",
            severidad=RestriccionHijo.Severidad.ALTA,
        )
        assert r.es_critica is False

    def test_str_incluye_tipo_y_severidad(self, hijo):
        from apps.clientes.models import RestriccionHijo
        r = RestriccionHijo.objects.create(
            hijo=hijo, tipo="Lactosa",
            severidad=RestriccionHijo.Severidad.MEDIA,
        )
        assert "Lactosa" in str(r)
        assert "Media" in str(r)

    def test_activo_default(self, hijo):
        from apps.clientes.models import RestriccionHijo
        r = RestriccionHijo.objects.create(
            hijo=hijo, tipo="Gluten",
            severidad=RestriccionHijo.Severidad.BAJA,
        )
        assert r.activo is True


# ── AlumnoResponsable ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAlumnoResponsableModel:

    def test_str_titular_incluye_tag(self, hijo, cliente):
        from apps.clientes.models import AlumnoResponsable
        ar = AlumnoResponsable.objects.create(
            hijo=hijo, cliente=cliente,
            parentesco=AlumnoResponsable.Parentesco.PADRE,
            es_titular=True,
        )
        assert "[TITULAR]" in str(ar)

    def test_str_no_titular_sin_tag(self, hijo, cliente):
        from apps.clientes.models import AlumnoResponsable
        ar = AlumnoResponsable.objects.create(
            hijo=hijo, cliente=cliente,
            parentesco=AlumnoResponsable.Parentesco.MADRE,
            es_titular=False,
        )
        assert "[TITULAR]" not in str(ar)

    def test_recibe_notificaciones_default_false(self, hijo, cliente):
        from apps.clientes.models import AlumnoResponsable
        ar = AlumnoResponsable.objects.create(
            hijo=hijo, cliente=cliente,
            parentesco=AlumnoResponsable.Parentesco.TUTOR,
        )
        assert ar.recibe_notificaciones is False
