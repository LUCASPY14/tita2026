"""
Tests para clientes/services.py.
Cubre: cambiar_titular, agregar_responsable.
"""
import pytest
from decimal import Decimal


@pytest.fixture
def hijo_con_responsables(db, cliente, tipo_cliente, lista_precio):
    from apps.clientes.models import Hijo, Cliente, AlumnoResponsable, Grado

    grado, _ = Grado.objects.get_or_create(
        nombre="1er grado srv", defaults={"nivel": 1, "orden": 1, "activo": True}
    )
    hijo = Hijo.objects.create(
        nombre="Titular",
        apellido="Test",
        cliente_responsable=cliente,
        grado=grado,
        activo=True,
    )
    AlumnoResponsable.objects.create(
        hijo=hijo,
        cliente=cliente,
        parentesco=AlumnoResponsable.Parentesco.PADRE,
        es_titular=True,
        activo=True,
    )

    cliente2 = Cliente.objects.create(
        nombres="Segundo",
        apellidos="Responsable",
        ruc_ci="9876543",
        tipo_cliente=tipo_cliente,
        lista_precio=lista_precio,
        limite_credito=Decimal("0"),
    )
    AlumnoResponsable.objects.create(
        hijo=hijo,
        cliente=cliente2,
        parentesco=AlumnoResponsable.Parentesco.MADRE,
        es_titular=False,
        activo=True,
    )

    return hijo, cliente, cliente2


# ── cambiar_titular ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCambiarTitular:

    def test_cambiar_titular_exitoso(self, hijo_con_responsables):
        from apps.clientes.services import cambiar_titular
        from apps.clientes.models import AlumnoResponsable

        hijo, cliente_actual, cliente_nuevo = hijo_con_responsables

        nuevo_resp = cambiar_titular(hijo, cliente_nuevo.pk)

        assert nuevo_resp.es_titular is True
        assert nuevo_resp.cliente_id == cliente_nuevo.pk

        hijo.refresh_from_db()
        assert hijo.cliente_responsable_id == cliente_nuevo.pk

        # El anterior ya no es titular
        anterior = AlumnoResponsable.objects.get(hijo=hijo, cliente=cliente_actual)
        assert anterior.es_titular is False

    def test_cambiar_titular_responsable_inexistente_falla(self, hijo_con_responsables):
        from apps.clientes.services import cambiar_titular
        from apps.clientes.models import AlumnoResponsable

        hijo, _, _ = hijo_con_responsables

        with pytest.raises(AlumnoResponsable.DoesNotExist):
            cambiar_titular(hijo, 99999)

    def test_cambiar_titular_responsable_inactivo_falla(self, hijo_con_responsables):
        from apps.clientes.services import cambiar_titular
        from apps.clientes.models import AlumnoResponsable

        hijo, _, cliente_nuevo = hijo_con_responsables
        AlumnoResponsable.objects.filter(hijo=hijo, cliente=cliente_nuevo).update(activo=False)

        with pytest.raises(ValueError, match="inactivo"):
            cambiar_titular(hijo, cliente_nuevo.pk)


# ── agregar_responsable ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAgregarResponsable:

    def test_agregar_responsable_nuevo(self, hijo_con_responsables, tipo_cliente, lista_precio):
        from apps.clientes.services import agregar_responsable
        from apps.clientes.models import Cliente, AlumnoResponsable

        hijo, _, _ = hijo_con_responsables
        cliente_nuevo = Cliente.objects.create(
            nombres="Tercero",
            apellidos="Resp",
            ruc_ci="1111112",
            tipo_cliente=tipo_cliente,
            lista_precio=lista_precio,
        )

        resp = agregar_responsable(
            hijo=hijo,
            cliente_id=cliente_nuevo.pk,
            parentesco=AlumnoResponsable.Parentesco.TUTOR,
            orden_cobro=3,
            recibe_notificaciones=True,
        )

        assert resp.activo is True
        assert resp.recibe_notificaciones is True

    def test_agregar_responsable_idempotente(self, hijo_con_responsables):
        from apps.clientes.services import agregar_responsable
        from apps.clientes.models import AlumnoResponsable

        hijo, _, cliente2 = hijo_con_responsables

        # Llamar dos veces con el mismo cliente
        resp1 = agregar_responsable(
            hijo=hijo,
            cliente_id=cliente2.pk,
            parentesco=AlumnoResponsable.Parentesco.MADRE,
        )
        resp2 = agregar_responsable(
            hijo=hijo,
            cliente_id=cliente2.pk,
            parentesco=AlumnoResponsable.Parentesco.MADRE,
        )

        assert resp1.pk == resp2.pk
        assert AlumnoResponsable.objects.filter(hijo=hijo, cliente=cliente2).count() == 1

    def test_reactivar_responsable_inactivo(self, hijo_con_responsables):
        from apps.clientes.services import agregar_responsable
        from apps.clientes.models import AlumnoResponsable

        hijo, _, cliente2 = hijo_con_responsables
        AlumnoResponsable.objects.filter(hijo=hijo, cliente=cliente2).update(activo=False)

        resp = agregar_responsable(
            hijo=hijo,
            cliente_id=cliente2.pk,
            parentesco=AlumnoResponsable.Parentesco.MADRE,
        )

        assert resp.activo is True
