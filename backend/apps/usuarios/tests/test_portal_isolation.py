"""
Aislamiento del portal de padres (CLIENTE_WEB).

Un padre solo debe ver datos de su propia familia. Este archivo protege contra
tres regresiones:

1. Fuga en listados: ninguna respuesta GET del portal contiene datos "marcados"
   de otra familia (se barren TODOS los endpoints GET sin parámetros).
2. Acceso directo por id (IDOR): pedir por id un objeto ajeno da 403/404.
3. Superficie nueva: si aparece un endpoint alcanzable por el portal que no está
   en PORTAL_GET_REVISADOS, el test falla para forzar su revisión (¿filtra por
   cliente? ¿es realmente para padres?).
"""
import json
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

# Endpoints GET (sin parámetros) que el portal puede alcanzar y ya fueron
# revisados: filtran por la familia del usuario o no exponen datos de terceros.
PORTAL_GET_REVISADOS = {
    "/api/v1/almuerzos/cuentas-mensuales/",
    "/api/v1/almuerzos/detalle-menu/",
    "/api/v1/almuerzos/menu/",
    "/api/v1/almuerzos/registros-consumo/",
    "/api/v1/almuerzos/saldos/",
    "/api/v1/almuerzos/saldos/resumen/",
    "/api/v1/almuerzos/suscripciones/",
    "/api/v1/bancard/confirmar/",
    "/api/v1/clientes/hijos/",
    "/api/v1/clientes/restricciones/",
    "/api/v1/contabilidad/datos-empresa/publico/",
    "/api/v1/core/bancard/confirmar/",
    "/api/v1/core/bancard/tarjetas/",
    "/api/v1/core/movimientos-tarjeta/",
    "/api/v1/core/tarjetas/",
    "/api/v1/notificaciones/notificaciones/",
    "/api/v1/notificaciones/preferencias/",
    "/api/v1/notificaciones/vapid-public-key/",
    "/api/v1/usuarios/2fa/estado/",
    "/api/v1/usuarios/portal/historial-cantina/",
    "/api/v1/usuarios/portal/historial-consumos/",
    "/api/v1/usuarios/portal/historial-recargas/",
    "/api/v1/usuarios/portal/mi-hijo/",
    "/api/v1/usuarios/portal/mis-facturas/",
    "/api/v1/usuarios/usuarios/me/",
}

_SALTAR = ("retorno", "logout", "schema", "docs", "redoc", "metrics", "health", "foto")
_SIN_ACCESO = (401, 403, 404, 405)

MARCA = "ZZAJENO"


@pytest.fixture(scope="module")
def rutas_get():
    """Todas las rutas GET sin parámetros de path, tomadas del esquema de la API."""
    from drf_spectacular.generators import SchemaGenerator

    schema = SchemaGenerator().get_schema(request=None, public=True)
    rutas = sorted(
        p for p, ops in schema["paths"].items()
        if "get" in ops and "{" not in p and not any(s in p for s in _SALTAR)
    )
    assert len(rutas) > 50, "el esquema de la API no devolvió rutas: el barrido sería vacío"
    return rutas


