"""
Tests de vistas de almuerzos.
Cubre: PrecioAlmuerzoViewSet, TipoAlmuerzoViewSet,
SuscripcionAlmuerzoViewSet, RegistroConsumoAlmuerzoViewSet (create + validaciones),
CuentaAlmuerzoMensualViewSet (generar, CLIENTE_WEB filter), PagoCuentaAlmuerzoViewSet,
AlergenoViewSet, ProductoAlergenoViewSet,
MenuDiarioViewSet (hoy), DetalleMenuDiarioViewSet, ReporteAlmuerzosView.
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from freezegun import freeze_time
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def api_admin(api_client, usuario_admin):
    api_client.force_authenticate(user=usuario_admin)
    return api_client


@pytest.fixture
def api_cajero(api_client, usuario_cajero):
    api_client.force_authenticate(user=usuario_cajero)
    return api_client


@pytest.fixture
def grado(db):
    from apps.clientes.models import Grado
    g, _ = Grado.objects.get_or_create(
        nombre="3er grado",
        defaults={"nivel": 3, "orden": 3, "activo": True},
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
        nro_tarjeta="ALMZ-VIEW01",
        hijo=hijo_almuerzo,
        saldo_actual=Decimal("50000"),
        estado=Tarjeta.Estado.ACTIVA,
    )


@pytest.fixture
def tarjeta_bloqueada(db, hijo_almuerzo):
    from apps.core.models import Tarjeta
    return Tarjeta.objects.create(
        nro_tarjeta="ALMZ-BLQ01",
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
def tipo_almuerzo(db):
    from apps.almuerzos.models import TipoAlmuerzo
    return TipoAlmuerzo.objects.create(
        nombre="Almuerzo Estándar View",
        precio_unitario=Decimal("12000"),
        activo=True,
    )


@pytest.fixture
def suscripcion_activa(db, hijo_almuerzo):
    from apps.almuerzos.models import SuscripcionAlmuerzo
    return SuscripcionAlmuerzo.objects.create(
        hijo=hijo_almuerzo,
        fecha_inicio=date.today(),
        estado=SuscripcionAlmuerzo.Estado.ACTIVA,
    )


@pytest.fixture
def suscripcion_suspendida(db, hijo_almuerzo):
    # sin fecha_fin para que el serializer no la rechace por vencida
    from apps.almuerzos.models import SuscripcionAlmuerzo
    return SuscripcionAlmuerzo.objects.create(
        hijo=hijo_almuerzo,
        fecha_inicio=date.today() - timedelta(days=60),
        estado=SuscripcionAlmuerzo.Estado.SUSPENDIDA,
    )


@pytest.fixture
def alergeno(db):
    from apps.almuerzos.models import Alergeno
    return Alergeno.objects.create(
        nombre="Maní",
        activo=True,
        severidad="ALTA",
    )


@pytest.fixture
def consumos_mes_actual(db, hijo_almuerzo, usuario_cajero):
    """5 almuerzos REGISTRADO+cobrados del hijo_almuerzo en el mes actual —
    equivalente vivo al viejo fixture cuenta_mensual, para los reportes que
    ahora agregan directo de RegistroConsumoAlmuerzo."""
    from apps.almuerzos.models import RegistroConsumoAlmuerzo
    hoy = date.today()
    return [
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, fecha_consumo=hoy, costo_almuerzo=Decimal("15000"),
            ya_cobrado=True, registrado_por=usuario_cajero,
        )
        for _ in range(5)
    ]


@pytest.fixture
def cuenta_mensual(db, hijo_almuerzo):
    from apps.almuerzos.models import CuentaAlmuerzoMensual
    hoy = date.today()
    return CuentaAlmuerzoMensual.objects.create(
        hijo=hijo_almuerzo,
        anio=hoy.year,
        mes=hoy.month,
        cantidad_almuerzos=5,
        monto_total=Decimal("75000"),
        monto_pagado=Decimal("0"),
        forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
        estado=CuentaAlmuerzoMensual.Estado.PENDIENTE,
    )


@pytest.fixture
def menu_hoy(db, usuario_admin):
    from apps.almuerzos.models import MenuDiario
    return MenuDiario.objects.create(
        # timezone.localdate() (no date.today()): la vista "hoy" filtra con
        # timezone.localdate(), y en tests TIME_ZONE=UTC — usar la misma
        # fuente que la vista evita que el fixture y la vista discrepen
        # según la hora del reloj real de la máquina que corre el test.
        fecha=timezone.localdate(),
        plato_principal="Milanesa con papas",
        activo=True,
        creado_por=usuario_admin,
    )


@pytest.fixture
def usuario_cliente_web(db, cliente):
    from apps.usuarios.models import Usuario
    return Usuario.objects.create_user(
        email="almweb@test.com",
        password="test1234",
        nombre="Web",
        apellido="Alm",
        rol=Usuario.Rol.CLIENTE_WEB,
        cliente=cliente,
    )


@pytest.fixture
def api_cliente_web(api_client, usuario_cliente_web):
    api_client.force_authenticate(user=usuario_cliente_web)
    return api_client


# ── ViewSets simples ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestViewSetsSimples:

    def test_precios_almuerzo_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/almuerzos/precios-almuerzo/")
        assert resp.status_code == 200

    def test_tipos_almuerzo_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/almuerzos/tipos-almuerzo/")
        assert resp.status_code == 200

    def test_suscripciones_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/almuerzos/suscripciones/")
        assert resp.status_code == 200

    def test_alergenos_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/almuerzos/alergenos/")
        assert resp.status_code == 200

    def test_productos_alergenos_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/almuerzos/productos-alergenos/")
        assert resp.status_code == 200

    def test_cuentas_mensuales_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/almuerzos/cuentas-mensuales/")
        assert resp.status_code == 200

    def test_pagos_cuentas_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/almuerzos/pagos-cuentas/")
        assert resp.status_code == 200

    def test_menu_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/almuerzos/menu/")
        assert resp.status_code == 200

    def test_detalle_menu_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/almuerzos/detalle-menu/")
        assert resp.status_code == 200

    def test_registros_consumo_list(self, api_cajero):
        resp = api_cajero.get("/api/v1/almuerzos/registros-consumo/")
        assert resp.status_code == 200

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/almuerzos/menu/")
        assert resp.status_code in (401, 403)


# ── SuscripcionAlmuerzoViewSet — acceso CLIENTE_WEB ───────────────────────────
# Antes de este fix, el ViewSet no tenía permission_classes propio y heredaba
# el default IsStaffUser (que excluye CLIENTE_WEB) → el portal de padres
# recibía 403 y mostraba "Sin plan de almuerzo activo" aunque sí hubiera uno.

@pytest.mark.django_db
class TestSuscripcionAlmuerzoAccesoClienteWeb:

    def test_cliente_web_puede_ver_la_suscripcion_de_su_hijo(self, api_cliente_web, suscripcion_activa, hijo_almuerzo):
        resp = api_cliente_web.get(
            "/api/v1/almuerzos/suscripciones/", {"hijo": hijo_almuerzo.id_hijo, "estado": "ACTIVA"}
        )
        assert resp.status_code == 200
        ids = [s["id_suscripcion"] for s in resp.data["results"]]
        assert suscripcion_activa.id_suscripcion in ids

    def test_cliente_web_no_ve_suscripciones_de_otra_familia(
        self, api_cliente_web, suscripcion_activa, tipo_cliente, lista_precio
    ):
        from decimal import Decimal
        from apps.clientes.models import Cliente, Hijo
        from apps.almuerzos.models import SuscripcionAlmuerzo

        otro_cliente = Cliente.objects.create(
            nombres="Otra", apellidos="Familia", ruc_ci="9998887",
            tipo_cliente=tipo_cliente, lista_precio=lista_precio,
            limite_credito=Decimal("100000"),
        )
        otro_hijo = Hijo.objects.create(
            nombre="Ajeno", apellido="Hijo", cliente_responsable=otro_cliente, activo=True,
        )
        otra_suscripcion = SuscripcionAlmuerzo.objects.create(
            hijo=otro_hijo,
            fecha_inicio=suscripcion_activa.fecha_inicio,
            estado=SuscripcionAlmuerzo.Estado.ACTIVA,
        )

        resp = api_cliente_web.get("/api/v1/almuerzos/suscripciones/")
        assert resp.status_code == 200
        ids = [s["id_suscripcion"] for s in resp.data["results"]]
        assert otra_suscripcion.id_suscripcion not in ids

    def test_cliente_web_no_puede_crear_suscripciones(self, api_cliente_web, hijo_almuerzo):
        resp = api_cliente_web.post("/api/v1/almuerzos/suscripciones/", {
            "hijo": hijo_almuerzo.id_hijo,
            "fecha_inicio": str(date.today()),
        })
        assert resp.status_code == 403

    def test_cajero_sigue_viendo_todas_las_suscripciones(self, api_cajero, suscripcion_activa):
        resp = api_cajero.get("/api/v1/almuerzos/suscripciones/")
        assert resp.status_code == 200
        ids = [s["id_suscripcion"] for s in resp.data["results"]]
        assert suscripcion_activa.id_suscripcion in ids


# ── SuscripcionAlmuerzoViewSet — una sola activa por hijo ─────────────────────

@pytest.mark.django_db
class TestSuscripcionUnicaActivaPorHijo:

    def test_segunda_suscripcion_activa_da_400_legible(
        self, api_admin, hijo_almuerzo, suscripcion_activa
    ):
        # unique_suscripcion_activa_por_hijo daría un IntegrityError (500) sin
        # la validación explícita del serializer.
        resp = api_admin.post("/api/v1/almuerzos/suscripciones/", {
            "hijo": hijo_almuerzo.id_hijo,
            "fecha_inicio": str(date.today()),
        })
        assert resp.status_code == 400
        assert "hijo" in resp.data["field_errors"]

    def test_segunda_suscripcion_no_activa_se_permite(
        self, api_admin, hijo_almuerzo, suscripcion_activa
    ):
        resp = api_admin.post("/api/v1/almuerzos/suscripciones/", {
            "hijo": hijo_almuerzo.id_hijo,
            "fecha_inicio": str(date.today()),
            "estado": "CANCELADA",
        })
        assert resp.status_code == 201

    def test_activar_suscripcion_cuando_ya_hay_otra_activa_falla(
        self, api_admin, hijo_almuerzo, suscripcion_activa
    ):
        from apps.almuerzos.models import SuscripcionAlmuerzo
        otra = SuscripcionAlmuerzo.objects.create(
            hijo=hijo_almuerzo,
            fecha_inicio=date.today(), estado=SuscripcionAlmuerzo.Estado.CANCELADA,
        )
        resp = api_admin.patch(
            f"/api/v1/almuerzos/suscripciones/{otra.pk}/", {"estado": "ACTIVA"},
        )
        assert resp.status_code == 400

    def test_reemplazar_la_propia_suscripcion_activa_no_falla(
        self, api_admin, suscripcion_activa
    ):
        # Editar campos de la MISMA suscripción activa (no crear otra) no
        # debe chocar consigo misma.
        resp = api_admin.patch(
            f"/api/v1/almuerzos/suscripciones/{suscripcion_activa.pk}/",
            {"estado": "ACTIVA"},
        )
        assert resp.status_code == 200


# ── PrecioAlmuerzoViewSet — precio_actual ─────────────────────────────────────

@pytest.mark.django_db
class TestPrecioActual:

    def test_sin_precio_retorna_404(self, api_cajero):
        resp = api_cajero.get("/api/v1/almuerzos/precios-almuerzo/precio-actual/")
        assert resp.status_code == 404

    def test_con_precio_retorna_datos(self, api_cajero, precio_almuerzo):
        resp = api_cajero.get("/api/v1/almuerzos/precios-almuerzo/precio-actual/")
        assert resp.status_code == 200
        assert resp.data["precio_unitario"] == "15000"


# ── MenuDiarioViewSet — hoy ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestMenuHoy:

    def test_sin_menu_hoy_retorna_404(self, api_cajero):
        resp = api_cajero.get("/api/v1/almuerzos/menu/hoy/")
        assert resp.status_code == 404

    def test_con_menu_hoy_retorna_datos(self, api_cajero, menu_hoy):
        resp = api_cajero.get("/api/v1/almuerzos/menu/hoy/")
        assert resp.status_code == 200
        assert resp.data["plato_principal"] == "Milanesa con papas"

    def test_create_asigna_creado_por(self, api_admin):
        resp = api_admin.post(
            "/api/v1/almuerzos/menu/",
            {"fecha": str(date.today() + timedelta(days=1)), "plato_principal": "Pollo asado", "activo": True},
            format="json",
        )
        assert resp.status_code == 201

    @override_settings(TIME_ZONE="America/Asuncion")
    @freeze_time("2026-09-23 01:00:00")  # 22:00 del 22/09 en Paraguay (UTC-3)
    def test_usa_fecha_local_no_utc_pasada_la_medianoche_utc(self, api_cajero, usuario_admin):
        """
        A esta hora ya es "mañana" en UTC pero todavía "hoy" en Paraguay.
        La vista debe resolver con timezone.localdate() (fecha de Paraguay);
        si usara date.today() en un contenedor con reloj UTC, buscaría el
        menú de un día que para la escuela todavía no llegó.
        """
        from apps.almuerzos.models import MenuDiario
        MenuDiario.objects.create(
            fecha=timezone.localdate(),  # 2026-09-22, la fecha real en Paraguay
            plato_principal="Sopa paraguaya",
            activo=True,
            creado_por=usuario_admin,
        )
        resp = api_cajero.get("/api/v1/almuerzos/menu/hoy/")
        assert resp.status_code == 200
        assert resp.data["plato_principal"] == "Sopa paraguaya"


# ── RegistroConsumoAlmuerzoViewSet ────────────────────────────────────────────

@pytest.mark.django_db
class TestRegistroConsumoDestroy:

    def test_destroy_siempre_405(self, api_cajero, hijo_almuerzo, tarjeta_almuerzo,
                                 precio_almuerzo, usuario_cajero):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        registro = RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo,
            fecha_consumo=date.today() - timedelta(days=1),
            costo_almuerzo=Decimal("15000"),
            ya_cobrado=True,
            nro_tarjeta=tarjeta_almuerzo,
            registrado_por=usuario_cajero,
            estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
        )
        resp = api_cajero.delete(f"/api/v1/almuerzos/registros-consumo/{registro.pk}/")
        assert resp.status_code == 403  # solo ADMIN puede eliminar


@pytest.fixture
def api_cocina_consumo(api_client):
    from apps.usuarios.models import Usuario
    cocina = Usuario.objects.create_user(
        email="cocina-consumo@test.com", password="test1234",
        nombre="Cocina", apellido="Consumo", rol=Usuario.Rol.COCINA,
    )
    api_client.force_authenticate(user=cocina)
    return api_client


@pytest.fixture
def api_supervisor_consumo(api_client):
    from apps.usuarios.models import Usuario
    supervisor = Usuario.objects.create_user(
        email="supervisor-consumo@test.com", password="test1234",
        nombre="Supervisor", apellido="Consumo", rol=Usuario.Rol.SUPERVISOR,
    )
    api_client.force_authenticate(user=supervisor)
    return api_client


@pytest.mark.django_db
class TestRegistroConsumoCreate:

    def test_primer_registro_ok(self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, precio_almuerzo, suscripcion_activa):
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk,
                "fecha_consumo": str(date.today()),
                "nro_tarjeta": tarjeta_almuerzo.pk,
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["ya_cobrado"] is True
        assert resp.data["costo_almuerzo"] == "15000"

    def test_cocina_puede_registrar(
        self, api_cocina_consumo, hijo_almuerzo, tarjeta_almuerzo, precio_almuerzo, suscripcion_activa,
    ):
        # Bug real reportado en producción: la pantalla /comedor es para
        # COCINA, pero el permiso estaba restringido a Cajero/Admin (403
        # "Usted no tiene permiso para realizar esta acción").
        resp = api_cocina_consumo.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk,
                "fecha_consumo": str(date.today()),
                "nro_tarjeta": tarjeta_almuerzo.pk,
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_supervisor_puede_registrar(
        self, api_supervisor_consumo, hijo_almuerzo, tarjeta_almuerzo, precio_almuerzo, suscripcion_activa,
    ):
        resp = api_supervisor_consumo.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk,
                "fecha_consumo": str(date.today()),
                "nro_tarjeta": tarjeta_almuerzo.pk,
            },
            format="json",
        )
        assert resp.status_code == 201

    def test_cliente_web_no_puede_registrar(
        self, api_cliente_web, hijo_almuerzo, tarjeta_almuerzo, precio_almuerzo, suscripcion_activa,
    ):
        resp = api_cliente_web.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk,
                "fecha_consumo": str(date.today()),
                "nro_tarjeta": tarjeta_almuerzo.pk,
            },
            format="json",
        )
        assert resp.status_code == 403

    def test_client_request_id_repetido_no_duplica_el_registro(
        self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, precio_almuerzo, suscripcion_activa,
    ):
        # Simula el reintento de la cola offline del Service Worker: perdió
        # la respuesta del primer POST (no la request) y reenvía el mismo
        # body con el mismo client_request_id.
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        body = {
            "hijo": hijo_almuerzo.pk,
            "fecha_consumo": str(date.today()),
            "nro_tarjeta": tarjeta_almuerzo.pk,
            "client_request_id": "11111111-1111-1111-1111-111111111111",
        }
        resp1 = api_cajero.post("/api/v1/almuerzos/registros-consumo/", body, format="json")
        resp2 = api_cajero.post("/api/v1/almuerzos/registros-consumo/", body, format="json")

        assert resp1.status_code == 201
        assert resp2.status_code == 201
        assert resp1.data["id_registro_consumo"] == resp2.data["id_registro_consumo"]
        assert RegistroConsumoAlmuerzo.objects.filter(hijo=hijo_almuerzo).count() == 1

    def test_sin_client_request_id_sigue_funcionando_como_antes(
        self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, precio_almuerzo, suscripcion_activa,
    ):
        # Compatibilidad hacia atrás: el campo es opcional, así que un
        # request sin client_request_id (clientes viejos) crea normalmente.
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {"hijo": hijo_almuerzo.pk, "fecha_consumo": str(date.today()), "nro_tarjeta": tarjeta_almuerzo.pk},
            format="json",
        )
        assert resp.status_code == 201
        assert RegistroConsumoAlmuerzo.objects.get(pk=resp.data["id_registro_consumo"]).client_request_id is None

    def test_sin_precio_usa_tipo_almuerzo(self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, tipo_almuerzo, suscripcion_activa):
        # No hay PrecioAlmuerzo activo → usa tipo_almuerzo.precio_unitario
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk,
                "fecha_consumo": str(date.today()),
                "nro_tarjeta": tarjeta_almuerzo.pk,
                "tipo_almuerzo": tipo_almuerzo.pk,
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["costo_almuerzo"] == "12000"

    def test_sin_precio_ni_tipo_falla(self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, suscripcion_activa):
        # No hay precio ni tipo → error
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk,
                "fecha_consumo": str(date.today()),
                "nro_tarjeta": tarjeta_almuerzo.pk,
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_segundo_registro_costo_cero(self, api_cajero, hijo_almuerzo, tarjeta_almuerzo,
                                          precio_almuerzo, usuario_cajero, suscripcion_activa):
        from django.utils import timezone
        from datetime import timedelta
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        # fecha/hora derivadas de timezone.localtime() de punta a punta — usar
        # date.today() (reloj del SO) junto con hora_registro (reloj de Django)
        # puede desalinearse si difieren de TIME_ZONE, sobre todo cerca de
        # medianoche.
        hoy = timezone.localtime().date()
        # Primer registro directo en BD, hace mas de 240s (umbral minimo entre
        # 1er y 2do registro) para que el segundo no sea tratado como reintento.
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo,
            fecha_consumo=hoy,
            hora_registro=(timezone.localtime() - timedelta(seconds=300)).time(),
            costo_almuerzo=Decimal("15000"),
            ya_cobrado=True,
            nro_tarjeta=tarjeta_almuerzo,
            registrado_por=usuario_cajero,
            estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
        )
        # Segundo registro vía API
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk,
                "fecha_consumo": str(hoy),
                "nro_tarjeta": tarjeta_almuerzo.pk,
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["ya_cobrado"] is False
        assert resp.data["costo_almuerzo"] == "0"

    def test_segundo_registro_muy_pronto_bloquea(self, api_cajero, hijo_almuerzo, tarjeta_almuerzo,
                                                   precio_almuerzo, usuario_cajero, suscripcion_activa):
        from django.utils import timezone
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        hoy = timezone.localtime().date()
        # Primer registro recien hecho (hora_registro = ahora por default)
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo,
            fecha_consumo=hoy,
            costo_almuerzo=Decimal("15000"),
            ya_cobrado=True,
            nro_tarjeta=tarjeta_almuerzo,
            registrado_por=usuario_cajero,
            estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
        )
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk,
                "fecha_consumo": str(hoy),
                "nro_tarjeta": tarjeta_almuerzo.pk,
            },
            format="json",
        )
        assert resp.status_code == 400
        assert "muy pronto" in resp.data["detail"]

    def test_tercer_registro_retorna_400_con_mensaje_limite(self, api_cajero, hijo_almuerzo, tarjeta_almuerzo,
                                                              precio_almuerzo, usuario_cajero, suscripcion_activa):
        from django.utils import timezone
        from datetime import timedelta
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        hoy = timezone.localtime().date()
        for segundos_atras in (600, 300):
            RegistroConsumoAlmuerzo.objects.create(
                hijo=hijo_almuerzo,
                fecha_consumo=hoy,
                hora_registro=(timezone.localtime() - timedelta(seconds=segundos_atras)).time(),
                costo_almuerzo=Decimal("15000") if segundos_atras == 600 else Decimal("0"),
                ya_cobrado=segundos_atras == 600,
                nro_tarjeta=tarjeta_almuerzo,
                registrado_por=usuario_cajero,
                estado=RegistroConsumoAlmuerzo.Estado.REGISTRADO,
            )
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk,
                "fecha_consumo": str(hoy),
                "nro_tarjeta": tarjeta_almuerzo.pk,
            },
            format="json",
        )
        assert resp.status_code == 400
        assert "Limite alcanzado" in resp.data["detail"]

    def test_tarjeta_bloqueada_falla(self, api_cajero, hijo_almuerzo, tarjeta_bloqueada, precio_almuerzo):
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk,
                "fecha_consumo": str(date.today()),
                "nro_tarjeta": tarjeta_bloqueada.pk,
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_tarjeta_de_otro_hijo_falla(self, api_cajero, hijo_almuerzo, precio_almuerzo, cliente, grado):
        from apps.clientes.models import Hijo
        from apps.core.models import Tarjeta
        otro_hijo = Hijo.objects.create(
            nombre="Otro", apellido="Hijo",
            cliente_responsable=cliente, grado=grado, activo=True,
        )
        tarjeta_otro = Tarjeta.objects.create(
            nro_tarjeta="OTRO-001", hijo=otro_hijo, estado=Tarjeta.Estado.ACTIVA,
        )
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk,
                "fecha_consumo": str(date.today()),
                "nro_tarjeta": tarjeta_otro.pk,
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_suscripcion_suspendida_falla(self, api_cajero, hijo_almuerzo, tarjeta_almuerzo,
                                           precio_almuerzo, suscripcion_suspendida):
        # La suscripción se resuelve del lado del servidor (read-only) — una
        # suspendida no cuenta como activa, así que no hay ninguna vigente.
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk,
                "fecha_consumo": str(date.today()),
                "nro_tarjeta": tarjeta_almuerzo.pk,
            },
            format="json",
        )
        assert resp.status_code == 400
        assert "suscrip" in resp.data["detail"].lower()

    def test_sin_suscripcion_falla(self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, precio_almuerzo):
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk,
                "fecha_consumo": str(date.today()),
                "nro_tarjeta": tarjeta_almuerzo.pk,
            },
            format="json",
        )
        assert resp.status_code == 400
        assert "suscrip" in resp.data["detail"].lower()

    def test_con_suscripcion_activa_ok(self, api_cajero, hijo_almuerzo, tarjeta_almuerzo,
                                        precio_almuerzo, suscripcion_activa):
        # La suscripción se resuelve sola del lado del servidor — no hace
        # falta (ni se puede: el campo es read-only) mandarla en el body.
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk,
                "fecha_consumo": str(date.today()),
                "nro_tarjeta": tarjeta_almuerzo.pk,
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["ya_cobrado"] is True
        assert resp.data["suscripcion"] == suscripcion_activa.pk


# ── CuentaAlmuerzoMensualViewSet ──────────────────────────────────────────────

@pytest.mark.django_db
class TestCuentaMensual:
    """CuentaAlmuerzoMensual quedó como archivo histórico de solo lectura:
    desde que el cobro vive en SaldoAlmuerzo (y se retiró el trigger que
    sincronizaba estas filas), ya no se crean cuentas nuevas por acá."""

    def test_generar_ya_no_existe(self, api_admin):
        resp = api_admin.post(
            "/api/v1/almuerzos/cuentas-mensuales/generar/",
            {"anio": 2026, "mes": 5},
            format="json",
        )
        assert resp.status_code in (404, 405)

    def test_post_rechazado_solo_lectura(self, api_admin, hijo_almuerzo):
        resp = api_admin.post(
            "/api/v1/almuerzos/cuentas-mensuales/",
            {"hijo": hijo_almuerzo.pk, "anio": 2026, "mes": 5},
            format="json",
        )
        assert resp.status_code == 405

    def test_delete_rechazado_solo_lectura(self, api_admin, cuenta_mensual):
        resp = api_admin.delete(
            f"/api/v1/almuerzos/cuentas-mensuales/{cuenta_mensual.pk}/"
        )
        assert resp.status_code == 405

    def test_cliente_web_filtra_sus_cuentas(self, api_cliente_web, cuenta_mensual):
        resp = api_cliente_web.get("/api/v1/almuerzos/cuentas-mensuales/")
        assert resp.status_code == 200

    def test_filtro_estado_acepta_varios_valores_separados_por_coma(self, api_cliente_web, cuenta_mensual):
        """PagarAlmuerzo.tsx pide ?estado=PENDIENTE,PARCIAL — antes de este fix
        el filtro auto-generado era un ChoiceFilter de valor único y devolvía
        400 (portal mostraba 'Error al cargar las cuentas de almuerzo')."""
        resp = api_cliente_web.get(
            "/api/v1/almuerzos/cuentas-mensuales/", {"estado": "PENDIENTE,PARCIAL"}
        )
        assert resp.status_code == 200
        ids = [c["id_cuenta_mensual"] for c in resp.data["results"]]
        assert cuenta_mensual.id_cuenta_mensual in ids

    def test_filtro_estado_un_solo_valor_sigue_funcionando(self, api_cliente_web, cuenta_mensual):
        resp = api_cliente_web.get(
            "/api/v1/almuerzos/cuentas-mensuales/", {"estado": "PAGADO"}
        )
        assert resp.status_code == 200
        ids = [c["id_cuenta_mensual"] for c in resp.data["results"]]
        assert cuenta_mensual.id_cuenta_mensual not in ids

    def test_cajero_puede_listar_solo_lectura(self, api_cajero, cuenta_mensual):
        resp = api_cajero.get("/api/v1/almuerzos/cuentas-mensuales/")
        assert resp.status_code == 200


# ── EstadoCuentaAlmuerzoView ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestEstadoCuentaAlmuerzo:

    def test_sin_anio_retorna_400(self, api_admin):
        resp = api_admin.get("/api/v1/almuerzos/estado-cuenta/")
        assert resp.status_code == 400

    def test_sin_consumos_retorna_vacio(self, api_admin):
        resp = api_admin.get("/api/v1/almuerzos/estado-cuenta/", {"anio": 2026})
        assert resp.status_code == 200
        assert resp.data == {"count": 0, "results": []}

    def test_con_consumos_arma_fila_por_hijo_y_mes(
        self, api_admin, consumos_mes_actual, hijo_almuerzo, tarjeta_almuerzo,
    ):
        hoy = date.today()
        resp = api_admin.get("/api/v1/almuerzos/estado-cuenta/", {"anio": hoy.year})
        assert resp.status_code == 200
        assert resp.data["count"] == 1
        fila = resp.data["results"][0]
        assert fila["hijo"] == hijo_almuerzo.pk
        assert fila["hijo_nombre"] == hijo_almuerzo.nombre_completo
        assert fila["nro_tarjeta"] == "ALMZ-VIEW01"
        assert fila["mes"] == hoy.month
        assert fila["cantidad_almuerzos"] == 5
        assert fila["monto_total"] == 75000

    def test_filtro_por_mes_excluye_otros_meses(self, api_admin, hijo_almuerzo, usuario_cajero):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, fecha_consumo=date(2026, 3, 10),
            costo_almuerzo=Decimal("15000"), ya_cobrado=True, registrado_por=usuario_cajero,
        )
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, fecha_consumo=date(2026, 4, 10),
            costo_almuerzo=Decimal("15000"), ya_cobrado=True, registrado_por=usuario_cajero,
        )
        resp = api_admin.get("/api/v1/almuerzos/estado-cuenta/", {"anio": 2026, "mes": 3})
        assert resp.status_code == 200
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["mes"] == 3

    def test_sin_mes_agrupa_por_cada_mes_con_consumo(self, api_admin, hijo_almuerzo, usuario_cajero):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, fecha_consumo=date(2026, 3, 10),
            costo_almuerzo=Decimal("15000"), ya_cobrado=True, registrado_por=usuario_cajero,
        )
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, fecha_consumo=date(2026, 4, 10),
            costo_almuerzo=Decimal("15000"), ya_cobrado=True, registrado_por=usuario_cajero,
        )
        resp = api_admin.get("/api/v1/almuerzos/estado-cuenta/", {"anio": 2026})
        assert resp.status_code == 200
        assert resp.data["count"] == 2
        meses = {f["mes"] for f in resp.data["results"]}
        assert meses == {3, 4}

    def test_repite_sin_cobrar_no_cuenta(self, api_admin, hijo_almuerzo, usuario_cajero):
        # El 2do registro del día (ya_cobrado=False) no debe sumar al reporte.
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, fecha_consumo=date(2026, 3, 10),
            costo_almuerzo=Decimal("15000"), ya_cobrado=True, registrado_por=usuario_cajero,
        )
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, fecha_consumo=date(2026, 3, 10),
            costo_almuerzo=Decimal("0"), ya_cobrado=False, registrado_por=usuario_cajero,
        )
        resp = api_admin.get("/api/v1/almuerzos/estado-cuenta/", {"anio": 2026, "mes": 3})
        assert resp.status_code == 200
        assert resp.data["results"][0]["cantidad_almuerzos"] == 1

    def test_estado_pendiente_y_pagado_segun_saldo(
        self, api_admin, hijo_almuerzo, usuario_cajero
    ):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo, SaldoAlmuerzo
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, fecha_consumo=date(2026, 3, 10),
            costo_almuerzo=Decimal("15000"), ya_cobrado=True, registrado_por=usuario_cajero,
        )
        SaldoAlmuerzo.objects.create(hijo=hijo_almuerzo, saldo_actual=Decimal("-15000"))
        resp = api_admin.get("/api/v1/almuerzos/estado-cuenta/", {"anio": 2026, "mes": 3})
        assert resp.data["results"][0]["estado"] == "PENDIENTE"
        assert resp.data["results"][0]["saldo_pendiente"] == 15000

    def test_recarga_del_mes_se_ve_en_monto_pagado(
        self, api_admin, hijo_almuerzo, usuario_cajero
    ):
        from datetime import datetime
        from django.utils import timezone
        from apps.almuerzos.models import RegistroConsumoAlmuerzo, RecargaSaldoAlmuerzo
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, fecha_consumo=date(2026, 3, 10),
            costo_almuerzo=Decimal("15000"), ya_cobrado=True, registrado_por=usuario_cajero,
        )
        RecargaSaldoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, monto_cargado=Decimal("15000"),
            fecha_carga=timezone.make_aware(datetime(2026, 3, 15)),
            estado=RecargaSaldoAlmuerzo.Estado.CONFIRMADA,
        )
        resp = api_admin.get("/api/v1/almuerzos/estado-cuenta/", {"anio": 2026, "mes": 3})
        assert resp.data["results"][0]["monto_pagado"] == 15000

    def test_requiere_permiso_staff(self, api_cliente_web):
        resp = api_cliente_web.get("/api/v1/almuerzos/estado-cuenta/", {"anio": 2026})
        assert resp.status_code == 403


# ── EstadoCuentaAlmuerzoView — arrastre real desde la billetera ──────────────

@pytest.mark.django_db
class TestEstadoCuentaAlmuerzoArrastre:

    @pytest.fixture
    def suscripcion_activa(self, db, hijo_almuerzo):
        from apps.almuerzos.models import SuscripcionAlmuerzo
        return SuscripcionAlmuerzo.objects.create(
            hijo=hijo_almuerzo, fecha_inicio=date(2026, 1, 1),
            estado=SuscripcionAlmuerzo.Estado.ACTIVA,
        )

    @pytest.fixture
    def precio_fijo(self, db):
        from apps.almuerzos.models import PrecioAlmuerzo
        return PrecioAlmuerzo.objects.create(
            precio_unitario=Decimal("25000"), fecha_inicio_vigencia=date(2026, 1, 1), activo=True,
        )

    def _comer(self, hijo, tarjeta, usuario, fecha):
        from apps.almuerzos.services import AlmuerzoService
        with freeze_time(fecha):
            AlmuerzoService.registrar_consumo(
                hijo=hijo, fecha_consumo=fecha, nro_tarjeta=tarjeta, registrado_por=usuario,
            )

    def _recargar(self, hijo, monto, fecha):
        from apps.almuerzos.services import AlmuerzoService
        with freeze_time(fecha):
            AlmuerzoService.recargar_saldo(hijo=hijo, monto=Decimal(str(monto)))

    def test_arrastre_real_mes_a_mes_por_la_billetera(
        self, api_admin, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, suscripcion_activa, precio_fijo,
    ):
        # Mayo: recarga 100.000, come 2 veces (50.000) -> saldo final 50.000.
        self._recargar(hijo_almuerzo, 100000, date(2026, 5, 1))
        self._comer(hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, date(2026, 5, 10))
        self._comer(hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, date(2026, 5, 20))
        # Junio: come 1 vez (25.000), sin recargar -> saldo final 25.000.
        self._comer(hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, date(2026, 6, 5))
        # Julio: come 2 veces (50.000), sin recargar -> saldo final -25.000 (deuda).
        self._comer(hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, date(2026, 7, 3))
        self._comer(hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, date(2026, 7, 15))

        resp = api_admin.get("/api/v1/almuerzos/estado-cuenta/", {"anio": 2026})
        assert resp.status_code == 200
        filas = {f["mes"]: f for f in resp.data["results"]}
        assert set(filas) == {5, 6, 7}

        assert filas[5]["saldo_inicial"] == 0
        assert filas[5]["saldo_final"] == 50000
        assert filas[5]["estado"] == "PAGADO"

        assert filas[6]["saldo_inicial"] == 50000
        assert filas[6]["saldo_final"] == 25000
        assert filas[6]["estado"] == "PAGADO"

        # El saldo_inicial de julio es el saldo_final de junio: el arrastre
        # se encadena mes a mes.
        assert filas[7]["saldo_inicial"] == 25000
        assert filas[7]["saldo_final"] == -25000
        assert filas[7]["estado"] == "PENDIENTE"
        assert not any(f["es_arrastre"] for f in filas.values())

    def test_corte_es_por_instante_no_por_mes_calendario(
        self, api_admin, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, suscripcion_activa, precio_fijo,
    ):
        """Reproduce el caso real de la migración: un ajuste a mitad de mes,
        con consumos del MISMO mes de antes y de después del instante exacto
        del ajuste — los de antes van al arrastre aunque caigan en agosto."""
        from apps.almuerzos.models import MovimientoSaldoAlmuerzo, SaldoAlmuerzo

        # Consumos de antes de la migración, ya cargados directo (sin billetera).
        with freeze_time(date(2026, 8, 3)):
            self._registro_directo(hijo_almuerzo, usuario_cajero, date(2026, 8, 3))
        with freeze_time(date(2026, 8, 5)):
            self._registro_directo(hijo_almuerzo, usuario_cajero, date(2026, 8, 5))

        # 06/08: migración — ajuste de +100.000 (lo que se trae del sistema viejo).
        # A las 23:00 para no dejar dudas de que es anterior al consumo del 07/08.
        with freeze_time(datetime(2026, 8, 6, 23, 0)):
            saldo = SaldoAlmuerzo.objects.create(hijo=hijo_almuerzo, saldo_actual=Decimal("100000"))
            MovimientoSaldoAlmuerzo.objects.create(
                saldo=saldo, tipo=MovimientoSaldoAlmuerzo.Tipo.AJUSTE,
                monto=Decimal("100000"), saldo_resultante=Decimal("100000"),
                observaciones="Saldo inicial migrado desde CuentaAlmuerzoMensual histórica",
            )

        # Después de la migración, consumo real por el servicio.
        self._comer(hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, date(2026, 8, 7))
        self._recargar(hijo_almuerzo, 450000, date(2026, 8, 20))

        resp = api_admin.get("/api/v1/almuerzos/estado-cuenta/", {"anio": 2026, "mes": 8})
        assert resp.status_code == 200
        agosto = next(f for f in resp.data["results"] if not f["es_arrastre"])
        arrastre = next(f for f in resp.data["results"] if f["es_arrastre"])

        # Los 2 consumos de antes del corte NO entran en el total de agosto.
        assert agosto["cantidad_almuerzos"] == 1
        assert agosto["monto_total"] == 25000
        # El ajuste pasa a ser el saldo_inicial real de agosto, no 0.
        assert agosto["saldo_inicial"] == 100000
        assert agosto["saldo_final"] == 100000 + 450000 - 25000

        assert arrastre["cantidad_almuerzos"] == 2
        assert arrastre["monto_total"] == 50000
        assert arrastre["saldo_final"] == 100000
        assert arrastre["arrastre_hasta_fecha"] == "2026-08-06"

        # Reconciliación exacta: inicial + pagado - consumido = final.
        assert agosto["saldo_inicial"] + agosto["monto_pagado"] - agosto["monto_total"] == agosto["saldo_final"]

    def _registro_directo(self, hijo, usuario, fecha):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        return RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo, fecha_consumo=fecha, costo_almuerzo=Decimal("25000"),
            ya_cobrado=True, registrado_por=usuario,
        )

    def test_meses_anteriores_al_primer_movimiento_se_agrupan_en_arrastre(
        self, api_admin, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, suscripcion_activa, precio_fijo,
    ):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        # Marzo: consumo cargado directo (como en el sistema viejo, con su
        # fecha_creacion real de esa época), sin pasar por el servicio -> no
        # genera movimiento de billetera.
        with freeze_time(date(2026, 3, 10)):
            RegistroConsumoAlmuerzo.objects.create(
                hijo=hijo_almuerzo, fecha_consumo=date(2026, 3, 10),
                costo_almuerzo=Decimal("15000"), ya_cobrado=True, registrado_por=usuario_cajero,
            )
        # Agosto: primer consumo real por el servicio -> primer movimiento de billetera.
        self._comer(hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, date(2026, 8, 5))

        resp = api_admin.get("/api/v1/almuerzos/estado-cuenta/", {"anio": 2026})
        assert resp.status_code == 200
        assert resp.data["count"] == 2

        arrastre = next(f for f in resp.data["results"] if f["es_arrastre"])
        assert arrastre["mes"] is None
        assert arrastre["cantidad_almuerzos"] == 1
        assert arrastre["monto_total"] == 15000
        assert arrastre["saldo_inicial"] is None and arrastre["saldo_final"] == 0
        assert arrastre["arrastre_hasta_fecha"] == "2026-08-05"

        agosto = next(f for f in resp.data["results"] if f["mes"] == 8)
        assert agosto["es_arrastre"] is False
        assert agosto["saldo_inicial"] == 0
        assert agosto["saldo_final"] == -25000
        assert agosto["estado"] == "PENDIENTE"

    def test_arrastre_aparece_al_final_del_orden(
        self, api_admin, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, suscripcion_activa, precio_fijo,
    ):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        with freeze_time(date(2026, 3, 10)):
            RegistroConsumoAlmuerzo.objects.create(
                hijo=hijo_almuerzo, fecha_consumo=date(2026, 3, 10),
                costo_almuerzo=Decimal("15000"), ya_cobrado=True, registrado_por=usuario_cajero,
            )
        self._comer(hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, date(2026, 8, 5))

        resp = api_admin.get("/api/v1/almuerzos/estado-cuenta/", {"anio": 2026})
        assert resp.data["results"][-1]["es_arrastre"] is True

    def test_sin_movimientos_usa_el_saldo_de_hoy_en_todas_las_filas(
        self, api_admin, hijo_almuerzo, usuario_cajero,
    ):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo, SaldoAlmuerzo
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, fecha_consumo=date(2026, 3, 10),
            costo_almuerzo=Decimal("15000"), ya_cobrado=True, registrado_por=usuario_cajero,
        )
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, fecha_consumo=date(2026, 4, 10),
            costo_almuerzo=Decimal("15000"), ya_cobrado=True, registrado_por=usuario_cajero,
        )
        SaldoAlmuerzo.objects.create(hijo=hijo_almuerzo, saldo_actual=Decimal("-30000"))

        resp = api_admin.get("/api/v1/almuerzos/estado-cuenta/", {"anio": 2026})
        assert resp.data["count"] == 2
        for fila in resp.data["results"]:
            assert fila["es_arrastre"] is False
            assert fila["saldo_inicial"] is None
            assert fila["saldo_final"] == -30000
            assert fila["estado"] == "PENDIENTE"


# ── PagoCuentaAlmuerzoViewSet ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestPagoCuenta:

    def test_create_ya_no_esta_permitido(self, api_cajero, cuenta_mensual, usuario_cajero):
        """PagoCuentaAlmuerzo es solo lectura: el pago de almuerzo pasa
        exclusivamente por RecargaSaldoAlmuerzo, para no cobrar el mismo
        almuerzo en dos sistemas distintos sin sincronía entre sí."""
        resp = api_cajero.post(
            "/api/v1/almuerzos/pagos-cuentas/",
            {
                "cuenta": cuenta_mensual.pk,
                "monto": 50000,
                "medio_pago": "EFECTIVO",
                "registrado_por": usuario_cajero.pk,
            },
            format="json",
        )
        assert resp.status_code == 405

    def test_list_ok(self, api_cajero):
        resp = api_cajero.get("/api/v1/almuerzos/pagos-cuentas/")
        assert resp.status_code == 200


# ── ReporteAlmuerzosView ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteAlmuerzos:

    def test_sin_anio_retorna_400(self, api_admin):
        resp = api_admin.get("/api/v1/almuerzos/reportes/")
        assert resp.status_code == 400

    def test_solo_mes_retorna_400(self, api_admin):
        resp = api_admin.get("/api/v1/almuerzos/reportes/", {"mes": "5"})
        assert resp.status_code == 400

    def test_con_anio_mes_retorna_estructura(self, api_admin):
        resp = api_admin.get("/api/v1/almuerzos/reportes/", {"anio": "2026", "mes": "5"})
        assert resp.status_code == 200
        assert "periodo" in resp.data
        assert "totales" in resp.data
        assert "filas" in resp.data

    def test_con_consumos_muestra_alumno(self, api_admin, consumos_mes_actual):
        hoy = date.today()
        resp = api_admin.get(
            "/api/v1/almuerzos/reportes/",
            {"anio": str(hoy.year), "mes": str(hoy.month)},
        )
        assert resp.status_code == 200
        assert resp.data["totales"]["alumnos"] >= 1
        assert resp.data["filas"][0]["cantidad_almuerzos"] == 5
        assert resp.data["filas"][0]["monto_total"] == 75000

    def test_filtro_por_hijo(self, api_admin, consumos_mes_actual, hijo_almuerzo):
        hoy = date.today()
        resp = api_admin.get(
            "/api/v1/almuerzos/reportes/",
            {"anio": str(hoy.year), "mes": str(hoy.month), "hijo": hijo_almuerzo.pk},
        )
        assert resp.status_code == 200
        assert len(resp.data["filas"]) == 1

    def test_filtro_por_grado(self, api_admin, consumos_mes_actual, grado):
        hoy = date.today()
        resp = api_admin.get(
            "/api/v1/almuerzos/reportes/",
            {"anio": str(hoy.year), "mes": str(hoy.month), "grado": grado.nombre[:4]},
        )
        assert resp.status_code == 200

    def test_formato_csv(self, api_admin, consumos_mes_actual):
        hoy = date.today()
        resp = api_admin.get(
            "/api/v1/almuerzos/reportes/",
            {"anio": str(hoy.year), "mes": str(hoy.month), "formato": "csv"},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]
        assert b"REPORTE DE ALMUERZOS" in resp.content

    def test_csv_incluye_alumno(self, api_admin, consumos_mes_actual):
        hoy = date.today()
        resp = api_admin.get(
            "/api/v1/almuerzos/reportes/",
            {"anio": str(hoy.year), "mes": str(hoy.month), "formato": "csv"},
        )
        assert resp.status_code == 200
        assert b"Pedro" in resp.content

    def test_filtro_por_tarjeta(self, api_admin, consumos_mes_actual, tarjeta_almuerzo):
        hoy = date.today()
        resp = api_admin.get(
            "/api/v1/almuerzos/reportes/",
            {"anio": str(hoy.year), "mes": str(hoy.month), "tarjeta": "ALMZ-VIEW01"},
        )
        assert resp.status_code == 200
        assert len(resp.data["filas"]) == 1
        assert resp.data["filas"][0]["nro_tarjeta"] == "ALMZ-VIEW01"

    def test_filas_incluyen_nro_tarjeta(self, api_admin, consumos_mes_actual, tarjeta_almuerzo):
        hoy = date.today()
        resp = api_admin.get(
            "/api/v1/almuerzos/reportes/",
            {"anio": str(hoy.year), "mes": str(hoy.month)},
        )
        assert resp.status_code == 200
        assert len(resp.data["filas"]) >= 1
        assert "nro_tarjeta" in resp.data["filas"][0]

    def test_estado_pendiente_cuando_saldo_negativo(self, api_admin, consumos_mes_actual, hijo_almuerzo):
        from apps.almuerzos.models import SaldoAlmuerzo
        SaldoAlmuerzo.objects.create(hijo=hijo_almuerzo, saldo_actual=Decimal("-75000"))
        hoy = date.today()
        resp = api_admin.get(
            "/api/v1/almuerzos/reportes/",
            {"anio": str(hoy.year), "mes": str(hoy.month)},
        )
        assert resp.status_code == 200
        assert resp.data["filas"][0]["estado"] == "PENDIENTE"
        assert resp.data["filas"][0]["monto_pendiente"] == 75000

    def test_estado_pagado_cuando_saldo_al_dia(self, api_admin, consumos_mes_actual, hijo_almuerzo):
        from apps.almuerzos.models import SaldoAlmuerzo
        SaldoAlmuerzo.objects.create(hijo=hijo_almuerzo, saldo_actual=Decimal("0"))
        hoy = date.today()
        resp = api_admin.get(
            "/api/v1/almuerzos/reportes/",
            {"anio": str(hoy.year), "mes": str(hoy.month)},
        )
        assert resp.status_code == 200
        assert resp.data["filas"][0]["estado"] == "PAGADO"
        assert resp.data["filas"][0]["monto_pendiente"] == 0

    def test_requiere_autenticacion(self, api_client):
        resp = api_client.get("/api/v1/almuerzos/reportes/", {"anio": "2026", "mes": "5"})
        assert resp.status_code in (401, 403)


# ── Cobertura de ramas adicionales ────────────────────────────────────────────

@pytest.mark.django_db
class TestRegistroConsumoLineasAdicionales:

    def test_sin_tarjeta_falla(self, api_cajero, hijo_almuerzo, precio_almuerzo):
        # nro_tarjeta=None → hits line 200 (ValidationError "Debe especificar la tarjeta")
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {"hijo": hijo_almuerzo.pk, "fecha_consumo": str(date.today())},
            format="json",
        )
        assert resp.status_code == 400

    def test_suscripcion_suspendida_falla(self, api_cajero, hijo_almuerzo, tarjeta_almuerzo,
                                           precio_almuerzo, suscripcion_suspendida):
        # suscripcion.estado != ACTIVA → hits line 219
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk,
                "fecha_consumo": str(date.today()),
                "nro_tarjeta": tarjeta_almuerzo.pk,
                "suscripcion": suscripcion_suspendida.pk,
            },
            format="json",
        )
        assert resp.status_code == 400

    def test_con_restriccion_no_critica_muestra_advertencias(
        self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, precio_almuerzo, suscripcion_activa
    ):
        # RestriccionHijo no crítica → validar_restricciones_alergenicas retorna advertencias
        # hits line 187 (data["advertencias"] = advertencias)
        from apps.clientes.models import RestriccionHijo
        RestriccionHijo.objects.create(
            hijo=hijo_almuerzo,
            tipo="ALERGIA",
            descripcion="Maní",
            severidad=RestriccionHijo.Severidad.ALTA,
            requiere_autorizacion=False,
            activo=True,
        )
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {"hijo": hijo_almuerzo.pk, "fecha_consumo": str(date.today()), "nro_tarjeta": tarjeta_almuerzo.pk},
            format="json",
        )
        assert resp.status_code == 201
        assert "advertencias" in resp.data

    def test_restriccion_critica_bloquea_con_detalle_estructurado(
        self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, precio_almuerzo, suscripcion_activa
    ):
        # Regresión: el bloqueo por restricción CRITICA debe llegar al frontend
        # con "restricciones" como lista de diccionarios en el nivel superior
        # de la respuesta (no envuelto por el manejador global de excepciones,
        # que aplanaría cada restricción a un string ilegible) — así
        # Comedor.tsx puede armar el aviso de "Autorizar e ingresar".
        from apps.clientes.models import RestriccionHijo
        RestriccionHijo.objects.create(
            hijo=hijo_almuerzo, tipo="ALERGIA", descripcion="Maní crítico",
            severidad=RestriccionHijo.Severidad.CRITICA, requiere_autorizacion=True, activo=True,
        )
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {"hijo": hijo_almuerzo.pk, "fecha_consumo": str(date.today()), "nro_tarjeta": tarjeta_almuerzo.pk},
            format="json",
        )
        assert resp.status_code == 400
        assert resp.data["restricciones"][0]["tipo"] == "ALERGIA"
        assert resp.data["restricciones"][0]["severidad"] == "CRITICA"

        resp2 = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk, "fecha_consumo": str(date.today()),
                "nro_tarjeta": tarjeta_almuerzo.pk, "forzar_restriccion": True,
            },
            format="json",
        )
        assert resp2.status_code == 201
        assert resp2.data["advertencias"][0]["severidad"] == "CRITICA"


@pytest.mark.django_db
class TestRegistroConsumoAlergenosMenu:
    """Cruce de alérgenos del menú del día contra las restricciones del hijo,
    al registrar el ingreso al comedor (mismo mecanismo que Ventas/ModoRecreo)."""

    def _menu_con_producto_alergenico(self, producto, usuario_admin):
        from apps.almuerzos.models import Alergeno, MenuDiario, DetalleMenuDiario, ProductoAlergeno
        menu = MenuDiario.objects.create(
            fecha=date.today(),
            plato_principal="Torta de maní",
            activo=True,
            creado_por=usuario_admin,
        )
        DetalleMenuDiario.objects.create(
            menu=menu, producto=producto, curso="POSTRE", cantidad=1,
        )
        alergeno = Alergeno.objects.create(nombre="Maní", severidad=Alergeno.Severidad.ALTA)
        ProductoAlergeno.objects.create(producto=producto, alergeno=alergeno, contiene=True)
        return menu

    def test_menu_con_alergeno_bloquea_sin_forzar(
        self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, precio_almuerzo, producto, usuario_admin
    ):
        from apps.clientes.models import RestriccionHijo
        RestriccionHijo.objects.create(
            hijo=hijo_almuerzo, tipo="ALERGIA", descripcion="Maní",
            severidad=RestriccionHijo.Severidad.ALTA, requiere_autorizacion=False, activo=True,
        )
        self._menu_con_producto_alergenico(producto, usuario_admin)
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {"hijo": hijo_almuerzo.pk, "fecha_consumo": str(date.today()), "nro_tarjeta": tarjeta_almuerzo.pk},
            format="json",
        )
        assert resp.status_code == 400
        assert resp.data["advertencias_alergenos"]
        assert resp.data["advertencias_alergenos"][0]["alergeno"] == "Maní"

    def test_menu_con_alergeno_forzar_registra_ok(
        self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, precio_almuerzo, producto, usuario_admin, suscripcion_activa
    ):
        from apps.clientes.models import RestriccionHijo
        RestriccionHijo.objects.create(
            hijo=hijo_almuerzo, tipo="ALERGIA", descripcion="Maní",
            severidad=RestriccionHijo.Severidad.ALTA, requiere_autorizacion=False, activo=True,
        )
        self._menu_con_producto_alergenico(producto, usuario_admin)
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {
                "hijo": hijo_almuerzo.pk, "fecha_consumo": str(date.today()),
                "nro_tarjeta": tarjeta_almuerzo.pk, "forzar_alergenos": True,
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["advertencias_alergenos"]

    def test_menu_sin_detalle_no_bloquea(
        self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, precio_almuerzo, usuario_admin, suscripcion_activa
    ):
        # Caso de hoy: un MenuDiario existe pero sin DetalleMenuDiario vinculado
        # (texto libre) — no debe cambiar el comportamiento existente.
        from apps.almuerzos.models import MenuDiario
        from apps.clientes.models import RestriccionHijo
        RestriccionHijo.objects.create(
            hijo=hijo_almuerzo, tipo="ALERGIA", descripcion="Maní",
            severidad=RestriccionHijo.Severidad.ALTA, requiere_autorizacion=False, activo=True,
        )
        MenuDiario.objects.create(
            fecha=date.today(), plato_principal="Milanesa", activo=True, creado_por=usuario_admin,
        )
        resp = api_cajero.post(
            "/api/v1/almuerzos/registros-consumo/",
            {"hijo": hijo_almuerzo.pk, "fecha_consumo": str(date.today()), "nro_tarjeta": tarjeta_almuerzo.pk},
            format="json",
        )
        assert resp.status_code == 201
        assert "advertencias_alergenos" not in resp.data


@pytest.mark.django_db
class TestDetalleMenuPermisos:

    def test_create_admin_ok(self, api_admin, menu_hoy, producto):
        resp = api_admin.post(
            "/api/v1/almuerzos/detalle-menu/",
            {"menu": menu_hoy.pk, "producto": producto.pk, "curso": "PLATO_PRINCIPAL", "es_opcional": False},
            format="json",
        )
        assert resp.status_code in (201, 400)

    def test_create_cocina_ok(self, api_client, menu_hoy, producto):
        # Cocina/Supervisor gestionan /menu-diario en el frontend — el permiso
        # de DetalleMenuDiarioViewSet debe alinearse con MenuDiarioViewSet
        # (IsStaffOrClienteWeb), no restringirse a ADMIN.
        from apps.usuarios.models import Usuario
        cocina = Usuario.objects.create_user(
            email="cocina@test.com", password="test1234",
            nombre="Cocina", apellido="Test", rol=Usuario.Rol.COCINA,
        )
        api_client.force_authenticate(user=cocina)
        resp = api_client.post(
            "/api/v1/almuerzos/detalle-menu/",
            {"menu": menu_hoy.pk, "producto": producto.pk, "curso": "PLATO_PRINCIPAL", "es_opcional": False},
            format="json",
        )
        assert resp.status_code in (201, 400)

    def test_create_cliente_web_prohibido(self, api_client, menu_hoy, producto, cliente):
        from apps.usuarios.models import Usuario
        padre = Usuario.objects.create_user(
            email="padre@test.com", password="test1234",
            nombre="Padre", apellido="Test", rol=Usuario.Rol.CLIENTE_WEB, cliente=cliente,
        )
        api_client.force_authenticate(user=padre)
        resp = api_client.post(
            "/api/v1/almuerzos/detalle-menu/",
            {"menu": menu_hoy.pk, "producto": producto.pk, "curso": "PLATO_PRINCIPAL", "es_opcional": False},
            format="json",
        )
        assert resp.status_code == 403


# ── RegistroConsumo destroy (admin) ───────────────────────────────────────────

@pytest.mark.django_db
class TestRegistroConsumoDestroyAdmin:
    """Líneas 177-184: destroy con ADMIN — solo permite borrar registros ANULADOS."""

    def _registro(self, hijo, tarjeta, cajero, estado):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        return RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo,
            fecha_consumo=date.today() - timedelta(days=2),
            costo_almuerzo=Decimal("15000"),
            ya_cobrado=True,
            nro_tarjeta=tarjeta,
            registrado_por=cajero,
            estado=estado,
        )

    def test_admin_elimina_registro_anulado_204(
        self, api_admin, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero
    ):
        registro = self._registro(
            hijo_almuerzo, tarjeta_almuerzo, usuario_cajero,
            "ANULADO",
        )
        resp = api_admin.delete(f"/api/v1/almuerzos/registros-consumo/{registro.pk}/")
        assert resp.status_code == 204

    def test_admin_no_puede_eliminar_no_anulado_400(
        self, api_admin, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero
    ):
        registro = self._registro(
            hijo_almuerzo, tarjeta_almuerzo, usuario_cajero,
            "REGISTRADO",
        )
        resp = api_admin.delete(f"/api/v1/almuerzos/registros-consumo/{registro.pk}/")
        assert resp.status_code == 400
        assert "ANULADO" in resp.data["error"]


# ── RegistroConsumo anular ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRegistroConsumoAnular:
    """POST .../registros-consumo/<id>/anular/ — reemplaza el PATCH estado=ANULADO
    que nunca funcionó porque `estado` es read_only en el serializer."""

    def _registro(self, hijo, tarjeta, cajero, ya_cobrado=True, costo="15000", estado="REGISTRADO"):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        return RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo,
            fecha_consumo=date.today(),
            costo_almuerzo=Decimal(costo),
            ya_cobrado=ya_cobrado,
            nro_tarjeta=tarjeta,
            registrado_por=cajero,
            estado=estado,
        )

    def test_sin_autenticacion_falla(self, api_client, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero):
        registro = self._registro(hijo_almuerzo, tarjeta_almuerzo, usuario_cajero)
        resp = api_client.post(f"/api/v1/almuerzos/registros-consumo/{registro.pk}/anular/")
        assert resp.status_code in (401, 403)

    def test_cliente_web_no_puede_anular(
        self, api_cliente_web, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero
    ):
        registro = self._registro(hijo_almuerzo, tarjeta_almuerzo, usuario_cajero)
        resp = api_cliente_web.post(f"/api/v1/almuerzos/registros-consumo/{registro.pk}/anular/")
        assert resp.status_code == 403
        registro.refresh_from_db()
        assert registro.estado == "REGISTRADO"

    def test_cocina_puede_anular(
        self, api_cocina_consumo, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero
    ):
        registro = self._registro(hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, ya_cobrado=False, costo="0")
        resp = api_cocina_consumo.post(f"/api/v1/almuerzos/registros-consumo/{registro.pk}/anular/")
        assert resp.status_code == 200
        registro.refresh_from_db()
        assert registro.estado == "ANULADO"

    def test_no_registrado_falla(self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero):
        registro = self._registro(hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, estado="ANULADO")
        resp = api_cajero.post(f"/api/v1/almuerzos/registros-consumo/{registro.pk}/anular/")
        assert resp.status_code == 400
        assert "REGISTRADO" in resp.data["detail"]

    def test_anula_y_revierte_saldo_cuando_estaba_cobrado(
        self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero
    ):
        from apps.almuerzos.models import SaldoAlmuerzo
        SaldoAlmuerzo.objects.create(hijo=hijo_almuerzo, saldo_actual=Decimal("-15000"))
        registro = self._registro(hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, ya_cobrado=True, costo="15000")

        resp = api_cajero.post(f"/api/v1/almuerzos/registros-consumo/{registro.pk}/anular/")

        assert resp.status_code == 200
        assert resp.data["estado"] == "ANULADO"
        registro.refresh_from_db()
        assert registro.estado == "ANULADO"
        saldo = SaldoAlmuerzo.objects.get(hijo=hijo_almuerzo)
        assert saldo.saldo_actual == Decimal("0")

    def test_anula_segundo_registro_sin_cobro_no_mueve_saldo(
        self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero
    ):
        from apps.almuerzos.models import SaldoAlmuerzo
        SaldoAlmuerzo.objects.create(hijo=hijo_almuerzo, saldo_actual=Decimal("5000"))
        registro = self._registro(hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, ya_cobrado=False, costo="0")

        resp = api_cajero.post(f"/api/v1/almuerzos/registros-consumo/{registro.pk}/anular/")

        assert resp.status_code == 200
        registro.refresh_from_db()
        assert registro.estado == "ANULADO"
        saldo = SaldoAlmuerzo.objects.get(hijo=hijo_almuerzo)
        assert saldo.saldo_actual == Decimal("5000")

    def test_no_toca_cuenta_mensual_historica(
        self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero
    ):
        # CuentaAlmuerzoMensual es archivo histórico de solo lectura (ya no
        # hay trigger que la sincronice) — anular un registro no debe
        # modificarla.
        from apps.almuerzos.models import CuentaAlmuerzoMensual
        hoy = date.today()
        cuenta = CuentaAlmuerzoMensual.objects.create(
            hijo=hijo_almuerzo, anio=hoy.year, mes=hoy.month,
            cantidad_almuerzos=1, monto_total=Decimal("15000"), monto_pagado=Decimal("0"),
            forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
        )
        registro = self._registro(hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, ya_cobrado=True, costo="15000")

        resp = api_cajero.post(f"/api/v1/almuerzos/registros-consumo/{registro.pk}/anular/")

        assert resp.status_code == 200
        cuenta.refresh_from_db()
        assert cuenta.monto_total == Decimal("15000")
        assert cuenta.cantidad_almuerzos == 1

    def test_queda_auditado(self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero):
        from apps.usuarios.models import AuditoriaOperacion
        registro = self._registro(hijo_almuerzo, tarjeta_almuerzo, usuario_cajero)

        resp = api_cajero.post(f"/api/v1/almuerzos/registros-consumo/{registro.pk}/anular/")

        assert resp.status_code == 200
        auditoria = AuditoriaOperacion.objects.filter(operacion="ANULAR_REGISTRO_ALMUERZO").first()
        assert auditoria is not None
        assert str(registro.hijo_id) in auditoria.descripcion


# ── RegistroConsumo: WhatsApp except silente ──────────────────────────────────

@pytest.mark.django_db
class TestRegistroConsumoWhatsappFallback:
    """Líneas 285-286: whatsapp_cliente lanza excepción → se ignora, create igual exitoso."""

    def test_create_exitoso_aunque_whatsapp_falle(
        self, api_cajero, hijo_almuerzo, tarjeta_almuerzo, precio_almuerzo, suscripcion_activa
    ):
        from unittest.mock import patch
        with patch(
            "apps.notificaciones.services.whatsapp_cliente",
            side_effect=Exception("WhatsApp caído"),
        ):
            resp = api_cajero.post(
                "/api/v1/almuerzos/registros-consumo/",
                {
                    "hijo": hijo_almuerzo.pk,
                    "fecha_consumo": str(date.today()),
                    "nro_tarjeta": tarjeta_almuerzo.pk,
                },
                format="json",
            )
        assert resp.status_code == 201


# ── ReporteConsumoGradoView ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteConsumoGrado:
    """Líneas 604-690: reporte consumo por grado — JSON y CSV."""

    def test_sin_params_retorna_400(self, api_admin):
        resp = api_admin.get("/api/v1/almuerzos/reporte-consumo-grado/")
        assert resp.status_code == 400

    def test_con_fechas_retorna_estructura(self, api_admin):
        resp = api_admin.get(
            "/api/v1/almuerzos/reporte-consumo-grado/",
            {"desde": "2026-01-01", "hasta": "2026-12-31"},
        )
        assert resp.status_code == 200
        assert "por_grado" in resp.data
        assert "horarios_pico" in resp.data
        assert "resumen" in resp.data

    def test_con_datos_calcula_tasa_rechazo(
        self, api_admin, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, precio_almuerzo
    ):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo,
            fecha_consumo=date(2026, 6, 10),
            costo_almuerzo=Decimal("15000"),
            ya_cobrado=True,
            nro_tarjeta=tarjeta_almuerzo,
            registrado_por=usuario_cajero,
            estado="REGISTRADO",
        )
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo,
            fecha_consumo=date(2026, 6, 11),
            costo_almuerzo=Decimal("15000"),
            ya_cobrado=False,
            nro_tarjeta=tarjeta_almuerzo,
            registrado_por=usuario_cajero,
            estado="RECHAZADO",
        )
        resp = api_admin.get(
            "/api/v1/almuerzos/reporte-consumo-grado/",
            {"desde": "2026-06-01", "hasta": "2026-06-30"},
        )
        assert resp.status_code == 200
        grados = resp.data["por_grado"]
        assert len(grados) == 1
        assert grados[0]["tasa_rechazo"] == 50.0

    def test_formato_csv_retorna_descarga(self, api_admin):
        resp = api_admin.get(
            "/api/v1/almuerzos/reporte-consumo-grado/",
            {"desde": "2026-01-01", "hasta": "2026-12-31", "formato": "csv"},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]
        assert "attachment" in resp["Content-Disposition"]

    def test_formato_csv_con_datos_incluye_filas(
        self, api_admin, hijo_almuerzo, tarjeta_almuerzo, usuario_cajero, precio_almuerzo
    ):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo,
            fecha_consumo=date(2026, 5, 10),
            costo_almuerzo=Decimal("15000"),
            ya_cobrado=True,
            nro_tarjeta=tarjeta_almuerzo,
            registrado_por=usuario_cajero,
            estado="REGISTRADO",
        )
        resp = api_admin.get(
            "/api/v1/almuerzos/reporte-consumo-grado/",
            {"desde": "2026-05-01", "hasta": "2026-05-31", "formato": "csv"},
        )
        assert resp.status_code == 200
        content = resp.content.decode("utf-8-sig")
        assert "3er grado" in content


# ── ReporteCobranzaAlmuerzosView ──────────────────────────────────────────────

@pytest.mark.django_db
class TestReporteCobranzaAlmuerzos:
    """Líneas 711-806: reporte cobranza por año — JSON y CSV."""

    def test_sin_anio_retorna_400(self, api_admin):
        resp = api_admin.get("/api/v1/almuerzos/reporte-cobranza/")
        assert resp.status_code == 400

    def test_anio_invalido_retorna_400(self, api_admin):
        resp = api_admin.get("/api/v1/almuerzos/reporte-cobranza/", {"anio": "no_anio"})
        assert resp.status_code == 400

    def test_con_anio_retorna_estructura(self, api_admin):
        resp = api_admin.get("/api/v1/almuerzos/reporte-cobranza/", {"anio": "2026"})
        assert resp.status_code == 200
        assert "por_mes" in resp.data
        assert "por_forma_cobro" in resp.data
        assert "resumen" in resp.data

    def test_con_cuentas_calcula_totales(
        self, api_admin, hijo_almuerzo, grado, usuario_cajero
    ):
        """monto_anual sale de RegistroConsumoAlmuerzo (consumo real), cobrado_anual
        de RecargaSaldoAlmuerzo (recargas del saldo corriente) — no del mismo modelo."""
        from datetime import datetime
        from django.utils import timezone
        from apps.almuerzos.models import RegistroConsumoAlmuerzo, RecargaSaldoAlmuerzo
        for _ in range(10):
            RegistroConsumoAlmuerzo.objects.create(
                hijo=hijo_almuerzo, fecha_consumo=date(2026, 6, 10),
                costo_almuerzo=Decimal("15000"), ya_cobrado=True,
                registrado_por=usuario_cajero,
            )
        RecargaSaldoAlmuerzo.objects.create(
            hijo=hijo_almuerzo,
            monto_cargado=Decimal("100000"),
            fecha_carga=timezone.make_aware(datetime(2026, 6, 15)),
            estado=RecargaSaldoAlmuerzo.Estado.CONFIRMADA,
            metodo_pago="EFECTIVO",
        )
        resp = api_admin.get("/api/v1/almuerzos/reporte-cobranza/", {"anio": "2026"})
        assert resp.status_code == 200
        assert resp.data["resumen"]["monto_anual"] == 150000
        assert resp.data["resumen"]["cobrado_anual"] == 100000

    def test_formato_csv_retorna_descarga(self, api_admin):
        resp = api_admin.get(
            "/api/v1/almuerzos/reporte-cobranza/",
            {"anio": "2026", "formato": "csv"},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp["Content-Type"]
        assert "attachment" in resp["Content-Disposition"]

    def test_formato_csv_con_datos_incluye_filas(
        self, api_admin, hijo_almuerzo, usuario_cajero
    ):
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        for _ in range(8):
            RegistroConsumoAlmuerzo.objects.create(
                hijo=hijo_almuerzo, fecha_consumo=date(2026, 3, 10),
                costo_almuerzo=Decimal("15000"), ya_cobrado=True,
                registrado_por=usuario_cajero,
            )
        resp = api_admin.get(
            "/api/v1/almuerzos/reporte-cobranza/",
            {"anio": "2026", "formato": "csv"},
        )
        assert resp.status_code == 200
        content = resp.content.decode("utf-8-sig")
        assert "Marzo" in content

    def test_excel_retorna_xlsx(self, api_admin):
        resp = api_admin.get(
            "/api/v1/almuerzos/reporte-cobranza/",
            {"anio": "2026", "formato": "excel"},
        )
        assert resp.status_code == 200
        assert "spreadsheetml" in resp["Content-Type"]
        assert "attachment" in resp.get("Content-Disposition", "")
        assert resp.get("Content-Disposition", "").endswith(".xlsx\"")

    def test_excel_con_datos_genera_filas(self, api_admin, hijo_almuerzo, usuario_cajero):
        import io
        from decimal import Decimal
        from openpyxl import load_workbook
        from apps.almuerzos.models import RegistroConsumoAlmuerzo
        RegistroConsumoAlmuerzo.objects.create(
            hijo=hijo_almuerzo, fecha_consumo=date(2026, 3, 10),
            costo_almuerzo=Decimal("15000"), ya_cobrado=True,
            registrado_por=usuario_cajero,
        )
        resp = api_admin.get(
            "/api/v1/almuerzos/reporte-cobranza/",
            {"anio": "2026", "formato": "excel"},
        )
        assert resp.status_code == 200
        wb = load_workbook(io.BytesIO(resp.content))
        ws = wb.active
        assert ws.max_row >= 2  # encabezado + al menos 1 fila

    def test_con_saldo_negativo_incluye_saldos_pendientes(self, api_admin, hijo_almuerzo):
        from apps.almuerzos.models import SaldoAlmuerzo
        SaldoAlmuerzo.objects.create(hijo=hijo_almuerzo, saldo_actual=Decimal("-20000"))

        resp = api_admin.get("/api/v1/almuerzos/reporte-cobranza/", {"anio": "2026"})
        assert resp.status_code == 200
        assert len(resp.data["saldos_pendientes"]) == 1
        assert resp.data["saldos_pendientes"][0]["saldo_actual"] == -20000

    def test_csv_con_saldo_negativo_incluye_seccion(self, api_admin, hijo_almuerzo):
        from apps.almuerzos.models import SaldoAlmuerzo
        SaldoAlmuerzo.objects.create(hijo=hijo_almuerzo, saldo_actual=Decimal("-20000"))

        resp = api_admin.get(
            "/api/v1/almuerzos/reporte-cobranza/", {"anio": "2026", "formato": "csv"},
        )
        content = resp.content.decode("utf-8-sig")
        assert "SALDOS NEGATIVOS ACTUALES" in content
        assert hijo_almuerzo.nombre in content

    def test_excel_con_saldo_negativo_incluye_seccion(self, api_admin, hijo_almuerzo):
        import io
        from openpyxl import load_workbook
        from apps.almuerzos.models import SaldoAlmuerzo
        SaldoAlmuerzo.objects.create(hijo=hijo_almuerzo, saldo_actual=Decimal("-20000"))

        resp = api_admin.get(
            "/api/v1/almuerzos/reporte-cobranza/", {"anio": "2026", "formato": "excel"},
        )
        wb = load_workbook(io.BytesIO(resp.content))
        ws = wb.active
        valores = [cell.value for row in ws.iter_rows() for cell in row]
        assert "SALDOS NEGATIVOS ACTUALES (cuenta corriente, no por mes)" in valores
