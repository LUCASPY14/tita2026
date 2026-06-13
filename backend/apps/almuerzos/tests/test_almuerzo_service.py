"""
Tests para AlmuerzoService.registrar_consumo y get_precio_activo.
Cubre: validaciones de tarjeta, fecha futura, primer/segundo registro,
costo en cuenta mensual, límite de crédito mensual.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from rest_framework.exceptions import ValidationError


@pytest.fixture
def grado(db):
    from apps.clientes.models import Grado
    g, _ = Grado.objects.get_or_create(
        nombre="2do grado",
        defaults={"nivel": 2, "orden": 2, "activo": True},
    )
    return g


@pytest.fixture
def hijo_almuerzo(db, cliente, grado):
    from apps.clientes.models import Hijo
    return Hijo.objects.create(
        nombre="Pedro",
        apellido="Almuerzo",
        cliente_responsable=cliente,
        grado=grado,
        activo=True,
    )


@pytest.fixture
def tarjeta_almuerzo(db, hijo_almuerzo):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="ALMZ-001",
        hijo=hijo_almuerzo,
        saldo_actual=Decimal("50000"),
        estado=Tarjeta.Estado.ACTIVA,
    )


@pytest.fixture
def tarjeta_bloqueada_almuerzo(db, hijo_almuerzo):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="ALMZ-002",
        hijo=hijo_almuerzo,
        saldo_actual=Decimal("10000"),
        estado=Tarjeta.Estado.BLOQUEADA,
    )


@pytest.fixture
def precio_almuerzo(db):
    from apps.almuerzos.models import PrecioAlmuerzo
    return PrecioAlmuerzo.objects.create(
        precio_unitario=Decimal("15000"),
        fecha_inicio_vigencia=date.today() - timedelta(days=30),
        activo=True,
    )


@pytest.fixture
def plan_sin_limite(db):
    from apps.almuerzos.models import PlanAlmuerzo
    return PlanAlmuerzo.objects.create(
        nombre="Plan Sin Límite",
        activo=True,
        precio_mensual=Decimal("200000"),
        limite_credito_mensual=None,
    )


@pytest.fixture
def plan_con_limite(db):
    from apps.almuerzos.models import PlanAlmuerzo
    return PlanAlmuerzo.objects.create(
        nombre="Plan Con Límite",
        activo=True,
        precio_mensual=Decimal("200000"),
        limite_credito_mensual=Decimal("10000"),
    )


@pytest.fixture
def suscripcion_activa(db, hijo_almuerzo, plan_sin_limite):
    from apps.almuerzos.models import SuscripcionAlmuerzo
    return SuscripcionAlmuerzo.objects.create(
        hijo=hijo_almuerzo,
        plan=plan_sin_limite,
        fecha_inicio=date.today(),
        estado=SuscripcionAlmuerzo.Estado.ACTIVA,
    )


# ── AlmuerzoService.get_precio_activo ─────────────────────────────────────────

@pytest.mark.django_db
class TestGetPrecioActivo:

    def test_retorna_precio_vigente(self, precio_almuerzo):
        from apps.almuerzos.services import AlmuerzoService
        precio = AlmuerzoService.get_precio_activo()
        assert precio is not None
        assert precio.precio_unitario == Decimal("15000")

    def test_retorna_none_sin_precio_configurado(self, db):
        from apps.almuerzos.services import AlmuerzoService
        precio = AlmuerzoService.get_precio_activo()
        assert precio is None


# ── AlmuerzoService.registrar_consumo ─────────────────────────────────────────

@pytest.mark.django_db
class TestRegistrarConsumo:

    def test_primer_registro_genera_costo(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, precio_almuerzo, suscripcion_activa
    ):
        from apps.almuerzos.services import AlmuerzoService
        from apps.almuerzos.models import CuentaAlmuerzoMensual

        hoy = date.today()
        registro = AlmuerzoService.registrar_consumo(
            hijo=hijo_almuerzo,
            fecha_consumo=hoy,
            nro_tarjeta=tarjeta_almuerzo,
            registrado_por=usuario_cajero,
            suscripcion=suscripcion_activa,
        )

        assert registro.ya_cobrado is True
        assert registro.costo_almuerzo == Decimal("15000")
        cuenta = CuentaAlmuerzoMensual.objects.get(
            hijo=hijo_almuerzo, anio=hoy.year, mes=hoy.month
        )
        assert cuenta.cantidad_almuerzos == 1
        assert cuenta.monto_total == Decimal("15000")

    def test_segundo_registro_sin_costo(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, precio_almuerzo, suscripcion_activa
    ):
        from apps.almuerzos.services import AlmuerzoService

        hoy = date.today()
        AlmuerzoService.registrar_consumo(
            hijo=hijo_almuerzo,
            fecha_consumo=hoy,
            nro_tarjeta=tarjeta_almuerzo,
            registrado_por=usuario_cajero,
            suscripcion=suscripcion_activa,
        )
        segundo = AlmuerzoService.registrar_consumo(
            hijo=hijo_almuerzo,
            fecha_consumo=hoy,
            nro_tarjeta=tarjeta_almuerzo,
            registrado_por=usuario_cajero,
            suscripcion=suscripcion_activa,
        )

        assert segundo.ya_cobrado is False
        assert segundo.costo_almuerzo == Decimal("0")

    def test_tercer_registro_bloqueado(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, precio_almuerzo, suscripcion_activa
    ):
        from apps.almuerzos.services import AlmuerzoService
        from django.core.exceptions import ValidationError as DjangoValidationError

        hoy = date.today()
        for _ in range(2):
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=hoy,
                nro_tarjeta=tarjeta_almuerzo,
                registrado_por=usuario_cajero,
                suscripcion=suscripcion_activa,
            )

        with pytest.raises(DjangoValidationError):
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=hoy,
                nro_tarjeta=tarjeta_almuerzo,
                registrado_por=usuario_cajero,
                suscripcion=suscripcion_activa,
            )

    def test_tarjeta_bloqueada_falla(
        self, hijo_almuerzo, tarjeta_bloqueada_almuerzo, usuario_cajero
    ):
        from apps.almuerzos.services import AlmuerzoService

        with pytest.raises(ValidationError, match="bloqueada"):
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=date.today(),
                nro_tarjeta=tarjeta_bloqueada_almuerzo,
                registrado_por=usuario_cajero,
            )

    def test_fecha_futura_falla(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, precio_almuerzo
    ):
        from apps.almuerzos.services import AlmuerzoService

        manana = date.today() + timedelta(days=1)
        with pytest.raises(ValidationError, match="futura"):
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=manana,
                nro_tarjeta=tarjeta_almuerzo,
                registrado_por=usuario_cajero,
            )

    def test_sin_tarjeta_falla(self, hijo_almuerzo, usuario_cajero):
        from apps.almuerzos.services import AlmuerzoService

        with pytest.raises(ValidationError, match="tarjeta"):
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=date.today(),
                nro_tarjeta=None,
                registrado_por=usuario_cajero,
            )

    def test_sin_precio_configurado_falla(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero
    ):
        from apps.almuerzos.services import AlmuerzoService

        with pytest.raises(ValidationError, match="precio"):
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=date.today(),
                nro_tarjeta=tarjeta_almuerzo,
                registrado_por=usuario_cajero,
            )

    def test_limite_credito_mensual_bloqueado(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, precio_almuerzo, db
    ):
        from apps.almuerzos.models import PlanAlmuerzo, SuscripcionAlmuerzo
        from apps.almuerzos.services import AlmuerzoService

        # Precio = 15000, límite = 10000 → debe bloquear en primer intento
        plan = PlanAlmuerzo.objects.create(
            nombre="Plan Ajustado",
            activo=True,
            precio_mensual=Decimal("200000"),
            limite_credito_mensual=Decimal("10000"),
        )
        suscripcion = SuscripcionAlmuerzo.objects.create(
            hijo=hijo_almuerzo,
            plan=plan,
            fecha_inicio=date.today(),
            estado=SuscripcionAlmuerzo.Estado.ACTIVA,
        )

        with pytest.raises(ValidationError, match="[Ll]imite"):
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=date.today(),
                nro_tarjeta=tarjeta_almuerzo,
                registrado_por=usuario_cajero,
                suscripcion=suscripcion,
            )

    def test_suscripcion_inactiva_falla(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, precio_almuerzo, db
    ):
        from apps.almuerzos.models import PlanAlmuerzo, SuscripcionAlmuerzo
        from apps.almuerzos.services import AlmuerzoService

        plan = PlanAlmuerzo.objects.create(
            nombre="Plan Inactivo",
            activo=True,
            precio_mensual=Decimal("100000"),
        )
        suscripcion = SuscripcionAlmuerzo.objects.create(
            hijo=hijo_almuerzo,
            plan=plan,
            fecha_inicio=date.today(),
            estado=SuscripcionAlmuerzo.Estado.SUSPENDIDA,
        )

        with pytest.raises(ValidationError, match="[Aa]ctiva"):
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=date.today(),
                nro_tarjeta=tarjeta_almuerzo,
                registrado_por=usuario_cajero,
                suscripcion=suscripcion,
            )

    def test_tarjeta_no_pertenece_al_hijo_falla(self, hijo_almuerzo, usuario_cajero, db):
        from apps.almuerzos.services import AlmuerzoService
        from apps.clientes.models import Hijo, Grado

        grado, _ = Grado.objects.get_or_create(
            nombre="5to grado", defaults={"nivel": 5, "orden": 5, "activo": True}
        )
        otro_hijo = Hijo.objects.create(
            nombre="Otro", apellido="Niño",
            cliente_responsable=hijo_almuerzo.cliente_responsable,
            grado=grado, activo=True,
        )
        from apps.core.models import Tarjeta
        tarjeta_otro = Tarjeta.objects.create(
            nro_tarjeta="OTRO-ALMZ-001",
            hijo=otro_hijo,
            saldo_actual=Decimal("50000"),
            estado=Tarjeta.Estado.ACTIVA,
        )

        with pytest.raises(ValidationError, match="pertenece"):
            AlmuerzoService.registrar_consumo(
                hijo=hijo_almuerzo,
                fecha_consumo=date.today(),
                nro_tarjeta=tarjeta_otro,
                registrado_por=usuario_cajero,
            )

    def test_usa_tipo_almuerzo_si_no_hay_precio_activo(
        self, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, suscripcion_activa, db
    ):
        from apps.almuerzos.services import AlmuerzoService
        from apps.almuerzos.models import TipoAlmuerzo

        tipo = TipoAlmuerzo.objects.create(
            nombre="Almuerzo Básico Test",
            precio_unitario=Decimal("12000"),
            activo=True,
        )
        registro = AlmuerzoService.registrar_consumo(
            hijo=hijo_almuerzo,
            fecha_consumo=date.today(),
            nro_tarjeta=tarjeta_almuerzo,
            registrado_por=usuario_cajero,
            suscripcion=suscripcion_activa,
            tipo_almuerzo=tipo,
        )
        assert registro.costo_almuerzo == Decimal("12000")