@pytest.fixture
def familias(db, cliente, usuario_cajero):
    """Familia A (usuario del portal) y familia B (datos marcados con ZZAJENO)."""
    from apps.almuerzos.models import (
        CuentaAlmuerzoMensual, RegistroConsumoAlmuerzo,
        SaldoAlmuerzo, SuscripcionAlmuerzo,
    )
    from apps.clientes.models import Cliente, Grado, Hijo, RestriccionHijo
    from apps.contabilidad.models import Factura
    from apps.core.models import MovimientoTarjeta, Tarjeta
    from apps.notificaciones.models import Notificacion
    from apps.usuarios.models import Usuario

    grado, _ = Grado.objects.get_or_create(nombre="G-ISO-P", defaults={"nivel": 3, "orden": 3})

    # ── Familia A: la del usuario del portal ──
    hijo_a = Hijo.objects.create(
        nombre="ZZPROPIO", apellido="Hijo", cliente_responsable=cliente, grado=grado, activo=True,
    )
    Tarjeta.objects.create(nro_tarjeta="ZZPROPIA1", hijo=hijo_a, saldo_actual=Decimal("1500"))
    padre = Usuario.objects.create_user(
        email="padre_a@iso.test", password="x12345678", nombre="Padre", apellido="A",
        rol=Usuario.Rol.CLIENTE_WEB, cliente=cliente,
    )

    # ── Familia B: ajena, con datos marcados ──
    cliente_b = Cliente.objects.create(
        nombres=f"{MARCA}CLI", apellidos="Familia", ruc_ci="8888881",
        tipo_cliente=cliente.tipo_cliente, lista_precio=cliente.lista_precio,
        limite_credito=Decimal("1"),
    )
    hijo_b = Hijo.objects.create(
        nombre=f"{MARCA}HIJO", apellido="Ajeno", cliente_responsable=cliente_b, grado=grado, activo=True,
    )
    tarjeta_b = Tarjeta.objects.create(nro_tarjeta=f"{MARCA}TARJ1", hijo=hijo_b, saldo_actual=Decimal("7777"))
    mov_b = MovimientoTarjeta.objects.create(
        tarjeta=tarjeta_b, tipo="RECARGA", monto=Decimal("500"),
        saldo_anterior=Decimal("7777"), saldo_resultante=Decimal("8277"),
    )
    consumo_b = RegistroConsumoAlmuerzo.objects.create(
        hijo=hijo_b, fecha_consumo=date.today(), costo_almuerzo=Decimal("25000"),
        registrado_por=usuario_cajero,
    )
    susc_b = SuscripcionAlmuerzo.objects.create(
        hijo=hijo_b, fecha_inicio=date.today(),
        estado=SuscripcionAlmuerzo.Estado.ACTIVA,
    )
    saldo_b = SaldoAlmuerzo.objects.create(hijo=hijo_b, saldo_actual=Decimal("-1234"))
    cuenta_b = CuentaAlmuerzoMensual.objects.create(
        hijo=hijo_b, anio=date.today().year, mes=date.today().month, cantidad_almuerzos=3,
        monto_total=Decimal("75000"), forma_cobro=CuentaAlmuerzoMensual.FormaCobro.EFECTIVO,
    )
    factura_b = Factura.objects.create(
        cliente=cliente_b, nro_factura="999-999-9999999", monto_total=Decimal("5000"),
    )
    restr_b = RestriccionHijo.objects.create(
        hijo=hijo_b, tipo="Alergia", descripcion=f"{MARCA}-RESTRICCION",
        severidad=RestriccionHijo.Severidad.ALTA,
    )
    padre_b = Usuario.objects.create_user(
        email="padre_b@iso.test", password="x12345678", nombre="Padre", apellido="B",
        rol=Usuario.Rol.CLIENTE_WEB, cliente=cliente_b,
    )
    notif_b = Notificacion.objects.create(
        usuario=padre_b, tipo=Notificacion.Tipo.SISTEMA,
        titulo=f"{MARCA}-NOTIFICACION", mensaje="privada de la familia B",
    )

    api = APIClient()
    api.force_authenticate(user=padre)
    return {
        "api": api,
        "urls_ajenas": [
            f"/api/v1/core/tarjetas/{tarjeta_b.nro_tarjeta}/",
            f"/api/v1/core/movimientos-tarjeta/{mov_b.pk}/",
            f"/api/v1/clientes/hijos/{hijo_b.pk}/",
            f"/api/v1/clientes/restricciones/{restr_b.pk}/",
            f"/api/v1/almuerzos/registros-consumo/{consumo_b.pk}/",
            f"/api/v1/almuerzos/suscripciones/{susc_b.pk}/",
            f"/api/v1/almuerzos/saldos/{saldo_b.pk}/",
            f"/api/v1/almuerzos/saldos/{saldo_b.pk}/movimientos/",
            f"/api/v1/almuerzos/cuentas-mensuales/{cuenta_b.pk}/",
            f"/api/v1/notificaciones/notificaciones/{notif_b.pk}/",
            f"/api/v1/contabilidad/facturas/{factura_b.pk}/",
            f"/api/v1/contabilidad/facturas/{factura_b.pk}/pdf/",
        ],
    }


@pytest.mark.django_db
class TestAislamientoPortal:

    def test_ningun_listado_del_portal_expone_datos_de_otra_familia(self, familias, rutas_get):
        api = familias["api"]
        fugas = []
        for ruta in rutas_get:
            resp = api.get(ruta)
            if resp.status_code != 200:
                continue
            cuerpo = json.dumps(getattr(resp, "data", None), default=str)
            if MARCA in cuerpo:
                fugas.append(ruta)
        assert not fugas, f"El portal ve datos de OTRA familia en: {fugas}"

    def test_el_barrido_no_es_vacio_ve_los_datos_propios(self, familias):
        """Control positivo: si el propio dato no aparece, el test anterior no probaría nada."""
        resp = familias["api"].get("/api/v1/core/tarjetas/")
        assert [t["nro_tarjeta"] for t in resp.data["results"]] == ["ZZPROPIA1"]

    def test_acceso_directo_por_id_a_objetos_ajenos_es_denegado(self, familias):
        api = familias["api"]
        permitidas = {
            url: api.get(url).status_code
            for url in familias["urls_ajenas"]
            if api.get(url).status_code not in (403, 404)
        }
        assert not permitidas, f"El portal pudo leer objetos de otra familia por id: {permitidas}"

    def test_no_hay_endpoints_nuevos_alcanzables_por_el_portal_sin_revisar(self, familias, rutas_get):
        api = familias["api"]
        alcanzables = {r for r in rutas_get if api.get(r).status_code not in _SIN_ACCESO}
        nuevos = alcanzables - PORTAL_GET_REVISADOS
        assert not nuevos, (
            "Endpoints GET alcanzables por el portal que no están revisados: "
            f"{sorted(nuevos)}. Verificá que filtren por el cliente del usuario "
            "(get_queryset) y agregalos a PORTAL_GET_REVISADOS en este archivo."
        )
