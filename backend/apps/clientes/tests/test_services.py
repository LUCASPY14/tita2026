"""
Tests para clientes/services.py.
Cubre: cambiar_titular, agregar_responsable, resolver_origen_pago_cc.
"""
import pytest
from decimal import Decimal
from rest_framework.exceptions import ValidationError


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


# ── crear_responsable_con_cliente_nuevo ─────────────────────────────────────

@pytest.mark.django_db
class TestCrearResponsableConClienteNuevo:

    def test_crea_cliente_tipo_familia_y_responsable(self, hijo_con_responsables):
        from apps.clientes.services import crear_responsable_con_cliente_nuevo
        from apps.clientes.models import AlumnoResponsable, TipoCliente

        hijo, _, _ = hijo_con_responsables
        resp = crear_responsable_con_cliente_nuevo(
            hijo=hijo,
            datos_cliente={"nombres": "Elena", "apellidos": "Cruz", "ruc_ci": "5551234"},
            parentesco=AlumnoResponsable.Parentesco.TIA,
        )
        assert resp.cliente.nombres == "Elena" and resp.cliente.ruc_ci == "5551234"
        assert resp.cliente.tipo_cliente == TipoCliente.objects.get(nombre="Familia")
        assert resp.es_titular is False

    def test_usa_la_lista_de_precio_por_defecto(self, hijo_con_responsables, lista_precio):
        from apps.clientes.services import crear_responsable_con_cliente_nuevo
        from apps.clientes.models import AlumnoResponsable
        from apps.productos.models import ListaPrecio

        lista_precio.es_por_defecto = True
        lista_precio.save()
        hijo, _, _ = hijo_con_responsables
        resp = crear_responsable_con_cliente_nuevo(
            hijo=hijo,
            datos_cliente={"nombres": "Fabio", "apellidos": "Ruiz", "ruc_ci": "5551235"},
            parentesco=AlumnoResponsable.Parentesco.TIO,
        )
        assert resp.cliente.lista_precio == lista_precio

    def test_sin_lista_por_defecto_crea_lista_general(self, hijo_con_responsables):
        from apps.clientes.services import crear_responsable_con_cliente_nuevo
        from apps.clientes.models import AlumnoResponsable
        from apps.productos.models import ListaPrecio

        hijo, _, _ = hijo_con_responsables
        resp = crear_responsable_con_cliente_nuevo(
            hijo=hijo,
            datos_cliente={"nombres": "Gina", "apellidos": "Ortiz", "ruc_ci": "5551236"},
            parentesco=AlumnoResponsable.Parentesco.OTRO,
        )
        assert resp.cliente.lista_precio == ListaPrecio.objects.get(nombre="Lista General")

    def test_ruc_ci_existente_no_crea_duplicado(self, hijo_con_responsables):
        from apps.clientes.services import crear_responsable_con_cliente_nuevo
        from apps.clientes.models import AlumnoResponsable, Cliente

        hijo, cliente1, _ = hijo_con_responsables
        with pytest.raises(ValidationError) as exc:
            crear_responsable_con_cliente_nuevo(
                hijo=hijo,
                datos_cliente={"nombres": "Copia", "apellidos": "De", "ruc_ci": cliente1.ruc_ci},
                parentesco=AlumnoResponsable.Parentesco.OTRO,
            )
        assert cliente1.nombre_completo in str(exc.value.detail["ruc_ci"])
        assert Cliente.objects.filter(ruc_ci=cliente1.ruc_ci).count() == 1

    def test_crea_usuario_portal_para_el_cliente_nuevo(self, hijo_con_responsables):
        from apps.clientes.services import crear_responsable_con_cliente_nuevo
        from apps.clientes.models import AlumnoResponsable
        from apps.usuarios.models import Usuario

        hijo, _, _ = hijo_con_responsables
        resp = crear_responsable_con_cliente_nuevo(
            hijo=hijo,
            datos_cliente={"nombres": "Hugo", "apellidos": "Vera", "ruc_ci": "5551237", "email": "hugo@test.com"},
            parentesco=AlumnoResponsable.Parentesco.ABUELO,
        )
        usuario = Usuario.objects.get(cliente=resp.cliente)
        assert usuario.email == "hugo@test.com" and usuario.rol == Usuario.Rol.CLIENTE_WEB


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


# ── resolver_origen_pago_cc ────────────────────────────────────────────────────

def _crear_deuda(cliente, usuario, monto, origen):
    from apps.clientes.models import CuentaCorrienteCliente
    saldo_anterior = cliente.saldo_cuenta_corriente
    CuentaCorrienteCliente.objects.create(
        cliente=cliente, tipo=CuentaCorrienteCliente.Tipo.DEBITO,
        monto=Decimal(monto), saldo_anterior=saldo_anterior, saldo_resultante=saldo_anterior + monto,
        creado_por=usuario, origen=origen,
    )


