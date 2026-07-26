"""
Cobertura de ramas no alcanzadas en almuerzos/serializers.py:
  - RegistroConsumoAlmuerzoSerializer.validate(): 3 errores de suscripción
  - PagoCuentaAlmuerzoSerializer.validate(): monto ≤ 0, monto > saldo
  - PagoAlmuerzoMensualSerializer.validate(): mes anterior/posterior a suscripción
  - DetalleMenuDiarioSerializer.validate_cantidad(): valor ≤ 0
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture
def grado(db):
    from apps.clientes.models import Grado
    g, _ = Grado.objects.get_or_create(
        nombre="3er Grado Test",
        defaults={"nivel": 3, "orden": 3, "activo": True},
    )
    return g


@pytest.fixture
def hijo_ser(db, cliente, grado):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="SerTest", apellido="A",
        cliente_responsable=cliente, grado=grado, activo=True,
    )


@pytest.fixture
def hijo_otro(db, cliente, grado):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="SerTest", apellido="B",
        cliente_responsable=cliente, grado=grado, activo=True,
    )


@pytest.fixture
def plan_almuerzo(db):
    from apps.almuerzos.models import PlanAlmuerzo
    return PlanAlmuerzo.objects.create(
        nombre="Plan Serializer Test",
        precio_mensual=Decimal("120000"),
    )


@pytest.fixture
def suscripcion(db, hijo_ser, plan_almuerzo):
    from apps.almuerzos.models import SuscripcionAlmuerzo
    hoy = date.today()
    return SuscripcionAlmuerzo.objects.create(
        hijo=hijo_ser,
        plan=plan_almuerzo,
        fecha_inicio=hoy,
        fecha_fin=hoy + timedelta(days=30),
        estado=SuscripcionAlmuerzo.Estado.ACTIVA,
    )


@pytest.fixture
def cuenta_almuerzo(db, hijo_ser):
    from apps.almuerzos.models import CuentaAlmuerzoMensual
    hoy = date.today()
    return CuentaAlmuerzoMensual.objects.create(
        hijo=hijo_ser,
        anio=hoy.year,
        mes=hoy.month,
        cantidad_almuerzos=20,
        monto_total=Decimal("60000"),
        forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
    )


# ==============================================================================
# RegistroConsumoAlmuerzoSerializer.validate()
# ==============================================================================

@pytest.mark.django_db
class TestRegistroConsumoSerializerValidate:

    def test_suscripcion_no_pertenece_a_hijo_falla(self, hijo_ser, hijo_otro, suscripcion):
        from apps.almuerzos.serializers import RegistroConsumoAlmuerzoSerializer
        # suscripcion → hijo_ser, pero pasamos hijo_otro → debe fallar
        ser = RegistroConsumoAlmuerzoSerializer(data={
            "hijo": hijo_otro.pk,
            "suscripcion": suscripcion.pk,
            "fecha_consumo": str(date.today()),
        })
        assert not ser.is_valid()
        assert "suscripcion" in ser.errors

    def test_suscripcion_fecha_inicio_posterior_a_consumo_falla(self, hijo_ser, plan_almuerzo):
        from apps.almuerzos.models import SuscripcionAlmuerzo
        from apps.almuerzos.serializers import RegistroConsumoAlmuerzoSerializer
        hoy = date.today()
        sus = SuscripcionAlmuerzo.objects.create(
            hijo=hijo_ser,
            plan=plan_almuerzo,
            fecha_inicio=hoy + timedelta(days=10),
            estado=SuscripcionAlmuerzo.Estado.ACTIVA,
        )
        ser = RegistroConsumoAlmuerzoSerializer(data={
            "hijo": hijo_ser.pk,
            "suscripcion": sus.pk,
            "fecha_consumo": str(hoy),
        })
        assert not ser.is_valid()
        assert "suscripcion" in ser.errors

    def test_suscripcion_vencida_en_fecha_consumo_falla(self, hijo_ser, plan_almuerzo):
        from apps.almuerzos.models import SuscripcionAlmuerzo
        from apps.almuerzos.serializers import RegistroConsumoAlmuerzoSerializer
        hoy = date.today()
        sus = SuscripcionAlmuerzo.objects.create(
            hijo=hijo_ser,
            plan=plan_almuerzo,
            fecha_inicio=hoy - timedelta(days=30),
            fecha_fin=hoy - timedelta(days=1),
            estado=SuscripcionAlmuerzo.Estado.ACTIVA,
        )
        ser = RegistroConsumoAlmuerzoSerializer(data={
            "hijo": hijo_ser.pk,
            "suscripcion": sus.pk,
            "fecha_consumo": str(hoy),
        })
        assert not ser.is_valid()
        assert "suscripcion" in ser.errors


# ==============================================================================
# PagoCuentaAlmuerzoSerializer.validate()
# ==============================================================================

@pytest.mark.django_db
class TestPagoCuentaAlmuerzoSerializerValidate:

    def test_monto_cero_falla(self, cuenta_almuerzo, usuario_cajero):
        from apps.almuerzos.serializers import PagoCuentaAlmuerzoSerializer
        ser = PagoCuentaAlmuerzoSerializer(data={
            "cuenta": cuenta_almuerzo.pk,
            "monto": "0",
            "medio_pago": "EFECTIVO",
            "registrado_por": usuario_cajero.pk,
        })
        assert not ser.is_valid()
        assert "monto" in ser.errors

    def test_monto_negativo_falla(self, cuenta_almuerzo, usuario_cajero):
        from apps.almuerzos.serializers import PagoCuentaAlmuerzoSerializer
        ser = PagoCuentaAlmuerzoSerializer(data={
            "cuenta": cuenta_almuerzo.pk,
            "monto": "-1000",
            "medio_pago": "EFECTIVO",
            "registrado_por": usuario_cajero.pk,
        })
        assert not ser.is_valid()
        assert "monto" in ser.errors

    def test_monto_mayor_a_saldo_pendiente_falla(self, cuenta_almuerzo, usuario_cajero):
        from apps.almuerzos.serializers import PagoCuentaAlmuerzoSerializer
        # saldo_pendiente = monto_total(60000) - monto_pagado(0) = 60000
        ser = PagoCuentaAlmuerzoSerializer(data={
            "cuenta": cuenta_almuerzo.pk,
            "monto": "99999",
            "medio_pago": "EFECTIVO",
            "registrado_por": usuario_cajero.pk,
        })
        assert not ser.is_valid()
        assert "monto" in ser.errors

    def test_monto_valido_ok(self, cuenta_almuerzo, usuario_cajero):
        from apps.almuerzos.serializers import PagoCuentaAlmuerzoSerializer
        ser = PagoCuentaAlmuerzoSerializer(data={
            "cuenta": cuenta_almuerzo.pk,
            "monto": "20000",
            "medio_pago": "EFECTIVO",
            "registrado_por": usuario_cajero.pk,
        })
        assert ser.is_valid(), ser.errors


# ==============================================================================
# PagoAlmuerzoMensualSerializer.validate()
# ==============================================================================

@pytest.mark.django_db
class TestPagoAlmuerzoMensualSerializerValidate:

    def test_mes_anterior_a_inicio_suscripcion_falla(self, suscripcion):
        from apps.almuerzos.serializers import PagoAlmuerzoMensualSerializer
        mes_anterior = (suscripcion.fecha_inicio - timedelta(days=32)).replace(day=1)
        ser = PagoAlmuerzoMensualSerializer(data={
            "suscripcion": suscripcion.pk,
            "mes_pagado": str(mes_anterior),
            "monto_pagado": "12000",
        })
        assert not ser.is_valid()
        assert "mes_pagado" in ser.errors

    def test_mes_posterior_a_fin_suscripcion_falla(self, suscripcion):
        from apps.almuerzos.serializers import PagoAlmuerzoMensualSerializer
        mes_posterior = (suscripcion.fecha_fin + timedelta(days=32)).replace(day=1)
        ser = PagoAlmuerzoMensualSerializer(data={
            "suscripcion": suscripcion.pk,
            "mes_pagado": str(mes_posterior),
            "monto_pagado": "12000",
        })
        assert not ser.is_valid()
        assert "mes_pagado" in ser.errors

    def test_mes_dentro_de_vigencia_ok(self, suscripcion):
        from apps.almuerzos.serializers import PagoAlmuerzoMensualSerializer
        mes_valido = suscripcion.fecha_inicio.replace(day=1)
        ser = PagoAlmuerzoMensualSerializer(data={
            "suscripcion": suscripcion.pk,
            "mes_pagado": str(mes_valido),
            "monto_pagado": "12000",
        })
        assert ser.is_valid(), ser.errors


# ==============================================================================
# DetalleMenuDiarioSerializer.validate_cantidad()
# ==============================================================================

@pytest.mark.django_db
class TestDetalleMenuDiarioSerializerValidateCantidad:

    @pytest.fixture
    def menu_diario(self, db):
        from apps.almuerzos.models import MenuDiario
        return MenuDiario.objects.create(
            fecha=date.today(),
            plato_principal="Sopa de verduras",
        )

    def test_cantidad_cero_falla(self, menu_diario, producto):
        from apps.almuerzos.serializers import DetalleMenuDiarioSerializer
        ser = DetalleMenuDiarioSerializer(data={
            "menu": menu_diario.pk,
            "producto": producto.pk,
            "cantidad": "0",
            "curso": "PLATO_PRINCIPAL",
        })
        assert not ser.is_valid()
        assert "cantidad" in ser.errors

    def test_cantidad_negativa_falla(self, menu_diario, producto):
        from apps.almuerzos.serializers import DetalleMenuDiarioSerializer
        ser = DetalleMenuDiarioSerializer(data={
            "menu": menu_diario.pk,
            "producto": producto.pk,
            "cantidad": "-5",
            "curso": "PLATO_PRINCIPAL",
        })
        assert not ser.is_valid()
        assert "cantidad" in ser.errors

    def test_cantidad_positiva_ok(self, menu_diario, producto):
        from apps.almuerzos.serializers import DetalleMenuDiarioSerializer
        ser = DetalleMenuDiarioSerializer(data={
            "menu": menu_diario.pk,
            "producto": producto.pk,
            "cantidad": "10",
            "curso": "PLATO_PRINCIPAL",
        })
        assert ser.is_valid(), ser.errors
