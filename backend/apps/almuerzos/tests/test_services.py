"""
Tests para almuerzos — generar_cuentas_mensuales y alertar_cuentas_vencidas.
"""
import pytest
from decimal import Decimal
from datetime import date


@pytest.fixture
def hijo_con_grado(db, cliente):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="María",
        apellido="López",
        cliente_responsable=cliente,
        grado="1er grado",
        activo=True,
    )


@pytest.fixture
def plan_almuerzo(db):
    from apps.almuerzos.models import PlanAlmuerzo
    return PlanAlmuerzo.objects.create(
        nombre="Plan Mensual",
        activo=True,
        precio_mensual=Decimal("200000"),
    )


@pytest.fixture
def suscripcion(db, hijo_con_grado, plan_almuerzo):
    from apps.almuerzos.models import SuscripcionAlmuerzo
    return SuscripcionAlmuerzo.objects.create(
        hijo=hijo_con_grado,
        plan=plan_almuerzo,
        fecha_inicio=date.today(),
        estado=SuscripcionAlmuerzo.Estado.ACTIVA,
    )


@pytest.mark.django_db
class TestGenerar_CuentasMensuales:

    def test_genera_cuenta_para_suscripcion_activa(self, suscripcion, hijo_con_grado):
        from apps.almuerzos.tasks import generar_cuentas_mensuales
        from apps.almuerzos.models import CuentaAlmuerzoMensual

        hoy = date.today()
        result = generar_cuentas_mensuales()

        assert CuentaAlmuerzoMensual.objects.filter(
            hijo=hijo_con_grado,
            mes=hoy.month,
            anio=hoy.year,
        ).exists()

    def test_no_duplica_cuentas_del_mismo_mes(self, suscripcion, hijo_con_grado):
        from apps.almuerzos.tasks import generar_cuentas_mensuales
        from apps.almuerzos.models import CuentaAlmuerzoMensual

        hoy = date.today()
        generar_cuentas_mensuales()
        generar_cuentas_mensuales()

        count = CuentaAlmuerzoMensual.objects.filter(
            hijo=hijo_con_grado,
            mes=hoy.month,
            anio=hoy.year,
        ).count()
        assert count == 1


@pytest.mark.django_db
class TestAlergenosValidacion:

    def test_sin_restricciones_no_genera_advertencias(self, hijo_con_grado):
        from apps.almuerzos.validators import verificar_alergenos_venta

        advertencias = verificar_alergenos_venta(hijo_con_grado, [])
        assert advertencias == []

    def test_producto_sin_alergenos_no_advierte(self, hijo_con_grado, producto):
        from apps.almuerzos.validators import verificar_alergenos_venta

        advertencias = verificar_alergenos_venta(hijo_con_grado, [producto])
        assert advertencias == []