@pytest.mark.django_db
class TestResolverOrigenPagoCC:

    def test_sin_deuda_categorizada_retorna_general(self, cliente):
        from apps.clientes.services import resolver_origen_pago_cc
        origen = resolver_origen_pago_cc(cliente, None, Decimal("10000"))
        assert origen == "GENERAL"

    def test_solo_cantina_infiere_sin_pedir_origen(self, cliente, usuario_cajero):
        from apps.clientes.models import CuentaCorrienteCliente
        from apps.clientes.services import resolver_origen_pago_cc
        _crear_deuda(cliente, usuario_cajero, 100000, CuentaCorrienteCliente.Origen.CANTINA)
        origen = resolver_origen_pago_cc(cliente, None, Decimal("50000"))
        assert origen == "CANTINA"

    def test_solo_almuerzo_infiere_sin_pedir_origen(self, cliente, usuario_cajero):
        from apps.clientes.models import CuentaCorrienteCliente
        from apps.clientes.services import resolver_origen_pago_cc
        _crear_deuda(cliente, usuario_cajero, 100000, CuentaCorrienteCliente.Origen.ALMUERZO)
        origen = resolver_origen_pago_cc(cliente, None, Decimal("50000"))
        assert origen == "ALMUERZO"

    def test_ambas_categorias_sin_origen_falla(self, cliente, usuario_cajero):
        from apps.clientes.models import CuentaCorrienteCliente
        from apps.clientes.services import resolver_origen_pago_cc
        _crear_deuda(cliente, usuario_cajero, 100000, CuentaCorrienteCliente.Origen.CANTINA)
        _crear_deuda(cliente, usuario_cajero, 50000, CuentaCorrienteCliente.Origen.ALMUERZO)
        with pytest.raises(ValidationError, match="origen"):
            resolver_origen_pago_cc(cliente, None, Decimal("30000"))

    def test_ambas_categorias_con_origen_valido_ok(self, cliente, usuario_cajero):
        from apps.clientes.models import CuentaCorrienteCliente
        from apps.clientes.services import resolver_origen_pago_cc
        _crear_deuda(cliente, usuario_cajero, 100000, CuentaCorrienteCliente.Origen.CANTINA)
        _crear_deuda(cliente, usuario_cajero, 50000, CuentaCorrienteCliente.Origen.ALMUERZO)
        origen = resolver_origen_pago_cc(cliente, "almuerzo", Decimal("30000"))
        assert origen == "ALMUERZO"

    def test_monto_supera_deuda_de_la_categoria_falla(self, cliente, usuario_cajero):
        from apps.clientes.models import CuentaCorrienteCliente
        from apps.clientes.services import resolver_origen_pago_cc
        _crear_deuda(cliente, usuario_cajero, 100000, CuentaCorrienteCliente.Origen.CANTINA)
        _crear_deuda(cliente, usuario_cajero, 50000, CuentaCorrienteCliente.Origen.ALMUERZO)
        with pytest.raises(ValidationError, match="monto"):
            resolver_origen_pago_cc(cliente, "ALMUERZO", Decimal("60000"))

    def test_monto_igual_a_la_deuda_de_la_categoria_ok(self, cliente, usuario_cajero):
        from apps.clientes.models import CuentaCorrienteCliente
        from apps.clientes.services import resolver_origen_pago_cc
        _crear_deuda(cliente, usuario_cajero, 100000, CuentaCorrienteCliente.Origen.CANTINA)
        _crear_deuda(cliente, usuario_cajero, 50000, CuentaCorrienteCliente.Origen.ALMUERZO)
        origen = resolver_origen_pago_cc(cliente, "ALMUERZO", Decimal("50000"))
        assert origen == "ALMUERZO"

    def test_deuda_categoria_inflada_por_credito_general_se_limita_al_total(
        self, cliente, usuario_cajero,
    ):
        """Un pago histórico sin clasificar (origen GENERAL) reduce la deuda
        total pero no se resta de ninguna categoría — la deuda por categoría
        queda inflada y nunca debe permitir pagar más que la deuda real."""
        from apps.clientes.models import CuentaCorrienteCliente
        from apps.clientes.services import resolver_origen_pago_cc
        _crear_deuda(cliente, usuario_cajero, 100000, CuentaCorrienteCliente.Origen.CANTINA)
        _crear_deuda(cliente, usuario_cajero, 50000, CuentaCorrienteCliente.Origen.ALMUERZO)
        # Pago sin clasificar que reduce la deuda total (150000 -> 70000)
        # pero no la de ninguna categoría (siguen en 100000 y 50000).
        CuentaCorrienteCliente.objects.create(
            cliente=cliente, tipo=CuentaCorrienteCliente.Tipo.CREDITO,
            monto=Decimal("80000"), saldo_anterior=Decimal("150000"),
            saldo_resultante=Decimal("70000"),
            creado_por=usuario_cajero, origen=CuentaCorrienteCliente.Origen.GENERAL,
        )
        assert cliente.saldo_cuenta_corriente == Decimal("70000")
        assert cliente.saldo_cc_cantina == Decimal("100000")

        with pytest.raises(ValidationError, match="monto"):
            resolver_origen_pago_cc(cliente, "CANTINA", Decimal("80000"))

        origen = resolver_origen_pago_cc(cliente, "CANTINA", Decimal("70000"))
        assert origen == "CANTINA"
