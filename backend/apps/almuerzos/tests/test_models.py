"""
Tests de modelos de almuerzos.
Cubre: __str__, @property, clean(), save(), calcular_estado, registrar_pago.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError


# ── Fixtures de apoyo ─────────────────────────────────────────────────────────

@pytest.fixture
def grado(db):
    from apps.clientes.models import Grado
    return Grado.objects.create(nombre="1er grado mod", nivel=1, orden=1, activo=True)


@pytest.fixture
def hijo_almuerzo(db, cliente, grado):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Pedro",
        apellido="Estudiante",
        cliente_responsable=cliente,
        grado=grado,
        activo=True,
    )


@pytest.fixture
def precio_almuerzo(db):
    from apps.almuerzos.models import PrecioAlmuerzo
    return PrecioAlmuerzo.objects.create(
        precio_unitario=Decimal("15000"),
        fecha_inicio_vigencia=date(2026, 1, 1),
        activo=True,
    )


@pytest.fixture
def tipo_almuerzo(db):
    from apps.almuerzos.models import TipoAlmuerzo
    return TipoAlmuerzo.objects.create(
        nombre="Menú completo test",
        precio_unitario=Decimal("15000"),
        activo=True,
    )


@pytest.fixture
def plan_almuerzo(db):
    from apps.almuerzos.models import PlanAlmuerzo
    return PlanAlmuerzo.objects.create(
        nombre="Plan Mensual Test",
        tipo=PlanAlmuerzo.TipoPlan.SIN_LIMITE,
        precio_mensual=Decimal("200000"),
        dias_semana_incluidos="LUN,MAR,MIE,JUE,VIE",
        activo=True,
    )


@pytest.fixture
def suscripcion(db, hijo_almuerzo, plan_almuerzo):
    from apps.almuerzos.models import SuscripcionAlmuerzo
    return SuscripcionAlmuerzo.objects.create(
        hijo=hijo_almuerzo,
        plan=plan_almuerzo,
        fecha_inicio=date(2026, 1, 1),
        estado=SuscripcionAlmuerzo.Estado.ACTIVA,
    )


@pytest.fixture
def registro(db, hijo_almuerzo, usuario_cajero):
    from apps.almuerzos.models import RegistroConsumoAlmuerzo
    return RegistroConsumoAlmuerzo.objects.create(
        hijo=hijo_almuerzo,
        fecha_consumo=date.today(),
        costo_almuerzo=Decimal("15000"),
        ya_cobrado=True,
        registrado_por=usuario_cajero,
    )


@pytest.fixture
def cuenta_mensual(db, hijo_almuerzo):
    from apps.almuerzos.models import CuentaAlmuerzoMensual
    return CuentaAlmuerzoMensual.objects.create(
        hijo=hijo_almuerzo,
        anio=2026,
        mes=1,
        cantidad_almuerzos=20,
        monto_total=Decimal("300000"),
        forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
        monto_pagado=Decimal("0"),
        estado=CuentaAlmuerzoMensual.Estado.PENDIENTE,
    )


@pytest.fixture
def pago_cuenta(db, cuenta_mensual, usuario_cajero):
    from apps.almuerzos.models import PagoCuentaAlmuerzo
    return PagoCuentaAlmuerzo.objects.create(
        cuenta=cuenta_mensual,
        monto=Decimal("100000"),
        medio_pago="EFECTIVO",
        registrado_por=usuario_cajero,
    )


@pytest.fixture
def menu_diario(db, producto, usuario_cajero):
    from apps.almuerzos.models import MenuDiario
    return MenuDiario.objects.create(
        fecha=date.today(),
        plato_principal="Milanesa con arroz",
        guarnicion="Ensalada",
        postre="Fruta",
        bebida="Agua",
        activo=True,
        creado_por=usuario_cajero,
    )


# ── PrecioAlmuerzo ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPrecioAlmuerzo:

    def test_str(self, precio_almuerzo):
        assert "₲" in str(precio_almuerzo) or "15" in str(precio_almuerzo)

    def test_clean_doble_activo_falla(self, precio_almuerzo):
        from apps.almuerzos.models import PrecioAlmuerzo
        precio2 = PrecioAlmuerzo(
            precio_unitario=Decimal("18000"),
            fecha_inicio_vigencia=date(2026, 6, 1),
            fecha_fin_vigencia=None,
            activo=True,
        )
        with pytest.raises(ValidationError, match="[Cc]errá|[Cc]ierra|ya existe"):
            precio2.clean()

    def test_clean_solapamiento_falla(self, precio_almuerzo):
        from apps.almuerzos.models import PrecioAlmuerzo
        precio2 = PrecioAlmuerzo(
            precio_unitario=Decimal("18000"),
            fecha_inicio_vigencia=date(2026, 1, 15),
            fecha_fin_vigencia=date(2026, 12, 31),
            activo=True,
        )
        with pytest.raises(ValidationError, match="[Ss]olapa"):
            precio2.clean()

    def test_clean_sin_solapamiento_ok(self, precio_almuerzo):
        from apps.almuerzos.models import PrecioAlmuerzo
        precio_almuerzo.fecha_fin_vigencia = date(2026, 5, 31)
        precio_almuerzo.save()

        precio2 = PrecioAlmuerzo(
            precio_unitario=Decimal("18000"),
            fecha_inicio_vigencia=date(2026, 6, 1),
            fecha_fin_vigencia=None,
            activo=True,
        )
        precio2.clean()  # no debe lanzar


# ── TipoAlmuerzo ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTipoAlmuerzo:

    def test_str(self, tipo_almuerzo):
        assert "Menú completo test" in str(tipo_almuerzo)

    def test_save_es_predeterminado_desactiva_el_anterior(self, tipo_almuerzo):
        from apps.almuerzos.models import TipoAlmuerzo
        tipo_almuerzo.es_predeterminado = True
        tipo_almuerzo.save()
        nuevo = TipoAlmuerzo.objects.create(
            nombre="Menú simple test", precio_unitario=Decimal("12000"),
            activo=True, es_predeterminado=True,
        )
        tipo_almuerzo.refresh_from_db()
        assert tipo_almuerzo.es_predeterminado is False
        assert nuevo.es_predeterminado is True

    def test_save_sin_predeterminado_no_desactiva_al_actual(self, tipo_almuerzo):
        from apps.almuerzos.models import TipoAlmuerzo
        tipo_almuerzo.es_predeterminado = True
        tipo_almuerzo.save()
        TipoAlmuerzo.objects.create(
            nombre="Menú simple test", precio_unitario=Decimal("12000"), activo=True,
        )
        tipo_almuerzo.refresh_from_db()
        assert tipo_almuerzo.es_predeterminado is True


# ── PlanAlmuerzo ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPlanAlmuerzo:

    def test_str(self, plan_almuerzo):
        assert "Plan Mensual Test" in str(plan_almuerzo)

    def test_save_es_predeterminado_desactiva_el_anterior(self, plan_almuerzo):
        from apps.almuerzos.models import PlanAlmuerzo
        plan_almuerzo.es_predeterminado = True
        plan_almuerzo.save()
        nuevo = PlanAlmuerzo.objects.create(
            nombre="Plan Cantidad Test", tipo=PlanAlmuerzo.TipoPlan.CANTIDAD,
            precio_mensual=Decimal("150000"), cantidad_almuerzos_mes=20,
            dias_semana_incluidos="LUN,MAR,MIE,JUE,VIE", activo=True, es_predeterminado=True,
        )
        plan_almuerzo.refresh_from_db()
        assert plan_almuerzo.es_predeterminado is False
        assert nuevo.es_predeterminado is True


# ── SuscripcionAlmuerzo ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSuscripcionAlmuerzo:

    def test_str(self, suscripcion):
        s = str(suscripcion)
        assert "Plan Mensual Test" in s or "Activa" in s


# ── RegistroConsumoAlmuerzo ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestRegistroConsumoAlmuerzo:

    def test_str(self, registro):
        assert "Registrado" in str(registro) or str(date.today()) in str(registro)

    def test_save_infiere_costo_desde_tipo_almuerzo(self, db, hijo_almuerzo, usuario_cajero, tipo_almuerzo):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        reg = RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo,
            tipo_almuerzo=tipo_almuerzo,
            fecha_consumo=date.today(),
            costo_almuerzo=None,
            registrado_por=usuario_cajero,
        )
        assert reg.costo_almuerzo == Decimal("15000")

    def test_save_infiere_costo_desde_precio_vigente(self, db, hijo_almuerzo, usuario_cajero, precio_almuerzo):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        reg = RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo,
            fecha_consumo=date.today(),
            costo_almuerzo=None,
            registrado_por=usuario_cajero,
        )
        assert reg.costo_almuerzo == Decimal("15000")


# ── CuentaAlmuerzoMensual ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCuentaAlmuerzoMensual:

    def test_str(self, cuenta_mensual):
        s = str(cuenta_mensual)
        assert "₲" in s or "2026" in s

    def test_saldo_pendiente(self, cuenta_mensual):
        assert cuenta_mensual.saldo_pendiente == Decimal("300000")

    def test_calcular_estado_pagado(self, cuenta_mensual):
        cuenta_mensual.monto_pagado = Decimal("300000")
        cuenta_mensual._calcular_estado()
        assert cuenta_mensual.estado == "PAGADO"
        assert cuenta_mensual.fecha_pago is not None

    def test_calcular_estado_parcial(self, cuenta_mensual):
        cuenta_mensual.monto_pagado = Decimal("100000")
        cuenta_mensual._calcular_estado()
        assert cuenta_mensual.estado == "PARCIAL"

    def test_calcular_estado_pendiente(self, cuenta_mensual):
        cuenta_mensual.monto_pagado = Decimal("0")
        cuenta_mensual._calcular_estado()
        assert cuenta_mensual.estado == "PENDIENTE"

    def test_actualizar_estado_persiste(self, cuenta_mensual):
        cuenta_mensual.monto_pagado = Decimal("300000")
        cuenta_mensual.actualizar_estado()
        cuenta_mensual.refresh_from_db()
        assert cuenta_mensual.estado == "PAGADO"

    def test_registrar_pago_actualiza_monto_y_estado(self, cuenta_mensual):
        cuenta_mensual.registrar_pago(Decimal("300000"))
        cuenta_mensual.refresh_from_db()
        assert cuenta_mensual.monto_pagado == Decimal("300000")
        assert cuenta_mensual.estado == "PAGADO"


# ── PagoCuentaAlmuerzo ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPagoCuentaAlmuerzo:

    def test_str(self, pago_cuenta):
        assert "₲" in str(pago_cuenta)

    def test_clean_monto_cero_falla(self, pago_cuenta):
        pago_cuenta.monto = Decimal("0")
        with pytest.raises(ValidationError, match="mayor a cero"):
            pago_cuenta.clean()

    def test_clean_monto_supera_saldo_falla(self, pago_cuenta):
        pago_cuenta.monto = Decimal("999999")
        with pytest.raises(ValidationError, match="[Ss]aldo"):
            pago_cuenta.clean()

    def test_clean_monto_valido_ok(self, pago_cuenta):
        pago_cuenta.monto = Decimal("100000")
        pago_cuenta.clean()  # no debe lanzar



# ── Alergeno y ProductoAlergeno ───────────────────────────────────────────────

@pytest.mark.django_db
class TestAlergeno:

    def test_str(self, db):
        from apps.almuerzos.models import Alergeno
        a = Alergeno.objects.create(nombre="Gluten", severidad=Alergeno.Severidad.ALTA)
        assert "Gluten" in str(a)

    def test_producto_alergeno_str_contiene(self, db, producto, usuario_cajero):
        from apps.almuerzos.models import Alergeno, ProductoAlergeno
        a = Alergeno.objects.create(nombre="Maní test", severidad=Alergeno.Severidad.ALTA)
        pa = ProductoAlergeno.objects.create(
            producto=producto, alergeno=a, contiene=True, registrado_por=usuario_cajero
        )
        assert "Contiene" in str(pa)

    def test_producto_alergeno_str_trazas(self, db, producto, usuario_cajero):
        from apps.almuerzos.models import Alergeno, ProductoAlergeno
        a = Alergeno.objects.create(nombre="Soja test", severidad=Alergeno.Severidad.MEDIA)
        pa = ProductoAlergeno.objects.create(
            producto=producto, alergeno=a, contiene=False, registrado_por=usuario_cajero
        )
        assert "Trazas" in str(pa)


# ── MenuDiario y DetalleMenuDiario ────────────────────────────────────────────

@pytest.mark.django_db
class TestMenuDiario:

    def test_str(self, menu_diario):
        assert "Milanesa" in str(menu_diario) or str(date.today()) in str(menu_diario)

    def test_tiene_alergenos_false(self, menu_diario):
        assert menu_diario.tiene_alergenos is False

    def test_tiene_alergenos_true(self, db, menu_diario, producto, usuario_cajero):
        from apps.almuerzos.models import DetalleMenuDiario, Alergeno, ProductoAlergeno
        a = Alergeno.objects.create(nombre="Leche test", severidad=Alergeno.Severidad.MEDIA)
        ProductoAlergeno.objects.create(
            producto=producto, alergeno=a, contiene=True, registrado_por=usuario_cajero
        )
        DetalleMenuDiario.objects.create(
            menu=menu_diario,
            producto=producto,
            curso=DetalleMenuDiario.Curso.PLATO_PRINCIPAL,
            cantidad=Decimal("1"),
        )
        assert menu_diario.tiene_alergenos is True

    def test_detalle_menu_str(self, db, menu_diario, producto):
        from apps.almuerzos.models import DetalleMenuDiario
        d = DetalleMenuDiario.objects.create(
            menu=menu_diario,
            producto=producto,
            curso=DetalleMenuDiario.Curso.POSTRE,
            cantidad=Decimal("1"),
        )
        s = str(d)
        assert "POSTRE" in s.upper() or str(date.today()) in s
