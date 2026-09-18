"""
Tests para almuerzos — verificar_alergenos_venta.
"""
import pytest


@pytest.fixture
def hijo_con_grado(db, cliente):
    from apps.clientes.models import Hijo, Grado
    grado, _ = Grado.objects.get_or_create(
        nombre="1er grado",
        defaults={"nivel": 1, "orden": 1, "activo": True},
    )
    return Hijo.objects.create(
        nombre="María",
        apellido="López",
        cliente_responsable=cliente,
        grado=grado,
        activo=True,
    )


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
